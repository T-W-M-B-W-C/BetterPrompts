"""Health check endpoints."""

from typing import Dict

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db.database import get_db
from app.core.logging import setup_logging

router = APIRouter()
logger = setup_logging()


@router.get("/health", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "intent-classifier"}


@router.get("/health/ready", response_model=Dict[str, str])
async def readiness_check() -> Dict[str, str]:
    """Readiness check including database and model status."""
    try:
        # Check database connection
        async for db in get_db():
            await db.execute(text("SELECT 1"))
        
        # Check if model is loaded
        from app.models import classifier
        if not classifier.is_initialized():
            raise HTTPException(status_code=503, detail="Model not initialized")
        
        return {"status": "ready", "service": "intent-classifier"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/health/live", response_model=Dict[str, str])
async def liveness_check() -> Dict[str, str]:
    """Liveness check for Kubernetes."""
    return {"status": "alive", "service": "intent-classifier"}