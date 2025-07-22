package services

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"github.com/betterprompts/api-gateway/internal/models"
	"github.com/google/uuid"
	"github.com/lib/pq"
	_ "github.com/lib/pq"
	"github.com/jmoiron/sqlx"
)

// CompleteDatabaseService provides all database operations
type CompleteDatabaseService struct {
	db *sqlx.DB
}

// NewCompleteDatabaseService creates a new complete database service
func NewCompleteDatabaseService(dsn string) (*CompleteDatabaseService, error) {
	db, err := sqlx.Connect("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	// Configure connection pool
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)
	db.SetConnMaxIdleTime(1 * time.Minute)

	return &CompleteDatabaseService{db: db}, nil
}

// Close closes the database connection
func (s *CompleteDatabaseService) Close() error {
	return s.db.Close()
}

// Health checks database health
func (s *CompleteDatabaseService) Health(ctx context.Context) error {
	return s.db.PingContext(ctx)
}

// =====================================================
// User Management
// =====================================================

// CreateUser creates a new user
func (s *CompleteDatabaseService) CreateUser(ctx context.Context, user *models.User) error {
	query := `
		INSERT INTO auth.users (
			id, email, username, password_hash, first_name, last_name,
			avatar_url, role, tier, preferences, metadata
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
		)`

	if user.ID == "" {
		user.ID = uuid.New().String()
	}
	if user.Roles[0] == "" {
		user.Roles[0] = "user"
	}
	if user.Tier == "" {
		user.Tier = "free"
	}

	prefsJSON, _ := json.Marshal(user.Preferences)
	metaJSON, _ := json.Marshal(user.Metadata)

	_, err := s.db.ExecContext(ctx, query,
		user.ID, user.Email, user.Username, user.PasswordHash,
		user.FirstName, user.LastName, user.AvatarURL,
		user.Roles[0], user.Tier, prefsJSON, metaJSON,
	)

	return err
}

// GetUserByEmail retrieves a user by email
func (s *CompleteDatabaseService) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	var user models.User
	var prefsJSON, metaJSON []byte

	query := `
		SELECT id, email, username, password_hash, first_name, last_name,
			   avatar_url, is_active, is_verified, role, tier, preferences,
			   metadata, created_at, updated_at, last_login_at
		FROM auth.users
		WHERE LOWER(email) = LOWER($1)`

	err := s.db.QueryRowContext(ctx, query, email).Scan(
		&user.ID, &user.Email, &user.Username, &user.PasswordHash,
		&user.FirstName, &user.LastName, &user.AvatarURL,
		&user.IsActive, &user.IsVerified, &user.Roles[0], &user.Tier,
		&prefsJSON, &metaJSON, &user.CreatedAt, &user.UpdatedAt,
		&user.LastLoginAt,
	)

	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("user not found")
	} else if err != nil {
		return nil, err
	}

	json.Unmarshal(prefsJSON, &user.Preferences)
	json.Unmarshal(metaJSON, &user.Metadata)

	return &user, nil
}

// GetUserByID retrieves a user by ID
func (s *CompleteDatabaseService) GetUserByID(ctx context.Context, id string) (*models.User, error) {
	var user models.User
	var prefsJSON, metaJSON []byte

	query := `
		SELECT id, email, username, password_hash, first_name, last_name,
			   avatar_url, is_active, is_verified, role, tier, preferences,
			   metadata, created_at, updated_at, last_login_at
		FROM auth.users
		WHERE id = $1`

	err := s.db.QueryRowContext(ctx, query, id).Scan(
		&user.ID, &user.Email, &user.Username, &user.PasswordHash,
		&user.FirstName, &user.LastName, &user.AvatarURL,
		&user.IsActive, &user.IsVerified, &user.Roles[0], &user.Tier,
		&prefsJSON, &metaJSON, &user.CreatedAt, &user.UpdatedAt,
		&user.LastLoginAt,
	)

	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("user not found")
	} else if err != nil {
		return nil, err
	}

	json.Unmarshal(prefsJSON, &user.Preferences)
	json.Unmarshal(metaJSON, &user.Metadata)

	return &user, nil
}

