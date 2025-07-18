package handlers

import (
	"net/http"

	"github.com/betterprompts/api-gateway/internal/services"
	"github.com/gin-gonic/gin"
)

// AnalyzeRequest represents the request body for intent analysis
type AnalyzeRequest struct {
	Text    string                 `json:"text" binding:"required,min=1,max=5000"`
	Context map[string]interface{} `json:"context,omitempty"`
}

// AnalyzeIntent handles intent analysis without enhancement
func AnalyzeIntent(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req AnalyzeRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "Invalid request body",
				"details": err.Error(),
			})
			return
		}

		// Classify intent
		result, err := clients.IntentClassifier.ClassifyIntent(c.Request.Context(), req.Text)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "Failed to analyze intent",
			})
			return
		}

		c.JSON(http.StatusOK, result)
	}
}