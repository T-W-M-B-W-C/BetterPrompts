"""Mock objects and utilities for intent-classifier tests."""

from typing import Dict, Any, List, Optional, Callable
from unittest.mock import AsyncMock, MagicMock, Mock
from datetime import datetime, timezone
import asyncio
import random
from contextlib import asynccontextmanager

from .constants import MOCK_TORCHSERVE_RESPONSES
from .builders import ResponseBuilder, MockDataBuilder


class MockTorchServeClient:
    """Mock TorchServe client for testing."""
    
    def __init__(
        self,
        default_response: Optional[Dict[str, Any]] = None,
        failure_rate: float = 0.0,
        latency_ms: int = 50
    ):
        self.default_response = default_response or MOCK_TORCHSERVE_RESPONSES["successful"]
        self.failure_rate = failure_rate
        self.latency_ms = latency_ms
        self.call_count = 0
        self.call_history = []
        self._is_healthy = True
        
    async def classify(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Mock classify method."""
        self.call_count += 1
        self.call_history.append({"prompt": prompt, "kwargs": kwargs, "timestamp": datetime.now(timezone.utc)})
        
        # Simulate latency
        await asyncio.sleep(self.latency_ms / 1000.0)
        
        # Simulate failures
        if random.random() < self.failure_rate:
            raise Exception("TorchServe request failed")
        
        # Return response
        response = self.default_response.copy()
        response["metadata"]["inference_time_ms"] = self.latency_ms
        return response
    
    async def batch_classify(self, prompts: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Mock batch classify method."""
        responses = []
        for i, prompt in enumerate(prompts):
            try:
                response = await self.classify(prompt, **kwargs)
                response["index"] = i
                responses.append(response)
            except Exception as e:
                responses.append({
                    "index": i,
                    "error": str(e),
                    "code": "CLASSIFICATION_ERROR"
                })
        return responses
    
    async def health_check(self) -> bool:
        """Mock health check."""
        return self._is_healthy
    
    def set_healthy(self, is_healthy: bool) -> None:
        """Set health status."""
        self._is_healthy = is_healthy
    
    def reset(self) -> None:
        """Reset mock state."""
        self.call_count = 0
        self.call_history = []
        self._is_healthy = True


class MockCacheService:
    """Mock cache service for testing."""
    
    def __init__(self, default_ttl: int = 3600):
        self.cache: Dict[str, Any] = {}
        self.default_ttl = default_ttl
        self.get_count = 0
        self.set_count = 0
        self.hit_count = 0
        self.miss_count = 0
        
    async def get_intent(self, prompt_hash: str) -> Optional[Dict[str, Any]]:
        """Mock get intent from cache."""
        self.get_count += 1
        result = self.cache.get(prompt_hash)
        
        if result:
            self.hit_count += 1
        else:
            self.miss_count += 1
            
        return result
    
    async def set_intent(
        self,
        prompt_hash: str,
        result: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> None:
        """Mock set intent in cache."""
        self.set_count += 1
        self.cache[prompt_hash] = {
            "result": result,
            "ttl": ttl or self.default_ttl,
            "cached_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def delete(self, key: str) -> None:
        """Mock delete from cache."""
        self.cache.pop(key, None)
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "get_count": self.get_count,
            "set_count": self.set_count,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": self.hit_count / self.get_count if self.get_count > 0 else 0
        }
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self.get_count = 0
        self.set_count = 0
        self.hit_count = 0
        self.miss_count = 0


class MockDatabaseService:
    """Mock database service for testing."""
    
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self.query_count = 0
        self.insert_count = 0
        
    async def save_classification(
        self,
        prompt: str,
        result: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """Mock save classification to database."""
        self.insert_count += 1
        record = MockDataBuilder.database_record(prompt, result, user_id)
        self.records.append(record)
        return record["id"]
    
    async def get_user_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Mock get user history."""
        self.query_count += 1
        user_records = [r for r in self.records if r.get("user_id") == user_id]
        return sorted(user_records, key=lambda x: x["created_at"], reverse=True)[:limit]
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Mock get database statistics."""
        self.query_count += 1
        return {
            "total_records": len(self.records),
            "unique_users": len(set(r.get("user_id") for r in self.records if r.get("user_id"))),
            "query_count": self.query_count,
            "insert_count": self.insert_count
        }
    
    def reset(self) -> None:
        """Reset database state."""
        self.records = []
        self.query_count = 0
        self.insert_count = 0


class MockMetricsCollector:
    """Mock metrics collector for testing."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.counters: Dict[str, int] = {}
        
    def record_latency(self, metric_name: str, value: float) -> None:
        """Record a latency measurement."""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)
    
    def increment_counter(self, counter_name: str, value: int = 1) -> None:
        """Increment a counter."""
        if counter_name not in self.counters:
            self.counters[counter_name] = 0
        self.counters[counter_name] += value
    
    def get_metric_stats(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        values = self.metrics.get(metric_name, [])
        if not values:
            return {"count": 0, "mean": 0, "min": 0, "max": 0}
            
        return {
            "count": len(values),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "p95": sorted(values)[int(len(values) * 0.95)] if len(values) > 1 else values[0]
        }
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()
        self.counters.clear()


@asynccontextmanager
async def mock_torchserve_server(
    host: str = "localhost",
    port: int = 8080,
    responses: Optional[Dict[str, Callable]] = None
):
    """Context manager that mocks a TorchServe server."""
    # This would typically start a mock HTTP server
    # For unit tests, we'll just yield a configured mock client
    client = MockTorchServeClient()
    
    if responses:
        # Configure custom responses
        pass
        
    yield client


def create_mock_app_state() -> Mock:
    """Create a mock FastAPI app state object."""
    state = Mock()
    state.ml_client = MockTorchServeClient()
    state.cache_service = MockCacheService()
    state.db_service = MockDatabaseService()
    state.metrics = MockMetricsCollector()
    state.config = {
        "model_name": "intent-classifier",
        "model_version": "1.0.0",
        "max_batch_size": 32,
        "cache_ttl": 3600,
        "enable_metrics": True
    }
    return state


def create_mock_dependencies() -> Dict[str, Any]:
    """Create mock dependencies for dependency injection."""
    return {
        "torchserve_client": MockTorchServeClient(),
        "cache_service": MockCacheService(),
        "db_service": MockDatabaseService(),
        "metrics_collector": MockMetricsCollector(),
        "current_user": lambda: {"user_id": "test-user", "roles": ["user"]},
        "rate_limiter": AsyncMock(return_value=True)
    }