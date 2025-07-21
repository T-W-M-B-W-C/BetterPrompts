# BetterPrompts AWS Migration Guide

## Executive Summary

This guide provides a comprehensive roadmap for migrating BetterPrompts from its current Docker-based infrastructure to a cost-optimized, auto-scaling AWS architecture. The migration is designed to reduce operational costs by 40% while improving scalability, reliability, and performance.

### Key Benefits
- **40% cost reduction** through spot instances, reserved capacity, and auto-scaling
- **99.9% availability** with multi-AZ deployment and automated failover
- **Elastic scalability** from 10 to 10,000+ RPS with auto-scaling
- **Reduced operational overhead** with managed services (EKS, RDS, ElastiCache)
- **Enhanced security** with VPC isolation, encryption, and IAM controls

### Migration Timeline
- **Total Duration**: 10-12 weeks
- **Phase 1**: Foundation (Weeks 1-2)
- **Phase 2**: Data Layer (Weeks 3-4)
- **Phase 3**: Application Layer (Weeks 5-6)
- **Phase 4**: ML Services (Weeks 7-8)
- **Phase 5**: Optimization & Cutover (Weeks 9-10)
- **Phase 6**: Post-Migration (Weeks 11-12)

## Pre-Migration Checklist

### Prerequisites

#### AWS Account Setup
- [ ] AWS Organization created with separate accounts for dev/staging/prod
- [ ] IAM roles and policies configured for administrators
- [ ] AWS Support plan upgraded (Business or Enterprise)
- [ ] Cost allocation tags defined
- [ ] AWS Activate credits applied (if eligible)

#### Team Preparation
- [ ] AWS training completed for key team members
- [ ] Migration team roles assigned
- [ ] Communication plan established
- [ ] Runbooks and documentation prepared
- [ ] Rollback procedures defined

#### Technical Requirements
- [ ] Current application containers tested and validated
- [ ] Database backup strategy confirmed
- [ ] SSL certificates obtained for domains
- [ ] DNS change procedures prepared
- [ ] Monitoring and alerting requirements documented

### Current State Assessment

#### Infrastructure Inventory
```yaml
Services:
  - Frontend: Next.js (2 replicas)
  - API Gateway: Go/Gin (not yet containerized)
  - Intent Classifier: Python/FastAPI (3 replicas)
  - Technique Selector: Go/Gin (3 replicas)
  - Prompt Generator: Python/FastAPI with GPU (3 replicas)
  - TorchServe: ML model serving (3 replicas with GPU)

Data Stores:
  - PostgreSQL 16 with pgvector
  - Redis 7 (3 databases)

Current Resources:
  - Total CPU: ~25-40 cores
  - Total Memory: ~40-60GB
  - GPU: 3-10 GPUs
  - Storage: ~200GB
```

## Phase 1: Foundation Setup (Weeks 1-2)

### Week 1: AWS Account and Networking

#### Day 1-2: Account Setup
```bash
# 1. Create AWS Organization
aws organizations create-organization --feature-set ALL

# 2. Create separate accounts
aws organizations create-account \
  --email dev@betterprompts.ai \
  --account-name "BetterPrompts-Development"

aws organizations create-account \
  --email staging@betterprompts.ai \
  --account-name "BetterPrompts-Staging"

aws organizations create-account \
  --email prod@betterprompts.ai \
  --account-name "BetterPrompts-Production"

# 3. Set up AWS SSO
aws sso-admin create-instance-access-control
```

#### Day 3-4: Terraform State Backend
```bash
# Create S3 bucket for Terraform state
aws s3 mb s3://betterprompts-terraform-state --region us-east-1
aws s3api put-bucket-versioning \
  --bucket betterprompts-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name betterprompts-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

#### Day 5: Deploy VPC
```bash
cd infrastructure/terraform
terraform init
terraform workspace new development

# Deploy VPC only
terraform apply -target=module.vpc -var-file=environments/development.tfvars
```

### Week 2: EKS Cluster Setup

#### Day 1-2: Deploy EKS
```bash
# Deploy EKS cluster
terraform apply -target=module.eks -var-file=environments/development.tfvars

