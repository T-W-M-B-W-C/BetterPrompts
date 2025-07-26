#!/bin/bash
# Debug and fix training data issues

echo "🔍 BetterPrompts Training Debugger"
echo "=================================="

# Step 1: Check data structure
echo -e "\n📊 Checking data structure..."
cat > check_data.py << 'EOF'
import json

try:
    with open('data/openai_training_data.json', 'r') as f:
        data = json.load(f)
    
    print("✅ JSON loaded successfully!")
    print(f"Data type: {type(data)}")
    
    if isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        for key in data.keys():
            if isinstance(data[key], list) and len(data[key]) > 0:
                print(f"\n{key}:")
                print(f"  - Length: {len(data[key])}")
                print(f"  - First item keys: {list(data[key][0].keys()) if isinstance(data[key][0], dict) else 'Not a dict'}")
                if isinstance(data[key][0], dict):
                    # Show sample without the full text
                    sample = data[key][0].copy()
                    if 'input' in sample:
                        sample['input'] = sample['input'][:50] + '...'
                    print(f"  - Sample: {sample}")
    
    elif isinstance(data, list):
        print(f"List length: {len(data)}")
        if len(data) > 0:
            print(f"First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
            
except Exception as e:
    print(f"❌ Error reading JSON: {e}")
    print("\nChecking file structure...")
    with open('data/openai_training_data.json', 'r') as f:
        for i in range(5):
            line = f.readline().strip()
            print(f"Line {i+1}: {line[:100]}...")
EOF

python check_data.py

# Step 2: Create fixed training script based on data structure
echo -e "\n✏️ Creating fixed training script..."
cat > train_working.py << 'EOF'
#!/usr/bin/env python3
"""Working training script with flexible data handling."""

import os
import json
import time
import torch
from transformers import AutoTokenizer, DistilBertForSequenceClassification, Trainer, TrainingArguments
from torch.utils.data import Dataset
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Intent labels
INTENT_LABELS = [
    "explanation", "creative_writing", "code_generation", "analysis",
    "question_answering", "summarization", "translation", "conversation",
    "reasoning", "planning"
]

class IntentDataset(Dataset):
    def __init__(self, examples, tokenizer, max_length=128):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length
        logger.info(f"Created dataset with {len(examples)} examples")
        
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        example = self.examples[idx]
        
        # Flexible text extraction
        text = None
        for key in ['input', 'text', 'prompt', 'query', 'question']:
            if key in example:
                text = example[key]
                break
        
        if text is None:
            # If no text found, use the first string value
            for value in example.values():
                if isinstance(value, str):
                    text = value
                    break
        
        if text is None:
            text = ""
            logger.warning(f"No text found in example {idx}: {example}")
        
        # Tokenize
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        # Flexible intent extraction
        intent = None
        for key in ['intent', 'label', 'category', 'class']:
            if key in example:
                intent = example[key]
                break
        
        if intent is None or intent not in INTENT_LABELS:
            intent = 'explanation'  # default
        
        label_idx = INTENT_LABELS.index(intent)
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': torch.tensor(label_idx, dtype=torch.long)
        }

def compute_metrics(eval_pred):
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

# Main training function
def train():
    # Load data
    logger.info("📂 Loading data...")
    with open('data/openai_training_data.json', 'r') as f:
        data = json.load(f)
    
    # Extract examples flexibly
    examples = None
    if isinstance(data, list):
        examples = data
    elif isinstance(data, dict):
        # Try common keys
        for key in ['examples', 'data', 'training_data', 'train']:
            if key in data and isinstance(data[key], list):
                examples = data[key]
                break
    
    if examples is None:
        raise ValueError("Could not find training examples in data")
    
    logger.info(f"Found {len(examples)} examples")
    
    # Quick validation
    if len(examples) > 0:
        logger.info(f"First example keys: {list(examples[0].keys())}")
    
    # Split data
    np.random.seed(42)
    np.random.shuffle(examples)
    
    train_size = int(0.8 * len(examples))
    val_size = int(0.1 * len(examples))
    
    train_examples = examples[:train_size]
    val_examples = examples[train_size:train_size + val_size]
    test_examples = examples[train_size + val_size:]
    
    logger.info(f"Split: Train={len(train_examples)}, Val={len(val_examples)}, Test={len(test_examples)}")
    
    # Initialize model
    logger.info("🤖 Initializing model...")
    tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')
    model = DistilBertForSequenceClassification.from_pretrained(
        'distilbert-base-uncased',
        num_labels=len(INTENT_LABELS)
    )
    
    # Setup device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    logger.info(f"Using device: {device}")
    
    if torch.cuda.is_available():
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
    
    # Create datasets
    train_dataset = IntentDataset(train_examples, tokenizer)
    val_dataset = IntentDataset(val_examples, tokenizer)
    
    # Training arguments
    batch_size = 32
    num_epochs = 3
    
    training_args = TrainingArguments(
        output_dir='./models',
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        warmup_steps=200,
        logging_dir='./logs',
        logging_steps=50,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        greater_is_better=True,
        fp16=torch.cuda.is_available(),
        dataloader_num_workers=2,
        remove_unused_columns=False,
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )
    
    # Train
    logger.info("🚂 Starting training...")
    logger.info(f"Training for {num_epochs} epochs with batch size {batch_size}")
    start_time = time.time()
    
    try:
        trainer.train()
        
        training_time = (time.time() - start_time) / 60
        logger.info(f"✅ Training completed in {training_time:.1f} minutes")
        
        # Save model
        logger.info("💾 Saving model...")
        trainer.save_model('./models/final')
        tokenizer.save_pretrained('./models/final')
        
        # Evaluate
        logger.info("📊 Evaluating...")
        results = trainer.evaluate()
        logger.info(f"Validation Accuracy: {results.get('eval_accuracy', 0)*100:.2f}%")
        
        # Test on a few examples
        logger.info("\n🧪 Testing on sample inputs:")
        test_texts = [
            "How do I implement a binary search tree?",
            "Write a poem about the ocean",
            "Explain quantum computing",
        ]
        
        model.eval()
        with torch.no_grad():
            for text in test_texts:
                inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
                inputs = {k: v.to(device) for k, v in inputs.items()}
                outputs = model(**inputs)
                predicted = torch.argmax(outputs.logits, dim=-1).item()
                logger.info(f"'{text[:50]}...' → {INTENT_LABELS[predicted]}")
        
        logger.info("\n🎉 All done! Model saved to ./models/final")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise

if __name__ == "__main__":
    train()
EOF

# Step 3: Create simple runner
echo -e "\n🚀 Creating simple runner..."
cat > run_training.sh << 'EOF'
#!/bin/bash
echo "🏃 Starting training with flexible data handling..."
python train_working.py 2>&1 | tee training_output.log
EOF

chmod +x run_training.sh

# Step 4: Summary
echo -e "\n📝 Debug Summary"
echo "================"
echo "1. Data structure has been checked"
echo "2. Created flexible training script: train_working.py"
echo "3. Ready to run with: ./run_training.sh"
echo ""
echo "🎯 Next step: Run ./run_training.sh to start training!"