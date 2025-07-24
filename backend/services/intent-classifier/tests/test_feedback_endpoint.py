"""Test the feedback endpoint functionality."""

import pytest
from httpx import AsyncClient
from app.main import app
from app.schemas.intent import IntentFeedback, IntentFeedbackResponse


@pytest.mark.asyncio
async def test_submit_feedback_correction():
    """Test submitting correction feedback."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Submit feedback
        feedback_data = {
            "text": "How do I implement a binary search?",
            "original_intent": "question_answering",
            "correct_intent": "code_generation",
            "original_confidence": 0.75,
            "correct_complexity": "moderate",
            "correct_techniques": ["few_shot", "chain_of_thought"],
            "feedback_type": "correction"
        }
        
        response = await client.post(
            "/api/v1/intents/feedback",
            json=feedback_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["status"] == "success"
        assert "feedback_id" in result
        assert isinstance(result["cache_updated"], bool)
        assert "successfully" in result["message"]


@pytest.mark.asyncio
async def test_submit_feedback_confirmation():
    """Test submitting confirmation feedback."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Submit feedback
        feedback_data = {
            "text": "Translate this to Spanish",
            "original_intent": "translation",
            "correct_intent": "translation",
            "original_confidence": 0.95,
            "feedback_type": "confirmation"
        }
        
        response = await client.post(
            "/api/v1/intents/feedback",
            json=feedback_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["status"] == "success"
        assert "feedback_id" in result


@pytest.mark.asyncio
async def test_feedback_stats_endpoint():
    """Test the feedback statistics endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/intents/feedback/stats")
        
        assert response.status_code == 200
        stats = response.json()
        
        assert "total_pending_feedback" in stats
        assert "feedback_types" in stats
        assert "cache_enabled" in stats
        assert "cache_ttl_hours" in stats
        
        assert isinstance(stats["total_pending_feedback"], int)
        assert stats["cache_ttl_hours"] == 1.0  # 1 hour as configured


@pytest.mark.asyncio
async def test_feedback_validation():
    """Test feedback validation."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test with invalid complexity
        feedback_data = {
            "text": "Test prompt",
            "original_intent": "question_answering",
            "correct_intent": "code_generation",
            "original_confidence": 0.75,
            "correct_complexity": "invalid_complexity",  # Invalid
            "feedback_type": "correction"
        }
        
        response = await client.post(
            "/api/v1/intents/feedback",
            json=feedback_data
        )
        
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_feedback_with_cache_update():
    """Test that feedback updates the cache."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        test_prompt = "What is machine learning?"
        
        # First, classify the prompt
        classify_response = await client.post(
            "/api/v1/intents/classify",
            json={"text": test_prompt}
        )
        
        assert classify_response.status_code == 200
        original_result = classify_response.json()
        
        # Submit correction feedback
        feedback_data = {
            "text": test_prompt,
            "original_intent": original_result["intent"],
            "correct_intent": "education",
            "original_confidence": original_result["confidence"],
            "correct_complexity": "complex",
            "correct_techniques": ["self_consistency", "tree_of_thoughts"],
            "feedback_type": "correction"
        }
        
        feedback_response = await client.post(
            "/api/v1/intents/feedback",
            json=feedback_data
        )
        
        assert feedback_response.status_code == 200
        feedback_result = feedback_response.json()
        
        # If caching is enabled, cache_updated should reflect the update
        if feedback_result["cache_updated"]:
            # Re-classify the same prompt
            reclassify_response = await client.post(
                "/api/v1/intents/classify",
                json={"text": test_prompt}
            )
            
            assert reclassify_response.status_code == 200
            updated_result = reclassify_response.json()
            
            # Check if the corrected values are returned
            assert updated_result["intent"] == "education"
            assert updated_result["confidence"] == 1.0
            assert updated_result["complexity"] == "complex"
            assert set(updated_result["suggested_techniques"]) == {"self_consistency", "tree_of_thoughts"}