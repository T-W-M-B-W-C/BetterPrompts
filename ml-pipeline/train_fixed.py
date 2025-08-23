#!/usr/bin/env python3
"""
Fixed training script for RunPod with correct transformers API
"""

import os
import sys
import json
import torch
import numpy as np
from pathlib import Path
from transformers import (
    AutoTokenizer,
    DistilBertForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# Intent labels
INTENT_LABELS = [
    "question_answering", "creative_writing", "code_generation",
    "data_analysis", "reasoning", "summarization", 
    "translation", "conversation", "task_planning", "problem_solving"
]

class IntentDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    
    accuracy = accuracy_score(labels, predictions)
    f1 = f1_score(labels, predictions, average='weighted')
    
    return {
        'accuracy': accuracy,
        'f1': f1
    }

def main():
    # Load data with default path
    default_path = "../runpod-training-package/data/openai_training_data.json"
    user_input = input(f"Enter path to training data (press Enter for default: {default_path}): ").strip()
    data_path = user_input if user_input else default_path
    
    print(f"\n📚 Loading data from: {data_path}")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Handle both formats
    if isinstance(data, dict) and 'examples' in data:
        examples = data['examples']
    else:
        examples = data
    
    print(f"✅ Loaded {len(examples)} examples")
    
    # Extract texts and labels
    texts = []
    labels = []
    intent_to_id = {label: i for i, label in enumerate(INTENT_LABELS)}
    
    for ex in examples:
        texts.append(ex.get('text', ex.get('prompt', '')))
        intent = ex.get('intent', 'problem_solving')
        labels.append(intent_to_id.get(intent, 0))
    
    # Split data
    X_train, X_temp, y_train, y_temp = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )
    
    print(f"📊 Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # Initialize model and tokenizer
    print("\n🤖 Loading DistilBERT model...")
    tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')
    model = DistilBertForSequenceClassification.from_pretrained(
        'distilbert-base-uncased',
        num_labels=len(INTENT_LABELS)
    )
    
    # Create datasets
    train_dataset = IntentDataset(X_train, y_train, tokenizer)
    val_dataset = IntentDataset(X_val, y_val, tokenizer)
    test_dataset = IntentDataset(X_test, y_test, tokenizer)
    
    # Training arguments - using correct parameter names
    output_dir = "models/distilbert_intent_classifier"
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,  # Reduced for faster training
        per_device_train_batch_size=32,
        per_device_eval_batch_size=64,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir=f'{output_dir}/logs',
        logging_steps=100,
        eval_strategy="steps",  # Correct parameter name
        eval_steps=500,
        save_strategy="steps",
        save_steps=1000,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        fp16=torch.cuda.is_available(),  # Only use fp16 if GPU available
        dataloader_num_workers=2,
        remove_unused_columns=False,
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
    )
    
    # Train
    print("\n🚀 Starting training...")
    print("=" * 60)
    
    trainer.train()
    
    # Save model
    print("\n💾 Saving model...")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    # Evaluate on test set
    print("\n📊 Evaluating on test set...")
    test_results = trainer.evaluate(eval_dataset=test_dataset)
    
    print("\n" + "=" * 60)
    print("✅ Training Complete!")
    print(f"📈 Test Accuracy: {test_results.get('eval_accuracy', 0)*100:.2f}%")
    print(f"📈 Test F1 Score: {test_results.get('eval_f1', 0)*100:.2f}%")
    print(f"💾 Model saved to: {output_dir}")
    print("=" * 60)
    
    # Save results
    with open(f"{output_dir}/test_results.json", 'w') as f:
        json.dump(test_results, f, indent=2)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)