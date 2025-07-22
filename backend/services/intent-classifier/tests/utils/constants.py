"""Test constants for intent-classifier tests."""

from enum import Enum
from typing import Dict, List, Any


class IntentType(str, Enum):
    """Standard intent types for testing."""
    EXPLAIN_CONCEPT = "explain_concept"
    GENERATE_CODE = "generate_code"
    DEBUG_ERROR = "debug_error"
    ANALYZE_DATA = "analyze_data"
    CREATE_CONTENT = "create_content"
    ANSWER_QUESTION = "answer_question"
    SUMMARIZE_TEXT = "summarize_text"
    TRANSLATE_TEXT = "translate_text"
    REVIEW_CODE = "review_code"
    OPTIMIZE_PERFORMANCE = "optimize_performance"


class ComplexityLevel(str, Enum):
    """Complexity levels for testing."""
    SIMPLE = "simple"
    INTERMEDIATE = "intermediate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class Domain(str, Enum):
    """Domain categories for testing."""
    PROGRAMMING = "programming"
    SCIENCE = "science"
    BUSINESS = "business"
    EDUCATION = "education"
    CREATIVE = "creative"
    GENERAL = "general"


class TechniqueType(str, Enum):
    """Prompt engineering techniques."""
    CHAIN_OF_THOUGHT = "chain_of_thought"
    FEW_SHOT = "few_shot"
    ZERO_SHOT = "zero_shot"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    SELF_CONSISTENCY = "self_consistency"
    STEP_BY_STEP = "step_by_step"
    ROLE_PLAY = "role_play"
    EMOTIONAL_APPEAL = "emotional_appeal"
    STRUCTURED_OUTPUT = "structured_output"
    ANALOGICAL = "analogical"
    REACT = "react"


# Test data samples
TEST_PROMPTS: Dict[str, Dict[str, Any]] = {
    "simple_question": {
        "text": "What is the capital of France?",
        "expected_intent": IntentType.ANSWER_QUESTION,
        "expected_complexity": ComplexityLevel.SIMPLE,
        "expected_domain": Domain.GENERAL,
        "expected_techniques": [TechniqueType.ZERO_SHOT]
    },
    "code_generation": {
        "text": "Write a Python function to calculate the nth Fibonacci number using dynamic programming",
        "expected_intent": IntentType.GENERATE_CODE,
        "expected_complexity": ComplexityLevel.INTERMEDIATE,
        "expected_domain": Domain.PROGRAMMING,
        "expected_techniques": [TechniqueType.FEW_SHOT, TechniqueType.STEP_BY_STEP]
    },
    "complex_analysis": {
        "text": "Analyze the quarterly sales data, identify trends, create visualizations, and provide recommendations for improving revenue in the next quarter",
        "expected_intent": IntentType.ANALYZE_DATA,
        "expected_complexity": ComplexityLevel.COMPLEX,
        "expected_domain": Domain.BUSINESS,
        "expected_techniques": [TechniqueType.CHAIN_OF_THOUGHT, TechniqueType.TREE_OF_THOUGHTS, TechniqueType.STRUCTURED_OUTPUT]
    },
    "debugging": {
        "text": "My React component is re-rendering infinitely. Here's the code: [code snippet]. Help me fix it.",
        "expected_intent": IntentType.DEBUG_ERROR,
        "expected_complexity": ComplexityLevel.INTERMEDIATE,
        "expected_domain": Domain.PROGRAMMING,
        "expected_techniques": [TechniqueType.CHAIN_OF_THOUGHT, TechniqueType.STEP_BY_STEP]
    },
    "creative_writing": {
        "text": "Write a short story about a robot learning to paint",
        "expected_intent": IntentType.CREATE_CONTENT,
        "expected_complexity": ComplexityLevel.INTERMEDIATE,
        "expected_domain": Domain.CREATIVE,
        "expected_techniques": [TechniqueType.ROLE_PLAY, TechniqueType.EMOTIONAL_APPEAL]
    },
    "educational": {
        "text": "Explain quantum computing to a 10-year-old",
        "expected_intent": IntentType.EXPLAIN_CONCEPT,
        "expected_complexity": ComplexityLevel.COMPLEX,
        "expected_domain": Domain.EDUCATION,
        "expected_techniques": [TechniqueType.ANALOGICAL, TechniqueType.STEP_BY_STEP]
    }
}


# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "api_response_time_ms": 200,
    "model_inference_time_ms": 500,
    "batch_inference_time_ms": 2000,
    "cache_hit_time_ms": 10,
    "min_confidence_score": 0.7,
    "max_retries": 3,
    "timeout_seconds": 30
}


# Error messages for testing
ERROR_MESSAGES = {
    "invalid_prompt": "Prompt text is required and must be a non-empty string",
    "prompt_too_long": "Prompt exceeds maximum length of 10000 characters",
    "torchserve_unavailable": "TorchServe is not available",
    "classification_failed": "Failed to classify intent",
    "invalid_confidence": "Confidence score must be between 0 and 1",
    "database_error": "Database operation failed",
    "cache_error": "Cache operation failed",
    "timeout_error": "Request timed out"
}


# Mock responses
MOCK_TORCHSERVE_RESPONSES = {
    "successful": {
        "intent": "explain_concept",
        "confidence": 0.95,
        "sub_intent": "technical",
        "complexity": "intermediate",
        "domain": "programming",
        "suggested_techniques": ["chain_of_thought", "few_shot"],
        "metadata": {
            "model_version": "1.0.0",
            "inference_time_ms": 45,
            "token_count": 128
        }
    },
    "low_confidence": {
        "intent": "unknown",
        "confidence": 0.45,
        "sub_intent": None,
        "complexity": "simple",
        "domain": "general",
        "suggested_techniques": ["zero_shot"],
        "metadata": {
            "model_version": "1.0.0",
            "inference_time_ms": 32,
            "token_count": 64
        }
    },
    "error": {
        "error": "Model inference failed",
        "code": "MODEL_ERROR",
        "details": "CUDA out of memory"
    }
}


# Test user contexts
TEST_USER_CONTEXTS = {
    "new_user": {
        "user_id": "test-user-001",
        "session_id": "session-001",
        "preferences": {},
        "history_count": 0
    },
    "experienced_user": {
        "user_id": "test-user-002",
        "session_id": "session-002",
        "preferences": {
            "preferred_techniques": ["chain_of_thought", "few_shot"],
            "domain_expertise": ["programming", "science"]
        },
        "history_count": 150
    },
    "api_user": {
        "user_id": "api-key-user",
        "session_id": None,
        "api_key": "test-api-key-123",
        "rate_limit": 1000
    }
}


# Batch test data
BATCH_TEST_SIZES = [1, 10, 32, 50, 100]
MAX_BATCH_SIZE = 100


# Redis cache keys for testing
CACHE_KEY_PATTERNS = {
    "intent": "intent:v1:{prompt_hash}",
    "user_history": "user:{user_id}:history",
    "session": "session:{session_id}",
    "rate_limit": "rate_limit:{user_id}:{window}"
}


# Test timeouts
TEST_TIMEOUTS = {
    "unit": 1.0,
    "integration": 5.0,
    "e2e": 30.0,
    "performance": 60.0
}