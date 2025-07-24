#!/usr/bin/env python3
"""Quick test script to verify model after training."""

import torch
from transformers import AutoTokenizer, DistilBertForSequenceClassification
import json

def test_model():
    """Test the trained model with sample inputs."""
    print("🔍 Loading trained model...")
    
    # Load model and tokenizer
    model_path = "models/final"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = DistilBertForSequenceClassification.from_pretrained(model_path)
    
    # Load config for labels
    with open("configs/training_config.json", "r") as f:
        config = json.load(f)
    intent_labels = config["intent_labels"]
    
    # Test examples
    test_inputs = [
        "How do I implement a binary search tree in Python?",
        "Write a poem about artificial intelligence",
        "Explain quantum computing in simple terms",
        "What are the benefits of renewable energy?",
        "Translate 'Hello world' to French"
    ]
    
    print("\n📊 Testing model predictions:\n")
    
    model.eval()
    with torch.no_grad():
        for text in test_inputs:
            # Tokenize
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
            
            # Predict
            outputs = model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            predicted_class = torch.argmax(predictions, dim=-1).item()
            confidence = predictions[0][predicted_class].item()
            
            print(f"Input: {text}")
            print(f"Predicted: {intent_labels[predicted_class]} (confidence: {confidence:.2%})")
            print("-" * 50)
    
    print("\n✅ Model test complete!")

if __name__ == "__main__":
    test_model()