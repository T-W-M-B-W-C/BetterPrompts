"""Caching service for intent classification results."""

import json
from typing import Optional, Dict, Any
import hashlib

import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import setup_logging

logger = setup_logging()


class CacheService:
    """Redis-based caching service."""
    
    def __init__(self):
        """Initialize cache service."""
        self.redis_client = None
        self.prefix = "intent_classifier:"
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.redis_client:
            await self.redis_client.close()
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text."""
        # Use hash to handle long texts
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"{self.prefix}{text_hash}"
    
    async def get_intent(self, text: str) -> Optional[Dict[str, Any]]:
        """Get cached intent classification result."""
        if not self.redis_client:
            return None
        
        try:
            key = self._get_cache_key(text)
            result = await self.redis_client.get(key)
            
            if result:
                logger.debug(f"Cache hit for text hash: {key}")
                return json.loads(result)
            
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set_intent(
        self,
        text: str,
        result: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache intent classification result."""
        if not self.redis_client:
            return False
        
        try:
            key = self._get_cache_key(text)
            ttl = ttl or settings.CACHE_TTL
            
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(result),
            )
            
            logger.debug(f"Cached result for text hash: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete_intent(self, text: str) -> bool:
        """Delete cached intent classification result."""
        if not self.redis_client:
            return False
        
        try:
            key = self._get_cache_key(text)
            await self.redis_client.delete(key)
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all cached results."""
        if not self.redis_client:
            return False
        
        try:
            pattern = f"{self.prefix}*"
            cursor = 0
            
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor,
                    match=pattern,
                    count=100,
                )
                
                if keys:
                    await self.redis_client.delete(*keys)
                
                if cursor == 0:
                    break
            
            logger.info("Cleared all cached intent results")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False


# Dependency injection
async def get_cache_service():
    """Get cache service instance."""
    async with CacheService() as cache:
        yield cache