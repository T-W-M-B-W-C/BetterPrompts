package rules

import (
	"fmt"
	"math"
	"sort"
	"strings"

	"github.com/betterprompts/technique-selector/internal/models"
	"github.com/sirupsen/logrus"
)

// Engine is the rule-based technique selection engine
type Engine struct {
	config *models.RulesConfig
	logger *logrus.Logger
}

// NewEngine creates a new technique selection engine
func NewEngine(config *models.RulesConfig, logger *logrus.Logger) *Engine {
	return &Engine{
		config: config,
		logger: logger,
	}
}

// SelectTechniques selects appropriate techniques based on the request
func (e *Engine) SelectTechniques(req *models.SelectionRequest) (*models.SelectionResponse, error) {
	e.logger.WithFields(logrus.Fields{
		"intent":     req.Intent,
		"complexity": req.Complexity,
		"text_len":   len(req.Text),
	}).Debug("Selecting techniques")

	// Calculate enhanced complexity if not provided
	if req.Complexity == 0 {
		req.Complexity = e.calculateComplexity(req.Text)
	}

	// Score all techniques
	scoredTechniques := e.scoreTechniques(req)

	// Filter and sort techniques
	selectedTechniques := e.filterAndSort(scoredTechniques, req)

	// Apply combination rules
	selectedTechniques = e.applyCombinationRules(selectedTechniques)

	// Limit number of techniques
	maxTechniques := req.MaxTechniques
	if maxTechniques == 0 {
		maxTechniques = e.config.SelectionRules.MaxTechniques
	}
	if len(selectedTechniques) > maxTechniques {
		selectedTechniques = selectedTechniques[:maxTechniques]
	}

	// Build response
	response := &models.SelectionResponse{
		Techniques: selectedTechniques,
		Confidence: e.calculateOverallConfidence(selectedTechniques),
		Reasoning:  e.generateReasoning(selectedTechniques, req),
		Metadata: map[string]interface{}{
			"complexity":     req.Complexity,
			"intent":         req.Intent,
			"word_count":     len(strings.Fields(req.Text)),
			"techniques_evaluated": len(scoredTechniques),
		},
	}

	if len(selectedTechniques) > 0 {
		response.PrimaryTechnique = selectedTechniques[0].ID
	}

	return response, nil
}

// scoreTechniques scores all techniques based on the request
func (e *Engine) scoreTechniques(req *models.SelectionRequest) []models.SelectedTechnique {
	var scoredTechniques []models.SelectedTechnique

	for _, technique := range e.config.Techniques {
		score, confidence, reasoning := e.scoreTechnique(technique, req)
		
		if score > 0 {
			selected := models.SelectedTechnique{
				ID:          technique.ID,
				Name:        technique.Name,
				Description: technique.Description,
				Template:    technique.Template,
				Priority:    technique.Priority,
				Score:       score,
				Confidence:  confidence,
				Reasoning:   reasoning,
				Parameters:  technique.Parameters,
			}
			scoredTechniques = append(scoredTechniques, selected)
		}
	}

	return scoredTechniques
}

// scoreTechnique scores a single technique
func (e *Engine) scoreTechnique(technique models.Technique, req *models.SelectionRequest) (float64, float64, string) {
	score := 0.0
	confidence := 0.0
	var reasons []string

	conditions := technique.Conditions

	// Check intent match
	intentMatch := false
	if len(conditions.Intents) > 0 {
		for _, intent := range conditions.Intents {
			if intent == req.Intent {
				intentMatch = true
				score += 30.0
				reasons = append(reasons, fmt.Sprintf("matches intent '%s'", intent))
				break
			}
		}
		if !intentMatch && len(conditions.Intents) > 0 {
			// Intent specified but doesn't match
			return 0, 0, ""
		}
	}

	// Check complexity threshold
	if conditions.ComplexityThreshold > 0 && req.Complexity >= conditions.ComplexityThreshold {
		score += 20.0
		reasons = append(reasons, fmt.Sprintf("complexity %.2f >= %.2f", req.Complexity, conditions.ComplexityThreshold))
	} else if conditions.ComplexityThreshold > 0 && req.Complexity < conditions.ComplexityThreshold {
		// Complexity too low
		return 0, 0, ""
	}

	// Check maximum complexity threshold
	if conditions.ComplexityThresholdMax > 0 && req.Complexity <= conditions.ComplexityThresholdMax {
		score += 10.0
		reasons = append(reasons, fmt.Sprintf("complexity %.2f <= %.2f", req.Complexity, conditions.ComplexityThresholdMax))
	} else if conditions.ComplexityThresholdMax > 0 && req.Complexity > conditions.ComplexityThresholdMax {
		// Complexity too high
		return 0, 0, ""
	}

	// Check keywords
	keywordMatches := 0
	textLower := strings.ToLower(req.Text)
	for _, keyword := range conditions.Keywords {
		if strings.Contains(textLower, strings.ToLower(keyword)) {
			keywordMatches++
		}
	}
	if keywordMatches > 0 {
		keywordScore := math.Min(float64(keywordMatches)*10, 30)
		score += keywordScore
		reasons = append(reasons, fmt.Sprintf("%d keyword matches", keywordMatches))
	}

	// Check multi-step indicators
	multiStepMatches := 0
	for _, indicator := range conditions.MultiStepIndicators {
		if strings.Contains(textLower, strings.ToLower(indicator)) {
			multiStepMatches++
		}
	}
	if multiStepMatches > 0 {
		score += float64(multiStepMatches) * 15
		reasons = append(reasons, "contains multi-step indicators")
	}

	// Check boolean conditions
	if conditions.RequiresExploration && strings.Contains(textLower, "explore") {
		score += 15
		reasons = append(reasons, "requires exploration")
	}
	if conditions.RequiresPattern && (strings.Contains(textLower, "pattern") || strings.Contains(textLower, "example")) {
		score += 15
		reasons = append(reasons, "requires pattern matching")
	}
	if conditions.RequiresAccuracy && (strings.Contains(textLower, "accurate") || strings.Contains(textLower, "verify")) {
		score += 15
		reasons = append(reasons, "requires accuracy")
	}
	if conditions.SimpleRequest && req.Complexity < 0.3 {
		score += 20
		reasons = append(reasons, "simple request")
	}

	// Apply priority boost based on intent
	if boost, exists := e.config.SelectionRules.IntentPriorityBoost[req.Intent][technique.ID]; exists {
		score += float64(boost) * 10
		reasons = append(reasons, fmt.Sprintf("intent priority boost +%d", boost))
	}

	// Apply base priority
	score += float64(technique.Priority)

	// Calculate confidence
	if score > 0 {
		confidence = math.Min(score/100.0, 1.0)
	}

	reasoning := strings.Join(reasons, ", ")
	return score, confidence, reasoning
}

