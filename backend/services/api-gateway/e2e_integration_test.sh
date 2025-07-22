#!/bin/bash

# E2E Integration Test Suite with Monitoring
# Wave-mode orchestrated testing for comprehensive validation

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
API_GATEWAY_URL="http://localhost/api/v1"
DIRECT_GATEWAY_URL="http://localhost:8000/api/v1"
INTENT_CLASSIFIER_URL="http://localhost:8001"
TECHNIQUE_SELECTOR_URL="http://localhost:8002"
PROMPT_GENERATOR_URL="http://localhost:8003"

# Monitoring setup
MONITOR_DIR="./test-results/monitoring"
mkdir -p "$MONITOR_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Performance tracking (using regular arrays for compatibility)
RESPONSE_TIMES=()
ERROR_COUNTS=()
TEST_NAMES=()
ERROR_TEST_NAMES=()

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}E2E Integration Test Suite - Enhancement Flow${NC}"
echo -e "${BLUE}Wave-Mode Orchestration Enabled${NC}"
echo -e "${BLUE}================================================${NC}"

# Function to log test results
log_test() {
    local test_name=$1
    local status=$2
    local response_time=$3
    local details=$4
    
    echo "{\"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)\", \"test\": \"$test_name\", \"status\": \"$status\", \"response_time_ms\": $response_time, \"details\": \"$details\"}" >> "$MONITOR_DIR/test_log_$TIMESTAMP.jsonl"
}

