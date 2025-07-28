// +build integration

package handlers_test

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/betterprompts/api-gateway/internal/auth"
	"github.com/betterprompts/api-gateway/internal/handlers"
	"github.com/betterprompts/api-gateway/internal/middleware"
	"github.com/betterprompts/api-gateway/internal/models"
	"github.com/betterprompts/api-gateway/internal/services"
	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/stretchr/testify/mock"
)

// MockDatabaseForIntegration for integration tests
type MockDatabaseForIntegration struct {
	mock.Mock
}

func (m *MockDatabaseForIntegration) GetPromptHistory(ctx context.Context, id string) (*models.PromptHistory, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.PromptHistory), args.Error(1)
}

func (m *MockDatabaseForIntegration) SavePromptHistory(ctx context.Context, entry models.PromptHistory) (string, error) {
	args := m.Called(ctx, entry)
	return args.String(0), args.Error(1)
}

func (m *MockDatabaseForIntegration) GetUserPromptHistoryWithFilters(ctx context.Context, userID string, req models.PaginationRequest) ([]*models.PromptHistory, int64, error) {
	args := m.Called(ctx, userID, req)
	if args.Get(0) == nil {
		return nil, args.Get(1).(int64), args.Error(2)
	}
	return args.Get(0).([]*models.PromptHistory), args.Get(1).(int64), args.Error(2)
}

func (m *MockDatabaseForIntegration) GetUserPromptHistory(ctx context.Context, userID string, limit, offset int) ([]models.PromptHistory, error) {
	args := m.Called(ctx, userID, limit, offset)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]models.PromptHistory), args.Error(1)
}

func (m *MockDatabaseForIntegration) DeletePromptHistory(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockDatabaseForIntegration) Ping() error {
	args := m.Called()
	return args.Error(0)
}

// MockIntentClassifierForIntegration is a mock implementation of the intent classifier
type MockIntentClassifierForIntegration struct {
	mock.Mock
}

func (m *MockIntentClassifierForIntegration) ClassifyIntent(ctx context.Context, text string) (*services.IntentClassificationResult, error) {
	args := m.Called(ctx, text)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*services.IntentClassificationResult), args.Error(1)
}

// MockTechniqueSelectorForIntegration is a mock implementation of the technique selector
type MockTechniqueSelectorForIntegration struct {
	mock.Mock
}

func (m *MockTechniqueSelectorForIntegration) SelectTechniques(ctx context.Context, req models.TechniqueSelectionRequest) ([]string, error) {
	args := m.Called(ctx, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]string), args.Error(1)
}

// MockPromptGeneratorForIntegration is a mock implementation of the prompt generator
type MockPromptGeneratorForIntegration struct {
	mock.Mock
}

func (m *MockPromptGeneratorForIntegration) GeneratePrompt(ctx context.Context, req models.PromptGenerationRequest) (*models.PromptGenerationResponse, error) {
	args := m.Called(ctx, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.PromptGenerationResponse), args.Error(1)
}

// setupTestRouter creates a test router with all the prompt history endpoints
func setupTestRouter(clients *services.ServiceClients, jwtManager *auth.JWTManager) *gin.Engine {
	gin.SetMode(gin.TestMode)
	router := gin.New()
	logger := logrus.New()

	// Add middleware
	router.Use(middleware.RequestID())
	router.Use(middleware.Logger(logger))

	// Protected routes
	protected := router.Group("/api/v1")
	protected.Use(middleware.AuthMiddleware(jwtManager, logger))
	{
		protected.GET("/prompts/history", handlers.GetPromptHistory(clients))
		protected.GET("/prompts/:id", handlers.GetPromptByID(clients))
		protected.POST("/prompts/:id/rerun", handlers.RerunPrompt(clients))
	}

	return router
}

// createTestJWT creates a test JWT token for authentication
func createTestJWT(userID string, jwtManager *auth.JWTManager) (string, error) {
	claims := jwt.MapClaims{
		"user_id": userID,
		"email":   "test@example.com",
		"exp":     time.Now().Add(time.Hour).Unix(),
		"iat":     time.Now().Unix(),
		"iss":     "betterprompts",
	}
	
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(jwtManager.Config.SecretKey))
}

