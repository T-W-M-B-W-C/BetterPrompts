package handlers

import (
	"net/http"

	"github.com/betterprompts/api-gateway/internal/services"
	"github.com/gin-gonic/gin"
)

// HealthCheck returns basic health status
func HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "healthy",
		"service": "api-gateway",
	})
}

// ReadinessCheck checks if all dependencies are ready
func ReadinessCheck(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Check database connection
		if err := clients.Database.Ping(); err != nil {
			c.JSON(http.StatusServiceUnavailable, gin.H{
				"status": "not ready",
				"error":  "database connection failed",
			})
			return
		}

		// Check Redis connection
		if err := clients.Cache.Ping(c.Request.Context()); err != nil {
			c.JSON(http.StatusServiceUnavailable, gin.H{
				"status": "not ready",
				"error":  "cache connection failed",
			})
			return
		}

		// Check service health
		services := map[string]string{
			"intent_classifier":  clients.IntentClassifierURL + "/health",
			"technique_selector": clients.TechniqueSelectorURL + "/health",
			"prompt_generator":   clients.PromptGeneratorURL + "/health",
		}

		for name, url := range services {
			if err := checkServiceHealth(url); err != nil {
				c.JSON(http.StatusServiceUnavailable, gin.H{
					"status": "not ready",
					"error":  name + " is not healthy",
				})
				return
			}
		}

		c.JSON(http.StatusOK, gin.H{
			"status": "ready",
			"service": "api-gateway",
		})
	}
}

// LivenessCheck returns liveness status
func LivenessCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "alive",
		"service": "api-gateway",
	})
}

func checkServiceHealth(url string) error {
	resp, err := http.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return err
	}
	return nil
}