# Function to test endpoint with monitoring
test_endpoint() {
    local name=$1
    local url=$2
    local data=$3
    local expected_status=${4:-200}
    local timeout=${5:-10}
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "\n${YELLOW}[Wave 1 - Service Discovery] Testing: $name${NC}"
    echo "URL: $url"
    echo "Request: $data"
    
    # Measure response time
    local start_time=$(date +%s%N)
    
    # Execute request with detailed output
    local temp_file=$(mktemp)
    local http_code=$(curl -s -w "%{http_code}" -o "$temp_file" \
        --connect-timeout 5 \
        --max-time "$timeout" \
        -X POST "$url" \
        -H "Content-Type: application/json" \
        -H "X-Request-ID: test-$TIMESTAMP-$$" \
        -d "$data" 2>/dev/null || echo "000")
    
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
    
    # Read response body
    local response_body=$(cat "$temp_file")
    rm -f "$temp_file"
    
    # Store response time
    TEST_NAMES+=("$name")
    RESPONSE_TIMES+=("$response_time")
    
    # Check status
    if [ "$http_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ Status: $http_code (expected: $expected_status)${NC}"
        echo -e "${GREEN}✓ Response Time: ${response_time}ms${NC}"
        echo "Response: $response_body" | jq . 2>/dev/null || echo "$response_body"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        log_test "$name" "PASS" "$response_time" "Status: $http_code"
        return 0
    else
        echo -e "${RED}✗ Status: $http_code (expected: $expected_status)${NC}"
        echo -e "${RED}✗ Response Time: ${response_time}ms${NC}"
        echo "Response: $response_body"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        ERROR_TEST_NAMES+=("$name")
        ERROR_COUNTS+=("1")
        log_test "$name" "FAIL" "$response_time" "Status: $http_code, Body: ${response_body:0:200}"
        return 1
    fi
}

# Function to monitor service health
monitor_health() {
    echo -e "\n${BLUE}[Wave 2 - Health Monitoring]${NC}"
    
    local services=(
        "API Gateway|$API_GATEWAY_URL/health"
        "Intent Classifier|$INTENT_CLASSIFIER_URL/health"
        "Technique Selector|$TECHNIQUE_SELECTOR_URL/health"
        "Prompt Generator|$PROMPT_GENERATOR_URL/health"
    )
    
    for service_info in "${services[@]}"; do
        IFS='|' read -r service_name health_url <<< "$service_info"
        echo -e "\n${YELLOW}Checking $service_name health...${NC}"
        
        local health_response=$(curl -s -w "\n%{http_code}" "$health_url" 2>/dev/null || echo "ERROR\n000")
        local health_body=$(echo "$health_response" | head -n -1)
        local health_code=$(echo "$health_response" | tail -n 1)
        
        if [ "$health_code" = "200" ]; then
            echo -e "${GREEN}✓ $service_name is healthy${NC}"
            echo "$health_body" | jq . 2>/dev/null || echo "$health_body"
        else
            echo -e "${RED}✗ $service_name health check failed (status: $health_code)${NC}"
            echo "$health_body"
        fi
    done
}

# Function to run concurrent tests
run_concurrent_tests() {
    echo -e "\n${BLUE}[Wave 3 - Concurrent Load Testing]${NC}"
    local concurrent_requests=10
    local test_data='{"text": "How do I optimize database queries?"}'
    
    echo -e "${YELLOW}Sending $concurrent_requests concurrent requests...${NC}"
    
    # Create temporary directory for concurrent results
    local temp_dir=$(mktemp -d)
    
    # Launch concurrent requests
    for i in $(seq 1 $concurrent_requests); do
        (
            local start=$(date +%s%N)
            local response=$(curl -s -w "\n%{http_code}" -X POST "$API_GATEWAY_URL/enhance" \
                -H "Content-Type: application/json" \
                -H "X-Request-ID: concurrent-$i-$TIMESTAMP" \
                -d "$test_data" 2>/dev/null || echo "ERROR\n000")
            local end=$(date +%s%N)
            local duration=$(( (end - start) / 1000000 ))
            
            local body=$(echo "$response" | head -n -1)
            local code=$(echo "$response" | tail -n 1)
            
            echo "$i|$code|$duration|$body" > "$temp_dir/result_$i"
        ) &
    done
    
    # Wait for all requests to complete
    wait
    
    # Analyze results
    local successful=0
    local total_time=0
    local min_time=999999
    local max_time=0
    
    for i in $(seq 1 $concurrent_requests); do
        if [ -f "$temp_dir/result_$i" ]; then
            IFS='|' read -r req_num status duration body < "$temp_dir/result_$i"
            
            if [ "$status" = "200" ]; then
                successful=$((successful + 1))
                total_time=$((total_time + duration))
                
                if [ "$duration" -lt "$min_time" ]; then
                    min_time=$duration
                fi
                if [ "$duration" -gt "$max_time" ]; then
                    max_time=$duration
                fi
            fi
        fi
    done
    
    # Calculate statistics
    local avg_time=0
    if [ "$successful" -gt 0 ]; then
        avg_time=$((total_time / successful))
    fi
    
    echo -e "${YELLOW}Concurrent Test Results:${NC}"
    echo "- Successful requests: $successful/$concurrent_requests"
    echo "- Average response time: ${avg_time}ms"
    echo "- Min response time: ${min_time}ms"
    echo "- Max response time: ${max_time}ms"
    
    # Cleanup
    rm -rf "$temp_dir"
    
    # Log results
    log_test "Concurrent Load Test" "COMPLETE" "$avg_time" "Success rate: $successful/$concurrent_requests"
}

# Function to test different scenarios
test_enhancement_scenarios() {
    echo -e "\n${BLUE}[Wave 4 - Enhancement Scenarios]${NC}"
    
    # Scenario 1: Simple question
    test_endpoint "Simple Question Enhancement" \
        "$API_GATEWAY_URL/enhance" \
        '{"text": "What is React?"}'
    
    # Scenario 2: Complex technical question
    test_endpoint "Complex Technical Enhancement" \
        "$API_GATEWAY_URL/enhance" \
        '{
            "text": "Design a distributed caching system for a microservices architecture handling 1M requests per second",
            "context": {"scale": "enterprise", "industry": "fintech"},
            "prefer_techniques": ["tree_of_thoughts", "structured_output"]
        }'
    
    # Scenario 3: Creative task
    test_endpoint "Creative Task Enhancement" \
        "$API_GATEWAY_URL/enhance" \
        '{
            "text": "Write a compelling product description for an AI-powered code assistant",
            "prefer_techniques": ["few_shot", "role_based"]
        }'
    
    # Scenario 4: Analysis request
    test_endpoint "Analysis Request Enhancement" \
        "$API_GATEWAY_URL/enhance" \
        '{
            "text": "Analyze the performance implications of using GraphQL vs REST APIs",
            "target_complexity": "complex"
        }'
    
    # Scenario 5: Edge case - very long text
    local long_text=$(printf 'Explain the following concepts in detail: %s' "$(seq 1 100 | xargs)")
    test_endpoint "Long Text Enhancement" \
        "$API_GATEWAY_URL/enhance" \
        "{\"text\": \"$long_text\"}"
    
    # Scenario 6: Special characters
    test_endpoint "Special Characters Enhancement" \
        "$API_GATEWAY_URL/enhance" \
        '{"text": "How do I handle \"quotes\" and \n newlines in JSON?"}'
}

