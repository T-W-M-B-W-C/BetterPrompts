# TorchServe Model Serving Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying and managing the TorchServe-based model serving infrastructure for BetterPrompts.

## Architecture Components

- **TorchServe**: Core model serving engine with GPU support
- **Kubernetes**: Container orchestration with auto-scaling
- **API Gateway**: Nginx/Kong/Traefik for load balancing and routing
- **Monitoring**: Prometheus + Grafana for metrics and alerting
- **CI/CD**: GitHub Actions for automated deployment

## Prerequisites

- Kubernetes cluster (1.25+) with GPU nodes
- AWS account with ECR access
- kubectl, kustomize, and helm installed
- Docker for local development

## Quick Start

### 1. Local Development

```bash
# Start local TorchServe with Docker Compose
cd infrastructure/model-serving
docker-compose -f docker/docker-compose.yml up -d

# Check health
curl http://localhost:8080/ping

# Test inference
curl -X POST http://localhost:8080/predictions/intent_classifier \
  -H "Content-Type: application/json" \
  -d '{"text": "How do I create a React component?"}'
```

### 2. Model Preparation

```bash
# Package trained model for TorchServe
python infrastructure/model-serving/scripts/package_models.py \
  --model-path ml-pipeline/models/production/intent_classifier_v1.0 \
  --version 1.0.0 \
  --handler infrastructure/model-serving/torchserve/handlers/intent_classifier_handler.py

# Validate model archive
ls -la infrastructure/model-serving/torchserve/models/
```

### 3. Deploy to Kubernetes

```bash
# Deploy to staging
./infrastructure/model-serving/scripts/deploy.sh staging 1.0.0 rolling

# Deploy to production
./infrastructure/model-serving/scripts/deploy.sh production 1.0.0 canary
```

## Model Management

### Registering a New Model

```bash
# Register model in the registry
python infrastructure/model-serving/scripts/model_versioning.py register \
  --name intent_classifier \
  --version 1.0.0 \
  --path infrastructure/model-serving/torchserve/models/intent_classifier_v1.0.0.mar
```

### Promoting Model Versions

```bash
# Promote to staging
python infrastructure/model-serving/scripts/model_versioning.py promote \
  --name intent_classifier \
  --version 1.0.0 \
  --to staging \
  --reason "Passed validation tests"

# Promote to production
python infrastructure/model-serving/scripts/model_versioning.py promote \
  --name intent_classifier \
  --version 1.0.0 \
  --to production \
  --reason "Approved for production release"
```

## Deployment Strategies

### Rolling Deployment
- Default strategy with zero downtime
- Gradually replaces old pods with new ones
- Suitable for most updates

### Canary Deployment
- Routes 10% of traffic to new version initially
- Monitors metrics before full rollout
- Best for risky changes

### Blue-Green Deployment
- Maintains two complete environments
- Instant switch between versions
- Quick rollback capability

## Monitoring and Observability

### Accessing Metrics

```bash
# Port-forward Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Access dashboards at http://localhost:3000
# Default credentials: admin/admin
```

### Key Metrics to Monitor

- **Inference Latency**: p50, p95, p99 percentiles
- **Request Rate**: Requests per second by model
- **Error Rate**: Failed inference percentage
- **GPU Utilization**: Memory and compute usage
- **Queue Size**: Pending request backlog

### Alerts

Critical alerts are configured for:
- High latency (>500ms p95)
- High error rate (>5%)
- GPU memory pressure (>90%)
- Pod restarts
- Model loading failures

## Scaling

### Horizontal Pod Autoscaling

```yaml
# HPA automatically scales based on:
- CPU utilization (target: 60%)
- Memory utilization (target: 70%)
- Custom metrics (inference latency)
```

### Manual Scaling

```bash
# Scale deployment
kubectl scale deployment torchserve -n model-serving --replicas=5

# Check scaling status
kubectl get hpa torchserve -n model-serving
```

## Troubleshooting

### Common Issues

1. **Model Loading Failures**
   ```bash
   # Check TorchServe logs
   kubectl logs -n model-serving -l app=torchserve --tail=100
   
   # Verify model archive
   kubectl exec -n model-serving torchserve-0 -- ls -la /models/
   ```

2. **High Latency**
   ```bash
   # Check resource usage
   kubectl top pods -n model-serving
   
   # Review batch configuration
   kubectl get cm torchserve-config -n model-serving -o yaml
   ```

3. **GPU Issues**
   ```bash
   # Check GPU availability
   kubectl describe nodes | grep -A5 "nvidia.com/gpu"
   
   # Verify GPU allocation
   kubectl describe pod -n model-serving -l app=torchserve
   ```

### Debug Commands

```bash
# Access TorchServe management API
kubectl port-forward -n model-serving svc/torchserve 8081:8081
curl http://localhost:8081/models

# Check model status
curl http://localhost:8081/models/intent_classifier

# View real-time logs
kubectl logs -n model-serving -l app=torchserve -f

# Execute commands in pod
kubectl exec -it -n model-serving torchserve-0 -- bash
```

## Security

### API Authentication
- JWT tokens for production API access
- IP whitelisting for management endpoints
- TLS encryption for all traffic

### Network Policies
```bash
# Apply network policies
kubectl apply -f infrastructure/model-serving/kubernetes/security/network-policies.yaml
```

## Backup and Recovery

### Model Backup
```bash
# Backup models to S3
aws s3 sync infrastructure/model-serving/torchserve/models/ \
  s3://betterprompts-model-backups/$(date +%Y%m%d)/
```

### Disaster Recovery
1. Restore model archives from S3
2. Redeploy infrastructure using Terraform
3. Apply Kubernetes manifests
4. Validate service health

## Performance Optimization

### TorchServe Tuning
- Batch size: 8 (configurable)
- Workers per model: 4
- Response timeout: 60s
- GPU memory fraction: 0.8

### Caching Strategy
- Nginx caches GET requests for 5 minutes
- Redis for frequently accessed predictions
- Model weights preloaded in memory

## Cost Optimization

- Use spot instances for non-production
- Scale down during off-peak hours
- Monitor and right-size GPU instances
- Implement request batching

## CI/CD Pipeline

The GitHub Actions workflow automates:
1. Model validation and testing
2. Docker image building
3. Security scanning
4. Kubernetes deployment
5. Smoke testing
6. Model registry updates

Trigger deployment:
```bash
# Via GitHub UI or API
gh workflow run model-deployment.yml \
  -f model_version=1.0.0 \
  -f environment=production \
  -f strategy=canary
```

## Support

For issues or questions:
- Check logs and metrics first
- Review troubleshooting section
- Contact ML Platform team
- Create GitHub issue with details