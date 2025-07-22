package handlers_test

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/betterprompts/api-gateway/internal/handlers"
	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// Integration tests for enhance handler focusing on request/response flow
func TestEnhanceHandler_RequestValidation(t *testing.T) {
	gin.SetMode(gin.TestMode)
	
	tests := []struct {
		name         string
		body         interface{}
		expectedCode int
		checkError   string
	}{
		{
			name:         "Valid request",
			body:         handlers.EnhanceRequest{Text: "Explain how to write unit tests"},
			expectedCode: http.StatusInternalServerError, // Will fail due to nil services
		},
		{
			name:         "Empty text",
			body:         handlers.EnhanceRequest{Text: ""},
			expectedCode: http.StatusBadRequest,
			checkError:   "Invalid request body",
		},
		{
			name:         "Text too long",
			body:         handlers.EnhanceRequest{Text: string(make([]byte, 5001))},
			expectedCode: http.StatusBadRequest,
			checkError:   "Invalid request body",
		},
		{
			name:         "Invalid JSON",
			body:         "not json",
			expectedCode: http.StatusBadRequest,
			checkError:   "Invalid request body",
		},
		{
			name:         "Missing text field",
			body:         map[string]interface{}{"context": map[string]string{"key": "value"}},
			expectedCode: http.StatusBadRequest,
			checkError:   "Invalid request body",
		},
		{
			name: "Valid with preferences",
			body: handlers.EnhanceRequest{
				Text:             "Create a REST API",
				PreferTechniques: []string{"step_by_step", "examples"},
			},
			expectedCode: http.StatusInternalServerError,
		},
		{
			name: "Valid with exclusions",
			body: handlers.EnhanceRequest{
				Text:              "Explain quantum computing",
				ExcludeTechniques: []string{"math_heavy", "technical_jargon"},
			},
			expectedCode: http.StatusInternalServerError,
		},
		{
			name: "Valid with context",
			body: handlers.EnhanceRequest{
				Text: "Debug this code",
				Context: map[string]interface{}{
					"language": "python",
					"error":    "IndexError",
				},
			},
			expectedCode: http.StatusInternalServerError,
		},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create router with minimal setup
			router := gin.New()
			router.Use(func(c *gin.Context) {
				c.Set("logger", logrus.NewEntry(logrus.New()))
				c.Set("request_id", "test-request-id")
				c.Next()
			})
			
			// Register handler with nil clients (will panic on actual use)
			router.POST("/enhance", handlers.EnhancePrompt(nil))
			
			// Prepare request
			var bodyBytes []byte
			if str, ok := tt.body.(string); ok {
				bodyBytes = []byte(str)
			} else {
				bodyBytes, _ = json.Marshal(tt.body)
			}
			
			req := httptest.NewRequest("POST", "/enhance", bytes.NewBuffer(bodyBytes))
			req.Header.Set("Content-Type", "application/json")
			
			// Execute
			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)
			
			// Assert
			assert.Equal(t, tt.expectedCode, w.Code)
			if tt.checkError != "" {
				assert.Contains(t, w.Body.String(), tt.checkError)
			}
		})
	}
}

