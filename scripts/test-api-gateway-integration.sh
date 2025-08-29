#!/bin/bash

# Comprehensive API Gateway Integration Test
# Tests all service endpoints and integration points

set -e

echo "🔬 API Gateway Integration Test Suite"
echo "====================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test function with JSON response validation
test_endpoint_json() {
    local method=$1
    local endpoint=$2
    local expected_status=$3
    local description=$4
    local data=$5
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "Testing $description... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint" 2>/dev/null || echo -e "\n000")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null || echo -e "\n000")
    fi
    
    # Split response body and status code
    body=$(echo "$response" | sed '$d')
    status_code=$(echo "$response" | tail -1)
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $status_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        # Try to parse JSON response for additional info
        if [ -n "$body" ] && command -v jq &> /dev/null; then
            echo "  Response: $(echo "$body" | jq -c '.' 2>/dev/null || echo "$body" | head -1)"
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: $expected_status, Got: $status_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        if [ -n "$body" ]; then
            echo "  Error: $body"
        fi
    fi
}

# Wait for services
echo "Waiting for services to start..."
for i in {1..30}; do
    if curl -s http://localhost/health > /dev/null 2>&1; then
        echo "Services are ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Services failed to start after 30 seconds${NC}"
        exit 1
    fi
    sleep 1
done

echo ""
echo -e "${BLUE}1. Infrastructure Health Checks${NC}"
echo "================================"
test_endpoint_json "GET" "/health" "200" "Nginx health"
test_endpoint_json "GET" "/api/v1/health" "200" "API Gateway health"
test_endpoint_json "GET" "/api/v1/ready" "200" "API Gateway readiness"

echo ""
echo -e "${BLUE}2. Service Discovery Test${NC}"
echo "========================="
# Check if services are reachable from API Gateway
echo "Checking internal service connectivity..."
docker compose exec -T api-gateway wget -q -O- http://intent-classifier:8001/health && echo -e "  ${GREEN}✓${NC} Intent Classifier reachable" || echo -e "  ${RED}✗${NC} Intent Classifier unreachable"
docker compose exec -T api-gateway wget -q -O- http://technique-selector:8002/health && echo -e "  ${GREEN}✓${NC} Technique Selector reachable" || echo -e "  ${RED}✗${NC} Technique Selector unreachable"
docker compose exec -T api-gateway wget -q -O- http://prompt-generator:8003/health && echo -e "  ${GREEN}✓${NC} Prompt Generator reachable" || echo -e "  ${RED}✗${NC} Prompt Generator unreachable"

echo ""
echo -e "${BLUE}3. Authentication Endpoints${NC}"
echo "==========================="
test_endpoint_json "POST" "/api/v1/auth/register" "400" "Auth registration (missing data)" '{}'
test_endpoint_json "POST" "/api/v1/auth/login" "400" "Auth login (missing data)" '{}'

echo ""
echo -e "${BLUE}4. Public Analysis Endpoint${NC}"
echo "============================"
test_endpoint_json "POST" "/api/v1/analyze" "200" "Intent analysis" '{"text": "How can I improve my writing skills?"}'

echo ""
echo -e "${BLUE}5. Protected Endpoints (No Auth)${NC}"
echo "================================="
test_endpoint_json "GET" "/api/v1/techniques" "401" "Techniques list (unauthorized)"
test_endpoint_json "POST" "/api/v1/enhance" "401" "Enhance prompt (unauthorized)" '{"text": "test"}'
test_endpoint_json "GET" "/api/v1/history" "401" "History (unauthorized)"

echo ""
echo -e "${BLUE}6. Service Integration Test${NC}"
echo "============================"
# Test the full flow with a real user
echo "Creating test user..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "integration-test@example.com",
        "password": "TestPassword123!",
        "name": "Integration Test"
    }' 2>/dev/null)

if echo "$REGISTER_RESPONSE" | grep -q "already exists"; then
    echo "  User already exists, proceeding with login..."
elif echo "$REGISTER_RESPONSE" | grep -q "error"; then
    echo -e "  ${YELLOW}⚠️  Registration failed: $REGISTER_RESPONSE${NC}"
else
    echo -e "  ${GREEN}✓${NC} User registered successfully"
fi

# Login
echo "Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "integration-test@example.com",
        "password": "TestPassword123!"
    }' 2>/dev/null)

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token' 2>/dev/null)
if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo -e "  ${RED}✗${NC} Login failed: $LOGIN_RESPONSE"
else
    echo -e "  ${GREEN}✓${NC} Login successful, got token"
    
    # Test authenticated endpoints
    echo ""
    echo -e "${BLUE}7. Authenticated Endpoint Tests${NC}"
    echo "================================"
    
    # Get techniques
    TECHNIQUES_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/techniques" \
        -H "Authorization: Bearer $TOKEN" 2>/dev/null)
    
    if echo "$TECHNIQUES_RESPONSE" | grep -q "chain_of_thought"; then
        echo -e "  ${GREEN}✓${NC} Techniques endpoint working"
    else
        echo -e "  ${RED}✗${NC} Techniques endpoint failed: $TECHNIQUES_RESPONSE"
    fi
    
    # Test enhance endpoint
    ENHANCE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/enhance" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "text": "Explain quantum computing in simple terms"
        }' 2>/dev/null)
    
    if echo "$ENHANCE_RESPONSE" | grep -q "enhanced_text"; then
        echo -e "  ${GREEN}✓${NC} Enhance endpoint working"
        echo "    Intent: $(echo "$ENHANCE_RESPONSE" | jq -r '.intent' 2>/dev/null)"
        echo "    Techniques: $(echo "$ENHANCE_RESPONSE" | jq -r '.techniques_used[]' 2>/dev/null | tr '\n' ', ')"
    else
        echo -e "  ${RED}✗${NC} Enhance endpoint failed: $ENHANCE_RESPONSE"
    fi
fi

echo ""
echo -e "${BLUE}8. Service Logs Check${NC}"
echo "====================="
echo "Checking for errors in service logs..."

# Function to check service logs
check_service_logs() {
    local service=$1
    local errors=$(docker compose logs "$service" 2>&1 | tail -20 | grep -i "error\|fatal\|panic" | wc -l)
    if [ "$errors" -gt 0 ]; then
        echo -e "  ${YELLOW}⚠️${NC}  $service: Found $errors error(s) in recent logs"
    else
        echo -e "  ${GREEN}✓${NC} $service: No recent errors"
    fi
}

check_service_logs "api-gateway"
check_service_logs "nginx"
check_service_logs "intent-classifier"
check_service_logs "technique-selector"
check_service_logs "prompt-generator"

echo ""
echo "====================================="
echo -e "${BLUE}Test Summary:${NC}"
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}✅ All integration tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed. Please check the logs above.${NC}"
    exit 1
fi