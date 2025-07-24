#!/usr/bin/env python3
"""Complete training pipeline for DistilBERT intent classifier."""

import os
import json
import argparse
import time
from pathlib import Path
from typing import Dict, Any

import numpy as np
import torch
from transformers import (
    AutoTokenizer,
    DistilBertForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
    TrainerCallback
)
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from loguru import logger
from tqdm.auto import tqdm


# Intent and complexity labels
INTENT_LABELS = [
    "question_answering", "creative_writing", "code_generation",
    "data_analysis", "reasoning", "summarization", 
    "translation", "conversation", "task_planning", "problem_solving"
]

COMPLEXITY_LABELS = ["simple", "moderate", "complex"]


class IntentDataset(Dataset):
    """Dataset for intent classification."""
    
    def __init__(self, examples, tokenizer, max_length=128):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        # Create label mappings
        self.intent_to_id = {label: i for i, label in enumerate(INTENT_LABELS)}
        self.complexity_to_id = {label: i for i, label in enumerate(COMPLEXITY_LABELS)}
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        example = self.examples[idx]
        
        # Tokenize text
        encoding = self.tokenizer(
            example['text'],
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        # Get labels
        intent_label = self.intent_to_id[example['intent']]
        complexity_label = self.complexity_to_id[example['complexity']]
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(intent_label, dtype=torch.long),
            'complexity_labels': torch.tensor(complexity_label, dtype=torch.long)
        }


def compute_metrics(eval_pred):
    """Compute metrics for evaluation."""
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    
    accuracy = accuracy_score(labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average='weighted'
    )
    
    return {
        'accuracy': accuracy,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }


class TQDMProgressCallback(TrainerCallback):
    """Custom callback to show TQDM progress during training."""
    
    def __init__(self):
        self.training_bar = None
        self.epoch_bar = None
        self.current_epoch = 0
        
    def on_train_begin(self, args, state, control, **kwargs):
        """Initialize progress bars."""
        self.training_bar = tqdm(
            total=state.max_steps,
            desc="Training Progress",
            unit="step"
        )
        self.epoch_bar = tqdm(
            total=args.num_train_epochs,
            desc="Epochs",
            unit="epoch",
            position=1,
            leave=True
        )
        
    def on_step_end(self, args, state, control, **kwargs):
        """Update progress bar after each step."""
        if self.training_bar:
            self.training_bar.update(1)
            
            # Update with current metrics
            if state.log_history:
                last_log = state.log_history[-1]
                loss = last_log.get('loss', 0)
                learning_rate = last_log.get('learning_rate', 0)
                self.training_bar.set_postfix({
                    'loss': f'{loss:.4f}',
                    'lr': f'{learning_rate:.2e}'
                })
                
    def on_epoch_end(self, args, state, control, **kwargs):
        """Update epoch progress."""
        if self.epoch_bar:
            self.epoch_bar.update(1)
            
            # Show validation metrics if available
            if state.log_history:
                for log in reversed(state.log_history):
                    if 'eval_accuracy' in log:
                        self.epoch_bar.set_postfix({
                            'val_acc': f"{log['eval_accuracy']:.4f}",
                            'val_loss': f"{log.get('eval_loss', 0):.4f}"
                        })
                        break
                        
    def on_train_end(self, args, state, control, **kwargs):
        """Close progress bars."""
        if self.training_bar:
            self.training_bar.close()
        if self.epoch_bar:
            self.epoch_bar.close()


def load_and_split_data(data_path: str, train_ratio=0.8, val_ratio=0.1):
    """Load data and split into train/val/test sets."""
    logger.info(f"Loading data from {data_path}")
    
    with tqdm(total=3, desc="Loading and splitting data") as pbar:
        # Load data
        with open(data_path, 'r') as f:
            data = json.load(f)
        pbar.update(1)
        
        examples = data['examples']
        logger.info(f"Total examples: {len(examples)}")
        
        # Shuffle data
        np.random.seed(42)
        np.random.shuffle(examples)
        pbar.update(1)
        
        # Split data
        train_size = int(train_ratio * len(examples))
        val_size = int(val_ratio * len(examples))
        
        train_examples = examples[:train_size]
        val_examples = examples[train_size:train_size + val_size]
        test_examples = examples[train_size + val_size:]
        pbar.update(1)
    
    logger.info(f"Train: {len(train_examples)}, Val: {len(val_examples)}, Test: {len(test_examples)}")
    
    return train_examples, val_examples, test_examples


