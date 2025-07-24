#!/bin/bash
# Monitor RunPod training progress

RUNPOD_HOST="root@103.196.86.219"
RUNPOD_PORT="18733"
SSH_KEY="~/.ssh/id_ed25519"

echo "📊 RunPod Training Monitor"
echo "========================="

while true; do
    clear
    echo "📊 RunPod Training Monitor - $(date)"
    echo "=================================="
    
    # Check training status
    echo -e "\n🏃 Training Status:"
    ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_HOST \
        "cd /workspace/betterprompts/ml-pipeline && tail -n 20 training.log 2>/dev/null | grep -E '(Epoch|Step|accuracy|loss|Complete)' | tail -5"
    
    # GPU Status
    echo -e "\n🎮 GPU Status:"
    ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_HOST \
        "nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader"
    
    # Check for completion
    ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_HOST \
        "ls /workspace/betterprompts/ml-pipeline/runpod_training_results_*.tar.gz 2>/dev/null" > /dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "\n✅ Training Complete! Results ready for download."
        echo "Run: ./download_results_runpod.sh"
        break
    fi
    
    echo -e "\nPress Ctrl+C to exit monitor"
    sleep 10
done