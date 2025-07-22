"""Main pytest configuration for prompt-generator service tests."""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Generator, Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import pytest_asyncio
from faker import Faker
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import fakeredis.aioredis

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment
os.environ["TESTING"] = "true"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["ANTHROPIC_API_KEY"] = "test-key"

# Import after setting up the path
from app.main import app
from app.config import settings
from app.engine import PromptEngine
from app.techniques import get_all_techniques

# Initialize Faker
fake = Faker()


# Event loop configuration
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# Database fixtures (if needed for prompt-generator)
@pytest_asyncio.fixture(scope="function")
async def test_db_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=NullPool,
    )
    
    # Create tables if any exist
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


# Redis fixtures
@pytest_asyncio.fixture(scope="function")
async def test_redis_client() -> AsyncGenerator[Any, None]:
    """Create a fake Redis client for testing."""
    client = fakeredis.aioredis.FakeRedis()
    yield client
    await client.flushall()
    await client.close()


# Mock LLM clients
@pytest.fixture(scope="function")
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = MagicMock()
    
    # Mock completion response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="This is a test response using chain of thought technique."
            )
        )
    ]
    mock_response.usage = MagicMock(
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150
    )
    
    client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    return client


@pytest.fixture(scope="function")
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    client = MagicMock()
    
    # Mock completion response
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(
            text="This is a test response using advanced reasoning."
        )
    ]
    mock_response.usage = MagicMock(
        input_tokens=100,
        output_tokens=50
    )
    
    client.messages.create = AsyncMock(return_value=mock_response)
    
    return client


# Prompt engine fixtures
@pytest.fixture(scope="function")
def mock_prompt_engine(mock_openai_client, mock_anthropic_client):
    """Create a mock prompt engine."""
    engine = PromptEngine()
    
    # Replace LLM clients with mocks
    with patch.object(engine, 'openai_client', mock_openai_client):
        with patch.object(engine, 'anthropic_client', mock_anthropic_client):
            yield engine


# Application fixtures
@pytest.fixture(scope="function")
def test_app(mock_prompt_engine, test_redis_client) -> FastAPI:
    """Create a test FastAPI application."""
    # Override dependencies if needed
    # app.dependency_overrides[get_prompt_engine] = lambda: mock_prompt_engine
    # app.dependency_overrides[get_redis] = lambda: test_redis_client
    
    yield app
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_client(test_app) -> TestClient:
    """Create a test client."""
    return TestClient(test_app)


@pytest_asyncio.fixture(scope="function")
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


# Authentication fixtures
@pytest.fixture(scope="function")
def test_jwt_token() -> str:
    """Create a test JWT token."""
    return "Bearer test-jwt-token"


@pytest.fixture(scope="function")
def authenticated_client(test_client, test_jwt_token) -> TestClient:
    """Create an authenticated test client."""
    test_client.headers["Authorization"] = test_jwt_token
    return test_client


# Test data fixtures
@pytest.fixture(scope="function")
def sample_generation_request() -> Dict[str, Any]:
    """Generate a sample prompt generation request."""
    return {
        "original_prompt": fake.sentence(nb_words=15),
        "intent": fake.random_element([
            "explain_concept", "generate_code", "debug_error",
            "analyze_data", "create_content", "answer_question"
        ]),
        "techniques": [
            fake.random_element([
                "chain_of_thought", "few_shot", "tree_of_thoughts",
                "self_consistency", "step_by_step"
            ])
            for _ in range(fake.random_int(min=1, max=3))
        ],
        "context": {
            "user_id": fake.uuid4(),
            "session_id": fake.uuid4(),
            "complexity": fake.random_element(["simple", "intermediate", "complex"]),
            "domain": fake.random_element(["programming", "science", "business", "general"])
        }
    }


