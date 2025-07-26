"""Health check endpoints with comprehensive model status monitoring."""

from typing import Dict, Any
import time

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db.database import get_db
from app.core.logging import setup_logging
from app.core.config import settings

router = APIRouter()
logger = setup_logging()


@router.get("/health", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "intent-classifier"}


@router.get("/health/ready", response_model=Dict[str, Any])
async def readiness_check() -> Dict[str, Any]:
    """Readiness check including database, all models, and adaptive routing status."""
    status_details = {
        "database": "unknown",
        "models": {
            "rules": "unknown",
            "zero_shot": "unknown",
            "distilbert": "unknown"
        },
        "adaptive_routing": "unknown",
        "cache": "unknown"
    }
    
    try:
        # Check database connection
        try:
            async for db in get_db():
                await db.execute(text("SELECT 1"))
            status_details["database"] = "healthy"
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            status_details["database"] = "unhealthy"
        
        # Check cache (Redis) connection
        try:
            from app.services.cache import CacheService
            cache = CacheService()
            await cache.redis_client.ping()
            status_details["cache"] = "healthy"
        except Exception as e:
            logger.error(f"Cache check failed: {e}")
            status_details["cache"] = "unhealthy"
        
        # Check if models are ready
        from app.models import classifier
        if not classifier.is_initialized():
            status_details["models"]["rules"] = "not_initialized"
            raise HTTPException(status_code=503, detail="Models not initialized")
        
        # Check individual model health
        # Rules-based classifier (always available)
        if classifier.enhanced_classifier:
            status_details["models"]["rules"] = "healthy"
        else:
            status_details["models"]["rules"] = "not_available"
        
        # Zero-shot classifier
        if classifier.hybrid_classifier:
            status_details["models"]["zero_shot"] = "healthy"
        else:
            status_details["models"]["zero_shot"] = "not_available"
        
        # DistilBERT (TorchServe)
        if settings.USE_TORCHSERVE and classifier.torchserve_client:
            try:
                torchserve_healthy = await classifier.torchserve_client.health_check()
                status_details["models"]["distilbert"] = "healthy" if torchserve_healthy else "unhealthy"
            except Exception as e:
                logger.error(f"TorchServe health check failed: {e}")
                status_details["models"]["distilbert"] = "unhealthy"
        else:
            status_details["models"]["distilbert"] = "not_configured"
        
        # Check adaptive routing
        if classifier.adaptive_router and settings.ENABLE_ADAPTIVE_ROUTING:
            status_details["adaptive_routing"] = "enabled"
            routing_stats = classifier.get_routing_stats()
            status_details["routing_stats"] = {
                "total_requests": routing_stats.get("total_requests", 0),
                "model_distribution": routing_stats.get("model_distribution", {})
            }
        else:
            status_details["adaptive_routing"] = "disabled"
        
        # Determine overall readiness
        is_ready = (
            status_details["database"] == "healthy" and
            status_details["cache"] == "healthy" and
            any(status == "healthy" for status in status_details["models"].values())
        )
        
        if not is_ready:
            raise HTTPException(status_code=503, detail="Service not ready")
        
        # All checks passed
        return {
            "status": "ready", 
            "service": "intent-classifier",
            "details": status_details,
            "version": settings.MODEL_VERSION,
            "features": {
                "adaptive_routing": settings.ENABLE_ADAPTIVE_ROUTING,
                "caching": settings.ENABLE_CACHING,
                "ab_testing": settings.AB_TEST_PERCENTAGE if hasattr(settings, 'AB_TEST_PERCENTAGE') else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "service": "intent-classifier", 
            "details": status_details,
            "error": str(e)
        }


@router.get("/health/live", response_model=Dict[str, str])
async def liveness_check() -> Dict[str, str]:
    """Liveness check for Kubernetes."""
    return {"status": "alive", "service": "intent-classifier"}


@router.get("/health/models", response_model=Dict[str, Any])
async def models_health_check() -> Dict[str, Any]:
    """Detailed health check for all models with performance metrics."""
    from app.models import classifier
    
    if not classifier.is_initialized():
        raise HTTPException(status_code=503, detail="Models not initialized")
    
    models_status = {}
    
    # Check each model with a test query
    test_query = "What is machine learning?"
    
    # Test rules-based classifier
    if classifier.enhanced_classifier:
        try:
            start_time = time.time()
            result = classifier.enhanced_classifier.classify(test_query)
            latency = (time.time() - start_time) * 1000
            
            models_status["rules"] = {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "confidence": result.confidence,
                "intent": result.intent
            }
        except Exception as e:
            logger.error(f"Rules classifier test failed: {e}")
            models_status["rules"] = {
                "status": "unhealthy",
                "error": str(e)
            }
    else:
        models_status["rules"] = {"status": "not_available"}
    
    # Test zero-shot classifier
    if classifier.hybrid_classifier:
        try:
            start_time = time.time()
            result = await classifier.hybrid_classifier.classify(test_query)
            latency = (time.time() - start_time) * 1000
            
            models_status["zero_shot"] = {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "confidence": result.get("confidence", 0),
                "intent": result.get("intent", "unknown")
            }
        except Exception as e:
            logger.error(f"Zero-shot classifier test failed: {e}")
            models_status["zero_shot"] = {
                "status": "unhealthy",
                "error": str(e)
            }
    else:
        models_status["zero_shot"] = {"status": "not_available"}
    
    # Test DistilBERT via TorchServe
    if settings.USE_TORCHSERVE and classifier.torchserve_client:
        try:
            start_time = time.time()
            result = await classifier.torchserve_client.classify(test_query)
            latency = (time.time() - start_time) * 1000
            
            models_status["distilbert"] = {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "confidence": result.get("confidence", 0),
                "intent": result.get("intent", "unknown")
            }
        except Exception as e:
            logger.error(f"DistilBERT test failed: {e}")
            models_status["distilbert"] = {
                "status": "unhealthy",
                "error": str(e)
            }
    else:
        models_status["distilbert"] = {"status": "not_configured"}
    
    # Get adaptive routing status if enabled
    routing_info = None
    if classifier.adaptive_router and settings.ENABLE_ADAPTIVE_ROUTING:
        routing_info = {
            "enabled": True,
            "statistics": classifier.get_routing_stats()
        }
    
    return {
        "models": models_status,
        "adaptive_routing": routing_info,
        "test_query": test_query,
        "timestamp": time.time()
    }


@router.get("/health/dependencies", response_model=Dict[str, Any])
async def dependencies_health_check() -> Dict[str, Any]:
    """Check health of all external dependencies."""
    dependencies = {}
    
    # Database
    try:
        async for db in get_db():
            start_time = time.time()
            await db.execute(text("SELECT 1"))
            latency = (time.time() - start_time) * 1000
        dependencies["postgres"] = {
            "status": "healthy",
            "latency_ms": round(latency, 2)
        }
    except Exception as e:
        dependencies["postgres"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Redis
    try:
        from app.services.cache import CacheService
        cache = CacheService()
        start_time = time.time()
        await cache.redis_client.ping()
        latency = (time.time() - start_time) * 1000
        
        # Get cache stats
        info = await cache.redis_client.info()
        dependencies["redis"] = {
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "unknown")
        }
    except Exception as e:
        dependencies["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # TorchServe (if configured)
    if settings.USE_TORCHSERVE:
        try:
            from app.models import classifier
            if classifier.torchserve_client:
                start_time = time.time()
                is_healthy = await classifier.torchserve_client.health_check()
                latency = (time.time() - start_time) * 1000
                
                dependencies["torchserve"] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "latency_ms": round(latency, 2),
                    "url": settings.TORCHSERVE_URL
                }
            else:
                dependencies["torchserve"] = {"status": "not_initialized"}
        except Exception as e:
            dependencies["torchserve"] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return {
        "dependencies": dependencies,
        "timestamp": time.time()
    }