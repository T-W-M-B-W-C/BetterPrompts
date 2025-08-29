# BetterPrompts Auto-Scaling & Cost Optimization Guide

This directory contains configurations for implementing comprehensive auto-scaling and cost optimization for the BetterPrompts platform on AWS EKS.

## 🎯 Overview

Our auto-scaling strategy operates at three levels:
1. **Cluster Level**: Node auto-scaling with Cluster Autoscaler
2. **Pod Level**: Horizontal and Vertical Pod Autoscaling
3. **Cost Optimization**: Spot instances, resource quotas, and monitoring

## 📊 Auto-Scaling Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Traffic                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 Application Load Balancer                    │
│                    (Auto-scales targets)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                        Pods (HPA)                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  Frontend  │  │API Gateway │  │ML Services │           │
│  │  2-10 pods │  │ 3-15 pods  │  │ 1-8 pods   │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Nodes (Cluster Autoscaler)                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │   System   │  │Application │  │    GPU     │           │
│  │  2-4 nodes │  │ 3-9 nodes  │  │ 1-5 nodes  │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│                  ┌────────────┐                             │
│                  │    Spot    │                             │
│                  │ 0-10 nodes │                             │
│                  └────────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Deployment Instructions

### Prerequisites

1. **EKS cluster deployed** using the Terraform configuration
2. **Metrics Server** installed for HPA functionality
3. **Prometheus** deployed for custom metrics

### Step 1: Deploy Cluster Autoscaler

```bash
# Update the CLUSTER_NAME in the manifest
sed -i 's/CLUSTER_NAME/betterprompts-production/g' autoscaling/cluster-autoscaler.yaml

# Update the AWS account ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
sed -i "s/ACCOUNT_ID/$AWS_ACCOUNT_ID/g" autoscaling/cluster-autoscaler.yaml

# Deploy Cluster Autoscaler
kubectl apply -f autoscaling/cluster-autoscaler.yaml

# Verify deployment
kubectl -n kube-system logs -f deployment/cluster-autoscaler
```

### Step 2: Deploy HPA Configurations

```bash
# Deploy HPA for all services
kubectl apply -f autoscaling/hpa-configs.yaml

# Check HPA status
kubectl get hpa -A
kubectl describe hpa frontend-hpa
```

### Step 3: Deploy VPA (Optional)

```bash
# Install VPA CRDs first
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/vertical-pod-autoscaler/deploy/vpa-v1-crd-gen.yaml

# Deploy VPA admission controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/vertical-pod-autoscaler/deploy/vpa-rbac.yaml

# Deploy VPA configurations
kubectl apply -f autoscaling/vpa-configs.yaml

# Check VPA recommendations
kubectl get vpa -A
kubectl describe vpa frontend-vpa
```

### Step 4: Deploy Spot Instance Handler

```bash
# Update AWS account ID
sed -i "s/ACCOUNT_ID/$AWS_ACCOUNT_ID/g" cost-optimization/spot-instance-handler.yaml

# Deploy Node Termination Handler
kubectl apply -f cost-optimization/spot-instance-handler.yaml

# Verify DaemonSet is running on all nodes
kubectl -n kube-system get ds aws-node-termination-handler
```

### Step 5: Apply Resource Quotas

```bash
# Create namespaces if they don't exist
kubectl create namespace development --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace staging --dry-run=client -o yaml | kubectl apply -f -

# Apply resource quotas
kubectl apply -f cost-optimization/resource-quotas.yaml

# Verify quotas
kubectl describe resourcequota -A
```

### Step 6: Deploy Cost Monitoring

```bash
# Deploy Prometheus rules
kubectl apply -f monitoring/cost-monitoring.yaml

# Import Grafana dashboard
# Access Grafana and import the dashboard from the ConfigMap
```

## 📈 Scaling Behaviors

### Frontend Service
- **Scale Up**: When CPU > 70% or Memory > 80%
- **Scale Down**: After 5 minutes of low usage
- **Min/Max**: 2-10 pods

### API Gateway
- **Scale Up**: When CPU > 60% or RPS > 1000
- **Scale Down**: After 5 minutes, max 20% reduction
- **Min/Max**: 3-15 pods

### ML Services
- **Scale Up**: When queue depth > 10 or GPU > 70%
- **Scale Down**: Very conservative (10 minutes)
- **Min/Max**: 1-8 pods

