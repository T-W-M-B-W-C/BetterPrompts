#!/bin/bash

# Test the enhance endpoint
echo "Testing the enhance endpoint..."

# Test 1: Basic enhancement request
echo -e "\n1. Basic enhancement request:"
curl -X POST http://localhost/api/v1/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "text": "How do I write a good React component?"
  }' | jq .

# Test 2: With context and preferences
echo -e "\n2. With context and preferences:"
curl -X POST http://localhost/api/v1/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Explain quantum computing",
    "context": {
      "audience": "beginners",
      "depth": "moderate"
    },
    "prefer_techniques": ["few_shot", "chain_of_thought"]
  }' | jq .

# Test 3: Complex request
echo -e "\n3. Complex request:"
curl -X POST http://localhost/api/v1/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Design a scalable microservices architecture for an e-commerce platform that handles millions of users with real-time inventory management and personalized recommendations",
    "target_complexity": "complex"
  }' | jq .

# Test 4: Direct technique selector test
echo -e "\n4. Direct technique selector test:"
curl -X POST http://localhost:8002/api/v1/select \
  -H "Content-Type: application/json" \
  -d '{
    "text": "How do I write a good React component?",
    "intent": "question_answering",
    "complexity": "simple"
  }' | jq .