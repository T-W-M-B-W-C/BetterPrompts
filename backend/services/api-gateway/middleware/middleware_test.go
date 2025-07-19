package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/stretchr/testify/assert"
)

func setupTestRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	router := gin.New()
	return router
}

func TestCORSMiddleware(t *testing.T) {
	router := setupTestRouter()
	router.Use(CORS())
	router.GET("/test", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "success"})
	})

	// Test preflight request
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("OPTIONS", "/test", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	req.Header.Set("Access-Control-Request-Method", "POST")
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusNoContent, w.Code)
	assert.Equal(t, "*", w.Header().Get("Access-Control-Allow-Origin"))
	assert.Contains(t, w.Header().Get("Access-Control-Allow-Methods"), "POST")
	assert.Contains(t, w.Header().Get("Access-Control-Allow-Headers"), "Content-Type")

	// Test actual request
	w = httptest.NewRecorder()
	req, _ = http.NewRequest("GET", "/test", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Equal(t, "*", w.Header().Get("Access-Control-Allow-Origin"))
}

func TestRateLimiter(t *testing.T) {
	router := setupTestRouter()
	
	// Create rate limiter with low limit for testing
	limiter := NewRateLimiter(2, 1) // 2 requests per second
	router.Use(limiter.Middleware())
	router.GET("/test", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "success"})
	})

	// First two requests should succeed
	for i := 0; i < 2; i++ {
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/test", nil)
		req.Header.Set("X-Real-IP", "127.0.0.1")
		router.ServeHTTP(w, req)
		assert.Equal(t, http.StatusOK, w.Code)
	}

	// Third request should be rate limited
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/test", nil)
	req.Header.Set("X-Real-IP", "127.0.0.1")
	router.ServeHTTP(w, req)
	assert.Equal(t, http.StatusTooManyRequests, w.Code)
	assert.Contains(t, w.Body.String(), "rate limit exceeded")

	// Wait and try again
	time.Sleep(1 * time.Second)
	w = httptest.NewRecorder()
	req, _ = http.NewRequest("GET", "/test", nil)
	req.Header.Set("X-Real-IP", "127.0.0.1")
	router.ServeHTTP(w, req)
	assert.Equal(t, http.StatusOK, w.Code)
}

func TestJWTAuth(t *testing.T) {
	router := setupTestRouter()
	jwtSecret := "test-secret"
	
	router.Use(JWTAuth(jwtSecret))
	router.GET("/protected", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "authenticated"})
	})

	// Test without token
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/protected", nil)
	router.ServeHTTP(w, req)
	assert.Equal(t, http.StatusUnauthorized, w.Code)

	// Test with invalid token
	w = httptest.NewRecorder()
	req, _ = http.NewRequest("GET", "/protected", nil)
	req.Header.Set("Authorization", "Bearer invalid-token")
	router.ServeHTTP(w, req)
	assert.Equal(t, http.StatusUnauthorized, w.Code)

	// Test with valid token
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"user_id": "test-user",
		"exp":     time.Now().Add(time.Hour).Unix(),
	})
	tokenString, _ := token.SignedString([]byte(jwtSecret))

	w = httptest.NewRecorder()
	req, _ = http.NewRequest("GET", "/protected", nil)
	req.Header.Set("Authorization", "Bearer "+tokenString)
	router.ServeHTTP(w, req)
	assert.Equal(t, http.StatusOK, w.Code)

	// Test with expired token
	expiredToken := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"user_id": "test-user",
		"exp":     time.Now().Add(-time.Hour).Unix(),
	})
	expiredTokenString, _ := expiredToken.SignedString([]byte(jwtSecret))

	w = httptest.NewRecorder()
	req, _ = http.NewRequest("GET", "/protected", nil)
	req.Header.Set("Authorization", "Bearer "+expiredTokenString)
	router.ServeHTTP(w, req)
	assert.Equal(t, http.StatusUnauthorized, w.Code)
}

func TestRequestLogger(t *testing.T) {
	router := setupTestRouter()
	router.Use(RequestLogger())
	router.GET("/test", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "success"})
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/test", nil)
	req.Header.Set("X-Request-ID", "test-123")
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	// In a real test, we would capture log output and verify it
}

func TestErrorHandler(t *testing.T) {
	router := setupTestRouter()
	router.Use(ErrorHandler())
	
	// Test panic recovery
	router.GET("/panic", func(c *gin.Context) {
		panic("test panic")
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/panic", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusInternalServerError, w.Code)
	assert.Contains(t, w.Body.String(), "internal server error")
}

func TestRequestSizeLimit(t *testing.T) {
	router := setupTestRouter()
	router.Use(RequestSizeLimit(1024)) // 1KB limit
	router.POST("/upload", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "success"})
	})

	// Test small request
	smallBody := make([]byte, 512)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/upload", bytes.NewReader(smallBody))
	router.ServeHTTP(w, req)
	assert.Equal(t, http.StatusOK, w.Code)

	// Test large request
	largeBody := make([]byte, 2048)
	w = httptest.NewRecorder()
	req, _ = http.NewRequest("POST", "/upload", bytes.NewReader(largeBody))
	router.ServeHTTP(w, req)
	assert.Equal(t, http.StatusRequestEntityTooLarge, w.Code)
}

func TestSecurityHeaders(t *testing.T) {
	router := setupTestRouter()
	router.Use(SecurityHeaders())
	router.GET("/test", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "success"})
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/test", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Equal(t, "nosniff", w.Header().Get("X-Content-Type-Options"))
	assert.Equal(t, "SAMEORIGIN", w.Header().Get("X-Frame-Options"))
	assert.Equal(t, "1; mode=block", w.Header().Get("X-XSS-Protection"))
	assert.Contains(t, w.Header().Get("Content-Security-Policy"), "default-src 'self'")
}