package main

import (
	"fmt"
	"os"

	"github.com/betterprompts/technique-selector/internal/handlers"
	"github.com/betterprompts/technique-selector/internal/models"
	"github.com/betterprompts/technique-selector/internal/rules"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"github.com/sirupsen/logrus"
	"gopkg.in/yaml.v3"
)

func main() {
	// Load environment variables
	if err := godotenv.Load(); err != nil {
		logrus.Warn("No .env file found")
	}

	// Initialize logger
	logger := logrus.New()
	logger.SetFormatter(&logrus.JSONFormatter{})
	
	logLevel := os.Getenv("LOG_LEVEL")
	if logLevel == "" {
		logLevel = "info"
	}
	level, err := logrus.ParseLevel(logLevel)
	if err != nil {
		logger.WithError(err).Warn("Invalid log level, defaulting to info")
		level = logrus.InfoLevel
	}
	logger.SetLevel(level)

	// Load rules configuration
	configPath := os.Getenv("RULES_CONFIG_PATH")
	if configPath == "" {
		configPath = "configs/rules.yaml"
	}

	config, err := loadConfig(configPath)
	if err != nil {
		logger.WithError(err).Fatal("Failed to load rules configuration")
	}

	logger.WithFields(logrus.Fields{
		"techniques_count": len(config.Techniques),
		"max_techniques":   config.SelectionRules.MaxTechniques,
	}).Info("Loaded rules configuration")

	// Initialize rules engine
	engine := rules.NewEngine(config, logger)

	// Initialize handlers
	handler := handlers.NewTechniqueHandler(engine, logger)

	// Setup Gin router
	if os.Getenv("GIN_MODE") == "release" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()
	router.Use(gin.Recovery())
	router.Use(loggerMiddleware(logger))

	// Routes
	router.GET("/health", handler.Health)
	router.GET("/ready", handler.Ready)
	
	// API v1 routes
	v1 := router.Group("/api/v1")
	{
		v1.POST("/select", handler.SelectTechniques)
		v1.GET("/techniques", handler.ListTechniques)
		v1.GET("/techniques/:id", handler.GetTechniqueByID)
	}

	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "8002"
	}

	logger.WithField("port", port).Info("Starting technique selector service")
	if err := router.Run(":" + port); err != nil {
		logger.WithError(err).Fatal("Failed to start server")
	}
}

// loadConfig loads the rules configuration from a YAML file
func loadConfig(path string) (*models.RulesConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	var config models.RulesConfig
	if err := yaml.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse config file: %w", err)
	}

	return &config, nil
}

// loggerMiddleware creates a Gin middleware for logging
func loggerMiddleware(logger *logrus.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Before request
		entry := logger.WithFields(logrus.Fields{
			"method": c.Request.Method,
			"path":   c.Request.URL.Path,
			"ip":     c.ClientIP(),
		})

		// Process request
		c.Next()

		// After request
		status := c.Writer.Status()
		entry = entry.WithFields(logrus.Fields{
			"status": status,
			"size":   c.Writer.Size(),
		})

		if status >= 400 {
			entry.Warn("Request completed with error")
		} else {
			entry.Info("Request completed")
		}
	}
}