# Function to validate service integration
validate_service_integration() {
    echo -e "\n${BLUE}[Wave 5 - Service Integration Validation]${NC}"
    
    # Test 1: Intent Classifier Integration
    echo -e "\n${YELLOW}Testing Intent Classifier Integration...${NC}"
    local intent_response=$(curl -s -X POST "$INTENT_CLASSIFIER_URL/api/v1/intents/classify" \
        -H "Content-Type: application/json" \
        -d '{"text": "How do I build a REST API?"}' 2>/dev/null)
    
    if echo "$intent_response" | jq -e '.intent' >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Intent Classifier responding correctly${NC}"
        echo "$intent_response" | jq .
    else
        echo -e "${RED}✗ Intent Classifier integration issue${NC}"
        echo "$intent_response"
    fi
    
    # Test 2: Technique Selector Integration
    echo -e "\n${YELLOW}Testing Technique Selector Integration...${NC}"
    local technique_response=$(curl -s -X POST "$TECHNIQUE_SELECTOR_URL/api/v1/select" \
        -H "Content-Type: application/json" \
        -d '{
            "text": "How do I build a REST API?",
            "intent": "question_answering",
            "complexity": "moderate"
        }' 2>/dev/null)
    
    if echo "$technique_response" | jq -e '.techniques' >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Technique Selector responding correctly${NC}"
        echo "$technique_response" | jq .
    else
        echo -e "${RED}✗ Technique Selector integration issue${NC}"
        echo "$technique_response"
    fi
    
    # Test 3: Full Enhancement Flow
    echo -e "\n${YELLOW}Testing Full Enhancement Flow...${NC}"
    local start_time=$(date +%s%N)
    local enhance_response=$(curl -s -w "\n%{http_code}" -X POST "$API_GATEWAY_URL/enhance" \
        -H "Content-Type: application/json" \
        -d '{"text": "Explain microservices architecture"}' 2>/dev/null)
    local end_time=$(date +%s%N)
    local total_time=$(( (end_time - start_time) / 1000000 ))
    
    local enhance_body=$(echo "$enhance_response" | head -n -1)
    local enhance_code=$(echo "$enhance_response" | tail -n 1)
    
    if [ "$enhance_code" = "200" ] && echo "$enhance_body" | jq -e '.enhanced_text' >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Full enhancement flow working (${total_time}ms)${NC}"
        echo "$enhance_body" | jq '{id, intent, complexity, techniques_used, processing_time_ms}'
    else
        echo -e "${RED}✗ Full enhancement flow failed${NC}"
        echo "Status: $enhance_code"
        echo "$enhance_body"
    fi
}

