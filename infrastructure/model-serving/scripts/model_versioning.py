#!/usr/bin/env python3
"""
Model Versioning and Registry Management
Handles model versioning, metadata tracking, and deployment lifecycle
"""

import json
import logging
import os
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError
import yaml

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Model deployment status."""
    TRAINING = "training"
    VALIDATION = "validation"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ModelVersion:
    """Represents a model version with semantic versioning."""
    
    def __init__(self, version_string: str):
        """Initialize from version string (e.g., '1.2.3')."""
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$', version_string)
        if not match:
            raise ValueError(f"Invalid version format: {version_string}")
        
        self.major = int(match.group(1))
        self.minor = int(match.group(2))
        self.patch = int(match.group(3))
        self.prerelease = match.group(4) or ""
    
    def __str__(self) -> str:
        """String representation."""
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base += f"-{self.prerelease}"
        return base
    
    def __lt__(self, other: 'ModelVersion') -> bool:
        """Compare versions for sorting."""
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def bump_major(self) -> 'ModelVersion':
        """Increment major version."""
        return ModelVersion(f"{self.major + 1}.0.0")
    
    def bump_minor(self) -> 'ModelVersion':
        """Increment minor version."""
        return ModelVersion(f"{self.major}.{self.minor + 1}.0")
    
    def bump_patch(self) -> 'ModelVersion':
        """Increment patch version."""
        return ModelVersion(f"{self.major}.{self.minor}.{self.patch + 1}")


class ModelRegistry:
    """Manages model versions and deployment lifecycle."""
    
    def __init__(self, config_path: str):
        """Initialize registry with configuration."""
        self.config = self._load_config(config_path)
        self.registry_path = Path(self.config['registry']['local_path'])
        self.registry_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize S3 client if configured
        self.s3_client = None
        if self.config['registry'].get('s3_bucket'):
            self.s3_client = boto3.client('s3')
            self.s3_bucket = self.config['registry']['s3_bucket']
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def register_model(
        self,
        model_name: str,
        version: str,
        model_path: str,
        metadata: Dict,
        status: ModelStatus = ModelStatus.VALIDATION
    ) -> Dict:
        """
        Register a new model version.
        
        Args:
            model_name: Name of the model
            version: Version string
            model_path: Path to model archive
            metadata: Model metadata
            status: Initial status
            
        Returns:
            Registration record
        """
        logger.info(f"Registering model: {model_name} v{version}")
        
        # Validate version
        model_version = ModelVersion(version)
        
        # Create registration record
        record = {
            "model_name": model_name,
            "version": str(model_version),
            "status": status.value,
            "registered_at": datetime.now().isoformat(),
            "model_path": model_path,
            "metadata": metadata,
            "deployment_history": [],
            "metrics": {},
            "tags": {}
        }
        
        # Save to local registry
        registry_file = self.registry_path / f"{model_name}_v{version}.json"
        with open(registry_file, 'w') as f:
            json.dump(record, f, indent=2)
        
        # Upload to S3 if configured
        if self.s3_client:
            self._upload_to_s3(registry_file, f"registry/{model_name}/v{version}/metadata.json")
            self._upload_to_s3(model_path, f"models/{model_name}/v{version}/{Path(model_path).name}")
        
        logger.info(f"Model registered successfully: {registry_file}")
        return record
    
    def promote_model(
        self,
        model_name: str,
        version: str,
        target_status: ModelStatus,
        reason: str
    ) -> bool:
        """
        Promote model to a new status.
        
        Args:
            model_name: Model name
            version: Version to promote
            target_status: Target status
            reason: Reason for promotion
            
        Returns:
            Success status
        """
        logger.info(f"Promoting {model_name} v{version} to {target_status.value}")
        
        # Load current record
        record = self.get_model_record(model_name, version)
        if not record:
            logger.error(f"Model not found: {model_name} v{version}")
            return False
        
        # Validate promotion path
        current_status = ModelStatus(record['status'])
        if not self._validate_promotion(current_status, target_status):
            logger.error(f"Invalid promotion: {current_status.value} -> {target_status.value}")
            return False
        
        # Update record
        record['status'] = target_status.value
        record['deployment_history'].append({
            "timestamp": datetime.now().isoformat(),
            "from_status": current_status.value,
            "to_status": target_status.value,
            "reason": reason
        })
        
        # Save updated record
        registry_file = self.registry_path / f"{model_name}_v{version}.json"
        with open(registry_file, 'w') as f:
            json.dump(record, f, indent=2)
        
        # Handle production promotion
        if target_status == ModelStatus.PRODUCTION:
            self._handle_production_promotion(model_name, version)
        
        logger.info(f"Model promoted successfully")
        return True
    
    def _validate_promotion(self, current: ModelStatus, target: ModelStatus) -> bool:
        """Validate promotion path."""
        valid_paths = {
            ModelStatus.TRAINING: [ModelStatus.VALIDATION],
            ModelStatus.VALIDATION: [ModelStatus.STAGING, ModelStatus.DEPRECATED],
            ModelStatus.STAGING: [ModelStatus.PRODUCTION, ModelStatus.VALIDATION, ModelStatus.DEPRECATED],
            ModelStatus.PRODUCTION: [ModelStatus.DEPRECATED, ModelStatus.ARCHIVED],
            ModelStatus.DEPRECATED: [ModelStatus.ARCHIVED]
        }
        
        return target in valid_paths.get(current, [])
    
    def _handle_production_promotion(self, model_name: str, version: str):
        """Handle special logic for production promotion."""
        # Find current production model
        current_prod = self.get_production_model(model_name)
        
        if current_prod and current_prod['version'] != version:
            # Demote current production model
            logger.info(f"Demoting current production model: v{current_prod['version']}")
            self.promote_model(
                model_name,
                current_prod['version'],
                ModelStatus.DEPRECATED,
                f"Replaced by v{version}"
            )
        
        # Create production symlink
        prod_link = self.registry_path / f"{model_name}_production.json"
        if prod_link.exists():
            prod_link.unlink()
        
        registry_file = self.registry_path / f"{model_name}_v{version}.json"
        prod_link.symlink_to(registry_file.name)
    
    def get_model_record(self, model_name: str, version: str) -> Optional[Dict]:
        """Get model registration record."""
        registry_file = self.registry_path / f"{model_name}_v{version}.json"
        
        if not registry_file.exists():
            return None
        
        with open(registry_file, 'r') as f:
            return json.load(f)
    
    def get_production_model(self, model_name: str) -> Optional[Dict]:
        """Get current production model."""
        prod_link = self.registry_path / f"{model_name}_production.json"
        
        if prod_link.exists() and prod_link.is_symlink():
            with open(prod_link, 'r') as f:
                return json.load(f)
        
        # Fallback: search for production status
        for file in self.registry_path.glob(f"{model_name}_v*.json"):
            with open(file, 'r') as f:
                record = json.load(f)
                if record['status'] == ModelStatus.PRODUCTION.value:
                    return record
        
        return None
    
    def list_models(self, model_name: str, status: Optional[ModelStatus] = None) -> List[Dict]:
        """List all versions of a model."""
        models = []
        
        for file in self.registry_path.glob(f"{model_name}_v*.json"):
            with open(file, 'r') as f:
                record = json.load(f)
                
                if status is None or record['status'] == status.value:
                    models.append(record)
        
        # Sort by version
        models.sort(key=lambda x: ModelVersion(x['version']), reverse=True)
        return models
    
    def update_metrics(self, model_name: str, version: str, metrics: Dict):
        """Update model metrics."""
        record = self.get_model_record(model_name, version)
        if not record:
            logger.error(f"Model not found: {model_name} v{version}")
            return
        
        # Update metrics
        record['metrics'].update(metrics)
        record['metrics']['last_updated'] = datetime.now().isoformat()
        
        # Save updated record
        registry_file = self.registry_path / f"{model_name}_v{version}.json"
        with open(registry_file, 'w') as f:
            json.dump(record, f, indent=2)
    
    def cleanup_old_versions(self, model_name: str, keep_count: int = 5):
        """Clean up old model versions."""
        models = self.list_models(model_name)
        
        # Group by status
        by_status = {}
        for model in models:
            status = model['status']
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(model)
        
        # Keep production and staging
        protected_statuses = [ModelStatus.PRODUCTION.value, ModelStatus.STAGING.value]
        
        # Find candidates for cleanup
        cleanup_candidates = []
        for status, models in by_status.items():
            if status not in protected_statuses:
                # Keep only the latest N versions
                if len(models) > keep_count:
                    cleanup_candidates.extend(models[keep_count:])
        
        # Archive old versions
        for model in cleanup_candidates:
            logger.info(f"Archiving old version: {model['model_name']} v{model['version']}")
            self.promote_model(
                model['model_name'],
                model['version'],
                ModelStatus.ARCHIVED,
                "Automated cleanup"
            )
    
    def _upload_to_s3(self, local_path: str, s3_key: str):
        """Upload file to S3."""
        try:
            self.s3_client.upload_file(local_path, self.s3_bucket, s3_key)
            logger.info(f"Uploaded to S3: s3://{self.s3_bucket}/{s3_key}")
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")


def main():
    """CLI for model registry operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Model Registry Management")
    parser.add_argument("--config", default="configs/model_registry.yaml")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Register command
    register_parser = subparsers.add_parser("register", help="Register a model")
    register_parser.add_argument("--name", required=True)
    register_parser.add_argument("--version", required=True)
    register_parser.add_argument("--path", required=True)
    register_parser.add_argument("--metadata", type=json.loads, default={})
    
    # Promote command
    promote_parser = subparsers.add_parser("promote", help="Promote a model")
    promote_parser.add_argument("--name", required=True)
    promote_parser.add_argument("--version", required=True)
    promote_parser.add_argument("--to", required=True, choices=[s.value for s in ModelStatus])
    promote_parser.add_argument("--reason", required=True)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List models")
    list_parser.add_argument("--name", required=True)
    list_parser.add_argument("--status", choices=[s.value for s in ModelStatus])
    
    args = parser.parse_args()
    
    # Initialize registry
    registry = ModelRegistry(args.config)
    
    # Execute command
    if args.command == "register":
        registry.register_model(
            args.name,
            args.version,
            args.path,
            args.metadata
        )
    elif args.command == "promote":
        registry.promote_model(
            args.name,
            args.version,
            ModelStatus(args.to),
            args.reason
        )
    elif args.command == "list":
        models = registry.list_models(
            args.name,
            ModelStatus(args.status) if args.status else None
        )
        for model in models:
            print(f"{model['version']} - {model['status']} - {model['registered_at']}")


if __name__ == "__main__":
    main()