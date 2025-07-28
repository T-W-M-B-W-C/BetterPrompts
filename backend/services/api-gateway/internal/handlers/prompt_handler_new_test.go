package handlers_test

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/betterprompts/api-gateway/internal/handlers"
	"github.com/betterprompts/api-gateway/internal/models"
	"github.com/betterprompts/api-gateway/internal/services"
	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// MockDatabase for prompt handler tests
type MockDatabaseForPrompt struct {
	mock.Mock
}

func (m *MockDatabaseForPrompt) GetPromptHistory(ctx context.Context, id string) (*models.PromptHistory, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.PromptHistory), args.Error(1)
}

func (m *MockDatabaseForPrompt) SavePromptHistory(ctx context.Context, entry models.PromptHistory) (string, error) {
	args := m.Called(ctx, entry)
	return args.String(0), args.Error(1)
}

func (m *MockDatabaseForPrompt) GetUserPromptHistoryWithFilters(ctx context.Context, userID string, req models.PaginationRequest) ([]*models.PromptHistory, int64, error) {
	args := m.Called(ctx, userID, req)
	if args.Get(0) == nil {
		return nil, args.Get(1).(int64), args.Error(2)
	}
	return args.Get(0).([]*models.PromptHistory), args.Get(1).(int64), args.Error(2)
}

func (m *MockDatabaseForPrompt) GetUserPromptHistory(ctx context.Context, userID string, limit, offset int) ([]models.PromptHistory, error) {
	args := m.Called(ctx, userID, limit, offset)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]models.PromptHistory), args.Error(1)
}

func (m *MockDatabaseForPrompt) DeletePromptHistory(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockDatabaseForPrompt) Ping() error {
	args := m.Called()
	return args.Error(0)
}

// Ensure MockDatabaseForPrompt implements DatabaseInterface
var _ services.DatabaseInterface = (*MockDatabaseForPrompt)(nil)

// MockIntentClassifierForPrompt is a mock implementation of the intent classifier
type MockIntentClassifierForPrompt struct {
	mock.Mock
}

func (m *MockIntentClassifierForPrompt) ClassifyIntent(ctx context.Context, text string) (*services.IntentClassificationResult, error) {
	args := m.Called(ctx, text)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*services.IntentClassificationResult), args.Error(1)
}

// MockTechniqueSelectorForPrompt is a mock implementation of the technique selector
type MockTechniqueSelectorForPrompt struct {
	mock.Mock
}

func (m *MockTechniqueSelectorForPrompt) SelectTechniques(ctx context.Context, req models.TechniqueSelectionRequest) ([]string, error) {
	args := m.Called(ctx, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]string), args.Error(1)
}

// MockPromptGeneratorForPrompt is a mock implementation of the prompt generator
type MockPromptGeneratorForPrompt struct {
	mock.Mock
}

func (m *MockPromptGeneratorForPrompt) GeneratePrompt(ctx context.Context, req models.PromptGenerationRequest) (*models.PromptGenerationResponse, error) {
	args := m.Called(ctx, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.PromptGenerationResponse), args.Error(1)
}

// Test GetPromptByID handler
func TestGetPromptByID(t *testing.T) {
	gin.SetMode(gin.TestMode)
	logger := logrus.New()

	tests := []struct {
		name           string
		promptID       string
		userID         string
		mockPrompt     *models.PromptHistory
		mockError      error
		expectedStatus int
		expectedError  string
	}{
		{
			name:     "successful retrieval",
			promptID: "test-prompt-id",
			userID:   "test-user-id",
			mockPrompt: &models.PromptHistory{
				ID:             "test-prompt-id",
				UserID:         sql.NullString{String: "test-user-id", Valid: true},
				OriginalInput:  "test input",
				EnhancedOutput: "enhanced output",
				TechniquesUsed: []string{"chain_of_thought"},
			},
			mockError:      nil,
			expectedStatus: http.StatusOK,
		},
		{
			name:           "prompt not found",
			promptID:       "non-existent-id",
			userID:         "test-user-id",
			mockPrompt:     nil,
			mockError:      errors.New("prompt history not found"),
			expectedStatus: http.StatusNotFound,
			expectedError:  "prompt not found",
		},
		{
			name:     "access denied - different user",
			promptID: "test-prompt-id",
			userID:   "test-user-id",
			mockPrompt: &models.PromptHistory{
				ID:     "test-prompt-id",
				UserID: sql.NullString{String: "different-user-id", Valid: true},
			},
			mockError:      nil,
			expectedStatus: http.StatusForbidden,
			expectedError:  "access denied",
		},
		{
			name:           "empty prompt ID",
			promptID:       "",
			userID:         "test-user-id",
			expectedStatus: http.StatusBadRequest,
			expectedError:  "prompt ID required",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create mock database
			mockDB := new(MockDatabaseForPrompt)
			if tt.promptID != "" && tt.name != "empty prompt ID" {
				mockDB.On("GetPromptHistory", mock.Anything, tt.promptID).Return(tt.mockPrompt, tt.mockError)
			}

			// Create service clients with mock
			clients := &services.ServiceClients{
				Database: mockDB,
			}

			// Create test context
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest("GET", "/api/v1/prompts/"+tt.promptID, nil)
			c.Params = gin.Params{{Key: "id", Value: tt.promptID}}
			c.Set("user_id", tt.userID)
			c.Set("logger", logger.WithField("test", true))

			// Call handler
			handler := handlers.GetPromptByID(clients)
			handler(c)

			// Check response
			assert.Equal(t, tt.expectedStatus, w.Code)

			if tt.expectedError != "" {
				var response map[string]string
				err := json.Unmarshal(w.Body.Bytes(), &response)
				assert.NoError(t, err)
				assert.Contains(t, response["error"], tt.expectedError)
			} else if tt.expectedStatus == http.StatusOK {
				var response models.PromptHistory
				err := json.Unmarshal(w.Body.Bytes(), &response)
				assert.NoError(t, err)
				assert.Equal(t, tt.mockPrompt.ID, response.ID)
			}

			mockDB.AssertExpectations(t)
		})
	}
}