// Test edge cases in request handling
func TestEnhanceHandler_EdgeCases(t *testing.T) {
	gin.SetMode(gin.TestMode)
	
	tests := []struct {
		name   string
		setup  func(*gin.Context)
		body   handlers.EnhanceRequest
		check  func(*testing.T, *httptest.ResponseRecorder)
	}{
		{
			name: "With authentication",
			setup: func(c *gin.Context) {
				c.Set("user_id", "user-123")
			},
			body: handlers.EnhanceRequest{
				Text: "Authenticated request",
			},
			check: func(t *testing.T, w *httptest.ResponseRecorder) {
				// Would check user_id handling if services were mocked
				assert.Equal(t, http.StatusInternalServerError, w.Code)
			},
		},
		{
			name: "With session ID header",
			setup: func(c *gin.Context) {
				c.Request.Header.Set("X-Session-ID", "session-123")
			},
			body: handlers.EnhanceRequest{
				Text: "Session tracked request",
			},
			check: func(t *testing.T, w *httptest.ResponseRecorder) {
				assert.Equal(t, http.StatusInternalServerError, w.Code)
			},
		},
		{
			name: "Unicode text",
			setup: func(c *gin.Context) {},
			body: handlers.EnhanceRequest{
				Text: "Explain 量子コンピューティング (quantum computing)",
			},
			check: func(t *testing.T, w *httptest.ResponseRecorder) {
				assert.Equal(t, http.StatusInternalServerError, w.Code)
			},
		},
		{
			name: "Special characters",
			setup: func(c *gin.Context) {},
			body: handlers.EnhanceRequest{
				Text: "What does SELECT * FROM users WHERE id = '1' OR '1'='1' do?",
			},
			check: func(t *testing.T, w *httptest.ResponseRecorder) {
				assert.Equal(t, http.StatusInternalServerError, w.Code)
			},
		},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			router := gin.New()
			router.Use(func(c *gin.Context) {
				c.Set("logger", logrus.NewEntry(logrus.New()))
				c.Set("request_id", "test-request-id")
				if tt.setup != nil {
					tt.setup(c)
				}
				c.Next()
			})
			
			router.POST("/enhance", handlers.EnhancePrompt(nil))
			
			bodyBytes, _ := json.Marshal(tt.body)
			req := httptest.NewRequest("POST", "/enhance", bytes.NewBuffer(bodyBytes))
			req.Header.Set("Content-Type", "application/json")
			
			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)
			
			tt.check(t, w)
		})
	}
}

// Test concurrent request handling
func TestEnhanceHandler_ConcurrentRequests(t *testing.T) {
	gin.SetMode(gin.TestMode)
	
	router := gin.New()
	router.Use(func(c *gin.Context) {
		c.Set("logger", logrus.NewEntry(logrus.New()))
		c.Set("request_id", "test-request-id")
		c.Next()
	})
	router.POST("/enhance", handlers.EnhancePrompt(nil))
	
	// Create multiple requests
	requests := []handlers.EnhanceRequest{
		{Text: "Request 1: Explain databases"},
		{Text: "Request 2: Write a function"},
		{Text: "Request 3: Debug this error"},
		{Text: "Request 4: Design a system"},
		{Text: "Request 5: Optimize performance"},
	}
	
	// Execute concurrently
	results := make(chan int, len(requests))
	
	for _, req := range requests {
		go func(r handlers.EnhanceRequest) {
			bodyBytes, _ := json.Marshal(r)
			request := httptest.NewRequest("POST", "/enhance", bytes.NewBuffer(bodyBytes))
			request.Header.Set("Content-Type", "application/json")
			
			w := httptest.NewRecorder()
			router.ServeHTTP(w, request)
			
			results <- w.Code
		}(req)
	}
	
	// Collect results
	for i := 0; i < len(requests); i++ {
		code := <-results
		// All should fail with 500 due to nil services
		assert.Equal(t, http.StatusInternalServerError, code)
	}
}

// Test request size limits
func TestEnhanceHandler_RequestSizeLimits(t *testing.T) {
	gin.SetMode(gin.TestMode)
	
	tests := []struct {
		name         string
		textSize     int
		expectedCode int
	}{
		{
			name:         "Minimum valid",
			textSize:     1,
			expectedCode: http.StatusInternalServerError,
		},
		{
			name:         "Normal size",
			textSize:     100,
			expectedCode: http.StatusInternalServerError,
		},
		{
			name:         "Near limit",
			textSize:     4999,
			expectedCode: http.StatusInternalServerError,
		},
		{
			name:         "At limit",
			textSize:     5000,
			expectedCode: http.StatusInternalServerError,
		},
		{
			name:         "Over limit",
			textSize:     5001,
			expectedCode: http.StatusBadRequest,
		},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			router := gin.New()
			router.Use(func(c *gin.Context) {
				c.Set("logger", logrus.NewEntry(logrus.New()))
				c.Set("request_id", "test-request-id")
				c.Next()
			})
			router.POST("/enhance", handlers.EnhancePrompt(nil))
			
			text := string(make([]byte, tt.textSize))
			for i := range text {
				text = text[:i] + "a" + text[i+1:]
			}
			
			req := handlers.EnhanceRequest{Text: text}
			bodyBytes, _ := json.Marshal(req)
			
			request := httptest.NewRequest("POST", "/enhance", bytes.NewBuffer(bodyBytes))
			request.Header.Set("Content-Type", "application/json")
			
			w := httptest.NewRecorder()
			router.ServeHTTP(w, request)
			
			assert.Equal(t, tt.expectedCode, w.Code)
		})
	}
}

