package services

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/betterprompts/api-gateway/internal/auth"
	"github.com/betterprompts/api-gateway/internal/models"
	"github.com/google/uuid"
	"github.com/lib/pq"
)

// UserService handles user-related operations
type UserService struct {
	db *DatabaseService
}

// NewUserService creates a new user service
func NewUserService(db *DatabaseService) *UserService {
	return &UserService{
		db: db,
	}
}

// CreateUser creates a new user
func (s *UserService) CreateUser(ctx context.Context, req models.UserRegistrationRequest) (*models.User, error) {
	// Validate password
	if err := auth.ValidatePassword(req.Password, auth.DefaultPasswordPolicy()); err != nil {
		return nil, fmt.Errorf("password validation failed: %w", err)
	}

	// Hash password
	passwordHash, err := auth.HashPassword(req.Password)
	if err != nil {
		return nil, fmt.Errorf("failed to hash password: %w", err)
	}

	// Generate verification token
	verifyToken, err := auth.GenerateSecureToken(32)
	if err != nil {
		return nil, fmt.Errorf("failed to generate verification token: %w", err)
	}

	// Create user
	user := &models.User{
		ID:               uuid.New().String(),
		Email:            strings.ToLower(req.Email),
		Username:         req.Username,
		PasswordHash:     passwordHash,
		FirstName:        req.FirstName,
		LastName:         req.LastName,
		Roles:            []string{"user"}, // Default role
		IsActive:         true,
		IsEmailVerified:  false,
		EmailVerifyToken: verifyToken,
		Preferences:      make(map[string]interface{}),
		CreatedAt:        time.Now(),
		UpdatedAt:        time.Now(),
	}

	// Convert preferences to JSON
	prefsJSON, err := json.Marshal(user.Preferences)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal preferences: %w", err)
	}

	// Insert user
	query := `
		INSERT INTO users (
			id, email, username, password_hash, first_name, last_name,
			roles, is_active, is_email_verified, email_verify_token,
			preferences, created_at, updated_at
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
		)`

	_, err = s.db.db.ExecContext(ctx, query,
		user.ID, user.Email, user.Username, user.PasswordHash,
		user.FirstName, user.LastName, pq.Array(user.Roles),
		user.IsActive, user.IsEmailVerified, user.EmailVerifyToken,
		prefsJSON, user.CreatedAt, user.UpdatedAt,
	)

	if err != nil {
		// Check for unique constraint violations
		if pqErr, ok := err.(*pq.Error); ok {
			if pqErr.Code == "23505" { // unique_violation
				if strings.Contains(pqErr.Error(), "email") {
					return nil, errors.New("email already exists")
				}
				if strings.Contains(pqErr.Error(), "username") {
					return nil, errors.New("username already exists")
				}
			}
		}
		return nil, fmt.Errorf("failed to create user: %w", err)
	}

	// TODO: Send verification email

	return user, nil
}

// GetUserByID retrieves a user by ID
func (s *UserService) GetUserByID(ctx context.Context, userID string) (*models.User, error) {
	user := &models.User{}
	var prefsJSON []byte

	query := `
		SELECT 
			id, email, username, password_hash, first_name, last_name,
			roles, is_active, is_email_verified, email_verify_token,
			password_reset_token, password_reset_expiry, last_login,
			failed_login_attempts, locked_until, preferences,
			created_at, updated_at
		FROM users
		WHERE id = $1`

	err := s.db.db.QueryRowContext(ctx, query, userID).Scan(
		&user.ID, &user.Email, &user.Username, &user.PasswordHash,
		&user.FirstName, &user.LastName, pq.Array(&user.Roles),
		&user.IsActive, &user.IsEmailVerified, &user.EmailVerifyToken,
		&user.PasswordResetToken, &user.PasswordResetExpiry, &user.LastLogin,
		&user.FailedLoginAttempts, &user.LockedUntil, &prefsJSON,
		&user.CreatedAt, &user.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, errors.New("user not found")
		}
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	// Parse preferences
	if err := json.Unmarshal(prefsJSON, &user.Preferences); err != nil {
		user.Preferences = make(map[string]interface{})
	}

	return user, nil
}

