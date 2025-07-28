package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/betterprompts/api-gateway/internal/config"
	"github.com/betterprompts/api-gateway/internal/handlers"
	"github.com/betterprompts/api-gateway/internal/middleware"
	"github.com/betterprompts/api-gateway/internal/services"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/sirupsen/logrus"
)

func init() {
	// Load .env file
	if err := godotenv.Load(); err != nil {
		logrus.Info("No .env file found")
	}
}

func main() {
	// Initialize configuration
	cfg := config.Load()

	// Set up logging
	logger := setupLogging(cfg.LogLevel)

	// Initialize services
	serviceClients := initializeServices(cfg, logger)

	// Set up Gin
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()

	// Add middleware
	router.Use(gin.Recovery())
	router.Use(middleware.Logger(logger))
	router.Use(middleware.CORSConfig(logger))
	router.Use(middleware.RateLimiter(cfg.RateLimitRequestsPerMinute, cfg.RateLimitBurst))
	router.Use(middleware.RequestID())

	// Health checks
	router.GET("/health", handlers.HealthCheck)
	router.GET("/health/ready", handlers.ReadinessCheck(serviceClients))
	router.GET("/health/live", handlers.LivenessCheck)

	// Metrics endpoint
	router.GET("/metrics", gin.WrapH(promhttp.Handler()))

	// API v1 routes
	v1 := router.Group("/api/v1")
	{
		// Public routes
		v1.POST("/enhance", handlers.EnhancePrompt(serviceClients))
		v1.POST("/analyze", handlers.AnalyzeIntent(serviceClients))
		v1.GET("/techniques", handlers.GetTechniques())

		// Protected routes
		protected := v1.Group("/")
		protected.Use(middleware.AuthRequired(cfg.JWTSecret))
		{
			protected.GET("/history", handlers.GetHistory(serviceClients))
			protected.POST("/feedback", handlers.SubmitFeedback(serviceClients))
			protected.GET("/preferences", handlers.GetPreferences(serviceClients))
			protected.PUT("/preferences", handlers.UpdatePreferences(serviceClients))
		}

		// Auth routes
		auth := v1.Group("/auth")
		{
			auth.POST("/register", handlers.Register(serviceClients))
			auth.POST("/login", handlers.Login(serviceClients))
			auth.POST("/refresh", handlers.RefreshToken(serviceClients))
			auth.POST("/logout", middleware.AuthRequired(cfg.JWTSecret), handlers.Logout(serviceClients))
		}
	}

	// Root endpoint
	router.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"service": "BetterPrompts API Gateway",
			"version": "1.0.0",
			"status":  "operational",
			"docs":    "/docs",
			"health":  "/health",
		})
	})

	// Swagger docs (if enabled)
	if cfg.EnableDocs {
		router.GET("/docs", handlers.SwaggerDocs)
	}

	// Create HTTP server
	srv := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.Port),
		Handler:      router,
		ReadTimeout:  time.Duration(cfg.RequestTimeout) * time.Second,
		WriteTimeout: time.Duration(cfg.RequestTimeout) * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	// Start server in goroutine
	go func() {
		logger.Infof("Starting API Gateway on port %d", cfg.Port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("Shutting down server...")

	// Graceful shutdown with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		logger.Fatalf("Server forced to shutdown: %v", err)
	}

	logger.Info("Server exited")
}

func setupLogging(level string) *logrus.Logger {
	logger := logrus.New()
	logger.SetFormatter(&logrus.JSONFormatter{})
	logger.SetOutput(os.Stdout)

	logLevel, err := logrus.ParseLevel(level)
	if err != nil {
		logLevel = logrus.InfoLevel
	}
	logger.SetLevel(logLevel)

	return logger
}

func initializeServices(cfg *config.Config, logger *logrus.Logger) *services.ServiceClients {
	return services.NewServiceClients(
		cfg.IntentClassifierURL,
		cfg.TechniqueSelectorURL,
		cfg.PromptGeneratorURL,
		cfg.DatabaseURL,
		cfg.RedisURL,
		logger,
	)
}