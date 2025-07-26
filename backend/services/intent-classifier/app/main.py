"""Main FastAPI application for Intent Classification Service."""

from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.v1 import health, intents, feature_flags
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.database import engine
from app.models import classifier

# Set up logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifecycle events."""
    # Startup
    logger.info("Starting Intent Classification Service...")
    
    # Initialize ML model
    await classifier.initialize_model()
    logger.info("ML model loaded successfully")
    
    # Create database tables
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Intent Classification Service...")
    await classifier.cleanup()


# Create FastAPI app
app = FastAPI(
    title="Intent Classification Service",
    description="Analyzes user input to identify task type and complexity",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add monitoring middleware
from app.middleware.monitoring import HealthCheckMiddleware
app.add_middleware(HealthCheckMiddleware)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(intents.router, prefix="/api/v1", tags=["intents"])
app.include_router(feature_flags.router, prefix="/api/v1", tags=["feature-flags"])


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Intent Classification Service",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
    }