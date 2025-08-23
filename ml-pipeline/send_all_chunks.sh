#!/bin/bash

echo "🚀 Sending all training data chunks to RunPod"
echo "="*60

# Send reassembly script first
echo "📤 Sending reassembly script..."
runpodctl send data/chunks/reassemble_chunks.py &
REASSEMBLE_PID=$!
sleep 2

# Send each chunk
for i in {00..10}; do
    echo "📤 Sending chunk $i..."
    runpodctl send data/chunks/training_chunk_${i}.json &
    CHUNK_PID=$!
    sleep 2  # Small delay between transfers
done

# Also send the training script
echo "📤 Sending training script..."
runpodctl send runpod_complete_training.py &

echo ""
echo "✅ All chunks sent!"
echo ""
echo "📝 The transfer codes will appear above."
echo "   Copy all the codes and run them on RunPod with:"
echo "   runpodctl receive <code>"
echo ""
echo "After receiving all files on RunPod:"
echo "1. python reassemble_chunks.py"
echo "2. python runpod_complete_training.py"

wait