// UpdateUserLastLogin updates user's last login time
func (s *CompleteDatabaseService) UpdateUserLastLogin(ctx context.Context, userID string) error {
	query := `
		UPDATE auth.users 
		SET last_login_at = CURRENT_TIMESTAMP, failed_login_attempts = 0
		WHERE id = $1`

	_, err := s.db.ExecContext(ctx, query, userID)
	return err
}

// IncrementFailedLogins increments failed login attempts
func (s *CompleteDatabaseService) IncrementFailedLogins(ctx context.Context, email string) (int, error) {
	var attempts int
	query := `
		UPDATE auth.users 
		SET failed_login_attempts = failed_login_attempts + 1
		WHERE LOWER(email) = LOWER($1)
		RETURNING failed_login_attempts`

	err := s.db.QueryRowContext(ctx, query, email).Scan(&attempts)
	return attempts, err
}

// LockUser locks a user account until specified time
func (s *CompleteDatabaseService) LockUser(ctx context.Context, email string, until time.Time) error {
	query := `
		UPDATE auth.users 
		SET locked_until = $2
		WHERE LOWER(email) = LOWER($1)`

	_, err := s.db.ExecContext(ctx, query, email, until)
	return err
}

// =====================================================
// Session Management
// =====================================================

// CreateSession creates a new session
func (s *CompleteDatabaseService) CreateSession(ctx context.Context, session *models.Session) error {
	query := `
		INSERT INTO auth.sessions (
			id, user_id, token_hash, refresh_token_hash,
			user_agent, ip_address, expires_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7)`

	if session.ID == "" {
		session.ID = uuid.New().String()
	}

	_, err := s.db.ExecContext(ctx, query,
		session.ID, session.UserID, session.TokenHash,
		session.RefreshTokenHash, session.UserAgent,
		session.IPAddress, session.ExpiresAt,
	)

	return err
}

// GetSessionByTokenHash retrieves a session by token hash
func (s *CompleteDatabaseService) GetSessionByTokenHash(ctx context.Context, tokenHash string) (*models.Session, error) {
	var session models.Session

	query := `
		SELECT id, user_id, token_hash, refresh_token_hash,
			   user_agent, ip_address, expires_at, created_at, last_activity
		FROM auth.sessions
		WHERE token_hash = $1 AND expires_at > CURRENT_TIMESTAMP`

	err := s.db.QueryRowContext(ctx, query, tokenHash).Scan(
		&session.ID, &session.UserID, &session.TokenHash,
		&session.RefreshTokenHash, &session.UserAgent,
		&session.IPAddress, &session.ExpiresAt,
		&session.CreatedAt, &session.LastActivity,
	)

	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("session not found or expired")
	}

	return &session, err
}

// UpdateSessionActivity updates session last activity
func (s *CompleteDatabaseService) UpdateSessionActivity(ctx context.Context, sessionID string) error {
	query := `
		UPDATE auth.sessions 
		SET last_activity = CURRENT_TIMESTAMP
		WHERE id = $1`

	_, err := s.db.ExecContext(ctx, query, sessionID)
	return err
}

// DeleteSession deletes a session
func (s *CompleteDatabaseService) DeleteSession(ctx context.Context, sessionID string) error {
	query := `DELETE FROM auth.sessions WHERE id = $1`
	_, err := s.db.ExecContext(ctx, query, sessionID)
	return err
}

// DeleteUserSessions deletes all sessions for a user
func (s *CompleteDatabaseService) DeleteUserSessions(ctx context.Context, userID string) error {
	query := `DELETE FROM auth.sessions WHERE user_id = $1`
	_, err := s.db.ExecContext(ctx, query, userID)
	return err
}

