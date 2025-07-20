# PyTorch CPU/GPU Configuration

This service supports both CPU-only and GPU-enabled PyTorch installations to optimize for different environments.

## Configuration

### Local Development (CPU-only)
By default, `docker compose up` will use CPU-only PyTorch, which:
- Downloads ~140MB instead of >1GB
- Builds much faster (2-3 minutes vs 12+ minutes)
- Works perfectly for development and testing

The `docker-compose.override.yml` file automatically sets:
```yaml
PYTORCH_VARIANT: cpu
```

### Production (GPU-enabled)
For production deployment on AWS with GPU instances:
```bash
# Use production compose file
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

This will:
- Install full PyTorch with CUDA support
- Enable GPU acceleration for ML models
- Configure proper GPU resource allocation

### Building Manually

```bash
# Build CPU version (fast, for local dev)
docker build --build-arg PYTORCH_VARIANT=cpu -t prompt-generator:cpu .

# Build GPU version (slow, for production)
docker build --build-arg PYTORCH_VARIANT=gpu -t prompt-generator:gpu .
```

## Requirements Files

- `requirements-base.txt` - All dependencies except PyTorch
- `requirements-cpu.txt` - Includes CPU-only PyTorch
- `requirements-gpu.txt` - Includes GPU-enabled PyTorch
- `requirements.txt` - Original file (kept for compatibility)

## Environment Variables

- `PYTORCH_VARIANT` - Build arg: "cpu" or "gpu"
- `PYTORCH_DEVICE` - Runtime: "cpu" or "cuda"
- `CUDA_VISIBLE_DEVICES` - GPU device ID (production only)

## Performance Impact

CPU-only PyTorch is sufficient for:
- Prompt generation and manipulation
- Text processing with transformers
- Development and testing

GPU acceleration benefits:
- Large-scale inference
- Batch processing
- Model fine-tuning (if implemented)