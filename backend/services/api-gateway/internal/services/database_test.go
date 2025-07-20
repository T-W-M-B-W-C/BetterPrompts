package services_test

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/betterprompts/api-gateway/internal/models"
	"github.com/betterprompts/api-gateway/internal/services"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/stretchr/testify/suite"
)

// DatabaseTestSuite contains all database tests
type DatabaseTestSuite struct {
	suite.Suite
	db      *services.CompleteDatabaseService
	ctx     context.Context
	cancel  context.CancelFunc
	testIDs map[string]string
}

// SetupSuite runs once before all tests
func (s *DatabaseTestSuite) SetupSuite() {
	// Get database connection string from environment or use default
	dsn := os.Getenv("TEST_DATABASE_URL")
	if dsn == "" {
		dsn = "postgres://betterprompts:changeme@localhost:5432/betterprompts_test?sslmode=disable"
	}

	// Create database service
	db, err := services.NewCompleteDatabaseService(dsn)
	require.NoError(s.T(), err, "Failed to create database service")
	
	s.db = db
	s.testIDs = make(map[string]string)
	
	// Clean up test data
	s.cleanupTestData()
}

// SetupTest runs before each test
func (s *DatabaseTestSuite) SetupTest() {
	s.ctx, s.cancel = context.WithTimeout(context.Background(), 30*time.Second)
}

// TearDownTest runs after each test
func (s *DatabaseTestSuite) TearDownTest() {
	s.cancel()
}

// TearDownSuite runs once after all tests
func (s *DatabaseTestSuite) TearDownSuite() {
	s.cleanupTestData()
	s.db.Close()
}

// cleanupTestData removes all test data
func (s *DatabaseTestSuite) cleanupTestData() {
	ctx := context.Background()
	
	// Delete test data in reverse order of dependencies
	queries := []string{
		"DELETE FROM analytics.api_metrics WHERE endpoint LIKE '/test%'",
		"DELETE FROM analytics.user_activity WHERE user_id IN (SELECT id FROM auth.users WHERE email LIKE 'test_%@example.com')",
		"DELETE FROM analytics.technique_effectiveness WHERE technique LIKE 'test_%'",
		"DELETE FROM prompts.embeddings WHERE source_id IN (SELECT id FROM prompts.history WHERE session_id LIKE 'test_%')",
		"DELETE FROM prompts.collection_prompts WHERE collection_id IN (SELECT id FROM prompts.collections WHERE name LIKE 'Test %')",
		"DELETE FROM prompts.collections WHERE name LIKE 'Test %'",
		"DELETE FROM prompts.saved_prompts WHERE user_id IN (SELECT id FROM auth.users WHERE email LIKE 'test_%@example.com')",
		"DELETE FROM prompts.history WHERE session_id LIKE 'test_%'",
		"DELETE FROM prompts.intent_patterns WHERE pattern LIKE 'test %'",
		"DELETE FROM auth.api_keys WHERE name LIKE 'Test %'",
		"DELETE FROM auth.user_preferences WHERE user_id IN (SELECT id FROM auth.users WHERE email LIKE 'test_%@example.com')",
		"DELETE FROM auth.sessions WHERE user_id IN (SELECT id FROM auth.users WHERE email LIKE 'test_%@example.com')",
		"DELETE FROM auth.users WHERE email LIKE 'test_%@example.com'",
	}
	
	for _, query := range queries {
		s.db.ExecContext(ctx, query)
	}
}

// =====================================================
// User Management Tests
// =====================================================

