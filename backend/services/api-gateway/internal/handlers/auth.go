package handlers

import (
	"net/http"
	"time"

	"github.com/betterprompts/api-gateway/internal/auth"
	"github.com/betterprompts/api-gateway/internal/middleware"
	"github.com/betterprompts/api-gateway/internal/models"
	"github.com/betterprompts/api-gateway/internal/services"
	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

// AuthHandler handles authentication endpoints
type AuthHandler struct {
	userService *services.UserService
	jwtManager  *auth.JWTManager
	cache       *services.CacheService
	logger      *logrus.Logger
}

// NewAuthHandler creates a new auth handler
func NewAuthHandler(userService *services.UserService, jwtManager *auth.JWTManager, cache *services.CacheService, logger *logrus.Logger) *AuthHandler {
	return &AuthHandler{
		userService: userService,
		jwtManager:  jwtManager,
		cache:       cache,
		logger:      logger,
	}
}

// Register handles user registration
func (h *AuthHandler) Register(c *gin.Context) {
	var req models.UserRegistrationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request body",
			"details": err.Error(),
		})
		return
	}

	// Validate passwords match
	if req.Password != req.ConfirmPassword {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Passwords do not match",
		})
		return
	}

	// Create user
	user, err := h.userService.CreateUser(c.Request.Context(), req)
	if err != nil {
		h.logger.WithError(err).Error("Failed to create user")
		
		// Check for specific errors
		errMsg := err.Error()
		statusCode := http.StatusInternalServerError
		
		if errMsg == "email already exists" || errMsg == "username already exists" {
			statusCode = http.StatusConflict
		} else if errMsg == "password validation failed" {
			statusCode = http.StatusBadRequest
		}
		
		c.JSON(statusCode, gin.H{
			"error": errMsg,
		})
		return
	}

	// Generate tokens
	accessToken, refreshToken, err := h.jwtManager.GenerateTokenPair(user.ID, user.Email, user.Roles)
	if err != nil {
		h.logger.WithError(err).Error("Failed to generate tokens")
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to generate authentication tokens",
		})
		return
	}

	// Store refresh token in cache if available
	if h.cache != nil {
		refreshKey := h.cache.Key("refresh_token", user.ID, refreshToken[:16])
		h.cache.StoreSession(c.Request.Context(), refreshKey, map[string]interface{}{
			"user_id": user.ID,
			"token": refreshToken,
		}, 7*24*time.Hour)
	}

	h.logger.WithFields(logrus.Fields{
		"user_id": user.ID,
		"email": user.Email,
	}).Info("User registered successfully")

	c.JSON(http.StatusCreated, models.UserLoginResponse{
		User: user,
		AccessToken: accessToken,
		RefreshToken: refreshToken,
		ExpiresIn: int64(h.jwtManager.GetConfig().AccessExpiry.Seconds()),
	})
}

