package handlers

import (
	"context"

	"github.com/betterprompts/api-gateway/internal/models"
	"github.com/betterprompts/api-gateway/internal/services"
	"github.com/stretchr/testify/mock"
)

// MockDatabase is a mock implementation of the database interface
type MockDatabase struct {
	mock.Mock
}

// GetPromptHistory mocks the GetPromptHistory method
func (m *MockDatabase) GetPromptHistory(ctx context.Context, id string) (*models.PromptHistory, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.PromptHistory), args.Error(1)
}

// SavePromptHistory mocks the SavePromptHistory method
func (m *MockDatabase) SavePromptHistory(ctx context.Context, entry models.PromptHistory) (string, error) {
	args := m.Called(ctx, entry)
	return args.String(0), args.Error(1)
}

// GetUserPromptHistoryWithFilters mocks the GetUserPromptHistoryWithFilters method
func (m *MockDatabase) GetUserPromptHistoryWithFilters(ctx context.Context, userID string, req models.PaginationRequest) ([]*models.PromptHistory, int64, error) {
	args := m.Called(ctx, userID, req)
	if args.Get(0) == nil {
		return nil, args.Get(1).(int64), args.Error(2)
	}
	return args.Get(0).([]*models.PromptHistory), args.Get(1).(int64), args.Error(2)
}

// GetUserPromptHistory mocks the GetUserPromptHistory method
func (m *MockDatabase) GetUserPromptHistory(ctx context.Context, userID string, limit, offset int) ([]models.PromptHistory, error) {
	args := m.Called(ctx, userID, limit, offset)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]models.PromptHistory), args.Error(1)
}

// DeletePromptHistory mocks the DeletePromptHistory method
func (m *MockDatabase) DeletePromptHistory(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

// Ping mocks the Ping method
func (m *MockDatabase) Ping() error {
	args := m.Called()
	return args.Error(0)
}

// Ensure MockDatabase implements DatabaseInterface
var _ services.DatabaseInterface = (*MockDatabase)(nil)