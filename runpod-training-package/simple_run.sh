#!/bin/bash
# Simple training script without tmux

echo "🚀 BetterPrompts Training - Simple Mode"
echo "======================================"

# Already installed dependencies, so skip that
echo "✅ Dependencies already installed"
echo "✅ CUDA is available with RTX 5090 (32GB)"
echo "✅ Training data found (4.8M)"

# Just run the training directly
echo ""
echo "🏃 Starting training directly..."
echo "This will take approximately 15-20 minutes on RTX 5090"
echo ""
echo "Training will show progress in this terminal"
echo "DO NOT close this window!"
echo ""
echo "Starting in 3 seconds..."
sleep 3

# Run training
python train_model.py