def train_distilbert(
    train_examples,
    val_examples,
    output_dir: str,
    model_name: str = "distilbert-base-uncased",
    max_length: int = 128,
    batch_size: int = 32,
    learning_rate: float = 5e-5,
    num_epochs: int = 5,
    warmup_steps: int = 500,
    fp16: bool = False
):
    """Train DistilBERT model."""
    logger.info("Initializing model and tokenizer...")
    
    # Initialize tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = DistilBertForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(INTENT_LABELS),
        problem_type="single_label_classification"
    )
    
    # Create datasets
    train_dataset = IntentDataset(train_examples, tokenizer, max_length)
    val_dataset = IntentDataset(val_examples, tokenizer, max_length)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        warmup_steps=warmup_steps,
        learning_rate=learning_rate,
        weight_decay=0.01,
        logging_dir=f'{output_dir}/logs',
        logging_steps=100,
        save_steps=500,
        eval_steps=500,
        evaluation_strategy="steps",
        save_strategy="steps",
        load_best_model_at_end=True,
        metric_for_best_model="eval_accuracy",
        greater_is_better=True,
        save_total_limit=3,
        fp16=fp16,
        gradient_checkpointing=False,
        dataloader_num_workers=4,
        remove_unused_columns=False,
        report_to=["tensorboard"],
    )
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
        callbacks=[
            EarlyStoppingCallback(
                early_stopping_patience=3,
                early_stopping_threshold=0.001
            ),
            TQDMProgressCallback()
        ]
    )
    
    # Train model
    logger.info("Starting training...")
    train_start = time.time()
    
    trainer.train()
    
    train_time = time.time() - train_start
    logger.info(f"Training completed in {train_time/60:.2f} minutes")
    
    # Save model
    logger.info(f"Saving model to {output_dir}")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    # Save config
    config = {
        "model_name": model_name,
        "max_length": max_length,
        "num_labels": len(INTENT_LABELS),
        "intent_labels": INTENT_LABELS,
        "complexity_labels": COMPLEXITY_LABELS,
        "training_args": training_args.to_dict()
    }
    
    with open(f"{output_dir}/config.json", 'w') as f:
        json.dump(config, f, indent=2)
    
    return trainer, model, tokenizer


def evaluate_model(model, tokenizer, test_examples, max_length=128):
    """Evaluate model on test set."""
    logger.info("Evaluating model on test set...")
    
    # Create test dataset
    test_dataset = IntentDataset(test_examples, tokenizer, max_length)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
    
    # Set model to eval mode
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    
    all_predictions = []
    all_labels = []
    
    # Run evaluation with progress bar
    with torch.no_grad():
        for batch in tqdm(test_loader, desc="Evaluating", unit="batch"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].numpy()
            
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            
            predictions = torch.argmax(outputs.logits, dim=-1).cpu().numpy()
            
            all_predictions.extend(predictions)
            all_labels.extend(labels)
    
    # Calculate metrics
    accuracy = accuracy_score(all_labels, all_predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_labels, all_predictions, average='weighted'
    )
    
    logger.info(f"Test Accuracy: {accuracy:.4f}")
    logger.info(f"Test F1: {f1:.4f}")
    logger.info(f"Test Precision: {precision:.4f}")
    logger.info(f"Test Recall: {recall:.4f}")
    
    return {
        'accuracy': accuracy,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }


def export_to_onnx_simple(model, tokenizer, output_path, max_length=128):
    """Simple ONNX export."""
    logger.info(f"Exporting model to ONNX format: {output_path}")
    
    # Create dummy input
    dummy_text = "How do I implement a neural network?"
    inputs = tokenizer(
        dummy_text,
        return_tensors="pt",
        max_length=max_length,
        padding="max_length",
        truncation=True
    )
    
    # Export to ONNX
    torch.onnx.export(
        model,
        (inputs["input_ids"], inputs["attention_mask"]),
        output_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=['input_ids', 'attention_mask'],
        output_names=['logits'],
        dynamic_axes={
            'input_ids': {0: 'batch_size'},
            'attention_mask': {0: 'batch_size'},
            'logits': {0: 'batch_size'}
        }
    )
    
    logger.info("ONNX export completed")


def main():
    parser = argparse.ArgumentParser(description="Train DistilBERT for intent classification")
    parser.add_argument(
        "--data-path",
        type=str,
        default="data_generation/openai_training_data.json",
        help="Path to training data JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/distilbert_intent_classifier",
        help="Output directory for trained model"
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="distilbert-base-uncased",
        help="Pre-trained model name"
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=128,
        help="Maximum sequence length"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Training batch size"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=5e-5,
        help="Learning rate"
    )
    parser.add_argument(
        "--num-epochs",
        type=int,
        default=5,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--fp16",
        action="store_true",
        help="Use mixed precision training"
    )
    parser.add_argument(
        "--export-onnx",
        action="store_true",
        help="Export model to ONNX format"
    )
    parser.add_argument(
        "--skip-evaluation",
        action="store_true",
        help="Skip test set evaluation"
    )
    
    args = parser.parse_args()
    
    # Load and split data
    train_examples, val_examples, test_examples = load_and_split_data(args.data_path)
    
    # Train model
    trainer, model, tokenizer = train_distilbert(
        train_examples,
        val_examples,
        args.output_dir,
        model_name=args.model_name,
        max_length=args.max_length,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        num_epochs=args.num_epochs,
        fp16=args.fp16
    )
    
    # Evaluate on test set
    if not args.skip_evaluation:
        test_metrics = evaluate_model(model, tokenizer, test_examples, args.max_length)
        
        # Check if accuracy meets requirement
        if test_metrics['accuracy'] >= 0.88:
            logger.success(f"✅ Model meets accuracy requirement: {test_metrics['accuracy']:.2%} >= 88%")
        else:
            logger.warning(f"⚠️ Model below accuracy requirement: {test_metrics['accuracy']:.2%} < 88%")
        
        # Save test metrics
        with open(f"{args.output_dir}/test_metrics.json", 'w') as f:
            json.dump(test_metrics, f, indent=2)
    
    # Export to ONNX if requested
    if args.export_onnx:
        onnx_path = f"{args.output_dir}/model.onnx"
        export_to_onnx_simple(model, tokenizer, onnx_path, args.max_length)
    
    logger.info("Training pipeline completed!")


if __name__ == "__main__":
    main()