"""Intent classification API endpoints."""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from prometheus_client import Counter, Histogram
import time

from app.schemas.intent import (
    IntentRequest,
    IntentResponse,
    IntentBatchRequest,
    IntentBatchResponse,
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