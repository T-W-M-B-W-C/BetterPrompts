"""Intent classification API endpoints."""

from typing import Dict, List, Optional, Any
import uuid
import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from prometheus_client import Counter, Histogram
import time

from app.schemas.intent import (
    IntentRequest,
    IntentResponse,
    IntentBatchRequest,
    IntentBatchResponse,
    IntentFeedback,
    IntentFeedbackResponse,
)
from app.models import classifier
from app.core.logging import setup_logging
from app.services.cache import CacheService
from app.core.config import settings
from app.models.torchserve_client import (
    TorchServeError,
    TorchServeConnectionError,
    TorchServeInferenceError
)

router = APIRouter()
logger = setup_logging()

# Metrics
intent_requests = Counter(
    "intent_classification_requests_total",
    "Total number of intent classification requests",
    ["status"]
)
intent_duration = Histogram(
    "intent_classification_duration_seconds",
    "Duration of intent classification requests",
)

# Feedback metrics
feedback_submissions = Counter(
    "intent_feedback_submissions_total",
    "Total number of feedback submissions",
    ["feedback_type", "status"]
)
feedback_corrections = Counter(
    "intent_feedback_corrections_total",
    "Total number of intent corrections",
    ["original_intent", "correct_intent"]
)


@router.post("/intents/classify", response_model=IntentResponse)
async def classify_intent(
    request: IntentRequest,
    cache: CacheService = Depends(CacheService),
) -> IntentResponse:
    """Classify the intent of a user input."""
    start_time = time.time()
    
    try:
        # Check cache if enabled
        if settings.ENABLE_CACHING:
            cached_result = await cache.get_intent(request.text)
            if cached_result:
                intent_requests.labels(status="cache_hit").inc()
                return IntentResponse(**cached_result)
        
        # Classify intent
        result = await classifier.classify(request.text)
        
        # Prepare response
        response = IntentResponse(
            intent=result["intent"],
            confidence=result["confidence"],
            complexity=result["complexity"],
            suggested_techniques=result["suggested_techniques"],
            metadata={
                "processing_time": time.time() - start_time,
                "model_version": settings.MODEL_VERSION,
                "tokens_used": result.get("tokens_used", 0),
            }
        )
        
        # Cache result if enabled
        if settings.ENABLE_CACHING:
            await cache.set_intent(request.text, response.model_dump())
        
        # Record metrics
        intent_requests.labels(status="success").inc()
        intent_duration.observe(time.time() - start_time)
        
        return response
        
    except TorchServeConnectionError as e:
        logger.error(f"TorchServe connection error: {e}")
        intent_requests.labels(status="torchserve_connection_error").inc()
        raise HTTPException(
            status_code=503, 
            detail="Model service temporarily unavailable. Please try again later."
        )
    except TorchServeInferenceError as e:
        logger.error(f"TorchServe inference error: {e}")
        intent_requests.labels(status="torchserve_inference_error").inc()
        raise HTTPException(
            status_code=500,
            detail="Model inference failed. Please check your input and try again."
        )
    except TorchServeError as e:
        logger.error(f"TorchServe error: {e}")
        intent_requests.labels(status="torchserve_error").inc()
        raise HTTPException(status_code=500, detail="Model service error")
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        intent_requests.labels(status="validation_error").inc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during classification: {e}", exc_info=True)
        intent_requests.labels(status="unexpected_error").inc()
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.post("/intents/classify/batch", response_model=IntentBatchResponse)
async def classify_intents_batch(
    request: IntentBatchRequest,
    cache: CacheService = Depends(CacheService),
) -> IntentBatchResponse:
    """Classify intents for multiple inputs."""
    start_time = time.time()
    
    try:
        results = []
        
        # Process each text
        for text in request.texts:
            # Check cache
            if settings.ENABLE_CACHING:
                cached_result = await cache.get_intent(text)
                if cached_result:
                    results.append(IntentResponse(**cached_result))
                    continue
            
            # Classify
            result = await classifier.classify(text)
            response = IntentResponse(
                intent=result["intent"],
                confidence=result["confidence"],
                complexity=result["complexity"],
                suggested_techniques=result["suggested_techniques"],
                metadata={
                    "model_version": settings.MODEL_VERSION,
                    "tokens_used": result.get("tokens_used", 0),
                }
            )
            
            # Cache result
            if settings.ENABLE_CACHING:
                await cache.set_intent(text, response.model_dump())
            
            results.append(response)
        
        # Record metrics
        intent_requests.labels(status="batch_success").inc()
        intent_duration.observe(time.time() - start_time)
        
        return IntentBatchResponse(
            results=results,
            total_processing_time=time.time() - start_time,
        )
        
    except TorchServeConnectionError as e:
        logger.error(f"TorchServe connection error in batch: {e}")
        intent_requests.labels(status="batch_torchserve_connection_error").inc()
        raise HTTPException(
            status_code=503, 
            detail="Model service temporarily unavailable. Please try again later."
        )
    except TorchServeError as e:
        logger.error(f"TorchServe error in batch: {e}")
        intent_requests.labels(status="batch_torchserve_error").inc()
        raise HTTPException(status_code=500, detail="Model service error during batch processing")
    except Exception as e:
        logger.error(f"Batch intent classification failed: {e}", exc_info=True)
        intent_requests.labels(status="batch_unexpected_error").inc()
        raise HTTPException(status_code=500, detail="Batch classification failed")


