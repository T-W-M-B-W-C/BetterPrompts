package handlers_test

import (
	"bytes"
	"context"
	"database/sql"
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
	"github.com/stretchr/testify/require"
	"github.com/stretchr/testify/suite"
)

// Mock Interfaces

type MockIntentClassifierClient struct {
	mock.Mock
}

func (m *MockIntentClassifierClient) ClassifyIntent(ctx context.Context, text string) (*services.IntentClassificationResult, error) {
	args := m.Called(ctx, text)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*services.IntentClassificationResult), args.Error(1)
}

type MockTechniqueSelectorClient struct {
	mock.Mock
}

func (m *MockTechniqueSelectorClient) SelectTechniques(ctx context.Context, req models.TechniqueSelectionRequest) ([]string, error) {
	args := m.Called(ctx, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]string), args.Error(1)
}

type MockPromptGeneratorClient struct {
	mock.Mock
}

func (m *MockPromptGeneratorClient) GeneratePrompt(ctx context.Context, req models.PromptGenerationRequest) (*models.PromptGenerationResponse, error) {
	args := m.Called(ctx, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.PromptGenerationResponse), args.Error(1)
}

type MockDatabaseService struct {
	mock.Mock
}

func (m *MockDatabaseService) SavePromptHistory(ctx context.Context, entry models.PromptHistory) (string, error) {
	args := m.Called(ctx, entry)
	return args.String(0), args.Error(1)
}

func (m *MockDatabaseService) Close() error {
	return nil
}

type MockCacheService struct {
	mock.Mock
}

func (m *MockCacheService) GetCachedIntentClassification(ctx context.Context, textHash string) (*services.IntentClassificationResult, error) {
	args := m.Called(ctx, textHash)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*services.IntentClassificationResult), args.Error(1)
}

func (m *MockCacheService) CacheIntentClassification(ctx context.Context, textHash string, result *services.IntentClassificationResult, ttl time.Duration) error {
	args := m.Called(ctx, textHash, result, ttl)
	return args.Error(0)
}

func (m *MockCacheService) CacheEnhancedPrompt(ctx context.Context, textHash string, techniques []string, result interface{}, ttl time.Duration) error {
	args := m.Called(ctx, textHash, techniques, result, ttl)
	return args.Error(0)
}

// Test Suite

type EnhanceHandlerTestSuite struct {
	suite.Suite
	mockIntentClassifier *MockIntentClassifierClient
	mockTechniqueSelector *MockTechniqueSelectorClient
	mockPromptGenerator   *MockPromptGeneratorClient
	mockDatabase          *MockDatabaseService
	mockCache             *MockCacheService
	clients               *services.ServiceClients
	logger                *logrus.Logger
	router                *gin.Engine
}

func (suite *EnhanceHandlerTestSuite) SetupTest() {
	gin.SetMode(gin.TestMode)
	
	// Initialize mocks
	suite.mockIntentClassifier = new(MockIntentClassifierClient)
	suite.mockTechniqueSelector = new(MockTechniqueSelectorClient)
	suite.mockPromptGenerator = new(MockPromptGeneratorClient)
	suite.mockDatabase = new(MockDatabaseService)
	suite.mockCache = new(MockCacheService)
	
	// Create service clients with mocks
	suite.clients = &services.ServiceClients{
		IntentClassifier:  suite.mockIntentClassifier,
		TechniqueSelector: suite.mockTechniqueSelector,
		PromptGenerator:   suite.mockPromptGenerator,
		Database:          suite.mockDatabase,
		Cache:            suite.mockCache,
	}
	
	// Initialize logger
	suite.logger = logrus.New()
	suite.logger.SetLevel(logrus.PanicLevel)
	
	// Setup router
	suite.router = gin.New()
	
	// Add required middleware
	suite.router.Use(func(c *gin.Context) {
		c.Set("logger", logrus.NewEntry(suite.logger))
		c.Set("request_id", "test-request-id")
		c.Next()
	})
	
	// Register enhance endpoint
	suite.router.POST("/api/v1/enhance", handlers.EnhancePrompt(suite.clients))
}

func (suite *EnhanceHandlerTestSuite) TearDownTest() {
	suite.mockIntentClassifier.AssertExpectations(suite.T())
	suite.mockTechniqueSelector.AssertExpectations(suite.T())
	suite.mockPromptGenerator.AssertExpectations(suite.T())
	suite.mockDatabase.AssertExpectations(suite.T())
	suite.mockCache.AssertExpectations(suite.T())
}

