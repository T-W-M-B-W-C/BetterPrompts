package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// TechniqueEffectiveness represents the effectiveness metrics
type TechniqueEffectiveness struct {
	Overall  float64            `json:"overall"`
	ByIntent map[string]float64 `json:"byIntent"`
}

// Technique represents a prompt engineering technique
type Technique struct {
	ID            string                 `json:"id"`
	Name          string                 `json:"name"`
	Category      string                 `json:"category"`
	Description   string                 `json:"description"`
	Complexity    int                    `json:"complexity"`
	Examples      []string               `json:"examples"`
	Parameters    map[string]interface{} `json:"parameters,omitempty"`
	Effectiveness TechniqueEffectiveness `json:"effectiveness"`
}

// GetTechniques returns available prompt engineering techniques
func GetTechniques() gin.HandlerFunc {
	techniques := []Technique{
		{
			ID:          "chain_of_thought",
			Name:        "Chain of Thought",
			Category:    "reasoning",
			Description: "Step-by-step reasoning that breaks down complex problems into manageable parts",
			Complexity:  2,
			Examples: []string{
				"Let me work through this step-by-step...",
				"First, I'll identify the key components...",
			},
			Effectiveness: TechniqueEffectiveness{
				Overall: 0.85,
				ByIntent: map[string]float64{
					"problem_solving": 0.9,
					"analysis": 0.85,
					"explanation": 0.8,
				},
			},
		},
		{
			ID:          "tree_of_thoughts",
			Name:        "Tree of Thoughts",
			Category:    "reasoning",
			Description: "Explores multiple reasoning paths and evaluates different approaches",
			Complexity:  3,
			Examples: []string{
				"I'll explore different approaches to this problem...",
				"Let me consider multiple perspectives...",
			},
			Effectiveness: TechniqueEffectiveness{
				Overall: 0.88,
				ByIntent: map[string]float64{
					"planning": 0.92,
					"decision_making": 0.9,
					"creative": 0.85,
				},
			},
		},
		{
			ID:          "few_shot",
			Name:        "Few-Shot Learning",
			Category:    "learning",
			Description: "Provides examples to guide the AI's response format and style",
			Complexity:  1,
			Examples: []string{
				"Here are some examples of what I'm looking for...",
				"Following the pattern from these examples...",
			},
			Effectiveness: TechniqueEffectiveness{
				Overall: 0.82,
				ByIntent: map[string]float64{
					"formatting": 0.9,
					"style_matching": 0.88,
					"pattern_recognition": 0.85,
				},
			},
		},
		{
			ID:          "zero_shot",
			Name:        "Zero-Shot Learning",
			Category:    "learning",
			Description: "Direct task completion without examples, relying on the AI's general knowledge",
			Complexity:  0,
			Examples: []string{
				"Please provide a direct answer to...",
				"Without additional context, here's my response...",
			},
			Effectiveness: TechniqueEffectiveness{
				Overall: 0.75,
				ByIntent: map[string]float64{
					"general": 0.8,
					"straightforward": 0.78,
					"quick_response": 0.85,
				},
			},
		},
		{
			ID:          "self_consistency",
			Name:        "Self-Consistency",
			Category:    "verification",
			Description: "Multiple attempts at solving with consistency verification",
			Complexity:  2,
			Examples: []string{
				"Let me solve this multiple ways to verify...",
				"I'll check my answer using different approaches...",
			},
			Effectiveness: TechniqueEffectiveness{
				Overall: 0.91,
				ByIntent: map[string]float64{
					"accuracy_critical": 0.95,
					"mathematical": 0.93,
					"verification": 0.9,
				},
			},
		},
		{
			ID:          "constitutional_ai",
			Name:        "Constitutional AI",
			Category:    "safety",
			Description: "Applies ethical principles and guidelines to responses",
			Complexity:  2,
			Examples: []string{
				"Considering the ethical implications...",
				"Following safety guidelines, I would suggest...",
			},
			Effectiveness: TechniqueEffectiveness{
				Overall: 0.87,
				ByIntent: map[string]float64{
					"sensitive": 0.92,
					"ethical": 0.9,
					"safety": 0.95,
				},
			},
		},
		{
			ID:          "iterative_refinement",
			Name:        "Iterative Refinement",
			Category:    "optimization",
			Description: "Progressive improvement through multiple iterations",
			Complexity:  2,
			Examples: []string{
				"Let me refine this approach...",
				"Building on the previous version...",
			},
			Effectiveness: TechniqueEffectiveness{
				Overall: 0.84,
				ByIntent: map[string]float64{
					"creative_writing": 0.88,
					"optimization": 0.86,
					"improvement": 0.85,
				},
			},
		},
	}

	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"techniques": techniques,
			"total":      len(techniques),
		})
	}
}