@router.get("/intents/types", response_model=Dict[str, List[str]])
async def get_intent_types() -> Dict[str, List[str]]:
    """Get available intent types and their descriptions."""
    return {
        "intent_types": [
            "question_answering",
            "creative_writing",
            "code_generation",
            "data_analysis",
            "reasoning",
            "summarization",
            "translation",
            "conversation",
            "task_planning",
            "problem_solving",
        ],
        "complexity_levels": ["simple", "moderate", "complex"],
        "techniques": [
            "chain_of_thought",
            "tree_of_thoughts",
            "few_shot",
            "zero_shot",
            "self_consistency",
            "constitutional_ai",
            "iterative_refinement",
        ]
    }


@router.post("/intents/feedback", response_model=IntentFeedbackResponse)
async def submit_feedback(
    feedback: IntentFeedback,
    cache: CacheService = Depends(CacheService),
) -> IntentFeedbackResponse:
    """Submit feedback for intent classification corrections."""
    try:
        # Generate feedback ID
        feedback_id = str(uuid.uuid4())
        
        # Add timestamp if not provided
        if not feedback.timestamp:
            feedback.timestamp = datetime.utcnow().isoformat()
        
        # Store feedback in Redis with a dedicated key
        feedback_key = f"intent_feedback:{feedback_id}"
        feedback_data = feedback.model_dump()
        feedback_data["feedback_id"] = feedback_id
        
        # Store feedback with 30-day retention
        await cache.redis_client.setex(
            feedback_key,
            30 * 24 * 3600,  # 30 days
            json.dumps(feedback_data),
        )
        
        # Track metrics
        feedback_submissions.labels(
            feedback_type=feedback.feedback_type,
            status="success"
        ).inc()
        
        if feedback.feedback_type == "correction":
            feedback_corrections.labels(
                original_intent=feedback.original_intent,
                correct_intent=feedback.correct_intent
            ).inc()
        
        # Update cache if this is a correction
        cache_updated = False
        if feedback.feedback_type == "correction" and settings.ENABLE_CACHING:
            # Delete the old cached result
            deleted = await cache.delete_intent(feedback.text)
            
            # Store the corrected result
            if deleted:
                corrected_result = {
                    "intent": feedback.correct_intent,
                    "confidence": 1.0,  # High confidence for user-corrected data
                    "complexity": feedback.correct_complexity or "moderate",
                    "suggested_techniques": feedback.correct_techniques or [],
                    "metadata": {
                        "source": "user_feedback",
                        "feedback_id": feedback_id,
                        "model_version": settings.MODEL_VERSION,
                    }
                }
                cache_updated = await cache.set_intent(
                    feedback.text,
                    corrected_result,
                    ttl=3600 * 24  # Cache corrections for 24 hours
                )
        
        # Store feedback in a list for batch processing
        feedback_list_key = "intent_feedback:pending"
        await cache.redis_client.lpush(feedback_list_key, feedback_id)
        
        logger.info(
            f"Feedback submitted: {feedback_id} - "
            f"Type: {feedback.feedback_type}, "
            f"Original: {feedback.original_intent}, "
            f"Correct: {feedback.correct_intent}"
        )
        
        return IntentFeedbackResponse(
            status="success",
            message="Feedback received and stored successfully",
            feedback_id=feedback_id,
            cache_updated=cache_updated,
        )
        
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}", exc_info=True)
        feedback_submissions.labels(
            feedback_type=feedback.feedback_type,
            status="error"
        ).inc()
        raise HTTPException(
            status_code=500,
            detail="Failed to submit feedback"
        )


@router.get("/intents/feedback/stats", response_model=Dict[str, Any])
async def get_feedback_stats(
    cache: CacheService = Depends(CacheService),
) -> Dict[str, Any]:
    """Get feedback statistics."""
    try:
        # Count pending feedback
        pending_count = await cache.redis_client.llen("intent_feedback:pending")
        
        # Get correction patterns from Redis (simplified version)
        # In production, you'd want to aggregate this data properly
        stats = {
            "total_pending_feedback": pending_count,
            "feedback_types": {
                "corrections": feedback_corrections._value.sum() if hasattr(feedback_corrections._value, 'sum') else 0,
                "confirmations": 0,  # Would need separate tracking
            },
            "cache_enabled": settings.ENABLE_CACHING,
            "cache_ttl_hours": settings.CACHE_TTL / 3600,
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve feedback statistics"
        )