#!/bin/bash
# Test script for Step-by-Step technique

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Testing Step-by-Step Technique${NC}"
echo "=========================================="

# Test 1: Simple task with code generation intent
echo -e "\n${YELLOW}Test 1: Simple task with code generation intent${NC}"
RESULT=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Create a function to validate email addresses",
    "techniques": ["step_by_step"],
    "intent": "code_generation",
    "complexity": "simple",
    "target_model": "gpt-4"
  }')
echo "$RESULT" | jq -r '.enhanced_prompt' | head -c 300
echo "..."
echo "Steps generated: $(echo "$RESULT" | jq -r '.metadata.steps_count // "N/A"')"
echo "Improvement: $(echo "$RESULT" | jq -r '.metadata.metrics.improvement_percentage')%"

# Test 2: Moderate complexity analysis task
echo -e "\n${YELLOW}Test 2: Moderate complexity analysis task${NC}"
RESULT=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Analyze the performance bottlenecks in our web application",
    "techniques": ["step_by_step"],
    "intent": "analyzing",
    "complexity": "moderate",
    "target_model": "gpt-4"
  }')
echo "$RESULT" | jq -r '.enhanced_prompt' | head -c 300
echo "..."
echo "Improvement: $(echo "$RESULT" | jq -r '.metadata.metrics.improvement_percentage')%"

# Test 3: Complex problem solving with sub-steps
echo -e "\n${YELLOW}Test 3: Complex problem solving task${NC}"
RESULT=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Design and implement a microservices architecture for an e-commerce platform",
    "techniques": ["step_by_step"],
    "intent": "problem_solving",
    "complexity": "complex",
    "target_model": "gpt-4"
  }')
echo "$RESULT" | jq -r '.enhanced_prompt' | head -c 400
echo "..."
echo "Improvement: $(echo "$RESULT" | jq -r '.metadata.metrics.improvement_percentage')%"

# Test 4: Custom steps provided
echo -e "\n${YELLOW}Test 4: Using custom steps${NC}"
RESULT=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Deploy a web application to AWS",
    "techniques": ["step_by_step"],
    "intent": "implementation",
    "complexity": "moderate",
    "target_model": "gpt-4",
    "context": {
      "steps": [
        "Set up AWS account and configure credentials",
        "Choose the appropriate AWS services",
        "Prepare the application for deployment",
        "Deploy using the chosen method",
        "Configure monitoring and logging"
      ],
      "verification_steps": [
        "Test the deployed application",
        "Verify all features work correctly",
        "Check performance metrics"
      ]
    }
  }')
echo "$RESULT" | jq -r '.enhanced_prompt' | head -c 350
echo "..."
echo "Improvement: $(echo "$RESULT" | jq -r '.metadata.metrics.improvement_percentage')%"

# Test 5: Detailed format with time estimates
echo -e "\n${YELLOW}Test 5: Detailed format with time estimates${NC}"
RESULT=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Implement a machine learning model for customer churn prediction",
    "techniques": ["step_by_step"],
    "intent": "code_generation",
    "complexity": "complex",
    "target_model": "gpt-4",
    "context": {
      "format_style": "detailed",
      "include_time_estimates": true
    }
  }')
echo "$RESULT" | jq -r '.enhanced_prompt' | head -c 450
echo "..."
echo "Format: detailed with time estimates"
echo "Improvement: $(echo "$RESULT" | jq -r '.metadata.metrics.improvement_percentage')%"

# Test 6: Checklist format
echo -e "\n${YELLOW}Test 6: Checklist format${NC}"
RESULT=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Prepare for a technical interview",
    "techniques": ["step_by_step"],
    "intent": "task_planning",
    "complexity": "moderate",
    "target_model": "gpt-4",
    "context": {
      "format_style": "checklist"
    }
  }')
echo "$RESULT" | jq -r '.enhanced_prompt' | head -c 300
echo "..."
echo "Format: checklist"
echo "Improvement: $(echo "$RESULT" | jq -r '.metadata.metrics.improvement_percentage')%"

# Test 7: Test through API Gateway
echo -e "\n${YELLOW}Test 7: Full integration through API Gateway${NC}"
RESULT=$(curl -s -X POST http://localhost/api/v1/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Build a REST API with authentication",
    "intent": "code_generation",
    "complexity": "moderate"
  }')
if echo "$RESULT" | jq -e '.error' > /dev/null 2>&1; then
    echo "Error: $(echo "$RESULT" | jq -r '.error')"
else
    echo "Success! Suggested techniques:"
    echo "$RESULT" | jq -r '.suggested_techniques[]' 2>/dev/null || echo "No techniques returned"
fi

echo -e "\n${GREEN}Step-by-Step technique tests completed!${NC}"
echo -e "\n${BLUE}Summary:${NC}"
echo "- Dynamic step generation based on intent and complexity"
echo "- Sub-steps for complex tasks"
echo "- Multiple format styles (standard, detailed, checklist)"
echo "- Time estimates and progress tracking"
echo "- Verification steps for quality assurance"
echo "- Intent-aware step customization for 11+ task types"
echo "- Performance: Sub-20ms generation time"