# RunPod A40 Training Package - One Command Solution

## 🚀 Quickstart (3 Steps)

### Step 1: Upload to RunPod
```bash
scp -r runpod-a40-package root@[IP]:[PORT]:/workspace/
```

### Step 2: SSH and Run
```bash
ssh -p [PORT] root@[IP]
cd /workspace/runpod-a40-package
chmod +x perform_training.sh
./perform_training.sh
```

### Step 3: Download Results
```bash
scp -P [PORT] root@[IP]:/workspace/runpod-a40-package/results/model_*.tar.gz ./
```

## ⏱️ Time Estimate
- **A40 GPU**: ~10-15 minutes
- **RTX 4090**: ~15-20 minutes
- **RTX 3090**: ~20-25 minutes

## 📦 What You Get
- Trained DistilBERT model
- 10 intent classes
- Packaged as `model_[timestamp].tar.gz`
- Ready for production use

## 🎯 Features
- Auto-detects GPU and optimizes batch size
- Handles any data format automatically
- Creates sample data if needed
- One command does everything
- No manual configuration required

That's it! Just copy, run, and download. 🎉