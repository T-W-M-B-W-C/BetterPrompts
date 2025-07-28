package handlers_test

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/betterprompts/api-gateway/internal/handlers"
	"github.com/betterprompts/api-gateway/internal/models"
	"github.com/betterprompts/api-gateway/internal/services"
	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// MockDatabaseForHistory for history handler tests
type MockDatabaseForHistory struct {
	mock.Mock
}

func (m *MockDatabaseForHistory) GetPromptHistory(ctx context.Context, id string) (*models.PromptHistory, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.PromptHistory), args.Error(1)
}

func (m *MockDatabaseForHistory) SavePromptHistory(ctx context.Context, entry models.PromptHistory) (string, error) {
	args := m.Called(ctx, entry)
	return args.String(0), args.Error(1)
}

func (m *MockDatabaseForHistory) GetUserPromptHistoryWithFilters(ctx context.Context, userID string, req models.PaginationRequest) ([]*models.PromptHistory, int64, error) {
	args := m.Called(ctx, userID, req)
	if args.Get(0) == nil {
		return nil, args.Get(1).(int64), args.Error(2)
	}
	return args.Get(0).([]*models.PromptHistory), args.Get(1).(int64), args.Error(2)
}

func (m *MockDatabaseForHistory) GetUserPromptHistory(ctx context.Context, userID string, limit, offset int) ([]models.PromptHistory, error) {
	args := m.Called(ctx, userID, limit, offset)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]models.PromptHistory), args.Error(1)
}

func (m *MockDatabaseForHistory) DeletePromptHistory(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockDatabaseForHistory) Ping() error {
	args := m.Called()
	return args.Error(0)
}

// Ensure MockDatabaseForHistory implements DatabaseInterface
var _ services.DatabaseInterface = (*MockDatabaseForHistory)(nil)