// Test RerunPrompt handler
func TestRerunPrompt(t *testing.T) {
	gin.SetMode(gin.TestMode)
	logger := logrus.New()

	tests := []struct {
		name                 string
		promptID             string
		userID               string
		mockPrompt           *models.PromptHistory
		mockGetError         error
		mockClassifyResult   *services.IntentClassificationResult
		mockClassifyError    error
		mockTechniques       []string
		mockTechniqueError   error
		mockGenerateResult   *models.PromptGenerationResponse
		mockGenerateError    error
		mockSaveID           string
		mockSaveError        error
		expectedStatus       int
		expectedError        string
	}{
		{
			name:     "successful rerun",
			promptID: "test-prompt-id",
			userID:   "test-user-id",
			mockPrompt: &models.PromptHistory{
				ID:             "test-prompt-id",
				UserID:         sql.NullString{String: "test-user-id", Valid: true},
				OriginalInput:  "test input",
				TechniquesUsed: []string{"chain_of_thought"},
				Intent:         sql.NullString{String: "reasoning", Valid: true},
				Complexity:     sql.NullString{String: "medium", Valid: true},
				IntentConfidence: sql.NullFloat64{Float64: 0.95, Valid: true},
			},
			mockClassifyResult: &services.IntentClassificationResult{
				Intent:     "reasoning",
				Confidence: 0.95,
				Complexity: "medium",
			},
			mockTechniques: []string{"chain_of_thought"},
			mockGenerateResult: &models.PromptGenerationResponse{
				Text:         "enhanced prompt",
				ModelVersion: "v1",
				TokensUsed:   100,
			},
			mockSaveID:     "new-prompt-id",
			expectedStatus: http.StatusOK,
		},
		{
			name:           "prompt not found",
			promptID:       "non-existent-id",
			userID:         "test-user-id",
			mockGetError:   errors.New("prompt history not found"),
			expectedStatus: http.StatusNotFound,
			expectedError:  "prompt not found",
		},
		{
			name:     "access denied",
			promptID: "test-prompt-id",
			userID:   "test-user-id",
			mockPrompt: &models.PromptHistory{
				ID:     "test-prompt-id",
				UserID: sql.NullString{String: "different-user-id", Valid: true},
			},
			expectedStatus: http.StatusForbidden,
			expectedError:  "access denied",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create mocks
			mockDB := new(MockDatabaseForPrompt)
			mockIntent := new(MockIntentClassifierForPrompt)
			mockTechnique := new(MockTechniqueSelectorForPrompt) 
			mockGenerator := new(MockPromptGeneratorForPrompt)

			// Setup mock expectations
			if tt.promptID != "" {
				mockDB.On("GetPromptHistory", mock.Anything, tt.promptID).Return(tt.mockPrompt, tt.mockGetError)
			}

			if tt.mockPrompt != nil && tt.mockPrompt.UserID.Valid && tt.mockPrompt.UserID.String == tt.userID {
				if tt.mockClassifyResult != nil {
					mockIntent.On("ClassifyIntent", mock.Anything, tt.mockPrompt.OriginalInput).
						Return(tt.mockClassifyResult, tt.mockClassifyError)
				}

				if tt.mockTechniques != nil {
					mockTechnique.On("SelectTechniques", mock.Anything, mock.Anything).
						Return(tt.mockTechniques, tt.mockTechniqueError)
				}

				if tt.mockGenerateResult != nil {
					mockGenerator.On("GeneratePrompt", mock.Anything, mock.Anything).
						Return(tt.mockGenerateResult, tt.mockGenerateError)
				}

				if tt.mockSaveID != "" {
					mockDB.On("SavePromptHistory", mock.Anything, mock.Anything).
						Return(tt.mockSaveID, tt.mockSaveError)
				}
			}

			// Create service clients
			clients := &services.ServiceClients{
				Database:          mockDB,
				IntentClassifier:  mockIntent,
				TechniqueSelector: mockTechnique,
				PromptGenerator:   mockGenerator,
			}

			// Create test context
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest("POST", "/api/v1/prompts/"+tt.promptID+"/rerun", nil)
			c.Params = gin.Params{{Key: "id", Value: tt.promptID}}
			c.Set("user_id", tt.userID)
			c.Set("logger", logger.WithField("test", true))
			c.Set("request_id", "test-request-id")

			// Call handler
			handler := handlers.RerunPrompt(clients)
			handler(c)

			// Check response
			assert.Equal(t, tt.expectedStatus, w.Code)

			if tt.expectedError != "" {
				var response map[string]string
				err := json.Unmarshal(w.Body.Bytes(), &response)
				assert.NoError(t, err)
				assert.Contains(t, response["error"], tt.expectedError)
			} else if tt.expectedStatus == http.StatusOK {
				var response map[string]interface{}
				err := json.Unmarshal(w.Body.Bytes(), &response)
				assert.NoError(t, err)
				assert.Equal(t, tt.mockSaveID, response["id"])
				assert.Equal(t, tt.mockGenerateResult.Text, response["enhanced_text"])
				assert.Equal(t, true, response["enhanced"])
			}

			// Verify mocks
			mockDB.AssertExpectations(t)
			mockIntent.AssertExpectations(t)
			mockTechnique.AssertExpectations(t)
			mockGenerator.AssertExpectations(t)
		})
	}
}