func (s *DatabaseTestSuite) TestUserCRUD() {
	// Create user
	user := &models.User{
		Email:        fmt.Sprintf("test_%s@example.com", uuid.New().String()),
		Username:     fmt.Sprintf("testuser_%s", uuid.New().String()),
		PasswordHash: "$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu",
		FirstName:    sql.NullString{String: "Test", Valid: true},
		LastName:     sql.NullString{String: "User", Valid: true},
		Role:         "user",
		Tier:         "free",
		Preferences:  map[string]interface{}{"theme": "dark"},
		Metadata:     map[string]interface{}{"source": "test"},
	}
	
	err := s.db.CreateUser(s.ctx, user)
	require.NoError(s.T(), err, "Failed to create user")
	require.NotEmpty(s.T(), user.ID, "User ID should be generated")
	
	s.testIDs["userID"] = user.ID
	
	// Get user by email
	fetchedUser, err := s.db.GetUserByEmail(s.ctx, user.Email)
	require.NoError(s.T(), err, "Failed to get user by email")
	assert.Equal(s.T(), user.Email, fetchedUser.Email)
	assert.Equal(s.T(), user.Username, fetchedUser.Username)
	assert.Equal(s.T(), "dark", fetchedUser.Preferences["theme"])
	
	// Get user by ID
	fetchedUserByID, err := s.db.GetUserByID(s.ctx, user.ID)
	require.NoError(s.T(), err, "Failed to get user by ID")
	assert.Equal(s.T(), user.ID, fetchedUserByID.ID)
	
	// Update last login
	err = s.db.UpdateUserLastLogin(s.ctx, user.ID)
	require.NoError(s.T(), err, "Failed to update last login")
	
	// Verify last login was updated
	updatedUser, err := s.db.GetUserByID(s.ctx, user.ID)
	require.NoError(s.T(), err)
	assert.True(s.T(), updatedUser.LastLoginAt.Valid)
	assert.WithinDuration(s.T(), time.Now(), updatedUser.LastLoginAt.Time, 5*time.Second)
}

func (s *DatabaseTestSuite) TestUserLoginAttempts() {
	// Create user
	email := fmt.Sprintf("test_login_%s@example.com", uuid.New().String())
	user := &models.User{
		Email:        email,
		Username:     fmt.Sprintf("testlogin_%s", uuid.New().String()),
		PasswordHash: "$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu",
	}
	
	err := s.db.CreateUser(s.ctx, user)
	require.NoError(s.T(), err)
	
	// Test failed login increments
	attempts, err := s.db.IncrementFailedLogins(s.ctx, email)
	require.NoError(s.T(), err)
	assert.Equal(s.T(), 1, attempts)
	
	attempts, err = s.db.IncrementFailedLogins(s.ctx, email)
	require.NoError(s.T(), err)
	assert.Equal(s.T(), 2, attempts)
	
	// Lock user
	lockUntil := time.Now().Add(30 * time.Minute)
	err = s.db.LockUser(s.ctx, email, lockUntil)
	require.NoError(s.T(), err)
	
	// Verify user is locked
	lockedUser, err := s.db.GetUserByEmail(s.ctx, email)
	require.NoError(s.T(), err)
	assert.True(s.T(), lockedUser.LockedUntil.Valid)
	assert.WithinDuration(s.T(), lockUntil, lockedUser.LockedUntil.Time, time.Second)
}

// =====================================================
// Session Management Tests
// =====================================================

func (s *DatabaseTestSuite) TestSessionCRUD() {
	// First create a user
	user := &models.User{
		Email:        fmt.Sprintf("test_session_%s@example.com", uuid.New().String()),
		Username:     fmt.Sprintf("testsession_%s", uuid.New().String()),
		PasswordHash: "$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu",
	}
	err := s.db.CreateUser(s.ctx, user)
	require.NoError(s.T(), err)
	
	// Create session
	session := &models.Session{
		UserID:           user.ID,
		TokenHash:        fmt.Sprintf("token_hash_%s", uuid.New().String()),
		RefreshTokenHash: fmt.Sprintf("refresh_hash_%s", uuid.New().String()),
		UserAgent:        sql.NullString{String: "TestAgent/1.0", Valid: true},
		IPAddress:        sql.NullString{String: "127.0.0.1", Valid: true},
		ExpiresAt:        time.Now().Add(24 * time.Hour),
	}
	
	err = s.db.CreateSession(s.ctx, session)
	require.NoError(s.T(), err)
	require.NotEmpty(s.T(), session.ID)
	
	// Get session by token
	fetchedSession, err := s.db.GetSessionByTokenHash(s.ctx, session.TokenHash)
	require.NoError(s.T(), err)
	assert.Equal(s.T(), session.UserID, fetchedSession.UserID)
	assert.Equal(s.T(), "TestAgent/1.0", fetchedSession.UserAgent.String)
	
	// Update session activity
	err = s.db.UpdateSessionActivity(s.ctx, session.ID)
	require.NoError(s.T(), err)
	
	// Delete session
	err = s.db.DeleteSession(s.ctx, session.ID)
	require.NoError(s.T(), err)
	
	// Verify session is deleted
	_, err = s.db.GetSessionByTokenHash(s.ctx, session.TokenHash)
	assert.Error(s.T(), err)
}