// Test technique preferences and exclusions
func TestEnhanceHandler_TechniquePreferences(t *testing.T) {
	tests := []struct {
		name    string
		request handlers.EnhanceRequest
	}{
		{
			name: "Single preference",
			request: handlers.EnhanceRequest{
				Text:             "Explain sorting algorithms",
				PreferTechniques: []string{"visual_examples"},
			},
		},
		{
			name: "Multiple preferences",
			request: handlers.EnhanceRequest{
				Text:             "Build a web app",
				PreferTechniques: []string{"step_by_step", "code_examples", "best_practices"},
			},
		},
		{
			name: "Single exclusion",
			request: handlers.EnhanceRequest{
				Text:              "Explain neural networks",
				ExcludeTechniques: []string{"heavy_math"},
			},
		},
		{
			name: "Multiple exclusions",
			request: handlers.EnhanceRequest{
				Text:              "Debug performance issue",
				ExcludeTechniques: []string{"verbose_logging", "complex_profiling"},
			},
		},
		{
			name: "Both preferences and exclusions",
			request: handlers.EnhanceRequest{
				Text:              "Create API documentation",
				PreferTechniques:  []string{"examples", "openapi_spec"},
				ExcludeTechniques: []string{"implementation_details"},
			},
		},
	}
	
	gin.SetMode(gin.TestMode)
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			router := gin.New()
			router.Use(func(c *gin.Context) {
				c.Set("logger", logrus.NewEntry(logrus.New()))
				c.Set("request_id", "test-request-id")
				c.Next()
			})
			router.POST("/enhance", handlers.EnhancePrompt(nil))
			
			bodyBytes, _ := json.Marshal(tt.request)
			req := httptest.NewRequest("POST", "/enhance", bytes.NewBuffer(bodyBytes))
			req.Header.Set("Content-Type", "application/json")
			
			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)
			
			// Would validate technique handling with mocked services
			assert.Equal(t, http.StatusInternalServerError, w.Code)
		})
	}
}

// Benchmark the enhance handler
func BenchmarkEnhanceHandler_MinimalRequest(b *testing.B) {
	gin.SetMode(gin.TestMode)
	
	router := gin.New()
	router.Use(func(c *gin.Context) {
		c.Set("logger", logrus.NewEntry(logrus.New()))
		c.Set("request_id", "bench-request-id")
		c.Next()
	})
	router.POST("/enhance", handlers.EnhancePrompt(nil))
	
	req := handlers.EnhanceRequest{Text: "Benchmark test"}
	bodyBytes, _ := json.Marshal(req)
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		request := httptest.NewRequest("POST", "/enhance", bytes.NewBuffer(bodyBytes))
		request.Header.Set("Content-Type", "application/json")
		
		w := httptest.NewRecorder()
		router.ServeHTTP(w, request)
	}
}

func BenchmarkEnhanceHandler_ComplexRequest(b *testing.B) {
	gin.SetMode(gin.TestMode)
	
	router := gin.New()
	router.Use(func(c *gin.Context) {
		c.Set("logger", logrus.NewEntry(logrus.New()))
		c.Set("request_id", "bench-request-id")
		c.Next()
	})
	router.POST("/enhance", handlers.EnhancePrompt(nil))
	
	req := handlers.EnhanceRequest{
		Text: "Create a comprehensive microservices architecture for an e-commerce platform",
		Context: map[string]interface{}{
			"scale":       "enterprise",
			"users":       "10M+",
			"regions":     []string{"US", "EU", "ASIA"},
			"compliance":  []string{"PCI-DSS", "GDPR"},
		},
		PreferTechniques:  []string{"architectural_patterns", "scalability_analysis", "security_considerations"},
		ExcludeTechniques: []string{"basic_examples"},
	}
	bodyBytes, _ := json.Marshal(req)
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		request := httptest.NewRequest("POST", "/enhance", bytes.NewBuffer(bodyBytes))
		request.Header.Set("Content-Type", "application/json")
		
		w := httptest.NewRecorder()
		router.ServeHTTP(w, request)
	}
}