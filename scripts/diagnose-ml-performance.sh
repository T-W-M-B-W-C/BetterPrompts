#!/bin/bash
# Diagnose ML inference performance issues

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_test() { echo -e "${BLUE}[TEST]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Test 1: Check TorchServe responsiveness
log_test "Testing TorchServe ping latency..."
START=$(date +%s.%N)
curl -s http://localhost:8080/ping > /dev/null
END=$(date +%s.%N)
PING_TIME=$(echo "$END - $START" | bc)
echo "  Ping time: ${PING_TIME}s"
if (( $(echo "$PING_TIME > 1.0" | bc -l) )); then
    log_warn "Ping is slow (>1s), TorchServe might be overloaded"
fi

# Test 2: Check model status
log_test "Checking model worker status..."
MODEL_STATUS=$(curl -s http://localhost:8081/models/intent_classifier)
echo "$MODEL_STATUS" | jq '.' 2>/dev/null || echo "$MODEL_STATUS"

# Test 3: Direct inference timing
log_test "Testing direct TorchServe inference timing..."
for i in {1..5}; do
    START=$(date +%s.%N)
    RESPONSE=$(curl -s -X POST http://localhost:8080/predictions/intent_classifier \
        -H "Content-Type: application/json" \
        -d '{"text": "test"}' 2>&1)
    END=$(date +%s.%N)
    INFERENCE_TIME=$(echo "$END - $START" | bc)
    
    if echo "$RESPONSE" | grep -q "intent"; then
        echo "  Request $i: ${INFERENCE_TIME}s"
    else
        echo "  Request $i: FAILED - $RESPONSE"
    fi
done

# Test 4: Check TorchServe metrics
log_test "Checking TorchServe metrics..."
METRICS=$(curl -s http://localhost:8082/metrics 2>/dev/null | grep -E "(ts_inference_latency|ts_queue_latency|WorkerThread)" | head -10)
if [ -n "$METRICS" ]; then
    echo "$METRICS"
else
    log_warn "No metrics available"
fi

# Test 5: Check resource usage
log_test "Checking container resource usage..."
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep -E "(torchserve|intent-classifier)" || true

# Test 6: Check logs for errors
log_test "Checking TorchServe logs for errors..."
docker compose logs --tail=20 torchserve 2>&1 | grep -iE "(error|exception|failed|timeout)" | tail -5 || echo "  No recent errors found"

# Test 7: Check config file
log_test "Checking TorchServe configuration..."
CONFIG_PATH=$(docker compose exec torchserve cat /home/model-server/config/config.properties 2>/dev/null | grep -E "(batch_size|max_batch_delay|workers|model_store)" | head -5)
echo "$CONFIG_PATH"

# Test 8: Test with different payload sizes
log_test "Testing with different payload sizes..."
for size in "short text" "This is a medium length text that simulates a typical user query" "This is a much longer text that simulates a complex user query with multiple sentences and various requirements that need to be processed by the model to test how it handles larger inputs"; do
    LEN=${#size}
    START=$(date +%s.%N)
    curl -s -X POST http://localhost:8080/predictions/intent_classifier \
        -H "Content-Type: application/json" \
        -d "{\"text\": \"$size\"}" > /dev/null 2>&1
    END=$(date +%s.%N)
    TIME=$(echo "$END - $START" | bc)
    echo "  Text length $LEN chars: ${TIME}s"
done

# Recommendations
echo -e "\n${GREEN}Recommendations:${NC}"
echo "1. If inference is slow (>1s), consider:"
echo "   - Reducing batch_size to 1 in config"
echo "   - Reducing max_batch_delay to 10ms"
echo "   - Using the optimized config: cp infrastructure/model-serving/torchserve/config/config.properties.optimized infrastructure/model-serving/torchserve/config/config.properties"
echo "   - Restarting TorchServe: docker compose restart torchserve"
echo ""
echo "2. If model is not responding:"
echo "   - Check model is loaded: curl http://localhost:8081/models"
echo "   - Re-initialize: ./infrastructure/model-serving/scripts/init_local_model_v2.sh"
echo ""
echo "3. For faster development inference:"
echo "   - Reduce workers to 1: minWorkers=1, maxWorkers=1"
echo "   - Disable batching: batch_size=1"
echo "   - Use simpler handler without preprocessing"