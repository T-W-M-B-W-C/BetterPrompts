#!/usr/bin/env python3
"""
Model Packaging Script for TorchServe
Handles model archiving, versioning, and deployment preparation
"""

import argparse
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

import yaml
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelPackager:
    """Handles model packaging for TorchServe deployment."""
    
    def __init__(self, config_path: str):
        """Initialize with configuration."""
        self.config = self._load_config(config_path)
        self.model_dir = Path(self.config['paths']['model_dir'])
        self.archive_dir = Path(self.config['paths']['archive_dir'])
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def package_intent_classifier(
        self,
        model_path: str,
        version: str,
        handler_path: str,
        extra_files: Optional[list] = None
    ) -> str:
        """
        Package Intent Classifier model for TorchServe.
        
        Args:
            model_path: Path to trained model directory
            version: Model version
            handler_path: Path to custom handler
            extra_files: Additional files to include
            
        Returns:
            Path to created MAR file
        """
        logger.info(f"Packaging Intent Classifier model version {version}")
        
        # Create temporary directory for model artifacts
        temp_dir = Path(f"/tmp/model_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Load model and tokenizer
            logger.info("Loading model and tokenizer...")
            model = AutoModelForSequenceClassification.from_pretrained(model_path)
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            
            # Save model in TorchServe format
            model_save_path = temp_dir / "model"
            model_save_path.mkdir(exist_ok=True)
            
            # Save PyTorch model
            torch.save({
                'model_state_dict': model.state_dict(),
                'config': model.config.to_dict(),
                'intent_labels': self.config['model']['intent_labels'],
                'version': version
            }, model_save_path / "model.pt")
            
            # Save tokenizer
            tokenizer_path = model_save_path / "tokenizer"
            tokenizer.save_pretrained(tokenizer_path)
            
            # Create model config
            model_config = {
                "model_name": "intent_classifier",
                "version": version,
                "model_type": "transformers",
                "num_labels": len(self.config['model']['intent_labels']),
                "max_length": self.config['model']['max_length'],
                "created_at": datetime.now().isoformat(),
                "framework": "pytorch",
                "handler": "intent_classifier_handler.py"
            }
            
            with open(model_save_path / "config.json", 'w') as f:
                json.dump(model_config, f, indent=2)
            
            # Create MAR archive
            mar_name = f"intent_classifier_v{version}.mar"
            mar_path = self.archive_dir / mar_name
            
            # Prepare torch-model-archiver command
            cmd = [
                "torch-model-archiver",
                "--model-name", "intent_classifier",
                "--version", version,
                "--serialized-file", str(model_save_path / "model.pt"),
                "--handler", handler_path,
                "--extra-files", f"{model_save_path}/tokenizer,{model_save_path}/config.json",
                "--export-path", str(self.archive_dir),
                "--force"
            ]
            
            if extra_files:
                extra_files_str = ",".join(extra_files)
                cmd.extend(["--extra-files", extra_files_str])
            
            logger.info(f"Creating MAR archive: {mar_name}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"Model archiver failed: {result.stderr}")
            
            # Generate model metadata
            self._generate_metadata(mar_path, model_config)
            
            logger.info(f"Successfully created model archive: {mar_path}")
            return str(mar_path)
            
        finally:
            # Cleanup temporary directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def _generate_metadata(self, mar_path: Path, model_config: Dict[str, Any]):
        """Generate metadata for model archive."""
        # Calculate checksum
        sha256_hash = hashlib.sha256()
        with open(mar_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        metadata = {
            "model_name": model_config["model_name"],
            "version": model_config["version"],
            "created_at": model_config["created_at"],
            "file_size": os.path.getsize(mar_path),
            "sha256": sha256_hash.hexdigest(),
            "framework": model_config["framework"],
            "handler": model_config["handler"],
            "requirements": self._get_requirements()
        }
        
        metadata_path = mar_path.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Generated metadata: {metadata_path}")
    
    def _get_requirements(self) -> Dict[str, str]:
        """Get current package requirements."""
        return {
            "torch": torch.__version__,
            "transformers": "4.35.2",
            "torchserve": "0.9.0"
        }
    
    def validate_model(self, mar_path: str) -> bool:
        """Validate model archive."""
        logger.info(f"Validating model archive: {mar_path}")
        
        # Check if file exists
        if not os.path.exists(mar_path):
            logger.error(f"Model archive not found: {mar_path}")
            return False
        
        # Check file size
        file_size = os.path.getsize(mar_path)
        if file_size < 1024 * 1024:  # Less than 1MB
            logger.error(f"Model archive too small: {file_size} bytes")
            return False
        
        logger.info("Model validation passed")
        return True
    
    def deploy_to_model_store(self, mar_path: str, model_store_path: str):
        """Deploy model to TorchServe model store."""
        logger.info(f"Deploying model to store: {model_store_path}")
        
        model_store = Path(model_store_path)
        model_store.mkdir(parents=True, exist_ok=True)
        
        # Copy MAR file
        mar_filename = Path(mar_path).name
        destination = model_store / mar_filename
        shutil.copy2(mar_path, destination)
        
        # Copy metadata
        metadata_path = Path(mar_path).with_suffix('.json')
        if metadata_path.exists():
            shutil.copy2(metadata_path, model_store / metadata_path.name)
        
        logger.info(f"Model deployed to: {destination}")
        
        # Create version symlink for latest
        latest_link = model_store / "intent_classifier_latest.mar"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(mar_filename)
        
        logger.info("Updated latest version symlink")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Package models for TorchServe")
    parser.add_argument(
        "--config",
        default="configs/model_packaging.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--model-path",
        required=True,
        help="Path to trained model directory"
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Model version (e.g., 1.0.0)"
    )
    parser.add_argument(
        "--handler",
        default="torchserve/handlers/intent_classifier_handler.py",
        help="Path to custom handler"
    )
    parser.add_argument(
        "--model-store",
        default="torchserve/model-store",
        help="Path to model store directory"
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Deploy to model store after packaging"
    )
    
    args = parser.parse_args()
    
    # Create packager
    packager = ModelPackager(args.config)
    
    # Package model
    mar_path = packager.package_intent_classifier(
        model_path=args.model_path,
        version=args.version,
        handler_path=args.handler
    )
    
    # Validate
    if not packager.validate_model(mar_path):
        logger.error("Model validation failed")
        sys.exit(1)
    
    # Deploy if requested
    if args.deploy:
        packager.deploy_to_model_store(mar_path, args.model_store)
    
    logger.info("Model packaging completed successfully")


if __name__ == "__main__":
    main()