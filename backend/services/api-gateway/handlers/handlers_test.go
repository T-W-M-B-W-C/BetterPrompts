package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// Mock service client
type MockServiceClient struct {
	mock.Mock
}

func (m *MockServiceClient) ClassifyIntent(request map[string]interface{}) (map[string]interface{}, error) {
	args := m.Called(request)
	return args.Get(0).(map[string]interface{}), args.Error(1)
}

func (m *MockServiceClient) SelectTechniques(request map[string]interface{}) (map[string]interface{}, error) {
	args := m.Called(request)
	return args.Get(0).(map[string]interface{}), args.Error(1)
}

func (m *MockServiceClient) GeneratePrompt(request map[string]interface{}) (map[string]interface{}, error) {
	args := m.Called(request)
	return args.Get(0).(map[string]interface{}), args.Error(1)
}

func setupRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	router := gin.New()
	return router
}

func TestHealthCheck(t *testing.T) {
	router := setupRouter()
	router.GET("/health", HealthCheck)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/health", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "healthy", response["status"])
	assert.Contains(t, response, "timestamp")
	assert.Contains(t, response, "services")
}

func TestEnhancePrompt_Success(t *testing.T) {
	router := setupRouter()
	mockClient := new(MockServiceClient)
	
	// Mock responses
	mockClient.On("ClassifyIntent", mock.Anything).Return(map[string]interface{}{
		"category":    "analysis",
		"confidence":  0.95,
		"complexity":  0.7,
		"sub_intents": []string{"data_analysis"},
	}, nil)

	mockClient.On("SelectTechniques", mock.Anything).Return(map[string]interface{}{
		"techniques": []map[string]interface{}{
			{
				"name":         "chain_of_thought",
				"description":  "Step-by-step reasoning",
				"effectiveness": 0.85,
			},
		},
	}, nil)

	mockClient.On("GeneratePrompt", mock.Anything).Return(map[string]interface{}{
		"enhanced_prompt": "Let's think step by step: Analyze the data...",
		"applied_techniques": []string{"chain_of_thought"},
	}, nil)

	// Create handler with mock
	handler := &EnhanceHandler{
		IntentClient:    mockClient,
		TechniqueClient: mockClient,
		PromptClient:    mockClient,
	}

	router.POST("/api/v1/enhance", handler.EnhancePrompt)

	body := map[string]interface{}{
		"input": "Analyze sales data",
		"options": map[string]interface{}{
			"auto_apply": true,
		},
	}

	jsonBody, _ := json.Marshal(body)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/enhance", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Contains(t, response, "request_id")
	assert.Contains(t, response, "intent")
	assert.Contains(t, response, "techniques")
	assert.Contains(t, response, "enhanced_prompt")
}

func TestEnhancePrompt_EmptyInput(t *testing.T) {
	router := setupRouter()
	handler := &EnhanceHandler{}
	router.POST("/api/v1/enhance", handler.EnhancePrompt)

	body := map[string]interface{}{
		"input": "",
	}

	jsonBody, _ := json.Marshal(body)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/enhance", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusBadRequest, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Contains(t, response["error"], "Input cannot be empty")
}

func TestEnhancePrompt_ServiceError(t *testing.T) {
	router := setupRouter()
	mockClient := new(MockServiceClient)
	
	// Mock service error
	mockClient.On("ClassifyIntent", mock.Anything).Return(
		map[string]interface{}{}, 
		assert.AnError,
	)

	handler := &EnhanceHandler{
		IntentClient: mockClient,
	}

	router.POST("/api/v1/enhance", handler.EnhancePrompt)

	body := map[string]interface{}{
		"input": "Test prompt",
	}

	jsonBody, _ := json.Marshal(body)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/enhance", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusInternalServerError, w.Code)
}

func TestAnalyzeIntent(t *testing.T) {
	router := setupRouter()
	mockClient := new(MockServiceClient)
	
	mockClient.On("ClassifyIntent", mock.Anything).Return(map[string]interface{}{
		"category":    "code_generation",
		"confidence":  0.92,
		"complexity":  0.5,
		"sub_intents": []string{"python", "algorithm"},
	}, nil)

	handler := &EnhanceHandler{
		IntentClient: mockClient,
	}

	router.POST("/api/v1/analyze", handler.AnalyzeIntent)

	body := map[string]interface{}{
		"input": "Write a Python sorting algorithm",
	}

	jsonBody, _ := json.Marshal(body)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/analyze", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "code_generation", response["category"])
	assert.Equal(t, 0.92, response["confidence"])
}

func TestGetTechniques(t *testing.T) {
	router := setupRouter()
	handler := &EnhanceHandler{}
	router.GET("/api/v1/techniques", handler.GetTechniques)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/v1/techniques", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Contains(t, response, "techniques")
	
	techniques := response["techniques"].([]interface{})
	assert.Greater(t, len(techniques), 0)
}

func TestRecordFeedback(t *testing.T) {
	router := setupRouter()
	handler := &EnhanceHandler{}
	router.POST("/api/v1/feedback", handler.RecordFeedback)

	body := map[string]interface{}{
		"request_id":    "test-123",
		"effectiveness": 0.9,
		"user_rating":   5,
		"comments":      "Very helpful",
	}

	jsonBody, _ := json.Marshal(body)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/feedback", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "recorded", response["status"])
}