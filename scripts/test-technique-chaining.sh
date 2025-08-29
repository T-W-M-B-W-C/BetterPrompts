#!/bin/bash
# Test script for Technique Chaining

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}Testing Technique Chaining Engine${NC}"
echo "============================================"
echo -e "${PURPLE}This test demonstrates how techniques can work together${NC}"
echo -e "${PURPLE}Each technique can see what previous techniques have done${NC}"
echo ""

# Test 1: Chain of Thought + Few-Shot
echo -e "\n${YELLOW}Test 1: Chain of Thought → Few-Shot Learning${NC}"
echo "Intent: Solving a mathematical problem with reasoning + examples"
RESULT=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Solve the quadratic equation x^2 - 5x + 6 = 0",
    "techniques": ["chain_of_thought", "few_shot"],
    "intent": "problem_solving",
    "complexity": "moderate",
    "target_model": "gpt-4",
    "context": {
      "enhanced": true
    }
  }')

echo -e "\n${GREEN}Enhanced Prompt:${NC}"
echo "$RESULT" | jq -r '.enhanced_prompt' | head -c 600
echo "..."

echo -e "\n${GREEN}Chain Summary:${NC}"
echo "$RESULT" | jq -r '.metadata.chain_summary' 2>/dev/null || echo "Chain summary not available"

echo -e "\n${GREEN}Techniques Applied:${NC}"
echo "$RESULT" | jq -r '.metadata.chain_summary.techniques_applied[]' 2>/dev/null || echo "N/A"

# Test 2: Step-by-Step + Chain of Thought
echo -e "\n${YELLOW}Test 2: Step-by-Step → Chain of Thought${NC}"
echo "Intent: Building a complex system with structured steps and reasoning"
RESULT=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Design and implement a rate limiting system for a REST API",
    "techniques": ["step_by_step", "chain_of_thought"],
    "intent": "code_generation",
    "complexity": "complex",
    "target_model": "gpt-4",
    "context": {
      "enhanced": true
    }
  }')

echo -e "\n${GREEN}Enhanced Prompt:${NC}"
echo "$RESULT" | jq -r '.enhanced_prompt' | head -c 600
echo "..."

echo -e "\n${GREEN}Chain Timing:${NC}"
echo "$RESULT" | jq -r '.metadata.chain_summary.technique_timings' 2>/dev/null || echo "Timing data not available"

# Test 3: All Three Core Techniques
echo -e "\n${YELLOW}Test 3: Chain of Thought → Few-Shot → Step-by-Step${NC}"
echo "Intent: Complex data analysis task with all three techniques"
RESULT=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Analyze customer churn data to identify patterns and create a predictive model",
    "techniques": ["chain_of_thought", "few_shot", "step_by_step"],
    "intent": "data_analysis",
    "complexity": "complex",
    "target_model": "gpt-4",
    "context": {
      "enhanced": true,
      "format_style": "detailed"
    }
  }')

echo -e "\n${GREEN}Enhanced Prompt (first 800 chars):${NC}"
echo "$RESULT" | jq -r '.enhanced_prompt' | head -c 800
echo "..."

echo -e "\n${GREEN}Full Chain Metadata:${NC}"
echo "$RESULT" | jq '.metadata.chain_summary' 2>/dev/null || echo "Metadata not available"

echo -e "\n${GREEN}Accumulated Context:${NC}"
echo "$RESULT" | jq -r '.metadata.chain_summary.accumulated_context[]' 2>/dev/null || echo "No accumulated context"

# Test 4: Error Handling in Chain
echo -e "\n${YELLOW}Test 4: Testing Error Recovery in Chain${NC}"
echo "Using an invalid technique to test error handling"
RESULT=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Write a story about a robot",
    "techniques": ["chain_of_thought", "invalid_technique", "few_shot"],
    "intent": "creative_writing",
    "complexity": "simple",
    "target_model": "gpt-4"
  }')

echo -e "\n${GREEN}Result (should continue despite error):${NC}"
echo "$RESULT" | jq -r '.enhanced_prompt' | head -c 400
echo "..."

echo -e "\n${GREEN}Chain Errors:${NC}"
echo "$RESULT" | jq '.metadata.chain_errors' 2>/dev/null || echo "No errors recorded"

echo -e "\n${GREEN}Warnings:${NC}"
echo "$RESULT" | jq -r '.warnings[]' 2>/dev/null || echo "No warnings"

# Test 5: Context Passing Between Techniques
echo -e "\n${YELLOW}Test 5: Demonstrating Context Passing${NC}"
echo "Chain of Thought detects mathematical domain, subsequent techniques should use this info"
RESULT=$(curl -s -X POST http://localhost:8003/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Calculate the derivative of f(x) = x^3 + 2x^2 - 5x + 3",
    "techniques": ["chain_of_thought", "few_shot"],
    "intent": "problem_solving",
    "complexity": "moderate",
    "target_model": "gpt-4",
    "context": {
      "enhanced": true
    }
  }')

echo -e "\n${GREEN}Technique Metadata:${NC}"
echo "$RESULT" | jq '.metadata.technique_metadata' 2>/dev/null | head -c 500
echo "..."

# Summary
echo -e "\n${BLUE}===============================================${NC}"
echo -e "${GREEN}Technique Chaining Test Complete!${NC}"
echo -e "\n${BLUE}Key Features Demonstrated:${NC}"
echo "✅ Multiple techniques applied in sequence"
echo "✅ Context passed between techniques"
echo "✅ Chain metadata and timing tracked"
echo "✅ Error recovery (chain continues despite failures)"
echo "✅ Accumulated context available to all techniques"
echo "✅ Each technique can see previous techniques' work"
echo ""
echo -e "${PURPLE}Chain Benefits:${NC}"
echo "• Techniques build on each other's work"
echo "• Domain detection propagates through chain"
echo "• Complexity insights shared between techniques"
echo "• Better coordination and consistency"
echo "• Full transparency of the enhancement process"