#!/usr/bin/env python3
"""
Intent Classifier Training Script for RunPod
Optimized for large datasets with GPU acceleration
"""

import os
import torch
import pandas as pd
import numpy as np
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
    EarlyStoppingCallback
)
from datasets import Dataset, DatasetDict
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
import json
from datetime import datetime
import logging
import gc

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    'model_name': 'microsoft/deberta-v3-base',
    'max_length': 256,
    'batch_size': 16,  # Adjust based on GPU memory
    'gradient_accumulation_steps': 2,
    'learning_rate': 2e-5,
    'num_epochs': 5,
    'warmup_ratio': 0.1,
    'weight_decay': 0.01,
    'fp16': True,  # Mixed precision training
    'gradient_checkpointing': True,  # Save memory
    'save_total_limit': 2,
    'eval_steps': 500,
    'save_steps': 1000,
    'logging_steps': 100,
    'seed': 42,
}

# Intent labels mapping
INTENT_LABELS = {
    'chain_of_thought': 0,
    'tree_of_thoughts': 1,
    'few_shot': 2,
    'zero_shot': 3,
    'self_consistency': 4,
    'constitutional_ai': 5,
    'role_prompting': 6,
    'retrieval_augmented': 7,
    'meta_prompting': 8,
    'prompt_chaining': 9,
    'general': 10
}

def load_training_data(data_path):
    """Load and prepare training data"""
    logger.info(f"Loading data from {data_path}")
    
    # Support multiple formats
    if data_path.endswith('.csv'):
        df = pd.read_csv(data_path)
    elif data_path.endswith('.json'):
        df = pd.read_json(data_path)
    elif data_path.endswith('.jsonl'):
        df = pd.read_json(data_path, lines=True)
    else:
        raise ValueError(f"Unsupported file format: {data_path}")
    
    # Ensure required columns
    if 'text' not in df.columns or 'label' not in df.columns:
        raise ValueError("Data must have 'text' and 'label' columns")
    
    # Convert string labels to integers if needed
    if df['label'].dtype == 'object':
        df['label'] = df['label'].map(INTENT_LABELS)
    
    # Remove NaN values
    df = df.dropna()
    
    logger.info(f"Loaded {len(df)} samples")
    logger.info(f"Label distribution:\n{df['label'].value_counts()}")
    
    return df

def prepare_datasets(df, tokenizer, test_size=0.2, val_size=0.1):
    """Prepare train, validation, and test datasets"""
    
    # Split data
    X = df['text'].values
    y = df['label'].values
    
    # First split: train+val vs test
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=test_size, random_state=CONFIG['seed'], stratify=y
    )
    
    # Second split: train vs val
    val_split = val_size / (1 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_split, random_state=CONFIG['seed'], stratify=y_temp
    )
    
    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # Create datasets
    def create_dataset(texts, labels):
        return Dataset.from_dict({
            'text': texts,
            'label': labels
        })
    
    train_dataset = create_dataset(X_train, y_train)
    val_dataset = create_dataset(X_val, y_val)
    test_dataset = create_dataset(X_test, y_test)
    
    # Tokenize datasets
    def tokenize_function(examples):
        return tokenizer(
            examples['text'],
            padding=False,
            truncation=True,
            max_length=CONFIG['max_length']
        )
    
    train_dataset = train_dataset.map(tokenize_function, batched=True)
    val_dataset = val_dataset.map(tokenize_function, batched=True)
    test_dataset = test_dataset.map(tokenize_function, batched=True)
    
    return train_dataset, val_dataset, test_dataset

def compute_metrics(eval_pred):
    """Compute metrics for evaluation"""
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average='weighted'
    )
    accuracy = accuracy_score(labels, predictions)
    
    return {
        'accuracy': accuracy,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

def main():
    # Set device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    if device.type == 'cuda':
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    # Clear cache
    if device.type == 'cuda':
        torch.cuda.empty_cache()
        gc.collect()
    
    # Load tokenizer and model
    logger.info(f"Loading model: {CONFIG['model_name']}")
    tokenizer = AutoTokenizer.from_pretrained(CONFIG['model_name'])
    model = AutoModelForSequenceClassification.from_pretrained(
        CONFIG['model_name'],
        num_labels=len(INTENT_LABELS),
        ignore_mismatched_sizes=True
    )
    
    # Enable gradient checkpointing
    if CONFIG['gradient_checkpointing']:
        model.gradient_checkpointing_enable()
    
    # Move model to device
    model = model.to(device)
    
    # Load and prepare data
    data_path = input("Enter path to training data (CSV/JSON/JSONL): ").strip()
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        return
    
    df = load_training_data(data_path)
    train_dataset, val_dataset, test_dataset = prepare_datasets(df, tokenizer)
    
    # Data collator
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    
    # Training arguments
    output_dir = f"./models/intent_classifier_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=CONFIG['num_epochs'],
        per_device_train_batch_size=CONFIG['batch_size'],
        per_device_eval_batch_size=CONFIG['batch_size'],
        gradient_accumulation_steps=CONFIG['gradient_accumulation_steps'],
        learning_rate=CONFIG['learning_rate'],
        warmup_ratio=CONFIG['warmup_ratio'],
        weight_decay=CONFIG['weight_decay'],
        logging_dir=f"{output_dir}/logs",
        logging_steps=CONFIG['logging_steps'],
        evaluation_strategy="steps",
        eval_steps=CONFIG['eval_steps'],
        save_strategy="steps",
        save_steps=CONFIG['save_steps'],
        save_total_limit=CONFIG['save_total_limit'],
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        fp16=CONFIG['fp16'] and device.type == 'cuda',
        gradient_checkpointing=CONFIG['gradient_checkpointing'],
        dataloader_num_workers=4,
        remove_unused_columns=False,
        seed=CONFIG['seed'],
        report_to=["tensorboard"],
        push_to_hub=False,
    )
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
    )
    
    # Train
    logger.info("Starting training...")
    train_result = trainer.train()
    
    # Save model
    logger.info(f"Saving model to {output_dir}")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    # Save training metrics
    with open(f"{output_dir}/training_metrics.json", 'w') as f:
        json.dump(train_result.metrics, f, indent=2)
    
    # Evaluate on test set
    logger.info("Evaluating on test set...")
    test_results = trainer.evaluate(eval_dataset=test_dataset)
    
    # Save test metrics
    with open(f"{output_dir}/test_metrics.json", 'w') as f:
        json.dump(test_results, f, indent=2)
    
    logger.info("Training complete!")
    logger.info(f"Model saved to: {output_dir}")
    logger.info(f"Test Accuracy: {test_results.get('eval_accuracy', 0):.4f}")
    logger.info(f"Test F1: {test_results.get('eval_f1', 0):.4f}")
    
    # Save label mapping
    label_mapping = {v: k for k, v in INTENT_LABELS.items()}
    with open(f"{output_dir}/label_mapping.json", 'w') as f:
        json.dump(label_mapping, f, indent=2)
    
    print(f"\n✅ Training complete! Model saved to: {output_dir}")
    print(f"📊 Test Accuracy: {test_results.get('eval_accuracy', 0):.4f}")
    print(f"📊 Test F1 Score: {test_results.get('eval_f1', 0):.4f}")

if __name__ == "__main__":
    main()