# Function to check performance metrics
check_performance_metrics() {
    echo -e "\n${BLUE}[Wave 6 - Performance Analysis]${NC}"
    
    # Check Prometheus metrics if available
    if curl -s "http://localhost:9090/api/v1/query?query=up" >/dev/null 2>&1; then
        echo -e "${YELLOW}Fetching Prometheus metrics...${NC}"
        
        # API Gateway request rate
        local request_rate=$(curl -s "http://localhost:9090/api/v1/query?query=rate(http_requests_total[5m])" | \
            jq -r '.data.result[0].value[1] // "N/A"' 2>/dev/null || echo "N/A")
        echo "- Request rate (5m): $request_rate req/s"
        
        # Response time percentiles
        local p95_latency=$(curl -s "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(http_request_duration_seconds_bucket[5m]))" | \
            jq -r '.data.result[0].value[1] // "N/A"' 2>/dev/null || echo "N/A")
        echo "- P95 latency: $p95_latency seconds"
        
        # Error rate
        local error_rate=$(curl -s "http://localhost:9090/api/v1/query?query=rate(http_requests_total{status=~\"5..\"}[5m])" | \
            jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
        echo "- Error rate (5xx): $error_rate errors/s"
    else
        echo -e "${YELLOW}Prometheus not available, using local metrics${NC}"
    fi
    
    # Display collected metrics
    echo -e "\n${YELLOW}Test Performance Summary:${NC}"
    for i in "${!TEST_NAMES[@]}"; do
        echo "- ${TEST_NAMES[$i]}: ${RESPONSE_TIMES[$i]}ms"
    done
}

# Function to generate test report
generate_test_report() {
    echo -e "\n${BLUE}[Wave 7 - Test Report Generation]${NC}"
    
    local report_file="$MONITOR_DIR/test_report_$TIMESTAMP.md"
    
    cat > "$report_file" << EOF
# E2E Integration Test Report
Generated: $(date)

## Summary
- Total Tests: $TOTAL_TESTS
- Passed: $PASSED_TESTS
- Failed: $FAILED_TESTS
- Success Rate: $(awk "BEGIN {printf \"%.2f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")%

## Performance Metrics
$(for i in "${!TEST_NAMES[@]}"; do
    echo "- ${TEST_NAMES[$i]}: ${RESPONSE_TIMES[$i]}ms"
done)

## Error Summary
$(if [ ${#ERROR_TEST_NAMES[@]} -eq 0 ]; then
    echo "No errors detected"
else
    for i in "${!ERROR_TEST_NAMES[@]}"; do
        echo "- ${ERROR_TEST_NAMES[$i]}: 1 error"
    done
fi)

## Test Execution Log
See: test_log_$TIMESTAMP.jsonl

## Recommendations
$(if [ $FAILED_TESTS -gt 0 ]; then
    echo "- Investigate failed tests and service integration issues"
    echo "- Check service logs for detailed error information"
    echo "- Verify all service dependencies are properly configured"
else
    echo "- All tests passed successfully"
    echo "- Consider adding more edge case scenarios"
    echo "- Monitor performance under sustained load"
fi)
EOF

    echo -e "${GREEN}Test report generated: $report_file${NC}"
    cat "$report_file"
}

# Main execution flow
main() {
    echo -e "${YELLOW}Starting E2E Integration Tests...${NC}"
    
    # Wave 1: Service Discovery
    monitor_health
    
    # Wave 2: Basic Integration
    validate_service_integration
    
    # Wave 3: Enhancement Scenarios
    test_enhancement_scenarios
    
    # Wave 4: Concurrent Testing
    run_concurrent_tests
    
    # Wave 5: Performance Analysis
    check_performance_metrics
    
    # Wave 6: Report Generation
    generate_test_report
    
    # Final summary
    echo -e "\n${BLUE}================================================${NC}"
    echo -e "${BLUE}Test Execution Complete${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo -e "Total: $TOTAL_TESTS | ${GREEN}Passed: $PASSED_TESTS${NC} | ${RED}Failed: $FAILED_TESTS${NC}"
    
    # Exit with appropriate code
    if [ $FAILED_TESTS -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Execute main function
main