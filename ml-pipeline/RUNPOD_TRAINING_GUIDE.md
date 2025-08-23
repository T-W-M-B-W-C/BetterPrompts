# 🚀 RunPod Training Guide for BetterPrompts Intent Classifier

## Overview
This guide will help you train the BetterPrompts intent classifier model on RunPod GPU instances. The training data has been generated locally with 11,000 examples.

## Prerequisites
- RunPod account with credits
- Generated training data (✅ Already complete - 11K examples)
- SSH access to transfer files

## Step-by-Step Instructions

### 1. Launch RunPod Instance

**Recommended GPU Options** (based on your scripts):
- **RTX 4090** (24GB) - Best value, $0.44/hr
- **RTX 3090** (24GB) - Budget option, $0.24/hr  
- **A100** (40GB) - Premium performance, $1.29/hr
- **V100** (16GB) - Reliable option, $0.59/hr

**Template Selection**:
- Choose "PyTorch 2.0.1" or "RunPod PyTorch"
- Ensure CUDA 11.8+ is included

### 2. Connect to Your Pod

```bash
# Get your pod's IP from RunPod dashboard
ssh root@[YOUR_POD_IP]

# Or use RunPod's web terminal
```

### 3. Initial Setup (Run Once)

```bash
# Download and run setup script
wget https://raw.githubusercontent.com/your-repo/betterprompts/main/ml-pipeline/scripts/setup_runpod.sh
chmod +x setup_runpod.sh
./setup_runpod.sh
```

### 4. Upload Your Training Data

From your **local machine**, upload the generated data:

```bash
# Navigate to your local ml-pipeline directory
cd /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts/ml-pipeline

# Upload the training data (3.4MB file)
scp data/raw/training_data_large.json root@[POD_IP]:/workspace/betterprompts/ml-pipeline/data/raw/

# Also upload the smaller dataset as backup
scp data/raw/training_data.json root@[POD_IP]:/workspace/betterprompts/ml-pipeline/data/raw/
```

### 5. Upload the ML Pipeline Code

```bash
# From your local machine, upload the entire ml-pipeline directory
cd /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts
scp -r ml-pipeline root@[POD_IP]:/workspace/betterprompts/
```

### 6. Install Dependencies on RunPod

```bash
# SSH into RunPod
ssh root@[POD_IP]

# Navigate to project
cd /workspace/betterprompts/ml-pipeline

# Install Python dependencies
pip install torch==2.0.1+cu118 -f https://download.pytorch.org/whl/torch_stable.html
pip install transformers==4.35.0 datasets==2.14.0 accelerate==0.24.0
pip install scikit-learn pandas numpy loguru tqdm tensorboard
pip install nvidia-ml-py3 gpustat
```

### 7. Modify Training Script for Your Data

The `runpod_train.py` script expects data at a specific path. Update it:

```bash
# On RunPod, edit the script
cd /workspace/betterprompts/ml-pipeline
nano scripts/runpod_train.py

# Change line 102 from:
# "training_data_exists": os.path.exists("data_generation/openai_training_data.json"),
# To:
# "training_data_exists": os.path.exists("data/raw/training_data_large.json"),

# Also update line 157-158 from:
# "--data-path", "data_generation/openai_training_data.json",
# To:
# "--data-path", "data/raw/training_data_large.json",
```

### 8. Run Training

**Option A: Using the automated RunPod trainer**
```bash
cd /workspace/betterprompts/ml-pipeline
python scripts/runpod_train.py --no-shutdown
```

**Option B: Direct training with intent classifier**
```bash
cd /workspace/betterprompts/ml-pipeline
python scripts/train_intent_classifier.py \
  --config configs/ml_pipeline_config.yaml \
  --data-path data/raw/training_data_large.json \
  --num-epochs 5 \
  --batch-size 32
```

**Option C: Train DistilBERT model (faster)**
```bash
cd /workspace/betterprompts/ml-pipeline
python scripts/train_distilbert_classifier.py \
  --data-path data/raw/training_data_large.json \
  --output-dir models/distilbert_intent_classifier \
  --num-epochs 5 \
  --batch-size 64
```

### 9. Monitor Training

```bash
# In a new terminal/tmux pane
watch -n 1 nvidia-smi  # Monitor GPU usage

# Or use the aliases from setup
gpu   # Monitor GPU
gpus  # Detailed GPU stats

# View TensorBoard (if available)
tensorboard --logdir models --host 0.0.0.0 --port 6006
```

### 10. Download Results

After training completes:

```bash
# The script will create a packaged archive
# Download from your local machine:
scp root@[POD_IP]:/workspace/betterprompts/ml-pipeline/runpod_training_results_*.tar.gz ./

# Or download specific model files
scp -r root@[POD_IP]:/workspace/betterprompts/ml-pipeline/models ./trained_models
```

## Expected Training Times

Based on GPU and 11,000 examples:
- **RTX 4090**: ~15-20 minutes
- **RTX 3090**: ~20-30 minutes
- **A100**: ~10-15 minutes
- **V100**: ~25-35 minutes

## Cost Estimates

For complete training:
- **RTX 4090**: ~$0.15 - $0.22
- **RTX 3090**: ~$0.08 - $0.12
- **A100**: ~$0.32 - $0.43
- **V100**: ~$0.25 - $0.35

## Troubleshooting

### Issue: CUDA Out of Memory
```bash
# Reduce batch size
python scripts/train_intent_classifier.py --batch-size 16
```

### Issue: Module Not Found
```bash
# Add to Python path
export PYTHONPATH=/workspace/betterprompts/ml-pipeline:$PYTHONPATH
```

### Issue: Data Not Found
```bash
# Check data location
ls -la /workspace/betterprompts/ml-pipeline/data/raw/
# Ensure training_data_large.json exists
```

### Issue: Slow Training
```bash
# Enable mixed precision training
python scripts/train_intent_classifier.py --fp16
```

## Quick One-Liner Setup (Advanced)

For experienced users, after SSH:
```bash
cd /workspace && \
git clone https://github.com/your-repo/betterprompts.git && \
cd betterprompts/ml-pipeline && \
pip install -r requirements.txt && \
echo "Upload data to data/raw/training_data_large.json then run: python scripts/train_intent_classifier.py"
```

## Notes

- The `runpod_train.py` script includes auto-shutdown after training (default 10 minutes)
- Use `--no-shutdown` flag to keep the pod running
- GPU monitoring is built into the training script
- Results are automatically packaged as `.tar.gz` for easy download
- The generated data (11K examples) is sufficient for good model performance

## Support Files Created

- `training_summary.json` - Training metrics and configuration
- `validation_results/` - Model validation results
- `models/` - Trained model files
- `*.tar.gz` - Packaged results for download