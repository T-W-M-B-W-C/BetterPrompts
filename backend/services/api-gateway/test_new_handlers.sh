#!/bin/bash

# Test script for new handler tests

echo "Running Phase 4 Handler Tests..."

# Create a temporary directory for testing
TEMP_DIR=$(mktemp -d)
TEST_PKG="github.com/betterprompts/api-gateway/internal/handlers"

# Copy the new test files to temp directory
cp internal/handlers/prompt_handler_new_test.go "$TEMP_DIR/"
cp internal/handlers/history_handler_new_test.go "$TEMP_DIR/"
cp internal/handlers/prompt_history_integration_new_test.go "$TEMP_DIR/"

# Copy required source files
cp -r internal "$TEMP_DIR/"

# Change to temp directory
cd "$TEMP_DIR"

# Create a go.mod file
cat > go.mod <<EOF
module github.com/betterprompts/api-gateway

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/sirupsen/logrus v1.9.3
    github.com/stretchr/testify v1.8.4
    github.com/golang-jwt/jwt/v5 v5.0.0
    github.com/lib/pq v1.10.9
    github.com/go-redis/redis/v8 v8.11.5
    github.com/google/uuid v1.3.0
)
EOF

# Run the tests
echo "Running unit tests..."
go test -run "TestGetPromptHistory|TestGetPromptByID|TestRerunPrompt" prompt_handler_new_test.go history_handler_new_test.go -v

echo "Running integration tests..."
go test -tags=integration -run "TestPromptHistoryEndpointsIntegration" prompt_history_integration_new_test.go -v

# Cleanup
cd -
rm -rf "$TEMP_DIR"

echo "Tests completed!"