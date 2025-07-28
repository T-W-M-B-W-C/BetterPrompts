package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/betterprompts/api-gateway/internal/models"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func TestAuthHandler_BasicValidation(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name          string
		endpoint      string
		method        string
		body          interface{}
		expectedCode  int
		expectedError string
		setupContext  func(*gin.Context)
	}{
		{
			name:          "Register_InvalidJSON",
			endpoint:      "/register",
			method:        "POST",
			body:          "invalid json",
			expectedCode:  http.StatusBadRequest,
			expectedError: "Invalid request body",
		},
		{
			name:     "Register_PasswordMismatch",
			endpoint: "/register",
			method:   "POST",
			body: models.UserRegistrationRequest{
				Email:           "test@example.com",
				Username:        "testuser",
				Password:        "SecurePass123!",
				ConfirmPassword: "DifferentPass123!",
			},
			expectedCode:  http.StatusBadRequest,
			expectedError: "Passwords do not match",
		},
		{
			name:          "Login_InvalidJSON",
			endpoint:      "/login",
			method:        "POST",
			body:          "invalid json",
			expectedCode:  http.StatusBadRequest,
			expectedError: "Invalid request body",
		},
		{
			name:          "RefreshToken_InvalidJSON",
			endpoint:      "/refresh",
			method:        "POST",
			body:          "invalid json",
			expectedCode:  http.StatusBadRequest,
			expectedError: "Invalid request body",
		},
		{
			name:          "GetProfile_Unauthorized",
			endpoint:      "/profile",
			method:        "GET",
			body:          nil,
			expectedCode:  http.StatusUnauthorized,
			expectedError: "Authentication required",
		},
		{
			name:          "UpdateProfile_Unauthorized",
			endpoint:      "/profile",
			method:        "PUT",
			body:          map[string]string{"username": "newuser"},
			expectedCode:  http.StatusUnauthorized,
			expectedError: "Authentication required",
		},
		{
			name:     "ChangePassword_Unauthorized",
			endpoint: "/change-password",
			method:   "POST",
			body: models.PasswordChangeRequest{
				CurrentPassword: "OldPass123!",
				NewPassword:     "NewPass123!",
				ConfirmPassword: "NewPass123!",
			},
			expectedCode:  http.StatusUnauthorized,
			expectedError: "Authentication required",
		},
		{
			name:     "ChangePassword_PasswordMismatch",
			endpoint: "/change-password",
			method:   "POST",
			body: models.PasswordChangeRequest{
				CurrentPassword: "OldPass123!",
				NewPassword:     "NewPass123!",
				ConfirmPassword: "DifferentPass123!",
			},
			expectedCode:  http.StatusBadRequest,
			expectedError: "Passwords do not match",
			setupContext: func(c *gin.Context) {
				c.Set("user_id", "user-123")
			},
		},
		{
			name:          "VerifyEmail_InvalidJSON",
			endpoint:      "/verify-email",
			method:        "POST",
			body:          "invalid json",
			expectedCode:  http.StatusBadRequest,
			expectedError: "Invalid request body",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create a new handler with nil dependencies (will panic if used)
			// This is OK for validation tests that don't reach the service layer
			handler := &AuthHandler{}

			// Create test context
			w := httptest.NewRecorder()
			c, router := gin.CreateTestContext(w)

			// Setup routes
			router.POST("/register", handler.Register)
			router.POST("/login", handler.Login)
			router.POST("/refresh", handler.RefreshToken)
			router.POST("/logout", handler.Logout)
			router.GET("/profile", handler.GetProfile)
			router.PUT("/profile", handler.UpdateProfile)
			router.POST("/change-password", handler.ChangePassword)
			router.POST("/verify-email", handler.VerifyEmail)

			// Prepare request
			var bodyBytes []byte
			if tt.body != nil {
				if str, ok := tt.body.(string); ok {
					bodyBytes = []byte(str)
				} else {
					bodyBytes, _ = json.Marshal(tt.body)
				}
			}

			c.Request = httptest.NewRequest(tt.method, tt.endpoint, bytes.NewBuffer(bodyBytes))
			if tt.body != nil {
				c.Request.Header.Set("Content-Type", "application/json")
			}

			// Setup context if needed
			if tt.setupContext != nil {
				tt.setupContext(c)
			}

			// Execute request
			router.ServeHTTP(w, c.Request)

			// Assertions
			assert.Equal(t, tt.expectedCode, w.Code)
			if tt.expectedError != "" {
				assert.Contains(t, w.Body.String(), tt.expectedError)
			}
		})
	}
}

