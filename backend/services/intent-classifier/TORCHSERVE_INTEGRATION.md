# TorchServe Integration Guide

This document explains how the Intent Classifier service integrates with TorchServe for model inference.

## Overview

The Intent Classifier service can operate in two modes:
1. **TorchServe Mode** (recommended for production): Uses TorchServe for scalable model serving
2. **Local Mode**: Loads the model directly in the service (for development/testing)

## Configuration

### Environment Variables

Configure the following in your `.env` file:

```env
# Enable/Disable TorchServe integration
USE_TORCHSERVE=true

# TorchServe connection settings
TORCHSERVE_HOST=localhost      # Use "torchserve" for Docker/K8s
TORCHSERVE_PORT=8080
TORCHSERVE_MODEL_NAME=intent_classifier
TORCHSERVE_TIMEOUT=30          # Request timeout in seconds
TORCHSERVE_MAX_RETRIES=3       # Number of retry attempts
```

### Docker Compose Configuration

For local development with Docker Compose:

```yaml
services:
  intent-classifier:
    environment:
      - USE_TORCHSERVE=true
      - TORCHSERVE_HOST=torchserve  # Service name in Docker network
      - TORCHSERVE_PORT=8080
    depends_on:
      - torchserve
```

### Kubernetes Configuration

For Kubernetes deployments:

```yaml
env:
  - name: USE_TORCHSERVE
    value: "true"
  - name: TORCHSERVE_HOST
    value: "torchserve.model-serving"  # K8s service DNS
  - name: TORCHSERVE_PORT
    value: "8080"
```

## Architecture

### Component Flow

```
User Request
    ↓
Intent Classifier API
    ↓
IntentClassifier.classify()
    ↓
[USE_TORCHSERVE?]
    ├─ Yes → TorchServeClient → TorchServe Server → Model
    └─ No  → Local Model (DeBERTa)
    ↓
Response
```

### TorchServe Client Features

1. **Connection Management**
   - Async HTTP client with connection pooling
   - Automatic health checks on startup
   - Configurable timeouts

2. **Error Handling**
   - Specific exception types for different failures
   - Automatic retry with exponential backoff
   - Graceful fallback options

3. **Performance Optimization**
   - Connection pooling for efficiency
   - Batch inference support
   - Response caching integration

## Testing

### 1. Start TorchServe

```bash
# Using Docker
docker run -p 8080:8080 -p 8081:8081 \
  -v $(pwd)/model-store:/models \
  betterprompts/torchserve:latest

# Or using the full stack
docker compose up torchserve
```

### 2. Verify TorchServe Health

```bash
# Health check
curl http://localhost:8080/ping

# Model status
curl http://localhost:8081/models/intent_classifier
```

### 3. Run Integration Tests

```bash
cd backend/services/intent-classifier

# Install dependencies
pip install -r requirements.txt

# Run test script
python test_torchserve_integration.py
```

### 4. Test API Endpoints

```bash
# Single classification
curl -X POST http://localhost:8001/api/v1/intents/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "How do I create a REST API in Python?"}'

# Batch classification
curl -X POST http://localhost:8001/api/v1/intents/classify/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["What is machine learning?", "Write a poem about spring"]}'

# Check service health
curl http://localhost:8001/health/ready
```

## Monitoring

### Health Checks

The service provides detailed health status:

```json
GET /health/ready

{
  "status": "ready",
  "service": "intent-classifier",
  "details": {
    "database": "healthy",
    "model": "initialized",
    "torchserve": "healthy"
  },
  "mode": "torchserve"
}
```

### Metrics

Prometheus metrics track TorchServe-specific events:

- `intent_classification_requests_total{status="torchserve_connection_error"}`
- `intent_classification_requests_total{status="torchserve_inference_error"}`
- `intent_classification_duration_seconds`

### Logging

Structured logs provide visibility:

```
INFO: Initializing TorchServe client
INFO: TorchServe health check passed
INFO: TorchServe inference successful in 0.123s
ERROR: TorchServe connection attempt 1 failed: Connection refused
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```
   TorchServeConnectionError: Failed to connect to TorchServe
   ```
   - Verify TorchServe is running: `docker ps | grep torchserve`
   - Check network connectivity: `nc -zv localhost 8080`
   - Verify TORCHSERVE_HOST setting

2. **Model Not Found**
   ```
   TorchServeInferenceError: Model 'intent_classifier' not found
   ```
   - Check model registration: `curl http://localhost:8081/models`
   - Deploy model: `./scripts/deploy.sh`

3. **Timeout Errors**
   ```
   TorchServeInferenceError: Request timeout after 30s
   ```
   - Increase TORCHSERVE_TIMEOUT
   - Check TorchServe resource allocation
   - Monitor GPU/CPU usage

### Fallback to Local Mode

To disable TorchServe and use local model:

```bash
export USE_TORCHSERVE=false
# Restart the service
```

## Performance Considerations

### TorchServe Benefits

- **Scalability**: Auto-scaling based on load
- **GPU Optimization**: Efficient GPU utilization
- **Model Versioning**: A/B testing and gradual rollouts
- **Monitoring**: Built-in metrics and logging

### When to Use Local Mode

- Development and debugging
- Small-scale deployments
- When TorchServe overhead isn't justified
- Offline/edge deployments

## Security

### Best Practices

1. **Network Security**
   - Use internal networks for TorchServe communication
   - Enable TLS for production deployments
   - Implement API authentication

2. **Input Validation**
   - Text length limits enforced
   - Input sanitization implemented
   - Rate limiting on API endpoints

3. **Error Messages**
   - User-friendly errors that don't expose internals
   - Detailed logging for debugging
   - Separate error codes for different failures