# Configure kubectl
aws eks update-kubeconfig --name betterprompts-development

# Verify cluster
kubectl get nodes
kubectl get pods -A
```

#### Day 3-4: Install Core Components
```bash
# Install metrics server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Deploy Cluster Autoscaler
kubectl apply -f infrastructure/kubernetes/autoscaling/cluster-autoscaler.yaml

# Install AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=betterprompts-development
```

#### Day 5: Initial Testing
```bash
# Deploy a test application
kubectl create deployment nginx --image=nginx --replicas=3
kubectl expose deployment nginx --type=LoadBalancer --port=80

# Test auto-scaling
kubectl scale deployment nginx --replicas=10
kubectl get nodes -w  # Watch nodes scale up
```

## Phase 2: Data Layer Migration (Weeks 3-4)

### Week 3: Database Migration

#### Day 1-2: Deploy RDS
```bash
# Deploy RDS PostgreSQL with pgvector
terraform apply -target=module.rds -var-file=environments/development.tfvars

# Get RDS endpoint
terraform output rds_endpoint
```

#### Day 3-4: Database Migration
```bash
# 1. Create backup of existing database
docker exec postgres-container pg_dump -U betterprompts > backup.sql

# 2. Create SSH tunnel to RDS (through bastion if needed)
ssh -L 5432:rds-endpoint:5432 bastion-host

# 3. Restore to RDS
psql -h localhost -U betterprompts_admin -d betterprompts < backup.sql

# 4. Enable pgvector extension
psql -h localhost -U betterprompts_admin -d betterprompts
CREATE EXTENSION IF NOT EXISTS vector;
```

#### Day 5: Data Validation
```sql
-- Verify data integrity
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM prompts;
SELECT COUNT(*) FROM ml_embeddings;

-- Test pgvector functionality
SELECT * FROM ml_embeddings 
ORDER BY embedding <-> '[0.1, 0.2, 0.3]' 
LIMIT 5;
```

### Week 4: Cache Layer Migration

#### Day 1-2: Deploy ElastiCache
```bash
# Deploy ElastiCache Redis cluster
terraform apply -target=module.elasticache -var-file=environments/development.tfvars

# Get Redis endpoint
terraform output redis_endpoint
```

#### Day 3-4: Redis Migration
```bash
# 1. Export data from existing Redis
docker exec redis-container redis-cli --rdb /data/dump.rdb

# 2. Import to ElastiCache (if needed)
# Note: ElastiCache doesn't support RDB restore directly
# Use redis-cli MIGRATE or application-level migration

# 3. Test connectivity
redis-cli -h redis-endpoint -p 6379 PING
```

## Phase 3: Application Migration (Weeks 5-6)

### Week 5: Container Registry and CI/CD

#### Day 1-2: ECR Setup
```bash
# Create ECR repositories
for repo in frontend api-gateway intent-classifier technique-selector prompt-generator; do
  aws ecr create-repository --repository-name betterprompts/$repo
done

# Get login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

#### Day 3-4: Build and Push Images
```bash
# Build and push all images
docker compose build

# Tag and push
for service in frontend api-gateway intent-classifier technique-selector prompt-generator; do
  docker tag betterprompts-$service:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/betterprompts/$service:latest
  
  docker push \
    $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/betterprompts/$service:latest
done
```

#### Day 5: CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy to EKS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
      
      - name: Build and push
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
      
      - name: Deploy to EKS
        run: |
          aws eks update-kubeconfig --name betterprompts-production
          kubectl set image deployment/frontend frontend=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
```

### Week 6: Application Deployment

#### Day 1-2: Deploy Core Services
```bash
# Create Kubernetes manifests
kubectl apply -f infrastructure/kubernetes/namespaces.yaml
kubectl apply -f infrastructure/kubernetes/configmaps.yaml
kubectl apply -f infrastructure/kubernetes/secrets.yaml

# Deploy applications
kubectl apply -f infrastructure/kubernetes/deployments/
kubectl apply -f infrastructure/kubernetes/services/

