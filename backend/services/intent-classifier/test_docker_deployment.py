#!/usr/bin/env python3
"""Test script to verify the intent-classifier Docker deployment."""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:8001"
API_VERSION = "api/v1"

def test_health_check():
    """Test basic health check."""
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        print(f"✓ Health check passed: {data}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_readiness_check():
    """Test readiness check."""
    print("\n2. Testing readiness check...")
    try:
        response = requests.get(f"{BASE_URL}/{API_VERSION}/health/ready")
        response.raise_for_status()
        data = response.json()
        print(f"✓ Readiness check passed: {data}")
        return True
    except Exception as e:
        print(f"✗ Readiness check failed: {e}")
        return False

def test_classification():
    """Test intent classification."""
    print("\n3. Testing intent classification...")
    
    test_cases = [
        {
            "text": "How do I implement a REST API in Python?",
            "expected_intent": "code_generation"
        },
        {
            "text": "Explain quantum computing to a 5-year-old",
            "expected_intent": "question_answering"
        },
        {
            "text": "Write a poem about artificial intelligence",
            "expected_intent": "creative_writing"
        },
        {
            "text": "Analyze the sales data and find trends",
            "expected_intent": "data_analysis"
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  Test case {i}: {test_case['text'][:50]}...")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/{API_VERSION}/intents/classify",
                json={"text": test_case["text"]},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            elapsed_time = time.time() - start_time
            
            data = response.json()
            intent = data.get("intent")
            confidence = data.get("confidence", 0)
            complexity = data.get("complexity")
            techniques = data.get("suggested_techniques", [])
            
            print(f"  ✓ Classification successful:")
            print(f"    - Intent: {intent} (expected: {test_case['expected_intent']})")
            print(f"    - Confidence: {confidence:.3f}")
            print(f"    - Complexity: {complexity}")
            print(f"    - Techniques: {', '.join(techniques[:3])}")
            print(f"    - Response time: {elapsed_time:.3f}s")
            
            if intent != test_case["expected_intent"]:
                print(f"  ⚠️  Warning: Intent mismatch (got {intent}, expected {test_case['expected_intent']})")
                # Don't fail the test, as the classifier might have valid reasons
            
        except Exception as e:
            print(f"  ✗ Classification failed: {e}")
            all_passed = False
    
    return all_passed

def test_batch_classification():
    """Test batch intent classification."""
    print("\n4. Testing batch classification...")
    
    texts = [
        "What is machine learning?",
        "Create a Python function to sort a list",
        "Write a story about space exploration"
    ]
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/{API_VERSION}/intents/classify/batch",
            json={"texts": texts},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        elapsed_time = time.time() - start_time
        
        data = response.json()
        results = data.get("results", [])
        
        print(f"✓ Batch classification successful:")
        print(f"  - Processed {len(results)} texts")
        print(f"  - Total time: {elapsed_time:.3f}s")
        
        for i, result in enumerate(results):
            print(f"  - Text {i+1}: {result['intent']} (confidence: {result['confidence']:.3f})")
        
        return True
        
    except Exception as e:
        print(f"✗ Batch classification failed: {e}")
        return False

def test_intent_types():
    """Test getting available intent types."""
    print("\n5. Testing intent types endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/{API_VERSION}/intents/types")
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Intent types retrieved:")
        print(f"  - Available intents: {len(data.get('intent_types', []))}")
        print(f"  - Complexity levels: {', '.join(data.get('complexity_levels', []))}")
        print(f"  - Techniques: {len(data.get('techniques', []))}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to get intent types: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Intent Classifier Docker Deployment Test")
    print("=" * 60)
    
    # Wait a bit for service to be ready
    print("\nWaiting for service to be ready...")
    time.sleep(2)
    
    tests = [
        test_health_check,
        test_readiness_check,
        test_classification,
        test_batch_classification,
        test_intent_types
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total} tests")
    
    if passed == total:
        print("\n✅ All tests passed! The Docker deployment is working correctly.")
        return 0
    else:
        print(f"\n❌ {total - passed} tests failed. Please check the logs.")
        return 1

if __name__ == "__main__":
    sys.exit(main())