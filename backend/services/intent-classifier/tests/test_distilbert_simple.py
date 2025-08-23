#!/usr/bin/env python3
"""Simple DistilBERT integration test"""

import sys
from pathlib import Path

# Test if model files exist
model_path = Path("../../../ml-pipeline/models/distilbert_intent_classifier").resolve()
print(f"Model path: {model_path}")
print(f"Model exists: {model_path.exists()}")

if model_path.exists():
    files = list(model_path.glob("*.json")) + list(model_path.glob("*.safetensors"))
    print(f"Found {len(files)} model files")
    for f in files[:5]:
        print(f"  - {f.name}")

# Try to load model directly
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    
    print("\nLoading DistilBERT model...")
    tokenizer = AutoTokenizer.from_pretrained(str(model_path))
    model = AutoModelForSequenceClassification.from_pretrained(str(model_path))
    
    print("Model loaded successfully!")
    print(f"Model type: {model.config.model_type}")
    print(f"Num labels: {model.config.num_labels}")
    
    # Test inference
    text = "Write a Python function to sort a list"
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)
        
    print(f"\nTest inference on: '{text}'")
    print(f"Output shape: {logits.shape}")
    print(f"Max probability: {probs.max().item():.3f}")
    print(f"Predicted class: {probs.argmax().item()}")
    
except Exception as e:
    print(f"\nError loading model: {e}")
    import traceback
    traceback.print_exc()