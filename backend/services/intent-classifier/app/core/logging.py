"""Logging configuration for the Intent Classification Service."""

import logging
import sys
from typing import Any, Dict

from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Set up logging configuration."""
    # Create logger
    logger = logging.getLogger("intent_classifier")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def log_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Create a structured log entry for requests."""
    return {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        **kwargs,
    }