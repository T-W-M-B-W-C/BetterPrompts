#!/bin/bash
# Quick performance test

echo "Testing TorchServe performance..."

# Warm up
curl -s -X POST http://localhost:8080/predictions/intent_classifier \
    -H "Content-Type: application/json" \
    -d '{"text": "warmup"}' > /dev/null

# Test 5 requests
echo "Response times:"
for i in {1..5}; do
    START=$(date +%s.%N)
    curl -s -X POST http://localhost:8080/predictions/intent_classifier \
        -H "Content-Type: application/json" \
        -d '{"text": "How do I create a React component?"}' > /dev/null
    END=$(date +%s.%N)
    TIME=$(echo "$END - $START" | bc)
    echo "  Request $i: ${TIME}s"
done

# Check current config
echo -e "\nCurrent TorchServe config:"
docker compose exec torchserve grep -E "(batch_size|max_batch_delay|workers)" /home/model-server/config/config.properties | grep -v "^#" | head -5