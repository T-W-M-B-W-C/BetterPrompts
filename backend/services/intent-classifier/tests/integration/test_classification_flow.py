"""Integration tests for the complete classification flow."""

import pytest
from unittest.mock import patch, AsyncMock
import time
from httpx import AsyncClient

from app.main import app
from app.schemas.intent import IntentRequest, IntentResponse


class TestClassificationFlow:
    """Integration tests for the full classification flow."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_classification_flow_with_cache_miss(self, async_client, mock_torchserve_client, mock_cache_service):
        """Test complete classification flow with cache miss."""
        # Arrange
        mock_cache_service.get_intent.return_value = None  # Cache miss
        mock_torchserve_client.classify.return_value = {
            "intent": "code_generation",
            "confidence": 0.92,
            "complexity": {"level": "moderate"},
            "techniques": [{"name": "chain_of_thought"}, {"name": "few_shot"}],
            "metadata": {"inference_time_ms": 150}
        }
        
        with patch('app.api.v1.intents.classifier.torchserve_client', mock_torchserve_client), \
             patch('app.api.v1.intents.classifier.use_torchserve', True), \
             patch('app.api.v1.intents.classifier._initialized', True):
            
            # Act
            response = await async_client.post(
                "/api/v1/intents/classify",
                json={"text": "Write a Python function to calculate factorial"}
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert data["intent"] == "code_generation"
            assert data["confidence"] == 0.92
            assert data["complexity"] == "moderate"
            assert "chain_of_thought" in data["suggested_techniques"]
            assert "few_shot" in data["suggested_techniques"]
            assert "processing_time" in data["metadata"]
            
            # Verify cache was checked and set
            mock_cache_service.get_intent.assert_called_once()
            mock_cache_service.set_intent.assert_called_once()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_classification_flow_with_cache_hit(self, async_client, mock_cache_service):
        """Test complete classification flow with cache hit."""
        # Arrange
        cached_result = {
            "intent": "question_answering",
            "confidence": 0.98,
            "complexity": "simple",
            "suggested_techniques": ["direct_answer"],
            "metadata": {"cached": True, "model_version": "1.0.0"}
        }
        mock_cache_service.get_intent.return_value = cached_result
        
        # Act
        start_time = time.time()
        response = await async_client.post(
            "/api/v1/intents/classify",
            json={"text": "What is the capital of France?"}
        )
        elapsed_time = time.time() - start_time
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["intent"] == "question_answering"
        assert data["confidence"] == 0.98
        assert data["complexity"] == "simple"
        assert data["metadata"]["cached"] is True
        
        # Cache hit should be fast
        assert elapsed_time < 0.1  # Less than 100ms
        
        # Verify cache was checked but not set
        mock_cache_service.get_intent.assert_called_once()
        mock_cache_service.set_intent.assert_not_called()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_classification_flow(self, async_client, mock_torchserve_client, mock_cache_service):
        """Test batch classification flow."""
        # Arrange
        mock_cache_service.get_intent.return_value = None  # All cache misses
        
        # Different responses for each text
        mock_torchserve_client.classify.side_effect = [
            {
                "intent": "code_generation",
                "confidence": 0.95,
                "complexity": {"level": "moderate"},
                "techniques": [{"name": "chain_of_thought"}],
                "metadata": {"inference_time_ms": 100}
            },
            {
                "intent": "question_answering",
                "confidence": 0.97,
                "complexity": {"level": "simple"},
                "techniques": [{"name": "direct_answer"}],
                "metadata": {"inference_time_ms": 80}
            },
            {
                "intent": "creative_writing",
                "confidence": 0.89,
                "complexity": {"level": "complex"},
                "techniques": [{"name": "few_shot"}, {"name": "iterative_refinement"}],
                "metadata": {"inference_time_ms": 120}
            }
        ]
        
        with patch('app.api.v1.intents.classifier.torchserve_client', mock_torchserve_client), \
             patch('app.api.v1.intents.classifier.use_torchserve', True), \
             patch('app.api.v1.intents.classifier._initialized', True):
            
            # Act
            response = await async_client.post(
                "/api/v1/intents/classify/batch",
                json={
                    "texts": [
                        "Write a sorting algorithm",
                        "What is machine learning?",
                        "Write a story about a robot"
                    ]
                }
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["results"]) == 3
            assert data["results"][0]["intent"] == "code_generation"
            assert data["results"][1]["intent"] == "question_answering"
            assert data["results"][2]["intent"] == "creative_writing"
            
            assert data["total_processing_time"] > 0
            
            # Verify cache operations
            assert mock_cache_service.get_intent.call_count == 3
            assert mock_cache_service.set_intent.call_count == 3
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_classification_with_context(self, async_client, mock_torchserve_client, mock_cache_service):
        """Test classification with additional context."""
        # Arrange
        mock_cache_service.get_intent.return_value = None
        mock_torchserve_client.classify.return_value = {
            "intent": "code_generation",
            "confidence": 0.94,
            "complexity": {"level": "moderate"},
            "techniques": [{"name": "chain_of_thought"}],
            "metadata": {"inference_time_ms": 110}
        }
        
        with patch('app.api.v1.intents.classifier.torchserve_client', mock_torchserve_client), \
             patch('app.api.v1.intents.classifier.use_torchserve', True), \
             patch('app.api.v1.intents.classifier._initialized', True):
            
            # Act
            response = await async_client.post(
                "/api/v1/intents/classify",
                json={
                    "text": "Implement binary search",
                    "context": {
                        "language": "Python",
                        "difficulty": "intermediate"
                    },
                    "user_id": "test-user-123"
                }
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["intent"] == "code_generation"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_classification_validation_errors(self, async_client):
        """Test classification with validation errors."""
        # Test empty text
        response = await async_client.post(
            "/api/v1/intents/classify",
            json={"text": ""}
        )
        assert response.status_code == 422
        
        # Test text too long
        response = await async_client.post(
            "/api/v1/intents/classify",
            json={"text": "a" * 5001}  # Exceeds max length
        )
        assert response.status_code == 422
        
        # Test missing text field
        response = await async_client.post(
            "/api/v1/intents/classify",
            json={}
        )
        assert response.status_code == 422
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_classification_torchserve_failure(self, async_client, mock_torchserve_client, mock_cache_service):
        """Test classification when TorchServe fails."""
        # Arrange
        mock_cache_service.get_intent.return_value = None
        mock_torchserve_client.classify.side_effect = Exception("TorchServe connection failed")
        
        with patch('app.api.v1.intents.classifier.torchserve_client', mock_torchserve_client), \
             patch('app.api.v1.intents.classifier.use_torchserve', True), \
             patch('app.api.v1.intents.classifier._initialized', True):
            
            # Act
            response = await async_client.post(
                "/api/v1/intents/classify",
                json={"text": "Test input"}
            )
            
            # Assert
            assert response.status_code == 500
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_intent_types_endpoint(self, async_client):
        """Test getting available intent types."""
        # Act
        response = await async_client.get("/api/v1/intents/types")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert "intent_types" in data
        assert "complexity_levels" in data
        assert "techniques" in data
        
        assert len(data["intent_types"]) == 10
        assert len(data["complexity_levels"]) == 3
        assert len(data["techniques"]) >= 7
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_endpoints(self, async_client):
        """Test all health check endpoints."""
        # Basic health check
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        
        # Liveness check
        response = await async_client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"
        
        # Readiness check (may fail if dependencies not mocked)
        response = await async_client.get("/health/ready")
        # Should at least return a response
        assert response.status_code in [200, 503]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, async_client):
        """Test Prometheus metrics endpoint."""
        # Act
        response = await async_client.get("/metrics")
        
        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        
        # Check for expected metrics
        metrics_text = response.text
        assert "intent_classification_requests_total" in metrics_text
        assert "intent_classification_duration_seconds" in metrics_text
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_client, mock_torchserve_client, mock_cache_service):
        """Test handling concurrent classification requests."""
        # Arrange
        mock_cache_service.get_intent.return_value = None
        mock_torchserve_client.classify.return_value = {
            "intent": "test",
            "confidence": 0.9,
            "complexity": {"level": "simple"},
            "techniques": [{"name": "test"}],
            "metadata": {"inference_time_ms": 50}
        }
        
        with patch('app.api.v1.intents.classifier.torchserve_client', mock_torchserve_client), \
             patch('app.api.v1.intents.classifier.use_torchserve', True), \
             patch('app.api.v1.intents.classifier._initialized', True):
            
            # Act - Send multiple concurrent requests
            import asyncio
            
            async def make_request(text):
                return await async_client.post(
                    "/api/v1/intents/classify",
                    json={"text": text}
                )
            
            tasks = [
                make_request(f"Test request {i}")
                for i in range(10)
            ]
            
            responses = await asyncio.gather(*tasks)
            
            # Assert
            assert all(r.status_code == 200 for r in responses)
            assert mock_torchserve_client.classify.call_count == 10