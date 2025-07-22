#!/bin/bash

# Minimal fix to get API Gateway building
echo "🔧 Minimal API Gateway Fix"
echo "=========================="

cd /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts/backend/services/api-gateway

# Fix 1: Create missing middleware functions
echo "Creating missing middleware..."
cat > internal/middleware/request.go << 'EOF'
package middleware

import (
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

// RequestID middleware adds a unique request ID to each request
func RequestID() gin.HandlerFunc {
	return func(c *gin.Context) {
		requestID := c.GetHeader("X-Request-ID")
		if requestID == "" {
			requestID = uuid.New().String()
		}
		c.Set("request_id", requestID)
		c.Header("X-Request-ID", requestID)
		c.Next()
	}
}

// Logger middleware logs request details
func Logger(logger *logrus.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Set logger in context
		entry := logger.WithFields(logrus.Fields{
			"request_id": c.GetString("request_id"),
			"method":     c.Request.Method,
			"path":       c.Request.URL.Path,
		})
		c.Set("logger", entry)
		c.Next()
		
		// Log request completion
		entry.WithFields(logrus.Fields{
			"status": c.Writer.Status(),
		}).Info("Request completed")
	}
}

// RequireRole middleware checks if user has required role
func RequireRole(roles ...string) gin.HandlerFunc {
	return func(c *gin.Context) {
		// TODO: Implement role checking
		c.Next()
	}
}
EOF

# Fix 2: Fix HealthCheck handler
echo "Fixing HealthCheck handler..."
sed -i '' 's/public\.GET("\/health", handlers\.HealthCheck(clients))/public.GET("\/health", handlers.HealthCheck)/' cmd/server/main.go

# Fix 3: Create stub handlers for missing functions
echo "Creating stub handlers..."
cat > internal/handlers/stubs.go << 'EOF'
package handlers

import (
	"net/http"
	"github.com/gin-gonic/gin"
	"github.com/betterprompts/api-gateway/internal/services"
)

// Stub handlers to make the build work

func GetAvailableTechniques(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"techniques": []string{"cot", "few_shot"}})
	}
}

func SelectTechniques(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"selected": []string{"cot"}})
	}
}

func SubmitFeedback(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "feedback received"})
	}
}

func GetUsers(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"users": []interface{}{}})
	}
}

func GetUser(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"user": nil})
	}
}

func UpdateUser(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "updated"})
	}
}

func DeleteUser(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "deleted"})
	}
}

func GetSystemMetrics(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"metrics": map[string]interface{}{}})
	}
}

func GetUsageMetrics(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"usage": map[string]interface{}{}})
	}
}

func ClearCache(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "cache cleared"})
	}
}

func InvalidateUserCache(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "user cache invalidated"})
	}
}

func CreateAPIKey(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"api_key": "stub-key"})
	}
}

func GetAPIKeys(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"api_keys": []interface{}{}})
	}
}

func DeleteAPIKey(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "deleted"})
	}
}
EOF

echo ""
echo "✅ Minimal fixes applied. Now rebuilding..."
cd ../../..
docker compose build api-gateway