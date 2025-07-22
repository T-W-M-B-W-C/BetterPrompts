# ML Integration Setup - TorchServe with Intent Classifier

## Overview

This document describes the ML integration between the Intent Classifier service and TorchServe. The configuration is already set up correctly in `docker-compose.yml` with `USE_TORCHSERVE=true`.

## Current Configuration Status ✅

### docker-compose.yml Configuration
- ✅ `USE_TORCHSERVE=true` - Already enabled (line 40)
- ✅ `TORCHSERVE_HOST=torchserve` - Correctly configured (line 41)
- ✅ `TORCHSERVE_PORT=8080` - Correct port (line 42)
- ✅ Service dependency on `torchserve` - Properly configured (line 52)

### TorchServe Configuration
- ✅ Inference API on port 8080
- ✅ Management API on port 8081
- ✅ Metrics API on port 8082
- ✅ Model store mounted as volume
- ✅ Custom handler implemented

## Setup Instructions

### Step 1: Start the Services

```bash
# From project root directory
docker compose down
docker compose build torchserve
docker compose up -d postgres redis torchserve
```

### Step 2: Initialize the Mock Model

```bash
# Run the initialization script
./infrastructure/model-serving/scripts/init_local_model.sh
```

This script will:
1. Create the model store directory
2. Start TorchServe if not running
3. Create a mock model using the Python script
4. Package the model as a MAR file
5. Register the model with TorchServe
6. Test the model inference

### Step 3: Start All Services

```bash
# Start remaining services
docker compose up -d
```

### Step 4: Verify Integration

```bash
# Run the integration test
./scripts/test-ml-integration.sh
```

## Testing the Integration

### Direct TorchServe Test
```bash
curl -X POST http://localhost:8080/predictions/intent_classifier \
  -H "Content-Type: application/json" \
  -d '{"text": "How do I create a React component?"}'
```

### Through API Gateway
```bash
curl -X POST http://localhost/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "How do I implement authentication in Node.js?"}'
```

Expected response:
```json
{
  "intent": {
    "primaryIntent": "code_generation",
    "confidence": 0.85,
    "complexity": "moderate",
    "domain": "backend",
    "taskType": "implementation"
  },
  "suggestedTechniques": [
    {
      "id": "chain_of_thought",
      "name": "Chain of Thought",
      "description": "Guide reasoning through step-by-step thinking",
      "confidence": 0.85
    }
  ]
}
```

## Troubleshooting

### Issue: Model not found
```bash
# Check model status
curl http://localhost:8081/models

# Re-run initialization
./infrastructure/model-serving/scripts/init_local_model.sh
```

### Issue: TorchServe not responding
```bash
# Check container status
docker compose ps torchserve

# View logs
docker compose logs torchserve

# Restart service
docker compose restart torchserve
```

### Issue: Intent classifier not connecting
```bash
# Check environment variables
docker compose exec intent-classifier env | grep TORCH

# Check logs for connection errors
docker compose logs intent-classifier | grep -i torchserve

# Restart intent-classifier
docker compose restart intent-classifier
```

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│   API Gateway   │────▶│ Intent Classifier│────▶│  TorchServe  │
│   (port 8090)   │     │   (port 8001)    │     │ (port 8080)  │
└─────────────────┘     └──────────────────┘     └──────────────┘
                                │                         │
                                ▼                         ▼
                        ┌──────────────┐         ┌──────────────┐
                        │   Database   │         │ Model Store  │
                        │  PostgreSQL  │         │   (volume)   │
                        └──────────────┘         └──────────────┘
```

## Model Details

### Mock Model Configuration
- **Model Type**: Intent Classifier
- **Input**: Text (up to 512 tokens)
- **Output**: Intent classification with confidence scores
- **Classes**: 10 intent types (question_answering, creative_writing, etc.)

### Handler Implementation
- Located at: `/infrastructure/model-serving/torchserve/handlers/intent_classifier_handler.py`
- Features:
  - Batch processing support
  - Complexity assessment
  - Technique recommendations
  - Comprehensive error handling

## Performance Considerations

- **Initial Load Time**: ~10-15 seconds for model initialization
- **Inference Time**: <500ms per request
- **Batch Size**: 8 (configurable)
- **Workers**: 2-4 (auto-scaling)

## Next Steps

1. ✅ ML Integration is configured and ready
2. 🔄 Implement prompt generation techniques
3. 🔄 Complete frontend-backend integration
4. 🔄 Add authentication UI

## Monitoring

View real-time logs:
```bash
# All ML-related services
docker compose logs -f intent-classifier torchserve

# TorchServe metrics
curl http://localhost:8082/metrics
```

## Production Considerations

For production deployment:
1. Replace mock model with trained DeBERTa model
2. Enable GPU support in TorchServe
3. Configure model versioning
4. Set up proper monitoring and alerting
5. Implement model A/B testing