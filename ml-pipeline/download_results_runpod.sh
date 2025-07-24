#!/bin/bash
# Download results from RunPod

RUNPOD_HOST="root@103.196.86.219"
RUNPOD_PORT="18733"
SSH_KEY="~/.ssh/id_ed25519"

echo "📥 Downloading results from RunPod..."

# Create results directory
mkdir -p runpod_results

# Download all result archives
echo "🔍 Finding result files..."
scp -P $RUNPOD_PORT -i $SSH_KEY \
    $RUNPOD_HOST:/workspace/betterprompts/ml-pipeline/runpod_training_results_*.tar.gz \
    runpod_results/

# Download training log
scp -P $RUNPOD_PORT -i $SSH_KEY \
    $RUNPOD_HOST:/workspace/betterprompts/ml-pipeline/training.log \
    runpod_results/

# Extract the latest results
cd runpod_results
latest_archive=$(ls -t runpod_training_results_*.tar.gz | head -1)

if [ -n "$latest_archive" ]; then
    echo "📦 Extracting $latest_archive..."
    tar -xzf "$latest_archive"
    
    echo "✅ Results downloaded and extracted!"
    echo ""
    echo "📁 Contents:"
    ls -la
    
    # Show training summary
    if [ -f "training_summary.json" ]; then
        echo ""
        echo "📊 Training Summary:"
        cat training_summary.json | python -m json.tool
    fi
    
    # Show validation results
    if [ -f "validation_results/validation_results.json" ]; then
        echo ""
        echo "🎯 Model Performance:"
        cat validation_results/validation_results.json | python -m json.tool | grep -E "(accuracy|f1_score)" | head -5
    fi
else
    echo "❌ No result files found!"
fi

echo ""
echo "🚀 Next steps:"
echo "1. Check model: ls models/distilbert_intent_classifier/"
echo "2. Copy integration file: cp distilbert_ml_classifier.py ../../backend/services/intent-classifier/app/models/"
echo "3. Test model: python ../../examples/use_distilbert_model.py"