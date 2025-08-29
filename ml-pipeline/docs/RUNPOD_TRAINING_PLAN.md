# RunPod Training Plan for Wave 5: DistilBERT Fine-tuning

## Overview

This plan outlines how to conduct the Wave 5 DistilBERT fine-tuning on RunPod's cloud GPU infrastructure, reducing training time from hours to ~20-30 minutes while optimizing costs.

## 1. RunPod Instance Selection

### Recommended GPU Options

#### Option A: RTX 4090 (Best Performance)
- **GPU**: NVIDIA RTX 4090 (24GB VRAM)
- **Cost**: ~$0.44/hour
- **Training Time**: ~15-20 minutes
- **Total Cost**: ~$0.15-0.20

#### Option B: RTX 3090 (Good Balance)
- **GPU**: NVIDIA RTX 3090 (24GB VRAM)
- **Cost**: ~$0.34/hour
- **Training Time**: ~20-25 minutes
- **Total Cost**: ~$0.15-0.17

#### Option C: A40 (Production Grade)
- **GPU**: NVIDIA A40 (48GB VRAM)
- **Cost**: ~$0.79/hour
- **Training Time**: ~15-20 minutes
- **Total Cost**: ~$0.25-0.30

### Instance Configuration
```yaml
recommended_specs:
  gpu: "RTX 3090"  # Best value for this task
  cpu_cores: 8
  ram: 32GB
  storage: 50GB  # For model checkpoints
  container: "runpod/pytorch:2.0.1-py3.10-cuda11.8"
```

## 2. Environment Setup

### Step 1: Create RunPod Account and Add Credits
1. Sign up at https://runpod.io
2. Add $10-20 credits (enough for multiple training runs)
3. Generate API key for programmatic access

### Step 2: Launch GPU Pod
```bash
# Using RunPod CLI (optional)
pip install runpodctl
runpodctl login

# Or use web interface to select:
# - RTX 3090 instance
# - PyTorch 2.0 template
# - 50GB disk
```

### Step 3: Initial Setup Script
Create `setup_runpod.sh`:
```bash
#!/bin/bash
# RunPod environment setup script

echo "=== Setting up RunPod environment for Wave 5 training ==="

# Update system
apt-get update && apt-get install -y \
    git \
    wget \
    unzip \
    htop \
    nvtop \
    tmux

# Install Python dependencies
pip install --upgrade pip
pip install \
    transformers==4.35.0 \
    torch==2.0.1 \
    datasets \
    accelerate \
    scikit-learn \
    loguru \
    tqdm \
    tensorboard \
    onnx \
    onnxruntime-gpu

# Create working directory
mkdir -p /workspace/betterprompts
cd /workspace/betterprompts

echo "✅ Environment setup complete!"
```

## 3. Data Transfer Strategy

### Option A: Direct Upload (Recommended for Small Data)
```bash
# From local machine
scp -r ml-pipeline root@[RUNPOD_IP]:/workspace/betterprompts/

# Or use rsync for better reliability
rsync -avz --progress ml-pipeline/ root@[RUNPOD_IP]:/workspace/betterprompts/ml-pipeline/
```

### Option B: Git Clone (Best for Code)
```bash
# On RunPod instance
git clone https://github.com/your-org/betterprompts.git
cd betterprompts/ml-pipeline
```

### Option C: Cloud Storage (Best for Large Data)
```bash
# Upload to S3/GCS first, then download on RunPod
aws s3 cp ml-pipeline/data_generation/openai_training_data.json s3://your-bucket/
# On RunPod
aws s3 cp s3://your-bucket/openai_training_data.json data_generation/
```

## 4. Automated Training Pipeline

