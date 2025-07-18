package middleware

import (
	"net/http"
	"strings"

	"github.com/betterprompts/api-gateway/internal/auth"
	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

// AuthMiddleware creates an authentication middleware
func AuthMiddleware(jwtManager *auth.JWTManager, logger *logrus.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Extract token from header
		authHeader := c.GetHeader("Authorization")
		token, err := auth.ExtractTokenFromHeader(authHeader)
		if err != nil {
			// Check cookie as fallback
			token, _ = c.Cookie("access_token")
			if token == "" {
				c.JSON(http.StatusUnauthorized, gin.H{
					"error": "Authorization required",
				})
				c.Abort()
				return
			}
		}

		// Validate token
		claims, err := jwtManager.ValidateAccessToken(token)
		if err != nil {
			logger.WithError(err).Debug("Invalid token")
			c.JSON(http.StatusUnauthorized, gin.H{
				"error": "Invalid or expired token",
			})
			c.Abort()
			return
		}

		// Set user information in context
		c.Set("user_id", claims.UserID)
		c.Set("user_email", claims.Email)
		c.Set("user_roles", claims.Roles)
		c.Set("auth_claims", claims)

		// Update session if exists
		if session := GetSession(c); session != nil {
			session.UserID = claims.UserID
			SetSessionData(c, "authenticated", true)
			SetSessionData(c, "user_email", claims.Email)
			SetSessionData(c, "user_roles", claims.Roles)
		}

		c.Next()
	}
}

// RequireAuth ensures the user is authenticated
func RequireAuth() gin.HandlerFunc {
	return func(c *gin.Context) {
		userID, exists := c.Get("user_id")
		if !exists || userID == "" {
			c.JSON(http.StatusUnauthorized, gin.H{
				"error": "Authentication required",
			})
			c.Abort()
			return
		}
		c.Next()
	}
}

// RequireRole ensures the user has one of the required roles
func RequireRole(roles ...string) gin.HandlerFunc {
	return func(c *gin.Context) {
		userRoles, exists := c.Get("user_roles")
		if !exists {
			c.JSON(http.StatusForbidden, gin.H{
				"error": "Access denied",
			})
			c.Abort()
			return
		}

		userRolesList, ok := userRoles.([]string)
		if !ok {
			c.JSON(http.StatusForbidden, gin.H{
				"error": "Invalid role format",
			})
			c.Abort()
			return
		}

		// Check if user has any of the required roles
		hasRole := false
		for _, requiredRole := range roles {
			for _, userRole := range userRolesList {
				if userRole == requiredRole {
					hasRole = true
					break
				}
			}
			if hasRole {
				break
			}
		}

		if !hasRole {
			c.JSON(http.StatusForbidden, gin.H{
				"error": "Insufficient permissions",
				"required_roles": roles,
			})
			c.Abort()
			return
		}

		c.Next()
	}
}

// RequirePermission ensures the user has the required permission
func RequirePermission(permission string) gin.HandlerFunc {
	return func(c *gin.Context) {
		userRoles, exists := c.Get("user_roles")
		if !exists {
			c.JSON(http.StatusForbidden, gin.H{
				"error": "Access denied",
			})
			c.Abort()
			return
		}

		userRolesList, ok := userRoles.([]string)
		if !ok {
			c.JSON(http.StatusForbidden, gin.H{
				"error": "Invalid role format",
			})
			c.Abort()
			return
		}

		// Check if any role has the required permission
		hasPermission := false
		for _, role := range userRolesList {
			if roleHasPermission(role, permission) {
				hasPermission = true
				break
			}
		}

		if !hasPermission {
			c.JSON(http.StatusForbidden, gin.H{
				"error": "Insufficient permissions",
				"required_permission": permission,
			})
			c.Abort()
			return
		}

		c.Next()
	}
}

// OptionalAuth extracts authentication if present but doesn't require it
func OptionalAuth(jwtManager *auth.JWTManager, logger *logrus.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Extract token from header
		authHeader := c.GetHeader("Authorization")
		token, err := auth.ExtractTokenFromHeader(authHeader)
		if err != nil {
			// Check cookie as fallback
			token, _ = c.Cookie("access_token")
			if token == "" {
				// No authentication provided, continue without it
				c.Next()
				return
			}
		}

		// Validate token
		claims, err := jwtManager.ValidateAccessToken(token)
		if err != nil {
			// Invalid token, continue without authentication
			logger.WithError(err).Debug("Invalid optional token")
			c.Next()
			return
		}

		// Set user information in context
		c.Set("user_id", claims.UserID)
		c.Set("user_email", claims.Email)
		c.Set("user_roles", claims.Roles)
		c.Set("auth_claims", claims)

		c.Next()
	}
}

// GetUserID retrieves the user ID from context
func GetUserID(c *gin.Context) (string, bool) {
	userID, exists := c.Get("user_id")
	if !exists {
		return "", false
	}
	id, ok := userID.(string)
	return id, ok
}

// GetUserRoles retrieves the user roles from context
func GetUserRoles(c *gin.Context) ([]string, bool) {
	roles, exists := c.Get("user_roles")
	if !exists {
		return nil, false
	}
	rolesList, ok := roles.([]string)
	return rolesList, ok
}

// HasRole checks if the current user has a specific role
func HasRole(c *gin.Context, role string) bool {
	roles, ok := GetUserRoles(c)
	if !ok {
		return false
	}
	for _, r := range roles {
		if r == role {
			return true
		}
	}
	return false
}

// IsAdmin checks if the current user is an admin
func IsAdmin(c *gin.Context) bool {
	return HasRole(c, "admin")
}

// IsDeveloper checks if the current user is a developer
func IsDeveloper(c *gin.Context) bool {
	return HasRole(c, "developer")
}

// roleHasPermission checks if a role has a specific permission
func roleHasPermission(role, permission string) bool {
	// In production, this would check against a database or configuration
	// For now, we'll use a simple mapping
	rolePermissions := map[string][]string{
		"admin": {
			"prompt:read:all",
			"prompt:write:all",
			"prompt:delete:all",
			"user:read:all",
			"user:write:all",
			"user:delete:all",
			"system:config:all",
		},
		"developer": {
			"prompt:read:own",
			"prompt:write:own",
			"prompt:delete:own",
			"prompt:read:public",
			"api:access:full",
		},
		"user": {
			"prompt:read:own",
			"prompt:write:own",
			"prompt:delete:own",
		},
	}

	permissions, exists := rolePermissions[role]
	if !exists {
		return false
	}

	// Check exact permission
	for _, p := range permissions {
		if p == permission {
			return true
		}
		
		// Check wildcard permissions (e.g., "prompt:*:all" matches "prompt:read:all")
		if matchPermission(p, permission) {
			return true
		}
	}

	return false
}

// matchPermission checks if a permission pattern matches a specific permission
func matchPermission(pattern, permission string) bool {
	patternParts := strings.Split(pattern, ":")
	permissionParts := strings.Split(permission, ":")

	if len(patternParts) != len(permissionParts) {
		return false
	}

	for i, part := range patternParts {
		if part != "*" && part != permissionParts[i] {
			return false
		}
	}

	return true
}