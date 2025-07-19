"""
Shared test configuration and fixtures for intent classifier tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch
import os

# Set test environment
os.environ["TESTING"] = "true"
os.environ["USE_TORCHSERVE"] = "false"  # Default to local model for unit tests


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_torchserve_client():
    """Mock TorchServe client for testing."""
    client = AsyncMock()
    client.health_check = AsyncMock(return_value=True)
    client.is_healthy = Mock(return_value=True)
    client.classify = AsyncMock(return_value={
        "intent": "test_intent",
        "confidence": 0.95,
        "complexity": {"level": "moderate", "score": 0.6},
        "suggested_techniques": ["chain_of_thought"],
        "metadata": {"inference_time_ms": 100}
    })
    client.batch_classify = AsyncMock(return_value=[
        {
            "intent": "test_intent",
            "confidence": 0.95,
            "complexity": {"level": "moderate", "score": 0.6},
            "metadata": {"batch_index": 0}
        }
    ])
    return client


@pytest.fixture
async def mock_cache_service():
    """Mock cache service for testing."""
    cache = AsyncMock()
    cache.get_intent = AsyncMock(return_value=None)  # Default to cache miss
    cache.set_intent = AsyncMock(return_value=None)
    return cache


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('app.core.config.settings') as mock_settings:
        mock_settings.USE_TORCHSERVE = False
        mock_settings.MODEL_NAME = "test-model"
        mock_settings.MODEL_MAX_LENGTH = 512
        mock_settings.MODEL_BATCH_SIZE = 32
        mock_settings.ENABLE_CACHING = True
        mock_settings.CACHE_TTL = 3600
        mock_settings.TORCHSERVE_URL = "http://localhost:8080/predictions/test"
        mock_settings.TORCHSERVE_HEALTH_URL = "http://localhost:8080/ping"
        mock_settings.TORCHSERVE_TIMEOUT = 30
        mock_settings.TORCHSERVE_MAX_RETRIES = 3
        mock_settings.HEALTH_CHECK_INTERVAL = 30
        mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
        mock_settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
        yield mock_settings


@pytest.fixture
def sample_intents():
    """Sample intent classification test data."""
    return [
        {
            "text": "Write a Python function to calculate fibonacci",
            "expected_intent": "code_generation",
            "expected_complexity": "moderate",
            "expected_techniques": ["few_shot", "chain_of_thought"]
        },
        {
            "text": "What is the capital of France?",
            "expected_intent": "question_answering",
            "expected_complexity": "simple",
            "expected_techniques": ["direct_answer"]
        },
        {
            "text": "Analyze sales data and create visualizations",
            "expected_intent": "data_analysis",
            "expected_complexity": "complex",
            "expected_techniques": ["chain_of_thought", "tree_of_thoughts"]
        }
    ]


@pytest.fixture
async def mock_model():
    """Mock ML model for testing."""
    model = Mock()
    model.predict = Mock(return_value={
        "intent": "test_intent",
        "confidence": 0.95,
        "tokens": 10
    })
    return model


@pytest.fixture
def performance_threshold():
    """Performance thresholds for tests."""
    return {
        "api_response_time": 0.2,  # 200ms
        "model_inference_time": 0.5,  # 500ms
        "batch_processing_time": 2.0,  # 2s for batch
        "cache_hit_speedup": 0.5  # 50% faster for cache hits
    }


# Test markers explanation
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.slow = pytest.mark.slow
pytest.mark.torchserve = pytest.mark.torchserve
pytest.mark.critical = pytest.mark.critical