// filterAndSort filters techniques by minimum confidence and sorts by score
func (e *Engine) filterAndSort(techniques []models.SelectedTechnique, req *models.SelectionRequest) []models.SelectedTechnique {
	var filtered []models.SelectedTechnique

	minConfidence := e.config.SelectionRules.MinConfidence
	for _, tech := range techniques {
		if tech.Confidence >= minConfidence {
			filtered = append(filtered, tech)
		}
	}

	// Sort by score (descending)
	sort.Slice(filtered, func(i, j int) bool {
		return filtered[i].Score > filtered[j].Score
	})

	return filtered
}

// applyCombinationRules applies compatibility rules to selected techniques
func (e *Engine) applyCombinationRules(techniques []models.SelectedTechnique) []models.SelectedTechnique {
	if len(techniques) <= 1 {
		return techniques
	}

	var result []models.SelectedTechnique
	result = append(result, techniques[0]) // Always keep the highest scoring technique

	for i := 1; i < len(techniques); i++ {
		candidate := techniques[i]
		compatible := true

		// Check incompatible combinations
		for _, existing := range result {
			if e.areIncompatible(existing.ID, candidate.ID) {
				compatible = false
				e.logger.WithFields(logrus.Fields{
					"technique1": existing.ID,
					"technique2": candidate.ID,
				}).Debug("Techniques are incompatible")
				break
			}
		}

		if compatible {
			result = append(result, candidate)
		}
	}

	return result
}

// areIncompatible checks if two techniques are incompatible
func (e *Engine) areIncompatible(tech1, tech2 string) bool {
	for _, combo := range e.config.SelectionRules.IncompatibleCombinations {
		if (combo[0] == tech1 && combo[1] == tech2) || (combo[0] == tech2 && combo[1] == tech1) {
			return true
		}
	}
	return false
}

// calculateComplexity calculates text complexity
func (e *Engine) calculateComplexity(text string) float64 {
	complexity := 0.0
	factors := e.config.ComplexityFactors

	// Word count factor
	wordCount := len(strings.Fields(text))
	for _, wcRange := range factors.WordCount {
		if wordCount >= wcRange.Range[0] && (wcRange.Range[1] == -1 || wordCount <= wcRange.Range[1]) {
			complexity += wcRange.Score
			break
		}
	}

	// Multi-part question
	if strings.Count(text, "?") > 1 || strings.Contains(text, " and ") {
		complexity += factors.MultiPartQuestion
	}

	// Technical terms (simplified check)
	technicalTerms := []string{"algorithm", "function", "database", "API", "implement", "optimize", "analyze"}
	for _, term := range technicalTerms {
		if strings.Contains(strings.ToLower(text), term) {
			complexity += factors.TechnicalTerms / float64(len(technicalTerms))
		}
	}

	// Abstract concepts
	abstractTerms := []string{"concept", "theory", "principle", "philosophy", "abstract"}
	for _, term := range abstractTerms {
		if strings.Contains(strings.ToLower(text), term) {
			complexity += factors.AbstractConcepts / float64(len(abstractTerms))
		}
	}

	return math.Min(complexity, 1.0)
}

// calculateOverallConfidence calculates the overall confidence
func (e *Engine) calculateOverallConfidence(techniques []models.SelectedTechnique) float64 {
	if len(techniques) == 0 {
		return 0
	}

	// Weighted average based on scores
	totalScore := 0.0
	totalWeightedConfidence := 0.0

	for _, tech := range techniques {
		totalScore += tech.Score
		totalWeightedConfidence += tech.Confidence * tech.Score
	}

	if totalScore == 0 {
		return 0
	}

	return totalWeightedConfidence / totalScore
}

// generateReasoning generates human-readable reasoning for the selection
func (e *Engine) generateReasoning(techniques []models.SelectedTechnique, req *models.SelectionRequest) string {
	parts := []string{
		fmt.Sprintf("Based on intent '%s' and complexity %.2f", req.Intent, req.Complexity),
	}

	if len(techniques) == 0 {
		parts = append(parts, "no techniques were selected as none met the criteria")
	} else if len(techniques) == 1 {
		parts = append(parts, fmt.Sprintf("selected '%s' technique because it %s", 
			techniques[0].Name, techniques[0].Reasoning))
	} else {
		techNames := make([]string, len(techniques))
		for i, tech := range techniques {
			techNames[i] = tech.Name
		}
		parts = append(parts, fmt.Sprintf("selected %d techniques: %s", 
			len(techniques), strings.Join(techNames, ", ")))
		parts = append(parts, fmt.Sprintf("Primary technique '%s' scored highest because it %s",
			techniques[0].Name, techniques[0].Reasoning))
	}

	return strings.Join(parts, ". ")
}