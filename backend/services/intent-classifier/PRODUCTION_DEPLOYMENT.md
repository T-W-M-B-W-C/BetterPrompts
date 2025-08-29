# Production Deployment Guide for Intent Classifier with TorchServe

This guide covers best practices and configurations for deploying the Intent Classifier service with TorchServe in production.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Infrastructure Requirements](#infrastructure-requirements)
3. [Security Configuration](#security-configuration)
4. [Performance Tuning](#performance-tuning)
5. [High Availability Setup](#high-availability-setup)
6. [Monitoring and Alerting](#monitoring-and-alerting)
7. [Deployment Checklist](#deployment-checklist)

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   API Gateway   │────▶│ Intent Classifier│────▶│   TorchServe    │
│  (Rate Limiting)│     │    Service      │     │  (GPU Enabled)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Prometheus    │     │     Redis       │     │   Model Store   │
│   + Grafana     │     │    (Cache)      │     │   (S3/GCS)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Infrastructure Requirements

### Minimum Production Requirements

#### Intent Classifier Service
- **CPU**: 4 cores
- **Memory**: 8GB RAM
- **Storage**: 20GB SSD
- **Network**: 1Gbps
- **Instances**: 3+ for HA

#### TorchServe
- **CPU**: 8 cores (or 4 cores + GPU)
- **GPU**: NVIDIA T4 or better (recommended)
- **Memory**: 16GB RAM (32GB with GPU)
- **Storage**: 50GB SSD
- **Network**: 10Gbps (for model loading)
- **Instances**: 2+ for HA

### Kubernetes Resources

```yaml
# intent-classifier-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: intent-classifier
  namespace: betterprompts
spec:
  replicas: 3
  selector:
    matchLabels:
      app: intent-classifier
  template:
    metadata:
      labels:
        app: intent-classifier
    spec:
      containers:
      - name: intent-classifier
        image: betterprompts/intent-classifier:latest
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
          limits:
            cpu: "4"
            memory: "8Gi"
        env:
        - name: USE_TORCHSERVE
          value: "true"
        - name: TORCHSERVE_HOST
          value: "torchserve.model-serving"
        - name: TORCHSERVE_PORT
          value: "8080"
        - name: CIRCUIT_BREAKER_FAILURE_THRESHOLD
          value: "5"
        - name: CIRCUIT_BREAKER_RECOVERY_TIMEOUT
          value: "60"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 5
        ports:
        - containerPort: 8001
          name: http
        - containerPort: 8000
          name: metrics
```

## Security Configuration

### 1. Network Security

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: intent-classifier-network-policy
spec:
  podSelector:
    matchLabels:
      app: intent-classifier
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8001
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: torchserve
    ports:
    - protocol: TCP
      port: 8080
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

### 2. TLS Configuration

```nginx
# nginx-ssl.conf
server {
    listen 443 ssl http2;
    server_name api.betterprompts.com;
    
    ssl_certificate /etc/ssl/certs/betterprompts.crt;
    ssl_certificate_key /etc/ssl/private/betterprompts.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location /api/v1/intents/ {
        proxy_pass http://intent-classifier:8001;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Secrets Management

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: intent-classifier-secrets
type: Opaque
stringData:
  JWT_SECRET: "your-production-jwt-secret"
  POSTGRES_PASSWORD: "your-db-password"
  REDIS_PASSWORD: "your-redis-password"
```

## Performance Tuning

### 1. TorchServe Configuration

```properties
# config.properties
inference_address=http://0.0.0.0:8080
management_address=http://0.0.0.0:8081
metrics_address=http://0.0.0.0:8082
number_of_netty_threads=32
job_queue_size=1000
model_store=/models
model_snapshot={"name":"startup.cfg","modelCount":1,"models":{"intent_classifier":{"1.0":{"defaultVersion":true,"marName":"intent_classifier.mar","minWorkers":2,"maxWorkers":8,"batchSize":32,"maxBatchDelay":50,"responseTimeout":120}}}}
```

### 2. Application Tuning

```python
# gunicorn.conf.py
bind = "0.0.0.0:8001"
workers = 4  # 2 * CPU cores + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 10000
max_requests_jitter = 1000
timeout = 30
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
```

### 3. Redis Configuration

```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save ""
appendonly no
tcp-backlog 511
tcp-keepalive 60
timeout 300
```

## High Availability Setup

### 1. Multi-Region Deployment

```yaml
# multi-region-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: intent-classifier-global
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
  selector:
    app: intent-classifier
  ports:
  - port: 80
    targetPort: 8001
```

### 2. Circuit Breaker Configuration

```python
# Production circuit breaker settings
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
CIRCUIT_BREAKER_EXPECTED_EXCEPTION_TYPES = ["ConnectError", "TimeoutException"]

# Health check settings
HEALTH_CHECK_INTERVAL = 30
HEALTH_CHECK_TIMEOUT = 5

# Retry configuration
TORCHSERVE_MAX_RETRIES = 3
TORCHSERVE_TIMEOUT = 30
```

### 3. Auto-scaling Configuration

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: intent-classifier-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: intent-classifier
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
```

## Monitoring and Alerting

### 1. Prometheus Configuration

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'intent-classifier'
    kubernetes_sd_configs:
    - role: pod
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_app]
      action: keep
      regex: intent-classifier
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
      action: replace
      target_label: __metrics_path__
      regex: (.+)
    - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
      action: replace
      regex: ([^:]+)(?::\d+)?;(\d+)
      replacement: $1:$2
      target_label: __address__
```

### 2. Grafana Dashboard

Import the dashboard from `monitoring/torchserve_dashboard.json` and configure:

- **Data Source**: Prometheus
- **Refresh Rate**: 5s
- **Time Range**: Last 1 hour
- **Variables**: 
  - `instance`: label_values(up{job="intent-classifier"}, instance)
  - `method`: label_values(torchserve_requests_total, method)

### 3. Alerting Rules

```yaml
# alerting-rules.yaml
groups:
  - name: intent_classifier_alerts
    interval: 30s
    rules:
      - alert: IntentClassifierDown
        expr: up{job="intent-classifier"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Intent Classifier instance {{ $labels.instance }} is down"
          
      - alert: TorchServeHighErrorRate
        expr: rate(torchserve_requests_total{status=~"error.*"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate for TorchServe requests"
          
      - alert: CircuitBreakerOpen
        expr: increase(torchserve_requests_total{status="circuit_breaker_open"}[5m]) > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Circuit breaker is open, TorchServe requests are being blocked"
          
      - alert: HighRequestLatency
        expr: histogram_quantile(0.95, rate(torchserve_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "95th percentile latency is above 5 seconds"
```

## Deployment Checklist

### Pre-Deployment

- [ ] **Infrastructure**
  - [ ] Kubernetes cluster with sufficient resources
  - [ ] GPU nodes for TorchServe (if using GPU)
  - [ ] Load balancer configured
  - [ ] DNS entries created

- [ ] **Security**
  - [ ] TLS certificates installed
  - [ ] Network policies applied
  - [ ] Secrets stored in secret manager
  - [ ] RBAC policies configured

- [ ] **Models**
  - [ ] Model artifacts uploaded to model store
  - [ ] Model versions tagged properly
  - [ ] Model serving configuration tested

- [ ] **Configuration**
  - [ ] Environment variables set correctly
  - [ ] Circuit breaker thresholds tuned
  - [ ] Cache TTL configured
  - [ ] Logging levels set appropriately

### Deployment Steps

1. **Deploy Infrastructure Components**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/secrets.yaml
   kubectl apply -f k8s/configmaps.yaml
   kubectl apply -f k8s/network-policies.yaml
   ```

2. **Deploy TorchServe**
   ```bash
   kubectl apply -f k8s/torchserve-deployment.yaml
   kubectl apply -f k8s/torchserve-service.yaml
   ```

3. **Deploy Intent Classifier**
   ```bash
   kubectl apply -f k8s/intent-classifier-deployment.yaml
   kubectl apply -f k8s/intent-classifier-service.yaml
   kubectl apply -f k8s/intent-classifier-hpa.yaml
   ```

4. **Setup Monitoring**
   ```bash
   kubectl apply -f k8s/prometheus-config.yaml
   kubectl apply -f k8s/grafana-deployment.yaml
   ```

5. **Verify Deployment**
   ```bash
   # Check pod status
   kubectl get pods -n betterprompts
   
   # Check service endpoints
   kubectl get svc -n betterprompts
   
   # Test health endpoints
   curl https://api.betterprompts.com/health
   curl https://api.betterprompts.com/health/ready
   
   # Test classification
   curl -X POST https://api.betterprompts.com/api/v1/intents/classify \
     -H "Content-Type: application/json" \
     -d '{"text": "How do I create a REST API?"}'
   ```

### Post-Deployment

- [ ] **Monitoring**
  - [ ] Grafana dashboards loading correctly
  - [ ] Prometheus scraping metrics
  - [ ] Alerts configured and firing correctly
  - [ ] Logs aggregating properly

- [ ] **Performance**
  - [ ] Load testing completed
  - [ ] Response times within SLA
  - [ ] Auto-scaling working correctly
  - [ ] Circuit breaker functioning

- [ ] **Documentation**
  - [ ] Runbooks updated
  - [ ] API documentation published
  - [ ] Operations guide distributed
  - [ ] Contact information current

## Troubleshooting

### Common Issues

1. **Circuit Breaker Keeps Tripping**
   - Check TorchServe health: `kubectl logs -n model-serving torchserve-0`
   - Verify network connectivity: `kubectl exec -it intent-classifier-0 -- nc -zv torchserve 8080`
   - Increase timeout values if needed

2. **High Memory Usage**
   - Review cache size and TTL settings
   - Check for memory leaks in logs
   - Consider increasing pod memory limits

3. **Slow Response Times**
   - Check TorchServe GPU utilization
   - Review batch size configuration
   - Verify model is using GPU if available

4. **Connection Refused Errors**
   - Ensure TorchServe is running and healthy
   - Check network policies aren't blocking traffic
   - Verify service discovery is working

## Maintenance

### Regular Tasks

- **Weekly**
  - Review error logs and metrics
  - Check certificate expiration dates
  - Verify backup procedures

- **Monthly**
  - Update dependencies and base images
  - Review and tune performance settings
  - Conduct security scans

- **Quarterly**
  - Disaster recovery drill
  - Performance benchmarking
  - Capacity planning review