func (s *DatabaseTestSuite) TestSessionCleanup() {
	// Create expired sessions
	user := &models.User{
		Email:        fmt.Sprintf("test_cleanup_%s@example.com", uuid.New().String()),
		Username:     fmt.Sprintf("testcleanup_%s", uuid.New().String()),
		PasswordHash: "$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu",
	}
	err := s.db.CreateUser(s.ctx, user)
	require.NoError(s.T(), err)
	
	// Create expired session
	expiredSession := &models.Session{
		UserID:           user.ID,
		TokenHash:        fmt.Sprintf("expired_hash_%s", uuid.New().String()),
		RefreshTokenHash: fmt.Sprintf("expired_refresh_%s", uuid.New().String()),
		ExpiresAt:        time.Now().Add(-1 * time.Hour), // Expired
	}
	err = s.db.CreateSession(s.ctx, expiredSession)
	require.NoError(s.T(), err)
	
	// Create valid session
	validSession := &models.Session{
		UserID:           user.ID,
		TokenHash:        fmt.Sprintf("valid_hash_%s", uuid.New().String()),
		RefreshTokenHash: fmt.Sprintf("valid_refresh_%s", uuid.New().String()),
		ExpiresAt:        time.Now().Add(1 * time.Hour),
	}
	err = s.db.CreateSession(s.ctx, validSession)
	require.NoError(s.T(), err)
	
	// Clean expired sessions
	deleted, err := s.db.CleanExpiredSessions(s.ctx)
	require.NoError(s.T(), err)
	assert.GreaterOrEqual(s.T(), deleted, int64(1))
	
	// Verify expired session is gone
	_, err = s.db.GetSessionByTokenHash(s.ctx, expiredSession.TokenHash)
	assert.Error(s.T(), err)
	
	// Verify valid session still exists
	_, err = s.db.GetSessionByTokenHash(s.ctx, validSession.TokenHash)
	assert.NoError(s.T(), err)
}

// =====================================================
// Prompt History Tests
// =====================================================

func (s *DatabaseTestSuite) TestPromptHistoryCRUD() {
	// Create user for history
	user := &models.User{
		Email:        fmt.Sprintf("test_history_%s@example.com", uuid.New().String()),
		Username:     fmt.Sprintf("testhistory_%s", uuid.New().String()),
		PasswordHash: "$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu",
	}
	err := s.db.CreateUser(s.ctx, user)
	require.NoError(s.T(), err)
	
	// Create prompt history
	history := &models.PromptHistory{
		UserID:           sql.NullString{String: user.ID, Valid: true},
		SessionID:        sql.NullString{String: fmt.Sprintf("test_session_%s", uuid.New().String()), Valid: true},
		RequestID:        sql.NullString{String: fmt.Sprintf("test_req_%s", uuid.New().String()), Valid: true},
		OriginalInput:    "Help me write a test",
		EnhancedOutput:   "Let me help you write a comprehensive test...",
		Intent:           sql.NullString{String: "problem_solving", Valid: true},
		IntentConfidence: sql.NullFloat64{Float64: 0.92, Valid: true},
		Complexity:       sql.NullString{String: "moderate", Valid: true},
		TechniquesUsed:   []string{"chain_of_thought", "step_by_step"},
		TechniqueScores:  map[string]float64{"chain_of_thought": 0.85, "step_by_step": 0.90},
		ProcessingTimeMs: sql.NullInt64{Int64: 145, Valid: true},
		TokenCount:       sql.NullInt64{Int64: 256, Valid: true},
		ModelUsed:        sql.NullString{String: "gpt-4", Valid: true},
		Metadata:         map[string]interface{}{"test": true},
	}
	
	err = s.db.SavePromptHistory(s.ctx, history)
	require.NoError(s.T(), err)
	require.NotEmpty(s.T(), history.ID)
	
	// Get prompt history
	histories, err := s.db.GetPromptHistory(s.ctx, user.ID, 10, 0)
	require.NoError(s.T(), err)
	require.Len(s.T(), histories, 1)
	
	fetchedHistory := histories[0]
	assert.Equal(s.T(), history.OriginalInput, fetchedHistory.OriginalInput)
	assert.Equal(s.T(), history.EnhancedOutput, fetchedHistory.EnhancedOutput)
	assert.Equal(s.T(), history.TechniquesUsed, fetchedHistory.TechniquesUsed)
	assert.Equal(s.T(), history.TechniqueScores["chain_of_thought"], fetchedHistory.TechniqueScores["chain_of_thought"])
	
	// Update feedback
	err = s.db.UpdatePromptFeedback(s.ctx, history.ID, 5, "Excellent help!")
	require.NoError(s.T(), err)
	
	// Toggle favorite
	err = s.db.TogglePromptFavorite(s.ctx, history.ID, user.ID)
	require.NoError(s.T(), err)
	
	// Verify updates
	updatedHistories, err := s.db.GetPromptHistory(s.ctx, user.ID, 10, 0)
	require.NoError(s.T(), err)
	require.Len(s.T(), updatedHistories, 1)
	
	updated := updatedHistories[0]
	assert.Equal(s.T(), int64(5), updated.FeedbackScore.Int64)
	assert.Equal(s.T(), "Excellent help!", updated.FeedbackText.String)
	assert.True(s.T(), updated.IsFavorite)
}