### Create `runpod_train.py`:
```python
#!/usr/bin/env python3
"""Automated training script for RunPod with monitoring."""

import os
import sys
import time
import subprocess
from datetime import datetime
import nvidia_ml_py3 as nvml

def monitor_gpu():
    """Monitor GPU usage during training."""
    nvml.nvmlInit()
    handle = nvml.nvmlDeviceGetHandleByIndex(0)
    
    info = nvml.nvmlDeviceGetMemoryInfo(handle)
    gpu_util = nvml.nvmlDeviceGetUtilizationRates(handle)
    
    print(f"GPU Memory: {info.used/1e9:.1f}GB / {info.total/1e9:.1f}GB")
    print(f"GPU Utilization: {gpu_util.gpu}%")
    
def run_training():
    """Run the complete training pipeline."""
    start_time = datetime.now()
    
    # Verify GPU
    print("🔍 Checking GPU availability...")
    result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
    print(result.stdout[:500])
    
    # Run training with optimal settings for GPU
    print("\n🚀 Starting DistilBERT training...")
    cmd = [
        "python", "train_distilbert.py",
        "--data-path", "data_generation/openai_training_data.json",
        "--output-dir", "models/distilbert_intent_classifier",
        "--num-epochs", "5",
        "--batch-size", "64",  # Larger batch size for GPU
        "--learning-rate", "5e-5",
        "--fp16",  # Mixed precision for faster training
        "--export-onnx"
    ]
    
    # Run with real-time output
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    
    for line in iter(process.stdout.readline, ''):
        print(line.rstrip())
        
        # Monitor GPU every 100 lines
        if "step" in line.lower():
            monitor_gpu()
    
    process.wait()
    
    # Calculate duration
    duration = (datetime.now() - start_time).total_seconds() / 60
    print(f"\n✅ Training completed in {duration:.1f} minutes")
    
    # Run validation
    print("\n📊 Running validation...")
    subprocess.run([
        "python", "scripts/validate_model_accuracy.py",
        "--model-path", "models/distilbert_intent_classifier",
        "--data-path", "data_generation/openai_training_data.json"
    ])
    
    # Package results
    print("\n📦 Packaging results...")
    subprocess.run([
        "tar", "-czf", 
        f"training_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz",
        "models/", "validation_results/"
    ])
    
    print("\n🎉 All done! Download your results:")
    print("   scp root@[RUNPOD_IP]:/workspace/betterprompts/*.tar.gz ./")

if __name__ == "__main__":
    run_training()
```

### Create `runpod_quick_start.sh`:
```bash
#!/bin/bash
# Quick start script for RunPod

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== BetterPrompts Wave 5 RunPod Training ===${NC}"

# Check if we're on RunPod
if [ ! -d "/workspace" ]; then
    echo "❌ This script should be run on a RunPod instance!"
    exit 1
fi

# Setup working directory
cd /workspace
if [ ! -d "betterprompts" ]; then
    echo -e "${BLUE}📥 Downloading training code...${NC}"
    git clone https://github.com/your-org/betterprompts.git
fi

cd betterprompts/ml-pipeline

# Install dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
pip install -r requirements.txt

# Check for training data
if [ ! -f "data_generation/openai_training_data.json" ]; then
    echo -e "${BLUE}📊 Downloading training data...${NC}"
    # Download from your storage
    wget https://your-storage/openai_training_data.json -O data_generation/openai_training_data.json
fi

# Start training with monitoring
echo -e "${GREEN}🚀 Starting training with GPU monitoring...${NC}"
python runpod_train.py

# Keep pod alive for result download
echo -e "${GREEN}✅ Training complete! Pod will stay active for 30 minutes.${NC}"
echo "Download results with:"
echo "  scp root@$(hostname -I | awk '{print $1}'):/workspace/betterprompts/*.tar.gz ./"
sleep 1800
```

## 5. Execution Workflow

### Step 1: Launch RunPod Instance
1. Go to RunPod dashboard
2. Select "GPU Pods" → "Deploy"
3. Choose RTX 3090
4. Select PyTorch template
5. Set disk to 50GB
6. Deploy

### Step 2: Connect and Setup
```bash
# SSH into instance
ssh root@[RUNPOD_IP]

# Run setup
curl -O https://your-repo/setup_runpod.sh
bash setup_runpod.sh
```

### Step 3: Transfer Data and Code
```bash
# From local machine
rsync -avz ml-pipeline/ root@[RUNPOD_IP]:/workspace/betterprompts/ml-pipeline/
```

### Step 4: Run Training
```bash
# On RunPod
cd /workspace/betterprompts/ml-pipeline
python runpod_train.py

# Or use tmux for persistent session
tmux new -s training
python runpod_train.py
# Ctrl+B, D to detach
```

