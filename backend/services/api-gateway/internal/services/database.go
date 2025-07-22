package services

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/betterprompts/api-gateway/internal/models"
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
	// Generate a unique ID
	id := fmt.Sprintf("ph_%d_%d", time.Now().Unix(), time.Now().Nanosecond())
	entry.ID = id
	entry.CreatedAt = time.Now()

	query := `
		INSERT INTO prompts.history (
			id, user_id, session_id, original_input, enhanced_output,
			intent, complexity, techniques_used, confidence, metadata, created_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
	`

	// Convert techniques to PostgreSQL array
	techniques := pq.Array(entry.TechniquesUsed)

	_, err := db.ExecContext(ctx, query,
		entry.ID,
		entry.UserID,
		entry.SessionID,
		entry.OriginalInput,
		entry.EnhancedOutput,
		entry.Intent,
		entry.Complexity,
		techniques,
		entry.IntentConfidence.Float64,
		entry.Metadata,
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
		SELECT id, user_id, session_id, original_input, enhanced_output,
			   intent, complexity, techniques_used, confidence, metadata, created_at
		FROM prompts.history
		WHERE id = $1
	`

	var entry models.PromptHistory
	var techniques pq.StringArray

	err := db.QueryRowContext(ctx, query, id).Scan(
		&entry.ID,
		&entry.UserID,
		&entry.SessionID,
		&entry.OriginalInput,
		&entry.EnhancedOutput,
		&entry.Intent,
		&entry.Complexity,
		&techniques,
		&entry.IntentConfidence.Float64,
		&entry.Metadata,
		&entry.CreatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("prompt history not found")
		}
		return nil, fmt.Errorf("failed to get prompt history: %w", err)
	}

	entry.TechniquesUsed = []string(techniques)
	return &entry, nil
}

// GetUserPromptHistory retrieves prompt history for a user
func (db *DatabaseService) GetUserPromptHistory(ctx context.Context, userID string, limit, offset int) ([]models.PromptHistory, error) {
	query := `
		SELECT id, user_id, session_id, original_input, enhanced_output,
			   intent, complexity, techniques_used, confidence, metadata, created_at
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
		var techniques pq.StringArray

		err := rows.Scan(
			&entry.ID,
			&entry.UserID,
			&entry.SessionID,
			&entry.OriginalInput,
			&entry.EnhancedOutput,
			&entry.Intent,
			&entry.Complexity,
			&techniques,
			&entry.IntentConfidence.Float64,
			&entry.Metadata,
			&entry.CreatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		entry.TechniquesUsed = []string(techniques)
		entries = append(entries, entry)
	}

	return entries, nil
}
// Ping tests the database connection
func (s *DatabaseService) Ping() error {
	return s.DB.Ping()
}
