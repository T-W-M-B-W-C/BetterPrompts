"""
Shared test configuration and fixtures for intent classifier tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment
os.environ["TESTING"] = "true"
os.environ["USE_TORCHSERVE"] = "false"  # Default to local model for unit tests

# Import after setting up the path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import fakeredis.aioredis
from faker import Faker

# Initialize Faker
fake = Faker()


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


# Database fixtures
@pytest.fixture
async def test_db_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=NullPool,
    )
    
    # Import Base after app modules are available
    from app.db.database import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session


# Redis fixtures
@pytest.fixture
async def test_redis_client() -> AsyncGenerator[Any, None]:
    """Create a fake Redis client for testing."""
    client = fakeredis.aioredis.FakeRedis()
    yield client
    await client.flushall()
    await client.close()


# Application fixtures
@pytest.fixture
def test_app(mock_torchserve_client, mock_cache_service, test_db_session) -> FastAPI:
    """Create a test FastAPI application."""
    from app.main import app
    from app.db.database import get_db
    from app.services.cache import get_cache_service
    
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: test_db_session
    app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
    
    # Mock TorchServe client if it exists
    if hasattr(app.state, "ml_client"):
        app.state.ml_client = mock_torchserve_client
    
    yield app
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_client(test_app) -> TestClient:
    """Create a test client."""
    return TestClient(test_app)


@pytest.fixture
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


# Authentication fixtures
@pytest.fixture
def test_jwt_token() -> str:
    """Create a test JWT token."""
    return "Bearer test-jwt-token"


@pytest.fixture
def authenticated_client(test_client, test_jwt_token) -> TestClient:
    """Create an authenticated test client."""
    test_client.headers["Authorization"] = test_jwt_token
    return test_client


# Test data generation fixtures
@pytest.fixture
def sample_prompt() -> str:
    """Generate a sample prompt for testing."""
    return fake.sentence(nb_words=10)


@pytest.fixture
def sample_classification_request() -> dict:
    """Generate a sample classification request."""
    return {
        "prompt": fake.sentence(nb_words=15),
        "context": {
            "user_id": fake.uuid4(),
            "session_id": fake.uuid4(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }


@pytest.fixture
def sample_classification_response() -> dict:
    """Generate a sample classification response."""
    return {
        "intent": fake.random_element([
            "explain_concept", "generate_code", "debug_error",
            "analyze_data", "create_content", "answer_question"
        ]),
        "confidence": fake.pyfloat(min_value=0.7, max_value=1.0, right_digits=2),
        "sub_intent": fake.random_element(["technical", "creative", "analytical"]),
        "complexity": fake.random_element(["simple", "intermediate", "complex"]),
        "domain": fake.random_element(["programming", "science", "business", "general"]),
        "suggested_techniques": [
            fake.random_element([
                "chain_of_thought", "few_shot", "tree_of_thoughts",
                "self_consistency", "step_by_step"
            ])
            for _ in range(fake.random_int(min=1, max=3))
        ]
    }


# Utility fixtures
@pytest.fixture(autouse=True)
async def reset_test_state():
    """Reset test state before each test."""
    # This fixture runs before each test automatically
    yield
    # Cleanup after test if needed


# Performance testing fixtures
@pytest.fixture
def benchmark_data():
    """Generate data for benchmark tests."""
    return {
        "small_prompt": fake.sentence(nb_words=5),
        "medium_prompt": fake.sentence(nb_words=50),
        "large_prompt": fake.text(max_nb_chars=1000),
        "batch_prompts": [fake.sentence(nb_words=10) for _ in range(100)]
    }


# Test configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "torchserve: mark test as requiring TorchServe"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )


# Test collection modifiers
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Skip TorchServe tests if not available
        if "torchserve" in item.keywords and not os.environ.get("USE_TORCHSERVE", "false") == "true":
            skip_torchserve = pytest.mark.skip(reason="TorchServe not available")
            item.add_marker(skip_torchserve)