#!/usr/bin/env python3
"""Self-contained DistilBERT training script for RunPod."""

import os
import json
import time
import sys
from datetime import datetime
from pathlib import Path
import logging
import subprocess
import tarfile

import numpy as np
import torch
from transformers import (
    AutoTokenizer,
    DistilBertForSequenceClassification,
    TrainingArguments,
    Trainer,
    TrainerCallback,
    EarlyStoppingCallback
)
from torch.utils.data import Dataset
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from tqdm.auto import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Intent labels
INTENT_LABELS = [
    "explanation", "creative_writing", "code_generation", "analysis",
    "question_answering", "summarization", "translation", "conversation",
    "reasoning", "planning"
]

# Complexity labels
COMPLEXITY_LABELS = ["simple", "moderate", "complex"]


class IntentDataset(Dataset):
    """Dataset for intent classification."""
    
    def __init__(self, examples, tokenizer, max_length=128):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        example = self.examples[idx]
        
        # Tokenize input
        encoding = self.tokenizer(
            example['input'],
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': torch.tensor(INTENT_LABELS.index(example['intent']), dtype=torch.long)
        }


class ProgressCallback(TrainerCallback):
    """Custom callback for progress tracking."""
    
    def __init__(self):
        self.training_bar = None
        self.current_epoch = 0
        
    def on_train_begin(self, args, state, control, **kwargs):
        logger.info(f"🚀 Starting training with {args.num_train_epochs} epochs")
        logger.info(f"Total training steps: {state.max_steps}")
        
    def on_epoch_begin(self, args, state, control, **kwargs):
        self.current_epoch += 1
        logger.info(f"\n📊 Epoch {self.current_epoch}/{args.num_train_epochs}")
        
    def on_log(self, args, state, control, logs=None, **kwargs):
        if state.global_step % args.logging_steps == 0 and logs:
            # Log metrics
            metrics = []
            if 'loss' in logs:
                metrics.append(f"loss: {logs['loss']:.4f}")
            if 'learning_rate' in logs:
                metrics.append(f"lr: {logs['learning_rate']:.2e}")
            if 'eval_accuracy' in logs:
                metrics.append(f"accuracy: {logs['eval_accuracy']:.4f}")
                
            if metrics:
                logger.info(f"Step {state.global_step}/{state.max_steps} - {' | '.join(metrics)}")


def load_and_split_data(data_path):
    """Load and split the training data."""
    logger.info(f"📂 Loading data from {data_path}")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    examples = data['examples']
    logger.info(f"Total examples: {len(examples):,}")
    
    # Shuffle and split
    np.random.seed(42)
    np.random.shuffle(examples)
    
    train_size = int(0.8 * len(examples))
    val_size = int(0.1 * len(examples))
    
    train_examples = examples[:train_size]
    val_examples = examples[train_size:train_size + val_size]
    test_examples = examples[train_size + val_size:]
    
    logger.info(f"Split sizes - Train: {len(train_examples):,}, Val: {len(val_examples):,}, Test: {len(test_examples):,}")
    
    return train_examples, val_examples, test_examples


def compute_metrics(eval_pred):
    """Compute metrics for evaluation."""
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    
    accuracy = accuracy_score(labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average='weighted', zero_division=0
    )
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }


def get_optimal_batch_size():
    """Determine optimal batch size based on GPU."""
    if not torch.cuda.is_available():
        return 16
        
    # Get GPU memory
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9  # GB
    
    if gpu_memory >= 40:
        return 128
    elif gpu_memory >= 24:
        return 64
    elif gpu_memory >= 16:
        return 32
    else:
        return 16


def train_model(train_examples, val_examples, output_dir="models"):
    """Train the DistilBERT model."""
    logger.info("🏗️ Initializing model and tokenizer...")
    
    # Load tokenizer and model
    model_name = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = DistilBertForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(INTENT_LABELS)
    )
    
    # Move to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    logger.info(f"Using device: {device}")
    
    # Create datasets
    train_dataset = IntentDataset(train_examples, tokenizer)
    val_dataset = IntentDataset(val_examples, tokenizer)
    
    # Determine batch size
    batch_size = get_optimal_batch_size()
    logger.info(f"Using batch size: {batch_size}")
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=5,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=5e-5,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir=f"{output_dir}/logs",
        logging_steps=50,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        greater_is_better=True,
        save_total_limit=3,
        fp16=torch.cuda.is_available(),
        dataloader_num_workers=4,
        remove_unused_columns=False,
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
            ProgressCallback(),
            EarlyStoppingCallback(
                early_stopping_patience=3,
                early_stopping_threshold=0.001
            )
        ]
    )
    
    # Train
    logger.info("🚂 Starting training...")
    start_time = time.time()
    
    trainer.train()
    
    training_time = (time.time() - start_time) / 60
    logger.info(f"✅ Training completed in {training_time:.1f} minutes")
    
    # Save final model
    trainer.save_model(f"{output_dir}/final")
    tokenizer.save_pretrained(f"{output_dir}/final")
    
    return model, tokenizer