// Helper functions

func (suite *EnhanceHandlerTestSuite) makeRequest(body interface{}) *httptest.ResponseRecorder {
	jsonBody, _ := json.Marshal(body)
	req := httptest.NewRequest("POST", "/api/v1/enhance", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	
	w := httptest.NewRecorder()
	suite.router.ServeHTTP(w, req)
	return w
}

func (suite *EnhanceHandlerTestSuite) makeAuthenticatedRequest(body interface{}, userID string) *httptest.ResponseRecorder {
	jsonBody, _ := json.Marshal(body)
	req := httptest.NewRequest("POST", "/api/v1/enhance", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Session-ID", "test-session-id")
	
	// Add auth middleware to set user_id
	router := gin.New()
	router.Use(func(c *gin.Context) {
		c.Set("logger", logrus.NewEntry(suite.logger))
		c.Set("request_id", "test-request-id")
		c.Set("user_id", userID)
		c.Next()
	})
	router.POST("/api/v1/enhance", handlers.EnhancePrompt(suite.clients))
	
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)
	return w
}

// Test cases

func (suite *EnhanceHandlerTestSuite) TestEnhancePrompt_Success() {
	// Prepare request
	req := handlers.EnhanceRequest{
		Text: "Write a function to calculate fibonacci numbers",
	}
	
	// Setup expectations
	intentResult := &services.IntentClassificationResult{
		Intent:              "code_generation",
		Confidence:          0.95,
		Complexity:          "moderate",
		SuggestedTechniques: []string{"chain_of_thought", "code_structure"},
	}
	
	techniques := []string{"chain_of_thought", "code_structure", "step_by_step"}
	
	generationResponse := &models.PromptGenerationResponse{
		Text:         "Let me break down the fibonacci calculation step by step...",
		ModelVersion: "gpt-4",
		TokensUsed:   150,
	}
	
	// Mock cache miss
	suite.mockCache.On("GetCachedIntentClassification", mock.Anything, mock.Anything).
		Return(nil, errors.New("cache miss"))
	
	// Mock successful intent classification
	suite.mockIntentClassifier.On("ClassifyIntent", mock.Anything, req.Text).
		Return(intentResult, nil)
	
	// Mock cache storage
	suite.mockCache.On("CacheIntentClassification", mock.Anything, mock.Anything, intentResult, 1*time.Hour).
		Return(nil)
	
	// Mock technique selection
	suite.mockTechniqueSelector.On("SelectTechniques", mock.Anything, mock.MatchedBy(func(r models.TechniqueSelectionRequest) bool {
		return r.Text == req.Text && r.Intent == intentResult.Intent && r.Complexity == intentResult.Complexity
	})).Return(techniques, nil)
	
	// Mock prompt generation
	suite.mockPromptGenerator.On("GeneratePrompt", mock.Anything, mock.MatchedBy(func(r models.PromptGenerationRequest) bool {
		return r.Text == req.Text && r.Intent == intentResult.Intent && len(r.Techniques) == len(techniques)
	})).Return(generationResponse, nil)
	
	// Mock database save
	suite.mockDatabase.On("SavePromptHistory", mock.Anything, mock.Anything).
		Return("history-id-123", nil)
	
	// Mock final cache
	suite.mockCache.On("CacheEnhancedPrompt", mock.Anything, mock.Anything, techniques, mock.Anything, 1*time.Hour).
		Return(nil)
	
	// Make request
	w := suite.makeRequest(req)
	
	// Assertions
	assert.Equal(suite.T(), http.StatusOK, w.Code)
	
	var response handlers.EnhanceResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	require.NoError(suite.T(), err)
	
	assert.Equal(suite.T(), "history-id-123", response.ID)
	assert.Equal(suite.T(), req.Text, response.OriginalText)
	assert.Equal(suite.T(), generationResponse.Text, response.EnhancedText)
	assert.Equal(suite.T(), intentResult.Intent, response.Intent)
	assert.Equal(suite.T(), intentResult.Complexity, response.Complexity)
	assert.Equal(suite.T(), techniques, response.TechniquesUsed)
	assert.Equal(suite.T(), intentResult.Confidence, response.Confidence)
	assert.Greater(suite.T(), response.ProcessingTime, float64(0))
}

func (suite *EnhanceHandlerTestSuite) TestEnhancePrompt_WithCache() {
	req := handlers.EnhanceRequest{
		Text: "Explain how neural networks work",
	}
	
	// Cached intent result
	cachedIntent := &services.IntentClassificationResult{
		Intent:              "explanation",
		Confidence:          0.90,
		Complexity:          "complex",
		SuggestedTechniques: []string{"eli5", "analogies"},
	}
	
	techniques := []string{"eli5", "analogies", "visual_description"}
	
	generationResponse := &models.PromptGenerationResponse{
		Text:         "Imagine neural networks like a brain...",
		ModelVersion: "gpt-4",
		TokensUsed:   200,
	}
	
	// Mock cache hit
	suite.mockCache.On("GetCachedIntentClassification", mock.Anything, mock.Anything).
		Return(cachedIntent, nil)
	
	// Should not call intent classifier
	
	// Mock technique selection
	suite.mockTechniqueSelector.On("SelectTechniques", mock.Anything, mock.Anything).
		Return(techniques, nil)
	
	// Mock prompt generation
	suite.mockPromptGenerator.On("GeneratePrompt", mock.Anything, mock.Anything).
		Return(generationResponse, nil)
	
	// Mock database save
	suite.mockDatabase.On("SavePromptHistory", mock.Anything, mock.Anything).
		Return("history-id-456", nil)
	
	// Mock final cache
	suite.mockCache.On("CacheEnhancedPrompt", mock.Anything, mock.Anything, techniques, mock.Anything, 1*time.Hour).
		Return(nil)
	
	// Make request
	w := suite.makeRequest(req)
	
	// Assertions
	assert.Equal(suite.T(), http.StatusOK, w.Code)
	
	// Verify intent classifier was not called
	suite.mockIntentClassifier.AssertNotCalled(suite.T(), "ClassifyIntent", mock.Anything, mock.Anything)
}

func (suite *EnhanceHandlerTestSuite) TestEnhancePrompt_InvalidRequest() {
	// Test cases for invalid requests
	testCases := []struct {
		name          string
		request       interface{}
		expectedError string
	}{
		{
			name:          "Empty text",
			request:       handlers.EnhanceRequest{Text: ""},
			expectedError: "Invalid request body",
		},
		{
			name:          "Text too long",
			request:       handlers.EnhanceRequest{Text: string(make([]byte, 5001))},
			expectedError: "Invalid request body",
		},
		{
			name:          "Invalid JSON",
			request:       "invalid json",
			expectedError: "Invalid request body",
		},
		{
			name:          "Missing text field",
			request:       map[string]interface{}{"context": map[string]interface{}{}},
			expectedError: "Invalid request body",
		},
	}
	
	for _, tc := range testCases {
		suite.Run(tc.name, func() {
			var w *httptest.ResponseRecorder
			
			if str, ok := tc.request.(string); ok {
				req := httptest.NewRequest("POST", "/api/v1/enhance", bytes.NewBufferString(str))
				req.Header.Set("Content-Type", "application/json")
				w = httptest.NewRecorder()
				suite.router.ServeHTTP(w, req)
			} else {
				w = suite.makeRequest(tc.request)
			}
			
			assert.Equal(suite.T(), http.StatusBadRequest, w.Code)
			assert.Contains(suite.T(), w.Body.String(), tc.expectedError)
		})
	}
}

func (suite *EnhanceHandlerTestSuite) TestEnhancePrompt_IntentClassificationFailure() {
	req := handlers.EnhanceRequest{
		Text: "Test prompt",
	}
	
	// Mock cache miss
	suite.mockCache.On("GetCachedIntentClassification", mock.Anything, mock.Anything).
		Return(nil, errors.New("cache miss"))
	
	// Mock intent classification failure
	suite.mockIntentClassifier.On("ClassifyIntent", mock.Anything, req.Text).
		Return(nil, errors.New("service unavailable"))
	
	// Make request
	w := suite.makeRequest(req)
	
	// Assertions
	assert.Equal(suite.T(), http.StatusInternalServerError, w.Code)
	assert.Contains(suite.T(), w.Body.String(), "Failed to analyze intent")
}

func (suite *EnhanceHandlerTestSuite) TestEnhancePrompt_TechniqueSelectionFailure() {
	req := handlers.EnhanceRequest{
		Text: "Generate a REST API",
	}
	
	intentResult := &services.IntentClassificationResult{
		Intent:              "code_generation",
		Confidence:          0.85,
		Complexity:          "moderate",
		SuggestedTechniques: []string{"api_design"},
	}
	
	// Setup mocks
	suite.mockCache.On("GetCachedIntentClassification", mock.Anything, mock.Anything).
		Return(nil, errors.New("cache miss"))
	
	suite.mockIntentClassifier.On("ClassifyIntent", mock.Anything, req.Text).
		Return(intentResult, nil)
	
	suite.mockCache.On("CacheIntentClassification", mock.Anything, mock.Anything, intentResult, 1*time.Hour).
		Return(nil)
	
	// Mock technique selection failure - should fall back to suggested techniques
	suite.mockTechniqueSelector.On("SelectTechniques", mock.Anything, mock.Anything).
		Return(nil, errors.New("technique selector unavailable"))
	
	// Mock prompt generation with fallback techniques
	generationResponse := &models.PromptGenerationResponse{
		Text:         "Here's a REST API design...",
		ModelVersion: "gpt-3.5",
		TokensUsed:   100,
	}
	
	suite.mockPromptGenerator.On("GeneratePrompt", mock.Anything, mock.MatchedBy(func(r models.PromptGenerationRequest) bool {
		// Should use suggested techniques from intent classifier
		return len(r.Techniques) == 1 && r.Techniques[0] == "api_design"
	})).Return(generationResponse, nil)
	
	suite.mockDatabase.On("SavePromptHistory", mock.Anything, mock.Anything).
		Return("history-id-789", nil)
	
	suite.mockCache.On("CacheEnhancedPrompt", mock.Anything, mock.Anything, intentResult.SuggestedTechniques, mock.Anything, 1*time.Hour).
		Return(nil)
	
	// Make request
	w := suite.makeRequest(req)
	
	// Assertions - should still succeed with fallback
	assert.Equal(suite.T(), http.StatusOK, w.Code)
	
	var response handlers.EnhanceResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	require.NoError(suite.T(), err)
	
	assert.Equal(suite.T(), intentResult.SuggestedTechniques, response.TechniquesUsed)
}

func (suite *EnhanceHandlerTestSuite) TestEnhancePrompt_PromptGenerationFailure() {
	req := handlers.EnhanceRequest{
		Text: "Explain quantum computing",
	}
	
	intentResult := &services.IntentClassificationResult{
		Intent:     "explanation",
		Confidence: 0.92,
		Complexity: "complex",
	}
	
	techniques := []string{"eli5", "progressive_disclosure"}
	
	// Setup mocks
	suite.mockCache.On("GetCachedIntentClassification", mock.Anything, mock.Anything).
		Return(nil, errors.New("cache miss"))
	
	suite.mockIntentClassifier.On("ClassifyIntent", mock.Anything, req.Text).
		Return(intentResult, nil)
	
	suite.mockCache.On("CacheIntentClassification", mock.Anything, mock.Anything, intentResult, 1*time.Hour).
		Return(nil)
	
	suite.mockTechniqueSelector.On("SelectTechniques", mock.Anything, mock.Anything).
		Return(techniques, nil)
	
	// Mock prompt generation failure
	suite.mockPromptGenerator.On("GeneratePrompt", mock.Anything, mock.Anything).
		Return(nil, errors.New("generation service error"))
	
	// Make request
	w := suite.makeRequest(req)
	
	// Assertions
	assert.Equal(suite.T(), http.StatusInternalServerError, w.Code)
	assert.Contains(suite.T(), w.Body.String(), "Failed to generate enhanced prompt")
}

func (suite *EnhanceHandlerTestSuite) TestEnhancePrompt_WithAuthentication() {
	req := handlers.EnhanceRequest{
		Text: "Create a todo list app",
		PreferTechniques: []string{"step_by_step", "examples"},
	}
	
	userID := "user-123"
	
	intentResult := &services.IntentClassificationResult{
		Intent:     "code_generation",
		Confidence: 0.88,
		Complexity: "simple",
	}
	
	techniques := []string{"step_by_step", "examples", "code_structure"}
	
	generationResponse := &models.PromptGenerationResponse{
		Text:         "Let's create a todo list app step by step...",
		ModelVersion: "gpt-4",
		TokensUsed:   180,
	}
	
	// Setup mocks
	suite.mockCache.On("GetCachedIntentClassification", mock.Anything, mock.Anything).
		Return(nil, errors.New("cache miss"))
	
	suite.mockIntentClassifier.On("ClassifyIntent", mock.Anything, req.Text).
		Return(intentResult, nil)
	
	suite.mockCache.On("CacheIntentClassification", mock.Anything, mock.Anything, intentResult, 1*time.Hour).
		Return(nil)
	
	// Verify user preferences are passed
	suite.mockTechniqueSelector.On("SelectTechniques", mock.Anything, mock.MatchedBy(func(r models.TechniqueSelectionRequest) bool {
		return r.UserID == userID && len(r.PreferTechniques) == 2
	})).Return(techniques, nil)
	
	suite.mockPromptGenerator.On("GeneratePrompt", mock.Anything, mock.Anything).
		Return(generationResponse, nil)
	
	// Verify user ID is saved in history
	suite.mockDatabase.On("SavePromptHistory", mock.Anything, mock.MatchedBy(func(h models.PromptHistory) bool {
		return h.UserID.Valid && h.UserID.String == userID
	})).Return("history-id-auth", nil)
	
	suite.mockCache.On("CacheEnhancedPrompt", mock.Anything, mock.Anything, techniques, mock.Anything, 1*time.Hour).
		Return(nil)
	
	// Make authenticated request
	w := suite.makeAuthenticatedRequest(req, userID)
	
	// Assertions
	assert.Equal(suite.T(), http.StatusOK, w.Code)
	
	var response handlers.EnhanceResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	require.NoError(suite.T(), err)
	
	assert.Equal(suite.T(), "history-id-auth", response.ID)
}

func (suite *EnhanceHandlerTestSuite) TestEnhancePrompt_DatabaseSaveFailure() {
	// Test that database save failure doesn't fail the request
	req := handlers.EnhanceRequest{
		Text: "Optimize this algorithm",
	}
	
	intentResult := &services.IntentClassificationResult{
		Intent:     "optimization",
		Confidence: 0.91,
		Complexity: "moderate",
	}
	
	techniques := []string{"performance_analysis", "algorithmic_optimization"}
	
	generationResponse := &models.PromptGenerationResponse{
		Text:         "Let's analyze the algorithm performance...",
		ModelVersion: "gpt-4",
		TokensUsed:   120,
	}
	
	// Setup mocks
	suite.mockCache.On("GetCachedIntentClassification", mock.Anything, mock.Anything).
		Return(nil, errors.New("cache miss"))
	
	suite.mockIntentClassifier.On("ClassifyIntent", mock.Anything, req.Text).
		Return(intentResult, nil)
	
	suite.mockCache.On("CacheIntentClassification", mock.Anything, mock.Anything, intentResult, 1*time.Hour).
		Return(nil)
	
	suite.mockTechniqueSelector.On("SelectTechniques", mock.Anything, mock.Anything).
		Return(techniques, nil)
	
	suite.mockPromptGenerator.On("GeneratePrompt", mock.Anything, mock.Anything).
		Return(generationResponse, nil)
	
	// Mock database save failure
	suite.mockDatabase.On("SavePromptHistory", mock.Anything, mock.Anything).
		Return("", errors.New("database connection error"))
	
	suite.mockCache.On("CacheEnhancedPrompt", mock.Anything, mock.Anything, techniques, mock.Anything, 1*time.Hour).
		Return(nil)
	
	// Make request
	w := suite.makeRequest(req)
	
	// Assertions - should still succeed
	assert.Equal(suite.T(), http.StatusOK, w.Code)
	
	var response handlers.EnhanceResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	require.NoError(suite.T(), err)
	
	assert.Empty(suite.T(), response.ID) // No history ID due to save failure
	assert.Equal(suite.T(), generationResponse.Text, response.EnhancedText)
}

// Test with context and metadata
func (suite *EnhanceHandlerTestSuite) TestEnhancePrompt_WithContext() {
	req := handlers.EnhanceRequest{
		Text: "Refactor this code",
		Context: map[string]interface{}{
			"language": "python",
			"framework": "django",
		},
		ExcludeTechniques: []string{"verbose_explanation"},
	}
	
	intentResult := &services.IntentClassificationResult{
		Intent:     "code_refactoring",
		Confidence: 0.93,
		Complexity: "moderate",
	}
	
	techniques := []string{"clean_code", "design_patterns"}
	
	generationResponse := &models.PromptGenerationResponse{
		Text:         "Here's the refactored code following clean code principles...",
		ModelVersion: "gpt-4",
		TokensUsed:   200,
	}
	
	// Setup mocks
	suite.mockCache.On("GetCachedIntentClassification", mock.Anything, mock.Anything).
		Return(nil, errors.New("cache miss"))
	
	suite.mockIntentClassifier.On("ClassifyIntent", mock.Anything, req.Text).
		Return(intentResult, nil)
	
	suite.mockCache.On("CacheIntentClassification", mock.Anything, mock.Anything, intentResult, 1*time.Hour).
		Return(nil)
	
	// Verify context and exclusions are passed
	suite.mockTechniqueSelector.On("SelectTechniques", mock.Anything, mock.MatchedBy(func(r models.TechniqueSelectionRequest) bool {
		return len(r.ExcludeTechniques) == 1 && r.ExcludeTechniques[0] == "verbose_explanation"
	})).Return(techniques, nil)
	
	// Verify context is passed to generator
	suite.mockPromptGenerator.On("GeneratePrompt", mock.Anything, mock.MatchedBy(func(r models.PromptGenerationRequest) bool {
		return r.Context != nil && r.Context["language"] == "python"
	})).Return(generationResponse, nil)
	
	suite.mockDatabase.On("SavePromptHistory", mock.Anything, mock.Anything).
		Return("history-id-context", nil)
	
	suite.mockCache.On("CacheEnhancedPrompt", mock.Anything, mock.Anything, techniques, mock.Anything, 1*time.Hour).
		Return(nil)
	
	// Make request
	w := suite.makeRequest(req)
	
	// Assertions
	assert.Equal(suite.T(), http.StatusOK, w.Code)
	
	var response handlers.EnhanceResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	require.NoError(suite.T(), err)
	
	assert.NotNil(suite.T(), response.Metadata)
	assert.Equal(suite.T(), float64(200), response.Metadata["tokens_used"])
}

// Benchmark tests
func BenchmarkEnhancePrompt(b *testing.B) {
	// Setup
	gin.SetMode(gin.TestMode)
	
	mockIC := new(MockIntentClassifierClient)
	mockTS := new(MockTechniqueSelectorClient)
	mockPG := new(MockPromptGeneratorClient)
	mockDB := new(MockDatabaseService)
	mockCache := new(MockCacheService)
	
	clients := &services.ServiceClients{
		IntentClassifier:  mockIC,
		TechniqueSelector: mockTS,
		PromptGenerator:   mockPG,
		Database:          mockDB,
		Cache:            mockCache,
	}
	
	router := gin.New()
	router.Use(func(c *gin.Context) {
		c.Set("logger", logrus.NewEntry(logrus.New()))
		c.Set("request_id", "bench-request-id")
		c.Next()
	})
	router.POST("/api/v1/enhance", handlers.EnhancePrompt(clients))
	
	// Mock responses
	intentResult := &services.IntentClassificationResult{
		Intent:     "general",
		Confidence: 0.9,
		Complexity: "moderate",
	}
	
	techniques := []string{"chain_of_thought"}
	
	generationResponse := &models.PromptGenerationResponse{
		Text:         "Enhanced prompt",
		ModelVersion: "gpt-3.5",
		TokensUsed:   100,
	}
	
	// Setup expectations
	mockCache.On("GetCachedIntentClassification", mock.Anything, mock.Anything).
		Return(nil, errors.New("cache miss"))
	mockIC.On("ClassifyIntent", mock.Anything, mock.Anything).
		Return(intentResult, nil)
	mockCache.On("CacheIntentClassification", mock.Anything, mock.Anything, mock.Anything, mock.Anything).
		Return(nil)
	mockTS.On("SelectTechniques", mock.Anything, mock.Anything).
		Return(techniques, nil)
	mockPG.On("GeneratePrompt", mock.Anything, mock.Anything).
		Return(generationResponse, nil)
	mockDB.On("SavePromptHistory", mock.Anything, mock.Anything).
		Return("history-id", nil)
	mockCache.On("CacheEnhancedPrompt", mock.Anything, mock.Anything, mock.Anything, mock.Anything, mock.Anything).
		Return(nil)
	
	req := handlers.EnhanceRequest{
		Text: "Benchmark test prompt",
	}
	
	jsonBody, _ := json.Marshal(req)
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		request := httptest.NewRequest("POST", "/api/v1/enhance", bytes.NewBuffer(jsonBody))
		request.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, request)
	}
}

// Run test suite
func TestEnhanceHandlerTestSuite(t *testing.T) {
	suite.Run(t, new(EnhanceHandlerTestSuite))
}