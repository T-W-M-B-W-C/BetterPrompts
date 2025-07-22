"""Unit tests for TorchServe client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from datetime import datetime, timedelta
import asyncio

from app.models.torchserve_client import (
    TorchServeClient,
    TorchServeError,
    TorchServeConnectionError,
    TorchServeInferenceError,
    get_torchserve_client,
    close_torchserve_client
)


class TestTorchServeClient:
    """Test suite for TorchServe client."""
    
    @pytest.fixture
    def client(self):
        """Create a TorchServe client instance."""
        return TorchServeClient()
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('app.models.torchserve_client.settings') as mock_settings:
            mock_settings.TORCHSERVE_URL = "http://localhost:8080/predictions/intent"
            mock_settings.TORCHSERVE_HEALTH_URL = "http://localhost:8080/ping"
            mock_settings.TORCHSERVE_TIMEOUT = 30
            mock_settings.TORCHSERVE_MAX_RETRIES = 3
            mock_settings.HEALTH_CHECK_INTERVAL = 30
            mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
            mock_settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
            mock_settings.MODEL_MAX_LENGTH = 512
            mock_settings.MODEL_BATCH_SIZE = 32
            yield mock_settings
    
    @pytest.mark.asyncio
    async def test_connect_success(self, client, mock_settings):
        """Test successful connection to TorchServe."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_async_client = AsyncMock()
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_async_client
            
            # Act
            await client.connect()
            
            # Assert
            assert client._client is not None
            assert client._is_healthy is True
            mock_async_client.get.assert_called_once_with(mock_settings.TORCHSERVE_HEALTH_URL)
    
    @pytest.mark.asyncio
    async def test_connect_health_check_failure(self, client, mock_settings):
        """Test connection when health check fails."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 503
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_async_client = AsyncMock()
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_async_client
            
            # Act
            await client.connect()
            
            # Assert
            assert client._client is not None
            assert client._is_healthy is False
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, client, mock_settings):
        """Test successful health check."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_async_client = AsyncMock()
        mock_async_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_async_client
        
        # Act
        result = await client.health_check()
        
        # Assert
        assert result is True
        assert client._is_healthy is True
        assert client._last_health_check is not None
    
    @pytest.mark.asyncio
    async def test_health_check_caching(self, client, mock_settings):
        """Test health check caching behavior."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_async_client = AsyncMock()
        mock_async_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_async_client
        
        # First health check
        await client.health_check()
        first_call_count = mock_async_client.get.call_count
        
        # Immediate second health check (should use cache)
        result = await client.health_check()
        
        # Assert
        assert result is True
        assert mock_async_client.get.call_count == first_call_count  # No additional calls
    
    @pytest.mark.asyncio
    async def test_health_check_connection_error(self, client, mock_settings):
        """Test health check with connection error."""
        # Arrange
        mock_async_client = AsyncMock()
        mock_async_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        client._client = mock_async_client
        
        # Act
        result = await client.health_check()
        
        # Assert
        assert result is False
        assert client._is_healthy is False
    
    def test_circuit_breaker_closed(self, client):
        """Test circuit breaker in closed state."""
        # Initially closed
        assert client._is_circuit_breaker_open() is False
        
        # After some failures (below threshold)
        client._circuit_breaker_failures = 3
        assert client._is_circuit_breaker_open() is False
    
    def test_circuit_breaker_open(self, client):
        """Test circuit breaker in open state."""
        # Trip the circuit breaker
        client._trip_circuit_breaker()
        
        # Should be open
        assert client._is_circuit_breaker_open() is True
        assert client._circuit_breaker_open_until is not None
    
    def test_circuit_breaker_recovery(self, client):
        """Test circuit breaker recovery after timeout."""
        # Trip the circuit breaker
        client._circuit_breaker_recovery_timeout = 1  # 1 second for testing
        client._trip_circuit_breaker()
        
        # Manually set recovery time to past
        client._circuit_breaker_open_until = datetime.now() - timedelta(seconds=1)
        
        # Should be closed again
        assert client._is_circuit_breaker_open() is False
        assert client._circuit_breaker_failures == 0
    
    @pytest.mark.asyncio
    async def test_classify_success(self, client, mock_settings):
        """Test successful classification request."""
        # Arrange
        text = "Write a Python function"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[{
            "intent": "code_generation",
            "confidence": 0.95,
            "complexity": {"level": "moderate"},
            "metadata": {"inference_time_ms": 100}
        }])
        
        mock_async_client = AsyncMock()
        mock_async_client.post = AsyncMock(return_value=mock_response)
        client._client = mock_async_client
        
        # Act
        result = await client.classify(text)
        
        # Assert
        assert result["intent"] == "code_generation"
        assert result["confidence"] == 0.95
        assert "client_inference_time_ms" in result["metadata"]
        assert result["metadata"]["retry_attempts"] == 0
        
        # Verify request payload
        mock_async_client.post.assert_called_once()
        call_args = mock_async_client.post.call_args
        assert call_args[0][0] == mock_settings.TORCHSERVE_URL
        assert call_args[1]["json"]["text"] == text
    
    @pytest.mark.asyncio
    async def test_classify_circuit_breaker_open(self, client):
        """Test classification when circuit breaker is open."""
        # Arrange
        client._trip_circuit_breaker()
        
        # Act & Assert
        with pytest.raises(TorchServeConnectionError, match="Circuit breaker is open"):
            await client.classify("Test text")
    
    @pytest.mark.asyncio
    async def test_classify_validation_error(self, client):
        """Test classification with invalid input."""
        # Act & Assert
        with pytest.raises(ValueError, match="non-empty string"):
            await client.classify("")
        
        with pytest.raises(ValueError, match="non-empty string"):
            await client.classify(None)
    
    @pytest.mark.asyncio
    async def test_classify_text_truncation(self, client, mock_settings):
        """Test that long text is truncated."""
        # Arrange
        long_text = "a" * 10000  # Very long text
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[{"intent": "test"}])
        
        mock_async_client = AsyncMock()
        mock_async_client.post = AsyncMock(return_value=mock_response)
        client._client = mock_async_client
        
        # Act
        await client.classify(long_text)
        
        # Assert
        call_args = mock_async_client.post.call_args
        sent_text = call_args[1]["json"]["text"]
        assert len(sent_text) <= mock_settings.MODEL_MAX_LENGTH * 4
    
    @pytest.mark.asyncio
    async def test_classify_retry_logic(self, client, mock_settings):
        """Test retry logic with exponential backoff."""
        # Arrange
        mock_settings.TORCHSERVE_MAX_RETRIES = 3
        
        # First two attempts fail, third succeeds
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json = MagicMock(return_value=[{"intent": "test"}])
        
        mock_async_client = AsyncMock()
        mock_async_client.post = AsyncMock(side_effect=[
            httpx.ConnectError("Connection failed"),
            httpx.TimeoutException("Timeout"),
            mock_response_success
        ])
        client._client = mock_async_client
        
        # Act
        result = await client.classify("Test text")
        
        # Assert
        assert result["intent"] == "test"
        assert result["metadata"]["retry_attempts"] == 2
        assert mock_async_client.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_classify_all_retries_exhausted(self, client, mock_settings):
        """Test when all retries are exhausted."""
        # Arrange
        mock_settings.TORCHSERVE_MAX_RETRIES = 2
        
        mock_async_client = AsyncMock()
        mock_async_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        client._client = mock_async_client
        
        # Act & Assert
        with pytest.raises(TorchServeConnectionError):
            await client.classify("Test text")
        
        assert mock_async_client.post.call_count == mock_settings.TORCHSERVE_MAX_RETRIES
    
    @pytest.mark.asyncio
    async def test_classify_circuit_breaker_trip(self, client, mock_settings):
        """Test circuit breaker trips after threshold failures."""
        # Arrange
        mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 3
        
        mock_async_client = AsyncMock()
        mock_async_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        client._client = mock_async_client
        
        # Make requests until circuit breaker trips
        for i in range(mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD):
            try:
                await client.classify(f"Test {i}")
            except TorchServeConnectionError:
                pass
        
        # Assert circuit breaker is now open
        assert client._is_circuit_breaker_open() is True
    
    @pytest.mark.asyncio
    async def test_batch_classify_success(self, client, mock_settings):
        """Test successful batch classification."""
        # Arrange
        texts = ["Text 1", "Text 2", "Text 3"]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[
            {"intent": "intent1", "confidence": 0.9},
            {"intent": "intent2", "confidence": 0.8},
            {"intent": "intent3", "confidence": 0.7}
        ])
        
        mock_async_client = AsyncMock()
        mock_async_client.post = AsyncMock(return_value=mock_response)
        client._client = mock_async_client
        
        # Act
        results = await client.batch_classify(texts)
        
        # Assert
        assert len(results) == 3
        assert results[0]["intent"] == "intent1"
        assert results[1]["intent"] == "intent2"
        assert results[2]["intent"] == "intent3"
        
        # Verify metadata added
        for i, result in enumerate(results):
            assert result["metadata"]["batch_index"] == i
            assert result["metadata"]["batch_size"] == 3
            assert "batch_inference_time_ms" in result["metadata"]
    
    @pytest.mark.asyncio
    async def test_batch_classify_size_limit(self, client, mock_settings):
        """Test batch size limiting."""
        # Arrange
        mock_settings.MODEL_BATCH_SIZE = 5
        texts = ["Text " + str(i) for i in range(10)]
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[{"intent": "test"} for _ in range(5)])
        
        mock_async_client = AsyncMock()
        mock_async_client.post = AsyncMock(return_value=mock_response)
        client._client = mock_async_client
        
        # Act
        results = await client.batch_classify(texts)
        
        # Assert
        assert len(results) == 5  # Limited to max batch size
        
        # Verify only 5 texts were sent
        call_args = mock_async_client.post.call_args
        sent_payload = call_args[1]["json"]
        assert len(sent_payload) == 5
    
    @pytest.mark.asyncio
    async def test_batch_classify_validation_error(self, client):
        """Test batch classification with invalid input."""
        # Act & Assert
        with pytest.raises(ValueError, match="non-empty list"):
            await client.batch_classify([])
        
        with pytest.raises(ValueError, match="non-empty list"):
            await client.batch_classify(None)
    
    def test_is_healthy(self, client):
        """Test is_healthy method."""
        # Initially not healthy
        assert client.is_healthy() is False
        
        # Set healthy
        client._is_healthy = True
        assert client.is_healthy() is True
        
        # Healthy but circuit breaker open
        client._trip_circuit_breaker()
        assert client.is_healthy() is False
    
    @pytest.mark.asyncio
    async def test_get_model_info(self, client):
        """Test getting model information."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "modelName": "intent-classifier",
            "modelVersion": "1.0",
            "status": "READY"
        })
        
        mock_async_client = AsyncMock()
        mock_async_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_async_client
        client.inference_url = "http://localhost:8080/predictions/intent"
        
        # Act
        info = await client.get_model_info()
        
        # Assert
        assert info["modelName"] == "intent-classifier"
        assert info["modelVersion"] == "1.0"
        assert info["status"] == "READY"
        
        # Verify management API URL
        expected_url = "http://localhost:8081/models/intent"
        mock_async_client.get.assert_called_once_with(expected_url)
    
    @pytest.mark.asyncio
    async def test_get_model_info_error(self, client):
        """Test get_model_info error handling."""
        # Arrange
        mock_async_client = AsyncMock()
        mock_async_client.get = AsyncMock(side_effect=Exception("Network error"))
        client._client = mock_async_client
        
        # Act
        info = await client.get_model_info()
        
        # Assert
        assert info == {}  # Returns empty dict on error
    
    @pytest.mark.asyncio
    async def test_context_manager(self, client, mock_settings):
        """Test using client as context manager."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_async_client = AsyncMock()
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_async_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_async_client
            
            # Act
            async with client:
                assert client._client is not None
            
            # Assert
            mock_async_client.aclose.assert_called_once()


class TestGlobalClient:
    """Test global client management functions."""
    
    @pytest.mark.asyncio
    async def test_get_torchserve_client(self):
        """Test getting global client instance."""
        # Clear any existing global client
        import app.models.torchserve_client
        app.models.torchserve_client._torchserve_client = None
        
        with patch.object(TorchServeClient, 'connect', new_callable=AsyncMock):
            # Act
            client1 = await get_torchserve_client()
            client2 = await get_torchserve_client()
            
            # Assert - should return same instance
            assert client1 is client2
            assert client1 is not None
    
    @pytest.mark.asyncio
    async def test_close_torchserve_client(self):
        """Test closing global client."""
        # Setup
        import app.models.torchserve_client
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        app.models.torchserve_client._torchserve_client = mock_client
        
        # Act
        await close_torchserve_client()
        
        # Assert
        mock_client.close.assert_called_once()
        assert app.models.torchserve_client._torchserve_client is None