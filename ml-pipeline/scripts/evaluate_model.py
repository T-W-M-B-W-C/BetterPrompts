#!/usr/bin/env python3
"""
Evaluate trained intent classification model
"""

import argparse
import json
import logging
import sys
from pathlib import Path
import torch
import yaml
import mlflow
import numpy as np
from typing import Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data.data_loader import create_dataloaders
from src.models.intent_classifier_model import IntentClassifier, IntentClassifierConfig
from src.evaluation.metrics import create_evaluation_report, calculate_metrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_model(model_path: str, config_path: str, device: torch.device) -> IntentClassifier:
    """Load trained model from checkpoint"""
    # Load configuration
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Get metadata for label count
    metadata_path = Path(config['data']['processed_data_path']) / 'metadata.json'
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Create model config
    model_config = IntentClassifierConfig(
        pretrained_model_name=config['model']['intent_classifier']['pretrained_model'],
        num_labels=len(metadata['intent_labels']),
        hidden_dropout_prob=config['model']['intent_classifier']['hidden_dropout_prob'],
        attention_dropout_prob=config['model']['intent_classifier']['attention_dropout_prob']
    )
    
    # Initialize model
    model = IntentClassifier(model_config)
    
    # Load weights
    if Path(model_path).is_dir():
        # MLflow model directory
        model_path = Path(model_path) / 'data' / 'model.pth'
    
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    
    logger.info(f"Loaded model from {model_path}")
    return model


def evaluate_on_test_set(
    model: IntentClassifier,
    test_loader,
    device: torch.device,
    label_names: list
) -> Dict:
    """Evaluate model on test set"""
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []
    total_loss = 0
    
    with torch.no_grad():
        for batch in test_loader:
            # Move to device
            batch = {k: v.to(device) if isinstance(v, torch.Tensor) else v 
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
    metrics = calculate_metrics(
        np.array(all_labels),
        np.array(all_preds),
        np.array(all_probs),
        label_names
    )
    
    if total_loss > 0:
        metrics['test_loss'] = total_loss / len(test_loader)
    
    return metrics


def evaluate_live_examples(model: IntentClassifier, tokenizer, device: torch.device) -> None:
    """Evaluate model on live examples"""
    examples = [
        "How do I implement a binary search tree in Python?",
        "Write a poem about artificial intelligence",
        "What is the capital of France?",
        "Analyze the trends in this sales data",
        "Translate 'Hello world' to Spanish",
        "Help me plan a birthday party for 20 people",
        "Why is the sky blue?",
        "Summarize this article about climate change",
        "Debug this JavaScript code that's not working",
        "Let's have a conversation about philosophy"
    ]
    
    logger.info("\nLive Example Predictions:")
    logger.info("-" * 80)
    
    model.eval()
    with torch.no_grad():
        for example in examples:
            # Tokenize
            inputs = tokenizer(
                example,
                return_tensors='pt',
                truncation=True,
                padding=True,
                max_length=512
            ).to(device)
            
            # Predict
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)
            pred_idx = torch.argmax(probs, dim=-1).item()
            confidence = probs[0, pred_idx].item()
            
            # Get label names from metadata
            metadata_path = Path('data/processed/metadata.json')
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                label_names = metadata['intent_labels']
                pred_label = label_names[pred_idx]
            else:
                pred_label = f"Class_{pred_idx}"
            
            logger.info(f"Text: {example[:60]}...")
            logger.info(f"Prediction: {pred_label} (confidence: {confidence:.3f})")
            logger.info("-" * 80)


def main():
    """Main evaluation function"""
    parser = argparse.ArgumentParser(description='Evaluate BetterPrompts intent classification model')
    parser.add_argument(
        '--model-path',
        type=str,
        required=True,
        help='Path to trained model checkpoint or MLflow model'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='configs/ml_pipeline_config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='evaluation_results',
        help='Directory to save evaluation results'
    )
    parser.add_argument(
        '--mlflow-run-id',
        type=str,
        help='MLflow run ID to load model from'
    )
    parser.add_argument(
        '--live-examples',
        action='store_true',
        help='Run predictions on live examples'
    )
    parser.add_argument(
        '--device',
        type=str,
        default='cuda' if torch.cuda.is_available() else 'cpu',
        help='Device to use for evaluation'
    )
    
    args = parser.parse_args()
    
    # Set device
    device = torch.device(args.device)
    logger.info(f"Using device: {device}")
    
    # Load model
    if args.mlflow_run_id:
        # Load from MLflow
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
        
        mlflow.set_tracking_uri(config['mlflow']['tracking_uri'])
        model_uri = f"runs:/{args.mlflow_run_id}/model"
        model = mlflow.pytorch.load_model(model_uri, map_location=device)
    else:
        # Load from checkpoint
        model = load_model(args.model_path, args.config, device)
    
    # Load configuration
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create test dataloader
    _, _, test_loader = create_dataloaders(
        config['data']['processed_data_path'],
        batch_size=config['training']['batch_size']
    )
    
    # Load label names
    metadata_path = Path(config['data']['processed_data_path']) / 'metadata.json'
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    label_names = metadata['intent_labels']
    
    # Evaluate on test set
    logger.info("Evaluating on test set...")
    test_metrics = evaluate_on_test_set(model, test_loader, device, label_names)
    
    # Log key metrics
    logger.info("\nTest Set Performance:")
    logger.info(f"Accuracy: {test_metrics['accuracy']:.4f}")
    logger.info(f"F1-score (weighted): {test_metrics['f1_weighted']:.4f}")
    logger.info(f"F1-score (macro): {test_metrics['f1_macro']:.4f}")
    
    if 'top_3_accuracy' in test_metrics:
        logger.info(f"Top-3 Accuracy: {test_metrics['top_3_accuracy']:.4f}")
    
    # Create detailed evaluation report
    logger.info(f"\nCreating detailed evaluation report...")
    create_evaluation_report(
        model, test_loader, device, label_names, args.output_dir
    )
    
    # Run live examples if requested
    if args.live_examples:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            config['model']['intent_classifier']['pretrained_model']
        )
        evaluate_live_examples(model, tokenizer, device)
    
    # Save summary
    summary_path = Path(args.output_dir) / 'evaluation_summary.json'
    with open(summary_path, 'w') as f:
        json.dump({
            'model_path': args.model_path,
            'test_accuracy': test_metrics['accuracy'],
            'test_f1_weighted': test_metrics['f1_weighted'],
            'test_f1_macro': test_metrics['f1_macro'],
            'num_test_samples': len(test_loader.dataset),
            'device': str(device)
        }, f, indent=2)
    
    logger.info(f"\nEvaluation complete! Results saved to {args.output_dir}")


if __name__ == "__main__":
    main()