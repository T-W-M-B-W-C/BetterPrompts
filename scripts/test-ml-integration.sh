#!/bin/bash
# Test ML integration between intent-classifier and TorchServe

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

# Test 1: Check TorchServe health
log_test "Testing TorchServe health endpoint..."
if curl -f -s http://localhost:8080/ping > /dev/null; then
    log_success "TorchServe is healthy"
else
    log_error "TorchServe is not responding"
    exit 1
fi

# Test 2: Check if model is loaded
log_test "Checking if intent_classifier model is loaded..."
MODEL_STATUS=$(curl -s http://localhost:8081/models/intent_classifier | jq -r '.[0].workers[0].status' 2>/dev/null || echo "NOT_FOUND")
if [ "$MODEL_STATUS" == "READY" ]; then
    log_success "Model is loaded and ready"
else
    log_error "Model status: $MODEL_STATUS (expected: READY)"
    log_info "You may need to run: ./infrastructure/model-serving/scripts/init_local_model.sh"
    exit 1
fi

# Test 3: Test direct TorchServe inference
log_test "Testing direct TorchServe inference..."
TORCHSERVE_RESPONSE=$(curl -s -X POST http://localhost:8080/predictions/intent_classifier \
    -H "Content-Type: application/json" \
    -d '{"text": "How do I create a React component?"}')

if echo "$TORCHSERVE_RESPONSE" | jq -e '.intent' > /dev/null 2>&1; then
    log_success "TorchServe inference successful"
    echo "  Intent: $(echo "$TORCHSERVE_RESPONSE" | jq -r '.intent')"
    echo "  Confidence: $(echo "$TORCHSERVE_RESPONSE" | jq -r '.confidence')"
else
    log_error "TorchServe inference failed"
    echo "Response: $TORCHSERVE_RESPONSE"
    exit 1
fi

# Test 4: Check intent-classifier service health
log_test "Testing intent-classifier service health..."
if curl -f -s http://localhost:8001/health > /dev/null; then
    log_success "Intent-classifier service is healthy"
else
    log_error "Intent-classifier service is not responding"
    exit 1
fi

# Test 5: Test full integration through API Gateway
log_test "Testing full ML integration through API Gateway..."
API_RESPONSE=$(curl -s -X POST http://localhost/api/v1/analyze \
    -H "Content-Type: application/json" \
    -d '{"text": "How do I implement authentication in a Node.js application?"}')

if echo "$API_RESPONSE" | jq -e '.intent' > /dev/null 2>&1; then
    log_success "Full ML integration successful!"
    echo -e "\n${GREEN}Analysis Results:${NC}"
    echo "  Intent: $(echo "$API_RESPONSE" | jq -r '.intent')"
    echo "  Confidence: $(echo "$API_RESPONSE" | jq -r '.confidence')"
    echo "  Complexity: $(echo "$API_RESPONSE" | jq -r '.complexity')"
    echo "  Suggested Techniques:"
    echo "$API_RESPONSE" | jq -r '.suggested_techniques[]' | sed 's/^/    - /'
else
    log_error "API Gateway integration failed"
    echo "Response: $API_RESPONSE"
    
    # Additional debugging
    log_info "Checking API Gateway logs..."
    docker compose logs --tail=20 api-gateway | grep -i error || true
    
    log_info "Checking intent-classifier logs..."
    docker compose logs --tail=20 intent-classifier | grep -i error || true
    
    exit 1
fi

# Test 6: Performance check
log_test "Testing response time..."
START_TIME=$(date +%s.%N)
curl -s -X POST http://localhost/api/v1/analyze \
    -H "Content-Type: application/json" \
    -d '{"text": "Quick test"}' > /dev/null
END_TIME=$(date +%s.%N)
RESPONSE_TIME=$(echo "$END_TIME - $START_TIME" | bc)

if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    log_success "Response time: ${RESPONSE_TIME}s (< 2s target)"
else
    log_error "Response time: ${RESPONSE_TIME}s (exceeds 2s target)"
fi

echo -e "\n${GREEN}All ML integration tests passed!${NC}"
echo -e "\nNext steps:"
echo "  1. The ML integration is working correctly"
echo "  2. You can now test the /enhance endpoint which uses this integration"
echo "  3. Monitor the services with: docker compose logs -f intent-classifier torchserve"