package config

import (
	"os"
	"strconv"
	"strings"
)

// Config holds all configuration for the API Gateway
type Config struct {
	// Application
	Environment string
	Port        int
	LogLevel    string
	EnableDocs  bool

	// Service URLs
	IntentClassifierURL  string
	TechniqueSelectorURL string
	PromptGeneratorURL   string

	// Database
	DatabaseURL string

	// Redis
	RedisURL string

	// JWT
	JWTSecret           string
	JWTExpirationHours  int
	RefreshTokenExpDays int

	// CORS
	CORSAllowedOrigins []string
	CORSAllowedMethods []string
	CORSAllowedHeaders []string

	// Rate Limiting
	RateLimitRequestsPerMinute int
	RateLimitBurst             int

	// Timeouts
	RequestTimeout int // seconds
}

// Load loads configuration from environment variables
func Load() *Config {
	return &Config{
		// Application
		Environment: getEnv("NODE_ENV", "development"),
		Port:        getEnvAsInt("API_GATEWAY_PORT", 8000),
		LogLevel:    getEnv("LOG_LEVEL", "info"),
		EnableDocs:  getEnvAsBool("ENABLE_DOCS", true),

		// Service URLs
		IntentClassifierURL:  getEnv("INTENT_CLASSIFIER_URL", "http://localhost:8001"),
		TechniqueSelectorURL: getEnv("TECHNIQUE_SELECTOR_URL", "http://localhost:8002"),
		PromptGeneratorURL:   getEnv("PROMPT_GENERATOR_URL", "http://localhost:8003"),

		// Database
		DatabaseURL: buildDatabaseURL(),

		// Redis
		RedisURL: buildRedisURL(),

		// JWT
		JWTSecret:           getEnv("JWT_SECRET", "your-secret-key-change-this"),
		JWTExpirationHours:  getEnvAsInt("JWT_EXPIRATION_HOURS", 24),
		RefreshTokenExpDays: getEnvAsInt("REFRESH_TOKEN_EXPIRATION_DAYS", 7),

		// CORS
		CORSAllowedOrigins: getEnvAsSlice("CORS_ALLOWED_ORIGINS", []string{"http://localhost:3000"}),
		CORSAllowedMethods: getEnvAsSlice("CORS_ALLOWED_METHODS", []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}),
		CORSAllowedHeaders: getEnvAsSlice("CORS_ALLOWED_HEADERS", []string{"Content-Type", "Authorization"}),

		// Rate Limiting
		RateLimitRequestsPerMinute: getEnvAsInt("RATE_LIMIT_REQUESTS_PER_MINUTE", 60),
		RateLimitBurst:             getEnvAsInt("RATE_LIMIT_BURST", 10),

		// Timeouts
		RequestTimeout: getEnvAsInt("REQUEST_TIMEOUT", 30),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvAsInt(key string, defaultValue int) int {
	valueStr := getEnv(key, "")
	if value, err := strconv.Atoi(valueStr); err == nil {
		return value
	}
	return defaultValue
}

func getEnvAsBool(key string, defaultValue bool) bool {
	valueStr := getEnv(key, "")
	if value, err := strconv.ParseBool(valueStr); err == nil {
		return value
	}
	return defaultValue
}

func getEnvAsSlice(key string, defaultValue []string) []string {
	valueStr := getEnv(key, "")
	if valueStr != "" {
		return strings.Split(valueStr, ",")
	}
	return defaultValue
}

func buildDatabaseURL() string {
	host := getEnv("POSTGRES_HOST", "localhost")
	port := getEnv("POSTGRES_PORT", "5432")
	user := getEnv("POSTGRES_USER", "betterprompts")
	password := getEnv("POSTGRES_PASSWORD", "changeme")
	dbname := getEnv("POSTGRES_DB", "betterprompts")

	return "postgres://" + user + ":" + password + "@" + host + ":" + port + "/" + dbname
}

func buildRedisURL() string {
	host := getEnv("REDIS_HOST", "localhost")
	port := getEnv("REDIS_PORT", "6379")
	password := getEnv("REDIS_PASSWORD", "")

	if password != "" {
		return "redis://:" + password + "@" + host + ":" + port + "/0"
	}
	return "redis://" + host + ":" + port + "/0"
}