package middleware

import (
	"crypto/rand"
	"encoding/hex"
	"time"

	"github.com/betterprompts/api-gateway/internal/services"
	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

// SessionData represents the data stored in a session
type SessionData struct {
	ID        string                 `json:"id"`
	UserID    string                 `json:"user_id,omitempty"`
	CreatedAt time.Time              `json:"created_at"`
	UpdatedAt time.Time              `json:"updated_at"`
	Data      map[string]interface{} `json:"data"`
}

// SessionMiddleware creates a session management middleware
func SessionMiddleware(cache *services.CacheService, logger *logrus.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Check for existing session ID in header or cookie
		sessionID := c.GetHeader("X-Session-ID")
		if sessionID == "" {
			sessionID, _ = c.Cookie("session_id")
		}

		var session *SessionData
		isNewSession := false

		// Try to load existing session
		if sessionID != "" && cache != nil {
			session = &SessionData{}
			err := cache.GetSession(c.Request.Context(), sessionID, session)
			if err != nil {
				// Session not found or expired
				session = nil
			}
		}

		// Create new session if needed
		if session == nil {
			sessionID = generateSessionID()
			session = &SessionData{
				ID:        sessionID,
				CreatedAt: time.Now(),
				UpdatedAt: time.Now(),
				Data:      make(map[string]interface{}),
			}
			isNewSession = true
		}

		// Store session in context
		c.Set("session_id", sessionID)
		c.Set("session", session)

		// Process request
		c.Next()

		// Save session after request if cache is available
		if cache != nil {
			// Update session timestamp
			session.UpdatedAt = time.Now()

			// Check if user was authenticated during request
			if userID, exists := c.Get("user_id"); exists {
				if uid, ok := userID.(string); ok {
					session.UserID = uid
				}
			}

			// Save session
			ttl := 24 * time.Hour // 24 hour session TTL
			err := cache.StoreSession(c.Request.Context(), sessionID, session, ttl)
			if err != nil {
				logger.WithError(err).Warn("Failed to save session")
			}
		}

		// Set session cookie for new sessions
		if isNewSession {
			c.SetCookie(
				"session_id",
				sessionID,
				86400, // 24 hours
				"/",
				"", // Domain
				false, // Secure (set to true in production with HTTPS)
				true, // HttpOnly
			)
			c.Header("X-Session-ID", sessionID)
		}
	}
}

// RequireSession ensures a valid session exists
func RequireSession() gin.HandlerFunc {
	return func(c *gin.Context) {
		session, exists := c.Get("session")
		if !exists || session == nil {
			c.JSON(401, gin.H{
				"error": "No valid session",
			})
			c.Abort()
			return
		}
		c.Next()
	}
}

// GetSession retrieves the current session from context
func GetSession(c *gin.Context) *SessionData {
	if session, exists := c.Get("session"); exists {
		if s, ok := session.(*SessionData); ok {
			return s
		}
	}
	return nil
}

// SetSessionData sets a value in the session
func SetSessionData(c *gin.Context, key string, value interface{}) {
	session := GetSession(c)
	if session != nil {
		session.Data[key] = value
	}
}

// GetSessionData retrieves a value from the session
func GetSessionData(c *gin.Context, key string) (interface{}, bool) {
	session := GetSession(c)
	if session != nil {
		val, exists := session.Data[key]
		return val, exists
	}
	return nil, false
}

// generateSessionID generates a cryptographically secure session ID
func generateSessionID() string {
	bytes := make([]byte, 32)
	if _, err := rand.Read(bytes); err != nil {
		// Fallback to timestamp-based ID if crypto rand fails
		return hex.EncodeToString([]byte(time.Now().String()))
	}
	return hex.EncodeToString(bytes)
}