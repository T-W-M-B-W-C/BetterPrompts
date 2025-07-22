#!/bin/bash
# End-to-End Integration Test for Enhance Endpoint
# Tests the complete enhancement pipeline with development auth bypass

set -e

# Configuration
API_BASE_URL="http://localhost/api/v1"
DIRECT_API_URL="http://localhost:8090/api/v1"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test tracking
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
print_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=0
    
    echo "Waiting for $service to be ready..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "$service is ready!"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    echo "ERROR: $service failed to start after $max_attempts seconds"
    return 1
}

# Test function
run_test() {
    local test_name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="$5"
    local validation="$6"
    
    print_test "$test_name"
    
    # Make request with dev bypass
    response=$(curl -s -w "\n%{http_code}" -X "$method" \
        "$API_BASE_URL$endpoint" \
        -H "Content-Type: application/json" \
        -H "X-Test-Mode: true" \
        ${data:+-d "$data"})
    
    # Extract status code and body
    status=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    # Check status code
    if [ "$status" != "$expected_status" ]; then
        print_error "$test_name - Expected status $expected_status, got $status"
        echo "Response body: $body"
        return 1
    fi
    
    # Run custom validation if provided
    if [ -n "$validation" ]; then
        if ! echo "$body" | jq -e "$validation" > /dev/null 2>&1; then
            print_error "$test_name - Validation failed: $validation"
            echo "Response body: $body"
            return 1
        fi
    fi
    
    print_success "$test_name"
    return 0
}

# Main test execution
echo "============================================"
echo "Enhance Endpoint Integration Test Suite"
echo "============================================"
echo ""

# 1. Wait for all services
echo "Checking service health..."
wait_for_service "API Gateway" "$API_BASE_URL/health" || exit 1
wait_for_service "Intent Classifier" "http://localhost:8001/health" || exit 1
wait_for_service "Technique Selector" "http://localhost:8002/health" || exit 1
wait_for_service "Prompt Generator" "http://localhost:8003/health" || exit 1
echo ""

# 2. Test health endpoints
run_test "API Gateway Health Check" "GET" "/health" "" "200" '.status == "healthy"'

# 3. Test enhance endpoint with various prompts
echo ""
echo "Testing Enhancement Pipeline..."
echo ""

# Test 1: Simple prompt with Chain of Thought
run_test "Enhance simple prompt with CoT" "POST" "/enhance" \
    '{"text": "How do I create a binary search tree in Python?", "prefer_techniques": ["chain_of_thought"]}' \
    "200" '.enhanced_prompt | length > 0'

# Test 2: Complex prompt with multiple techniques
run_test "Enhance complex prompt" "POST" "/enhance" \
    '{"text": "Design a distributed caching system that handles millions of requests per second with fault tolerance", "prefer_techniques": ["tree_of_thoughts", "structured_output"]}' \
    "200" '.enhanced_prompt | length > 0'

# Test 3: Educational prompt
run_test "Enhance educational prompt" "POST" "/enhance" \
    '{"text": "Explain recursion to a beginner", "prefer_techniques": ["few_shot", "analogical"]}' \
    "200" '.enhanced_prompt | length > 0'

# Test 4: Debugging prompt
run_test "Enhance debugging prompt" "POST" "/enhance" \
    '{"text": "My React component renders infinitely. How do I debug this?", "prefer_techniques": ["step_by_step"]}' \
    "200" '.enhanced_prompt | length > 0'

# Test 5: Creative prompt
run_test "Enhance creative prompt" "POST" "/enhance" \
    '{"text": "Write a story about AI helping humanity", "prefer_techniques": ["role_play", "emotional_appeal"]}' \
    "200" '.enhanced_prompt | length > 0'

# 4. Test intent classification separately
echo ""
echo "Testing Intent Classification..."
echo ""

run_test "Analyze programming intent" "POST" "/analyze" \
    '{"text": "How to implement quicksort algorithm"}' \
    "200" '.intent != null and .complexity != null'

run_test "Analyze creative intent" "POST" "/analyze" \
    '{"text": "Write a poem about the sunset"}' \
    "200" '.intent != null and .complexity != null'

# 5. Test error handling
echo ""
echo "Testing Error Handling..."
echo ""

run_test "Empty text error" "POST" "/enhance" \
    '{"text": ""}' \
    "400" '.error != null'

run_test "Invalid technique error" "POST" "/enhance" \
    '{"text": "Test prompt", "prefer_techniques": ["invalid_technique"]}' \
    "200" '.enhanced_prompt != null'  # Should still work, just ignore invalid technique

# 6. Test response structure
echo ""
echo "Testing Response Structure..."
echo ""

# Full response validation
response=$(curl -s -X POST "$API_BASE_URL/enhance" \
    -H "Content-Type: application/json" \
    -H "X-Test-Mode: true" \
    -d '{"text": "Explain how neural networks work"}')

print_test "Validate enhance response structure"
if echo "$response" | jq -e '.enhanced_prompt and .intent and .complexity and .techniques and .original_text' > /dev/null 2>&1; then
    print_success "Response has all required fields"
else
    print_error "Response missing required fields"
    echo "Response: $response"
fi

# 7. Performance test
echo ""
echo "Testing Performance..."
echo ""

print_test "Enhancement response time"
start_time=$(date +%s%N)
curl -s -X POST "$API_BASE_URL/enhance" \
    -H "Content-Type: application/json" \
    -H "X-Test-Mode: true" \
    -d '{"text": "Quick performance test"}' > /dev/null
end_time=$(date +%s%N)
duration=$(((end_time - start_time) / 1000000))

if [ $duration -lt 3000 ]; then
    print_success "Response time: ${duration}ms (< 3s)"
else
    print_error "Response time: ${duration}ms (> 3s threshold)"
fi

# 8. Test technique selection
echo ""
echo "Testing Technique Selection..."
echo ""

# Test that preferred techniques are respected
response=$(curl -s -X POST "$API_BASE_URL/enhance" \
    -H "Content-Type: application/json" \
    -H "X-Test-Mode: true" \
    -d '{"text": "Test prompt", "prefer_techniques": ["chain_of_thought", "few_shot"]}')

print_test "Preferred techniques are used"
techniques=$(echo "$response" | jq -r '.techniques[]' 2>/dev/null | tr '\n' ' ')
if [[ "$techniques" == *"chain_of_thought"* ]]; then
    print_success "Chain of thought technique was applied"
else
    print_error "Preferred technique not applied"
fi

# Summary
echo ""
echo "============================================"
echo "Test Summary"
echo "============================================"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    
    # Show service logs for debugging
    echo ""
    echo "Recent API Gateway logs:"
    docker compose logs --tail=20 api-gateway | grep -E "error|Error|ERROR" || echo "No errors in logs"
    
    exit 1
fi