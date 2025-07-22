#!/bin/bash
# Initialize mock model for local development with Docker Compose

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in correct directory
if [ ! -f "docker-compose.yml" ]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

log_info "Initializing TorchServe model for local development..."

# Create necessary directories
log_info "Creating model store directory..."
mkdir -p infrastructure/model-serving/torchserve/model-store

# Check if TorchServe container is running
if ! docker compose ps torchserve | grep -q "Up"; then
    log_warn "TorchServe container is not running. Starting it..."
    docker compose up -d torchserve
    log_info "Waiting for TorchServe to be ready..."
    sleep 10
fi

# Copy the create_mock_model.py script into the container
log_info "Copying model creation script to container..."
docker cp infrastructure/model-serving/scripts/create_mock_model.py betterprompts-torchserve:/tmp/

# Create mock model using the Python script
log_info "Creating mock model files..."
docker compose exec torchserve bash -c "cd /tmp && python /tmp/create_mock_model.py"

# Check if custom handler exists, otherwise use the mock handler
log_info "Checking for handler..."
if docker compose exec torchserve test -f /home/model-server/handlers/intent_classifier_handler.py; then
    HANDLER_PATH="/home/model-server/handlers/intent_classifier_handler.py"
    log_info "Using custom handler"
else
    HANDLER_PATH="/tmp/mock_model/handler.py"
    log_info "Using mock handler"
fi

# Create model archive inside the container
log_info "Creating model archive..."
docker compose exec torchserve bash -c "
    cd /tmp && \
    torch-model-archiver \
        --model-name intent_classifier \
        --version 1.0 \
        --handler $HANDLER_PATH \
        --extra-files mock_model/config.json \
        --serialized-file mock_model/model.pth \
        --export-path /home/model-server/model-store \
        --force
"

# Register the model
log_info "Registering model with TorchServe..."
docker compose exec torchserve bash -c "
    curl -X POST 'http://localhost:8081/models?url=intent_classifier.mar&initial_workers=2&synchronous=true'
"

# Verify model is loaded
log_info "Verifying model status..."
sleep 5
MODEL_STATUS=$(docker compose exec torchserve curl -s http://localhost:8081/models/intent_classifier)
echo "Model status: $MODEL_STATUS"

# Test inference
log_info "Testing model inference..."
TEST_RESPONSE=$(docker compose exec torchserve curl -s -X POST http://localhost:8080/predictions/intent_classifier \
    -H "Content-Type: application/json" \
    -d '{"text": "How do I create a React component?"}')

if echo "$TEST_RESPONSE" | grep -q "intent"; then
    log_info "Model inference test successful!"
    echo "Response: $TEST_RESPONSE"
else
    log_error "Model inference test failed"
    echo "Response: $TEST_RESPONSE"
    exit 1
fi

# Update docker-compose.yml environment variable if needed
log_info "Verifying intent-classifier service configuration..."
if ! grep -q "USE_TORCHSERVE=true" docker-compose.yml; then
    log_error "USE_TORCHSERVE is not set to true in docker-compose.yml"
    log_warn "Please ensure USE_TORCHSERVE=true is set for the intent-classifier service"
fi

log_info "TorchServe model initialization complete!"
log_info ""
log_info "You can now test the full integration:"
log_info "  1. Restart the intent-classifier service: docker compose restart intent-classifier"
log_info "  2. Test the /analyze endpoint: curl -X POST http://localhost/api/v1/analyze -H 'Content-Type: application/json' -d '{\"text\": \"How do I learn Python?\"}'\"