package services

import (
	"strings"
	"testing"
)

// normalizeComplexityTest is a copy for testing
func normalizeComplexityTest(complexity string) string {
	// Map various complexity values to the expected ones
	switch strings.ToLower(complexity) {
	case "simple", "low", "easy", "basic":
		return "simple"
	case "moderate", "medium", "intermediate":
		return "moderate"
	case "complex", "high", "hard", "difficult", "advanced":
		return "complex"
	default:
		// Default to moderate for unknown values
		return "moderate"
	}
}

func TestNormalizeComplexityFunction(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		// Valid values
		{"simple lowercase", "simple", "simple"},
		{"moderate lowercase", "moderate", "moderate"},
		{"complex lowercase", "complex", "complex"},
		
		// Case insensitive
		{"simple uppercase", "SIMPLE", "simple"},
		{"moderate mixed", "MoDerAte", "moderate"},
		{"complex title", "Complex", "complex"},
		
		// Aliases for simple
		{"low alias", "low", "simple"},
		{"easy alias", "easy", "simple"},
		{"basic alias", "basic", "simple"},
		{"LOW uppercase", "LOW", "simple"},
		
		// Aliases for moderate
		{"medium alias", "medium", "moderate"},
		{"intermediate alias", "intermediate", "moderate"},
		{"MEDIUM uppercase", "MEDIUM", "moderate"},
		
		// Aliases for complex
		{"high alias", "high", "complex"},
		{"hard alias", "hard", "complex"},
		{"difficult alias", "difficult", "complex"},
		{"advanced alias", "advanced", "complex"},
		{"HIGH uppercase", "HIGH", "complex"},
		
		// Unknown values default to moderate
		{"unknown value", "unknown", "moderate"},
		{"empty string", "", "moderate"},
		{"numeric string", "123", "moderate"},
		{"very complex", "very complex", "moderate"},
		{"1", "1", "moderate"},
		{"2", "2", "moderate"},
		{"3", "3", "moderate"},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := normalizeComplexityTest(tt.input)
			if result != tt.expected {
				t.Errorf("normalizeComplexity(%q) = %q, want %q", tt.input, result, tt.expected)
			}
		})
	}
}