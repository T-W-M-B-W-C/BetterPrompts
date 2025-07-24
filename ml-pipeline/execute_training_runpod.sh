#!/bin/bash
# Execute training on RunPod

# Configuration
RUNPOD_HOST="root@103.196.86.219"
RUNPOD_PORT="18733"
SSH_KEY="~/.ssh/id_ed25519"

echo "🚀 Starting Training on RunPod..."

# Create training execution script
cat > run_training_commands.sh << 'EOF'
#!/bin/bash
cd /workspace/betterprompts/ml-pipeline

echo "🔍 Checking GPU..."
nvidia-smi

echo "📊 System Info:"
echo "CPU Cores: $(nproc)"
echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "Disk: $(df -h /workspace | tail -1 | awk '{print $4}' ) free"

# Check if training data exists
if [ ! -f "data_generation/openai_training_data.json" ]; then
    echo "❌ Training data not found!"
    echo "Please upload data_generation/openai_training_data.json"
    exit 1
fi

echo "✅ Training data found"
echo "📏 Data size: $(du -h data_generation/openai_training_data.json | cut -f1)"

# Start training with tmux
echo "🏃 Starting training in tmux session..."
tmux new-session -d -s training "python scripts/runpod_train.py --shutdown-delay 15 2>&1 | tee training.log"

echo "📺 Training started in tmux session 'training'"
echo "Commands:"
echo "  - Attach: tmux attach -t training"
echo "  - Detach: Ctrl+B, D"
echo "  - Monitor: tail -f training.log"

# Also start monitoring in another tmux session
tmux new-session -d -s monitor "watch -n 1 nvidia-smi"

echo "🎯 Both sessions started:"
echo "  - training: Main training process"
echo "  - monitor: GPU monitoring"
EOF

# Execute on RunPod
ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_HOST \
    "bash -s" < run_training_commands.sh

rm run_training_commands.sh

echo "
📋 Next Steps:
1. Connect to monitor progress:
   ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_HOST

2. Attach to training:
   tmux attach -t training

3. Check logs:
   tail -f /workspace/betterprompts/ml-pipeline/training.log

4. Download results (after ~25 minutes):
   scp -P $RUNPOD_PORT -i $SSH_KEY $RUNPOD_HOST:/workspace/betterprompts/ml-pipeline/*.tar.gz ./
"