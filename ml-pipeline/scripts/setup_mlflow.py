#!/usr/bin/env python3
"""
Setup MLflow tracking server and experiment structure
"""

import os
import sys
import logging
import mlflow
from pathlib import Path
import yaml
import click

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def setup_mlflow_experiment(config: dict):
    """Setup MLflow experiment structure"""
    # Set tracking URI
    mlflow.set_tracking_uri(config['mlflow']['tracking_uri'])
    
    # Create experiment if it doesn't exist
    experiment_name = config['mlflow']['experiment_name']
    experiment = mlflow.get_experiment_by_name(experiment_name)
    
    if experiment is None:
        experiment_id = mlflow.create_experiment(
            experiment_name,
            artifact_location=str(Path(config['paths']['artifacts_dir']).absolute()),
            tags={
                "project": config['project']['name'],
                "version": config['project']['version'],
                "description": config['project']['description']
            }
        )
        logger.info(f"Created experiment: {experiment_name} (ID: {experiment_id})")
    else:
        logger.info(f"Experiment already exists: {experiment_name} (ID: {experiment.experiment_id})")
    
    return experiment_name


def create_model_registry(config: dict):
    """Initialize model registry"""
    mlflow.set_registry_uri(config['mlflow']['registry_uri'])
    
    # Register model schemas
    model_schemas = {
        "intent_classifier": {
            "description": "DeBERTa-v3 based intent classification model",
            "tags": {
                "framework": "pytorch",
                "task": "classification",
                "base_model": "deberta-v3"
            }
        },
        "complexity_analyzer": {
            "description": "Prompt complexity analysis model",
            "tags": {
                "framework": "pytorch",
                "task": "regression",
                "base_model": "deberta-v3"
            }
        }
    }
    
    for model_name, schema in model_schemas.items():
        try:
            # Check if model already exists
            client = mlflow.MlflowClient()
            registered_models = [m.name for m in client.search_registered_models()]
            
            if model_name not in registered_models:
                client.create_registered_model(
                    name=model_name,
                    tags=schema['tags'],
                    description=schema['description']
                )
                logger.info(f"Registered model: {model_name}")
            else:
                logger.info(f"Model already registered: {model_name}")
                
        except Exception as e:
            logger.error(f"Error registering model {model_name}: {e}")


def setup_tracking_tags(config: dict):
    """Setup default tracking tags"""
    tags = {
        "mlflow.note.content": f"BetterPrompts ML Pipeline v{config['project']['version']}",
        "mlflow.source.git.repoURL": "https://github.com/betterprompts/ml-pipeline",
        "mlflow.source.type": "PROJECT",
        "environment": "development"
    }
    
    # Save default tags
    tags_path = Path(config['paths']['artifacts_dir']) / "mlflow_tags.yaml"
    tags_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(tags_path, 'w') as f:
        yaml.dump(tags, f)
    
    logger.info(f"Saved default MLflow tags to: {tags_path}")


@click.command()
@click.option('--config', default='configs/ml_pipeline_config.yaml', help='Path to configuration file')
@click.option('--reset', is_flag=True, help='Reset MLflow database')
def main(config: str, reset: bool):
    """Setup MLflow for BetterPrompts ML Pipeline"""
    # Load configuration
    config_data = load_config(config)
    
    # Create necessary directories
    for path_key, path_value in config_data['paths'].items():
        Path(path_value).mkdir(parents=True, exist_ok=True)
    
    # Reset if requested
    if reset:
        db_path = config_data['mlflow']['tracking_uri'].replace('sqlite:///', '')
        if os.path.exists(db_path):
            os.remove(db_path)
            logger.info(f"Removed existing MLflow database: {db_path}")
        
        registry_path = config_data['mlflow']['registry_uri'].replace('sqlite:///', '')
        if os.path.exists(registry_path):
            os.remove(registry_path)
            logger.info(f"Removed existing model registry: {registry_path}")
    
    # Setup experiment
    experiment_name = setup_mlflow_experiment(config_data)
    logger.info(f"MLflow experiment ready: {experiment_name}")
    
    # Setup model registry
    create_model_registry(config_data)
    logger.info("Model registry initialized")
    
    # Setup tracking tags
    setup_tracking_tags(config_data)
    
    logger.info("MLflow setup complete!")
    logger.info(f"Start MLflow UI with: mlflow ui --backend-store-uri {config_data['mlflow']['tracking_uri']}")


if __name__ == "__main__":
    main()