// =====================================================
// Technique Effectiveness Tests
// =====================================================

func (s *DatabaseTestSuite) TestTechniqueEffectiveness() {
	technique := fmt.Sprintf("test_%s", uuid.New().String())
	intent := "test_intent"
	
	// Update effectiveness multiple times
	for i := 0; i < 5; i++ {
		score := float64(3 + i%3) // Scores: 3, 4, 5, 3, 4
		err := s.db.UpdateTechniqueEffectiveness(s.ctx, technique, intent, score)
		require.NoError(s.T(), err)
	}
	
	// Get effectiveness
	effectiveness, err := s.db.GetTechniqueEffectiveness(s.ctx, 1)
	require.NoError(s.T(), err)
	
	// Find our test technique
	var found bool
	for _, te := range effectiveness {
		if te.Technique == technique && te.Intent == intent {
			found = true
			assert.Equal(s.T(), 5, te.TotalCount)
			assert.Equal(s.T(), 2, te.SuccessCount) // Only scores >= 4 are success
			assert.InDelta(s.T(), 3.8, te.AverageFeedback.Float64, 0.1)
			break
		}
	}
	assert.True(s.T(), found, "Test technique effectiveness not found")
}

// =====================================================
// Analytics Tests
// =====================================================

func (s *DatabaseTestSuite) TestUserActivity() {
	// Create user
	user := &models.User{
		Email:        fmt.Sprintf("test_activity_%s@example.com", uuid.New().String()),
		Username:     fmt.Sprintf("testactivity_%s", uuid.New().String()),
		PasswordHash: "$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu",
	}
	err := s.db.CreateUser(s.ctx, user)
	require.NoError(s.T(), err)
	
	// Record activity
	activity := &models.UserActivity{
		UserID:    user.ID,
		Type:      "prompt_enhanced",
		Data:      map[string]interface{}{"technique": "chain_of_thought", "success": true},
		SessionID: sql.NullString{String: "test_session", Valid: true},
		IPAddress: sql.NullString{String: "127.0.0.1", Valid: true},
		UserAgent: sql.NullString{String: "TestAgent/1.0", Valid: true},
	}
	
	err = s.db.RecordUserActivity(s.ctx, activity)
	require.NoError(s.T(), err)
	require.NotEmpty(s.T(), activity.ID)
}

func (s *DatabaseTestSuite) TestDailyStats() {
	// This would typically be run as a scheduled job
	err := s.db.UpdateDailyStats(s.ctx)
	require.NoError(s.T(), err)
	
	// Get stats
	stats, err := s.db.GetDailyStats(s.ctx, 7)
	require.NoError(s.T(), err)
	
	// Should have at least today's stats
	assert.GreaterOrEqual(s.T(), len(stats), 1)
}

// =====================================================
// User Preferences Tests
// =====================================================

