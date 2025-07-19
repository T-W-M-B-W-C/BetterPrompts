"""Health check endpoints."""

from typing import Dict, Any

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
    """Readiness check including database, model, and TorchServe status."""
    status_details = {
        "database": "unknown",
        "model": "unknown",
        "torchserve": "not_applicable"
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
        
        # Check if model/TorchServe is ready
        from app.models import classifier
        if not classifier.is_initialized():
            status_details["model"] = "not_initialized"
            raise HTTPException(status_code=503, detail="Model not initialized")
        
        status_details["model"] = "initialized"
        
        # Check TorchServe connectivity if enabled
        if settings.USE_TORCHSERVE and classifier.torchserve_client:
            try:
                torchserve_healthy = await classifier.torchserve_client.health_check()
                status_details["torchserve"] = "healthy" if torchserve_healthy else "unhealthy"
                
                if not torchserve_healthy:
                    raise HTTPException(status_code=503, detail="TorchServe not healthy")
            except Exception as e:
                logger.error(f"TorchServe health check failed: {e}")
                status_details["torchserve"] = "unhealthy"
                raise HTTPException(status_code=503, detail="TorchServe not available")
        
        # All checks passed
        return {
            "status": "ready", 
            "service": "intent-classifier",
            "details": status_details,
            "mode": "torchserve" if settings.USE_TORCHSERVE else "local"
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