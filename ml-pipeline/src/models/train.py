"""
Training script for intent classification model with hyperparameter tuning
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
import warnings

import mlflow
import mlflow.pytorch
import numpy as np
import optuna
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import DataLoader
from transformers import (
    get_linear_schedule_with_warmup,
    get_cosine_schedule_with_warmup,
    AutoTokenizer
)
from tqdm import tqdm
import yaml
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.data.data_loader import DataModule, create_dataloaders
from src.models.intent_classifier_model import IntentClassifier, IntentClassifierConfig
from src.evaluation.metrics import calculate_metrics, plot_confusion_matrix

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Trainer:
    """Trainer class for intent classification model"""
    
    def __init__(self, config_path: str = "configs/ml_pipeline_config.yaml"):
        """Initialize trainer with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Set device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Initialize MLflow
        mlflow.set_tracking_uri(self.config['mlflow']['tracking_uri'])
        mlflow.set_experiment(self.config['mlflow']['experiment_name'])
        
        # Load data module
        self.data_module = DataModule(config_path)
        self.data_module.setup()
        
        # Get label mappings
        self.label_names = self.data_module.train_dataset.get_label_names()
        self.label_to_id = self.data_module.train_dataset.get_label_to_id()
        self.id_to_label = {v: k for k, v in self.label_to_id.items()}
    
    def create_model(self, trial: Optional[optuna.Trial] = None) -> IntentClassifier:
        """Create model with optional hyperparameter tuning"""
        if trial and self.config['hyperparameter_tuning']['enabled']:
            # Hyperparameter search
            learning_rate = trial.suggest_float(
                'learning_rate',
                self.config['hyperparameter_tuning']['parameters']['learning_rate']['low'],
                self.config['hyperparameter_tuning']['parameters']['learning_rate']['high'],
                log=True
            )
            
            dropout_prob = trial.suggest_float(
                'dropout_prob',
                0.1,
                0.5
            )
            
            pooling_strategy = trial.suggest_categorical(
                'pooling_strategy',
                ['cls', 'mean', 'max', 'attention']
            )
            
            use_complexity = trial.suggest_categorical(
                'use_complexity',
                [True, False]
            )
            
            # Create config
            model_config = IntentClassifierConfig(
                pretrained_model_name=self.config['model']['intent_classifier']['pretrained_model'],
                num_labels=len(self.label_names),
                hidden_dropout_prob=dropout_prob,
                attention_dropout_prob=dropout_prob,
                pooling_strategy=pooling_strategy,
                use_complexity_features=use_complexity
            )
        else:
            # Use default config
            model_config = IntentClassifierConfig(
                pretrained_model_name=self.config['model']['intent_classifier']['pretrained_model'],
                num_labels=len(self.label_names),
                hidden_dropout_prob=self.config['model']['intent_classifier']['hidden_dropout_prob'],
                attention_dropout_prob=self.config['model']['intent_classifier']['attention_dropout_prob']
            )
        
        model = IntentClassifier(model_config)
        return model.to(self.device)
    
    def train_epoch(
        self,
        model: IntentClassifier,
        dataloader: DataLoader,
        optimizer: torch.optim.Optimizer,
        scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None,
        accumulation_steps: int = 1
    ) -> Dict[str, float]:
        """Train for one epoch"""
        model.train()
        total_loss = 0
        all_preds = []
        all_labels = []
        
        progress_bar = tqdm(dataloader, desc="Training")
        
        for batch_idx, batch in enumerate(progress_bar):
            # Move batch to device
            batch = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v 
                    for k, v in batch.items()}
            
            # Forward pass
            outputs = model(**batch)
            loss = outputs.loss / accumulation_steps
            
            # Backward pass
            loss.backward()
            
            # Update weights
            if (batch_idx + 1) % accumulation_steps == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                if scheduler:
                    scheduler.step()
                optimizer.zero_grad()
            
            # Track metrics
            total_loss += loss.item() * accumulation_steps
            
            if 'labels' in batch:
                preds = torch.argmax(outputs.logits, dim=-1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(batch['labels'].cpu().numpy())
            
            # Update progress bar
            progress_bar.set_postfix({'loss': loss.item() * accumulation_steps})
        
        # Calculate metrics
        metrics = {
            'loss': total_loss / len(dataloader),
            'accuracy': accuracy_score(all_labels, all_preds) if all_labels else 0
        }
        
        return metrics
    
    def evaluate(
        self,
        model: IntentClassifier,
        dataloader: DataLoader
    ) -> Dict[str, float]:
        """Evaluate model"""
        model.eval()
        total_loss = 0
        all_preds = []
        all_labels = []
        all_probs = []
        
        with torch.no_grad():
            for batch in tqdm(dataloader, desc="Evaluating"):
                # Move batch to device
                batch = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v 
                        for k, v in batch.items()}
                
                # Forward pass
                outputs = model(**batch)
                
                if outputs.loss is not None:
                    total_loss += outputs.loss.item()
                
                # Get predictions
                probs = torch.softmax(outputs.logits, dim=-1)
                preds = torch.argmax(probs, dim=-1)
                
                all_probs.extend(probs.cpu().numpy())
                all_preds.extend(preds.cpu().numpy())
                if 'labels' in batch:
                    all_labels.extend(batch['labels'].cpu().numpy())
        
        # Calculate metrics
        if all_labels:
            metrics = calculate_metrics(
                np.array(all_labels),
                np.array(all_preds),
                np.array(all_probs),
                self.label_names
            )
            metrics['loss'] = total_loss / len(dataloader)
        else:
            metrics = {'loss': total_loss / len(dataloader)}
        
        return metrics
    
    def train(
        self,
        trial: Optional[optuna.Trial] = None,
        num_epochs: Optional[int] = None
    ) -> Dict[str, float]:
        """Full training loop"""
        # Create model
        model = self.create_model(trial)
        
        # Get hyperparameters
        if trial:
            learning_rate = trial.params.get('learning_rate', self.config['training']['learning_rate'])
            batch_size = trial.suggest_categorical(
                'batch_size',
                self.config['hyperparameter_tuning']['parameters']['batch_size']['choices']
            )
            warmup_ratio = trial.suggest_float(
                'warmup_ratio',
                self.config['hyperparameter_tuning']['parameters']['warmup_ratio']['low'],
                self.config['hyperparameter_tuning']['parameters']['warmup_ratio']['high']
            )
            weight_decay = trial.suggest_float(
                'weight_decay',
                self.config['hyperparameter_tuning']['parameters']['weight_decay']['low'],
                self.config['hyperparameter_tuning']['parameters']['weight_decay']['high']
            )
        else:
            learning_rate = self.config['training']['learning_rate']
            batch_size = self.config['training']['batch_size']
            warmup_ratio = 0.1
            weight_decay = self.config['training']['weight_decay']
        
        # Update batch size if different
        if batch_size != self.data_module.batch_size:
            self.data_module.batch_size = batch_size
        
        # Get dataloaders
        train_loader = self.data_module.train_dataloader()
        val_loader = self.data_module.val_dataloader()
        
        # Setup optimizer
        optimizer = AdamW(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # Setup scheduler
        num_training_steps = len(train_loader) * (num_epochs or self.config['training']['num_epochs'])
        num_warmup_steps = int(warmup_ratio * num_training_steps)
        
        scheduler = get_cosine_schedule_with_warmup(
            optimizer,
            num_warmup_steps=num_warmup_steps,
            num_training_steps=num_training_steps
        )
        
        # Training parameters
        accumulation_steps = self.config['training']['gradient_accumulation_steps']
        num_epochs = num_epochs or self.config['training']['num_epochs']
        best_metric = -float('inf')
        best_epoch = 0
        patience = 3
        patience_counter = 0
        
        # Start MLflow run
        with mlflow.start_run(nested=True if trial else False):
            # Log parameters
            mlflow.log_params({
                'model': self.config['model']['intent_classifier']['pretrained_model'],
                'learning_rate': learning_rate,
                'batch_size': batch_size,
                'num_epochs': num_epochs,
                'warmup_ratio': warmup_ratio,
                'weight_decay': weight_decay,
                'accumulation_steps': accumulation_steps
            })
            
            if trial:
                mlflow.log_params(trial.params)
            
            # Training loop
            for epoch in range(num_epochs):
                logger.info(f"\nEpoch {epoch + 1}/{num_epochs}")
                
                # Train
                train_metrics = self.train_epoch(
                    model, train_loader, optimizer, scheduler, accumulation_steps
                )
                
                # Evaluate
                val_metrics = self.evaluate(model, val_loader)
                
                # Log metrics
                mlflow.log_metrics({
                    f'train_{k}': v for k, v in train_metrics.items()
                }, step=epoch)
                mlflow.log_metrics({
                    f'val_{k}': v for k, v in val_metrics.items()
                }, step=epoch)
                
                logger.info(f"Train Loss: {train_metrics['loss']:.4f}, "
                          f"Train Acc: {train_metrics['accuracy']:.4f}")
                logger.info(f"Val Loss: {val_metrics['loss']:.4f}, "
                          f"Val Acc: {val_metrics.get('accuracy', 0):.4f}")
                
                # Check for improvement
                metric_name = self.config['training']['metric_for_best_model']
                current_metric = val_metrics.get(metric_name, val_metrics.get('accuracy', 0))
                
                if current_metric > best_metric:
                    best_metric = current_metric
                    best_epoch = epoch
                    patience_counter = 0
                    
                    # Save best model
                    if not trial:  # Only save during final training
                        model_path = Path(self.config['paths']['models_dir']) / 'checkpoints' / 'best_model'
                        model_path.mkdir(parents=True, exist_ok=True)
                        torch.save(model.state_dict(), model_path / 'model.pt')
                        
                        # Log model to MLflow
                        mlflow.pytorch.log_model(model, "model")
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        logger.info(f"Early stopping at epoch {epoch + 1}")
                        break
                
                # Report to Optuna
                if trial:
                    trial.report(current_metric, epoch)
                    if trial.should_prune():
                        raise optuna.TrialPruned()
            
            logger.info(f"Best {metric_name}: {best_metric:.4f} at epoch {best_epoch + 1}")
            
            # Final evaluation on test set
            if not trial:
                test_loader = self.data_module.test_dataloader()
                test_metrics = self.evaluate(model, test_loader)
                
                mlflow.log_metrics({
                    f'test_{k}': v for k, v in test_metrics.items()
                })
                
                logger.info(f"Test Accuracy: {test_metrics.get('accuracy', 0):.4f}")
                
                # Save classification report
                if 'classification_report' in test_metrics:
                    report_path = Path('artifacts') / 'classification_report.txt'
                    report_path.parent.mkdir(exist_ok=True)
                    with open(report_path, 'w') as f:
                        f.write(test_metrics['classification_report'])
                    mlflow.log_artifact(str(report_path))
        
        return {'best_metric': best_metric, 'best_epoch': best_epoch}
    
    def hyperparameter_search(self):
        """Run hyperparameter optimization with Optuna"""
        logger.info("Starting hyperparameter search...")
        
        def objective(trial):
            try:
                result = self.train(trial, num_epochs=5)  # Fewer epochs for search
                return result['best_metric']
            except optuna.TrialPruned:
                raise
            except Exception as e:
                logger.error(f"Trial failed: {e}")
                return 0
        
        # Create study
        study = optuna.create_study(
            direction='maximize',
            pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=2)
        )
        
        # Run optimization
        study.optimize(
            objective,
            n_trials=self.config['hyperparameter_tuning']['n_trials'],
            timeout=self.config['hyperparameter_tuning']['timeout']
        )
        
        # Log best parameters
        logger.info(f"Best parameters: {study.best_params}")
        logger.info(f"Best value: {study.best_value}")
        
        # Save study results
        results_path = Path('artifacts') / 'optuna_results.json'
        results_path.parent.mkdir(exist_ok=True)
        
        with open(results_path, 'w') as f:
            json.dump({
                'best_params': study.best_params,
                'best_value': study.best_value,
                'n_trials': len(study.trials)
            }, f, indent=2)
        
        return study.best_params


def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description='Train intent classification model')
    parser.add_argument('--config', type=str, default='configs/ml_pipeline_config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--hyperparameter-search', action='store_true',
                       help='Run hyperparameter search')
    parser.add_argument('--resume', type=str, help='Path to checkpoint to resume from')
    
    args = parser.parse_args()
    
    # Initialize trainer
    trainer = Trainer(args.config)
    
    # Run training
    if args.hyperparameter_search:
        best_params = trainer.hyperparameter_search()
        
        # Train final model with best parameters
        logger.info("Training final model with best parameters...")
        with mlflow.start_run(run_name="final_model"):
            mlflow.log_params(best_params)
            trainer.train()
    else:
        with mlflow.start_run():
            trainer.train()


if __name__ == "__main__":
    main()