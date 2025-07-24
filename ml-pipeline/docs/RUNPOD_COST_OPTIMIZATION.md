# RunPod Cost Optimization Guide

## Overview

This guide provides strategies to minimize costs while training on RunPod, potentially reducing expenses by 50-80% through smart optimization.

## 1. GPU Selection Strategy

### Cost-Performance Analysis

| GPU | $/Hour | VRAM | Training Time | Total Cost | Best For |
|-----|--------|------|---------------|------------|----------|
| RTX 3090 | $0.34 | 24GB | 25 min | $0.14 | **Best Value** ✅ |
| RTX 4090 | $0.44 | 24GB | 20 min | $0.15 | Fastest |
| A40 | $0.79 | 48GB | 20 min | $0.26 | Large batches |
| A100 40GB | $1.89 | 40GB | 15 min | $0.47 | Production |

**Recommendation**: RTX 3090 offers the best cost/performance ratio for DistilBERT training.

## 2. Spot Instance Strategy

### Using Spot/Preemptible Instances
```bash
# Spot instances are 50-70% cheaper
# RTX 3090 Spot: ~$0.10-0.17/hour vs $0.34/hour
```

### Implementing Checkpointing
```python
# In training script, save frequently
training_args = TrainingArguments(
    save_steps=100,  # Save every 100 steps
    save_total_limit=3,  # Keep only 3 checkpoints
    load_best_model_at_end=True,
    save_strategy="steps"
)
```

### Resume from Interruption
```bash
# If spot instance is interrupted
python train_distilbert.py \
    --resume_from_checkpoint models/distilbert_intent_classifier/checkpoint-latest
```

## 3. Batch Size Optimization

### Memory-Efficient Settings
```python
# Maximize GPU utilization without OOM
def get_optimal_batch_size(gpu_memory_gb):
    if gpu_memory_gb >= 40:
        return 128  # A100, A40
    elif gpu_memory_gb >= 24:
        return 64   # RTX 3090/4090
    elif gpu_memory_gb >= 16:
        return 32   # V100, RTX 3080
    else:
        return 16   # Smaller GPUs
```

### Gradient Accumulation
```python
# Simulate larger batch sizes on smaller GPUs
training_args = TrainingArguments(
    per_device_train_batch_size=32,
    gradient_accumulation_steps=2,  # Effective batch size = 64
    fp16=True  # Mixed precision saves memory
)
```

## 4. Training Time Reduction

### Early Stopping
```python
# Stop training when model stops improving
from transformers import EarlyStoppingCallback

trainer = Trainer(
    callbacks=[
        EarlyStoppingCallback(
            early_stopping_patience=2,  # Stop after 2 epochs without improvement
            early_stopping_threshold=0.001
        )
    ]
)
```

### Learning Rate Optimization
```python
# Use learning rate finder
def find_optimal_lr(model, train_dataloader):
    # Start with very low LR
    lrs = np.logspace(-7, -2, 100)
    losses = []
    
    for lr in lrs:
        # Train for a few steps
        loss = train_step(model, train_dataloader, lr)
        losses.append(loss)
        
        # Stop if loss explodes
        if loss > min(losses) * 4:
            break
    
    # Optimal LR is where loss decreases fastest
    optimal_lr = lrs[np.argmin(np.gradient(losses))]
    return optimal_lr
```

## 5. Data Loading Optimization

### Efficient Data Pipeline
```python
# Use multiple workers and pin memory
train_dataloader = DataLoader(
    train_dataset,
    batch_size=batch_size,
    num_workers=8,  # Parallel data loading
    pin_memory=True,  # Faster GPU transfer
    prefetch_factor=2  # Prefetch next batches
)
```

### Data Caching
```python
# Cache tokenized data
from datasets import load_from_disk

# First run: tokenize and save
tokenized_dataset = dataset.map(tokenize_function, batched=True)
tokenized_dataset.save_to_disk("./tokenized_data")

# Subsequent runs: load from cache
tokenized_dataset = load_from_disk("./tokenized_data")
```

## 6. Mixed Precision Training