### Node Scaling
- **Scale Up**: When pods can't be scheduled
- **Scale Down**: When utilization < 50% for 5 minutes
- **Spot Priority**: Prefer spot instances for non-ML workloads

## 💰 Cost Optimization Features

### 1. Spot Instance Usage
- 40% of workloads on spot instances
- Automatic handling of interruptions
- Fallback to on-demand when needed

### 2. Resource Right-Sizing
- VPA provides recommendations
- Prevents over-provisioning
- Optimizes resource requests

### 3. Scheduled Scaling
```bash
# Example: Scale down development environment at night
kubectl patch hpa frontend-hpa -n development --type merge -p '{"spec":{"minReplicas":0}}'
```

### 4. Idle Resource Detection
- Alerts on underutilized resources
- Identifies optimization opportunities
- Tracks resource waste

## 📊 Monitoring & Alerts

### Key Metrics to Monitor

1. **Cluster Metrics**
   - Node CPU/Memory utilization
   - Pod scheduling latency
   - Spot instance interruption rate

2. **Application Metrics**
   - Request rate and latency
   - Queue depths
   - Error rates

3. **Cost Metrics**
   - Hourly cost by namespace
   - Resource waste percentage
   - Spot instance savings

### Alert Thresholds

| Alert | Threshold | Action |
|-------|-----------|--------|
| High Cost | > $10/hour | Review scaling policies |
| Low Utilization | < 30% for 2h | Scale down resources |
| High Waste | > 50% unused | Right-size pods |
| Spot Termination | Any | Monitor replacements |

## 🛠️ Troubleshooting

### HPA Not Scaling

```bash
# Check metrics server
kubectl top nodes
kubectl top pods

# Check HPA status
kubectl describe hpa <hpa-name>

# Check metrics
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes
```

### Cluster Autoscaler Issues

```bash
# Check CA logs
kubectl -n kube-system logs deployment/cluster-autoscaler

# Check node labels
kubectl get nodes --show-labels | grep cluster-autoscaler

# Check ASG tags in AWS
aws autoscaling describe-auto-scaling-groups
```

### Spot Instance Problems

```bash
# Check spot instance requests
aws ec2 describe-spot-instance-requests

# Check node termination handler
kubectl -n kube-system logs daemonset/aws-node-termination-handler

# Force cordon/drain test
kubectl cordon <node-name>
kubectl drain <node-name> --ignore-daemonsets
```

## 🔧 Advanced Configurations

### Custom Metrics HPA

```yaml
# Example: Scale based on SQS queue depth
- type: External
  external:
    metric:
      name: sqs_queue_depth
      selector:
        matchLabels:
          queue_name: ml-inference
    target:
      type: Value
      value: "100"
```

### Predictive Scaling

```yaml
# Add to HPA behavior section
behavior:
  scaleUp:
    policies:
    - type: Percent
      value: 200
      periodSeconds: 60
    predictive:
      lookback: 24h
      algorithm: linear
```

### Multi-Cluster Scaling

For multi-region deployments:
1. Use Global Accelerator for traffic distribution
2. Implement cross-region metrics aggregation
3. Coordinate scaling policies across regions

## 📚 Best Practices

1. **Start Conservative**: Begin with higher thresholds and adjust based on observations
2. **Monitor Actively**: Watch metrics for the first week after deployment
3. **Test Scaling**: Perform load tests to validate scaling behaviors
4. **Document Changes**: Keep track of threshold adjustments and their impacts
5. **Review Regularly**: Monthly reviews of scaling efficiency and costs

## 🔗 Additional Resources

- [Kubernetes Autoscaling Guide](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/cluster-autoscaling/)
- [Spot Instance Best Practices](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-best-practices.html)
- [Cost Optimization Checklist](https://www.cncf.io/blog/2021/05/20/finops-for-kubernetes/)

## 📝 Configuration Checklist

- [ ] Cluster Autoscaler deployed and working
- [ ] HPA configured for all services
- [ ] VPA deployed (at least in recommendation mode)
- [ ] Spot instance handler running on all nodes
- [ ] Resource quotas applied to all namespaces
- [ ] Cost monitoring dashboard accessible
- [ ] Alerts configured and tested
- [ ] Scaling behaviors validated with load tests
- [ ] Documentation updated with any customizations