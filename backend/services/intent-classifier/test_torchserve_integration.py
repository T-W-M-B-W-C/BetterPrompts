#!/usr/bin/env python3
"""Test script to validate TorchServe integration."""

import asyncio
import httpx
import json
from typing import Dict, Any

# Configuration
TORCHSERVE_URL = "http://localhost:8080/predictions/intent_classifier"
TORCHSERVE_HEALTH_URL = "http://localhost:8080/ping"
API_GATEWAY_URL = "http://localhost:8001/api/v1/intents/classify"

# Test cases
TEST_CASES = [
    {
        "text": "How do I implement a binary search tree in Python?",
        "expected_intent": "code_generation",
        "expected_complexity": ["moderate", "complex"]
    },
    {
        "text": "What is the capital of France?",
        "expected_intent": "question_answering",
        "expected_complexity": ["simple"]
    },
    {
        "text": "Write a creative story about a time-traveling scientist",
        "expected_intent": "creative_writing",
        "expected_complexity": ["moderate", "complex"]
    },
    {
        "text": "Analyze this sales data and identify trends",
        "expected_intent": "data_analysis",
        "expected_complexity": ["moderate", "complex"]
    }
]


async def test_torchserve_health():
    """Test TorchServe health endpoint."""
    print("\n1. Testing TorchServe Health Check...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(TORCHSERVE_HEALTH_URL)
            if response.status_code == 200:
                print("✅ TorchServe is healthy")
                return True
            else:
                print(f"❌ TorchServe health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Failed to connect to TorchServe: {e}")
        return False


async def test_direct_torchserve():
    """Test direct TorchServe inference."""
    print("\n2. Testing Direct TorchServe Inference...")
    
    for i, test_case in enumerate(TEST_CASES[:2], 1):
        print(f"\n   Test {i}: {test_case['text'][:50]}...")
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {"text": test_case["text"]}
                response = await client.post(
                    TORCHSERVE_URL,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list):
                        result = result[0]
                    
                    print(f"   ✅ Response received:")
                    print(f"      Intent: {result.get('intent')}")
                    print(f"      Confidence: {result.get('confidence', 0):.3f}")
                    print(f"      Complexity: {result.get('complexity', {}).get('level', 'N/A')}")
                    
                    # Validate expected intent
                    if result.get('intent') == test_case['expected_intent']:
                        print(f"   ✅ Intent matches expected: {test_case['expected_intent']}")
                    else:
                        print(f"   ⚠️  Intent mismatch - Expected: {test_case['expected_intent']}, Got: {result.get('intent')}")
                        
                else:
                    print(f"   ❌ Request failed: {response.status_code}")
                    print(f"      Error: {response.text}")
                    
        except Exception as e:
            print(f"   ❌ Direct inference failed: {e}")


async def test_api_endpoint():
    """Test API endpoint integration."""
    print("\n3. Testing API Endpoint Integration...")
    
    # First check if the service is ready
    try:
        async with httpx.AsyncClient() as client:
            health_response = await client.get("http://localhost:8001/health/ready")
            if health_response.status_code != 200:
                print("❌ Intent classifier service not ready")
                print(f"   Response: {health_response.json()}")
                return
    except Exception as e:
        print(f"❌ Failed to connect to intent classifier service: {e}")
        return
    
    # Test classification endpoint
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n   Test {i}: {test_case['text'][:50]}...")
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {"text": test_case["text"]}
                response = await client.post(
                    API_GATEWAY_URL,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    print(f"   ✅ API Response received:")
                    print(f"      Intent: {result.get('intent')}")
                    print(f"      Confidence: {result.get('confidence', 0):.3f}")
                    print(f"      Complexity: {result.get('complexity')}")
                    print(f"      Techniques: {', '.join(result.get('suggested_techniques', []))}")
                    
                    # Validate expected values
                    if result.get('intent') == test_case['expected_intent']:
                        print(f"   ✅ Intent matches expected: {test_case['expected_intent']}")
                    else:
                        print(f"   ⚠️  Intent mismatch - Expected: {test_case['expected_intent']}, Got: {result.get('intent')}")
                        
                    if result.get('complexity') in test_case['expected_complexity']:
                        print(f"   ✅ Complexity within expected range: {result.get('complexity')}")
                    else:
                        print(f"   ⚠️  Complexity unexpected - Expected: {test_case['expected_complexity']}, Got: {result.get('complexity')}")
                        
                else:
                    print(f"   ❌ API request failed: {response.status_code}")
                    print(f"      Error: {response.json()}")
                    
        except Exception as e:
            print(f"   ❌ API test failed: {e}")


async def test_batch_endpoint():
    """Test batch classification endpoint."""
    print("\n4. Testing Batch Classification...")
    
    texts = [test_case["text"] for test_case in TEST_CASES]
    
    try:
        async with httpx.AsyncClient() as client:
            payload = {"texts": texts}
            response = await client.post(
                "http://localhost:8001/api/v1/intents/classify/batch",
                json=payload,
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Batch classification successful")
                print(f"   Total processing time: {result.get('total_processing_time', 0):.3f}s")
                print(f"   Results count: {len(result.get('results', []))}")
                
                for i, res in enumerate(result.get('results', []), 1):
                    print(f"\n   Result {i}:")
                    print(f"      Intent: {res.get('intent')}")
                    print(f"      Confidence: {res.get('confidence', 0):.3f}")
                    print(f"      Complexity: {res.get('complexity')}")
                    
            else:
                print(f"❌ Batch request failed: {response.status_code}")
                print(f"   Error: {response.json()}")
                
    except Exception as e:
        print(f"❌ Batch test failed: {e}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("TorchServe Integration Test Suite")
    print("=" * 60)
    
    # Test 1: TorchServe health
    torchserve_healthy = await test_torchserve_health()
    
    if torchserve_healthy:
        # Test 2: Direct TorchServe inference
        await test_direct_torchserve()
    else:
        print("\n⚠️  Skipping direct TorchServe tests - service not healthy")
    
    # Test 3: API endpoint
    await test_api_endpoint()
    
    # Test 4: Batch endpoint
    await test_batch_endpoint()
    
    print("\n" + "=" * 60)
    print("Test Suite Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())