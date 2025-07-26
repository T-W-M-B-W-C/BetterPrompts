"""Feature flag system for gradual rollout and A/B testing."""

import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime
import os

from app.core.logging import setup_logging
from app.core.config import settings

logger = setup_logging()


class FeatureFlags:
    """Manage feature flags for the intent classifier service."""
    
    def __init__(self):
        """Initialize feature flags from environment or config."""
        self.flags = {
            "adaptive_routing": {
                "enabled": settings.ENABLE_ADAPTIVE_ROUTING if hasattr(settings, 'ENABLE_ADAPTIVE_ROUTING') else False,
                "rollout_percentage": 100,  # Percentage of users who get this feature
                "description": "Enable Wave 6 adaptive multi-model routing"
            },
            "ab_testing": {
                "enabled": True,
                "rollout_percentage": settings.AB_TEST_PERCENTAGE * 100 if hasattr(settings, 'AB_TEST_PERCENTAGE') else 10,
                "description": "Enable A/B testing for routing strategies"
            },
            "distilbert_model": {
                "enabled": settings.USE_TORCHSERVE if hasattr(settings, 'USE_TORCHSERVE') else False,
                "rollout_percentage": 100,
                "description": "Enable DistilBERT model via TorchServe"
            },
            "zero_shot_fallback": {
                "enabled": True,
                "rollout_percentage": 100,
                "description": "Enable zero-shot classification as fallback"
            },
            "caching": {
                "enabled": settings.ENABLE_CACHING if hasattr(settings, 'ENABLE_CACHING') else True,
                "rollout_percentage": 100,
                "description": "Enable Redis caching for classification results"
            },
            "feedback_learning": {
                "enabled": True,
                "rollout_percentage": 100,
                "description": "Enable user feedback collection and learning"
            },
            "performance_mode": {
                "enabled": False,
                "rollout_percentage": 20,
                "description": "Prioritize speed over accuracy (rules-first mode)"
            },
            "quality_mode": {
                "enabled": False,
                "rollout_percentage": 10,
                "description": "Prioritize accuracy over speed (DistilBERT-first mode)"
            },
            "enhanced_logging": {
                "enabled": settings.DEBUG if hasattr(settings, 'DEBUG') else False,
                "rollout_percentage": 100,
                "description": "Enable detailed logging for debugging"
            }
        }
        
        # Load overrides from environment
        self._load_env_overrides()
        
        # Load from config file if exists
        self._load_config_file()
        
        logger.info(f"Feature flags initialized: {self._get_enabled_flags()}")
    
    def _load_env_overrides(self):
        """Load feature flag overrides from environment variables."""
        # Pattern: FEATURE_FLAG_<FLAG_NAME>_ENABLED=true/false
        # Pattern: FEATURE_FLAG_<FLAG_NAME>_ROLLOUT=50
        
        for flag_name in self.flags:
            env_key_enabled = f"FEATURE_FLAG_{flag_name.upper()}_ENABLED"
            env_key_rollout = f"FEATURE_FLAG_{flag_name.upper()}_ROLLOUT"
            
            # Check for enabled override
            if env_key_enabled in os.environ:
                value = os.environ[env_key_enabled].lower()
                self.flags[flag_name]["enabled"] = value in ("true", "1", "yes", "on")
                logger.info(f"Feature flag {flag_name} enabled override: {self.flags[flag_name]['enabled']}")
            
            # Check for rollout percentage override
            if env_key_rollout in os.environ:
                try:
                    rollout = int(os.environ[env_key_rollout])
                    self.flags[flag_name]["rollout_percentage"] = max(0, min(100, rollout))
                    logger.info(f"Feature flag {flag_name} rollout override: {self.flags[flag_name]['rollout_percentage']}%")
                except ValueError:
                    logger.error(f"Invalid rollout percentage for {flag_name}: {os.environ[env_key_rollout]}")
    
    def _load_config_file(self):
        """Load feature flags from config file if exists."""
        config_path = os.path.join(os.path.dirname(__file__), "feature_flags.json")
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                
                for flag_name, flag_config in config.items():
                    if flag_name in self.flags:
                        self.flags[flag_name].update(flag_config)
                        logger.info(f"Loaded config for feature flag {flag_name}")
                    else:
                        logger.warning(f"Unknown feature flag in config: {flag_name}")
            except Exception as e:
                logger.error(f"Failed to load feature flags config: {e}")
    
    def _get_enabled_flags(self) -> list:
        """Get list of enabled feature flags."""
        return [name for name, config in self.flags.items() if config["enabled"]]
    
    def is_enabled(self, flag_name: str, user_id: Optional[str] = None) -> bool:
        """Check if a feature flag is enabled for a user.
        
        Args:
            flag_name: Name of the feature flag
            user_id: Optional user ID for consistent rollout
            
        Returns:
            True if feature is enabled for this user
        """
        if flag_name not in self.flags:
            logger.warning(f"Unknown feature flag: {flag_name}")
            return False
        
        flag = self.flags[flag_name]
        
        # Check if globally enabled
        if not flag["enabled"]:
            return False
        
        # Check rollout percentage
        rollout = flag["rollout_percentage"]
        if rollout >= 100:
            return True
        if rollout <= 0:
            return False
        
        # Consistent rollout based on user ID
        if user_id:
            # Hash user ID to get consistent assignment
            hash_value = int(hashlib.md5(f"{flag_name}:{user_id}".encode()).hexdigest(), 16)
            user_percentage = hash_value % 100
            return user_percentage < rollout
        else:
            # Random rollout for anonymous users
            import random
            return random.randint(0, 99) < rollout
    
    def get_all_flags(self) -> Dict[str, Dict[str, Any]]:
        """Get all feature flags and their configurations."""
        return self.flags.copy()
    
    def get_user_flags(self, user_id: Optional[str] = None) -> Dict[str, bool]:
        """Get feature flag states for a specific user."""
        return {
            flag_name: self.is_enabled(flag_name, user_id)
            for flag_name in self.flags
        }
    
    def update_flag(self, flag_name: str, enabled: Optional[bool] = None, 
                   rollout_percentage: Optional[int] = None) -> bool:
        """Update a feature flag configuration.
        
        Args:
            flag_name: Name of the feature flag
            enabled: Whether to enable/disable the flag
            rollout_percentage: Rollout percentage (0-100)
            
        Returns:
            True if update was successful
        """
        if flag_name not in self.flags:
            logger.error(f"Cannot update unknown feature flag: {flag_name}")
            return False
        
        if enabled is not None:
            self.flags[flag_name]["enabled"] = enabled
            logger.info(f"Updated feature flag {flag_name} enabled: {enabled}")
        
        if rollout_percentage is not None:
            self.flags[flag_name]["rollout_percentage"] = max(0, min(100, rollout_percentage))
            logger.info(f"Updated feature flag {flag_name} rollout: {rollout_percentage}%")
        
        return True
    
    def get_flag_metrics(self) -> Dict[str, Any]:
        """Get metrics about feature flag usage."""
        total_flags = len(self.flags)
        enabled_flags = len(self._get_enabled_flags())
        
        rollout_stats = {
            "full": 0,  # 100% rollout
            "partial": 0,  # 1-99% rollout
            "none": 0  # 0% rollout
        }
        
        for flag in self.flags.values():
            if not flag["enabled"]:
                continue
                
            rollout = flag["rollout_percentage"]
            if rollout >= 100:
                rollout_stats["full"] += 1
            elif rollout > 0:
                rollout_stats["partial"] += 1
            else:
                rollout_stats["none"] += 1
        
        return {
            "total_flags": total_flags,
            "enabled_flags": enabled_flags,
            "disabled_flags": total_flags - enabled_flags,
            "rollout_distribution": rollout_stats,
            "flags": self._get_enabled_flags()
        }


# Global feature flags instance
feature_flags = FeatureFlags()