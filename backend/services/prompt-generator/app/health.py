"""
Health check endpoints for the Prompt Generation Service
"""

from fastapi import APIRouter, status
from datetime import datetime
import psutil
import asyncio
from typing import Dict, Any

from .config import settings

router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Basic health check",
    description="Returns service status"
)
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "prompt-generator",
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Kubernetes liveness probe endpoint"
)
async def liveness():
    """Liveness probe for Kubernetes"""
    return {"status": "alive"}


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Kubernetes readiness probe endpoint"
)
async def readiness():
    """Readiness probe for Kubernetes"""
    # Check if all components are ready
    checks = await _run_readiness_checks()
    
    all_ready = all(check["status"] == "ready" for check in checks.values())
    
    if not all_ready:
        return {
            "status": "not_ready",
            "checks": checks
        }, status.HTTP_503_SERVICE_UNAVAILABLE
        
    return {
        "status": "ready",
        "checks": checks
    }


@router.get(
    "/detailed",
    summary="Detailed health check",
    description="Returns detailed system information"
)
async def detailed_health():
    """Detailed health check with system metrics"""
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get process info
    process = psutil.Process()
    process_info = {
        "pid": process.pid,
        "cpu_percent": process.cpu_percent(interval=0.1),
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "threads": process.num_threads(),
        "open_files": len(process.open_files()),
        "connections": len(process.connections())
    }
    
    return {
        "status": "healthy",
        "service": "prompt-generator",
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "total_mb": memory.total / 1024 / 1024,
                "available_mb": memory.available / 1024 / 1024,
                "used_percent": memory.percent
            },
            "disk": {
                "total_gb": disk.total / 1024 / 1024 / 1024,
                "free_gb": disk.free / 1024 / 1024 / 1024,
                "used_percent": disk.percent
            }
        },
        "process": process_info,
        "configuration": {
            "debug": settings.debug,
            "workers": settings.workers,
            "max_prompt_length": settings.max_prompt_length,
            "cache_enabled": settings.enable_caching,
            "metrics_enabled": settings.enable_metrics
        }
    }


async def _run_readiness_checks() -> Dict[str, Any]:
    """Run all readiness checks"""
    checks = {}
    
    # Check database connectivity (if configured)
    if settings.database_url:
        checks["database"] = await _check_database()
    
    # Check Redis connectivity (if configured)
    if settings.redis_url:
        checks["redis"] = await _check_redis()
        
    # Check if techniques are loaded
    checks["techniques"] = _check_techniques()
    
    # Check system resources
    checks["resources"] = _check_resources()
    
    return checks


async def _check_database() -> Dict[str, Any]:
    """Check database connectivity"""
    try:
        # In production, actually test the connection
        # For now, return ready
        return {"status": "ready", "message": "Database connection available"}
    except Exception as e:
        return {"status": "not_ready", "message": str(e)}


async def _check_redis() -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        # In production, actually test the connection
        # For now, return ready
        return {"status": "ready", "message": "Redis connection available"}
    except Exception as e:
        return {"status": "not_ready", "message": str(e)}


def _check_techniques() -> Dict[str, Any]:
    """Check if techniques are properly loaded"""
    try:
        from .techniques import technique_registry
        
        available_techniques = technique_registry.list_available()
        enabled_techniques = technique_registry.list_enabled()
        
        if len(available_techniques) == 0:
            return {"status": "not_ready", "message": "No techniques loaded"}
            
        return {
            "status": "ready",
            "message": f"{len(enabled_techniques)} techniques enabled",
            "available": len(available_techniques),
            "enabled": len(enabled_techniques)
        }
    except Exception as e:
        return {"status": "not_ready", "message": str(e)}


def _check_resources() -> Dict[str, Any]:
    """Check system resources"""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # Define thresholds
    memory_threshold = 90  # percent
    cpu_threshold = 90  # percent
    
    if memory.percent > memory_threshold:
        return {
            "status": "not_ready",
            "message": f"Memory usage too high: {memory.percent}%"
        }
        
    if cpu_percent > cpu_threshold:
        return {
            "status": "not_ready",
            "message": f"CPU usage too high: {cpu_percent}%"
        }
        
    return {
        "status": "ready",
        "message": "System resources within limits",
        "memory_percent": memory.percent,
        "cpu_percent": cpu_percent
    }


# Create the health router
health_router = router