package services

import (
	"context"
	"github.com/betterprompts/api-gateway/internal/models"
)

// DatabaseInterface defines the interface for database operations
type DatabaseInterface interface {
	GetPromptHistory(ctx context.Context, id string) (*models.PromptHistory, error)
	SavePromptHistory(ctx context.Context, entry models.PromptHistory) (string, error)
	GetUserPromptHistoryWithFilters(ctx context.Context, userID string, req models.PaginationRequest) ([]*models.PromptHistory, int64, error)
	GetUserPromptHistory(ctx context.Context, userID string, limit, offset int) ([]models.PromptHistory, error)
	DeletePromptHistory(ctx context.Context, id string) error
	Ping() error
}

// Ensure DatabaseService implements DatabaseInterface
var _ DatabaseInterface = (*DatabaseService)(nil)

// IntentClassifierInterface defines the interface for intent classification operations
type IntentClassifierInterface interface {
	ClassifyIntent(ctx context.Context, text string) (*IntentClassificationResult, error)
}

// TechniqueSelectorInterface defines the interface for technique selection operations
type TechniqueSelectorInterface interface {
	SelectTechniques(ctx context.Context, req models.TechniqueSelectionRequest) ([]string, error)
}

// PromptGeneratorInterface defines the interface for prompt generation operations
type PromptGeneratorInterface interface {
	GeneratePrompt(ctx context.Context, req models.PromptGenerationRequest) (*models.PromptGenerationResponse, error)
}