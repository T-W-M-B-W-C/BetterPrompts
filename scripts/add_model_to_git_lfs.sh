#!/bin/bash

# Script to add trained model to Git LFS
# Run this on RunPod after training completes

set -e

echo "🔍 Checking Git LFS status..."
git lfs version

echo "📁 Checking model directory..."
MODEL_DIR="ml-pipeline/models/distilbert_intent_classifier"

if [ ! -d "$MODEL_DIR" ]; then
    echo "❌ Model directory not found: $MODEL_DIR"
    echo "Please ensure you're in the BetterPrompts directory and the model has been trained."
    exit 1
fi

echo "📊 Model files found:"
ls -lah "$MODEL_DIR"

# Calculate total size
TOTAL_SIZE=$(du -sh "$MODEL_DIR" | cut -f1)
echo "📦 Total model size: $TOTAL_SIZE"

echo ""
echo "🔧 Adding model files to Git..."

# Track any additional patterns if needed
git lfs track "*.model"
git lfs track "*.json"
git add .gitattributes

# Add the model files
git add "$MODEL_DIR"

echo ""
echo "📝 Creating commit..."
git commit -m "feat(ml-pipeline): add trained DistilBERT intent classifier model

- Trained on 10,020 examples
- Achieved high accuracy on test set
- Model files tracked with Git LFS
- Includes tokenizer and config files
- Ready for deployment to TorchServe"

echo ""
echo "🚀 Pushing to remote (this may take a while for large files)..."
git push origin phase04-completion

echo ""
echo "✅ Model successfully added to Git with LFS!"
echo ""
echo "📥 To pull this model on another machine, use:"
echo "   git lfs pull"
echo ""
echo "🎯 Model location: $MODEL_DIR"