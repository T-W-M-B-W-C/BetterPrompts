#!/bin/bash

# Transfer script for uploading data to RunPod
# This uses RunPodCTL for file transfer

echo "🚀 BetterPrompts RunPod Data Transfer Script"
echo "==========================================="

# Check if runpodctl is installed
if ! command -v runpodctl &> /dev/null; then
    echo "❌ runpodctl not found. Please install it first:"
    echo "   brew install runpod/runpodctl/runpodctl"
    exit 1
fi

# Check if API key is configured
if ! runpodctl config get apiKey &> /dev/null; then
    echo "❌ RunPod API key not configured."
    echo "   Please run: runpodctl config --apiKey YOUR_API_KEY"
    exit 1
fi

# Your pod ID (extracted from SSH username)
POD_ID="4s55m34wvxlnyo"

echo "📋 Pod ID: $POD_ID"
echo ""

# Step 1: List pods to verify connection
echo "🔍 Verifying pod connection..."
runpodctl pod list | grep $POD_ID

if [ $? -ne 0 ]; then
    echo "❌ Pod not found. Please check your pod ID."
    exit 1
fi

# Step 2: Create workspace directory on pod
echo "📁 Creating workspace directory on pod..."
runpodctl exec $POD_ID "mkdir -p /workspace/betterprompts/ml-pipeline/data/raw"

# Step 3: Upload training data
echo "📤 Uploading training data..."
LOCAL_DATA="/Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts/ml-pipeline/data/raw/training_data_large.json"
REMOTE_PATH="/workspace/betterprompts/ml-pipeline/data/raw/"

if [ -f "$LOCAL_DATA" ]; then
    runpodctl send $POD_ID "$LOCAL_DATA" "$REMOTE_PATH"
    echo "✅ Training data uploaded"
else
    echo "❌ Training data not found at $LOCAL_DATA"
    exit 1
fi

# Step 4: Upload training scripts
echo "📤 Uploading training scripts..."

# Upload the complete training script
runpodctl send $POD_ID "runpod_complete_training.py" "/workspace/betterprompts/ml-pipeline/"

# Upload the original training scripts if needed
if [ -d "scripts" ]; then
    runpodctl send $POD_ID "scripts/" "/workspace/betterprompts/ml-pipeline/"
    echo "✅ Scripts uploaded"
fi

# Step 5: Upload configs if they exist
if [ -d "configs" ]; then
    echo "📤 Uploading configs..."
    runpodctl send $POD_ID "configs/" "/workspace/betterprompts/ml-pipeline/"
    echo "✅ Configs uploaded"
fi

# Step 6: Upload source code
if [ -d "src" ]; then
    echo "📤 Uploading source code..."
    runpodctl send $POD_ID "src/" "/workspace/betterprompts/ml-pipeline/"
    echo "✅ Source code uploaded"
fi

echo ""
echo "✅ All files uploaded successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Connect to your pod:"
echo "   runpodctl exec $POD_ID bash"
echo ""
echo "2. Navigate to the project:"
echo "   cd /workspace/betterprompts/ml-pipeline"
echo ""
echo "3. Run the training:"
echo "   python runpod_complete_training.py"
echo ""
echo "4. After training, download results:"
echo "   runpodctl receive $POD_ID /workspace/betterprompts/ml-pipeline/training_results_*.tar.gz ./"
echo ""
echo "5. Shutdown the pod when done:"
echo "   runpodctl stop $POD_ID"