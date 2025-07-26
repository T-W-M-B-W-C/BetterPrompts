"""Monitoring middleware for production deployment."""

import time
import uuid
from typing import Callable
from prometheus_client import Counter, Histogram, Gauge
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import setup_logging

logger = setup_logging()

# Prometheus metrics
request_count = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"]
)

request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

active_requests = Gauge(
    "http_requests_active",
    "Number of active HTTP requests"
)

model_selection_count = Counter(
    "model_selection_total",
    "Model selection counts by routing decision",
    ["model", "reason"]
)

feature_flag_usage = Counter(
    "feature_flag_usage_total",
    "Feature flag usage counts",
    ["flag_name", "enabled"]
)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request monitoring."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with monitoring."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Track active requests
        active_requests.inc()
        
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else "unknown"
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            request_count.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
            
            request_duration.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_seconds": duration
                }
            )
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(duration)
            
            return response
            
        except Exception as e:
            # Log error
            logger.error(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e)
                },
                exc_info=True
            )
            
            # Record error metric
            request_count.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500
            ).inc()
            
            # Re-raise exception
            raise
            
        finally:
            # Decrement active requests
            active_requests.dec()


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware to skip logging for health check endpoints."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Skip logging for health checks to reduce noise."""
        # Skip logging for health endpoints
        if request.url.path in ["/health", "/health/ready", "/health/live"]:
            return await call_next(request)
        
        # Use monitoring middleware for other endpoints
        return await MonitoringMiddleware().dispatch(request, call_next)