// Login handles user login
func (h *AuthHandler) Login(c *gin.Context) {
	var req models.UserLoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request body",
			"details": err.Error(),
		})
		return
	}

	// Get user by email or username
	user, err := h.userService.GetUserByEmailOrUsername(c.Request.Context(), req.EmailOrUsername)
	if err != nil {
		h.logger.WithError(err).Debug("User not found")
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "Invalid credentials",
		})
		return
	}

	// Check if account is locked
	if user.LockedUntil != nil && user.LockedUntil.After(time.Now()) {
		c.JSON(http.StatusForbidden, gin.H{
			"error": "Account is locked due to too many failed login attempts",
			"locked_until": user.LockedUntil.Format(time.RFC3339),
		})
		return
	}

	// Check if account is active
	if !user.IsActive {
		c.JSON(http.StatusForbidden, gin.H{
			"error": "Account is not active",
		})
		return
	}

	// Verify password
	if err := auth.VerifyPassword(req.Password, user.PasswordHash); err != nil {
		// Increment failed login attempts
		h.userService.IncrementFailedLogin(c.Request.Context(), user.ID)
		
		h.logger.WithFields(logrus.Fields{
			"user_id": user.ID,
			"email": user.Email,
		}).Warn("Failed login attempt")
		
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "Invalid credentials",
		})
		return
	}

	// Update last login
	if err := h.userService.UpdateLastLogin(c.Request.Context(), user.ID); err != nil {
		h.logger.WithError(err).Warn("Failed to update last login")
	}

	// Generate tokens
	var tokenExpiry time.Duration
	if req.RememberMe {
		tokenExpiry = 30 * 24 * time.Hour // 30 days
	} else {
		tokenExpiry = h.jwtManager.GetConfig().AccessExpiry
	}

	// Create custom JWT manager for remember me
	customJWT := h.jwtManager
	if req.RememberMe {
		config := h.jwtManager.GetConfig()
		config.AccessExpiry = tokenExpiry
		customJWT = auth.NewJWTManager(config)
	}

	accessToken, refreshToken, err := customJWT.GenerateTokenPair(user.ID, user.Email, user.Roles)
	if err != nil {
		h.logger.WithError(err).Error("Failed to generate tokens")
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to generate authentication tokens",
		})
		return
	}

	// Store refresh token in cache if available
	if h.cache != nil {
		refreshKey := h.cache.Key("refresh_token", user.ID, refreshToken[:16])
		h.cache.StoreSession(c.Request.Context(), refreshKey, map[string]interface{}{
			"user_id": user.ID,
			"token": refreshToken,
		}, 7*24*time.Hour)
	}

	// Set cookies if remember me
	if req.RememberMe {
		c.SetCookie(
			"access_token",
			accessToken,
			int(tokenExpiry.Seconds()),
			"/",
			"", // Domain
			false, // Secure (set to true in production)
			true, // HttpOnly
		)
	}

	h.logger.WithFields(logrus.Fields{
		"user_id": user.ID,
		"email": user.Email,
		"remember_me": req.RememberMe,
	}).Info("User logged in successfully")

	c.JSON(http.StatusOK, models.UserLoginResponse{
		User: user,
		AccessToken: accessToken,
		RefreshToken: refreshToken,
		ExpiresIn: int64(tokenExpiry.Seconds()),
	})
}

// RefreshToken handles token refresh
func (h *AuthHandler) RefreshToken(c *gin.Context) {
	var req models.RefreshTokenRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request body",
			"details": err.Error(),
		})
		return
	}

	// Validate refresh token
	claims, err := h.jwtManager.ValidateRefreshToken(req.RefreshToken)
	if err != nil {
		h.logger.WithError(err).Debug("Invalid refresh token")
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "Invalid refresh token",
		})
		return
	}

	// Check if refresh token exists in cache
	if h.cache != nil {
		refreshKey := h.cache.Key("refresh_token", claims.UserID, req.RefreshToken[:16])
		var tokenData map[string]interface{}
		if err := h.cache.GetSession(c.Request.Context(), refreshKey, &tokenData); err != nil {
			h.logger.WithError(err).Debug("Refresh token not found in cache")
			c.JSON(http.StatusUnauthorized, gin.H{
				"error": "Invalid refresh token",
			})
			return
		}
	}

	// Get user to refresh roles
	user, err := h.userService.GetUserByID(c.Request.Context(), claims.UserID)
	if err != nil {
		h.logger.WithError(err).Error("Failed to get user for token refresh")
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to refresh token",
		})
		return
	}

	// Generate new access token
	accessToken, err := h.jwtManager.RefreshAccessToken(req.RefreshToken, user.Email, user.Roles)
	if err != nil {
		h.logger.WithError(err).Error("Failed to refresh access token")
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to refresh token",
		})
		return
	}

	h.logger.WithFields(logrus.Fields{
		"user_id": claims.UserID,
	}).Info("Token refreshed successfully")

	c.JSON(http.StatusOK, models.RefreshTokenResponse{
		AccessToken: accessToken,
		ExpiresIn: int64(h.jwtManager.GetConfig().AccessExpiry.Seconds()),
	})
}

