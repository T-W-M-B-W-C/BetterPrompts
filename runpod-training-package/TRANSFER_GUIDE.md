# Transfer Guide for RunPod

## Method 1: Direct SCP (Recommended)

From your local machine:
```bash
# 1. First, copy the training data if you have it
cp ml-pipeline/data_generation/openai_training_data.json runpod-training-package/data/

# 2. Transfer the entire package
scp -r -P 18733 runpod-training-package root@103.196.86.219:/workspace/
```

Enter the password when prompted.

## Method 2: Using tar archive

```bash
# 1. Create archive
tar -czf runpod-training-package.tar.gz runpod-training-package/

# 2. Transfer archive
scp -P 18733 runpod-training-package.tar.gz root@103.196.86.219:/workspace/

# 3. SSH into RunPod
ssh -p 18733 root@103.196.86.219

# 4. Extract on RunPod
cd /workspace
tar -xzf runpod-training-package.tar.gz
rm runpod-training-package.tar.gz
```

## Method 3: Two-step transfer (if data is large)

```bash
# 1. Transfer code first
scp -r -P 18733 runpod-training-package root@103.196.86.219:/workspace/

# 2. Transfer data separately
scp -P 18733 ml-pipeline/data_generation/openai_training_data.json \
    root@103.196.86.219:/workspace/runpod-training-package/data/
```

## After Transfer

1. SSH into RunPod:
   ```bash
   ssh -p 18733 root@103.196.86.219
   ```

2. Start training:
   ```bash
   cd /workspace/runpod-training-package
   ./start_training.sh
   ```

3. Monitor progress:
   ```bash
   ./monitor.sh
   ```