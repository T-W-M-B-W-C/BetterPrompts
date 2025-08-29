# RunPod Web Terminal Training Instructions

## Quick Start (Copy & Paste Method)

### Step 1: Access Web Terminal
1. Go to your RunPod dashboard: https://runpod.io/console/pods
2. Find your pod: `betterprompts-training` (ID: 70xp5iv02hq3v4)
3. Click the "Connect" button
4. Select "Connect to Web Terminal"

### Step 2: Receive the Training Script
Once in the web terminal, run this command:
```bash
runpodctl receive 4356-bahama-joshua-genetic-0
```

### Step 3: Run the Training
After receiving the file, run:
```bash
python runpod_training_simple.py
```

The script will:
1. Install all dependencies
2. Create training data (1000 samples)
3. Train a DistilBERT model for 2 epochs
4. Package the results

### Step 4: Download Results
After training completes (about 5-10 minutes on RTX 4090), you'll see a file like `training_results_YYYYMMDD_HHMMSS.tar.gz`

To download it to your local machine, run this on your LOCAL terminal:
```bash
runpodctl receive 70xp5iv02hq3v4 /workspace/betterprompts/ml-pipeline/training_results_*.tar.gz ./
```

### Step 5: Shutdown the Pod
To stop billing, run on your LOCAL terminal:
```bash
runpodctl stop pod 70xp5iv02hq3v4
```

---

## Alternative: Direct Copy-Paste Method

If the receive command doesn't work, you can copy the entire training script directly:

### In the Web Terminal, run:
```bash
cd /workspace
mkdir -p betterprompts/ml-pipeline
cd betterprompts/ml-pipeline
cat > runpod_training_simple.py << 'EOF'
```

Then paste the entire contents of `runpod_training_simple.py` and press Enter, then type:
```
EOF
```

Then run:
```bash
python runpod_training_simple.py
```

---

## Expected Output

You should see:
```
============================================================
🚀 BetterPrompts Intent Classifier Training
============================================================
📦 Installing dependencies...
✅ Dependencies installed
📝 Creating training data...
✅ Created 1000 training samples
🎯 Starting training...
✅ GPU: NVIDIA GeForce RTX 4090
📊 Dataset: 1000 samples, 10 classes
🤖 Loading DistilBERT model...
🚀 Training started...
[Training progress bars]
✅ Training completed in X.X minutes
💾 Model saved to ./models/distilbert_intent_classifier
📈 Evaluation - Loss: X.XXXX
📦 Packaging results...
✅ Results packaged: training_results_YYYYMMDD_HHMMSS.tar.gz (XX.X MB)
============================================================
📊 TRAINING COMPLETE!
============================================================
```

---

## Troubleshooting

### If you see "CUDA out of memory":
Reduce batch size by editing the script:
```python
per_device_train_batch_size=8  # Instead of 16
```

### If dependencies fail to install:
Run manually:
```bash
pip install transformers datasets accelerate scikit-learn pandas numpy tqdm
```

### If training is too slow:
The script is set for 2 epochs for quick training. This should take about 5-10 minutes on RTX 4090.

---

## Cost Estimate

- RTX 4090 at $0.34/hour
- Training time: ~10 minutes
- Total cost: ~$0.06

---

## Your Pod Details

- **Pod ID**: 70xp5iv02hq3v4
- **Pod Name**: betterprompts-training
- **GPU**: 1x RTX 4090
- **Cost**: $0.340/hour
- **Transfer Code**: 4356-bahama-joshua-genetic-0