# Deploy HPA
kubectl apply -f infrastructure/kubernetes/autoscaling/hpa-configs.yaml
```

#### Day 3-4: Configure Ingress
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: betterprompts-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/certificate-arn: ${ACM_CERT_ARN}
spec:
  rules:
  - host: api.betterprompts.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 80
```

#### Day 5: Integration Testing
```bash
# Run smoke tests
./scripts/smoke-tests.sh

# Run load tests
k6 run scripts/load-test.js

# Verify auto-scaling
watch kubectl get hpa
```

## Phase 4: ML Services Migration (Weeks 7-8)

### Week 7: GPU Infrastructure

#### Day 1-2: Verify GPU Nodes
```bash
# Check GPU nodes
kubectl get nodes -l node_group=gpu

# Deploy NVIDIA device plugin
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/main/deployments/static/nvidia-device-plugin.yml

# Verify GPU availability
kubectl describe node gpu-node
```

#### Day 3-5: Deploy TorchServe
```bash
# Deploy TorchServe
kubectl apply -f infrastructure/kubernetes/deployments/torchserve.yaml

# Upload models to S3
aws s3 cp models/ s3://betterprompts-models/ --recursive

# Register models with TorchServe
curl -X POST "http://torchserve:8081/models" \
  -F "model_name=intent_classifier" \
  -F "url=s3://betterprompts-models/intent_classifier.mar"
```

### Week 8: ML Service Integration

#### Day 1-3: Update Service Configurations
```python
# Update intent classifier to use TorchServe
TORCHSERVE_URL = os.getenv("TORCHSERVE_URL", "http://torchserve:8080")

async def classify_intent(text: str):
    response = await http_client.post(
        f"{TORCHSERVE_URL}/predictions/intent_classifier",
        json={"text": text}
    )
    return response.json()
```

#### Day 4-5: Performance Testing
```bash
# Run ML-specific load tests
python scripts/ml_load_test.py

# Monitor GPU utilization
kubectl exec -it torchserve-pod -- nvidia-smi -l 1

# Check inference latency
curl -w "@curl-format.txt" -X POST http://torchserve:8080/predictions/intent_classifier
```

## Phase 5: Optimization & Cutover (Weeks 9-10)

### Week 9: Performance Optimization

#### Day 1-2: Enable Cost Optimizations
```bash
# Deploy spot instance handler
kubectl apply -f infrastructure/kubernetes/cost-optimization/spot-instance-handler.yaml

# Apply resource quotas
kubectl apply -f infrastructure/kubernetes/cost-optimization/resource-quotas.yaml

# Deploy cost monitoring
kubectl apply -f infrastructure/kubernetes/monitoring/cost-monitoring.yaml
```

#### Day 3-4: Fine-tune Auto-scaling
```bash
# Adjust HPA thresholds based on load testing
kubectl edit hpa frontend-hpa

# Enable VPA recommendations
kubectl apply -f infrastructure/kubernetes/autoscaling/vpa-configs.yaml

# Review recommendations
kubectl describe vpa
```

#### Day 5: Security Hardening
```bash
# Apply network policies
kubectl apply -f infrastructure/kubernetes/security/network-policies.yaml

# Enable Pod Security Standards
kubectl label namespace default pod-security.kubernetes.io/enforce=restricted

# Run security scan
kubesec scan infrastructure/kubernetes/deployments/*.yaml
```

### Week 10: Cutover

#### Day 1: Final Testing
```bash
# Run full integration test suite
./scripts/integration-tests.sh

# Verify all endpoints
./scripts/health-check.sh

# Load test at production scale
k6 run scripts/production-load-test.js
```

#### Day 2-3: DNS Cutover
```bash
# 1. Lower DNS TTL (24 hours before)
# 2. Update DNS to point to AWS ALB
# 3. Monitor traffic shift
# 4. Keep old infrastructure running
```

#### Day 4-5: Monitoring and Validation
```bash
# Monitor application metrics
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Check error rates
kubectl logs -f deployment/api-gateway

# Verify cost optimization
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity DAILY \
  --metrics "UnblendedCost"
```

