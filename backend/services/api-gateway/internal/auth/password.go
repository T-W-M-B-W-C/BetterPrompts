package auth

import (
	"crypto/rand"
	"crypto/subtle"
	"encoding/base64"
	"errors"
	"fmt"
	"strings"

	"golang.org/x/crypto/bcrypt"
)

const (
	// MinPasswordLength is the minimum allowed password length
	MinPasswordLength = 8
	// MaxPasswordLength is the maximum allowed password length (bcrypt limitation)
	MaxPasswordLength = 72
	// DefaultCost is the default bcrypt cost
	DefaultCost = 12
)

// PasswordPolicy defines password requirements
type PasswordPolicy struct {
	MinLength          int
	RequireUppercase   bool
	RequireLowercase   bool
	RequireNumbers     bool
	RequireSpecialChar bool
	PreventCommon      bool
}

// DefaultPasswordPolicy returns the default password policy
func DefaultPasswordPolicy() PasswordPolicy {
	return PasswordPolicy{
		MinLength:          MinPasswordLength,
		RequireUppercase:   true,
		RequireLowercase:   true,
		RequireNumbers:     true,
		RequireSpecialChar: true,
		PreventCommon:      true,
	}
}

// HashPassword hashes a password using bcrypt
func HashPassword(password string) (string, error) {
	// Validate password length
	if len(password) < MinPasswordLength {
		return "", fmt.Errorf("password must be at least %d characters long", MinPasswordLength)
	}
	if len(password) > MaxPasswordLength {
		return "", fmt.Errorf("password must be at most %d characters long", MaxPasswordLength)
	}
	
	// Generate hash
	hash, err := bcrypt.GenerateFromPassword([]byte(password), DefaultCost)
	if err != nil {
		return "", fmt.Errorf("failed to hash password: %w", err)
	}
	
	return string(hash), nil
}

// VerifyPassword compares a password with its hash
func VerifyPassword(password, hash string) error {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	if err != nil {
		if errors.Is(err, bcrypt.ErrMismatchedHashAndPassword) {
			return errors.New("invalid password")
		}
		return fmt.Errorf("failed to verify password: %w", err)
	}
	return nil
}

// ValidatePassword validates a password against the policy
func ValidatePassword(password string, policy PasswordPolicy) error {
	// Check length
	if len(password) < policy.MinLength {
		return fmt.Errorf("password must be at least %d characters long", policy.MinLength)
	}
	
	// Check character requirements
	var hasUpper, hasLower, hasNumber, hasSpecial bool
	
	for _, char := range password {
		switch {
		case char >= 'A' && char <= 'Z':
			hasUpper = true
		case char >= 'a' && char <= 'z':
			hasLower = true
		case char >= '0' && char <= '9':
			hasNumber = true
		case strings.ContainsRune("!@#$%^&*()_+-=[]{}|;:,.<>?", char):
			hasSpecial = true
		}
	}
	
	if policy.RequireUppercase && !hasUpper {
		return errors.New("password must contain at least one uppercase letter")
	}
	if policy.RequireLowercase && !hasLower {
		return errors.New("password must contain at least one lowercase letter")
	}
	if policy.RequireNumbers && !hasNumber {
		return errors.New("password must contain at least one number")
	}
	if policy.RequireSpecialChar && !hasSpecial {
		return errors.New("password must contain at least one special character")
	}
	
	// Check common passwords
	if policy.PreventCommon && isCommonPassword(password) {
		return errors.New("password is too common, please choose a stronger password")
	}
	
	return nil
}

// GenerateSecureToken generates a cryptographically secure random token
func GenerateSecureToken(length int) (string, error) {
	bytes := make([]byte, length)
	if _, err := rand.Read(bytes); err != nil {
		return "", fmt.Errorf("failed to generate secure token: %w", err)
	}
	return base64.URLEncoding.EncodeToString(bytes), nil
}

// ConstantTimeCompare performs a constant time comparison of two strings
func ConstantTimeCompare(a, b string) bool {
	return subtle.ConstantTimeCompare([]byte(a), []byte(b)) == 1
}

// isCommonPassword checks if a password is in the common passwords list
func isCommonPassword(password string) bool {
	// This is a small subset. In production, use a comprehensive list
	commonPasswords := []string{
		"password", "password123", "123456", "12345678", "1234567890",
		"qwerty", "abc123", "admin", "letmein", "welcome",
		"monkey", "dragon", "baseball", "football", "iloveyou",
		"trustno1", "1234567", "sunshine", "master", "123123",
		"welcome123", "shadow", "ashley", "football123", "jesus",
		"michael", "ninja", "mustang", "password1", "password123!",
	}
	
	lowercasePassword := strings.ToLower(password)
	for _, common := range commonPasswords {
		if lowercasePassword == common {
			return true
		}
	}
	
	return false
}

// PasswordStrength calculates password strength score (0-100)
func PasswordStrength(password string) int {
	score := 0
	
	// Length score (max 30 points)
	length := len(password)
	if length >= 8 {
		score += 10
	}
	if length >= 12 {
		score += 10
	}
	if length >= 16 {
		score += 10
	}
	
	// Character variety score (max 40 points)
	var hasUpper, hasLower, hasNumber, hasSpecial bool
	for _, char := range password {
		switch {
		case char >= 'A' && char <= 'Z':
			hasUpper = true
		case char >= 'a' && char <= 'z':
			hasLower = true
		case char >= '0' && char <= '9':
			hasNumber = true
		case !((char >= 'A' && char <= 'Z') || (char >= 'a' && char <= 'z') || (char >= '0' && char <= '9')):
			hasSpecial = true
		}
	}
	
	if hasUpper {
		score += 10
	}
	if hasLower {
		score += 10
	}
	if hasNumber {
		score += 10
	}
	if hasSpecial {
		score += 10
	}
	
	// Pattern complexity score (max 30 points)
	if !hasRepetitiveChars(password) {
		score += 10
	}
	if !hasSequentialChars(password) {
		score += 10
	}
	if !isCommonPassword(password) {
		score += 10
	}
	
	return score
}

// hasRepetitiveChars checks for repetitive characters
func hasRepetitiveChars(password string) bool {
	for i := 0; i < len(password)-2; i++ {
		if password[i] == password[i+1] && password[i+1] == password[i+2] {
			return true
		}
	}
	return false
}

// hasSequentialChars checks for sequential characters
func hasSequentialChars(password string) bool {
	for i := 0; i < len(password)-2; i++ {
		if password[i]+1 == password[i+1] && password[i+1]+1 == password[i+2] {
			return true
		}
		if password[i]-1 == password[i+1] && password[i+1]-1 == password[i+2] {
			return true
		}
	}
	return false
}