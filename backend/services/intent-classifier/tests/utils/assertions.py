"""Custom assertions for intent-classifier tests."""

from typing import Dict, Any, List, Optional, Union
import pytest
from datetime import datetime


class AssertionHelpers:
    """Custom assertion helpers for intent classification tests."""
    
    @staticmethod
    def assert_valid_classification_response(response: Dict[str, Any], check_techniques: bool = True) -> None:
        """Assert that a classification response has all required fields with valid values."""
        # Required fields
        assert "intent" in response, "Response missing 'intent' field"
        assert "confidence" in response, "Response missing 'confidence' field"
        assert "complexity" in response, "Response missing 'complexity' field"
        assert "domain" in response, "Response missing 'domain' field"
        
        # Field types
        assert isinstance(response["intent"], str), "Intent must be a string"
        assert isinstance(response["confidence"], (int, float)), "Confidence must be a number"
        assert isinstance(response["complexity"], str), "Complexity must be a string"
        assert isinstance(response["domain"], str), "Domain must be a string"
        
        # Value ranges
        assert 0 <= response["confidence"] <= 1, f"Confidence {response['confidence']} not in range [0, 1]"
        assert response["intent"], "Intent cannot be empty"
        
        # Optional fields
        if check_techniques and "suggested_techniques" in response:
            assert isinstance(response["suggested_techniques"], list), "Suggested techniques must be a list"
            assert all(isinstance(t, str) for t in response["suggested_techniques"]), "All techniques must be strings"
            assert len(response["suggested_techniques"]) > 0, "At least one technique should be suggested"
        
        if "metadata" in response:
            assert isinstance(response["metadata"], dict), "Metadata must be a dictionary"
            if "inference_time_ms" in response["metadata"]:
                assert response["metadata"]["inference_time_ms"] >= 0, "Inference time must be non-negative"
    
    @staticmethod
    def assert_error_response(response: Dict[str, Any], expected_code: Optional[str] = None) -> None:
        """Assert that an error response has the correct structure."""
        assert "error" in response, "Error response missing 'error' field"
        assert isinstance(response["error"], str), "Error message must be a string"
        
        if "code" in response:
            assert isinstance(response["code"], str), "Error code must be a string"
            if expected_code:
                assert response["code"] == expected_code, f"Expected error code {expected_code}, got {response['code']}"
        
        if "status_code" in response:
            assert isinstance(response["status_code"], int), "Status code must be an integer"
            assert 400 <= response["status_code"] < 600, "Status code should be in error range (4xx or 5xx)"
    
    @staticmethod
    def assert_batch_response(responses: List[Dict[str, Any]], expected_size: int) -> None:
        """Assert that a batch response is valid."""
        assert isinstance(responses, list), "Batch response must be a list"
        assert len(responses) == expected_size, f"Expected {expected_size} responses, got {len(responses)}"
        
        for i, response in enumerate(responses):
            assert "index" in response, f"Response {i} missing 'index' field"
            assert response["index"] == i, f"Response index mismatch: expected {i}, got {response['index']}"
            
            if "error" not in response:
                AssertionHelpers.assert_valid_classification_response(response)
    
    @staticmethod
    def assert_confidence_threshold(response: Dict[str, Any], min_confidence: float = 0.7) -> None:
        """Assert that confidence meets minimum threshold."""
        assert response["confidence"] >= min_confidence, \
            f"Confidence {response['confidence']} below threshold {min_confidence}"
    
    @staticmethod
    def assert_technique_compatibility(
        intent: str,
        techniques: List[str],
        compatibility_map: Optional[Dict[str, List[str]]] = None
    ) -> None:
        """Assert that suggested techniques are compatible with the intent."""
        if compatibility_map is None:
            # Default compatibility rules
            compatibility_map = {
                "generate_code": ["few_shot", "step_by_step", "chain_of_thought"],
                "explain_concept": ["analogical", "step_by_step", "chain_of_thought"],
                "debug_error": ["chain_of_thought", "step_by_step", "tree_of_thoughts"],
                "analyze_data": ["chain_of_thought", "tree_of_thoughts", "structured_output"],
                "create_content": ["role_play", "emotional_appeal", "few_shot"],
                "answer_question": ["zero_shot", "chain_of_thought", "self_consistency"]
            }
        
        if intent in compatibility_map:
            compatible_techniques = compatibility_map[intent]
            assert any(t in compatible_techniques for t in techniques), \
                f"No compatible techniques found for intent '{intent}'. Got: {techniques}"
    
    @staticmethod
    def assert_performance_within_limits(
        response: Dict[str, Any],
        max_inference_time_ms: int = 500
    ) -> None:
        """Assert that performance metrics are within acceptable limits."""
        if "metadata" in response and "inference_time_ms" in response["metadata"]:
            inference_time = response["metadata"]["inference_time_ms"]
            assert inference_time <= max_inference_time_ms, \
                f"Inference time {inference_time}ms exceeds limit {max_inference_time_ms}ms"
    
    @staticmethod
    def assert_cache_hit(response_headers: Dict[str, str]) -> None:
        """Assert that a response was served from cache."""
        assert "X-Cache-Hit" in response_headers, "Missing cache hit header"
        assert response_headers["X-Cache-Hit"].lower() == "true", "Response not served from cache"
    
    @staticmethod
    def assert_rate_limit_headers(headers: Dict[str, str]) -> None:
        """Assert that rate limit headers are present and valid."""
        required_headers = ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
        
        for header in required_headers:
            assert header in headers, f"Missing rate limit header: {header}"
        
        # Validate header values
        limit = int(headers["X-RateLimit-Limit"])
        remaining = int(headers["X-RateLimit-Remaining"])
        reset = int(headers["X-RateLimit-Reset"])
        
        assert limit > 0, "Rate limit must be positive"
        assert 0 <= remaining <= limit, "Remaining requests must be between 0 and limit"
        assert reset > 0, "Reset timestamp must be positive"
    
    @staticmethod
    def assert_similar_intents(
        intent1: str,
        intent2: str,
        similarity_groups: Optional[List[List[str]]] = None
    ) -> None:
        """Assert that two intents are similar based on grouping."""
        if similarity_groups is None:
            similarity_groups = [
                ["generate_code", "debug_error", "review_code", "optimize_performance"],
                ["explain_concept", "answer_question", "summarize_text"],
                ["analyze_data", "create_content", "translate_text"]
            ]
        
        for group in similarity_groups:
            if intent1 in group and intent2 in group:
                return  # Intents are in the same group, so they're similar
        
        pytest.fail(f"Intents '{intent1}' and '{intent2}' are not similar")
    
    @staticmethod
    def assert_valid_timestamp(timestamp: Union[str, datetime], max_age_seconds: int = 60) -> None:
        """Assert that a timestamp is valid and recent."""
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {timestamp}")
        else:
            dt = timestamp
        
        now = datetime.now(dt.tzinfo or datetime.now().astimezone().tzinfo)
        age = (now - dt).total_seconds()
        
        assert age >= 0, "Timestamp is in the future"
        assert age <= max_age_seconds, f"Timestamp is too old: {age}s > {max_age_seconds}s"


# Convenience functions for common assertions
def assert_classification_success(response: Dict[str, Any]) -> None:
    """Assert that a classification was successful."""
    AssertionHelpers.assert_valid_classification_response(response)
    AssertionHelpers.assert_confidence_threshold(response)
    AssertionHelpers.assert_performance_within_limits(response)


def assert_classification_quality(
    response: Dict[str, Any],
    expected_intent: Optional[str] = None,
    min_confidence: float = 0.8
) -> None:
    """Assert classification quality metrics."""
    assert_classification_success(response)
    
    if expected_intent:
        assert response["intent"] == expected_intent, \
            f"Expected intent '{expected_intent}', got '{response['intent']}'"
    
    AssertionHelpers.assert_confidence_threshold(response, min_confidence)