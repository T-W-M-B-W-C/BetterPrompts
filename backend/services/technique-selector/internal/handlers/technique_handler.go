package handlers

import (
	"net/http"

	"github.com/betterprompts/technique-selector/internal/models"
	"github.com/betterprompts/technique-selector/internal/rules"
	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

// TechniqueHandler handles technique selection requests
type TechniqueHandler struct {
	engine *rules.Engine
	logger *logrus.Logger
}

// NewTechniqueHandler creates a new technique handler
func NewTechniqueHandler(engine *rules.Engine, logger *logrus.Logger) *TechniqueHandler {
	return &TechniqueHandler{
		engine: engine,
		logger: logger,
	}
}

// SelectTechniques handles POST /select endpoint
func (h *TechniqueHandler) SelectTechniques(c *gin.Context) {
	var req models.SelectionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.logger.WithError(err).Error("Failed to bind request")
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request body",
			"details": err.Error(),
		})
		return
	}

	// Log request
	h.logger.WithFields(logrus.Fields{
		"intent":     req.Intent,
		"complexity": req.Complexity,
		"text_len":   len(req.Text),
	}).Info("Selecting techniques")

	// Select techniques
	response, err := h.engine.SelectTechniques(&req)
	if err != nil {
		h.logger.WithError(err).Error("Failed to select techniques")
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to select techniques",
			"details": err.Error(),
		})
		return
	}

	// Log response
	h.logger.WithFields(logrus.Fields{
		"techniques_count": len(response.Techniques),
		"primary_technique": response.PrimaryTechnique,
		"confidence": response.Confidence,
	}).Info("Techniques selected")

	c.JSON(http.StatusOK, response)
}

// ListTechniques handles GET /techniques endpoint
func (h *TechniqueHandler) ListTechniques(c *gin.Context) {
	// This would return all available techniques
	// For now, we'll return a placeholder
	techniques := []gin.H{
		{
			"id":          "chain_of_thought",
			"name":        "Chain of Thought",
			"description": "Step-by-step reasoning that breaks down complex problems",
		},
		{
			"id":          "tree_of_thoughts",
			"name":        "Tree of Thoughts",
			"description": "Explores multiple reasoning paths and evaluates different approaches",
		},
		{
			"id":          "few_shot",
			"name":        "Few-Shot Learning",
			"description": "Provides examples to guide the response format and style",
		},
		{
			"id":          "zero_shot",
			"name":        "Zero-Shot Learning",
			"description": "Direct task completion without examples",
		},
		{
			"id":          "self_consistency",
			"name":        "Self-Consistency",
			"description": "Multiple attempts at solving with consistency verification",
		},
		{
			"id":          "constitutional_ai",
			"name":        "Constitutional AI",
			"description": "Applies ethical principles and guidelines to responses",
		},
		{
			"id":          "iterative_refinement",
			"name":        "Iterative Refinement",
			"description": "Progressive improvement through multiple iterations",
		},
		{
			"id":          "role_based",
			"name":        "Role-Based Prompting",
			"description": "Assumes a specific role or expertise for the response",
		},
		{
			"id":          "structured_output",
			"name":        "Structured Output",
			"description": "Provides response in a specific structured format",
		},
		{
			"id":          "metacognitive",
			"name":        "Metacognitive Prompting",
			"description": "Reflects on the thinking process while solving",
		},
	}

	c.JSON(http.StatusOK, gin.H{
		"techniques": techniques,
		"total":      len(techniques),
	})
}

// GetTechniqueByID handles GET /techniques/:id endpoint
func (h *TechniqueHandler) GetTechniqueByID(c *gin.Context) {
	techniqueID := c.Param("id")
	
	// In a real implementation, this would look up the technique from the config
	// For now, return a placeholder
	c.JSON(http.StatusOK, gin.H{
		"id":          techniqueID,
		"name":        "Technique Name",
		"description": "Technique description",
		"examples": []string{
			"Example 1",
			"Example 2",
		},
		"use_cases": []string{
			"Use case 1",
			"Use case 2",
		},
	})
}

// Health handles health check endpoint
func (h *TechniqueHandler) Health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "healthy",
		"service": "technique-selector",
	})
}

// Ready handles readiness check endpoint
func (h *TechniqueHandler) Ready(c *gin.Context) {
	// Check if engine is loaded
	if h.engine == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"status": "not ready",
			"reason": "engine not initialized",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status":  "ready",
		"service": "technique-selector",
	})
}