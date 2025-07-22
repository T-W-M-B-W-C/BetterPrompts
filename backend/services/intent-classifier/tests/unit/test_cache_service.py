"""Unit tests for cache service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import hashlib

from app.services.cache import CacheService


class TestCacheService:
    """Test suite for cache service."""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        client = AsyncMock()
        client.get = AsyncMock(return_value=None)
        client.setex = AsyncMock(return_value=True)
        client.delete = AsyncMock(return_value=True)
        client.scan = AsyncMock(return_value=(0, []))
        client.close = AsyncMock()
        return client
    
    @pytest.fixture
    async def cache_service(self, mock_redis_client):
        """Create a cache service with mocked Redis client."""
        service = CacheService()
        service.redis_client = mock_redis_client
        return service
    
    @pytest.mark.asyncio
    async def test_context_manager(self, mock_redis_client):
        """Test cache service as context manager."""
        with patch('redis.asyncio.from_url', return_value=mock_redis_client):
            async with CacheService() as service:
                assert service.redis_client is not None
            
            # Verify close was called
            mock_redis_client.close.assert_called_once()
    
    def test_get_cache_key(self):
        """Test cache key generation."""
        service = CacheService()
        text = "Test input text"
        
        # Generate expected hash
        expected_hash = hashlib.sha256(text.encode()).hexdigest()
        expected_key = f"intent_classifier:{expected_hash}"
        
        # Test
        key = service._get_cache_key(text)
        assert key == expected_key
    
    def test_get_cache_key_consistency(self):
        """Test cache key generation is consistent."""
        service = CacheService()
        text = "Consistent text"
        
        # Generate key multiple times
        key1 = service._get_cache_key(text)
        key2 = service._get_cache_key(text)
        key3 = service._get_cache_key(text)
        
        # All keys should be identical
        assert key1 == key2 == key3
    
    def test_get_cache_key_different_texts(self):
        """Test cache keys are different for different texts."""
        service = CacheService()
        
        key1 = service._get_cache_key("Text 1")
        key2 = service._get_cache_key("Text 2")
        
        assert key1 != key2
    
    @pytest.mark.asyncio
    async def test_get_intent_cache_hit(self, cache_service, mock_redis_client):
        """Test getting cached intent (cache hit)."""
        # Arrange
        cached_data = {
            "intent": "cached_intent",
            "confidence": 0.95,
            "complexity": "moderate",
            "suggested_techniques": ["chain_of_thought"]
        }
        mock_redis_client.get.return_value = json.dumps(cached_data)
        
        # Act
        result = await cache_service.get_intent("test text")
        
        # Assert
        assert result == cached_data
        mock_redis_client.get.assert_called_once()
        
        # Verify correct key was used
        expected_key = cache_service._get_cache_key("test text")
        mock_redis_client.get.assert_called_with(expected_key)
    
    @pytest.mark.asyncio
    async def test_get_intent_cache_miss(self, cache_service, mock_redis_client):
        """Test getting cached intent (cache miss)."""
        # Arrange
        mock_redis_client.get.return_value = None
        
        # Act
        result = await cache_service.get_intent("test text")
        
        # Assert
        assert result is None
        mock_redis_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_intent_no_client(self):
        """Test get_intent when Redis client is not available."""
        # Arrange
        service = CacheService()
        service.redis_client = None
        
        # Act
        result = await service.get_intent("test text")
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_intent_error_handling(self, cache_service, mock_redis_client):
        """Test error handling in get_intent."""
        # Arrange
        mock_redis_client.get.side_effect = Exception("Redis connection error")
        
        # Act
        result = await cache_service.get_intent("test text")
        
        # Assert
        assert result is None  # Returns None on error
    
    @pytest.mark.asyncio
    async def test_set_intent_success(self, cache_service, mock_redis_client):
        """Test successfully caching intent result."""
        # Arrange
        text = "test text"
        result = {
            "intent": "test_intent",
            "confidence": 0.9,
            "complexity": "simple",
            "suggested_techniques": ["few_shot"]
        }
        
        with patch('app.services.cache.settings.CACHE_TTL', 3600):
            # Act
            success = await cache_service.set_intent(text, result)
            
            # Assert
            assert success is True
            mock_redis_client.setex.assert_called_once()
            
            # Verify arguments
            expected_key = cache_service._get_cache_key(text)
            call_args = mock_redis_client.setex.call_args
            assert call_args[0][0] == expected_key
            assert call_args[0][1] == 3600
            assert json.loads(call_args[0][2]) == result
    
    @pytest.mark.asyncio
    async def test_set_intent_custom_ttl(self, cache_service, mock_redis_client):
        """Test caching with custom TTL."""
        # Arrange
        text = "test text"
        result = {"intent": "test"}
        custom_ttl = 7200
        
        # Act
        success = await cache_service.set_intent(text, result, ttl=custom_ttl)
        
        # Assert
        assert success is True
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][1] == custom_ttl
    
    @pytest.mark.asyncio
    async def test_set_intent_no_client(self):
        """Test set_intent when Redis client is not available."""
        # Arrange
        service = CacheService()
        service.redis_client = None
        
        # Act
        success = await service.set_intent("text", {"intent": "test"})
        
        # Assert
        assert success is False
    
    @pytest.mark.asyncio
    async def test_set_intent_error_handling(self, cache_service, mock_redis_client):
        """Test error handling in set_intent."""
        # Arrange
        mock_redis_client.setex.side_effect = Exception("Redis write error")
        
        # Act
        success = await cache_service.set_intent("text", {"intent": "test"})
        
        # Assert
        assert success is False
    
    @pytest.mark.asyncio
    async def test_delete_intent_success(self, cache_service, mock_redis_client):
        """Test successfully deleting cached intent."""
        # Arrange
        text = "test text"
        
        # Act
        success = await cache_service.delete_intent(text)
        
        # Assert
        assert success is True
        expected_key = cache_service._get_cache_key(text)
        mock_redis_client.delete.assert_called_once_with(expected_key)
    
    @pytest.mark.asyncio
    async def test_delete_intent_no_client(self):
        """Test delete_intent when Redis client is not available."""
        # Arrange
        service = CacheService()
        service.redis_client = None
        
        # Act
        success = await service.delete_intent("text")
        
        # Assert
        assert success is False
    
    @pytest.mark.asyncio
    async def test_delete_intent_error_handling(self, cache_service, mock_redis_client):
        """Test error handling in delete_intent."""
        # Arrange
        mock_redis_client.delete.side_effect = Exception("Redis delete error")
        
        # Act
        success = await cache_service.delete_intent("text")
        
        # Assert
        assert success is False
    
    @pytest.mark.asyncio
    async def test_clear_all_success(self, cache_service, mock_redis_client):
        """Test clearing all cached results."""
        # Arrange
        # Simulate paginated scan results
        mock_redis_client.scan.side_effect = [
            (100, ["intent_classifier:key1", "intent_classifier:key2"]),
            (0, ["intent_classifier:key3"])  # cursor 0 means end
        ]
        
        # Act
        success = await cache_service.clear_all()
        
        # Assert
        assert success is True
        assert mock_redis_client.scan.call_count == 2
        assert mock_redis_client.delete.call_count == 2
        
        # Verify correct keys were deleted
        delete_calls = mock_redis_client.delete.call_args_list
        assert delete_calls[0][0] == ("intent_classifier:key1", "intent_classifier:key2")
        assert delete_calls[1][0] == ("intent_classifier:key3",)
    
    @pytest.mark.asyncio
    async def test_clear_all_no_keys(self, cache_service, mock_redis_client):
        """Test clearing when no keys exist."""
        # Arrange
        mock_redis_client.scan.return_value = (0, [])
        
        # Act
        success = await cache_service.clear_all()
        
        # Assert
        assert success is True
        mock_redis_client.scan.assert_called_once()
        mock_redis_client.delete.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_clear_all_no_client(self):
        """Test clear_all when Redis client is not available."""
        # Arrange
        service = CacheService()
        service.redis_client = None
        
        # Act
        success = await service.clear_all()
        
        # Assert
        assert success is False
    
    @pytest.mark.asyncio
    async def test_clear_all_error_handling(self, cache_service, mock_redis_client):
        """Test error handling in clear_all."""
        # Arrange
        mock_redis_client.scan.side_effect = Exception("Redis scan error")
        
        # Act
        success = await cache_service.clear_all()
        
        # Assert
        assert success is False
    
    @pytest.mark.asyncio
    async def test_cache_service_with_settings(self):
        """Test cache service initialization with settings."""
        # Arrange
        mock_redis_client = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        
        with patch('app.services.cache.settings', mock_settings), \
             patch('redis.asyncio.from_url', return_value=mock_redis_client) as mock_from_url:
            
            # Act
            async with CacheService() as service:
                pass
            
            # Assert
            mock_from_url.assert_called_once_with(
                "redis://localhost:6379/0",
                encoding="utf-8",
                decode_responses=True
            )
    
    @pytest.mark.asyncio
    async def test_dependency_injection(self):
        """Test get_cache_service dependency injection."""
        from app.services.cache import get_cache_service
        
        mock_redis_client = AsyncMock()
        with patch('redis.asyncio.from_url', return_value=mock_redis_client):
            # Act
            async for service in get_cache_service():
                # Assert
                assert isinstance(service, CacheService)
                assert service.redis_client is not None
    
    @pytest.mark.asyncio
    async def test_cache_key_prefix(self):
        """Test that cache keys use correct prefix."""
        service = CacheService()
        
        # Test various inputs
        test_cases = [
            "short text",
            "A much longer text that might be used for classification",
            "Text with special characters: @#$%^&*()",
            "Multi-line\ntext\nwith\nbreaks"
        ]
        
        for text in test_cases:
            key = service._get_cache_key(text)
            assert key.startswith("intent_classifier:")
            # Verify hash part is 64 characters (SHA256)
            hash_part = key.replace("intent_classifier:", "")
            assert len(hash_part) == 64
            # Verify hash contains only hex characters
            assert all(c in "0123456789abcdef" for c in hash_part)