func (s *DatabaseTestSuite) TestUserPreferences() {
	// Create user
	user := &models.User{
		Email:        fmt.Sprintf("test_prefs_%s@example.com", uuid.New().String()),
		Username:     fmt.Sprintf("testprefs_%s", uuid.New().String()),
		PasswordHash: "$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu",
	}
	err := s.db.CreateUser(s.ctx, user)
	require.NoError(s.T(), err)
	
	// Get default preferences
	prefs, err := s.db.GetUserPreferences(s.ctx, user.ID)
	require.NoError(s.T(), err)
	assert.Equal(s.T(), "light", prefs.UITheme)
	assert.Equal(s.T(), "en", prefs.UILanguage)
	assert.True(s.T(), prefs.EmailNotifications)
	
	// Update preferences
	prefs.PreferredTechniques = []string{"chain_of_thought", "few_shot"}
	prefs.ExcludedTechniques = []string{"emotional_appeal"}
	prefs.ComplexityPreference = sql.NullString{String: "advanced", Valid: true}
	prefs.UITheme = "dark"
	prefs.CustomSettings = map[string]interface{}{"show_tips": true}
	
	err = s.db.UpdateUserPreferences(s.ctx, prefs)
	require.NoError(s.T(), err)
	
	// Verify update
	updatedPrefs, err := s.db.GetUserPreferences(s.ctx, user.ID)
	require.NoError(s.T(), err)
	assert.Equal(s.T(), "dark", updatedPrefs.UITheme)
	assert.Equal(s.T(), []string{"chain_of_thought", "few_shot"}, updatedPrefs.PreferredTechniques)
	assert.Equal(s.T(), []string{"emotional_appeal"}, updatedPrefs.ExcludedTechniques)
	assert.Equal(s.T(), "advanced", updatedPrefs.ComplexityPreference.String)
	assert.Equal(s.T(), true, updatedPrefs.CustomSettings["show_tips"])
}

// =====================================================
// Saved Prompts and Collections Tests
// =====================================================

func (s *DatabaseTestSuite) TestSavedPromptsAndCollections() {
	// Create user
	user := &models.User{
		Email:        fmt.Sprintf("test_saved_%s@example.com", uuid.New().String()),
		Username:     fmt.Sprintf("testsaved_%s", uuid.New().String()),
		PasswordHash: "$2a$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu",
	}
	err := s.db.CreateUser(s.ctx, user)
	require.NoError(s.T(), err)
	
	// Create prompt history first
	history := &models.PromptHistory{
		UserID:         sql.NullString{String: user.ID, Valid: true},
		SessionID:      sql.NullString{String: "test_session", Valid: true},
		OriginalInput:  "Test prompt",
		EnhancedOutput: "Enhanced test prompt",
		TechniquesUsed: []string{"test_technique"},
	}
	err = s.db.SavePromptHistory(s.ctx, history)
	require.NoError(s.T(), err)
	
	// Save prompt
	saved := &models.SavedPrompt{
		UserID:      user.ID,
		HistoryID:   sql.NullString{String: history.ID, Valid: true},
		Title:       "Test Saved Prompt",
		Description: sql.NullString{String: "A test prompt", Valid: true},
		Tags:        []string{"test", "example"},
		IsPublic:    true,
	}
	
	err = s.db.SavePrompt(s.ctx, saved)
	require.NoError(s.T(), err)
	require.NotEmpty(s.T(), saved.ID)
	require.NotEmpty(s.T(), saved.ShareToken.String)
	
	// Create collection
	collection := &models.Collection{
		UserID:      user.ID,
		Name:        "Test Collection",
		Description: sql.NullString{String: "Test collection description", Valid: true},
		Color:       sql.NullString{String: "#3B82F6", Valid: true},
		Icon:        sql.NullString{String: "folder", Valid: true},
		IsPublic:    false,
	}
	
	err = s.db.CreateCollection(s.ctx, collection)
	require.NoError(s.T(), err)
	require.NotEmpty(s.T(), collection.ID)
	
	// Add prompt to collection
	err = s.db.AddPromptToCollection(s.ctx, collection.ID, saved.ID, 1)
	require.NoError(s.T(), err)
	
	// Get saved prompts
	prompts, err := s.db.GetSavedPrompts(s.ctx, user.ID, 10, 0)
	require.NoError(s.T(), err)
	require.Len(s.T(), prompts, 1)
	
	fetchedPrompt := prompts[0]
	assert.Equal(s.T(), saved.Title, fetchedPrompt.Title)
	assert.Equal(s.T(), saved.Tags, fetchedPrompt.Tags)
	assert.Equal(s.T(), history.OriginalInput, fetchedPrompt.OriginalInput)
	assert.Equal(s.T(), history.EnhancedOutput, fetchedPrompt.EnhancedOutput)
}

// Run the test suite
func TestDatabaseSuite(t *testing.T) {
	suite.Run(t, new(DatabaseTestSuite))
}