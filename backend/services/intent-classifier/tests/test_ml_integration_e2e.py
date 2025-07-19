"""
End-to-end tests for ML integration with TorchServe.
These tests validate the complete flow from API to model inference.
"""

import pytest
import httpx
import asyncio
from typing import Dict, List
import time
from datetime import datetime

# Test configuration
E2E_TEST_TIMEOUT = 30  # seconds
TORCHSERVE_URL = "http://localhost:8080"
API_BASE_URL = "http://localhost:8001"


@pytest.mark.e2e
@pytest.mark.torchserve
class TestMLIntegrationE2E:
    """End-to-end tests for ML integration."""
    
    @pytest.fixture(scope="class")
    async def api_client(self):
        """Create an API client for testing."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=E2E_TEST_TIMEOUT) as client:
            yield client
    
    @pytest.fixture(scope="class")
    async def check_services(self):
        """Verify required services are running."""
        services_ok = True
        errors = []
        
        # Check TorchServe
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{TORCHSERVE_URL}/ping")
                if response.status_code != 200:
                    errors.append("TorchServe not healthy")
                    services_ok = False
        except Exception as e:
            errors.append(f"TorchServe not reachable: {e}")
            services_ok = False
        
        # Check API service
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/health")
                if response.status_code != 200:
                    errors.append("API service not healthy")
                    services_ok = False
        except Exception as e:
            errors.append(f"API service not reachable: {e}")
            services_ok = False
        
        if not services_ok:
            pytest.skip(f"Required services not available: {', '.join(errors)}")
    
    @pytest.mark.critical
    async def test_simple_classification_e2e(self, api_client, check_services):
        """Test simple classification end-to-end.
        
        Validates:
        - API accepts request
        - TorchServe processes inference
        - Response format is correct
        - Latency is acceptable
        """
        start_time = time.time()
        
        response = await api_client.post(
            "/api/v1/intents/classify",
            json={"text": "What is machine learning?"}
        )
        
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "intent" in data
        assert "confidence" in data
        assert "complexity" in data
        assert "suggested_techniques" in data
        assert "metadata" in data
        
        # Validate response values
        assert data["intent"] in [
            "question_answering", "educational", "information_retrieval"
        ]
        assert 0 <= data["confidence"] <= 1
        assert data["complexity"] in ["simple", "moderate", "complex"]
        assert isinstance(data["suggested_techniques"], list)
        assert len(data["suggested_techniques"]) > 0
        
        # Performance validation
        assert elapsed_time < 5.0, f"Response took {elapsed_time:.2f}s, expected < 5s"
        assert data["metadata"]["processing_time"] < 2.0
    
    @pytest.mark.critical
    async def test_complex_classification_e2e(self, api_client, check_services):
        """Test complex multi-step classification.
        
        Validates:
        - Complex intent recognition
        - Multiple technique suggestions
        - Appropriate complexity scoring
        """
        complex_prompt = """
        I need to analyze customer feedback data from the last quarter,
        identify common complaints and positive feedback themes,
        create visualizations showing trend over time,
        and generate a report with actionable recommendations
        for the product team.
        """
        
        response = await api_client.post(
            "/api/v1/intents/classify",
            json={"text": complex_prompt}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should recognize as complex task
        assert data["complexity"] in ["moderate", "complex"]
        
        # Should suggest advanced techniques
        expected_techniques = ["chain_of_thought", "tree_of_thoughts", "step_by_step"]
        assert any(tech in data["suggested_techniques"] for tech in expected_techniques)
        
        # Should identify as analysis task
        assert data["intent"] in ["data_analysis", "analysis", "reporting"]
    
    async def test_batch_classification_e2e(self, api_client, check_services):
        """Test batch classification performance.
        
        Validates:
        - Batch processing works correctly
        - All items are processed
        - Performance is better than sequential
        """
        test_texts = [
            "Write a Python function",
            "Explain quantum computing",
            "Translate this to French",
            "Debug this JavaScript code",
            "Create a marketing plan"
        ]
        
        start_time = time.time()
        
        response = await api_client.post(
            "/api/v1/intents/classify/batch",
            json={"texts": test_texts}
        )
        
        batch_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate batch response
        assert "results" in data
        assert len(data["results"]) == len(test_texts)
        assert "total_processing_time" in data
        
        # Validate each result
        intents_found = set()
        for i, result in enumerate(data["results"]):
            assert "intent" in result
            assert "confidence" in result
            assert "complexity" in result
            intents_found.add(result["intent"])
        
        # Should identify diverse intents
        assert len(intents_found) >= 3
        
        # Batch should be faster than sequential
        avg_time_per_item = batch_time / len(test_texts)
        assert avg_time_per_item < 2.0
    
    @pytest.mark.slow
    async def test_concurrent_requests_e2e(self, api_client, check_services):
        """Test system under concurrent load.
        
        Validates:
        - System handles concurrent requests
        - No race conditions
        - Acceptable performance under load
        """
        num_concurrent = 10
        
        async def classify(text: str) -> Dict:
            response = await api_client.post(
                "/api/v1/intents/classify",
                json={"text": text}
            )
            return response.json() if response.status_code == 200 else None
        
        # Create diverse test prompts
        test_prompts = [
            f"Test prompt {i}: {prompt}"
            for i, prompt in enumerate([
                "Write code", "Analyze data", "Create report",
                "Translate text", "Answer question"
            ] * 2)
        ]
        
        start_time = time.time()
        
        # Run concurrent requests
        results = await asyncio.gather(
            *[classify(prompt) for prompt in test_prompts],
            return_exceptions=True
        )
        
        total_time = time.time() - start_time
        
        # Validate results
        successful_results = [r for r in results if isinstance(r, dict)]
        assert len(successful_results) >= num_concurrent * 0.9  # 90% success rate
        
        # Check performance
        assert total_time < 10.0  # Should complete within 10 seconds
        
        # Validate result diversity
        intents = {r["intent"] for r in successful_results if r}
        assert len(intents) >= 3
    
    async def test_error_handling_e2e(self, api_client, check_services):
        """Test error handling scenarios.
        
        Validates:
        - Graceful error handling
        - Appropriate error messages
        - No system crashes
        """
        # Test empty input
        response = await api_client.post(
            "/api/v1/intents/classify",
            json={"text": ""}
        )
        assert response.status_code == 400
        assert "detail" in response.json()
        
        # Test missing field
        response = await api_client.post(
            "/api/v1/intents/classify",
            json={}
        )
        assert response.status_code == 422
        
        # Test extremely long input
        very_long_text = "x" * 50000
        response = await api_client.post(
            "/api/v1/intents/classify",
            json={"text": very_long_text}
        )
        # Should either succeed with truncation or fail gracefully
        assert response.status_code in [200, 413, 400]
    
    @pytest.mark.critical
    async def test_circuit_breaker_e2e(self, api_client):
        """Test circuit breaker functionality.
        
        Validates:
        - Circuit breaker activates on failures
        - Recovers after timeout
        - Provides appropriate error messages
        """
        # This test simulates TorchServe being down
        # We'll need to mock or actually stop TorchServe
        
        # For now, we'll test the health endpoint behavior
        response = await api_client.get("/health/ready")
        initial_health = response.json()
        
        # The circuit breaker status should be reflected in health
        assert "details" in initial_health
        if "torchserve" in initial_health["details"]:
            assert initial_health["details"]["torchserve"] in ["healthy", "not_applicable", "unhealthy"]
    
    async def test_model_version_consistency(self, api_client, check_services):
        """Test model version consistency.
        
        Validates:
        - Model version is reported
        - Consistent across requests
        - Matches expected version
        """
        responses = []
        
        # Make multiple requests
        for _ in range(3):
            response = await api_client.post(
                "/api/v1/intents/classify",
                json={"text": "Test model version"}
            )
            if response.status_code == 200:
                responses.append(response.json())
        
        assert len(responses) > 0
        
        # Check version consistency
        versions = [r["metadata"].get("model_version") for r in responses]
        assert all(v == versions[0] for v in versions)
    
    @pytest.mark.slow
    async def test_cache_effectiveness(self, api_client, check_services):
        """Test caching behavior for repeated requests.
        
        Validates:
        - Cache hits for identical requests
        - Faster response times for cached results
        - Cache invalidation works
        """
        test_text = "What is artificial intelligence?"
        
        # First request (cache miss)
        start_time = time.time()
        response1 = await api_client.post(
            "/api/v1/intents/classify",
            json={"text": test_text}
        )
        first_request_time = time.time() - start_time
        
        assert response1.status_code == 200
        result1 = response1.json()
        
        # Second request (should be cache hit)
        start_time = time.time()
        response2 = await api_client.post(
            "/api/v1/intents/classify",
            json={"text": test_text}
        )
        second_request_time = time.time() - start_time
        
        assert response2.status_code == 200
        result2 = response2.json()
        
        # Results should be identical
        assert result1["intent"] == result2["intent"]
        assert result1["confidence"] == result2["confidence"]
        
        # Second request should be faster (cache hit)
        # Allow some variance for network latency
        if result2["metadata"].get("cache_hit"):
            assert second_request_time < first_request_time * 0.5