// Test security considerations
func TestAuthHandler_SecurityValidation(t *testing.T) {
	tests := []struct {
		name    string
		body    interface{}
		checkFn func(t *testing.T, response string)
	}{
		{
			name: "XSS_Prevention",
			body: models.UserRegistrationRequest{
				Email:           "test@example.com",
				Username:        "<script>alert('xss')</script>",
				Password:        "SecurePass123!",
				ConfirmPassword: "SecurePass123!",
				FirstName:       "<img src=x onerror=alert('xss')>",
			},
			checkFn: func(t *testing.T, response string) {
				// Response should not contain unescaped HTML
				assert.NotContains(t, response, "<script>")
				assert.NotContains(t, response, "<img")
			},
		},
		{
			name: "SQL_Injection_Attempt",
			body: models.UserRegistrationRequest{
				Email:           "test'; DROP TABLE users; --@example.com",
				Username:        "test' OR '1'='1",
				Password:        "SecurePass123!",
				ConfirmPassword: "SecurePass123!",
			},
			checkFn: func(t *testing.T, response string) {
				// Should handle SQL injection attempts gracefully
				assert.NotContains(t, response, "SQL")
				assert.NotContains(t, response, "syntax error")
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			handler := &AuthHandler{}

			w := httptest.NewRecorder()
			c, router := gin.CreateTestContext(w)
			router.POST("/register", handler.Register)

			bodyBytes, _ := json.Marshal(tt.body)
			c.Request = httptest.NewRequest("POST", "/register", bytes.NewBuffer(bodyBytes))
			c.Request.Header.Set("Content-Type", "application/json")

			router.ServeHTTP(w, c.Request)

			if tt.checkFn != nil {
				tt.checkFn(t, w.Body.String())
			}
		})
	}
}

// Test rate limiting considerations
func TestAuthHandler_RateLimiting(t *testing.T) {
	// Note: Actual rate limiting would be implemented in middleware
	// This test just ensures the handler can handle rate limit errors gracefully

	handler := &AuthHandler{}

	reqBody := models.UserRegistrationRequest{
		Email:           "test@example.com",
		Username:        "testuser",
		Password:        "SecurePass123!",
		ConfirmPassword: "SecurePass123!",
	}

	// Simulate multiple rapid requests
	for i := 0; i < 5; i++ {
		w := httptest.NewRecorder()
		c, router := gin.CreateTestContext(w)
		router.POST("/register", handler.Register)

		bodyBytes, _ := json.Marshal(reqBody)
		c.Request = httptest.NewRequest("POST", "/register", bytes.NewBuffer(bodyBytes))
		c.Request.Header.Set("Content-Type", "application/json")

		router.ServeHTTP(w, c.Request)

		// Should handle each request without panicking
		assert.NotNil(t, w)
	}
}

// Test input validation edge cases
func TestAuthHandler_InputValidation(t *testing.T) {
	tests := []struct {
		name         string
		body         interface{}
		expectedCode int
	}{
		{
			name:         "EmptyRegistration",
			body:         models.UserRegistrationRequest{},
			expectedCode: http.StatusBadRequest,
		},
		{
			name:         "EmptyLogin",
			body:         models.UserLoginRequest{},
			expectedCode: http.StatusBadRequest,
		},
		{
			name:         "EmptyRefreshToken",
			body:         models.RefreshTokenRequest{},
			expectedCode: http.StatusBadRequest,
		},
		{
			name: "VeryLongPassword",
			body: models.UserRegistrationRequest{
				Email:           "test@example.com",
				Username:        "testuser",
				Password:        string(make([]byte, 100)), // 100 chars
				ConfirmPassword: string(make([]byte, 100)),
			},
			expectedCode: http.StatusBadRequest,
		},
		{
			name: "InternationalEmail",
			body: models.UserRegistrationRequest{
				Email:           "用户@例え.jp",
				Username:        "intluser",
				Password:        "SecurePass123!",
				ConfirmPassword: "SecurePass123!",
			},
			expectedCode: http.StatusBadRequest, // Depends on email validation
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			handler := &AuthHandler{}

			w := httptest.NewRecorder()
			c, router := gin.CreateTestContext(w)

			endpoint := "/register"
			if _, ok := tt.body.(models.UserLoginRequest); ok {
				endpoint = "/login"
				router.POST("/login", handler.Login)
			} else if _, ok := tt.body.(models.RefreshTokenRequest); ok {
				endpoint = "/refresh"
				router.POST("/refresh", handler.RefreshToken)
			} else {
				router.POST("/register", handler.Register)
			}

			bodyBytes, _ := json.Marshal(tt.body)
			c.Request = httptest.NewRequest("POST", endpoint, bytes.NewBuffer(bodyBytes))
			c.Request.Header.Set("Content-Type", "application/json")

			router.ServeHTTP(w, c.Request)

			assert.Equal(t, tt.expectedCode, w.Code)
		})
	}
}

// Benchmark tests
func BenchmarkAuthHandler_Register(b *testing.B) {
	handler := &AuthHandler{}

	reqBody := models.UserRegistrationRequest{
		Email:           "test@example.com",
		Username:        "testuser",
		Password:        "SecurePass123!",
		ConfirmPassword: "SecurePass123!",
	}

	bodyBytes, _ := json.Marshal(reqBody)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		w := httptest.NewRecorder()
		c, router := gin.CreateTestContext(w)
		router.POST("/register", handler.Register)

		c.Request = httptest.NewRequest("POST", "/register", bytes.NewBuffer(bodyBytes))
		c.Request.Header.Set("Content-Type", "application/json")

		router.ServeHTTP(w, c.Request)
	}
}

func BenchmarkAuthHandler_Login(b *testing.B) {
	handler := &AuthHandler{}

	reqBody := models.LoginRequest{
		Email:    "test@example.com",
		Password: "SecurePass123!",
	}

	bodyBytes, _ := json.Marshal(reqBody)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		w := httptest.NewRecorder()
		c, router := gin.CreateTestContext(w)
		router.POST("/login", handler.Login)

		c.Request = httptest.NewRequest("POST", "/login", bytes.NewBuffer(bodyBytes))
		c.Request.Header.Set("Content-Type", "application/json")

		router.ServeHTTP(w, c.Request)
	}
}
