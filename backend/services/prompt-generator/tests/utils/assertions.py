"""Custom assertions for prompt-generator tests."""

from typing import Dict, Any, List, Optional, Union
import pytest
from datetime import datetime


class PromptAssertions:
    """Custom assertion helpers for prompt generation tests."""
    
    @staticmethod
    def assert_valid_generation_response(response: Dict[str, Any]) -> None:
        """Assert that a generation response has all required fields with valid values."""
        # Required fields
        assert "enhanced_prompt" in response, "Response missing 'enhanced_prompt' field"
        assert "techniques_applied" in response, "Response missing 'techniques_applied' field"
        assert "metadata" in response, "Response missing 'metadata' field"
        
        # Field types
        assert isinstance(response["enhanced_prompt"], str), "Enhanced prompt must be a string"
        assert isinstance(response["techniques_applied"], list), "Techniques applied must be a list"
        assert isinstance(response["metadata"], dict), "Metadata must be a dictionary"
        
        # Field content validation
        assert response["enhanced_prompt"], "Enhanced prompt cannot be empty"
        assert len(response["techniques_applied"]) > 0, "At least one technique must be applied"
        assert all(isinstance(t, str) for t in response["techniques_applied"]), "All techniques must be strings"
        
        # Metadata validation
        metadata = response["metadata"]
        assert "generation_time_ms" in metadata, "Metadata missing generation time"
        assert "token_count" in metadata, "Metadata missing token count"
        assert "model_used" in metadata, "Metadata missing model used"
        
        # Value ranges
        assert metadata["generation_time_ms"] >= 0, "Generation time must be non-negative"
        assert metadata["token_count"] > 0, "Token count must be positive"
    
    @staticmethod
    def assert_technique_applied(
        original_prompt: str,
        enhanced_prompt: str,
        technique: str
    ) -> None:
        """Assert that a specific technique was properly applied."""
        # Basic check - enhanced prompt should be different and longer
        assert enhanced_prompt != original_prompt, f"Technique {technique} didn't modify the prompt"
        
        # Technique-specific checks
        technique_markers = {
            "chain_of_thought": ["step by step", "First,", "Next,", "Finally,", "Let me think"],
            "few_shot": ["Example", "Input:", "Output:", "examples"],
            "tree_of_thoughts": ["Approach", "multiple", "explore", "paths", "consider"],
            "step_by_step": ["Step 1", "Step 2", "steps:", "follow these steps"],
            "role_play": ["As a", "expert", "perspective", "professional"],
            "structured_output": ["###", "format:", "structure", "organized"],
            "emotional_appeal": ["important", "crucial", "together", "understand"],
            "analogical": ["similar to", "like", "analogy", "think of it as"],
            "react": ["Thought:", "Action:", "Observation:", "Reasoning:"],
            "self_consistency": ["verify", "multiple angles", "cross-check", "consistent"]
        }
        
        if technique in technique_markers:
            markers = technique_markers[technique]
            assert any(marker.lower() in enhanced_prompt.lower() for marker in markers), \
                f"Technique {technique} markers not found in enhanced prompt"
    
    @staticmethod
    def assert_prompt_quality(
        original_prompt: str,
        enhanced_prompt: str,
        max_expansion_ratio: float = 3.0,
        min_expansion_ratio: float = 1.2
    ) -> None:
        """Assert that the enhanced prompt meets quality standards."""
        original_length = len(original_prompt.split())
        enhanced_length = len(enhanced_prompt.split())
        expansion_ratio = enhanced_length / original_length if original_length > 0 else float('inf')
        
        assert expansion_ratio >= min_expansion_ratio, \
            f"Enhanced prompt not sufficiently expanded (ratio: {expansion_ratio:.2f} < {min_expansion_ratio})"
        
        assert expansion_ratio <= max_expansion_ratio, \
            f"Enhanced prompt too verbose (ratio: {expansion_ratio:.2f} > {max_expansion_ratio})"
        
        # Check that original content is preserved
        assert any(word in enhanced_prompt for word in original_prompt.split() if len(word) > 3), \
            "Enhanced prompt doesn't seem to preserve original content"
    
    @staticmethod
    def assert_optimization_valid(
        original_prompt: str,
        optimized_prompt: str,
        optimization_goals: List[str]
    ) -> None:
        """Assert that optimization goals were met."""
        for goal in optimization_goals:
            if goal == "clarity":
                # Check for clarity improvements (simplified language, better structure)
                assert len(optimized_prompt.split('.')) >= len(original_prompt.split('.')), \
                    "Clarity optimization should improve sentence structure"
            
            elif goal == "conciseness":
                # Check that prompt is more concise
                assert len(optimized_prompt) <= len(original_prompt) * 1.1, \
                    "Conciseness optimization should not increase length significantly"
            
            elif goal == "specificity":
                # Check for more specific language
                specific_words = ["specifically", "exactly", "precisely", "particular"]
                assert any(word in optimized_prompt.lower() for word in specific_words) or \
                       len(optimized_prompt.split()) > len(original_prompt.split()), \
                    "Specificity optimization should add detail"
    
    @staticmethod
    def assert_batch_response_valid(
        responses: List[Dict[str, Any]],
        expected_size: int,
        allow_errors: bool = False
    ) -> None:
        """Assert that a batch response is valid."""
        assert isinstance(responses, list), "Batch response must be a list"
        assert len(responses) == expected_size, f"Expected {expected_size} responses, got {len(responses)}"
        
        error_count = 0
        for i, response in enumerate(responses):
            assert "index" in response, f"Response {i} missing 'index' field"
            assert response["index"] == i, f"Response index mismatch: expected {i}, got {response['index']}"
            
            if "error" in response:
                error_count += 1
                if not allow_errors:
                    pytest.fail(f"Unexpected error in batch response at index {i}: {response['error']}")
            else:
                PromptAssertions.assert_valid_generation_response(response)
        
        if allow_errors and error_count == 0:
            pytest.fail("Expected some errors in batch response but found none")
    
    @staticmethod
    def assert_model_consistency(
        responses: List[Dict[str, Any]],
        expected_model: Optional[str] = None
    ) -> None:
        """Assert that all responses used consistent model."""
        models_used = set()
        
        for response in responses:
            if "metadata" in response and "model_used" in response["metadata"]:
                models_used.add(response["metadata"]["model_used"])
        
        assert len(models_used) == 1, f"Inconsistent models used: {models_used}"
        
        if expected_model:
            assert expected_model in models_used, \
                f"Expected model {expected_model}, but got {models_used}"
    
    @staticmethod
    def assert_performance_within_limits(
        response: Dict[str, Any],
        max_generation_time_ms: int = 1000,
        max_tokens: int = 2000
    ) -> None:
        """Assert that performance metrics are within acceptable limits."""
        if "metadata" in response:
            metadata = response["metadata"]
            
            if "generation_time_ms" in metadata:
                assert metadata["generation_time_ms"] <= max_generation_time_ms, \
                    f"Generation time {metadata['generation_time_ms']}ms exceeds limit {max_generation_time_ms}ms"
            
            if "token_count" in metadata:
                assert metadata["token_count"] <= max_tokens, \
                    f"Token count {metadata['token_count']} exceeds limit {max_tokens}"
    
    @staticmethod
    def assert_cache_hit(response_headers: Dict[str, str]) -> None:
        """Assert that a response was served from cache."""
        assert "X-Cache-Hit" in response_headers, "Missing cache hit header"
        assert response_headers["X-Cache-Hit"].lower() == "true", "Response not served from cache"
    
    @staticmethod
    def assert_technique_compatibility(
        intent: str,
        techniques: List[str],
        compatibility_map: Optional[Dict[str, List[str]]] = None
    ) -> None:
        """Assert that techniques are compatible with the intent."""
        if compatibility_map is None:
            # Use default compatibility from constants
            from .constants import TECHNIQUE_COMPATIBILITY
            compatibility_map = TECHNIQUE_COMPATIBILITY
        
        if intent in compatibility_map:
            compatible_techniques = compatibility_map[intent]
            for technique in techniques:
                assert technique in compatible_techniques, \
                    f"Technique '{technique}' not compatible with intent '{intent}'"


# Convenience assertion functions
def assert_generation_success(response: Dict[str, Any]) -> None:
    """Assert that a prompt generation was successful."""
    PromptAssertions.assert_valid_generation_response(response)
    PromptAssertions.assert_performance_within_limits(response)


def assert_enhanced_prompt_quality(
    original: str,
    enhanced: str,
    techniques: List[str]
) -> None:
    """Assert overall quality of enhanced prompt."""
    PromptAssertions.assert_prompt_quality(original, enhanced)
    
    # Check that at least one technique was applied
    for technique in techniques:
        try:
            PromptAssertions.assert_technique_applied(original, enhanced, technique)
            return  # At least one technique was successfully applied
        except AssertionError:
            continue
    
    pytest.fail(f"None of the techniques {techniques} were properly applied")