// GetUserByEmail retrieves a user by email
func (s *UserService) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	user := &models.User{}
	var prefsJSON []byte

	query := `
		SELECT 
			id, email, username, password_hash, first_name, last_name,
			roles, is_active, is_email_verified, email_verify_token,
			password_reset_token, password_reset_expiry, last_login,
			failed_login_attempts, locked_until, preferences,
			created_at, updated_at
		FROM users
		WHERE LOWER(email) = LOWER($1)`

	err := s.db.db.QueryRowContext(ctx, query, email).Scan(
		&user.ID, &user.Email, &user.Username, &user.PasswordHash,
		&user.FirstName, &user.LastName, pq.Array(&user.Roles),
		&user.IsActive, &user.IsEmailVerified, &user.EmailVerifyToken,
		&user.PasswordResetToken, &user.PasswordResetExpiry, &user.LastLogin,
		&user.FailedLoginAttempts, &user.LockedUntil, &prefsJSON,
		&user.CreatedAt, &user.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, errors.New("user not found")
		}
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	// Parse preferences
	if err := json.Unmarshal(prefsJSON, &user.Preferences); err != nil {
		user.Preferences = make(map[string]interface{})
	}

	return user, nil
}

// GetUserByUsername retrieves a user by username
func (s *UserService) GetUserByUsername(ctx context.Context, username string) (*models.User, error) {
	user := &models.User{}
	var prefsJSON []byte

	query := `
		SELECT 
			id, email, username, password_hash, first_name, last_name,
			roles, is_active, is_email_verified, email_verify_token,
			password_reset_token, password_reset_expiry, last_login,
			failed_login_attempts, locked_until, preferences,
			created_at, updated_at
		FROM users
		WHERE LOWER(username) = LOWER($1)`

	err := s.db.db.QueryRowContext(ctx, query, username).Scan(
		&user.ID, &user.Email, &user.Username, &user.PasswordHash,
		&user.FirstName, &user.LastName, pq.Array(&user.Roles),
		&user.IsActive, &user.IsEmailVerified, &user.EmailVerifyToken,
		&user.PasswordResetToken, &user.PasswordResetExpiry, &user.LastLogin,
		&user.FailedLoginAttempts, &user.LockedUntil, &prefsJSON,
		&user.CreatedAt, &user.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, errors.New("user not found")
		}
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	// Parse preferences
	if err := json.Unmarshal(prefsJSON, &user.Preferences); err != nil {
		user.Preferences = make(map[string]interface{})
	}

	return user, nil
}

// GetUserByEmailOrUsername retrieves a user by email or username
func (s *UserService) GetUserByEmailOrUsername(ctx context.Context, emailOrUsername string) (*models.User, error) {
	// Check if it's an email
	if strings.Contains(emailOrUsername, "@") {
		return s.GetUserByEmail(ctx, emailOrUsername)
	}
	// Otherwise, try username
	return s.GetUserByUsername(ctx, emailOrUsername)
}

// UpdateUser updates user information
func (s *UserService) UpdateUser(ctx context.Context, userID string, req models.UserUpdateRequest) (*models.User, error) {
	// Get existing user
	user, err := s.GetUserByID(ctx, userID)
	if err != nil {
		return nil, err
	}

	// Update fields if provided
	if req.FirstName != nil {
		user.FirstName = *req.FirstName
	}
	if req.LastName != nil {
		user.LastName = *req.LastName
	}
	if req.Username != nil {
		user.Username = *req.Username
	}
	if req.Preferences != nil {
		user.Preferences = *req.Preferences
	}
	user.UpdatedAt = time.Now()

	// Convert preferences to JSON
	prefsJSON, err := json.Marshal(user.Preferences)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal preferences: %w", err)
	}

	// Update user
	query := `
		UPDATE users SET
			username = $2, first_name = $3, last_name = $4,
			preferences = $5, updated_at = $6
		WHERE id = $1`

	_, err = s.db.db.ExecContext(ctx, query,
		user.ID, user.Username, user.FirstName, user.LastName,
		prefsJSON, user.UpdatedAt,
	)

	if err != nil {
		if pqErr, ok := err.(*pq.Error); ok {
			if pqErr.Code == "23505" && strings.Contains(pqErr.Error(), "username") {
				return nil, errors.New("username already exists")
			}
		}
		return nil, fmt.Errorf("failed to update user: %w", err)
	}

	return user, nil
}

