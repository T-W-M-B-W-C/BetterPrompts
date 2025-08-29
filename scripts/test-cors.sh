#!/bin/bash
# Test script for CORS configuration

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000/api/v1"
ORIGIN="http://localhost:3000"

echo -e "${BLUE}Testing CORS Configuration${NC}"
echo "========================================"

# Test 1: OPTIONS Preflight Request
echo -e "\n${YELLOW}Test 1: OPTIONS Preflight Request${NC}"
echo "Testing preflight for POST /enhance endpoint..."

RESPONSE=$(curl -s -X OPTIONS "${API_URL}/enhance" \
  -H "Origin: ${ORIGIN}" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  -D - \
  -o /dev/null)

echo "$RESPONSE" | head -20

# Check for CORS headers
if echo "$RESPONSE" | grep -q "Access-Control-Allow-Origin: ${ORIGIN}"; then
    echo -e "${GREEN}✓ Access-Control-Allow-Origin header present${NC}"
else
    echo -e "${RED}✗ Access-Control-Allow-Origin header missing${NC}"
fi

if echo "$RESPONSE" | grep -q "Access-Control-Allow-Credentials: true"; then
    echo -e "${GREEN}✓ Access-Control-Allow-Credentials header present${NC}"
else
    echo -e "${RED}✗ Access-Control-Allow-Credentials header missing${NC}"
fi

# Test 2: Actual Request with Origin
echo -e "\n${YELLOW}Test 2: GET Request with Origin Header${NC}"
echo "Testing GET /health endpoint with origin..."

RESPONSE=$(curl -s -X GET "${API_URL}/health" \
  -H "Origin: ${ORIGIN}" \
  -D - \
  -o -)

if echo "$RESPONSE" | grep -q "Access-Control-Allow-Origin: ${ORIGIN}"; then
    echo -e "${GREEN}✓ CORS headers present on GET request${NC}"
else
    echo -e "${RED}✗ CORS headers missing on GET request${NC}"
fi

# Extract body from response
BODY=$(echo "$RESPONSE" | tail -1)
echo "Response body: $BODY"

# Test 3: POST Request with Credentials
echo -e "\n${YELLOW}Test 3: POST Request with Credentials${NC}"
echo "Testing POST /analyze endpoint..."

RESPONSE=$(curl -s -X POST "${API_URL}/analyze" \
  -H "Origin: ${ORIGIN}" \
  -H "Content-Type: application/json" \
  -H "Cookie: session=test-session" \
  -d '{"text": "Test prompt for CORS"}' \
  -D - \
  -w "\n%{http_code}")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
echo "HTTP Status Code: $HTTP_CODE"

if echo "$RESPONSE" | grep -q "Access-Control-Allow-Origin: ${ORIGIN}"; then
    echo -e "${GREEN}✓ CORS headers present on POST request${NC}"
else
    echo -e "${RED}✗ CORS headers missing on POST request${NC}"
fi

# Test 4: Different Origin (should be allowed in dev)
echo -e "\n${YELLOW}Test 4: Different Localhost Origin${NC}"
DIFFERENT_ORIGIN="http://localhost:3001"
echo "Testing with origin: $DIFFERENT_ORIGIN"

RESPONSE=$(curl -s -X OPTIONS "${API_URL}/enhance" \
  -H "Origin: ${DIFFERENT_ORIGIN}" \
  -H "Access-Control-Request-Method: POST" \
  -D - \
  -o /dev/null | head -5)

if echo "$RESPONSE" | grep -q "Access-Control-Allow-Origin: ${DIFFERENT_ORIGIN}"; then
    echo -e "${GREEN}✓ Alternative origin allowed${NC}"
else
    echo -e "${RED}✗ Alternative origin not allowed${NC}"
fi

# Test 5: Invalid Origin (non-localhost)
echo -e "\n${YELLOW}Test 5: Invalid Origin Test${NC}"
INVALID_ORIGIN="http://evil.com"
echo "Testing with invalid origin: $INVALID_ORIGIN"

RESPONSE=$(curl -s -X OPTIONS "${API_URL}/enhance" \
  -H "Origin: ${INVALID_ORIGIN}" \
  -H "Access-Control-Request-Method: POST" \
  -D - \
  -o /dev/null | head -10)

if echo "$RESPONSE" | grep -q "Access-Control-Allow-Origin: ${INVALID_ORIGIN}"; then
    echo -e "${RED}✗ WARNING: Invalid origin was allowed!${NC}"
else
    echo -e "${GREEN}✓ Invalid origin correctly rejected${NC}"
fi

# Test 6: Check Exposed Headers
echo -e "\n${YELLOW}Test 6: Exposed Headers Check${NC}"
echo "Checking for exposed headers..."

RESPONSE=$(curl -s -X GET "${API_URL}/health" \
  -H "Origin: ${ORIGIN}" \
  -D - \
  -o /dev/null | grep -i "Access-Control-Expose-Headers")

if [ -n "$RESPONSE" ]; then
    echo -e "${GREEN}✓ Exposed headers configured:${NC}"
    echo "$RESPONSE"
else
    echo -e "${RED}✗ No exposed headers found${NC}"
fi

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}CORS Configuration Test Complete${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${GREEN}Tips for Frontend Integration:${NC}"
echo "1. Ensure your API client includes credentials:"
echo "   fetch(url, { credentials: 'include' })"
echo "   axios.defaults.withCredentials = true"
echo ""
echo "2. Use the correct API URL:"
echo "   Through nginx: http://localhost/api/v1"
echo "   Direct: http://localhost:8000/api/v1"
echo ""
echo "3. Check browser console for CORS errors"
echo "4. Verify cookies are being sent with requests"