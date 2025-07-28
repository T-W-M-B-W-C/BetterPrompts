package services

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/betterprompts/api-gateway/internal/models"
	"github.com/google/uuid"
	"github.com/lib/pq"
)

// DatabaseService extends sql.DB with application-specific methods
type DatabaseService struct {
	*sql.DB
}

// NewDatabaseService creates a new database service
func NewDatabaseService(db *sql.DB) *DatabaseService {
	return &DatabaseService{DB: db}
}

// SavePromptHistory saves a prompt history entry to the database
func (db *DatabaseService) SavePromptHistory(ctx context.Context, entry models.PromptHistory) (string, error) {
	// Generate a unique UUID
	id := uuid.New().String()
	entry.ID = id
	entry.CreatedAt = time.Now()

	query := `
		INSERT INTO prompts.history (
			id, user_id, original_input, enhanced_output,
			intent, complexity, techniques_used, metadata, created_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
	`

	// Convert metadata to JSON
	metadataJSON, _ := json.Marshal(entry.Metadata)

	// Convert techniques slice to PostgreSQL array
	techniquesArray := pq.Array(entry.TechniquesUsed)

	_, err := db.ExecContext(ctx, query,
		entry.ID,
		entry.UserID.String,
		entry.OriginalInput,
		entry.EnhancedOutput,
		entry.Intent.String,  // intent
		entry.Complexity.String, // complexity
		techniquesArray,
		metadataJSON,
		entry.CreatedAt,
	)

	if err != nil {
		return "", fmt.Errorf("failed to save prompt history: %w", err)
	}

	return id, nil
}

// GetPromptHistory retrieves a prompt history entry by ID
func (db *DatabaseService) GetPromptHistory(ctx context.Context, id string) (*models.PromptHistory, error) {
	query := `
		SELECT id, user_id, original_input, enhanced_output,
			   intent, complexity, techniques_used, metadata,
			   feedback_score, feedback_text, created_at, updated_at
		FROM prompts.history
		WHERE id = $1
	`

	var entry models.PromptHistory
	var userID sql.NullString
	var techniques pq.StringArray
	var metadataJSON []byte
	var intent, complexity sql.NullString
	var feedbackScore sql.NullInt64
	var feedbackText sql.NullString
	var updatedAt sql.NullTime

	err := db.QueryRowContext(ctx, query, id).Scan(
		&entry.ID,
		&userID,
		&entry.OriginalInput,
		&entry.EnhancedOutput,
		&intent,
		&complexity,
		&techniques,
		&metadataJSON,
		&feedbackScore,
		&feedbackText,
		&entry.CreatedAt,
		&updatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("prompt history not found")
		}
		return nil, fmt.Errorf("failed to get prompt history: %w", err)
	}

	// Set nullable fields
	entry.UserID = userID
	entry.Intent = intent
	entry.Complexity = complexity
	entry.FeedbackScore = feedbackScore
	entry.FeedbackText = feedbackText
	if updatedAt.Valid {
		entry.UpdatedAt = updatedAt.Time
	}

	// Convert techniques array
	entry.TechniquesUsed = []string(techniques)
	
	var metadata map[string]interface{}
	if err := json.Unmarshal(metadataJSON, &metadata); err == nil {
		entry.Metadata = metadata
	}

	return &entry, nil
}

