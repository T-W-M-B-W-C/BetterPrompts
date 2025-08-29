#!/usr/bin/env python3
"""
Training script for DistilBERT-based intent classification model
Optimized for faster training and inference while maintaining high accuracy
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional

import torch
import yaml
from transformers import DistilBertTokenizer

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data.data_processor import DataProcessor
from src.models.distilbert_classifier_model import create_distilbert_model
from src.models.train import Trainer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DistilBertTrainer(Trainer):
    """Extended trainer for DistilBERT model with specific optimizations"""
    
    def __init__(self, config_path: str = "configs/ml_pipeline_config.yaml"):
        """Initialize DistilBERT trainer with configuration"""
        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Override model configuration for DistilBERT
        self._setup_distilbert_config()
        
        # Call parent initialization
        super().__init__(config_path)
        
        # Initialize tokenizer for DistilBERT
        self.tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
        
        logger.info("Initialized DistilBertTrainer")
    
    def _setup_distilbert_config(self):
        """Setup DistilBERT-specific configuration"""
        # Add DistilBERT configuration if not present
        if 'distilbert_classifier' not in self.config['model']:
            self.config['model']['distilbert_classifier'] = {
                'architecture': 'distilbert',
                'pretrained_model': 'distilbert-base-uncased',
                'num_labels': 10,
                'hidden_dropout_prob': 0.1,
                'attention_dropout_prob': 0.1,
                'max_position_embeddings': 512,
                'use_complexity_features': True,
                'pooling_strategy': 'cls',
                'use_layer_norm': True,
                'classifier_hidden_size': 768
            }
        
        # Optimize training parameters for DistilBERT
        self.config['training']['learning_rate'] = 5e-5  # Slightly higher LR for DistilBERT
        self.config['training']['warmup_steps'] = 300  # Less warmup needed
        self.config['training']['batch_size'] = 64  # Can use larger batch size
        
        logger.info("Configured training parameters for DistilBERT")
    
    def create_model(self, trial: Optional[object] = None) -> torch.nn.Module:
        """Create DistilBERT model with optional hyperparameter tuning"""
        if trial and self.config['hyperparameter_tuning']['enabled']:
            # Hyperparameter search for DistilBERT
            learning_rate = trial.suggest_float(
                'learning_rate',
                1e-5,
                1e-4,
                log=True
            )
            
            dropout_prob = trial.suggest_float(
                'dropout_prob',
                0.1,
                0.3
            )
            
            pooling_strategy = trial.suggest_categorical(
                'pooling_strategy',
                ['cls', 'mean', 'attention']  # Skip 'max' for DistilBERT
            )
            
            use_complexity = trial.suggest_categorical(
                'use_complexity',
                [True, False]
            )
            
            use_layer_norm = trial.suggest_categorical(
                'use_layer_norm',
                [True, False]
            )
            
            # Create model with trial parameters
            model = create_distilbert_model(
                num_labels=len(self.label_names),
                hidden_dropout_prob=dropout_prob,
                attention_dropout_prob=dropout_prob,
                pooling_strategy=pooling_strategy,
                use_complexity_features=use_complexity,
                use_layer_norm=use_layer_norm
            )
        else:
            # Use default config
            model = create_distilbert_model(
                config_path=None,  # We'll pass parameters directly
                num_labels=len(self.label_names),
                pretrained_model_name=self.config['model']['distilbert_classifier']['pretrained_model'],
                hidden_dropout_prob=self.config['model']['distilbert_classifier']['hidden_dropout_prob'],
                attention_dropout_prob=self.config['model']['distilbert_classifier']['attention_dropout_prob'],
                use_complexity_features=self.config['model']['distilbert_classifier'].get('use_complexity_features', True),
                pooling_strategy=self.config['model']['distilbert_classifier'].get('pooling_strategy', 'cls'),
                use_layer_norm=self.config['model']['distilbert_classifier'].get('use_layer_norm', True)
            )
        
        return model.to(self.device)
    
    def benchmark_inference_speed(self, model: torch.nn.Module, num_samples: int = 100):
        """Benchmark inference speed of DistilBERT model"""
        logger.info(f"Benchmarking inference speed with {num_samples} samples...")
        
        model.eval()
        
        # Create dummy inputs
        batch_size = 8
        sequence_length = 128
        
        dummy_input_ids = torch.randint(0, 30000, (batch_size, sequence_length)).to(self.device)
        dummy_attention_mask = torch.ones(batch_size, sequence_length).to(self.device)
        
        # Warmup
        for _ in range(10):
            with torch.no_grad():
                _ = model(dummy_input_ids, attention_mask=dummy_attention_mask)
        
        # Benchmark
        torch.cuda.synchronize() if torch.cuda.is_available() else None
        start_time = time.time()
        
        for _ in range(num_samples // batch_size):
            with torch.no_grad():
                _ = model(dummy_input_ids, attention_mask=dummy_attention_mask)
        
        torch.cuda.synchronize() if torch.cuda.is_available() else None
        end_time = time.time()
        
        total_time = end_time - start_time
        samples_per_second = num_samples / total_time
        ms_per_sample = (total_time / num_samples) * 1000
        
        logger.info(f"Inference speed: {samples_per_second:.1f} samples/second")
        logger.info(f"Latency: {ms_per_sample:.2f} ms/sample")
        
        return {
            'samples_per_second': samples_per_second,
            'ms_per_sample': ms_per_sample
        }


def compare_with_deberta(config_path: str):
    """Compare DistilBERT performance with DeBERTa baseline"""
    logger.info("Comparing DistilBERT with DeBERTa baseline...")
    
    # This would load DeBERTa results from MLflow or a saved file
    # For now, we'll use placeholder values
    deberta_metrics = {
        'accuracy': 0.92,
        'f1_weighted': 0.91,
        'inference_speed': 50,  # samples/second
        'model_size_mb': 440
    }
    
    logger.info("DeBERTa baseline metrics:")
    for key, value in deberta_metrics.items():
        logger.info(f"  {key}: {value}")
    
    return deberta_metrics


def main():
    """Main training function for DistilBERT"""
    parser = argparse.ArgumentParser(
        description='Train DistilBERT-based intent classification model'
    )
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
        '--hyperparameter-search',
        action='store_true',
        help='Run hyperparameter search'
    )
    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Benchmark inference speed after training'
    )
    parser.add_argument(
        '--compare-baseline',
        action='store_true',
        help='Compare with DeBERTa baseline'
    )
    parser.add_argument(
        '--experiment-name',
        type=str,
        default='distilbert_intent_classification',
        help='MLflow experiment name'
    )
    parser.add_argument(
        '--run-name',
        type=str,
        help='MLflow run name'
    )
    parser.add_argument(
        '--num-epochs',
        type=int,
        help='Override number of training epochs'
    )
    parser.add_argument(
        '--freeze-layers',
        type=int,
        default=0,
        help='Number of transformer layers to freeze (0 = no freezing)'
    )
    
    args = parser.parse_args()
    
    # Change to project directory
    os.chdir(project_root)
    
    # Initialize trainer
    logger.info("Initializing DistilBERT trainer...")
    trainer = DistilBertTrainer(args.config)
    
    # Override experiment name
    import mlflow
    mlflow.set_experiment(args.experiment_name)
    
    # Prepare data if requested
    if args.prepare_data:
        logger.info("Preparing training data...")
        # Use existing data preparation logic
        from scripts.train_intent_classifier import prepare_data
        prepare_data(args.config, force_regenerate=False)
    
    # Compare with baseline if requested
    if args.compare_baseline:
        baseline_metrics = compare_with_deberta(args.config)
    
    # Run training
    logger.info("Starting DistilBERT training...")
    
    if args.hyperparameter_search:
        # Run hyperparameter search
        logger.info("Running hyperparameter search for DistilBERT...")
        best_params = trainer.hyperparameter_search()
        
        # Train final model with best parameters
        logger.info("Training final DistilBERT model with best parameters...")
        with mlflow.start_run(run_name=args.run_name or "distilbert_final"):
            mlflow.log_params(best_params)
            mlflow.log_param("model_architecture", "distilbert")
            mlflow.log_param("freeze_layers", args.freeze_layers)
            
            # Override freeze_layers if specified
            if args.freeze_layers > 0:
                model = trainer.create_model()
                # Freeze layers after model creation
                for i in range(args.freeze_layers):
                    for param in model.distilbert.transformer.layer[i].parameters():
                        param.requires_grad = False
                logger.info(f"Frozen {args.freeze_layers} transformer layers")
            
            results = trainer.train(num_epochs=args.num_epochs)
            
            # Log model size
            model_size_mb = sum(p.numel() * p.element_size() for p in model.parameters()) / 1024 / 1024
            mlflow.log_metric("model_size_mb", model_size_mb)
            logger.info(f"Model size: {model_size_mb:.1f} MB")
    else:
        # Train with default parameters
        with mlflow.start_run(run_name=args.run_name or "distilbert_training"):
            mlflow.log_param("model_architecture", "distilbert")
            mlflow.log_param("freeze_layers", args.freeze_layers)
            
            # Create model with potential layer freezing
            model = trainer.create_model()
            if args.freeze_layers > 0:
                for i in range(args.freeze_layers):
                    for param in model.distilbert.transformer.layer[i].parameters():
                        param.requires_grad = False
                logger.info(f"Frozen {args.freeze_layers} transformer layers")
            
            results = trainer.train(num_epochs=args.num_epochs)
            
            # Log model size
            model_size_mb = sum(p.numel() * p.element_size() for p in model.parameters()) / 1024 / 1024
            mlflow.log_metric("model_size_mb", model_size_mb)
            logger.info(f"Model size: {model_size_mb:.1f} MB")
    
    # Benchmark inference speed if requested
    if args.benchmark:
        model = trainer.create_model()
        # Load best checkpoint
        checkpoint_path = Path(trainer.config['paths']['models_dir']) / 'checkpoints' / 'best_model' / 'model.pt'
        if checkpoint_path.exists():
            model.load_state_dict(torch.load(checkpoint_path))
            logger.info(f"Loaded best model from {checkpoint_path}")
        
        speed_metrics = trainer.benchmark_inference_speed(model)
        
        with mlflow.start_run(run_name="distilbert_benchmark"):
            mlflow.log_metrics(speed_metrics)
            
            # Compare with baseline if available
            if args.compare_baseline:
                speedup = speed_metrics['samples_per_second'] / baseline_metrics['inference_speed']
                mlflow.log_metric("speedup_vs_deberta", speedup)
                logger.info(f"Speedup vs DeBERTa: {speedup:.2f}x")
    
    logger.info("DistilBERT training complete!")
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("DISTILBERT TRAINING SUMMARY")
    logger.info("="*50)
    logger.info(f"Model: DistilBERT-base-uncased")
    logger.info(f"Task: Intent Classification ({len(trainer.label_names)} classes)")
    
    if 'model_size_mb' in locals():
        logger.info(f"Model Size: {model_size_mb:.1f} MB")
        if args.compare_baseline:
            size_reduction = (1 - model_size_mb / baseline_metrics['model_size_mb']) * 100
            logger.info(f"Size Reduction vs DeBERTa: {size_reduction:.1f}%")
    
    if args.benchmark and 'speed_metrics' in locals():
        logger.info(f"Inference Speed: {speed_metrics['samples_per_second']:.1f} samples/sec")
        logger.info(f"Latency: {speed_metrics['ms_per_sample']:.2f} ms/sample")
    
    logger.info("="*50)
    
    # Print MLflow UI command
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"\nView results with: mlflow ui --backend-store-uri {config['mlflow']['tracking_uri']}")


if __name__ == "__main__":
    main()