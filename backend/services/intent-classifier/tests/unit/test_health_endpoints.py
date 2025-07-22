"""Unit tests for health check endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.api.v1.health import health_check, readiness_check, liveness_check


class TestHealthEndpoints:
    """Test suite for health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test basic health check endpoint."""
        # Act
        result = await health_check()
        
        # Assert
        assert result["status"] == "healthy"
        assert result["service"] == "intent-classifier"
    
    @pytest.mark.asyncio
    async def test_liveness_check_success(self):
        """Test liveness check endpoint."""
        # Act
        result = await liveness_check()
        
        # Assert
        assert result["status"] == "alive"
        assert result["service"] == "intent-classifier"
    
    @pytest.mark.asyncio
    async def test_readiness_check_all_healthy(self):
        """Test readiness check when all components are healthy."""
        # Arrange
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        
        mock_classifier = MagicMock()
        mock_classifier.is_initialized = MagicMock(return_value=True)
        mock_classifier.torchserve_client = AsyncMock()
        mock_classifier.torchserve_client.health_check = AsyncMock(return_value=True)
        
        async def mock_get_db():
            yield mock_db
        
        with patch('app.api.v1.health.get_db', mock_get_db), \
             patch('app.api.v1.health.classifier', mock_classifier), \
             patch('app.api.v1.health.settings.USE_TORCHSERVE', True):
            
            # Act
            result = await readiness_check()
            
            # Assert
            assert result["status"] == "ready"
            assert result["service"] == "intent-classifier"
            assert result["details"]["database"] == "healthy"
            assert result["details"]["model"] == "initialized"
            assert result["details"]["torchserve"] == "healthy"
            assert result["mode"] == "torchserve"
    
    @pytest.mark.asyncio
    async def test_readiness_check_database_unhealthy(self):
        """Test readiness check when database is unhealthy."""
        # Arrange
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("Database connection failed"))
        
        mock_classifier = MagicMock()
        mock_classifier.is_initialized = MagicMock(return_value=True)
        
        async def mock_get_db():
            yield mock_db
        
        with patch('app.api.v1.health.get_db', mock_get_db), \
             patch('app.api.v1.health.classifier', mock_classifier), \
             patch('app.api.v1.health.settings.USE_TORCHSERVE', False):
            
            # Act
            result = await readiness_check()
            
            # Assert
            assert result["status"] == "ready"  # Still ready if only DB is down
            assert result["details"]["database"] == "unhealthy"
            assert result["details"]["model"] == "initialized"
            assert result["mode"] == "local"
    
    @pytest.mark.asyncio
    async def test_readiness_check_model_not_initialized(self):
        """Test readiness check when model is not initialized."""
        # Arrange
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        
        mock_classifier = MagicMock()
        mock_classifier.is_initialized = MagicMock(return_value=False)
        
        async def mock_get_db():
            yield mock_db
        
        with patch('app.api.v1.health.get_db', mock_get_db), \
             patch('app.api.v1.health.classifier', mock_classifier):
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await readiness_check()
            
            assert exc_info.value.status_code == 503
            assert exc_info.value.detail == "Model not initialized"
    
    @pytest.mark.asyncio
    async def test_readiness_check_torchserve_unhealthy(self):
        """Test readiness check when TorchServe is unhealthy."""
        # Arrange
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        
        mock_classifier = MagicMock()
        mock_classifier.is_initialized = MagicMock(return_value=True)
        mock_classifier.torchserve_client = AsyncMock()
        mock_classifier.torchserve_client.health_check = AsyncMock(return_value=False)
        
        async def mock_get_db():
            yield mock_db
        
        with patch('app.api.v1.health.get_db', mock_get_db), \
             patch('app.api.v1.health.classifier', mock_classifier), \
             patch('app.api.v1.health.settings.USE_TORCHSERVE', True):
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await readiness_check()
            
            assert exc_info.value.status_code == 503
            assert exc_info.value.detail == "TorchServe not healthy"
    
    @pytest.mark.asyncio
    async def test_readiness_check_torchserve_error(self):
        """Test readiness check when TorchServe health check fails."""
        # Arrange
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        
        mock_classifier = MagicMock()
        mock_classifier.is_initialized = MagicMock(return_value=True)
        mock_classifier.torchserve_client = AsyncMock()
        mock_classifier.torchserve_client.health_check = AsyncMock(
            side_effect=Exception("Connection error")
        )
        
        async def mock_get_db():
            yield mock_db
        
        with patch('app.api.v1.health.get_db', mock_get_db), \
             patch('app.api.v1.health.classifier', mock_classifier), \
             patch('app.api.v1.health.settings.USE_TORCHSERVE', True):
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await readiness_check()
            
            assert exc_info.value.status_code == 503
            assert exc_info.value.detail == "TorchServe not available"
    
    @pytest.mark.asyncio
    async def test_readiness_check_local_mode(self):
        """Test readiness check in local mode (no TorchServe)."""
        # Arrange
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        
        mock_classifier = MagicMock()
        mock_classifier.is_initialized = MagicMock(return_value=True)
        mock_classifier.torchserve_client = None
        
        async def mock_get_db():
            yield mock_db
        
        with patch('app.api.v1.health.get_db', mock_get_db), \
             patch('app.api.v1.health.classifier', mock_classifier), \
             patch('app.api.v1.health.settings.USE_TORCHSERVE', False):
            
            # Act
            result = await readiness_check()
            
            # Assert
            assert result["status"] == "ready"
            assert result["details"]["database"] == "healthy"
            assert result["details"]["model"] == "initialized"
            assert result["details"]["torchserve"] == "not_applicable"
            assert result["mode"] == "local"
    
    @pytest.mark.asyncio
    async def test_readiness_check_unexpected_error(self):
        """Test readiness check handling of unexpected errors."""
        # Arrange
        with patch('app.api.v1.health.get_db', side_effect=Exception("Unexpected error")):
            
            # Act
            result = await readiness_check()
            
            # Assert
            assert result["status"] == "not_ready"
            assert result["service"] == "intent-classifier"
            assert "error" in result
            assert "Unexpected error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_readiness_check_details_structure(self):
        """Test the structure of readiness check details."""
        # Arrange
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        
        mock_classifier = MagicMock()
        mock_classifier.is_initialized = MagicMock(return_value=True)
        
        async def mock_get_db():
            yield mock_db
        
        with patch('app.api.v1.health.get_db', mock_get_db), \
             patch('app.api.v1.health.classifier', mock_classifier), \
             patch('app.api.v1.health.settings.USE_TORCHSERVE', False):
            
            # Act
            result = await readiness_check()
            
            # Assert
            assert "details" in result
            details = result["details"]
            assert "database" in details
            assert "model" in details
            assert "torchserve" in details
            
            # Verify all detail values are strings
            assert isinstance(details["database"], str)
            assert isinstance(details["model"], str)
            assert isinstance(details["torchserve"], str)