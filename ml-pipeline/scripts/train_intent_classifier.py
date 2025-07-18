#!/usr/bin/env python3
"""
Main script to train the intent classification model
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data.data_processor import DataProcessor
from src.models.train import Trainer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if the environment is properly set up"""
    import torch
    import transformers
    import mlflow
    
    logger.info("Environment check:")
    logger.info(f"  PyTorch version: {torch.__version__}")
    logger.info(f"  CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"  CUDA version: {torch.version.cuda}")
        logger.info(f"  GPU: {torch.cuda.get_device_name(0)}")
    logger.info(f"  Transformers version: {transformers.__version__}")
    logger.info(f"  MLflow version: {mlflow.__version__}")


def prepare_data(config_path: str, force_regenerate: bool = False):
    """Prepare training data"""
    config_dir = Path(config_path).parent
    raw_data_path = config_dir.parent / 'data' / 'raw' / 'training_data.json'
    processed_data_path = config_dir.parent / 'data' / 'processed'
    
    # Check if processed data exists
    if processed_data_path.exists() and not force_regenerate:
        logger.info(f"Processed data already exists at {processed_data_path}")
        return
    
    # Check if raw data exists
    if not raw_data_path.exists():
        logger.info("Raw data not found. Generating sample data...")
        # Generate sample data
        import subprocess
        subprocess.run([
            sys.executable,
            str(project_root / 'scripts' / 'generate_sample_data.py'),
            '--num-samples', '1000',
            '--output-path', str(raw_data_path),
            '--add-cross-intent'
        ], check=True)
    
    # Process data
    logger.info("Processing data...")
    processor = DataProcessor(config_path)
    processor.process_pipeline(
        input_path=str(raw_data_path),
        output_dir=str(processed_data_path)
    )
    logger.info("Data processing complete!")


def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description='Train BetterPrompts intent classification model')
    parser.add_argument(
        '--config',
        type=str,
        default='configs/ml_pipeline_config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--prepare-data',
        action='store_true',
        help='Prepare training data before training'
    )
    parser.add_argument(
        '--force-regenerate',
        action='store_true',
        help='Force regenerate processed data'
    )
    parser.add_argument(
        '--hyperparameter-search',
        action='store_true',
        help='Run hyperparameter search before training'
    )
    parser.add_argument(
        '--skip-env-check',
        action='store_true',
        help='Skip environment check'
    )
    parser.add_argument(
        '--experiment-name',
        type=str,
        help='MLflow experiment name (overrides config)'
    )
    parser.add_argument(
        '--run-name',
        type=str,
        help='MLflow run name'
    )
    
    args = parser.parse_args()
    
    # Change to project directory
    os.chdir(project_root)
    
    # Check environment
    if not args.skip_env_check:
        check_environment()
    
    # Prepare data if requested
    if args.prepare_data:
        prepare_data(args.config, args.force_regenerate)
    
    # Set up MLflow
    if args.experiment_name:
        import mlflow
        import yaml
        
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
        
        mlflow.set_tracking_uri(config['mlflow']['tracking_uri'])
        mlflow.set_experiment(args.experiment_name)
    
    # Initialize trainer
    logger.info("Initializing trainer...")
    trainer = Trainer(args.config)
    
    # Run training
    logger.info("Starting training...")
    if args.hyperparameter_search:
        # Run hyperparameter search
        logger.info("Running hyperparameter search...")
        best_params = trainer.hyperparameter_search()
        
        # Train final model with best parameters
        logger.info("Training final model with best parameters...")
        import mlflow
        with mlflow.start_run(run_name=args.run_name or "final_model"):
            mlflow.log_params(best_params)
            trainer.train()
    else:
        # Train with default parameters
        import mlflow
        with mlflow.start_run(run_name=args.run_name):
            trainer.train()
    
    logger.info("Training complete!")
    
    # Print MLflow UI command
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"\nView results with: mlflow ui --backend-store-uri {config['mlflow']['tracking_uri']}")


if __name__ == "__main__":
    main()