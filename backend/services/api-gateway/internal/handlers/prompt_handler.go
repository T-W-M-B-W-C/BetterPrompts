package handlers

import (
	"database/sql"
	"net/http"

	"github.com/betterprompts/api-gateway/internal/models"
	"github.com/betterprompts/api-gateway/internal/services"
	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

// GetPromptByID retrieves a specific prompt by ID
func GetPromptByID(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Get user ID from context (set by auth middleware)
		userID, exists := c.Get("user_id")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}

		// Get prompt ID from URL parameter
		promptID := c.Param("id")
		if promptID == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "prompt ID required"})
			return
		}

		// Get the prompt from database
		prompt, err := clients.Database.GetPromptHistory(c.Request.Context(), promptID)
		if err != nil {
			if err.Error() == "prompt history not found" {
				c.JSON(http.StatusNotFound, gin.H{"error": "prompt not found"})
				return
			}
			c.MustGet("logger").(*logrus.Entry).WithError(err).Error("Failed to get prompt")
			c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to retrieve prompt"})
			return
		}

		// Verify the user owns this prompt
		if !prompt.UserID.Valid || prompt.UserID.String != userID.(string) {
			c.JSON(http.StatusForbidden, gin.H{"error": "access denied"})
			return
		}

		c.JSON(http.StatusOK, prompt)
	}
}

// RerunPrompt reruns a prompt with the same technique
func RerunPrompt(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		logger := c.MustGet("logger").(*logrus.Entry)

		// Get user ID from context (set by auth middleware)
		userID, exists := c.Get("user_id")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}

		// Get prompt ID from URL parameter
		promptID := c.Param("id")
		if promptID == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "prompt ID required"})
			return
		}

		// Get the original prompt from database
		originalPrompt, err := clients.Database.GetPromptHistory(c.Request.Context(), promptID)
		if err != nil {
			if err.Error() == "prompt history not found" {
				c.JSON(http.StatusNotFound, gin.H{"error": "prompt not found"})
				return
			}
			logger.WithError(err).Error("Failed to get prompt")
			c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to retrieve prompt"})
			return
		}

		// Verify the user owns this prompt
		if !originalPrompt.UserID.Valid || originalPrompt.UserID.String != userID.(string) {
			c.JSON(http.StatusForbidden, gin.H{"error": "access denied"})
			return
		}

		// Create a new enhancement request using the original data
		enhanceReq := models.EnhanceRequest{
			Text:              originalPrompt.OriginalInput,
			PreferTechniques:  originalPrompt.TechniquesUsed,
			ExcludeTechniques: []string{}, // Clear any exclusions
		}

		// If we have the complexity, set it
		if originalPrompt.Complexity.Valid {
			enhanceReq.Complexity = originalPrompt.Complexity.String
		}

		// Manually call the enhancement logic
		// First, get intent classification (or reuse if available)
		var intentResult *services.IntentClassificationResult
		if originalPrompt.Intent.Valid && originalPrompt.IntentConfidence.Valid {
			// Reuse the original intent classification
			intentResult = &services.IntentClassificationResult{
				Intent:              originalPrompt.Intent.String,
				Confidence:          originalPrompt.IntentConfidence.Float64,
				Complexity:          originalPrompt.Complexity.String,
				SuggestedTechniques: originalPrompt.TechniquesUsed,
			}
		} else {
			// Re-classify intent
			intentResult, err = clients.IntentClassifier.ClassifyIntent(c.Request.Context(), enhanceReq.Text)
			if err != nil {
				logger.WithError(err).Error("Intent classification failed")
				c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to analyze intent"})
				return
			}
		}

		// Create technique selection request
		techniqueRequest := models.TechniqueSelectionRequest{
			Text:              enhanceReq.Text,
			Intent:            intentResult.Intent,
			Complexity:        intentResult.Complexity,
			PreferTechniques:  originalPrompt.TechniquesUsed, // Use same techniques
			ExcludeTechniques: []string{},
			UserID:            userID,
		}

		// Select techniques (should return the same ones)
		techniques, err := clients.TechniqueSelector.SelectTechniques(c.Request.Context(), techniqueRequest)
		if err != nil {
			logger.WithError(err).Error("Technique selection failed")
			techniques = originalPrompt.TechniquesUsed // Fallback to original
		}

		// Generate enhanced prompt
		generationRequest := models.PromptGenerationRequest{
			Text:       enhanceReq.Text,
			Intent:     intentResult.Intent,
			Complexity: intentResult.Complexity,
			Techniques: techniques,
			Context: map[string]interface{}{
				"enhanced": true,
				"rerun":    true,
				"original_prompt_id": promptID,
			},
		}

		enhancedPrompt, err := clients.PromptGenerator.GeneratePrompt(c.Request.Context(), generationRequest)
		if err != nil {
			logger.WithError(err).Error("Prompt generation failed")
			c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to generate enhanced prompt"})
			return
		}

		// Save the new history entry
		sessionID := c.GetHeader("X-Session-ID")
		if sessionID == "" {
			sessionID = c.MustGet("request_id").(string)
		}

		historyEntry := models.PromptHistory{
			UserID:           sql.NullString{String: userID.(string), Valid: true},
			SessionID:        sql.NullString{String: sessionID, Valid: true},
			OriginalInput:    enhanceReq.Text,
			EnhancedOutput:   enhancedPrompt.Text,
			Intent:           sql.NullString{String: intentResult.Intent, Valid: true},
			Complexity:       sql.NullString{String: intentResult.Complexity, Valid: true},
			TechniquesUsed:   techniques,
			IntentConfidence: sql.NullFloat64{Float64: intentResult.Confidence, Valid: true},
			Metadata: map[string]interface{}{
				"model_version": enhancedPrompt.ModelVersion,
				"rerun_from":    promptID,
			},
		}

		historyID, err := clients.Database.SavePromptHistory(c.Request.Context(), historyEntry)
		if err != nil {
			logger.WithError(err).Warn("Failed to save prompt history")
			// Don't fail the request if history save fails
		}

		// Prepare response
		response := gin.H{
			"id":               historyID,
			"original_text":    enhanceReq.Text,
			"enhanced_text":    enhancedPrompt.Text,
			"enhanced_prompt":  enhancedPrompt.Text, // Alias for compatibility
			"intent":           intentResult.Intent,
			"complexity":       intentResult.Complexity,
			"techniques":       techniques,
			"techniques_used":  techniques,
			"confidence":       intentResult.Confidence,
			"enhanced":         true,
			"metadata": gin.H{
				"tokens_used":    enhancedPrompt.TokensUsed,
				"model_version":  enhancedPrompt.ModelVersion,
				"rerun_from":     promptID,
			},
		}

		logger.WithFields(logrus.Fields{
			"original_prompt_id": promptID,
			"new_history_id":     historyID,
			"techniques_used":    techniques,
		}).Info("Prompt rerun successful")

		c.JSON(http.StatusOK, response)
	}
}