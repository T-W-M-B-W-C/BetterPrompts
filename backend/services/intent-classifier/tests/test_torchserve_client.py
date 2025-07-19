"""Unit tests for TorchServe client with mocking."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import httpx

from app.models.torchserve_client import (
    TorchServeClient,
    TorchServeError,
    TorchServeConnectionError,
    TorchServeInferenceError,
    get_torchserve_client,
    close_torchserve_client
)


@pytest.fixture
async def mock_client():
    """Create a mock TorchServe client."""
    with patch('app.models.torchserve_client.AsyncClient') as mock_async_client:
        client = TorchServeClient()
        client._client = AsyncMock()
        yield client


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('app.models.torchserve_client.settings') as mock_settings:
        mock_settings.TORCHSERVE_URL = "http://localhost:8080/predictions/test_model"
        mock_settings.TORCHSERVE_HEALTH_URL = "http://localhost:8080/ping"
        mock_settings.TORCHSERVE_TIMEOUT = 30
        mock_settings.TORCHSERVE_MAX_RETRIES = 3
        mock_settings.HEALTH_CHECK_INTERVAL = 30
        mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
        mock_settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
        mock_settings.MODEL_MAX_LENGTH = 512
        mock_settings.MODEL_BATCH_SIZE = 32
        yield mock_settings


class TestTorchServeClient:
    """Test TorchServe client functionality."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_client):
        """Test successful health check."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client._client.get.return_value = mock_response
        
        result = await mock_client.health_check()
        
        assert result is True
        assert mock_client._is_healthy is True
        assert mock_client._last_health_check is not None
        
    @pytest.mark.asyncio
    async def test_health_check_failure(self, mock_client):
        """Test failed health check."""
        mock_response = AsyncMock()
        mock_response.status_code = 503
        mock_client._client.get.return_value = mock_response
        
        result = await mock_client.health_check()
        
        assert result is False
        assert mock_client._is_healthy is False
        
    @pytest.mark.asyncio
    async def test_health_check_caching(self, mock_client):
        """Test health check caching."""
        # First check
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client._client.get.return_value = mock_response
        
        await mock_client.health_check()
        first_call_count = mock_client._client.get.call_count
        
        # Second check (should use cache)
        await mock_client.health_check()
        second_call_count = mock_client._client.get.call_count
        
        assert second_call_count == first_call_count  # No additional calls
        
    @pytest.mark.asyncio
    async def test_classify_success(self, mock_client, mock_settings):
        """Test successful classification."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            "intent": "code_generation",
            "confidence": 0.95,
            "complexity": "moderate"
        }]
        mock_client._client.post.return_value = mock_response
        
        result = await mock_client.classify("Write a Python function")
        
        assert result["intent"] == "code_generation"
        assert result["confidence"] == 0.95
        assert result["metadata"]["retry_attempts"] == 0
        
    @pytest.mark.asyncio
    async def test_classify_with_retry(self, mock_client, mock_settings):
        """Test classification with retry logic."""
        # First attempt fails, second succeeds
        mock_client._client.post.side_effect = [
            httpx.ConnectError("Connection refused"),
            AsyncMock(
                status_code=200,
                json=AsyncMock(return_value=[{
                    "intent": "code_generation",
                    "confidence": 0.95
                }])
            )
        ]
        
        result = await mock_client.classify("Write a Python function")
        
        assert result["intent"] == "code_generation"
        assert result["metadata"]["retry_attempts"] == 1
        assert mock_client._client.post.call_count == 2
        
    @pytest.mark.asyncio
    async def test_circuit_breaker_trip(self, mock_client, mock_settings):
        """Test circuit breaker functionality."""
        # Simulate multiple failures
        mock_client._client.post.side_effect = httpx.ConnectError("Connection refused")
        mock_client._circuit_breaker_failures = 4  # One below threshold
        
        with pytest.raises(TorchServeConnectionError):
            await mock_client.classify("Test input")
            
        # Circuit breaker should be tripped
        assert mock_client._circuit_breaker_failures == 5
        assert mock_client._circuit_breaker_open_until is not None
        
        # Subsequent requests should fail immediately
        with pytest.raises(TorchServeConnectionError, match="Circuit breaker is open"):
            await mock_client.classify("Another test")
            
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, mock_client):
        """Test circuit breaker recovery."""
        # Trip the circuit breaker
        mock_client._circuit_breaker_open_until = datetime.now() - timedelta(seconds=1)
        
        # Should be closed now
        assert not mock_client._is_circuit_breaker_open()
        assert mock_client._circuit_breaker_open_until is None
        assert mock_client._circuit_breaker_failures == 0
        
    @pytest.mark.asyncio
    async def test_batch_classify_success(self, mock_client, mock_settings):
        """Test successful batch classification."""
        texts = ["Text 1", "Text 2", "Text 3"]
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"intent": "question_answering", "confidence": 0.9},
            {"intent": "code_generation", "confidence": 0.95},
            {"intent": "creative_writing", "confidence": 0.85}
        ]
        mock_client._client.post.return_value = mock_response
        
        results = await mock_client.batch_classify(texts)
        
        assert len(results) == 3
        assert results[0]["metadata"]["batch_index"] == 0
        assert results[0]["metadata"]["batch_size"] == 3
        
    @pytest.mark.asyncio
    async def test_batch_classify_size_limit(self, mock_client, mock_settings):
        """Test batch size limiting."""
        # Create batch larger than limit
        texts = ["Text"] * 50  # Assuming batch size is 32
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"intent": "test"}] * 32
        mock_client._client.post.return_value = mock_response
        
        results = await mock_client.batch_classify(texts)
        
        # Should be limited to batch size
        assert len(results) == 32
        
    @pytest.mark.asyncio
    async def test_input_validation(self, mock_client):
        """Test input validation."""
        # Empty text
        with pytest.raises(ValueError, match="non-empty string"):
            await mock_client.classify("")
            
        # Non-string input
        with pytest.raises(ValueError, match="non-empty string"):
            await mock_client.classify(None)
            
        # Empty batch
        with pytest.raises(ValueError, match="non-empty list"):
            await mock_client.batch_classify([])
            
    @pytest.mark.asyncio
    async def test_model_info(self, mock_client):
        """Test getting model information."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "modelName": "intent_classifier",
            "modelVersion": "1.0",
            "status": "Loaded"
        }
        mock_client._client.get.return_value = mock_response
        
        info = await mock_client.get_model_info()
        
        assert info["modelName"] == "intent_classifier"
        assert info["status"] == "Loaded"
        
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality."""
        with patch('app.models.torchserve_client.AsyncClient') as mock_async_client:
            mock_instance = AsyncMock()
            mock_async_client.return_value = mock_instance
            
            async with TorchServeClient() as client:
                assert client._client is not None
                
            # Should be closed after context
            mock_instance.aclose.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_global_client_singleton(self):
        """Test global client singleton pattern."""
        client1 = await get_torchserve_client()
        client2 = await get_torchserve_client()
        
        assert client1 is client2
        
        await close_torchserve_client()


class TestMetrics:
    """Test Prometheus metrics integration."""
    
    @pytest.mark.asyncio
    async def test_request_metrics(self, mock_client):
        """Test request metrics are recorded."""
        with patch('app.models.torchserve_client.torchserve_requests') as mock_counter:
            with patch('app.models.torchserve_client.torchserve_request_duration') as mock_histogram:
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.json.return_value = [{"intent": "test"}]
                mock_client._client.post.return_value = mock_response
                
                await mock_client.classify("Test")
                
                mock_counter.labels.assert_called_with(method="classify", status="success")
                mock_histogram.labels.assert_called_with(method="classify")
                
    @pytest.mark.asyncio
    async def test_retry_metrics(self, mock_client):
        """Test retry metrics are recorded."""
        with patch('app.models.torchserve_client.torchserve_retry_count') as mock_retry:
            mock_client._client.post.side_effect = [
                httpx.ConnectError("Failed"),
                AsyncMock(status_code=200, json=AsyncMock(return_value=[{"intent": "test"}]))
            ]
            
            await mock_client.classify("Test")
            
            mock_retry.labels.assert_called_with(method="classify")