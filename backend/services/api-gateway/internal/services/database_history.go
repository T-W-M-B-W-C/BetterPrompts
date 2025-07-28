package services

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/betterprompts/api-gateway/internal/models"
	"github.com/google/uuid"
)

// SavePromptHistoryWithID saves a prompt history entry and returns the ID
func (s *CompleteDatabaseService) SavePromptHistoryWithID(ctx context.Context, entry *models.PromptHistory) (string, error) {
	query := `
		INSERT INTO prompts.history (
			id, user_id, original_input, enhanced_output,
			intent, complexity, techniques_used, metadata,
			created_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP)
		RETURNING id`

	if entry.ID == "" {
		entry.ID = uuid.New().String()
	}

	techniquesJSON, _ := json.Marshal(entry.TechniquesUsed)
	metaJSON, _ := json.Marshal(entry.Metadata)

	var id string
	err := s.db.QueryRowContext(ctx, query,
		entry.ID, 
		entry.UserID, 
		entry.OriginalInput, 
		entry.EnhancedOutput,
		entry.Intent.String,      // intent
		entry.Complexity.String,  // complexity
		techniquesJSON,
		metaJSON,
	).Scan(&id)

	if err != nil {
		return "", fmt.Errorf("failed to save prompt history: %w", err)
	}

	return id, nil
}

// GetPromptHistoryByID retrieves a single prompt history entry by ID
func (s *CompleteDatabaseService) GetPromptHistoryByID(ctx context.Context, historyID string) (*models.PromptHistory, error) {
	query := `
		SELECT id, user_id, original_input, enhanced_output,
			   intent, complexity, techniques_used, metadata,
			   feedback_score, feedback_text, created_at, updated_at
		FROM prompts.history
		WHERE id = $1`

	var entry models.PromptHistory
	var userID sql.NullString
	var techniquesJSON, metaJSON []byte
	var intent, complexity sql.NullString
	var feedbackScore sql.NullInt64
	var feedbackText sql.NullString

	err := s.db.QueryRowContext(ctx, query, historyID).Scan(
		&entry.ID,
		&userID,
		&entry.OriginalInput,
		&entry.EnhancedOutput,
		&intent,
		&complexity,
		&techniquesJSON,
		&metaJSON,
		&feedbackScore,
		&feedbackText,
		&entry.CreatedAt,
		&entry.UpdatedAt,
	)

	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("prompt history not found")
	} else if err != nil {
		return nil, fmt.Errorf("failed to get prompt history: %w", err)
	}

	// Set nullable fields
	entry.UserID = userID
	entry.Intent = intent
	entry.Complexity = complexity
	entry.FeedbackScore = feedbackScore
	entry.FeedbackText = feedbackText

	// Unmarshal JSON fields
	var techniques []string
	if err := json.Unmarshal(techniquesJSON, &techniques); err == nil {
		entry.TechniquesUsed = techniques
	}
	
	var metadata map[string]interface{}
	if err := json.Unmarshal(metaJSON, &metadata); err == nil {
		entry.Metadata = metadata
	}

	return &entry, nil
}

// GetUserPromptHistoryWithFilters retrieves user's prompt history with search and filters
func (s *CompleteDatabaseService) GetUserPromptHistoryWithFilters(ctx context.Context, userID string, req models.PaginationRequest) ([]*models.PromptHistory, int64, error) {
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
			"techniques_used::text ILIKE $%d",
			argCounter,
		))
		args = append(args, "%"+req.Technique+"%")
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
	err := s.db.QueryRowContext(ctx, countQuery, args...).Scan(&totalCount)
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

	rows, err := s.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, 0, fmt.Errorf("failed to query prompts: %w", err)
	}
	defer rows.Close()

	var entries []*models.PromptHistory
	for rows.Next() {
		var entry models.PromptHistory
		var userID sql.NullString
		var techniquesJSON, metaJSON []byte
		var taskType, intent, complexity sql.NullString
		var rating sql.NullInt64
		var feedback sql.NullString
		var updatedAt sql.NullTime

		err := rows.Scan(
			&entry.ID,
			&userID,
			&entry.OriginalInput,
			&entry.EnhancedOutput,
			&taskType,
			&intent,
			&complexity,
			&techniquesJSON,
			&metaJSON,
			&rating,
			&feedback,
			&entry.CreatedAt,
			&updatedAt,
		)
		if err != nil {
			return nil, 0, fmt.Errorf("failed to scan prompt: %w", err)
		}

		// Set nullable fields
		entry.UserID = userID
		entry.Intent = intent
		entry.Complexity = complexity
		if rating.Valid {
			entry.FeedbackScore = sql.NullInt64{Int64: rating.Int64, Valid: true}
		}
		entry.FeedbackText = feedback
		if updatedAt.Valid {
			entry.UpdatedAt = updatedAt.Time
		}

		// Unmarshal JSON fields
		var techniques []string
		if err := json.Unmarshal(techniquesJSON, &techniques); err == nil {
			entry.TechniquesUsed = techniques
		}
		
		var metadata map[string]interface{}
		if err := json.Unmarshal(metaJSON, &metadata); err == nil {
			entry.Metadata = metadata
		}

		entries = append(entries, &entry)
	}

	if err = rows.Err(); err != nil {
		return nil, 0, fmt.Errorf("failed to iterate prompts: %w", err)
	}

	return entries, totalCount, nil
}

// RerunPromptHistory creates a new enhancement using the same technique
func (s *CompleteDatabaseService) RerunPromptHistory(ctx context.Context, historyID string, userID string) (*models.PromptHistory, error) {
	// First, get the original prompt
	original, err := s.GetPromptHistoryByID(ctx, historyID)
	if err != nil {
		return nil, err
	}

	// Verify ownership
	if !original.UserID.Valid || original.UserID.String != userID {
		return nil, fmt.Errorf("prompt not found or unauthorized")
	}

	// Return the original data for re-processing
	// The actual re-enhancement will be done by the handlers
	return original, nil
}

// DeletePromptHistory deletes a prompt history entry
func (s *CompleteDatabaseService) DeletePromptHistory(ctx context.Context, id string) error {
	query := "DELETE FROM prompts WHERE id = $1"
	result, err := s.db.ExecContext(ctx, query, id)
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