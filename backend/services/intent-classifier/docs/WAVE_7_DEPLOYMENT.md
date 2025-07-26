# Wave 7: Production Deployment Guide

## Overview

Wave 7 implements production-ready deployment for the intent classifier with comprehensive health checks, graceful degradation, feature flags, and monitoring.

## Key Components Implemented

### 1. Enhanced Health Checks

#### Endpoints
- `/health` - Basic liveness check
- `/health/ready` - Comprehensive readiness check including all models
- `/health/live` - Kubernetes liveness probe
- `/health/models` - Detailed model status with performance metrics
- `/health/dependencies` - External dependency health (Postgres, Redis, TorchServe)

#### Model Health Monitoring
```bash
# Check all models health
curl http://localhost:8001/health/models

# Response includes:
# - Individual model status (rules, zero-shot, DistilBERT)
# - Latency measurements for each model
# - Adaptive routing statistics
```

### 2. Graceful Degradation

The system now includes multiple fallback mechanisms:

1. **Adaptive Router Fallback**: If routing fails, falls back to standard classification
2. **Model Chain Fallback**: DistilBERT → Zero-Shot → Rules
3. **Cache Graceful Handling**: Continues operation if Redis unavailable
4. **Database Degradation**: Read-only mode if database writes fail

### 3. Feature Flag System

#### Available Feature Flags

```python
{
    "adaptive_routing": true,      # Enable Wave 6 routing
    "ab_testing": true,           # A/B testing for routing strategies  
    "distilbert_model": false,    # Enable TorchServe DistilBERT
    "zero_shot_fallback": true,   # Zero-shot as fallback
    "caching": true,              # Redis caching
    "feedback_learning": true,    # User feedback collection
    "performance_mode": false,    # Rules-first for speed
    "quality_mode": false,        # DistilBERT-first for accuracy
    "enhanced_logging": false     # Detailed debug logging
}
```

#### API Endpoints

```bash
# Get all feature flags
GET /api/v1/feature-flags

# Check specific flag for user
GET /api/v1/feature-flags/check/adaptive_routing?user_id=user123

# Update feature flag
PUT /api/v1/feature-flags/adaptive_routing
{
    "enabled": true,
    "rollout_percentage": 50
}

# Get user's flags
GET /api/v1/feature-flags/user/user123
```

#### Environment Variables

```bash
# Enable/disable flags
FEATURE_FLAG_ADAPTIVE_ROUTING_ENABLED=true
FEATURE_FLAG_ADAPTIVE_ROUTING_ROLLOUT=50

# Pattern: FEATURE_FLAG_<FLAG_NAME>_ENABLED=true/false
# Pattern: FEATURE_FLAG_<FLAG_NAME>_ROLLOUT=0-100
```

### 4. Monitoring Setup

#### Prometheus Metrics

New metrics added:
- `http_requests_total` - HTTP request counts
- `http_request_duration_seconds` - Request latency
- `model_selection_total` - Model routing decisions
- `feature_flag_usage_total` - Feature flag usage tracking
- `intent_classifier_model_health` - Model health status

#### Grafana Dashboards

Pre-configured dashboards for:
- Service overview (requests, errors, latency)
- Model performance (selection distribution, latencies)
- Feature flag usage and rollout status
- System resources (CPU, memory, connections)

#### Alerts

Configured alerts for:
- Service down (2 minutes)
- High error rate (>5%)
- High latency (p95 >500ms)
- Model unhealthy status
- Low cache hit rate (<30%)
- High memory usage (>80%)

## Deployment Instructions

### 1. Local Development

```bash
# Build and run with docker-compose
docker compose build intent-classifier
docker compose up -d

# Check health
curl http://localhost:8001/health/ready
```

### 2. Production Deployment

```bash
# Use production compose file
docker compose -f docker-compose.prod.yml up -d

# With TorchServe enabled
docker compose -f docker-compose.prod.yml --profile torchserve up -d

# With full monitoring stack
docker compose -f docker-compose.prod.yml --profile monitoring up -d
```

### 3. Environment Configuration

Create `.env` file:
```env
# Database
POSTGRES_PASSWORD=secure-password

# Feature Flags
ENABLE_ADAPTIVE_ROUTING=true
AB_TEST_PERCENTAGE=0.1

# TorchServe (if using)
USE_TORCHSERVE=true
TORCHSERVE_HOST=torchserve
TORCHSERVE_PORT=8080

# Monitoring
GRAFANA_PASSWORD=admin-password
```

### 4. Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: intent-classifier
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: intent-classifier
        image: intent-classifier:latest
        ports:
        - containerPort: 8001
        env:
        - name: ENABLE_ADAPTIVE_ROUTING
          value: "true"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8001
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8001
          periodSeconds: 10
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

## Gradual Rollout Strategy

### Phase 1: Canary Deployment (Week 1)
1. Deploy with adaptive routing disabled
2. Monitor baseline metrics
3. Enable for 10% of traffic

### Phase 2: Progressive Rollout (Week 2)
1. Enable adaptive routing for 25% users
2. Monitor model distribution and latencies
3. Compare error rates between control/test

### Phase 3: Full Rollout (Week 3)
1. Enable for 50% → 75% → 100%
2. Monitor for performance degradation
3. Adjust confidence thresholds based on data

### Phase 4: Optimization (Week 4)
1. Analyze A/B test results
2. Select winning routing strategy
3. Fine-tune thresholds and parameters

## Monitoring Checklist

### Pre-Deployment
- [ ] Verify all health endpoints return 200
- [ ] Check Prometheus scraping metrics
- [ ] Confirm Grafana dashboards load
- [ ] Test alert routing to Slack/PagerDuty

### Post-Deployment
- [ ] Monitor error rates (<1%)
- [ ] Check p95 latency (<200ms)
- [ ] Verify cache hit rate (>60%)
- [ ] Monitor model distribution

### Daily Checks
- [ ] Review Grafana dashboards
- [ ] Check alert history
- [ ] Monitor feature flag rollout
- [ ] Review user feedback

## Troubleshooting

### Common Issues

1. **Models not initializing**
   ```bash
   # Check logs
   docker logs intent-classifier-prod
   
   # Verify model files
   docker exec intent-classifier-prod ls -la /app/models
   ```

2. **TorchServe connection failures**
   ```bash
   # Check TorchServe health
   curl http://localhost:8080/ping
   
   # View TorchServe logs
   docker logs torchserve-prod
   ```

3. **Feature flags not updating**
   ```bash
   # Refresh flags from config
   curl -X POST http://localhost:8001/api/v1/feature-flags/refresh
   
   # Check environment variables
   docker exec intent-classifier-prod env | grep FEATURE_FLAG
   ```

## Performance Tuning

### Model Loading
- Use model caching volume
- Implement lazy loading for zero-shot
- Pre-warm models on startup

### Request Handling
- Adjust `MAX_WORKERS` based on CPU cores
- Tune `MODEL_BATCH_SIZE` for throughput
- Configure connection pooling for database

### Caching Strategy
- Increase `CACHE_TTL` for stable patterns
- Use cache warming for common queries
- Monitor cache memory usage

## Security Considerations

### API Security
- Enable rate limiting per user/IP
- Implement JWT authentication
- Use HTTPS in production
- Sanitize user inputs

### Model Security
- Validate model files on load
- Restrict model file access
- Monitor for adversarial inputs
- Implement input size limits

## Next Steps

1. **Wave 8**: Comprehensive testing and validation
2. **Performance benchmarking**: Load testing at scale
3. **Model improvements**: Continuous learning from feedback
4. **Feature expansion**: Additional routing strategies