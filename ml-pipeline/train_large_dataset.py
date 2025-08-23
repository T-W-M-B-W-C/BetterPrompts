#!/usr/bin/env python3
"""
Simple training script for large datasets on RunPod
Uses the working train_distilbert.py with your data
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Check if we're in the right directory
    if not os.path.exists("train_distilbert.py"):
        print("Error: train_distilbert.py not found!")
        print("Please run from /workspace/BetterPrompts/ml-pipeline/")
        return 1
    
    # Get data path from user or use default
    data_path = input("Enter path to your training data (or press Enter for default): ").strip()
    
    if not data_path:
        # Default path - change this to your actual data location
        data_path = "data_generation/openai_training_data.json"
    
    # Check if data exists
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        print("Please provide the correct path to your training data.")
        return 1
    
    print(f"\n🚀 Starting training with data from: {data_path}")
    print("=" * 60)
    
    # Training command - same as the working one but with your data
    cmd = [
        "python", "train_distilbert.py",
        "--data-path", data_path,
        "--output-dir", "models/distilbert_intent_classifier",
        "--num-epochs", "5",
        "--batch-size", "32",  # Adjust based on your GPU memory
        "--learning-rate", "5e-5",
        "--fp16",  # Mixed precision for faster training
        "--export-onnx"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 60)
    
    # Run training
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ Training completed successfully!")
        print("Model saved to: models/distilbert_intent_classifier/")
    else:
        print(f"\n❌ Training failed with code {result.returncode}")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())