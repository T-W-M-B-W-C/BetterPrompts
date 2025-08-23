#!/usr/bin/env python3
"""
Execute commands on RunPod to receive files and run training
"""

import subprocess
import os

# First receive the training script
print("📥 Receiving training script...")
os.system("runpodctl receive 4356-bahama-joshua-genetic-0")

# Check if file was received
if os.path.exists("runpod_training_simple.py"):
    print("✅ Training script received!")
    
    # Run the training script
    print("🚀 Starting training...")
    exec(open("runpod_training_simple.py").read())
else:
    print("❌ Failed to receive training script")
    print("Current directory contents:")
    os.system("ls -la")