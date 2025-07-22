#!/bin/bash
# Initialize mock model for local development with Docker Compose - Version 2

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

log_info "Initializing TorchServe model for local development (v2)..."

# Create necessary directories
log_info "Creating directories..."
mkdir -p infrastructure/model-serving/torchserve/model-store

# Check if TorchServe container is running
if ! docker compose ps torchserve | grep -q "Up"; then
    log_warn "TorchServe container is not running. Starting it..."
    docker compose up -d torchserve
    log_info "Waiting for TorchServe to be ready..."
    sleep 15
fi

# Create a simple mock model directly in the container
log_info "Creating mock model directly in container..."
docker compose exec torchserve bash -c 'cat > /tmp/create_simple_model.py << "EOF"
import torch
import json

# Create a simple model state dict
model_state = {
    "fc.weight": torch.randn(10, 768),
    "fc.bias": torch.randn(10)
}

# Save the model
torch.save(model_state, "/tmp/model.pth")

# Create config
config = {
    "model_type": "intent_classifier",
    "num_classes": 10,
    "labels": [
        "question_answering", "creative_writing", "code_generation",
        "data_analysis", "reasoning", "summarization", "translation",
        "conversation", "task_planning", "problem_solving"
    ]
}

with open("/tmp/config.json", "w") as f:
    json.dump(config, f, indent=2)

print("Mock model files created successfully")
EOF'

# Run the model creation script
docker compose exec torchserve python /tmp/create_simple_model.py

# Create a simple base handler
log_info "Creating base handler..."
docker compose exec torchserve bash -c 'cat > /tmp/base_handler.py << "EOF"
import torch
import json
from ts.torch_handler.base_handler import BaseHandler

class IntentClassifierHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        self.labels = [
            "question_answering", "creative_writing", "code_generation",
            "data_analysis", "reasoning", "summarization", "translation",
            "conversation", "task_planning", "problem_solving"
        ]
    
    def preprocess(self, data):
        """Extract text from request."""
        processed = []
        for row in data:
            text = row.get("data") or row.get("text") or row.get("body", {}).get("text", "")
            if isinstance(text, bytes):
                text = text.decode("utf-8")
            processed.append(text)
        return processed
    
    def inference(self, data):
        """Mock inference - return random predictions."""
        results = []
        for text in data:
            # Generate random scores
            scores = torch.rand(len(self.labels))
            probs = torch.softmax(scores, dim=0)
            
            # Get top prediction
            max_idx = torch.argmax(probs).item()
            
            results.append({
                "scores": scores.tolist(),
                "probabilities": probs.tolist(),
                "predicted_idx": max_idx
            })
        return results
    
    def postprocess(self, data):
        """Format the output."""
        output = []
        for i, result in enumerate(data):
            probs = result["probabilities"]
            idx = result["predicted_idx"]
            
            # Build response
            response = {
                "intent": self.labels[idx],
                "confidence": float(probs[idx]),
                "complexity": {
                    "level": "moderate",
                    "score": 0.5
                },
                "techniques": [
                    {
                        "name": "chain_of_thought",
                        "confidence": 0.8,
                        "description": "Step-by-step reasoning"
                    }
                ],
                "all_intents": {
                    self.labels[j]: float(probs[j]) 
                    for j in range(len(self.labels))
                }
            }
            output.append(response)
        
        return output

_service = IntentClassifierHandler()

def handle(data, context):
    """Entry point for TorchServe."""
    try:
        if not data:
            data = [{}]
        
        # Call the handler pipeline
        _service.context = context
        input_data = _service.preprocess(data)
        output = _service.inference(input_data)
        return _service.postprocess(output)
    except Exception as e:
        return [{"error": str(e)}]
EOF'

# Create model archive
log_info "Creating model archive..."
docker compose exec torchserve bash -c "
    cd /tmp && \
    torch-model-archiver \
        --model-name intent_classifier \
        --version 1.0 \
        --handler base_handler.py \
        --extra-files config.json \
        --serialized-file model.pth \
        --export-path /home/model-server/model-store \
        --force
"

# Check if model already exists and unregister if needed
log_info "Checking existing models..."
if docker compose exec torchserve curl -s http://localhost:8081/models/intent_classifier &>/dev/null; then
    log_info "Unregistering existing model..."
    docker compose exec torchserve curl -X DELETE http://localhost:8081/models/intent_classifier/1.0
    sleep 2
fi

# Register the model
log_info "Registering model with TorchServe..."
docker compose exec torchserve curl -X POST \
    "http://localhost:8081/models?url=intent_classifier.mar&initial_workers=2&synchronous=true"

# Wait for model to be ready
log_info "Waiting for model to be ready..."
sleep 5

# Verify model is loaded
log_info "Verifying model status..."
MODEL_STATUS=$(docker compose exec torchserve curl -s http://localhost:8081/models/intent_classifier)
echo "Model status: $MODEL_STATUS"

# Test inference
log_info "Testing model inference..."
TEST_RESPONSE=$(docker compose exec torchserve curl -s -X POST http://localhost:8080/predictions/intent_classifier \
    -H "Content-Type: application/json" \
    -d '{"text": "How do I create a React component?"}')

if echo "$TEST_RESPONSE" | grep -q "intent"; then
    log_info "Model inference test successful!"
    echo "Response: $TEST_RESPONSE" | jq '.' 2>/dev/null || echo "$TEST_RESPONSE"
else
    log_error "Model inference test failed"
    echo "Response: $TEST_RESPONSE"
    exit 1
fi

log_info "TorchServe model initialization complete!"
log_info ""
log_info "Next steps:"
log_info "  1. Restart intent-classifier: docker compose restart intent-classifier"
log_info "  2. Test the integration: ./scripts/test-ml-integration.sh"