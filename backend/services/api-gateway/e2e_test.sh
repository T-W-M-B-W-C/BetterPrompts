#!/bin/bash

echo "Starting E2E Enhancement Test..."
echo "================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test an endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local data=$3
    local expected_status=${4:-200}
    
    echo -e "\n${YELLOW}Testing: $name${NC}"
    echo "URL: $url"
    echo "Request: $data"
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$data")
    
    body=$(echo "$response" | head -n -1)
    status=$(echo "$response" | tail -n 1)
    
    if [ "$status" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ Status: $status (expected: $expected_status)${NC}"
        echo "Response: $body" | jq . 2>/dev/null || echo "$body"
    else
        echo -e "${RED}✗ Status: $status (expected: $expected_status)${NC}"
        echo "Response: $body"
    fi
    
    return $([ "$status" -eq "$expected_status" ] && echo 0 || echo 1)
}

# Test 1: Check if services are healthy
echo -e "\n${YELLOW}=== Service Health Checks ===${NC}"

echo -e "\n${YELLOW}API Gateway Health${NC}"
curl -s http://localhost/health | jq .

echo -e "\n${YELLOW}Intent Classifier Health${NC}"
curl -s http://localhost:8001/health | jq . || echo "Intent classifier not accessible on :8001"

echo -e "\n${YELLOW}Technique Selector Health${NC}"
curl -s http://localhost:8002/health | jq . || echo "Technique selector not accessible on :8002"

echo -e "\n${YELLOW}Prompt Generator Health${NC}"
curl -s http://localhost:8003/health | jq . || echo "Prompt generator not accessible on :8003"

# Test 2: Direct service tests
echo -e "\n${YELLOW}=== Direct Service Tests ===${NC}"

# Test intent classifier directly
test_endpoint "Intent Classifier Direct" \
    "http://localhost:8001/api/v1/intents/classify" \
    '{"text": "How do I write a good React component?"}'

# Test technique selector directly
test_endpoint "Technique Selector Direct" \
    "http://localhost:8002/api/v1/select" \
    '{"text": "How do I write a good React component?", "intent": "question_answering", "complexity": "simple"}'

# Test 3: Full enhancement flow through API Gateway
echo -e "\n${YELLOW}=== API Gateway Enhancement Tests ===${NC}"

# Simple enhancement
test_endpoint "Simple Enhancement" \
    "http://localhost/api/v1/enhance" \
    '{"text": "How do I write a good React component?"}'

# Enhancement with preferences
test_endpoint "Enhancement with Preferences" \
    "http://localhost/api/v1/enhance" \
    '{
        "text": "Explain quantum computing",
        "context": {"audience": "beginners"},
        "prefer_techniques": ["few_shot", "chain_of_thought"]
    }'

# Complex enhancement
test_endpoint "Complex Enhancement" \
    "http://localhost/api/v1/enhance" \
    '{
        "text": "Design a scalable microservices architecture for an e-commerce platform that handles millions of users",
        "target_complexity": "complex"
    }'

# Test 4: Check logs for errors
echo -e "\n${YELLOW}=== Recent Error Logs ===${NC}"
echo "Checking API Gateway logs for errors..."
docker compose logs api-gateway --tail=20 | grep -E "(ERROR|error|Error)" || echo "No recent errors in API Gateway"

echo -e "\n${YELLOW}=== Test Complete ===${NC}"