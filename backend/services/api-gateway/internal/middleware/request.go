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

