"""Integration tests for circuit breaker functionality."""

import pytest
from unittest.mock import patch, AsyncMock
import asyncio
from datetime import datetime, timedelta

from app.models.torchserve_client import TorchServeClient, TorchServeConnectionError
import httpx


class TestCircuitBreaker:
    """Test circuit breaker pattern implementation."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self):
        """Test that circuit breaker opens after reaching failure threshold."""
        # Arrange
        client = TorchServeClient()
        
        with patch('app.models.torchserve_client.settings') as mock_settings:
            mock_settings.TORCHSERVE_URL = "http://localhost:8080/predictions/test"
            mock_settings.TORCHSERVE_TIMEOUT = 1
            mock_settings.TORCHSERVE_MAX_RETRIES = 1
            mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 3
            mock_settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 5
            mock_settings.MODEL_MAX_LENGTH = 512
            
            # Mock HTTP client to always fail
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
            client._client = mock_http_client
            
            # Act - Make requests until circuit breaker trips
            failures = 0
            for i in range(mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD):
                try:
                    await client.classify(f"Test {i}")
                except TorchServeConnectionError:
                    failures += 1
            
            # Assert
            assert failures == mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD
            assert client._is_circuit_breaker_open() is True
            
            # Further requests should fail immediately
            with pytest.raises(TorchServeConnectionError, match="Circuit breaker is open"):
                await client.classify("This should fail immediately")
            
            # Verify no actual HTTP call was made
            call_count_before = mock_http_client.post.call_count
            try:
                await client.classify("Another request")
            except TorchServeConnectionError:
                pass
            assert mock_http_client.post.call_count == call_count_before
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout period."""
        # Arrange
        client = TorchServeClient()
        
        with patch('app.models.torchserve_client.settings') as mock_settings:
            mock_settings.TORCHSERVE_URL = "http://localhost:8080/predictions/test"
            mock_settings.TORCHSERVE_TIMEOUT = 1
            mock_settings.TORCHSERVE_MAX_RETRIES = 1
            mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 2
            mock_settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 1  # 1 second for faster testing
            mock_settings.MODEL_MAX_LENGTH = 512
            
            # Mock HTTP client
            mock_http_client = AsyncMock()
            client._client = mock_http_client
            
            # First, trip the circuit breaker
            client._circuit_breaker_failures = mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD
            client._trip_circuit_breaker()
            
            assert client._is_circuit_breaker_open() is True
            
            # Wait for recovery timeout
            await asyncio.sleep(1.1)
            
            # Circuit breaker should be closed now
            assert client._is_circuit_breaker_open() is False
            assert client._circuit_breaker_failures == 0
            
            # Now setup successful response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = lambda: [{"intent": "test", "confidence": 0.9}]
            mock_http_client.post = AsyncMock(return_value=mock_response)
            
            # Should be able to make requests again
            result = await client.classify("Test after recovery")
            assert result["intent"] == "test"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_state(self):
        """Test circuit breaker half-open state behavior."""
        # Arrange
        client = TorchServeClient()
        
        with patch('app.models.torchserve_client.settings') as mock_settings:
            mock_settings.TORCHSERVE_URL = "http://localhost:8080/predictions/test"
            mock_settings.TORCHSERVE_TIMEOUT = 1
            mock_settings.TORCHSERVE_MAX_RETRIES = 1
            mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 2
            mock_settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 1
            mock_settings.MODEL_MAX_LENGTH = 512
            
            # Mock HTTP client
            mock_http_client = AsyncMock()
            client._client = mock_http_client
            
            # Trip the circuit breaker
            client._trip_circuit_breaker()
            
            # Wait for recovery timeout
            await asyncio.sleep(1.1)
            
            # First request after recovery fails (half-open test)
            mock_http_client.post = AsyncMock(side_effect=httpx.ConnectError("Still failing"))
            
            with pytest.raises(TorchServeConnectionError):
                await client.classify("Test in half-open state")
            
            # Circuit breaker should be open again
            assert client._is_circuit_breaker_open() is True
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_circuit_breaker_success_resets_counter(self):
        """Test that successful requests reset the failure counter."""
        # Arrange
        client = TorchServeClient()
        
        with patch('app.models.torchserve_client.settings') as mock_settings:
            mock_settings.TORCHSERVE_URL = "http://localhost:8080/predictions/test"
            mock_settings.TORCHSERVE_TIMEOUT = 1
            mock_settings.TORCHSERVE_MAX_RETRIES = 1
            mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 3
            mock_settings.MODEL_MAX_LENGTH = 512
            
            # Mock HTTP client
            mock_http_client = AsyncMock()
            client._client = mock_http_client
            
            # First, accumulate some failures (but not enough to trip)
            mock_http_client.post = AsyncMock(side_effect=httpx.ConnectError("Failed"))
            
            try:
                await client.classify("Test 1")
            except TorchServeConnectionError:
                pass
            
            assert client._circuit_breaker_failures == 1
            
            # Now a successful request
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = lambda: [{"intent": "test", "confidence": 0.9}]
            mock_http_client.post = AsyncMock(return_value=mock_response)
            
            result = await client.classify("Test 2")
            
            # Assert
            assert result["intent"] == "test"
            assert client._circuit_breaker_failures == 0  # Reset to 0
            assert client._is_circuit_breaker_open() is False
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_circuit_breaker_batch_requests(self):
        """Test circuit breaker behavior with batch requests."""
        # Arrange
        client = TorchServeClient()
        
        with patch('app.models.torchserve_client.settings') as mock_settings:
            mock_settings.TORCHSERVE_URL = "http://localhost:8080/predictions/test"
            mock_settings.TORCHSERVE_TIMEOUT = 1
            mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 2
            mock_settings.MODEL_MAX_LENGTH = 512
            mock_settings.MODEL_BATCH_SIZE = 10
            
            # Trip the circuit breaker
            client._trip_circuit_breaker()
            
            # Act & Assert
            with pytest.raises(TorchServeConnectionError, match="Circuit breaker is open"):
                await client.batch_classify(["Text 1", "Text 2", "Text 3"])
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_circuit_breaker_metrics(self):
        """Test that circuit breaker state is reflected in metrics."""
        # Arrange
        client = TorchServeClient()
        
        with patch('app.models.torchserve_client.settings') as mock_settings, \
             patch('app.models.torchserve_client.torchserve_requests') as mock_requests_metric:
            
            mock_settings.TORCHSERVE_URL = "http://localhost:8080/predictions/test"
            mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 1
            mock_settings.MODEL_MAX_LENGTH = 512
            
            # Trip the circuit breaker
            client._trip_circuit_breaker()
            
            # Act
            try:
                await client.classify("Test")
            except TorchServeConnectionError:
                pass
            
            # Assert
            mock_requests_metric.labels.assert_called_with(
                method="classify",
                status="circuit_breaker_open"
            )
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_is_healthy_with_circuit_breaker(self):
        """Test is_healthy method considers circuit breaker state."""
        # Arrange
        client = TorchServeClient()
        
        # Initially not healthy (not connected)
        assert client.is_healthy() is False
        
        # Set as healthy
        client._is_healthy = True
        assert client.is_healthy() is True
        
        # Trip circuit breaker
        client._trip_circuit_breaker()
        assert client.is_healthy() is False  # Not healthy when circuit breaker is open
        
        # Reset circuit breaker
        client._circuit_breaker_open_until = None
        assert client.is_healthy() is True
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_circuit_breaker_concurrent_requests(self):
        """Test circuit breaker behavior under concurrent load."""
        # Arrange
        client = TorchServeClient()
        
        with patch('app.models.torchserve_client.settings') as mock_settings:
            mock_settings.TORCHSERVE_URL = "http://localhost:8080/predictions/test"
            mock_settings.TORCHSERVE_TIMEOUT = 1
            mock_settings.TORCHSERVE_MAX_RETRIES = 1
            mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
            mock_settings.MODEL_MAX_LENGTH = 512
            
            # Mock HTTP client to fail
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(side_effect=httpx.ConnectError("Failed"))
            client._client = mock_http_client
            
            # Act - Send concurrent requests
            async def make_request(i):
                try:
                    await client.classify(f"Test {i}")
                    return "success"
                except TorchServeConnectionError as e:
                    if "Circuit breaker is open" in str(e):
                        return "circuit_open"
                    return "connection_error"
            
            tasks = [make_request(i) for i in range(10)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Assert
            # Some requests should have connection errors, some circuit breaker errors
            assert "connection_error" in results
            assert "circuit_open" in results
            assert client._is_circuit_breaker_open() is True
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_circuit_breaker_gradual_recovery(self):
        """Test gradual recovery pattern after circuit breaker opens."""
        # Arrange
        client = TorchServeClient()
        
        with patch('app.models.torchserve_client.settings') as mock_settings:
            mock_settings.TORCHSERVE_URL = "http://localhost:8080/predictions/test"
            mock_settings.TORCHSERVE_TIMEOUT = 1
            mock_settings.TORCHSERVE_MAX_RETRIES = 1
            mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 2
            mock_settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 1
            mock_settings.MODEL_MAX_LENGTH = 512
            
            # Mock HTTP client
            mock_http_client = AsyncMock()
            client._client = mock_http_client
            
            # Trip the circuit breaker
            client._trip_circuit_breaker()
            
            # Wait for recovery
            await asyncio.sleep(1.1)
            
            # Simulate gradual recovery - first few requests fail, then succeed
            request_count = 0
            
            async def mock_post(*args, **kwargs):
                nonlocal request_count
                request_count += 1
                
                if request_count <= 2:
                    raise httpx.ConnectError("Still recovering")
                
                # Success after a few attempts
                response = AsyncMock()
                response.status_code = 200
                response.json = lambda: [{"intent": "test", "confidence": 0.9}]
                return response
            
            mock_http_client.post = mock_post
            
            # First request fails, circuit breaker opens again
            with pytest.raises(TorchServeConnectionError):
                await client.classify("Test 1")
            
            assert client._is_circuit_breaker_open() is True
            
            # Wait and try again
            await asyncio.sleep(1.1)
            
            # This time it should succeed
            result = await client.classify("Test 2")
            assert result["intent"] == "test"
            assert client._circuit_breaker_failures == 0