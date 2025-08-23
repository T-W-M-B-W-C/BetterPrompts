#!/usr/bin/env python3
"""
Complete RunPod Training Script for BetterPrompts Intent Classifier
This script can be copied and pasted directly into RunPod web terminal
"""

import os
import sys
import json
import time
import torch
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_gpu():
    """Check GPU availability"""
    if torch.cuda.is_available():
        logger.info(f"✅ GPU Available: {torch.cuda.get_device_name(0)}")
        logger.info(f"   CUDA Version: {torch.version.cuda}")
        logger.info(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        return True
    else:
        logger.warning("⚠️ No GPU detected, training will be slow")
        return False

def install_dependencies():
    """Install required packages"""
    logger.info("📦 Installing dependencies...")
    os.system("pip install -q transformers==4.35.0 datasets==2.14.0 accelerate==0.24.0")
    os.system("pip install -q scikit-learn pandas numpy tqdm")
    logger.info("✅ Dependencies installed")

def download_training_data():
    """Download training data from GitHub or create sample data"""
    logger.info("📥 Setting up training data...")
    
    # Create data directory
    os.makedirs("data/raw", exist_ok=True)
    
    # Try to download from your repo (if it's public)
    # Otherwise, create sample data
    try:
        import urllib.request
        # Replace with your actual data URL if available
        url = "https://raw.githubusercontent.com/your-repo/betterprompts/main/ml-pipeline/data/raw/training_data_large.json"
        urllib.request.urlretrieve(url, "data/raw/training_data.json")
        logger.info("✅ Downloaded training data")
    except:
        logger.info("Creating sample training data...")
        # Create sample data with the 10 intent categories
        intents = [
            "question_answering", "creative_writing", "code_generation",
            "summarization", "translation", "data_analysis",
            "problem_solving", "conversation", "instruction_following",
            "reasoning"
        ]
        
        samples = []
        for intent in intents:
            for i in range(100):  # 100 samples per intent
                samples.append({
                    "text": f"Sample prompt for {intent} task {i}",
                    "label": intent
                })
        
        with open("data/raw/training_data.json", "w") as f:
            json.dump(samples, f, indent=2)
        
        logger.info(f"✅ Created sample data with {len(samples)} examples")
    
    return "data/raw/training_data.json"

def train_distilbert_classifier(data_path):
    """Train DistilBERT classifier"""
    logger.info("🎯 Starting DistilBERT training...")
    
    from transformers import (
        DistilBertTokenizer,
        DistilBertForSequenceClassification,
        TrainingArguments,
        Trainer
    )
    from datasets import Dataset
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    
    # Load data
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    # Encode labels
    le = LabelEncoder()
    df['label_encoded'] = le.fit_transform(df['label'])
    num_labels = len(le.classes_)
    
    logger.info(f"📊 Dataset: {len(df)} samples, {num_labels} classes")
    logger.info(f"   Classes: {list(le.classes_)}")
    
    # Split data
    train_df, val_df = train_test_split(df, test_size=0.2, stratify=df['label_encoded'])
    
    # Initialize tokenizer and model
    tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
    model = DistilBertForSequenceClassification.from_pretrained(
        'distilbert-base-uncased',
        num_labels=num_labels
    )
    
    # Move model to GPU if available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    
    # Tokenize data
    def tokenize_function(examples):
        return tokenizer(
            examples['text'],
            padding='max_length',
            truncation=True,
            max_length=128
        )
    
    # Create datasets
    train_dataset = Dataset.from_pandas(train_df[['text', 'label_encoded']])
    val_dataset = Dataset.from_pandas(val_df[['text', 'label_encoded']])
    
    train_dataset = train_dataset.map(tokenize_function, batched=True)
    val_dataset = val_dataset.map(tokenize_function, batched=True)
    
    train_dataset = train_dataset.rename_column('label_encoded', 'labels')
    val_dataset = val_dataset.rename_column('label_encoded', 'labels')
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir='./models/distilbert_intent',
        num_train_epochs=3,
        per_device_train_batch_size=32 if torch.cuda.is_available() else 8,
        per_device_eval_batch_size=64,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=50,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=torch.cuda.is_available(),  # Use mixed precision on GPU
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
    )
    
    # Train
    logger.info("🚀 Training started...")
    start_time = time.time()
    
    trainer.train()
    
    training_time = time.time() - start_time
    logger.info(f"✅ Training completed in {training_time/60:.1f} minutes")
    
    # Save model
    model_path = "./models/distilbert_intent_classifier"
    trainer.save_model(model_path)
    tokenizer.save_pretrained(model_path)
    
    # Save label encoder
    import pickle
    with open(f"{model_path}/label_encoder.pkl", "wb") as f:
        pickle.dump(le, f)
    
    logger.info(f"💾 Model saved to {model_path}")
    
    # Evaluate
    eval_results = trainer.evaluate()
    logger.info(f"📈 Evaluation results: {eval_results}")
    
    return model_path, eval_results

def package_results():
    """Package training results for download"""
    logger.info("📦 Packaging results...")
    
    import tarfile
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"training_results_{timestamp}.tar.gz"
    
    with tarfile.open(archive_name, "w:gz") as tar:
        tar.add("models", arcname="models")
        if os.path.exists("logs"):
            tar.add("logs", arcname="logs")
    
    logger.info(f"✅ Results packaged: {archive_name}")
    logger.info(f"   Size: {os.path.getsize(archive_name) / 1e6:.1f} MB")
    
    return archive_name

def main():
    """Main training pipeline"""
    logger.info("="*50)
    logger.info("🚀 BetterPrompts Intent Classifier Training")
    logger.info("="*50)
    
    # Check environment
    has_gpu = check_gpu()
    
    # Install dependencies
    install_dependencies()
    
    # Get training data
    data_path = download_training_data()
    
    # Train model
    model_path, eval_results = train_distilbert_classifier(data_path)
    
    # Package results
    archive_path = package_results()
    
    # Print summary
    logger.info("="*50)
    logger.info("📊 TRAINING SUMMARY")
    logger.info("="*50)
    logger.info(f"✅ Model: DistilBERT")
    logger.info(f"✅ GPU Used: {has_gpu}")
    logger.info(f"✅ Model Path: {model_path}")
    logger.info(f"✅ Results Archive: {archive_path}")
    logger.info(f"✅ Eval Loss: {eval_results.get('eval_loss', 'N/A'):.4f}")
    logger.info("="*50)
    logger.info("🎉 Training complete! Download the archive to get your model.")
    logger.info(f"   Download command: scp root@[POD_IP]:/workspace/betterprompts/ml-pipeline/{archive_path} ./")

if __name__ == "__main__":
    main()