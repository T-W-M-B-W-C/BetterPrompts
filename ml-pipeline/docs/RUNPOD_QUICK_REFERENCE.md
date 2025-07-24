# RunPod Quick Reference Guide

## 🚀 Quick Start (5 Minutes)

### 1. Launch RunPod Instance
1. Go to [runpod.io](https://runpod.io)
2. Click "GPU Pods" → "Deploy"
3. Select **RTX 3090** (best value)
4. Choose **PyTorch 2.0.1** template
5. Set **50GB** disk
6. Deploy!

### 2. Connect & Setup (Copy-Paste Commands)
```bash
# SSH into your pod
ssh root@[YOUR_POD_IP]

# Quick setup (one command)
curl -fsSL https://raw.githubusercontent.com/your-repo/main/ml-pipeline/scripts/setup_runpod.sh | bash
```

### 3. Upload Your Data
```bash
# From your local machine
scp ml-pipeline/data_generation/openai_training_data.json \
    root@[POD_IP]:/workspace/betterprompts/ml-pipeline/data_generation/
```

### 4. Start Training
```bash
# On RunPod
cd /workspace/betterprompts/ml-pipeline
python scripts/runpod_train.py
```

### 5. Download Results
```bash
# From your local machine (after ~25 minutes)
scp root@[POD_IP]:/workspace/betterprompts/ml-pipeline/*.tar.gz ./
```

## 📊 Monitoring Commands

```bash
# Watch GPU usage
watch -n 1 nvidia-smi

# Monitor training progress
python scripts/runpod_monitor.py

# Check logs
tail -f models/distilbert_intent_classifier/logs/train.log

# Start TensorBoard
tensorboard --logdir models --host 0.0.0.0 --port 6006
```

## 💰 Cost Estimates

| GPU | Time | Cost |
|-----|------|------|
| RTX 3090 | 25 min | $0.14 |
| RTX 3090 Spot | 25 min | $0.05 |
| RTX 4090 | 20 min | $0.15 |

## 🛠️ Troubleshooting

### CUDA Out of Memory
```bash
# Reduce batch size
python train_distilbert.py --batch-size 32
```

### Connection Lost
```bash
# Use tmux to persist session
tmux new -s training
python scripts/runpod_train.py
# Detach: Ctrl+B, D
# Reattach: tmux attach -t training
```

### Slow Upload
```bash
# Compress first
tar -czf ml-pipeline.tar.gz ml-pipeline/
scp ml-pipeline.tar.gz root@[POD_IP]:/workspace/
# On RunPod
tar -xzf ml-pipeline.tar.gz
```

## ⚡ Speed Optimizations

```python
# Optimal settings for RTX 3090
python train_distilbert.py \
    --batch-size 64 \
    --fp16 \
    --num-epochs 5 \
    --learning-rate 5e-5
```

## 📦 What You Get

After training completes:
- `runpod_training_results_[timestamp].tar.gz` containing:
  - Trained model (250MB)
  - ONNX optimized model (65MB)
  - Validation results (89%+ accuracy)
  - Training summary JSON

## 🔄 Resume from Checkpoint

If interrupted:
```bash
python train_distilbert.py \
    --resume_from_checkpoint models/distilbert_intent_classifier/checkpoint-latest
```

## 📈 Next Steps

1. Extract your results:
   ```bash
   tar -xzf runpod_training_results_*.tar.gz
   ```

2. Copy model to intent classifier:
   ```bash
   cp distilbert_ml_classifier.py ../backend/services/intent-classifier/app/models/
   ```

3. Test the model:
   ```bash
   python examples/use_distilbert_model.py
   ```

## 🚨 Important Notes

- Pod auto-shuts down after 10 minutes post-training
- Use `--no-shutdown` to keep pod alive
- Spot instances save 70% but may be interrupted
- Always use tmux/screen for long sessions

## 📞 Support

- RunPod Discord: [discord.gg/runpod](https://discord.gg/runpod)
- RunPod Docs: [docs.runpod.io](https://docs.runpod.io)

---

**Pro Tip**: Save this guide locally before starting! 📎