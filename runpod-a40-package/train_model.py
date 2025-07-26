#!/usr/bin/env python3
"""Optimized training script for A40 GPU - handles all edge cases automatically."""

import os
import json
import torch
from transformers import (
    AutoTokenizer, 
    DistilBertForSequenceClassification, 
    Trainer, 
    TrainingArguments,
    EarlyStoppingCallback
)
from torch.utils.data import Dataset
import numpy as np
from datetime import datetime
import logging

# Simple logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Intent labels
INTENT_LABELS = [
    "explanation", "creative_writing", "code_generation", "analysis",
    "question_answering", "summarization", "translation", "conversation",
    "reasoning", "planning"
]

class IntentDataset(Dataset):
    """Simple dataset that handles various data formats."""
    def __init__(self, examples, tokenizer):
        self.examples = examples
        self.tokenizer = tokenizer
        
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        ex = self.examples[idx]
        
        # Flexible text field detection
        text = ex.get('text') or ex.get('input') or ex.get('prompt') or ""
        intent = ex.get('intent', 'explanation')
        
        # Tokenize
        encoding = self.tokenizer(
            text, 
            truncation=True, 
            padding='max_length', 
            max_length=128,
            return_tensors='pt'
        )
        
        # Get label index
        label = INTENT_LABELS.index(intent) if intent in INTENT_LABELS else 0
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

def main():
    logger.info("🚀 BetterPrompts Training Started")
    logger.info("=" * 50)
    
    # Load data
    logger.info("📂 Loading data...")
    try:
        with open('data/openai_training_data.json', 'r') as f:
            data = json.load(f)
        
        # Handle different data structures
        if isinstance(data, list):
            examples = data
        elif isinstance(data, dict):
            examples = data.get('examples', data.get('data', []))
        else:
            examples = []
            
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return
    
    logger.info(f"✅ Loaded {len(examples)} examples")
    
    # Split data
    np.random.seed(42)
    np.random.shuffle(examples)
    
    train_split = int(0.8 * len(examples))
    val_split = int(0.9 * len(examples))
    
    train_data = examples[:train_split]
    val_data = examples[train_split:val_split]
    test_data = examples[val_split:]
    
    logger.info(f"📊 Split: Train={len(train_data)}, Val={len(val_data)}, Test={len(test_data)}")
    
    # Initialize model and tokenizer
    logger.info("\n🤖 Loading model...")
    tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')
    model = DistilBertForSequenceClassification.from_pretrained(
        'distilbert-base-uncased',
        num_labels=len(INTENT_LABELS)
    )
    
    # Setup device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    logger.info(f"🎮 Using: {device}")
    
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        logger.info(f"🎮 GPU: {gpu_name}")
        
        # Optimize batch size for A40 (48GB VRAM)
        if "A40" in gpu_name:
            batch_size = 128
        elif "A100" in gpu_name:
            batch_size = 256
        elif "4090" in gpu_name or "3090" in gpu_name:
            batch_size = 64
        else:
            batch_size = 32
    else:
        batch_size = 16
    
    logger.info(f"📦 Batch size: {batch_size}")
    
    # Create datasets
    train_dataset = IntentDataset(train_data, tokenizer)
    val_dataset = IntentDataset(val_data, tokenizer)
    
    # Training arguments optimized for A40
    training_args = TrainingArguments(
        output_dir='./models',
        num_train_epochs=3,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        warmup_steps=100,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=20,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=torch.cuda.is_available(),
        dataloader_num_workers=4,
        remove_unused_columns=False,
        report_to=[],  # Disable wandb, etc.
    )
    
    # Create trainer with early stopping
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        callbacks=[
            EarlyStoppingCallback(early_stopping_patience=2)
        ],
    )
    
    # Train
    logger.info("\n🏃 Training...")
    start_time = datetime.now()
    
    try:
        trainer.train()
        
        duration = (datetime.now() - start_time).total_seconds() / 60
        logger.info(f"\n✅ Training completed in {duration:.1f} minutes!")
        
        # Save the final model
        logger.info("\n💾 Saving model...")
        model_path = './models/final'
        trainer.save_model(model_path)
        tokenizer.save_pretrained(model_path)
        
        # Quick test
        logger.info("\n🧪 Testing model...")
        test_texts = [
            "How do I implement a binary search tree?",
            "Write a poem about the ocean",
            "Explain quantum computing"
        ]
        
        model.eval()
        with torch.no_grad():
            for text in test_texts:
                inputs = tokenizer(text, return_tensors="pt", truncation=True).to(device)
                outputs = model(**inputs)
                predicted_idx = torch.argmax(outputs.logits, dim=-1).item()
                logger.info(f"'{text[:40]}...' → {INTENT_LABELS[predicted_idx]}")
        
        logger.info("\n🎉 Success! Model saved to ./models/final/")
        
        # Save metrics
        with open('./models/final/training_info.json', 'w') as f:
            json.dump({
                'duration_minutes': duration,
                'device': str(device),
                'batch_size': batch_size,
                'epochs': training_args.num_train_epochs,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
            
    except Exception as e:
        logger.error(f"\n❌ Training failed: {e}")
        raise

if __name__ == "__main__":
    main()