#!/usr/bin/env python3
"""Test the full classifier integration with DistilBERT"""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

# Minimal config setup
import os
os.environ["MODEL_NAME"] = "distilbert"
os.environ["USE_TORCHSERVE"] = "false"
os.environ["ENABLE_ADAPTIVE_ROUTING"] = "false"

from app.models.classifier import IntentClassifier

async def test():
    classifier = IntentClassifier()
    
    print("Initializing classifier...")
    await classifier.initialize_model()
    
    test_cases = [
        ("Write a Python function to sort a list", "code_generation"),
        ("What is the capital of France?", "question_answering"),
        ("Translate this to Spanish: Hello world", "translation"),
        ("Analyze sales data and create a report", "data_analysis"),
        ("Help me plan a project timeline", "task_planning"),
    ]
    
    print("\n" + "="*60)
    for prompt, expected in test_cases:
        print(f"\nPrompt: {prompt}")
        try:
            result = await classifier.classify(prompt)
            print(f"  Intent: {result['intent']} (expected: {expected})")
            print(f"  Confidence: {result['confidence']:.3f}")
            print(f"  Method: {result.get('classification_method', 'unknown')}")
            print(f"  Complexity: {result['complexity']}")
            
            # Check if using DistilBERT
            if result.get('classification_method') == 'distilbert':
                print("  ✓ Using DistilBERT model")
            else:
                print(f"  ⚠ Using fallback: {result.get('classification_method')}")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "="*60)
    await classifier.cleanup()
    print("\nIntegration test complete!")

if __name__ == "__main__":
    asyncio.run(test())