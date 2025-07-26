"""Feature flags API endpoints for managing rollout and experiments."""

from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.feature_flags import feature_flags
from app.core.logging import setup_logging

router = APIRouter()
logger = setup_logging()


class FeatureFlagUpdate(BaseModel):
    """Feature flag update request."""
    enabled: Optional[bool] = None
    rollout_percentage: Optional[int] = None


@router.get("/feature-flags", response_model=Dict[str, Any])
async def get_feature_flags() -> Dict[str, Any]:
    """Get all feature flags and their configurations."""
    return {
        "flags": feature_flags.get_all_flags(),
        "metrics": feature_flags.get_flag_metrics()
    }


@router.get("/feature-flags/{flag_name}", response_model=Dict[str, Any])
async def get_feature_flag(flag_name: str) -> Dict[str, Any]:
    """Get a specific feature flag configuration."""
    flags = feature_flags.get_all_flags()
    
    if flag_name not in flags:
        raise HTTPException(status_code=404, detail=f"Feature flag '{flag_name}' not found")
    
    return {
        "name": flag_name,
        "config": flags[flag_name]
    }


@router.get("/feature-flags/check/{flag_name}", response_model=Dict[str, bool])
async def check_feature_flag(
    flag_name: str,
    user_id: Optional[str] = Query(None, description="User ID for consistent rollout")
) -> Dict[str, bool]:
    """Check if a feature flag is enabled for a specific user."""
    is_enabled = feature_flags.is_enabled(flag_name, user_id)
    
    return {
        "enabled": is_enabled,
        "user_id": user_id
    }


@router.get("/feature-flags/user/{user_id}", response_model=Dict[str, Any])
async def get_user_feature_flags(user_id: str) -> Dict[str, Any]:
    """Get all feature flag states for a specific user."""
    flags = feature_flags.get_user_flags(user_id)
    
    return {
        "user_id": user_id,
        "flags": flags
    }


@router.put("/feature-flags/{flag_name}", response_model=Dict[str, Any])
async def update_feature_flag(
    flag_name: str,
    update: FeatureFlagUpdate
) -> Dict[str, Any]:
    """Update a feature flag configuration."""
    success = feature_flags.update_flag(
        flag_name,
        enabled=update.enabled,
        rollout_percentage=update.rollout_percentage
    )
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Feature flag '{flag_name}' not found")
    
    # Get updated flag config
    flags = feature_flags.get_all_flags()
    
    return {
        "status": "updated",
        "name": flag_name,
        "config": flags[flag_name]
    }


@router.post("/feature-flags/refresh", response_model=Dict[str, str])
async def refresh_feature_flags() -> Dict[str, str]:
    """Refresh feature flags from configuration sources."""
    try:
        # Reinitialize to reload from env and config
        feature_flags.__init__()
        
        return {
            "status": "success",
            "message": "Feature flags refreshed from configuration"
        }
    except Exception as e:
        logger.error(f"Failed to refresh feature flags: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh feature flags")