// TestPromptHistoryEndpointsIntegration tests the full flow of prompt history endpoints
func TestPromptHistoryEndpointsIntegration(t *testing.T) {
	// Skip if not running integration tests
	if testing.Short() {
		t.Skip("Skipping integration test")
	}

	// Setup test database (in-memory or test database)
	// Note: This assumes you have a test database setup function
	// db := setupTestDatabase(t)
	// defer db.Close()

	// For this example, we'll use mocks
	mockDB := new(MockDatabaseForIntegration)
	mockIntent := new(MockIntentClassifierForIntegration)
	mockTechnique := new(MockTechniqueSelectorForIntegration)
	mockGenerator := new(MockPromptGeneratorForIntegration)

	clients := &services.ServiceClients{
		Database:          mockDB,
		IntentClassifier:  mockIntent,
		TechniqueSelector: mockTechnique,
		PromptGenerator:   mockGenerator,
	}

	// Setup JWT manager
	jwtConfig := auth.JWTConfig{
		SecretKey:        "test-secret-key",
		RefreshSecretKey: "test-refresh-key",
		Issuer:          "betterprompts",
	}
	jwtManager := auth.NewJWTManager(jwtConfig)

	// Setup router
	router := setupTestRouter(clients, jwtManager)

	// Test user
	userID := "test-user-id"
	token, err := createTestJWT(userID, jwtManager)
	require.NoError(t, err)

	t.Run("GET /api/v1/prompts/history", func(t *testing.T) {
		// Mock data
		mockHistory := []*models.PromptHistory{
			{
				ID:             "prompt-1",
				UserID:         sql.NullString{String: userID, Valid: true},
				OriginalInput:  "test input 1",
				EnhancedOutput: "enhanced output 1",
				TechniquesUsed: []string{"chain_of_thought"},
				CreatedAt:      time.Now(),
			},
			{
				ID:             "prompt-2",
				UserID:         sql.NullString{String: userID, Valid: true},
				OriginalInput:  "test input 2",
				EnhancedOutput: "enhanced output 2",
				TechniquesUsed: []string{"step_by_step"},
				CreatedAt:      time.Now().Add(-1 * time.Hour),
			},
		}

		// Setup mock expectation
		mockDB.On("GetUserPromptHistoryWithFilters", mock.Anything, userID, mock.Anything).
			Return(mockHistory, int64(2), nil)

		// Make request
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/api/v1/prompts/history?page=1&limit=10", nil)
		req.Header.Set("Authorization", "Bearer "+token)
		router.ServeHTTP(w, req)

		// Check response
		assert.Equal(t, http.StatusOK, w.Code)

		var response models.PaginatedResponseWithMeta
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Equal(t, int64(2), response.Pagination.TotalRecords)
	})

	t.Run("GET /api/v1/prompts/:id", func(t *testing.T) {
		promptID := "prompt-1"
		mockPrompt := &models.PromptHistory{
			ID:             promptID,
			UserID:         sql.NullString{String: userID, Valid: true},
			OriginalInput:  "test input",
			EnhancedOutput: "enhanced output",
			TechniquesUsed: []string{"chain_of_thought"},
			CreatedAt:      time.Now(),
		}

		// Setup mock expectation
		mockDB.On("GetPromptHistory", mock.Anything, promptID).Return(mockPrompt, nil)

		// Make request
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/api/v1/prompts/"+promptID, nil)
		req.Header.Set("Authorization", "Bearer "+token)
		router.ServeHTTP(w, req)

		// Check response
		assert.Equal(t, http.StatusOK, w.Code)

		var response models.PromptHistory
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Equal(t, promptID, response.ID)
	})

	t.Run("POST /api/v1/prompts/:id/rerun", func(t *testing.T) {
		promptID := "prompt-1"
		newPromptID := "new-prompt-id"

		mockPrompt := &models.PromptHistory{
			ID:               promptID,
			UserID:           sql.NullString{String: userID, Valid: true},
			OriginalInput:    "test input",
			TechniquesUsed:   []string{"chain_of_thought"},
			Intent:           sql.NullString{String: "reasoning", Valid: true},
			Complexity:       sql.NullString{String: "medium", Valid: true},
			IntentConfidence: sql.NullFloat64{Float64: 0.95, Valid: true},
		}

		// Setup mock expectations
		mockDB.On("GetPromptHistory", mock.Anything, promptID).Return(mockPrompt, nil)
		mockDB.On("SavePromptHistory", mock.Anything, mock.Anything).Return(newPromptID, nil)

		mockTechnique.On("SelectTechniques", mock.Anything, mock.Anything).
			Return([]string{"chain_of_thought"}, nil)

		mockGenerator.On("GeneratePrompt", mock.Anything, mock.Anything).
			Return(&models.PromptGenerationResponse{
				Text:         "enhanced prompt",
				ModelVersion: "v1",
				TokensUsed:   100,
			}, nil)

		// Make request
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/api/v1/prompts/"+promptID+"/rerun", nil)
		req.Header.Set("Authorization", "Bearer "+token)
		router.ServeHTTP(w, req)

		// Check response
		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Equal(t, newPromptID, response["id"])
		assert.Equal(t, "enhanced prompt", response["enhanced_text"])
		assert.Equal(t, true, response["enhanced"])
		
		metadata, ok := response["metadata"].(map[string]interface{})
		assert.True(t, ok)
		assert.Equal(t, promptID, metadata["rerun_from"])
	})

	t.Run("Unauthorized access", func(t *testing.T) {
		// Make request without token
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/api/v1/prompts/history", nil)
		router.ServeHTTP(w, req)

		// Check response
		assert.Equal(t, http.StatusUnauthorized, w.Code)
	})

	t.Run("Access denied for other user's prompt", func(t *testing.T) {
		promptID := "other-user-prompt"
		mockPrompt := &models.PromptHistory{
			ID:             promptID,
			UserID:         sql.NullString{String: "other-user-id", Valid: true},
			OriginalInput:  "test input",
			EnhancedOutput: "enhanced output",
		}

		// Setup mock expectation
		mockDB.On("GetPromptHistory", mock.Anything, promptID).Return(mockPrompt, nil)

		// Make request
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/api/v1/prompts/"+promptID, nil)
		req.Header.Set("Authorization", "Bearer "+token)
		router.ServeHTTP(w, req)

		// Check response
		assert.Equal(t, http.StatusForbidden, w.Code)

		var response map[string]string
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Equal(t, "access denied", response["error"])
	})
}