// CleanExpiredSessions removes expired sessions
func (s *CompleteDatabaseService) CleanExpiredSessions(ctx context.Context) (int64, error) {
	query := `DELETE FROM auth.sessions WHERE expires_at < CURRENT_TIMESTAMP`
	result, err := s.db.ExecContext(ctx, query)
	if err != nil {
		return 0, err
	}
	return result.RowsAffected()
}

// =====================================================
// Prompt History
// =====================================================

// SavePromptHistory saves a prompt history entry
func (s *CompleteDatabaseService) SavePromptHistory(ctx context.Context, entry *models.PromptHistory) error {
	query := `
		INSERT INTO prompts.history (
			id, user_id, session_id, request_id, original_input, enhanced_output,
			intent, intent_confidence, complexity, techniques_used, technique_scores,
			processing_time_ms, token_count, model_used, metadata
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)`

	if entry.ID == "" {
		entry.ID = uuid.New().String()
	}

	techniques := pq.Array(entry.TechniquesUsed)
	scoresJSON, _ := json.Marshal(entry.TechniqueScores)
	metaJSON, _ := json.Marshal(entry.Metadata)

	_, err := s.db.ExecContext(ctx, query,
		entry.ID, entry.UserID, entry.SessionID, entry.RequestID,
		entry.OriginalInput, entry.EnhancedOutput,
		entry.Intent, entry.IntentConfidence, entry.Complexity,
		techniques, scoresJSON, entry.ProcessingTimeMs,
		entry.TokenCount, entry.ModelUsed, metaJSON,
	)

	return err
}