// UpdateLastLogin updates the user's last login time
func (s *UserService) UpdateLastLogin(ctx context.Context, userID string) error {
	now := time.Now()
	query := `
		UPDATE users SET
			last_login = $2,
			failed_login_attempts = 0,
			locked_until = NULL
		WHERE id = $1`

	_, err := s.db.db.ExecContext(ctx, query, userID, now)
	if err != nil {
		return fmt.Errorf("failed to update last login: %w", err)
	}

	return nil
}

// IncrementFailedLogin increments failed login attempts and locks account if necessary
func (s *UserService) IncrementFailedLogin(ctx context.Context, userID string) error {
	// First, get current failed attempts
	var failedAttempts int
	query := `SELECT failed_login_attempts FROM users WHERE id = $1`
	err := s.db.db.QueryRowContext(ctx, query, userID).Scan(&failedAttempts)
	if err != nil {
		return fmt.Errorf("failed to get failed attempts: %w", err)
	}

	failedAttempts++

	// Lock account after 5 failed attempts
	var lockUntil *time.Time
	if failedAttempts >= 5 {
		lockTime := time.Now().Add(30 * time.Minute)
		lockUntil = &lockTime
	}

	// Update failed attempts and lock status
	updateQuery := `
		UPDATE users SET
			failed_login_attempts = $2,
			locked_until = $3
		WHERE id = $1`

	_, err = s.db.db.ExecContext(ctx, updateQuery, userID, failedAttempts, lockUntil)
	if err != nil {
		return fmt.Errorf("failed to update failed login: %w", err)
	}

	return nil
}

// ChangePassword changes user's password
func (s *UserService) ChangePassword(ctx context.Context, userID string, currentPassword, newPassword string) error {
	// Get user
	user, err := s.GetUserByID(ctx, userID)
	if err != nil {
		return err
	}

	// Verify current password
	if err := auth.VerifyPassword(currentPassword, user.PasswordHash); err != nil {
		return errors.New("current password is incorrect")
	}

	// Validate new password
	if err := auth.ValidatePassword(newPassword, auth.DefaultPasswordPolicy()); err != nil {
		return fmt.Errorf("password validation failed: %w", err)
	}

	// Hash new password
	newHash, err := auth.HashPassword(newPassword)
	if err != nil {
		return fmt.Errorf("failed to hash password: %w", err)
	}

	// Update password
	query := `UPDATE users SET password_hash = $2, updated_at = $3 WHERE id = $1`
	_, err = s.db.db.ExecContext(ctx, query, userID, newHash, time.Now())
	if err != nil {
		return fmt.Errorf("failed to update password: %w", err)
	}

	return nil
}

// VerifyEmail verifies user's email
func (s *UserService) VerifyEmail(ctx context.Context, token string) error {
	query := `
		UPDATE users SET
			is_email_verified = true,
			email_verify_token = '',
			updated_at = $2
		WHERE email_verify_token = $1 AND is_email_verified = false`

	result, err := s.db.db.ExecContext(ctx, query, token, time.Now())
	if err != nil {
		return fmt.Errorf("failed to verify email: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rowsAffected == 0 {
		return errors.New("invalid or expired verification token")
	}

	return nil
}

// DeleteUser deletes a user
func (s *UserService) DeleteUser(ctx context.Context, userID string) error {
	query := `DELETE FROM users WHERE id = $1`
	result, err := s.db.db.ExecContext(ctx, query, userID)
	if err != nil {
		return fmt.Errorf("failed to delete user: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rowsAffected == 0 {
		return errors.New("user not found")
	}

	return nil
}