// Test GetPromptHistory handler
func TestGetPromptHistory(t *testing.T) {
	gin.SetMode(gin.TestMode)
	logger := logrus.New()

	tests := []struct {
		name           string
		userID         string
		queryParams    map[string]string
		mockHistory    []*models.PromptHistory
		mockTotal      int64
		mockError      error
		expectedStatus int
		expectedError  string
		checkResponse  func(*testing.T, []byte)
	}{
		{
			name:   "successful retrieval with default pagination",
			userID: "test-user-id",
			queryParams: map[string]string{},
			mockHistory: []*models.PromptHistory{
				{
					ID:             "prompt-1",
					OriginalInput:  "test input 1",
					EnhancedOutput: "enhanced output 1",
					TechniquesUsed: []string{"chain_of_thought"},
					CreatedAt:      time.Now(),
				},
				{
					ID:             "prompt-2",
					OriginalInput:  "test input 2",
					EnhancedOutput: "enhanced output 2",
					TechniquesUsed: []string{"step_by_step"},
					CreatedAt:      time.Now().Add(-1 * time.Hour),
				},
			},
			mockTotal:      2,
			mockError:      nil,
			expectedStatus: http.StatusOK,
			checkResponse: func(t *testing.T, body []byte) {
				var response models.PaginatedResponseWithMeta
				err := json.Unmarshal(body, &response)
				assert.NoError(t, err)
				assert.Equal(t, 1, response.Pagination.Page)
				assert.Equal(t, 20, response.Pagination.Limit)
				assert.Equal(t, int64(2), response.Pagination.TotalRecords)
				assert.Equal(t, 1, response.Pagination.TotalPages)
				assert.False(t, response.Pagination.HasPrevious)
				assert.False(t, response.Pagination.HasNext)
				
				// Check data
				data, ok := response.Data.([]interface{})
				assert.True(t, ok)
				assert.Len(t, data, 2)
			},
		},
		{
			name:   "successful retrieval with search filter",
			userID: "test-user-id",
			queryParams: map[string]string{
				"search": "python",
				"page":   "1",
				"limit":  "10",
			},
			mockHistory: []*models.PromptHistory{
				{
					ID:             "prompt-1",
					OriginalInput:  "python function",
					EnhancedOutput: "enhanced python output",
					TechniquesUsed: []string{"chain_of_thought"},
					CreatedAt:      time.Now(),
				},
			},
			mockTotal:      1,
			mockError:      nil,
			expectedStatus: http.StatusOK,
			checkResponse: func(t *testing.T, body []byte) {
				var response models.PaginatedResponseWithMeta
				err := json.Unmarshal(body, &response)
				assert.NoError(t, err)
				assert.Equal(t, int64(1), response.Pagination.TotalRecords)
			},
		},
		{
			name:   "successful retrieval with technique filter",
			userID: "test-user-id",
			queryParams: map[string]string{
				"technique": "chain_of_thought",
			},
			mockHistory: []*models.PromptHistory{
				{
					ID:             "prompt-1",
					OriginalInput:  "test input",
					EnhancedOutput: "enhanced output",
					TechniquesUsed: []string{"chain_of_thought"},
					CreatedAt:      time.Now(),
				},
			},
			mockTotal:      1,
			mockError:      nil,
			expectedStatus: http.StatusOK,
		},
		{
			name:   "successful retrieval with date range",
			userID: "test-user-id",
			queryParams: map[string]string{
				"date_from": time.Now().Add(-24 * time.Hour).Format(time.RFC3339),
				"date_to":   time.Now().Format(time.RFC3339),
			},
			mockHistory:    []*models.PromptHistory{},
			mockTotal:      0,
			mockError:      nil,
			expectedStatus: http.StatusOK,
		},
		{
			name:           "database error",
			userID:         "test-user-id",
			queryParams:    map[string]string{},
			mockHistory:    nil,
			mockTotal:      0,
			mockError:      errors.New("database connection failed"),
			expectedStatus: http.StatusInternalServerError,
			expectedError:  "failed to retrieve history",
		},
		{
			name:   "pagination page 2",
			userID: "test-user-id",
			queryParams: map[string]string{
				"page":  "2",
				"limit": "5",
			},
			mockHistory:    []*models.PromptHistory{},
			mockTotal:      10,
			mockError:      nil,
			expectedStatus: http.StatusOK,
			checkResponse: func(t *testing.T, body []byte) {
				var response models.PaginatedResponseWithMeta
				err := json.Unmarshal(body, &response)
				assert.NoError(t, err)
				assert.Equal(t, 2, response.Pagination.Page)
				assert.Equal(t, 5, response.Pagination.Limit)
				assert.Equal(t, int64(10), response.Pagination.TotalRecords)
				assert.Equal(t, 2, response.Pagination.TotalPages)
				assert.True(t, response.Pagination.HasPrevious)
				assert.False(t, response.Pagination.HasNext)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create mock database
			mockDB := new(MockDatabaseForHistory)
			
			// Setup expectation based on query params
			expectedReq := models.ParsePaginationRequest(createTestContext(tt.queryParams))
			mockDB.On("GetUserPromptHistoryWithFilters", mock.Anything, tt.userID, mock.MatchedBy(func(req models.PaginationRequest) bool {
				// Match the important fields
				return req.Page == expectedReq.Page &&
					req.Limit == expectedReq.Limit &&
					req.Search == expectedReq.Search &&
					req.Technique == expectedReq.Technique
			})).Return(tt.mockHistory, tt.mockTotal, tt.mockError)

			// Create service clients with mock
			clients := &services.ServiceClients{
				Database: mockDB,
			}

			// Create test context
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			
			// Build request with query params
			req := httptest.NewRequest("GET", "/api/v1/prompts/history", nil)
			q := req.URL.Query()
			for key, value := range tt.queryParams {
				q.Add(key, value)
			}
			req.URL.RawQuery = q.Encode()
			c.Request = req
			
			c.Set("user_id", tt.userID)
			c.Set("logger", logger.WithField("test", true))

			// Call handler
			handler := handlers.GetPromptHistory(clients)
			handler(c)

			// Check response
			assert.Equal(t, tt.expectedStatus, w.Code)

			if tt.expectedError != "" {
				var response map[string]string
				err := json.Unmarshal(w.Body.Bytes(), &response)
				assert.NoError(t, err)
				assert.Contains(t, response["error"], tt.expectedError)
			} else if tt.checkResponse != nil {
				tt.checkResponse(t, w.Body.Bytes())
			}

			mockDB.AssertExpectations(t)
		})
	}
}

// Test unauthorized access
func TestGetPromptHistoryUnauthorized(t *testing.T) {
	gin.SetMode(gin.TestMode)
	logger := logrus.New()

	// Create mock database
	mockDB := new(MockDatabaseForHistory)
	clients := &services.ServiceClients{
		Database: mockDB,
	}

	// Create test context without user_id
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest("GET", "/api/v1/prompts/history", nil)
	c.Set("logger", logger.WithField("test", true))

	// Call handler
	handler := handlers.GetPromptHistory(clients)
	handler(c)

	// Check response
	assert.Equal(t, http.StatusUnauthorized, w.Code)
	
	var response map[string]string
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "unauthorized", response["error"])
}

// Helper function to create test context with query params
func createTestContext(queryParams map[string]string) *gin.Context {
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	
	req := httptest.NewRequest("GET", "/api/v1/prompts/history", nil)
	q := req.URL.Query()
	for key, value := range queryParams {
		q.Add(key, value)
	}
	req.URL.RawQuery = q.Encode()
	c.Request = req
	
	return c
}