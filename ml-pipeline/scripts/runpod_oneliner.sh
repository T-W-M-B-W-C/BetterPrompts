#!/bin/bash
# One-liner setup for RunPod
# Usage: curl -fsSL https://your-repo/runpod_oneliner.sh | bash

echo "🚀 BetterPrompts RunPod Setup"

# Install dependencies
apt-get update -qq && apt-get install -y git wget tmux
pip install torch transformers datasets accelerate scikit-learn loguru tqdm nvidia-ml-py3

# Clone repo
cd /workspace
git clone https://github.com/your-org/betterprompts.git
cd betterprompts/ml-pipeline

# Download training data (update URL)
wget -O data_generation/openai_training_data.json https://your-storage/openai_training_data.json

# Start training
python scripts/runpod_train.py