### Step 5: Monitor Progress
```bash
# Watch GPU usage
watch -n 1 nvidia-smi

# Monitor training logs
tail -f models/distilbert_intent_classifier/logs/events*

# Check TensorBoard (optional)
tensorboard --logdir models/distilbert_intent_classifier/logs --host 0.0.0.0
```

### Step 6: Download Results
```bash
# From local machine
scp root@[RUNPOD_IP]:/workspace/betterprompts/training_results_*.tar.gz ./

# Extract
tar -xzf training_results_*.tar.gz
```

## 6. Cost Optimization

### Auto-Shutdown Script
```python
# add to runpod_train.py
def auto_shutdown(delay_minutes=5):
    """Auto-shutdown pod after delay."""
    print(f"⏰ Pod will shut down in {delay_minutes} minutes...")
    time.sleep(delay_minutes * 60)
    subprocess.run(["shutdown", "-h", "now"])
```

### Spot Instances
- Use RunPod's spot instances for 50-70% savings
- Good for non-critical training runs
- May be interrupted (rare for short runs)

### Preemptible Strategy
```bash
# Save checkpoints frequently
--save_steps 100
--save_total_limit 3

# Resume from checkpoint if interrupted
--resume_from_checkpoint models/distilbert_intent_classifier/checkpoint-latest
```

## 7. Monitoring and Debugging

### Real-time Monitoring Dashboard
```python
# Create monitoring_dashboard.py
import time
import subprocess
import psutil
from rich.console import Console
from rich.table import Table
from rich.live import Live

def get_system_stats():
    # GPU stats
    gpu_info = subprocess.run(
        ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
        capture_output=True, text=True
    ).stdout.strip().split(',')
    
    # System stats
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    
    return {
        "gpu_util": f"{gpu_info[0]}%",
        "gpu_mem": f"{float(gpu_info[1])/1000:.1f}GB / {float(gpu_info[2])/1000:.1f}GB",
        "cpu": f"{cpu_percent}%",
        "ram": f"{memory.percent}%"
    }

def create_dashboard():
    table = Table(title="Training Monitor")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    stats = get_system_stats()
    for key, value in stats.items():
        table.add_row(key, value)
    
    return table

# Run dashboard
console = Console()
with Live(create_dashboard(), refresh_per_second=1) as live:
    while True:
        time.sleep(1)
        live.update(create_dashboard())
```

## 8. Troubleshooting

### Common Issues and Solutions

#### CUDA Out of Memory
```bash
# Reduce batch size
--batch_size 32  # or even 16

# Enable gradient checkpointing
--gradient_checkpointing
```

#### Connection Timeout
```bash
# Use tmux or screen
tmux new -s training
# Run training
# Detach: Ctrl+B, D
# Reattach: tmux attach -t training
```

#### Slow Data Transfer
```bash
# Compress before transfer
tar -czf ml-pipeline.tar.gz ml-pipeline/
scp ml-pipeline.tar.gz root@[IP]:/workspace/
# On RunPod
tar -xzf ml-pipeline.tar.gz
```

## 9. Integration with CI/CD

### GitHub Actions RunPod Integration
```yaml
name: Train on RunPod
on:
  workflow_dispatch:
    inputs:
      gpu_type:
        default: 'RTX 3090'
        
jobs:
  train:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to RunPod
        env:
          RUNPOD_API_KEY: ${{ secrets.RUNPOD_API_KEY }}
        run: |
          pip install runpod
          python scripts/deploy_runpod_training.py
```

## 10. Summary

### Quick Reference Commands
```bash
# 1. Launch RTX 3090 pod on RunPod

# 2. SSH and setup
ssh root@[IP]
git clone [your-repo]
cd betterprompts/ml-pipeline
pip install -r requirements.txt

# 3. Run training
python runpod_train.py

# 4. Download results
scp root@[IP]:/workspace/betterprompts/training_results*.tar.gz ./
```

### Expected Outcomes
- **Training Time**: 20-25 minutes
- **Cost**: $0.15-0.20
- **Model Accuracy**: >88%
- **Files Generated**:
  - Trained model (250MB)
  - ONNX model (65MB) 
  - Validation results
  - Training logs

### Next Steps After Training
1. Integrate trained model into intent classifier service
2. Deploy to production with TorchServe
3. Monitor performance on real data
4. Set up continuous training pipeline