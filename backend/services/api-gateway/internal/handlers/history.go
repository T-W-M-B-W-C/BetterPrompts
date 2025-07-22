package handlers

import (
	"github.com/sirupsen/logrus"
	"net/http"
	"strconv"

	"github.com/betterprompts/api-gateway/internal/services"
	"github.com/gin-gonic/gin"
)

// GetPromptHistory retrieves the user's prompt history
func GetPromptHistory(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Get user ID from context (set by auth middleware)
		userID, exists := c.Get("user_id")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}

		// Parse query parameters
		page := c.DefaultQuery("page", "1")
		limit := c.DefaultQuery("limit", "20")

		pageNum, err := strconv.Atoi(page)
		if err != nil || pageNum < 1 {
			pageNum = 1
		}

		limitNum, err := strconv.Atoi(limit)
		if err != nil || limitNum < 1 || limitNum > 100 {
			limitNum = 20
		}

		// Calculate offset
		offset := (pageNum - 1) * limitNum

		// Get history from database
		history, err := clients.Database.GetUserPromptHistory(c.Request.Context(), userID.(string), limitNum, offset)
		if err != nil {
			c.MustGet("logger").(*logrus.Entry).WithError(err).Error("Failed to get prompt history")
			c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to retrieve history"})
			return
		}

		// Return the history items
		c.JSON(http.StatusOK, history)
	}
}

// GetPromptHistoryItem retrieves a specific prompt history item
func GetPromptHistoryItem(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Get user ID from context
		userID, exists := c.Get("user_id")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}

		// Get history ID from URL parameter
		historyID := c.Param("id")
		if historyID == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "history ID required"})
			return
		}

		// Get the history item
		item, err := clients.Database.GetPromptHistory(c.Request.Context(), historyID)
		if err != nil {
			if err.Error() == "prompt history not found" {
				c.JSON(http.StatusNotFound, gin.H{"error": "history item not found"})
				return
			}
			c.MustGet("logger").(*logrus.Entry).WithError(err).Error("Failed to get prompt history item")
			c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to retrieve history item"})
			return
		}

		// Verify the user owns this history item
		if !item.UserID.Valid || item.UserID.String != userID.(string) {
			c.JSON(http.StatusForbidden, gin.H{"error": "access denied"})
			return
		}

		c.JSON(http.StatusOK, item)
	}
}

// DeletePromptHistoryItem deletes a specific prompt history item
func DeletePromptHistoryItem(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Get user ID from context
		userID, exists := c.Get("user_id")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}

		// Get history ID from URL parameter
		historyID := c.Param("id")
		if historyID == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "history ID required"})
			return
		}

		// First, get the item to verify ownership
		item, err := clients.Database.GetPromptHistory(c.Request.Context(), historyID)
		if err != nil {
			if err.Error() == "prompt history not found" {
				c.JSON(http.StatusNotFound, gin.H{"error": "history item not found"})
				return
			}
			c.MustGet("logger").(*logrus.Entry).WithError(err).Error("Failed to get prompt history item")
			c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to retrieve history item"})
			return
		}

		// Verify the user owns this history item
		if !item.UserID.Valid || item.UserID.String != userID.(string) {
			c.JSON(http.StatusForbidden, gin.H{"error": "access denied"})
			return
		}

		// Delete the item
		query := "DELETE FROM prompts.history WHERE id = $1"
		_, err = clients.Database.DB.ExecContext(c.Request.Context(), query, historyID)
		if err != nil {
			c.MustGet("logger").(*logrus.Entry).WithError(err).Error("Failed to delete prompt history item")
			c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to delete history item"})
			return
		}

		c.JSON(http.StatusOK, gin.H{"message": "history item deleted successfully"})
	}
}