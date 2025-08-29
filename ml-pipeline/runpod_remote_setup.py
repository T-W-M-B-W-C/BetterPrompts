#!/usr/bin/env python3
"""
RunPod Remote Setup and Training Script
This script will be executed on the RunPod instance to:
1. Receive the transferred files
2. Set up the environment
3. Run the training
"""

import os
import sys
import subprocess
import time

def run_command(cmd):
    """Run a shell command and print output"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode

def main():
    print("="*60)
    print("🚀 RunPod Training Setup for BetterPrompts")
    print("="*60)
    
    # Step 1: Create workspace
    print("\n📁 Creating workspace...")
    os.makedirs("/workspace/betterprompts/ml-pipeline/data/raw", exist_ok=True)
    os.chdir("/workspace/betterprompts/ml-pipeline")
    
    # Step 2: Receive training data
    print("\n📥 Receiving training data...")
    run_command("runpodctl receive 3346-memphis-airport-ozone-6")
    
    # Step 3: Receive training script
    print("\n📥 Receiving training script...")
    run_command("runpodctl receive 1253-madam-bali-manager-7")
    
    # Step 4: Install dependencies
    print("\n📦 Installing dependencies...")
    run_command("pip install -q torch==2.0.1+cu118 -f https://download.pytorch.org/whl/torch_stable.html")
    run_command("pip install -q transformers==4.35.0 datasets==2.14.0 accelerate==0.24.0")
    run_command("pip install -q scikit-learn pandas numpy loguru tqdm tensorboard")
    run_command("pip install -q nvidia-ml-py3 gpustat")
    
    # Step 5: Check GPU
    print("\n🎮 Checking GPU...")
    run_command("nvidia-smi")
    
    # Step 6: Move data to correct location
    print("\n📂 Organizing files...")
    if os.path.exists("training_data_large.json"):
        run_command("mv training_data_large.json data/raw/")
        print("✅ Training data moved to data/raw/")
    
    # Step 7: Run training
    print("\n🚀 Starting training...")
    print("="*60)
    
    # Execute the training script
    if os.path.exists("runpod_complete_training.py"):
        exec(open("runpod_complete_training.py").read())
    else:
        print("❌ Training script not found!")
        print("Available files:")
        run_command("ls -la")

if __name__ == "__main__":
    main()