### Automatic Mixed Precision
```python
# Reduces memory usage and speeds up training
training_args = TrainingArguments(
    fp16=True,  # Enable mixed precision
    fp16_opt_level="O2",  # Optimization level
    fp16_backend="cuda_amp"  # Use CUDA AMP
)

# Or with Accelerate
from accelerate import Accelerator
accelerator = Accelerator(mixed_precision="fp16")
```

## 7. Model Optimization

### Layer Freezing
```python
# Freeze base layers, only train classifier
def freeze_base_layers(model, freeze_layers=10):
    for i, (name, param) in enumerate(model.named_parameters()):
        if i < freeze_layers:
            param.requires_grad = False
    return model
```

### Pruning (Post-Training)
```python
# Remove less important weights
import torch.nn.utils.prune as prune

def prune_model(model, amount=0.3):
    for module in model.modules():
        if isinstance(module, torch.nn.Linear):
            prune.l1_unstructured(module, name='weight', amount=amount)
    return model
```

## 8. Auto-Shutdown Configuration

### Immediate Shutdown After Training
```python
# In runpod_train.py
def auto_shutdown(delay_seconds=300):
    """Shutdown pod after delay to allow result download."""
    print(f"Shutting down in {delay_seconds} seconds...")
    time.sleep(delay_seconds)
    subprocess.run(["shutdown", "-h", "now"])

# Run after training completes
if training_successful:
    package_results()
    auto_shutdown(300)  # 5 minutes to download
```

### Cost Monitoring Script
```python
def calculate_cost(start_time, gpu_hourly_rate=0.34):
    """Calculate current training cost."""
    runtime_hours = (time.time() - start_time) / 3600
    cost = runtime_hours * gpu_hourly_rate
    
    print(f"Runtime: {runtime_hours:.2f} hours")
    print(f"Current cost: ${cost:.3f}")
    
    # Estimate total cost based on progress
    if current_step > 0:
        progress = current_step / total_steps
        estimated_total = cost / progress
        print(f"Estimated total: ${estimated_total:.3f}")
    
    return cost
```

## 9. Batch Job Optimization

### Queue Multiple Experiments
```bash
#!/bin/bash
# Run multiple experiments on same pod

experiments=(
    "--learning_rate 5e-5 --batch_size 32"
    "--learning_rate 3e-5 --batch_size 64"
    "--learning_rate 2e-5 --batch_size 32 --warmup_steps 1000"
)

for exp in "${experiments[@]}"; do
    echo "Running experiment: $exp"
    python train_distilbert.py $exp
    
    # Save results
    mkdir -p results/exp_$RANDOM
    mv models/* results/exp_$RANDOM/
done

# Shutdown after all experiments
shutdown -h now
```

## 10. Cost Tracking Dashboard

### Real-Time Cost Monitor
```python
# Add to training loop
class CostTracker:
    def __init__(self, gpu_hourly_rate):
        self.start_time = time.time()
        self.gpu_rate = gpu_hourly_rate
        
    def log_cost(self, step, total_steps):
        runtime_hours = (time.time() - self.start_time) / 3600
        current_cost = runtime_hours * self.gpu_rate
        
        if step > 0:
            progress = step / total_steps
            eta_hours = (runtime_hours / progress) - runtime_hours
            total_cost = current_cost / progress
            
            logger.info(f"💰 Cost: ${current_cost:.3f} | "
                       f"ETA: {eta_hours:.1f}h | "
                       f"Total: ${total_cost:.3f}")
```

## Summary: Maximum Savings Strategy

### Optimal Configuration for Minimum Cost:
```python
# 1. Use RTX 3090 Spot Instance (~$0.10/hour)
# 2. Optimize batch size for full GPU utilization
# 3. Enable mixed precision training
# 4. Implement early stopping
# 5. Auto-shutdown after training

# Expected cost: $0.04-0.08 per training run (75% savings)
```

### Quick Cost Comparison:
- **Without optimization**: $0.20-0.30 per run
- **With optimization**: $0.04-0.08 per run
- **Savings**: 60-75% reduction

### Emergency Cost Control:
```bash
# Set maximum runtime limit
timeout 30m python train_distilbert.py

# Or in Python
import signal
def timeout_handler(signum, frame):
    raise TimeoutError("Training time limit reached")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(1800)  # 30 minutes
```