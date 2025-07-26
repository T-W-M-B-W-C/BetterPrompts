# Wave 6 Integration Guide

## Quick Start

### 1. Enable Adaptive Routing

Add to your `.env` file:
```env
ENABLE_ADAPTIVE_ROUTING=true
AB_TEST_PERCENTAGE=0.1
```

### 2. Run the Demo

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Wave 6 demo
python demo_wave6_routing.py

# Test with trained model
python integrate_wave6_distilbert.py
```

### 3. Start the Service

```bash
# With Docker
docker compose up intent-classifier

# Or locally
uvicorn app.main:app --port 8001 --reload
```

### 4. Test the API

```bash
# Standard classification (will use adaptive routing)
curl -X POST http://localhost:8001/api/v1/intents/classify \
  -H "Content-Type: application/json" \
  -d '{
    "text": "How do I implement a binary search tree?",
    "latency_requirement": "standard"
  }'

# Get routing statistics
curl http://localhost:8001/api/v1/intents/routing/stats

# Update routing configuration
curl -X POST http://localhost:8001/api/v1/intents/routing/config \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "rules",
    "confidence_threshold": 0.8
  }'
```

## Model Hierarchy

1. **Rules** → Fast (10-30ms), 75% accuracy
2. **Zero-Shot** → Balanced (100-200ms), 85% accuracy  
3. **DistilBERT** → Accurate (300-500ms), 92% accuracy

## Routing Logic

- **Critical latency (<50ms)**: Rules only
- **Standard latency (<200ms)**: Rules → Zero-shot fallback
- **Relaxed latency (<500ms)**: All models available

## A/B Testing

10% of traffic is randomly assigned to test groups:
- **control**: Default progressive routing
- **aggressive_rules**: Lower confidence threshold
- **balanced**: Prefer zero-shot
- **quality_first**: Always use best model

## Monitoring

Track performance via:
- `/api/v1/intents/routing/stats` - Real-time statistics
- Prometheus metrics - `intent_routing_*`
- Application logs - Routing decisions

## TorchServe Integration

To use the trained DistilBERT model:

1. Deploy model to TorchServe
2. Update `.env`:
   ```env
   USE_TORCHSERVE=true
   TORCHSERVE_HOST=localhost
   TORCHSERVE_PORT=8080
   ```
3. The router will automatically use it when available

## Customization

Adjust thresholds in `.env`:
```env
RULES_CONFIDENCE_THRESHOLD=0.85
ZERO_SHOT_CONFIDENCE_THRESHOLD=0.70
DISTILBERT_CONFIDENCE_THRESHOLD=0.0
```

Or dynamically via API:
```bash
POST /api/v1/intents/routing/config
{
  "model_type": "zero_shot",
  "confidence_threshold": 0.75
}
```