#!/usr/bin/env python3
"""
Simple RunPod Training Script - Downloads data and trains model
Copy this entire script to RunPod and run it
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def install_dependencies():
    """Install required packages"""
    logger.info("📦 Installing dependencies...")
    os.system("pip install -q transformers==4.35.0 datasets==2.14.0 accelerate==0.24.0")
    os.system("pip install -q scikit-learn pandas numpy tqdm")
    logger.info("✅ Dependencies installed")

def create_training_data():
    """Create training data with 10 intent categories"""
    logger.info("📝 Creating training data...")
    
    # Define the 10 intent categories with example templates
    intent_templates = {
        "question_answering": [
            "What is {}?",
            "How does {} work?",
            "Can you explain {}?",
            "Why is {} important?",
            "When should I use {}?"
        ],
        "creative_writing": [
            "Write a story about {}",
            "Create a poem about {}",
            "Generate a creative description of {}",
            "Compose a narrative involving {}",
            "Draft a fictional account of {}"
        ],
        "code_generation": [
            "Write code to {}",
            "Create a function that {}",
            "Implement {} in Python",
            "Generate a script for {}",
            "Build a program to {}"
        ],
        "summarization": [
            "Summarize this text: {}",
            "Provide a brief overview of {}",
            "What are the key points of {}?",
            "Give me the highlights of {}",
            "Condense this information: {}"
        ],
        "translation": [
            "Translate {} to Spanish",
            "How do you say {} in French?",
            "Convert this to German: {}",
            "What's the Japanese translation of {}?",
            "Translate {} into Italian"
        ],
        "data_analysis": [
            "Analyze this data: {}",
            "What patterns do you see in {}?",
            "Interpret these results: {}",
            "Extract insights from {}",
            "What conclusions can we draw from {}?"
        ],
        "problem_solving": [
            "How can I solve {}?",
            "What's the solution to {}?",
            "Help me fix {}",
            "Troubleshoot this issue: {}",
            "Find a way to {}"
        ],
        "conversation": [
            "Let's discuss {}",
            "What are your thoughts on {}?",
            "Can we talk about {}?",
            "I'd like to chat about {}",
            "Share your perspective on {}"
        ],
        "instruction_following": [
            "Follow these steps: {}",
            "Complete this task: {}",
            "Execute these instructions: {}",
            "Perform the following: {}",
            "Carry out this procedure: {}"
        ],
        "reasoning": [
            "Explain the logic behind {}",
            "What's the reasoning for {}?",
            "Justify why {}",
            "Analyze the cause of {}",
            "Deduce the implications of {}"
        ]
    }
    
    # Topics for variation
    topics = [
        "machine learning", "climate change", "quantum computing", "artificial intelligence",
        "blockchain", "renewable energy", "space exploration", "genetics", "robotics",
        "cybersecurity", "data science", "neural networks", "cloud computing", "IoT",
        "biotechnology", "nanotechnology", "virtual reality", "5G technology", "automation",
        "deep learning", "computer vision", "natural language processing", "edge computing"
    ]
    
    # Generate samples
    samples = []
    samples_per_intent = 100  # Adjust this for more/less data
    
    for intent, templates in intent_templates.items():
        for i in range(samples_per_intent):
            template = templates[i % len(templates)]
            topic = topics[i % len(topics)]
            text = template.format(topic)
            
            samples.append({
                "text": text,
                "label": intent
            })
    
    # Shuffle samples
    import random
    random.shuffle(samples)
    
    # Save to file
    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/training_data.json", "w") as f:
        json.dump(samples, f, indent=2)
    
    logger.info(f"✅ Created {len(samples)} training samples")
    return "data/raw/training_data.json"

def train_model(data_path):
    """Train DistilBERT classifier"""
    logger.info("🎯 Starting training...")
    
    # Check GPU
    if torch.cuda.is_available():
        logger.info(f"✅ GPU: {torch.cuda.get_device_name(0)}")
        device = "cuda"
    else:
        logger.info("⚠️ No GPU detected, using CPU")
        device = "cpu"
    
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
    
    # Split data
    train_df, val_df = train_test_split(df, test_size=0.2, stratify=df['label_encoded'], random_state=42)
    
    # Initialize tokenizer and model
    logger.info("🤖 Loading DistilBERT model...")
    tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
    model = DistilBertForSequenceClassification.from_pretrained(
        'distilbert-base-uncased',
        num_labels=num_labels
    )
    
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
    
    # Training arguments - optimized for quick training
    training_args = TrainingArguments(
        output_dir='./models/distilbert_intent',
        num_train_epochs=2,  # Reduced epochs for quick training
        per_device_train_batch_size=16 if device == "cuda" else 4,
        per_device_eval_batch_size=32,
        warmup_steps=100,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=20,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        fp16=(device == "cuda"),  # Use mixed precision on GPU
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
    logger.info(f"📈 Evaluation - Loss: {eval_results.get('eval_loss', 'N/A'):.4f}")
    
    return model_path

def package_results():
    """Package results for download"""
    logger.info("📦 Packaging results...")
    
    import tarfile
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"training_results_{timestamp}.tar.gz"
    
    with tarfile.open(archive_name, "w:gz") as tar:
        if os.path.exists("models"):
            tar.add("models", arcname="models")
        if os.path.exists("logs"):
            tar.add("logs", arcname="logs")
    
    file_size = os.path.getsize(archive_name) / (1024 * 1024)  # MB
    logger.info(f"✅ Results packaged: {archive_name} ({file_size:.1f} MB)")
    
    return archive_name

def main():
    """Main training pipeline"""
    print("="*60)
    print("🚀 BetterPrompts Intent Classifier Training")
    print("="*60)
    
    # Create workspace
    os.makedirs("/workspace/betterprompts/ml-pipeline", exist_ok=True)
    os.chdir("/workspace/betterprompts/ml-pipeline")
    
    # Install dependencies
    install_dependencies()
    
    # Create training data
    data_path = create_training_data()
    
    # Train model
    model_path = train_model(data_path)
    
    # Package results
    archive_path = package_results()
    
    # Print summary
    print("="*60)
    print("📊 TRAINING COMPLETE!")
    print("="*60)
    print(f"✅ Model saved: {model_path}")
    print(f"✅ Archive created: {archive_path}")
    print("="*60)
    print("📥 To download results:")
    print(f"   runpodctl receive <POD_ID> {archive_path} ./")
    print("="*60)

if __name__ == "__main__":
    main()