@pytest.fixture(scope="function")
def sample_generation_response() -> Dict[str, Any]:
    """Generate a sample generation response."""
    return {
        "enhanced_prompt": fake.paragraph(nb_sentences=5),
        "techniques_applied": [
            fake.random_element([
                "chain_of_thought", "few_shot", "tree_of_thoughts",
                "self_consistency", "step_by_step"
            ])
            for _ in range(fake.random_int(min=1, max=3))
        ],
        "metadata": {
            "generation_time_ms": fake.random_int(min=100, max=500),
            "token_count": fake.random_int(min=50, max=500),
            "model_used": fake.random_element(["gpt-4", "claude-3", "gpt-3.5-turbo"]),
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "explanation": "Applied techniques to enhance the prompt for better results."
    }


@pytest.fixture(scope="function")
def technique_examples() -> Dict[str, List[str]]:
    """Get example prompts for each technique."""
    return {
        "chain_of_thought": [
            "Let's think through this step by step:",
            "First, I'll analyze the problem:",
            "Breaking this down into steps:"
        ],
        "few_shot": [
            "Here are some examples:",
            "Example 1: Input: X, Output: Y",
            "Following the pattern from these examples:"
        ],
        "tree_of_thoughts": [
            "Let's explore multiple approaches:",
            "Approach 1: ...\nApproach 2: ...\nApproach 3: ...",
            "Evaluating different paths:"
        ],
        "self_consistency": [
            "Let me verify this from multiple angles:",
            "Checking consistency across approaches:",
            "Cross-validating the solution:"
        ],
        "step_by_step": [
            "Step 1: ...\nStep 2: ...\nStep 3: ...",
            "Following these steps in order:",
            "Here's the systematic approach:"
        ],
        "role_play": [
            "As an expert in this field:",
            "From the perspective of a specialist:",
            "Acting as a professional:"
        ],
        "emotional_appeal": [
            "This is really important because:",
            "I understand how crucial this is:",
            "Let's work together on this:"
        ],
        "structured_output": [
            "I'll provide the answer in this format:",
            "Structured response:\n- Point 1:\n- Point 2:",
            "Organizing the information:"
        ],
        "analogical": [
            "This is similar to:",
            "Think of it like:",
            "By analogy:"
        ],
        "react": [
            "Thought: ...\nAction: ...\nObservation: ...",
            "Reasoning: ...\nExecution: ...\nResult: ...",
            "Let me think and act on this:"
        ],
        "zero_shot": [
            "Based on my understanding:",
            "Directly addressing your question:",
            "Here's the answer:"
        ]
    }


# Performance testing fixtures
@pytest.fixture(scope="function")
def benchmark_prompts() -> Dict[str, Any]:
    """Generate prompts for benchmark tests."""
    return {
        "simple": fake.sentence(nb_words=5),
        "medium": fake.sentence(nb_words=50),
        "complex": fake.text(max_nb_chars=1000),
        "batch": [fake.sentence(nb_words=10) for _ in range(100)]
    }


# Mock technique implementations
@pytest.fixture(scope="function")
def mock_techniques():
    """Mock technique implementations."""
    techniques = {}
    
    for technique_name in [
        "chain_of_thought", "few_shot", "tree_of_thoughts",
        "self_consistency", "step_by_step", "role_play",
        "emotional_appeal", "structured_output", "analogical",
        "react", "zero_shot"
    ]:
        mock_technique = MagicMock()
        mock_technique.apply = AsyncMock(
            return_value=f"Enhanced prompt using {technique_name}"
        )
        mock_technique.name = technique_name
        mock_technique.description = f"Mock {technique_name} technique"
        techniques[technique_name] = mock_technique
    
    return techniques


# Utility fixtures
@pytest.fixture(autouse=True)
async def reset_test_state():
    """Reset test state before each test."""
    # This fixture runs before each test automatically
    yield
    # Cleanup after test if needed


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
        "markers", "llm: mark test as requiring LLM API"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )
    config.addinivalue_line(
        "markers", "technique: mark test as testing specific technique"
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
        
        # Skip LLM tests if API keys not available
        if "llm" in item.keywords and not os.environ.get("OPENAI_API_KEY"):
            skip_llm = pytest.mark.skip(reason="LLM API keys not available")
            item.add_marker(skip_llm)