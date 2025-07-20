"""
Redis service for caching and session management in Python services
"""
import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import timedelta
import logging

import redis
from redis import ConnectionPool
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Redis service for caching operations"""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        db: int = 0,
        key_prefix: str = "",
        default_ttl: int = 300,
        pool_size: int = 50,
        decode_responses: bool = False
    ):
        """
        Initialize Redis service
        
        Args:
            host: Redis host
            port: Redis port
            password: Redis password
            db: Redis database number
            key_prefix: Prefix for all keys
            default_ttl: Default TTL in seconds
            pool_size: Connection pool size
            decode_responses: Whether to decode responses to strings
        """
        self.host = host or settings.REDIS_HOST
        self.port = port or settings.REDIS_PORT
        self.password = password or settings.REDIS_PASSWORD
        self.db = db
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        
        # Create connection pool
        self.pool = ConnectionPool(
            host=self.host,
            port=self.port,
            password=self.password,
            db=self.db,
            max_connections=pool_size,
            decode_responses=decode_responses,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        self.client = redis.Redis(connection_pool=self.pool)
        self._test_connection()
    
    def _test_connection(self):
        """Test Redis connection"""
        try:
            self.client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _build_key(self, namespace: str, key: str) -> str:
        """Build a namespaced key"""
        if self.key_prefix:
            return f"{self.key_prefix}:{namespace}:{key}"
        return f"{namespace}:{key}"
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize a value for storage"""
        if isinstance(value, (str, bytes)):
            return value if isinstance(value, bytes) else value.encode()
        return pickle.dumps(value)
    
    def _deserialize(self, value: Optional[bytes]) -> Any:
        """Deserialize a stored value"""
        if value is None:
            return None
        try:
            # Try to decode as string first
            return value.decode() if isinstance(value, bytes) else value
        except (UnicodeDecodeError, AttributeError):
            # Fall back to pickle
            try:
                return pickle.loads(value)
            except Exception:
                return value
    
    # Session Management
    
    def set_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Store a session"""
        key = self._build_key("session", session_id)
        ttl = ttl or 86400  # 24 hours default
        
        try:
            return self.client.setex(
                key,
                ttl,
                json.dumps(data)
            )
        except Exception as e:
            logger.error(f"Failed to set session {session_id}: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a session"""
        key = self._build_key("session", session_id)
        
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        key = self._build_key("session", session_id)
        return bool(self.client.delete(key))
    
    def refresh_session(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """Refresh session TTL"""
        key = self._build_key("session", session_id)
        ttl = ttl or 86400  # 24 hours default
        return self.client.expire(key, ttl)
    
    # API Response Caching
    
    def cache_api_response(
        self,
        endpoint: str,
        params: str,
        response: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache an API response"""
        key = self._build_key("api:response", f"{endpoint}:{params}")
        ttl = ttl or 300  # 5 minutes default
        
        try:
            return self.client.setex(
                key,
                ttl,
                json.dumps(response) if not isinstance(response, str) else response
            )
        except Exception as e:
            logger.error(f"Failed to cache API response: {e}")
            return False
    
    def get_cached_api_response(
        self,
        endpoint: str,
        params: str
    ) -> Optional[Any]:
        """Get cached API response"""
        key = self._build_key("api:response", f"{endpoint}:{params}")
        
        try:
            data = self.client.get(key)
            if data:
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    return data.decode() if isinstance(data, bytes) else data
            return None
        except Exception as e:
            logger.error(f"Failed to get cached API response: {e}")
            return None
    
    # ML Model Caching
    
    def cache_prediction(
        self,
        model_name: str,
        input_hash: str,
        prediction: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache ML model prediction"""
        key = self._build_key(f"ml:{model_name}", input_hash)
        ttl = ttl or 3600  # 1 hour default
        
        try:
            return self.client.setex(
                key,
                ttl,
                self._serialize(prediction)
            )
        except Exception as e:
            logger.error(f"Failed to cache prediction: {e}")
            return False
    
    def get_cached_prediction(
        self,
        model_name: str,
        input_hash: str
    ) -> Optional[Any]:
        """Get cached ML model prediction"""
        key = self._build_key(f"ml:{model_name}", input_hash)
        
        try:
            data = self.client.get(key)
            return self._deserialize(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached prediction: {e}")
            return None
    
    # Rate Limiting
    
    def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window: int = 3600
    ) -> tuple[bool, int]:
        """
        Check if request is within rate limits
        
        Returns:
            Tuple of (allowed, current_count)
        """
        key = self._build_key("ratelimit", identifier)
        
        try:
            pipeline = self.client.pipeline()
            pipeline.incr(key)
            pipeline.expire(key, window)
            results = pipeline.execute()
            
            current_count = results[0]
            
            return current_count <= limit, current_count
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Allow request on error
            return True, 0
    
    def get_rate_limit_info(self, identifier: str) -> Dict[str, Any]:
        """Get rate limit information"""
        key = self._build_key("ratelimit", identifier)
        
        try:
            pipeline = self.client.pipeline()
            pipeline.get(key)
            pipeline.ttl(key)
            results = pipeline.execute()
            
            count = int(results[0]) if results[0] else 0
            ttl = results[1] if results[1] > 0 else 0
            
            return {
                "count": count,
                "ttl": ttl
            }
        except Exception as e:
            logger.error(f"Failed to get rate limit info: {e}")
            return {"count": 0, "ttl": 0}
    
    # Generic Cache Methods
    
    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set a value with optional TTL"""
        full_key = self._build_key(namespace, key)
        ttl = ttl or self.default_ttl
        
        try:
            return self.client.setex(
                full_key,
                ttl,
                self._serialize(value)
            )
        except Exception as e:
            logger.error(f"Failed to set {full_key}: {e}")
            return False
    
    def get(self, namespace: str, key: str) -> Optional[Any]:
        """Get a value"""
        full_key = self._build_key(namespace, key)
        
        try:
            data = self.client.get(full_key)
            return self._deserialize(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get {full_key}: {e}")
            return None
    
    def delete(self, namespace: str, key: str) -> bool:
        """Delete a key"""
        full_key = self._build_key(namespace, key)
        return bool(self.client.delete(full_key))
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        count = 0
        try:
            # Use SCAN to avoid blocking
            for key in self.client.scan_iter(pattern, count=100):
                if self.client.delete(key):
                    count += 1
            return count
        except Exception as e:
            logger.error(f"Failed to delete pattern {pattern}: {e}")
            return count
    
    def exists(self, namespace: str, key: str) -> bool:
        """Check if a key exists"""
        full_key = self._build_key(namespace, key)
        return bool(self.client.exists(full_key))
    
    def set_nx(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set a key only if it doesn't exist"""
        full_key = self._build_key(namespace, key)
        
        try:
            return self.client.set(
                full_key,
                self._serialize(value),
                nx=True,
                ex=ttl or self.default_ttl
            )
        except Exception as e:
            logger.error(f"Failed to setnx {full_key}: {e}")
            return False
    
    def increment(self, namespace: str, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        full_key = self._build_key(namespace, key)
        
        try:
            return self.client.incrby(full_key, amount)
        except Exception as e:
            logger.error(f"Failed to increment {full_key}: {e}")
            return 0
    
    def get_many(self, namespace: str, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values"""
        full_keys = [self._build_key(namespace, k) for k in keys]
        
        try:
            values = self.client.mget(full_keys)
            return {
                key: self._deserialize(value)
                for key, value in zip(keys, values)
                if value is not None
            }
        except Exception as e:
            logger.error(f"Failed to get many keys: {e}")
            return {}
    
    def set_many(
        self,
        namespace: str,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values"""
        ttl = ttl or self.default_ttl
        
        try:
            pipeline = self.client.pipeline()
            for key, value in mapping.items():
                full_key = self._build_key(namespace, key)
                pipeline.setex(full_key, ttl, self._serialize(value))
            
            results = pipeline.execute()
            return all(results)
        except Exception as e:
            logger.error(f"Failed to set many keys: {e}")
            return False
    
    # Health Check
    
    def health_check(self) -> bool:
        """Check Redis health"""
        try:
            return self.client.ping()
        except Exception:
            return False
    
    def close(self):
        """Close Redis connections"""
        try:
            self.pool.disconnect()
        except Exception:
            pass


# Global Redis instances for different use cases
_redis_instances: Dict[str, RedisService] = {}


def get_redis_service(
    name: str = "default",
    **kwargs
) -> RedisService:
    """
    Get or create a Redis service instance
    
    Args:
        name: Instance name
        **kwargs: Arguments for RedisService constructor
    
    Returns:
        RedisService instance
    """
    if name not in _redis_instances:
        _redis_instances[name] = RedisService(**kwargs)
    
    return _redis_instances[name]


# Convenience function for default Redis instance
def get_default_redis() -> RedisService:
    """Get the default Redis service instance"""
    return get_redis_service("default", key_prefix="intent-classifier")