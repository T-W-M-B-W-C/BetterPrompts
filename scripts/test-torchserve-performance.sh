#!/bin/bash
# Quick performance test for TorchServe

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}TorchServe Performance Test${NC}"
echo "=============================="

# Check if TorchServe is running
if ! docker compose ps torchserve | grep -q "Up"; then
    echo -e "${RED}TorchServe is not running!${NC}"
    echo "Start it with: docker compose up -d torchserve"
    exit 1
fi

# Warm up request
echo -e "\n${YELLOW}Warming up...${NC}"
curl -s -X POST http://localhost:8080/predictions/intent_classifier \
    -H "Content-Type: application/json" \
    -d '{"text": "warmup"}' > /dev/null 2>&1

# Performance test
echo -e "\n${GREEN}Running performance test (10 requests)...${NC}"
TOTAL_TIME=0

for i in {1..10}; do
    START=$(date +%s.%N)
    RESPONSE=$(curl -s -X POST http://localhost:8080/predictions/intent_classifier \
        -H "Content-Type: application/json" \
        -d '{"text": "How do I implement authentication in Node.js?"}' 2>&1)
    END=$(date +%s.%N)
    
    TIME=$(echo "$END - $START" | bc)
    TOTAL_TIME=$(echo "$TOTAL_TIME + $TIME" | bc)
    
    if echo "$RESPONSE" | grep -q "intent"; then
        printf "Request %2d: %.3fs ✓\n" $i $TIME
    else
        printf "Request %2d: %.3fs ✗ (failed)\n" $i $TIME
    fi
done

# Calculate average
AVG_TIME=$(echo "scale=3; $TOTAL_TIME / 10" | bc)

echo -e "\n${GREEN}Results:${NC}"
echo "Average response time: ${AVG_TIME}s"

# Performance assessment
if (( $(echo "$AVG_TIME < 0.2" | bc -l) )); then
    echo -e "${GREEN}✓ Excellent performance (<200ms)${NC}"
elif (( $(echo "$AVG_TIME < 0.5" | bc -l) )); then
    echo -e "${YELLOW}⚡ Good performance (<500ms)${NC}"
elif (( $(echo "$AVG_TIME < 1.0" | bc -l) )); then
    echo -e "${YELLOW}⚠ Acceptable performance (<1s)${NC}"
else
    echo -e "${RED}✗ Poor performance (>1s)${NC}"
    echo "Consider running: ./scripts/switch-torchserve-env.sh dev"
fi

# Show current configuration
echo -e "\n${GREEN}Current Configuration:${NC}"
./scripts/switch-torchserve-env.sh status | grep -E "(Configuration:|batch_size|max_batch_delay|Workers)" | head -5