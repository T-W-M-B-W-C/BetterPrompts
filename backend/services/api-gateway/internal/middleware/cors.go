package middleware

import (
	"os"
	"strings"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

// CORSConfig returns a CORS middleware configuration
func CORSConfig(logger *logrus.Logger) gin.HandlerFunc {
	// Default allowed origins for development
	allowedOrigins := []string{
		"http://localhost:3000",     // Frontend development server
		"http://localhost:3001",     // Alternative frontend port
		"http://localhost",          // Production frontend through nginx
		"http://127.0.0.1:3000",     // Alternative localhost notation
		"http://localhost:80",       // Explicit port 80
	}
	
	// Add additional origins from environment variable
	if envOrigins := os.Getenv("CORS_ALLOWED_ORIGINS"); envOrigins != "" {
		additionalOrigins := strings.Split(envOrigins, ",")
		for _, origin := range additionalOrigins {
			origin = strings.TrimSpace(origin)
			if origin != "" {
				allowedOrigins = append(allowedOrigins, origin)
			}
		}
	}
	
	// Add production origin if set
	if prodOrigin := os.Getenv("PRODUCTION_ORIGIN"); prodOrigin != "" {
		allowedOrigins = append(allowedOrigins, prodOrigin)
	}
	
	config := cors.Config{
		AllowOrigins: allowedOrigins,
		AllowMethods: []string{
			"GET",
			"POST",
			"PUT",
			"PATCH",
			"DELETE",
			"OPTIONS",
			"HEAD",
		},
		AllowHeaders: []string{
			"Origin",
			"Content-Type",
			"Content-Length",
			"Accept",
			"Accept-Encoding",
			"Accept-Language",
			"Authorization",
			"X-Session-ID",
			"X-Request-ID",
			"X-CSRF-Token",
			"X-Requested-With",
			"Cache-Control",
			"Pragma",
		},
		ExposeHeaders: []string{
			"X-Request-ID",
			"X-Session-ID",
			"X-RateLimit-Limit",
			"X-RateLimit-Remaining",
			"X-RateLimit-Reset",
			"Content-Length",
			"Content-Type",
			"Content-Disposition",
		},
		AllowCredentials: true,
		MaxAge:          12 * time.Hour,
		AllowWildcard:   false, // Don't allow wildcard for security
		AllowWebSockets: true,  // Allow WebSocket upgrades if needed
	}
	
	// Custom validation function for dynamic origin checking
	config.AllowOriginFunc = func(origin string) bool {
		// Check if origin is in allowed list
		for _, allowed := range allowedOrigins {
			if origin == allowed {
				return true
			}
		}
		
		// In development, be more permissive
		if os.Getenv("NODE_ENV") == "development" {
			// Allow any localhost origin in development
			if strings.HasPrefix(origin, "http://localhost:") ||
				strings.HasPrefix(origin, "http://127.0.0.1:") ||
				strings.HasPrefix(origin, "http://[::1]:") {
				logger.WithField("origin", origin).Debug("Allowing development origin")
				return true
			}
		}
		
		logger.WithField("origin", origin).Warn("Rejected CORS origin")
		return false
	}
	
	// Log configuration for debugging
	logger.WithFields(logrus.Fields{
		"allowed_origins":   allowedOrigins,
		"allow_credentials": config.AllowCredentials,
		"max_age":          config.MaxAge,
		"environment":      os.Getenv("NODE_ENV"),
	}).Info("CORS middleware configured")
	
	return cors.New(config)
}

// ValidateOrigin checks if an origin is allowed
func ValidateOrigin(origin string, allowedOrigins []string) bool {
	for _, allowed := range allowedOrigins {
		if origin == allowed {
			return true
		}
		// Support wildcard subdomains
		if strings.HasSuffix(allowed, "*") {
			prefix := strings.TrimSuffix(allowed, "*")
			if strings.HasPrefix(origin, prefix) {
				return true
			}
		}
	}
	return false
}