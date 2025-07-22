package services

import (
	"context"
	"strings"
)

// MockIntentClassifierClient provides a mock implementation for testing
type MockIntentClassifierClient struct {
	baseURL string
	client  interface{}
}

// NewMockIntentClassifierClient creates a new mock client
func NewMockIntentClassifierClient() *IntentClassifierClient {
	return &IntentClassifierClient{
		baseURL: "mock://intent-classifier",
		client:  nil,
	}
}

// ClassifyIntentMock provides deterministic intent classification for testing
func (c *IntentClassifierClient) ClassifyIntentMock(ctx context.Context, text string) (*IntentClassificationResult, error) {
	// Simple rule-based classification for testing
	result := &IntentClassificationResult{
		Confidence: 0.95,
		IntentScores: map[string]float64{},
		Metadata: map[string]interface{}{
			"mock": true,
			"text_length": len(text),
		},
	}

	// Determine intent based on keywords
	textLower := strings.ToLower(text)
	switch {
	case strings.Contains(textLower, "how do i") || strings.Contains(textLower, "how to"):
		result.Intent = "question_answering"
		result.SuggestedTechniques = []string{"chain_of_thought", "structured_output"}
	case strings.Contains(textLower, "explain") || strings.Contains(textLower, "what is"):
		result.Intent = "explanation"
		result.SuggestedTechniques = []string{"few_shot", "chain_of_thought"}
	case strings.Contains(textLower, "design") || strings.Contains(textLower, "create"):
		result.Intent = "creative_generation"
		result.SuggestedTechniques = []string{"tree_of_thoughts", "iterative_refinement"}
	case strings.Contains(textLower, "analyze") || strings.Contains(textLower, "evaluate"):
		result.Intent = "analysis"
		result.SuggestedTechniques = []string{"metacognitive", "self_consistency"}
	default:
		result.Intent = "general"
		result.SuggestedTechniques = []string{"chain_of_thought"}
	}

	// Determine complexity based on text length and keywords
	// IMPORTANT: Must be one of "simple", "moderate", "complex" to match validation
	switch {
	case len(text) < 50 && !strings.Contains(textLower, "complex"):
		result.Complexity = "simple"
	case len(text) < 150 || strings.Contains(textLower, "basic"):
		result.Complexity = "moderate"
	default:
		result.Complexity = "complex"
	}

	// Special handling for specific keywords
	if strings.Contains(textLower, "quantum") || strings.Contains(textLower, "microservices") || strings.Contains(textLower, "architecture") {
		result.Complexity = "complex"
		result.SuggestedTechniques = append(result.SuggestedTechniques, "tree_of_thoughts")
	}

	return result, nil
}