#!/usr/bin/env python3
"""Validate trained model accuracy on test set."""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)
from loguru import logger
import matplotlib.pyplot as plt
import seaborn as sns

from src.models.distilbert_classifier import DistilBERTClassifier
from src.data.intent_dataset import IntentDataset, INTENT_LABELS, COMPLEXITY_LABELS
from src.data.data_loader import create_data_loaders


class ModelValidator:
    """Validate model performance on test set."""
    
    def __init__(self, model_path: str, data_path: str):
        """Initialize the validator."""
        self.model_path = Path(model_path)
        self.data_path = Path(data_path)
        
        # Load model configuration
        config_path = self.model_path / "config.json"
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.get("model_name", "distilbert-base-uncased")
        )
        
        # Load model
        self.model = self._load_model()
        self.model.eval()
        
        # Set device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        logger.info(f"Loaded model from {model_path}")
        logger.info(f"Using device: {self.device}")
    
    def _load_model(self) -> DistilBERTClassifier:
        """Load the trained model."""
        model = DistilBERTClassifier(
            num_labels=len(INTENT_LABELS),
            model_name=self.config.get("model_name", "distilbert-base-uncased"),
            use_complexity_features=self.config.get("use_complexity_features", True),
            pooling_strategy=self.config.get("pooling_strategy", "cls"),
            dropout_rate=self.config.get("dropout_rate", 0.2),
            freeze_layers=self.config.get("freeze_layers", 0),
            predict_complexity=self.config.get("predict_complexity", True)
        )
        
        # Load state dict
        state_dict = torch.load(
            self.model_path / "pytorch_model.bin",
            map_location=torch.device("cpu")
        )
        model.load_state_dict(state_dict)
        
        return model
    
    def load_test_data(self) -> DataLoader:
        """Load test dataset."""
        # Load data
        with open(self.data_path, 'r') as f:
            data = json.load(f)
        
        # Extract examples
        examples = data['examples']
        
        # Split data (using same logic as training)
        np.random.seed(42)
        np.random.shuffle(examples)
        
        train_size = int(0.8 * len(examples))
        val_size = int(0.1 * len(examples))
        
        test_examples = examples[train_size + val_size:]
        
        logger.info(f"Test set size: {len(test_examples)} examples")
        
        # Create dataset
        test_dataset = IntentDataset(
            examples=test_examples,
            tokenizer=self.tokenizer,
            max_length=self.config.get("max_length", 128),
            use_complexity_features=self.config.get("use_complexity_features", True)
        )
        
        # Create dataloader
        test_loader = DataLoader(
            test_dataset,
            batch_size=32,
            shuffle=False,
            num_workers=4
        )
        
        return test_loader
    
    def validate(
        self,
        test_loader: DataLoader,
        save_results: bool = True,
        output_dir: str = "validation_results"
    ) -> Dict[str, Any]:
        """Run validation on test set."""
        logger.info("Starting validation...")
        
        all_intent_preds = []
        all_intent_labels = []
        all_complexity_preds = []
        all_complexity_labels = []
        
        # Disable gradient computation
        with torch.no_grad():
            for batch in test_loader:
                # Move to device
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                
                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask
                )
                
                # Get predictions
                intent_preds = outputs['intent_logits'].argmax(dim=-1).cpu().numpy()
                all_intent_preds.extend(intent_preds)
                all_intent_labels.extend(batch['intent_labels'].numpy())
                
                if self.config.get("predict_complexity", True):
                    complexity_preds = outputs['complexity_logits'].argmax(dim=-1).cpu().numpy()
                    all_complexity_preds.extend(complexity_preds)
                    all_complexity_labels.extend(batch['complexity_labels'].numpy())
        
        # Calculate metrics
        results = self._calculate_metrics(
            all_intent_preds,
            all_intent_labels,
            all_complexity_preds if all_complexity_preds else None,
            all_complexity_labels if all_complexity_labels else None
        )
        
        # Log results
        self._log_results(results)
        
        # Save results if requested
        if save_results:
            self._save_results(results, output_dir)
        
        return results
    
    def _calculate_metrics(
        self,
        intent_preds: List[int],
        intent_labels: List[int],
        complexity_preds: List[int] = None,
        complexity_labels: List[int] = None
    ) -> Dict[str, Any]:
        """Calculate validation metrics."""
        results = {}
        
        # Intent classification metrics
        intent_accuracy = accuracy_score(intent_labels, intent_preds)
        intent_precision, intent_recall, intent_f1, _ = precision_recall_fscore_support(
            intent_labels, intent_preds, average='weighted'
        )
        
        results['intent'] = {
            'accuracy': intent_accuracy,
            'precision': intent_precision,
            'recall': intent_recall,
            'f1': intent_f1,
            'confusion_matrix': confusion_matrix(intent_labels, intent_preds).tolist(),
            'classification_report': classification_report(
                intent_labels, intent_preds,
                target_names=INTENT_LABELS,
                output_dict=True
            )
        }
        
        # Per-class metrics
        per_class_report = classification_report(
            intent_labels, intent_preds,
            target_names=INTENT_LABELS,
            output_dict=True
        )
        
        results['intent']['per_class'] = {
            label: {
                'precision': metrics['precision'],
                'recall': metrics['recall'],
                'f1-score': metrics['f1-score'],
                'support': metrics['support']
            }
            for label, metrics in per_class_report.items()
            if label in INTENT_LABELS
        }
        
        # Complexity prediction metrics (if available)
        if complexity_preds is not None:
            complexity_accuracy = accuracy_score(complexity_labels, complexity_preds)
            complexity_precision, complexity_recall, complexity_f1, _ = precision_recall_fscore_support(
                complexity_labels, complexity_preds, average='weighted'
            )
            
            results['complexity'] = {
                'accuracy': complexity_accuracy,
                'precision': complexity_precision,
                'recall': complexity_recall,
                'f1': complexity_f1,
                'confusion_matrix': confusion_matrix(complexity_labels, complexity_preds).tolist(),
                'classification_report': classification_report(
                    complexity_labels, complexity_preds,
                    target_names=COMPLEXITY_LABELS,
                    output_dict=True
                )
            }
        
        return results
    
    def _log_results(self, results: Dict[str, Any]) -> None:
        """Log validation results."""
        logger.info("=" * 50)
        logger.info("VALIDATION RESULTS")
        logger.info("=" * 50)
        
        # Intent classification results
        intent_results = results['intent']
        logger.info(f"Intent Classification:")
        logger.info(f"  Accuracy: {intent_results['accuracy']:.4f} ({intent_results['accuracy']*100:.2f}%)")
        logger.info(f"  Precision: {intent_results['precision']:.4f}")
        logger.info(f"  Recall: {intent_results['recall']:.4f}")
        logger.info(f"  F1-Score: {intent_results['f1']:.4f}")
        
        # Check if accuracy meets requirement
        if intent_results['accuracy'] >= 0.88:
            logger.success(f"✅ Accuracy requirement met! ({intent_results['accuracy']*100:.2f}% >= 88%)")
        else:
            logger.warning(f"⚠️ Accuracy below requirement: {intent_results['accuracy']*100:.2f}% < 88%")
        
        # Per-class performance
        logger.info("\nPer-Class Performance:")
        for intent in INTENT_LABELS:
            metrics = results['intent']['per_class'][intent]
            logger.info(f"  {intent:20s}: F1={metrics['f1-score']:.3f}, Precision={metrics['precision']:.3f}, Recall={metrics['recall']:.3f}")
        
        # Complexity prediction results (if available)
        if 'complexity' in results:
            logger.info("\nComplexity Prediction:")
            complexity_results = results['complexity']
            logger.info(f"  Accuracy: {complexity_results['accuracy']:.4f}")
            logger.info(f"  F1-Score: {complexity_results['f1']:.4f}")
        
        logger.info("=" * 50)
    
    def _save_results(self, results: Dict[str, Any], output_dir: str) -> None:
        """Save validation results."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save results as JSON
        results_path = output_path / "validation_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {results_path}")
        
        # Create visualizations
        self._create_visualizations(results, output_path)
    
    def _create_visualizations(self, results: Dict[str, Any], output_dir: Path) -> None:
        """Create visualization plots."""
        # Intent confusion matrix
        plt.figure(figsize=(12, 10))
        cm = np.array(results['intent']['confusion_matrix'])
        sns.heatmap(
            cm,
            annot=True,
            fmt='d',
            cmap='Blues',
            xticklabels=INTENT_LABELS,
            yticklabels=INTENT_LABELS
        )
        plt.title('Intent Classification Confusion Matrix')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(output_dir / 'intent_confusion_matrix.png', dpi=300)
        plt.close()
        
        # Per-class F1 scores
        plt.figure(figsize=(10, 6))
        intents = []
        f1_scores = []
        for intent in INTENT_LABELS:
            intents.append(intent)
            f1_scores.append(results['intent']['per_class'][intent]['f1-score'])
        
        bars = plt.bar(intents, f1_scores)
        plt.axhline(y=0.88, color='r', linestyle='--', label='Target (88%)')
        plt.xlabel('Intent')
        plt.ylabel('F1-Score')
        plt.title('Per-Intent F1-Scores')
        plt.xticks(rotation=45, ha='right')
        plt.legend()
        
        # Color bars based on performance
        for bar, score in zip(bars, f1_scores):
            if score >= 0.88:
                bar.set_color('green')
            elif score >= 0.80:
                bar.set_color('orange')
            else:
                bar.set_color('red')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'per_intent_f1_scores.png', dpi=300)
        plt.close()
        
        # Complexity confusion matrix (if available)
        if 'complexity' in results:
            plt.figure(figsize=(8, 6))
            cm = np.array(results['complexity']['confusion_matrix'])
            sns.heatmap(
                cm,
                annot=True,
                fmt='d',
                cmap='Greens',
                xticklabels=COMPLEXITY_LABELS,
                yticklabels=COMPLEXITY_LABELS
            )
            plt.title('Complexity Prediction Confusion Matrix')
            plt.xlabel('Predicted')
            plt.ylabel('Actual')
            plt.tight_layout()
            plt.savefig(output_dir / 'complexity_confusion_matrix.png', dpi=300)
            plt.close()
        
        logger.info(f"Visualizations saved to {output_dir}")
    
    def validate_with_examples(
        self,
        num_examples: int = 20,
        show_errors: bool = True
    ) -> None:
        """Validate with example predictions."""
        logger.info(f"\nValidating with {num_examples} examples...")
        
        # Load test data
        with open(self.data_path, 'r') as f:
            data = json.load(f)
        
        # Get test examples
        examples = data['examples']
        np.random.seed(42)
        np.random.shuffle(examples)
        
        train_size = int(0.8 * len(examples))
        val_size = int(0.1 * len(examples))
        test_examples = examples[train_size + val_size:]
        
        # Sample examples
        sample_indices = np.random.choice(len(test_examples), num_examples, replace=False)
        
        correct_count = 0
        errors = []
        
        for idx in sample_indices:
            example = test_examples[idx]
            
            # Tokenize
            inputs = self.tokenizer(
                example['text'],
                padding="max_length",
                truncation=True,
                max_length=self.config.get("max_length", 128),
                return_tensors="pt"
            )
            
            # Move to device
            input_ids = inputs['input_ids'].to(self.device)
            attention_mask = inputs['attention_mask'].to(self.device)
            
            # Predict
            with torch.no_grad():
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask
                )
            
            # Get predictions
            intent_pred_idx = outputs['intent_logits'].argmax(dim=-1).item()
            intent_pred = INTENT_LABELS[intent_pred_idx]
            
            # Check if correct
            if intent_pred == example['intent']:
                correct_count += 1
            else:
                errors.append({
                    'text': example['text'],
                    'true': example['intent'],
                    'pred': intent_pred,
                    'confidence': torch.softmax(outputs['intent_logits'], dim=-1).max().item()
                })
        
        accuracy = correct_count / num_examples
        logger.info(f"Sample accuracy: {accuracy:.2f} ({correct_count}/{num_examples})")
        
        if show_errors and errors:
            logger.info("\nClassification errors:")
            for i, error in enumerate(errors[:5]):  # Show first 5 errors
                logger.info(f"\nError {i+1}:")
                logger.info(f"  Text: {error['text'][:100]}...")
                logger.info(f"  True: {error['true']}")
                logger.info(f"  Pred: {error['pred']} (confidence: {error['confidence']:.3f})")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Validate model accuracy")
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to trained model directory"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        required=True,
        help="Path to training data JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="validation_results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--show-examples",
        action="store_true",
        help="Show example predictions"
    )
    parser.add_argument(
        "--num-examples",
        type=int,
        default=20,
        help="Number of examples to show"
    )
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = ModelValidator(args.model_path, args.data_path)
    
    # Load test data
    test_loader = validator.load_test_data()
    
    # Run validation
    results = validator.validate(
        test_loader,
        save_results=True,
        output_dir=args.output_dir
    )
    
    # Show examples if requested
    if args.show_examples:
        validator.validate_with_examples(
            num_examples=args.num_examples,
            show_errors=True
        )
    
    # Return success/failure based on accuracy
    if results['intent']['accuracy'] >= 0.88:
        logger.success("✅ Model meets accuracy requirement!")
        return 0
    else:
        logger.error("❌ Model does not meet accuracy requirement!")
        return 1


if __name__ == "__main__":
    exit(main())