def evaluate_model(model, tokenizer, test_examples):
    """Evaluate the model on test set."""
    logger.info("📊 Evaluating model on test set...")
    
    # Create test dataset
    test_dataset = IntentDataset(test_examples, tokenizer)
    
    # Create trainer for evaluation
    trainer = Trainer(
        model=model,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics
    )
    
    # Evaluate
    results = trainer.evaluate(eval_dataset=test_dataset)
    
    logger.info(f"Test Accuracy: {results['eval_accuracy']*100:.2f}%")
    logger.info(f"Test F1 Score: {results['eval_f1']*100:.2f}%")
    
    return results


def export_to_onnx(model, tokenizer, output_path="models/onnx"):
    """Export model to ONNX format."""
    logger.info("📦 Exporting to ONNX...")
    
    try:
        os.makedirs(output_path, exist_ok=True)
        
        # Dummy input for tracing
        dummy_input = tokenizer(
            "Example text for ONNX export",
            return_tensors="pt",
            padding="max_length",
            max_length=128,
            truncation=True
        )
        
        # Export
        torch.onnx.export(
            model,
            tuple(dummy_input.values()),
            f"{output_path}/distilbert_intent_classifier.onnx",
            input_names=['input_ids', 'attention_mask'],
            output_names=['logits'],
            dynamic_axes={
                'input_ids': {0: 'batch_size'},
                'attention_mask': {0: 'batch_size'},
                'logits': {0: 'batch_size'}
            },
            opset_version=11
        )
        
        logger.info("✅ ONNX export successful")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️  ONNX export failed: {e}")
        return False


def package_results(model_dir, results, training_time):
    """Package all results into a tar.gz file."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_name = f"results/training_results_{timestamp}.tar.gz"
    
    logger.info(f"📦 Packaging results to {archive_name}")
    
    # Save training summary
    summary = {
        "timestamp": timestamp,
        "training_time_minutes": training_time,
        "test_accuracy": results['eval_accuracy'],
        "test_f1": results['eval_f1'],
        "model_path": model_dir,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    }
    
    with open("results/training_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Create archive
    with tarfile.open(archive_name, "w:gz") as tar:
        tar.add(model_dir, arcname="model")
        tar.add("results/training_summary.json", arcname="training_summary.json")
        tar.add("logs/training.log", arcname="training.log")
        if os.path.exists("models/onnx"):
            tar.add("models/onnx", arcname="onnx")
    
    logger.info(f"✅ Results packaged: {archive_name}")
    logger.info(f"📥 Download with:")
    logger.info(f"   scp -P 18733 root@[POD_IP]:/workspace/runpod-training-package/{archive_name} ./")
    
    return archive_name


def main():
    """Main training pipeline."""
    logger.info("="*50)
    logger.info("BetterPrompts DistilBERT Training Pipeline")
    logger.info("="*50)
    
    start_time = time.time()
    
    # Load data
    train_examples, val_examples, test_examples = load_and_split_data("data/openai_training_data.json")
    
    # Train model
    model, tokenizer = train_model(train_examples, val_examples)
    
    # Evaluate
    results = evaluate_model(model, tokenizer, test_examples)
    
    # Export to ONNX
    export_to_onnx(model, tokenizer)
    
    # Calculate total time
    total_time = (time.time() - start_time) / 60
    
    # Package results
    os.makedirs("results", exist_ok=True)
    package_results("models/final", results, total_time)
    
    logger.info("="*50)
    logger.info(f"🎉 Training pipeline completed in {total_time:.1f} minutes!")
    logger.info(f"📊 Final test accuracy: {results['eval_accuracy']*100:.2f}%")
    logger.info("="*50)
    
    # Auto-shutdown warning
    logger.info("⏰ Pod will auto-shutdown in 15 minutes...")
    logger.info("💡 Press Ctrl+C in the tmux session to cancel shutdown")
    
    # Wait before shutdown
    try:
        time.sleep(900)  # 15 minutes
        logger.info("Shutting down pod...")
        subprocess.run(["shutdown", "-h", "now"])
    except KeyboardInterrupt:
        logger.info("Shutdown cancelled")


if __name__ == "__main__":
    main()