package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// Technique represents a prompt engineering technique
type Technique struct {
	ID          string   `json:"id"`
	Name        string   `json:"name"`
	Description string   `json:"description"`
	UseCases    []string `json:"use_cases"`
	Examples    []string `json:"examples"`
}

// GetTechniques returns available prompt engineering techniques
func GetTechniques() gin.HandlerFunc {
	techniques := []Technique{
		{
			ID:          "chain_of_thought",
			Name:        "Chain of Thought",
			Description: "Step-by-step reasoning that breaks down complex problems into manageable parts",
			UseCases:    []string{"problem solving", "mathematical reasoning", "logical analysis"},
			Examples: []string{
				"Let me work through this step-by-step...",
				"First, I'll identify the key components...",
			},
		},
		{
			ID:          "tree_of_thoughts",
			Name:        "Tree of Thoughts",
			Description: "Explores multiple reasoning paths and evaluates different approaches",
			UseCases:    []string{"complex planning", "decision making", "creative problem solving"},
			Examples: []string{
				"I'll explore different approaches to this problem...",
				"Let me consider multiple perspectives...",
			},
		},
		{
			ID:          "few_shot",
			Name:        "Few-Shot Learning",
			Description: "Provides examples to guide the AI's response format and style",
			UseCases:    []string{"formatting tasks", "style matching", "pattern recognition"},
			Examples: []string{
				"Here are some examples of what I'm looking for...",
				"Following the pattern from these examples...",
			},
		},
		{
			ID:          "zero_shot",
			Name:        "Zero-Shot Learning",
			Description: "Direct task completion without examples, relying on the AI's general knowledge",
			UseCases:    []string{"general questions", "straightforward tasks", "quick responses"},
			Examples: []string{
				"Please provide a direct answer to...",
				"Without additional context, here's my response...",
			},
		},
		{
			ID:          "self_consistency",
			Name:        "Self-Consistency",
			Description: "Multiple attempts at solving with consistency verification",
			UseCases:    []string{"accuracy-critical tasks", "mathematical problems", "fact verification"},
			Examples: []string{
				"Let me solve this multiple ways to verify...",
				"I'll check my answer using different approaches...",
			},
		},
		{
			ID:          "constitutional_ai",
			Name:        "Constitutional AI",
			Description: "Applies ethical principles and guidelines to responses",
			UseCases:    []string{"sensitive topics", "ethical considerations", "safety-critical tasks"},
			Examples: []string{
				"Considering the ethical implications...",
				"Following safety guidelines, I would suggest...",
			},
		},
		{
			ID:          "iterative_refinement",
			Name:        "Iterative Refinement",
			Description: "Progressive improvement through multiple iterations",
			UseCases:    []string{"creative writing", "code optimization", "design improvement"},
			Examples: []string{
				"Let me refine this approach...",
				"Building on the previous version...",
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