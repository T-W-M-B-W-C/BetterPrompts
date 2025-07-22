package services

import (
	"testing"
)

func TestNormalizeComplexity(t *testing.T) {
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
			result := normalizeComplexity(tt.input)
			if result != tt.expected {
				t.Errorf("normalizeComplexity(%q) = %q, want %q", tt.input, result, tt.expected)
			}
		})
	}
}

func TestComplexityValidation(t *testing.T) {
	// Test that all normalized values are valid for the technique selector
	validComplexities := map[string]bool{
		"simple":   true,
		"moderate": true,
		"complex":  true,
	}
	
	// Test a variety of inputs
	inputs := []string{
		"simple", "SIMPLE", "low", "easy", "basic",
		"moderate", "MODERATE", "medium", "intermediate",
		"complex", "COMPLEX", "high", "hard", "difficult", "advanced",
		"unknown", "", "123", "very complex",
	}
	
	for _, input := range inputs {
		normalized := normalizeComplexity(input)
		if !validComplexities[normalized] {
			t.Errorf("normalizeComplexity(%q) returned invalid value %q", input, normalized)
		}
	}
}