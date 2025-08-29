# ML Integration Troubleshooting Guide

## Quick Fix

Try the v2 initialization script that creates everything inside the container:

```bash
./infrastructure/model-serving/scripts/init_local_model_v2.sh
```

## Common Issues and Solutions

### Issue: Python script not found in container

**Error**: `python: can't open file '/home/model-server/scripts/create_mock_model.py': [Errno 2] No such file or directory`

**Solution 1**: Use the v2 script that creates everything inside the container:
```bash
./infrastructure/model-serving/scripts/init_local_model_v2.sh
```

**Solution 2**: Manually create the model:
```bash
# 1. Enter the TorchServe container
docker compose exec torchserve bash

# 2. Create a simple model manually
cd /tmp
cat > create_model.py << 'EOF'
import torch
import json

# Create model files
torch.save({"fc.weight": torch.randn(10, 768), "fc.bias": torch.randn(10)}, "model.pth")
with open("config.json", "w") as f:
    json.dump({"model_type": "intent_classifier", "num_classes": 10}, f)
print("Model created")
EOF

python create_model.py

# 3. Create model archive
torch-model-archiver \
    --model-name intent_classifier \
    --version 1.0 \
    --serialized-file model.pth \
    --extra-files config.json \
    --export-path /home/model-server/model-store \
    --force

# 4. Exit container
exit

# 5. Register the model
docker compose exec torchserve curl -X POST \
    "http://localhost:8081/models?url=intent_classifier.mar&initial_workers=2"
```

### Issue: Model registration fails

**Error**: Model already exists or registration timeout

**Solution**:
```bash
# Unregister existing model
docker compose exec torchserve curl -X DELETE \
    http://localhost:8081/models/intent_classifier/1.0

# Wait a moment
sleep 5

# Re-register
docker compose exec torchserve curl -X POST \
    "http://localhost:8081/models?url=intent_classifier.mar&initial_workers=2"
```

### Issue: TorchServe container not starting

**Solution**:
```bash
# Check logs
docker compose logs torchserve

# Common fixes:
# 1. Remove old model store
rm -rf infrastructure/model-serving/torchserve/model-store/*

# 2. Rebuild container
docker compose build torchserve

# 3. Start fresh
docker compose down
docker compose up -d torchserve
```

### Issue: Intent classifier can't connect to TorchServe

**Solution**:
```bash
# 1. Verify network connectivity
docker compose exec intent-classifier ping torchserve

# 2. Check environment variables
docker compose exec intent-classifier env | grep TORCHSERVE

# 3. Test direct connection from intent-classifier
docker compose exec intent-classifier curl http://torchserve:8080/ping

# 4. Restart intent-classifier
docker compose restart intent-classifier
```

## Step-by-Step Manual Setup

If automated scripts fail, follow these manual steps:

### 1. Start TorchServe
```bash
docker compose up -d torchserve
docker compose logs -f torchserve  # Watch for "Model server started"
```

### 2. Create a minimal model archive
```bash
# Create a temporary directory
mkdir -p /tmp/torch_model
cd /tmp/torch_model

# Create minimal model files
echo '{"model_type": "mock"}' > config.json
echo 'import torch; torch.save({}, "model.pth")' | python3
echo 'def handle(data, context): return [{"intent": "test", "confidence": 0.9}]' > handler.py

# Create archive
torch-model-archiver \
    --model-name intent_classifier \
    --version 1.0 \
    --handler handler.py \
    --extra-files config.json \
    --export-path .

# Copy to container
docker cp intent_classifier.mar betterprompts-torchserve:/home/model-server/model-store/
```

### 3. Register model in TorchServe
```bash
docker compose exec torchserve curl -X POST \
    "http://localhost:8081/models?url=intent_classifier.mar"
```

### 4. Test the model
```bash
# Direct test
curl -X POST http://localhost:8080/predictions/intent_classifier \
    -H "Content-Type: application/json" \
    -d '{"text": "test"}'

# Through API Gateway
curl -X POST http://localhost/api/v1/analyze \
    -H "Content-Type: application/json" \
    -d '{"text": "test"}'
```

## Verification Commands

```bash
# Check TorchServe health
curl http://localhost:8080/ping

# List loaded models
curl http://localhost:8081/models

# Check model status
curl http://localhost:8081/models/intent_classifier

# View TorchServe logs
docker compose logs --tail=50 torchserve

# View intent-classifier logs
docker compose logs --tail=50 intent-classifier
```

## Complete Reset

If nothing works, perform a complete reset:

```bash
# 1. Stop all services
docker compose down

# 2. Clean up volumes
docker volume prune -f

# 3. Remove model store
rm -rf infrastructure/model-serving/torchserve/model-store/*

# 4. Rebuild images
docker compose build --no-cache torchserve intent-classifier

# 5. Start fresh
docker compose up -d

# 6. Run v2 initialization
./infrastructure/model-serving/scripts/init_local_model_v2.sh
```

## Next Steps After Successful Setup

1. Verify ML integration: `./scripts/test-ml-integration.sh`
2. Monitor services: `docker compose logs -f intent-classifier torchserve`
3. Test enhance endpoint: 
   ```bash
   curl -X POST http://localhost/api/v1/enhance \
     -H "Content-Type: application/json" \
     -d '{"text": "How do I learn Python?"}'
   ```