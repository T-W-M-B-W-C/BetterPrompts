# Intent Classifier Docker Deployment Guide

## Overview
This guide explains how to deploy and test the intent-classifier service using Docker.

## Changes Made

### 1. Optimized Dockerfile
- **Multi-stage build**: Reduces final image size by separating build and runtime stages
- **CPU-only PyTorch**: Uses CPU-optimized torch to reduce image size (GPU version can be enabled if needed)
- **Virtual environment**: Isolates Python dependencies for better reproducibility
- **Proper PYTHONPATH**: Ensures all modules are discoverable
- **Caching optimizations**: Better layer caching for faster rebuilds

### 2. Docker Compose Configuration
- **Build context**: Updated to use the service directory directly
- **Environment variables**: Added PYTHONPATH and disabled TorchServe for local development
- **Volume mounts**: Proper mounting for development with hot-reload capability

### 3. Module Import Fixes
- All imports use relative paths from the app directory
- PYTHONPATH is set to /app in the container
- Module structure validated with proper __init__.py files

## Deployment Instructions

### 1. Build the Container
```bash
# From the project root directory
docker compose build intent-classifier

# Or rebuild without cache if needed
docker compose build --no-cache intent-classifier
```

### 2. Start the Service
```bash
# Start just the intent-classifier and its dependencies
docker compose up -d postgres redis intent-classifier

# Or start all services
docker compose up -d

# Check logs
docker compose logs -f intent-classifier
```

### 3. Verify Deployment
```bash
# Run the automated test script
cd backend/services/intent-classifier
python test_docker_deployment.py

# Or test manually with curl
# Health check
curl http://localhost:8001/health

# Readiness check
curl http://localhost:8001/api/v1/health/ready

# Test classification
curl -X POST http://localhost:8001/api/v1/intents/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "How do I create a REST API in Python?"}'
```

## Container Details

### Image Size Optimization
- Base image: python:3.11-slim (~150MB)
- With ML dependencies: ~2.5GB (CPU-only torch)
- With GPU support: ~4GB (if enabled)

### Resource Requirements
- Memory: 2GB minimum, 4GB recommended
- CPU: 2 cores minimum for good performance
- Disk: 3GB for image + cache

### Environment Variables
- `PYTHONPATH=/app`: Ensures module discovery
- `USE_TORCHSERVE=false`: Uses local hybrid classifier
- `TRANSFORMERS_CACHE=/app/.cache/huggingface`: Model cache location
- `LOG_LEVEL=DEBUG`: Detailed logging for development

## Troubleshooting

### Module Import Errors
If you see import errors:
1. Ensure PYTHONPATH is set in docker-compose.yml
2. Check that all __init__.py files exist
3. Verify the build context is correct

### Memory Issues
If the container crashes with memory errors:
1. Increase Docker memory allocation (Docker Desktop > Settings > Resources)
2. Reduce worker count in uvicorn command
3. Use smaller models in zero-shot classifier

### Slow Startup
First startup may be slow due to:
1. Model downloading (if using transformers)
2. Dependency compilation
3. Database migrations

## Testing the Deployment

### Unit Tests
```bash
# Run inside container
docker compose exec intent-classifier python -m pytest tests/

# Or from outside
docker compose run --rm intent-classifier python -m pytest tests/
```

### Integration Tests
```bash
# Test with other services
docker compose up -d
python test_docker_deployment.py
```

### Performance Testing
```bash
# Simple load test
ab -n 100 -c 10 -p test_data.json -T application/json \
  http://localhost:8001/api/v1/intents/classify
```

## Production Considerations

### For GPU Support
1. Change Dockerfile to use GPU-enabled torch:
   ```dockerfile
   RUN pip install torch==2.1.1+cu118 --index-url https://download.pytorch.org/whl/cu118
   ```
2. Use nvidia-docker runtime
3. Set appropriate CUDA environment variables

### For TorchServe Integration
1. Set `USE_TORCHSERVE=true` in environment
2. Ensure TorchServe service is running
3. Configure TORCHSERVE_HOST and TORCHSERVE_PORT

### Security
1. Run as non-root user (already configured)
2. Use secrets management for API keys
3. Enable TLS for production endpoints
4. Implement rate limiting

## Monitoring

### Health Endpoints
- `/health` - Basic health check
- `/api/v1/health/ready` - Readiness with dependency checks
- `/api/v1/health/live` - Kubernetes liveness probe

### Metrics
- Prometheus metrics at `/metrics`
- Classification latency histograms
- Request counters by status

### Logs
- Structured JSON logging
- Log aggregation with ELK stack recommended
- Debug level for development, INFO for production