// GetUserPromptHistory retrieves prompt history for a user
func (db *DatabaseService) GetUserPromptHistory(ctx context.Context, userID string, limit, offset int) ([]models.PromptHistory, error) {
	query := `
		SELECT id, user_id, original_input, enhanced_output,
			   intent, complexity, techniques_used, metadata,
			   feedback_score, feedback_text, created_at
		FROM prompts.history
		WHERE user_id = $1
		ORDER BY created_at DESC
		LIMIT $2 OFFSET $3
	`

	rows, err := db.QueryContext(ctx, query, userID, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to query prompt history: %w", err)
	}
	defer rows.Close()

	var entries []models.PromptHistory
	for rows.Next() {
		var entry models.PromptHistory
		var uid sql.NullString
		var techniques pq.StringArray
		var metadataJSON []byte
		var intent, complexity sql.NullString
		var rating sql.NullInt64
		var feedback sql.NullString

		err := rows.Scan(
			&entry.ID,
			&uid,
			&entry.OriginalInput,
			&entry.EnhancedOutput,
			&intent,
			&complexity,
			&techniques,
			&metadataJSON,
			&rating,
			&feedback,
			&entry.CreatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		// Set nullable fields
		entry.UserID = uid
		entry.Intent = intent
		entry.Complexity = complexity
		if rating.Valid {
			entry.FeedbackScore = sql.NullInt64{Int64: rating.Int64, Valid: true}
		}
		entry.FeedbackText = feedback

		// Convert techniques array
		entry.TechniquesUsed = []string(techniques)
		
		var metadata map[string]interface{}
		if err := json.Unmarshal(metadataJSON, &metadata); err == nil {
			entry.Metadata = metadata
		}

		entries = append(entries, entry)
	}

	return entries, nil
}

// DeletePromptHistory deletes a prompt history entry
func (s *DatabaseService) DeletePromptHistory(ctx context.Context, id string) error {
	query := "DELETE FROM prompts.history WHERE id = $1"
	result, err := s.DB.ExecContext(ctx, query, id)
	if err != nil {
		return fmt.Errorf("failed to delete prompt history: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to check affected rows: %w", err)
	}

	if rowsAffected == 0 {
		return fmt.Errorf("prompt history not found")
	}

	return nil
}

// Ping tests the database connection
func (s *DatabaseService) Ping() error {
	return s.DB.Ping()
}

// GetUserPromptHistoryWithFilters retrieves user's prompt history with search and filters
func (s *DatabaseService) GetUserPromptHistoryWithFilters(ctx context.Context, userID string, req models.PaginationRequest) ([]*models.PromptHistory, int64, error) {
	// Build the WHERE clause
	whereConditions := []string{"user_id = $1"}
	args := []interface{}{userID}
	argCounter := 2

	// Add search condition
	if req.Search != "" {
		whereConditions = append(whereConditions, fmt.Sprintf(
			"(original_input ILIKE $%d OR enhanced_output ILIKE $%d)",
			argCounter, argCounter+1,
		))
		searchTerm := "%" + req.Search + "%"
		args = append(args, searchTerm, searchTerm)
		argCounter += 2
	}

	// Add technique filter
	if req.Technique != "" {
		whereConditions = append(whereConditions, fmt.Sprintf(
			"$%d = ANY(techniques_used::text[])",
			argCounter,
		))
		args = append(args, req.Technique)
		argCounter++
	}

	// Add date range filters
	if !req.DateFrom.IsZero() {
		whereConditions = append(whereConditions, fmt.Sprintf(
			"created_at >= $%d",
			argCounter,
		))
		args = append(args, req.DateFrom)
		argCounter++
	}

	if !req.DateTo.IsZero() {
		whereConditions = append(whereConditions, fmt.Sprintf(
			"created_at <= $%d",
			argCounter,
		))
		args = append(args, req.DateTo)
		argCounter++
	}

	whereClause := strings.Join(whereConditions, " AND ")

	// First, get the total count
	countQuery := fmt.Sprintf(`
		SELECT COUNT(*) 
		FROM prompts.history 
		WHERE %s`, whereClause)

	var totalCount int64
	err := s.QueryRowContext(ctx, countQuery, args...).Scan(&totalCount)
	if err != nil {
		return nil, 0, fmt.Errorf("failed to count prompts: %w", err)
	}

	// Build the main query with pagination
	query := fmt.Sprintf(`
		SELECT id, user_id, original_input, enhanced_output,
			   intent, complexity, techniques_used, metadata,
			   feedback_score, feedback_text, created_at, updated_at
		FROM prompts.history
		WHERE %s
		ORDER BY %s %s
		LIMIT $%d OFFSET $%d`,
		whereClause,
		req.SortBy,
		req.SortDirection,
		argCounter,
		argCounter+1,
	)

	args = append(args, req.Limit, req.CalculateOffset())

	rows, err := s.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, 0, fmt.Errorf("failed to query prompts: %w", err)
	}
	defer rows.Close()

	var entries []*models.PromptHistory
	for rows.Next() {
		var entry models.PromptHistory
		var techniques pq.StringArray
		var updatedAt sql.NullTime
		var metadataJSON []byte

		err := rows.Scan(
			&entry.ID,
			&entry.UserID,
			&entry.OriginalInput,
			&entry.EnhancedOutput,
			&entry.Intent,
			&entry.Complexity,
			&techniques,
			&metadataJSON,
			&entry.FeedbackScore,
			&entry.FeedbackText,
			&entry.CreatedAt,
			&updatedAt,
		)
		if err != nil {
			return nil, 0, fmt.Errorf("failed to scan prompt: %w", err)
		}

		entry.TechniquesUsed = []string(techniques)
		if updatedAt.Valid {
			entry.UpdatedAt = updatedAt.Time
		}

		// Unmarshal metadata JSON
		var metadata map[string]interface{}
		if err := json.Unmarshal(metadataJSON, &metadata); err == nil {
			entry.Metadata = metadata
		}

		entries = append(entries, &entry)
	}

	if err = rows.Err(); err != nil {
		return nil, 0, fmt.Errorf("failed to iterate prompts: %w", err)
	}

	return entries, totalCount, nil
}
