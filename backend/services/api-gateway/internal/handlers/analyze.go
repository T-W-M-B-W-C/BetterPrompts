package handlers

import (
	"net/http"

	"github.com/betterprompts/api-gateway/internal/services"
	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

// AnalyzeRequest represents the request body for intent analysis
type AnalyzeRequest struct {
	Text    string                 `json:"text" binding:"required,min=1,max=5000"`
	Context map[string]interface{} `json:"context,omitempty"`
}

// AnalyzeIntent handles intent analysis without enhancement
func AnalyzeIntent(clients *services.ServiceClients) gin.HandlerFunc {
	logger := logrus.New()
	logger.SetFormatter(&logrus.JSONFormatter{})
	
	return func(c *gin.Context) {
		logger.Info("Analyze endpoint called")
		
		var req AnalyzeRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			logger.WithError(err).Error("Failed to bind JSON")
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "Invalid request body",
				"details": err.Error(),
			})
			return
		}

		logger.WithField("text", req.Text).Info("Classifying intent")
		
		// Classify intent
		result, err := clients.IntentClassifier.ClassifyIntent(c.Request.Context(), req.Text)
		if err != nil {
			// Log the error for debugging
			logger.WithError(err).Error("Failed to classify intent")
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "Failed to analyze intent",
				"details": err.Error(), // Include error details for debugging
			})
			return
		}

		logger.Info("Successfully classified intent")
		c.JSON(http.StatusOK, result)
	}
}