// Logout handles user logout
func (h *AuthHandler) Logout(c *gin.Context) {
	// Get user ID from context
	userID, _ := middleware.GetUserID(c)

	// Get refresh token from request
	var req struct {
		RefreshToken string `json:"refresh_token"`
	}
	c.ShouldBindJSON(&req)

	// Invalidate refresh token in cache
	if h.cache != nil && req.RefreshToken != "" && userID != "" {
		refreshKey := h.cache.Key("refresh_token", userID, req.RefreshToken[:16])
		h.cache.DeleteSession(c.Request.Context(), refreshKey)
	}

	// Clear cookies
	c.SetCookie(
		"access_token",
		"",
		-1,
		"/",
		"",
		false,
		true,
	)

	h.logger.WithField("user_id", userID).Info("User logged out")

	c.JSON(http.StatusOK, gin.H{
		"message": "Logged out successfully",
	})
}

// GetProfile gets user profile
func (h *AuthHandler) GetProfile(c *gin.Context) {
	userID, exists := middleware.GetUserID(c)
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "Authentication required",
		})
		return
	}

	user, err := h.userService.GetUserByID(c.Request.Context(), userID)
	if err != nil {
		h.logger.WithError(err).Error("Failed to get user profile")
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to get profile",
		})
		return
	}

	c.JSON(http.StatusOK, user)
}

// UpdateProfile updates user profile
func (h *AuthHandler) UpdateProfile(c *gin.Context) {
	userID, exists := middleware.GetUserID(c)
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "Authentication required",
		})
		return
	}

	var req models.UserUpdateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request body",
			"details": err.Error(),
		})
		return
	}

	user, err := h.userService.UpdateUser(c.Request.Context(), userID, req)
	if err != nil {
		h.logger.WithError(err).Error("Failed to update user profile")
		
		statusCode := http.StatusInternalServerError
		if err.Error() == "username already exists" {
			statusCode = http.StatusConflict
		}
		
		c.JSON(statusCode, gin.H{
			"error": err.Error(),
		})
		return
	}

	h.logger.WithField("user_id", userID).Info("Profile updated successfully")

	c.JSON(http.StatusOK, user)
}

// ChangePassword changes user password
func (h *AuthHandler) ChangePassword(c *gin.Context) {
	userID, exists := middleware.GetUserID(c)
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "Authentication required",
		})
		return
	}

	var req models.PasswordChangeRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request body",
			"details": err.Error(),
		})
		return
	}

	if req.NewPassword != req.ConfirmPassword {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Passwords do not match",
		})
		return
	}

	err := h.userService.ChangePassword(c.Request.Context(), userID, req.CurrentPassword, req.NewPassword)
	if err != nil {
		h.logger.WithError(err).Error("Failed to change password")
		
		statusCode := http.StatusInternalServerError
		if err.Error() == "current password is incorrect" {
			statusCode = http.StatusBadRequest
		}
		
		c.JSON(statusCode, gin.H{
			"error": err.Error(),
		})
		return
	}

	h.logger.WithField("user_id", userID).Info("Password changed successfully")

	c.JSON(http.StatusOK, gin.H{
		"message": "Password changed successfully",
	})
}

// VerifyEmail verifies user email
func (h *AuthHandler) VerifyEmail(c *gin.Context) {
	var req models.EmailVerificationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request body",
			"details": err.Error(),
		})
		return
	}

	err := h.userService.VerifyEmail(c.Request.Context(), req.Token)
	if err != nil {
		h.logger.WithError(err).Error("Failed to verify email")
		
		statusCode := http.StatusInternalServerError
		if err.Error() == "invalid or expired verification token" {
			statusCode = http.StatusBadRequest
		}
		
		c.JSON(statusCode, gin.H{
			"error": err.Error(),
		})
		return
	}

	h.logger.Info("Email verified successfully")

	c.JSON(http.StatusOK, gin.H{
		"message": "Email verified successfully",
	})
}