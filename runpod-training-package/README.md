# RunPod Training Package

This is a self-contained package for training DistilBERT on RunPod.

## Quick Start

1. Copy this entire directory to RunPod:
   ```bash
   scp -r -P 18733 runpod-training-package root@103.196.86.219:/workspace/
   ```

2. SSH into RunPod:
   ```bash
   ssh -p 18733 root@103.196.86.219
   ```

3. Run the training:
   ```bash
   cd /workspace/runpod-training-package
   ./start_training.sh
   ```

4. Monitor progress:
   ```bash
   ./monitor.sh
   ```

5. Download results (from your local machine after training):
   ```bash
   scp -P 18733 root@103.196.86.219:/workspace/runpod-training-package/results/*.tar.gz ./
   ```

## What's Included

- `start_training.sh` - Main training script
- `monitor.sh` - Monitor training progress
- `train_model.py` - Training code
- `requirements.txt` - Python dependencies
- `configs/` - Training configurations

## Expected Results

- Training time: 20-25 minutes
- Model accuracy: >88%
- Output: Trained model + ONNX export