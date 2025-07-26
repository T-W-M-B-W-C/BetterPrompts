#!/bin/bash
# Quick fix for the training script

echo "🔧 Applying fix..."

# Fix the training script inline
sed -i 's/evaluation_strategy=/eval_strategy=/g' train_model.py

echo "✅ Fix applied! Running training..."

# Run the training
python train_model.py

# Package results
echo -e "\n📦 Packaging results..."
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p results
tar -czf "results/model_${timestamp}.tar.gz" models/final/

echo -e "\n✅ Training complete!"
echo -e "Model saved to: results/model_${timestamp}.tar.gz"