// GetPromptHistory retrieves prompt history with pagination
func (s *CompleteDatabaseService) GetPromptHistory(ctx context.Context, userID string, limit, offset int) ([]*models.PromptHistory, error) {
	query := `
		SELECT id, user_id, session_id, request_id, original_input, enhanced_output,
			   intent, intent_confidence, complexity, techniques_used, technique_scores,
			   processing_time_ms, token_count, model_used, feedback_score,
			   feedback_text, is_favorite, metadata, created_at
		FROM prompts.history
		WHERE user_id = $1
		ORDER BY created_at DESC
		LIMIT $2 OFFSET $3`

	rows, err := s.db.QueryContext(ctx, query, userID, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var entries []*models.PromptHistory
	for rows.Next() {
		var entry models.PromptHistory
		var techniques pq.StringArray
		var scoresJSON, metaJSON []byte

		err := rows.Scan(
			&entry.ID, &entry.UserID, &entry.SessionID, &entry.RequestID,
			&entry.OriginalInput, &entry.EnhancedOutput,
			&entry.Intent, &entry.IntentConfidence, &entry.Complexity,
			&techniques, &scoresJSON, &entry.ProcessingTimeMs,
			&entry.TokenCount, &entry.ModelUsed, &entry.FeedbackScore,
			&entry.FeedbackText, &entry.IsFavorite, &metaJSON, &entry.CreatedAt,
		)
		if err != nil {
			return nil, err
		}

		entry.TechniquesUsed = []string(techniques)
		json.Unmarshal(scoresJSON, &entry.TechniqueScores)
		json.Unmarshal(metaJSON, &entry.Metadata)

		entries = append(entries, &entry)
	}

	return entries, nil
}

// UpdatePromptFeedback updates feedback for a prompt
func (s *CompleteDatabaseService) UpdatePromptFeedback(ctx context.Context, historyID string, score int, text string) error {
	query := `
		UPDATE prompts.history 
		SET feedback_score = $2, feedback_text = $3
		WHERE id = $1`

	_, err := s.db.ExecContext(ctx, query, historyID, score, text)
	return err
}

// TogglePromptFavorite toggles favorite status
func (s *CompleteDatabaseService) TogglePromptFavorite(ctx context.Context, historyID string, userID string) error {
	query := `
		UPDATE prompts.history 
		SET is_favorite = NOT is_favorite
		WHERE id = $1 AND user_id = $2`

	result, err := s.db.ExecContext(ctx, query, historyID, userID)
	if err != nil {
		return err
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return err
	}
	if rows == 0 {
		return fmt.Errorf("prompt not found or unauthorized")
	}

	return nil
}

// =====================================================
// Technique Effectiveness
// =====================================================

// UpdateTechniqueEffectiveness updates technique effectiveness metrics
func (s *CompleteDatabaseService) UpdateTechniqueEffectiveness(ctx context.Context, technique, intent string, feedbackScore float64) error {
	query := `
		INSERT INTO analytics.technique_effectiveness 
			(id, technique, intent, success_count, total_count, average_feedback, date)
		VALUES 
			($1, $2, $3, $4, $5, $6, CURRENT_DATE)
		ON CONFLICT (technique, intent, date) DO UPDATE
		SET 
			success_count = CASE 
				WHEN $6 >= 4 THEN technique_effectiveness.success_count + 1 
				ELSE technique_effectiveness.success_count 
			END,
			total_count = technique_effectiveness.total_count + 1,
			average_feedback = (
				(technique_effectiveness.average_feedback * technique_effectiveness.total_count) + $6
			) / (technique_effectiveness.total_count + 1)`

	successCount := 0
	if feedbackScore >= 4 {
		successCount = 1
	}

	_, err := s.db.ExecContext(ctx, query,
		uuid.New().String(), technique, intent,
		successCount, 1, feedbackScore,
	)

	return err
}

// GetTechniqueEffectiveness retrieves technique effectiveness data
func (s *CompleteDatabaseService) GetTechniqueEffectiveness(ctx context.Context, days int) ([]models.TechniqueEffectiveness, error) {
	query := `
		SELECT technique, intent, 
			   SUM(success_count) as success_count,
			   SUM(total_count) as total_count,
			   AVG(average_feedback) as average_feedback
		FROM analytics.technique_effectiveness
		WHERE date >= CURRENT_DATE - INTERVAL '%d days'
		GROUP BY technique, intent
		ORDER BY technique, intent`

	rows, err := s.db.QueryContext(ctx, fmt.Sprintf(query, days))
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var results []models.TechniqueEffectiveness
	for rows.Next() {
		var te models.TechniqueEffectiveness
		err := rows.Scan(
			&te.Technique, &te.Intent,
			&te.SuccessCount, &te.TotalCount,
			&te.AverageFeedback,
		)
		if err != nil {
			return nil, err
		}
		results = append(results, te)
	}

	return results, nil
}

// =====================================================
// Analytics
// =====================================================

// RecordUserActivity records user activity
func (s *CompleteDatabaseService) RecordUserActivity(ctx context.Context, activity *models.UserActivity) error {
	query := `
		INSERT INTO analytics.user_activity (
			id, user_id, activity_type, activity_data,
			session_id, ip_address, user_agent
		) VALUES ($1, $2, $3, $4, $5, $6, $7)`

	if activity.ID == "" {
		activity.ID = uuid.New().String()
	}

	dataJSON, _ := json.Marshal(activity.Data)

	_, err := s.db.ExecContext(ctx, query,
		activity.ID, activity.UserID, activity.Type,
		dataJSON, activity.SessionID, activity.IPAddress,
		activity.UserAgent,
	)

	return err
}

// UpdateDailyStats updates daily statistics
func (s *CompleteDatabaseService) UpdateDailyStats(ctx context.Context) error {
	// This would typically be run as a scheduled job
	query := `
		INSERT INTO analytics.daily_stats (
			id, date, total_requests, unique_users, new_users,
			total_enhancements, average_response_time_ms, error_count
		)
		SELECT 
			$1,
			CURRENT_DATE,
			COUNT(*) as total_requests,
			COUNT(DISTINCT user_id) as unique_users,
			COUNT(DISTINCT CASE 
				WHEN u.created_at::date = CURRENT_DATE THEN u.id 
			END) as new_users,
			COUNT(*) as total_enhancements,
			AVG(processing_time_ms) as average_response_time_ms,
			0 as error_count
		FROM prompts.history h
		LEFT JOIN auth.users u ON h.user_id = u.id
		WHERE h.created_at::date = CURRENT_DATE
		ON CONFLICT (date) DO UPDATE
		SET 
			total_requests = EXCLUDED.total_requests,
			unique_users = EXCLUDED.unique_users,
			new_users = EXCLUDED.new_users,
			total_enhancements = EXCLUDED.total_enhancements,
			average_response_time_ms = EXCLUDED.average_response_time_ms`

	_, err := s.db.ExecContext(ctx, query, uuid.New().String())
	return err
}

// GetDailyStats retrieves daily statistics
func (s *CompleteDatabaseService) GetDailyStats(ctx context.Context, days int) ([]models.DailyStats, error) {
	query := `
		SELECT date, total_requests, unique_users, new_users,
			   total_enhancements, average_response_time_ms, error_count
		FROM analytics.daily_stats
		WHERE date >= CURRENT_DATE - INTERVAL '%d days'
		ORDER BY date DESC`

	rows, err := s.db.QueryContext(ctx, fmt.Sprintf(query, days))
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var stats []models.DailyStats
	for rows.Next() {
		var s models.DailyStats
		err := rows.Scan(
			&s.Date, &s.TotalRequests, &s.UniqueUsers,
			&s.NewUsers, &s.TotalEnhancements,
			&s.AverageResponseTimeMs, &s.ErrorCount,
		)
		if err != nil {
			return nil, err
		}
		stats = append(stats, s)
	}

	return stats, nil
}

// =====================================================
// User Preferences
// =====================================================

// GetUserPreferences retrieves user preferences
func (s *CompleteDatabaseService) GetUserPreferences(ctx context.Context, userID string) (*models.UserPreferences, error) {
	var prefs models.UserPreferences
	var preferredTech, excludedTech pq.StringArray
	var customJSON []byte

	query := `
		SELECT id, user_id, preferred_techniques, excluded_techniques,
			   complexity_preference, ui_theme, ui_language,
			   email_notifications, analytics_opt_in, custom_settings
		FROM auth.user_preferences
		WHERE user_id = $1`

	err := s.db.QueryRowContext(ctx, query, userID).Scan(
		&prefs.ID, &prefs.UserID, &preferredTech, &excludedTech,
		&prefs.ComplexityPreference, &prefs.UITheme, &prefs.UILanguage,
		&prefs.EmailNotifications, &prefs.AnalyticsOptIn, &customJSON,
	)

	if err == sql.ErrNoRows {
		// Return default preferences
		return &models.UserPreferences{
			UserID:             userID,
			UITheme:            "light",
			UILanguage:         "en",
			EmailNotifications: true,
			AnalyticsOptIn:     true,
		}, nil
	} else if err != nil {
		return nil, err
	}

	prefs.PreferredTechniques = []string(preferredTech)
	prefs.ExcludedTechniques = []string(excludedTech)
	json.Unmarshal(customJSON, &prefs.CustomSettings)

	return &prefs, nil
}

// UpdateUserPreferences updates user preferences
func (s *CompleteDatabaseService) UpdateUserPreferences(ctx context.Context, prefs *models.UserPreferences) error {
	query := `
		INSERT INTO auth.user_preferences (
			id, user_id, preferred_techniques, excluded_techniques,
			complexity_preference, ui_theme, ui_language,
			email_notifications, analytics_opt_in, custom_settings
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
		ON CONFLICT (user_id) DO UPDATE
		SET 
			preferred_techniques = $3,
			excluded_techniques = $4,
			complexity_preference = $5,
			ui_theme = $6,
			ui_language = $7,
			email_notifications = $8,
			analytics_opt_in = $9,
			custom_settings = $10`

	if prefs.ID == "" {
		prefs.ID = uuid.New().String()
	}

	preferredTech := pq.Array(prefs.PreferredTechniques)
	excludedTech := pq.Array(prefs.ExcludedTechniques)
	customJSON, _ := json.Marshal(prefs.CustomSettings)

	_, err := s.db.ExecContext(ctx, query,
		prefs.ID, prefs.UserID, preferredTech, excludedTech,
		prefs.ComplexityPreference, prefs.UITheme, prefs.UILanguage,
		prefs.EmailNotifications, prefs.AnalyticsOptIn, customJSON,
	)

	return err
}

// =====================================================
// Saved Prompts and Collections
// =====================================================

// SavePrompt saves a prompt to user's library
func (s *CompleteDatabaseService) SavePrompt(ctx context.Context, saved *models.SavedPrompt) error {
	query := `
		INSERT INTO prompts.saved_prompts (
			id, user_id, history_id, title, description,
			tags, is_public, share_token
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`

	if saved.ID == "" {
		saved.ID = uuid.New().String()
	}
	if saved.IsPublic && !saved.ShareToken.Valid || saved.ShareToken.String == "" {
		saved.ShareToken = sql.NullString{String: uuid.New().String(), Valid: true}
	}

	tags := pq.Array(saved.Tags)

	_, err := s.db.ExecContext(ctx, query,
		saved.ID, saved.UserID, saved.HistoryID,
		saved.Title, saved.Description, tags,
		saved.IsPublic, saved.ShareToken,
	)

	return err
}

// GetSavedPrompts retrieves user's saved prompts
func (s *CompleteDatabaseService) GetSavedPrompts(ctx context.Context, userID string, limit, offset int) ([]*models.SavedPrompt, error) {
	query := `
		SELECT sp.id, sp.user_id, sp.history_id, sp.title, sp.description,
			   sp.tags, sp.is_public, sp.share_token, sp.view_count,
			   sp.created_at, sp.updated_at,
			   h.original_input, h.enhanced_output, h.techniques_used
		FROM prompts.saved_prompts sp
		JOIN prompts.history h ON sp.history_id = h.id
		WHERE sp.user_id = $1
		ORDER BY sp.created_at DESC
		LIMIT $2 OFFSET $3`

	rows, err := s.db.QueryContext(ctx, query, userID, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var prompts []*models.SavedPrompt
	for rows.Next() {
		var sp models.SavedPrompt
		var tags, techniques pq.StringArray

		err := rows.Scan(
			&sp.ID, &sp.UserID, &sp.HistoryID, &sp.Title,
			&sp.Description, &tags, &sp.IsPublic, &sp.ShareToken,
			&sp.ViewCount, &sp.CreatedAt, &sp.UpdatedAt,
			&sp.OriginalInput, &sp.EnhancedOutput, &techniques,
		)
		if err != nil {
			return nil, err
		}

		sp.Tags = []string(tags)
		sp.TechniquesUsed = []string(techniques)
		prompts = append(prompts, &sp)
	}

	return prompts, nil
}

// CreateCollection creates a prompt collection
func (s *CompleteDatabaseService) CreateCollection(ctx context.Context, collection *models.Collection) error {
	query := `
		INSERT INTO prompts.collections (
			id, user_id, name, description, color, icon, is_public, share_token
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`

	if collection.ID == "" {
		collection.ID = uuid.New().String()
	}
	if collection.IsPublic && !collection.ShareToken.Valid || collection.ShareToken.String == "" {
		collection.ShareToken = sql.NullString{String: uuid.New().String(), Valid: true}
	}

	_, err := s.db.ExecContext(ctx, query,
		collection.ID, collection.UserID, collection.Name,
		collection.Description, collection.Color, collection.Icon,
		collection.IsPublic, collection.ShareToken,
	)

	return err
}

// AddPromptToCollection adds a prompt to a collection
func (s *CompleteDatabaseService) AddPromptToCollection(ctx context.Context, collectionID, promptID string, position int) error {
	query := `
		INSERT INTO prompts.collection_prompts (
			collection_id, saved_prompt_id, position
		) VALUES ($1, $2, $3)
		ON CONFLICT (collection_id, saved_prompt_id) DO UPDATE
		SET position = $3`

	_, err := s.db.ExecContext(ctx, query, collectionID, promptID, position)
	return err
}