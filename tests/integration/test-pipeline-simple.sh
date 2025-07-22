#!/bin/bash
# Simple pipeline test to debug the enhance endpoint

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================"
echo "Simple Pipeline Test - Debug Mode"
echo "============================================"
echo ""

# Test data
TEST_TEXT="How do I implement a binary search tree in Python?"

# 1. Test Intent Classifier directly
echo -e "${YELLOW}[1] Testing Intent Classifier...${NC}"
intent_response=$(curl -s -X POST http://localhost:8001/api/v1/intents/classify \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$TEST_TEXT\"}")

echo "Response:"
echo "$intent_response" | jq .

# Extract values
intent=$(echo "$intent_response" | jq -r '.intent')
complexity=$(echo "$intent_response" | jq -r '.complexity')
echo -e "${GREEN}Intent: $intent, Complexity: $complexity${NC}"
echo ""

# 2. Test Technique Selector directly
echo -e "${YELLOW}[2] Testing Technique Selector...${NC}"
technique_response=$(curl -s -X POST http://localhost:8002/api/v1/select \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": \"$TEST_TEXT\",
    \"intent\": \"$intent\",
    \"complexity\": \"$complexity\"
  }")

echo "Response:"
echo "$technique_response" | jq .

# Extract techniques
techniques=$(echo "$technique_response" | jq -r '.techniques[].id' | tr '\n' ' ')
echo -e "${GREEN}Selected techniques: $techniques${NC}"
echo ""

# 3. Test Prompt Generator directly
echo -e "${YELLOW}[3] Testing Prompt Generator...${NC}"
# Convert techniques to JSON array
techniques_json=$(echo "$techniques" | xargs -n1 | jq -R . | jq -s .)
generator_response=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": \"$TEST_TEXT\",
    \"intent\": \"$intent\",
    \"complexity\": \"$complexity\",
    \"techniques\": $techniques_json
  }")

echo "Response:"
echo "$generator_response" | jq .

# Extract enhanced prompt
enhanced=$(echo "$generator_response" | jq -r '.enhanced_prompt')
if [ -n "$enhanced" ] && [ "$enhanced" != "null" ]; then
    echo -e "${GREEN}Enhanced prompt generated successfully!${NC}"
else
    echo -e "${RED}Enhanced prompt is empty!${NC}"
fi
echo ""

# 4. Test full pipeline through API Gateway
echo -e "${YELLOW}[4] Testing Full Pipeline (API Gateway)...${NC}"
full_response=$(curl -s -X POST http://localhost/api/v1/enhance \
  -H "Content-Type: application/json" \
  -H "X-Test-Mode: true" \
  -d "{\"text\": \"$TEST_TEXT\"}")

echo "Response:"
echo "$full_response" | jq .

# Check if enhanced_text is present
enhanced_text=$(echo "$full_response" | jq -r '.enhanced_text')
if [ -n "$enhanced_text" ] && [ "$enhanced_text" != "null" ] && [ "$enhanced_text" != "" ]; then
    echo -e "${GREEN}✓ Full pipeline working!${NC}"
else
    echo -e "${RED}✗ Full pipeline failed - enhanced_text is empty${NC}"
    
    # Show API Gateway logs
    echo ""
    echo "Recent API Gateway errors:"
    docker compose logs --tail=20 api-gateway | grep -E "error|Error|failed" || echo "No errors found"
fi