## Phase 6: Post-Migration (Weeks 11-12)

### Week 11: Cleanup and Documentation

#### Old Infrastructure Removal
```bash
# After 1 week of stable operation
# 1. Take final backup
docker compose exec postgres pg_dump -U betterprompts > final-backup.sql

# 2. Stop old services
docker compose down

# 3. Archive configuration
tar -czf old-infrastructure-backup.tar.gz docker-compose.yml docker/
```

#### Documentation Updates
- [ ] Update README with new infrastructure details
- [ ] Document new deployment procedures
- [ ] Create troubleshooting guide
- [ ] Update monitoring dashboards

### Week 12: Optimization Review

#### Cost Analysis
```bash
# Generate cost report
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --group-by Type=DIMENSION,Key=SERVICE

# Review savings
# Expected: 40% reduction from baseline
```

#### Performance Review
- API response time: Target < 200ms (p95)
- ML inference time: Target < 500ms (p95)
- Availability: Target 99.9%
- Auto-scaling effectiveness

## Rollback Procedures

### Application Rollback
```bash
# 1. Quick rollback (change image tag)
kubectl set image deployment/frontend frontend=previous-image:tag

# 2. Full rollback (revert to docker compose)
# Update DNS to point back to original infrastructure
# Start docker compose environment
```

### Database Rollback
```bash
# 1. Stop applications
kubectl scale deployment --all --replicas=0

# 2. Restore from backup
psql -h rds-endpoint -U admin -d betterprompts < backup.sql

# 3. Restart applications
kubectl scale deployment --all --replicas=3
```

## Validation Checklist

### Infrastructure Validation
- [ ] VPC and networking configured correctly
- [ ] EKS cluster running with all node groups
- [ ] RDS accessible and pgvector enabled
- [ ] ElastiCache cluster healthy
- [ ] S3 buckets created with proper permissions
- [ ] Load balancer SSL certificates working

### Application Validation
- [ ] All services deployed and running
- [ ] Health checks passing
- [ ] Auto-scaling working (HPA and Cluster Autoscaler)
- [ ] Logs aggregating properly
- [ ] Metrics visible in monitoring

### Performance Validation
- [ ] API response times meet SLA
- [ ] ML inference times acceptable
- [ ] Database queries optimized
- [ ] No memory leaks or resource issues

### Security Validation
- [ ] Network policies enforced
- [ ] IAM roles properly configured
- [ ] Secrets managed securely
- [ ] Encryption enabled for data at rest
- [ ] VPC flow logs enabled

### Cost Validation
- [ ] Spot instances running
- [ ] Reserved instances purchased
- [ ] Cost monitoring alerts working
- [ ] Monthly costs within budget

## Support Contacts

### AWS Support
- Account ID: [Your AWS Account ID]
- Support Plan: Business/Enterprise
- Phone: 1-800-xxx-xxxx

### Internal Contacts
- Migration Lead: [Name] - [Email]
- Infrastructure Team: [Email]
- On-call: [PagerDuty/Phone]

### Escalation Path
1. On-call engineer
2. Team lead
3. Infrastructure architect
4. CTO

## Appendices

### A. Useful Commands
```bash
# Check cluster status
kubectl get nodes
kubectl get pods -A
kubectl top nodes
kubectl top pods

# View logs
kubectl logs -f deployment/api-gateway
stern api-gateway  # Better log viewer

# Debug pods
kubectl describe pod <pod-name>
kubectl exec -it <pod-name> -- /bin/bash

# Cost analysis
kubectl cost namespace
```

### B. Monitoring URLs
- Grafana: https://grafana.betterprompts.ai
- Prometheus: https://prometheus.betterprompts.ai
- AWS Console: https://console.aws.amazon.com
- Cost Explorer: https://console.aws.amazon.com/cost-management/

### C. Reference Architecture
See `planning/aws-architecture-design.md` for detailed architecture diagrams and component specifications.

---

This migration guide should be treated as a living document and updated throughout the migration process with lessons learned and optimizations discovered.