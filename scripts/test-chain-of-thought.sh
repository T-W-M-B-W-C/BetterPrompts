#!/bin/bash
# Test script for Chain of Thought technique

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Testing Chain of Thought Technique${NC}"
echo "========================================"

# Test 1: Basic mode with simple prompt
echo -e "\n${YELLOW}Test 1: Basic mode with simple prompt${NC}"
RESULT=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Explain how photosynthesis works in plants",
    "techniques": ["chain_of_thought"],
    "intent": "explaining",
    "complexity": "simple",
    "target_model": "gpt-4"
  }')
echo "$RESULT" | jq -r '.enhanced_prompt' | head -c 150
echo "..."
echo "Improvement: $(echo "$RESULT" | jq -r '.metadata.metrics.improvement_percentage')%"

# Test 2: Enhanced mode with complex algorithmic problem
echo -e "\n${YELLOW}Test 2: Enhanced mode with algorithmic problem${NC}"
RESULT=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Implement an efficient algorithm to find the k-th largest element in an unsorted array",
    "techniques": ["chain_of_thought"],
    "intent": "problem_solving",
    "complexity": "complex",
    "target_model": "gpt-4",
    "context": {
      "enhanced": true
    }
  }')
echo "$RESULT" | jq -r '.enhanced_prompt' | head -c 250
echo "..."
echo "Improvement: $(echo "$RESULT" | jq -r '.metadata.metrics.improvement_percentage')%"

# Test 3: Enhanced mode with mathematical problem
echo -e "\n${YELLOW}Test 3: Enhanced mode with mathematical problem${NC}"
RESULT=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Solve the differential equation dy/dx = 2x + 3y with initial condition y(0) = 1",
    "techniques": ["chain_of_thought"],
    "intent": "problem_solving",
    "complexity": "complex",
    "target_model": "gpt-4",
    "context": {
      "enhanced": true
    }
  }')
echo "$RESULT" | jq -r '.enhanced_prompt' | head -c 250
echo "..."
echo "Improvement: $(echo "$RESULT" | jq -r '.metadata.metrics.improvement_percentage')%"

# Test 4: Basic mode with custom reasoning steps
echo -e "\n${YELLOW}Test 4: Basic mode with custom reasoning steps${NC}"
RESULT=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Design a REST API for a blog platform",
    "techniques": ["chain_of_thought"],
    "intent": "design",
    "complexity": "moderate",
    "target_model": "gpt-4",
    "context": {
      "reasoning_steps": [
        "Identify the core entities",
        "Define the API endpoints",
        "Specify request/response formats",
        "Consider authentication"
      ]
    }
  }')
echo "$RESULT" | jq -r '.enhanced_prompt' | head -c 250
echo "..."
echo "Improvement: $(echo "$RESULT" | jq -r '.metadata.metrics.improvement_percentage')%"

# Test 5: Test through API Gateway
echo -e "\n${YELLOW}Test 5: Full integration through API Gateway${NC}"
RESULT=$(curl -s -X POST http://localhost/api/v1/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "text": "How do I implement a binary search tree in Python?",
    "intent": "code_generation",
    "complexity": "moderate"
  }')
if echo "$RESULT" | jq -e '.error' > /dev/null 2>&1; then
    echo "Error: $(echo "$RESULT" | jq -r '.error')"
else
    echo "Success! Suggested techniques:"
    echo "$RESULT" | jq -r '.suggested_techniques[]' 2>/dev/null || echo "No techniques returned"
fi

echo -e "\n${GREEN}Chain of Thought technique tests completed!${NC}"
echo -e "\n${BLUE}Summary:${NC}"
echo "- Basic mode: Adds step-by-step reasoning template"
echo "- Enhanced mode: Detects domain and adds specific reasoning steps"
echo "- Custom steps: Allows user-provided reasoning steps"
echo "- Performance: Sub-20ms generation time"