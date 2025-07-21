# BetterPrompts AWS Architecture Design

## Executive Summary

This document outlines a cost-optimized, auto-scaling AWS architecture for BetterPrompts, leveraging managed services for operational efficiency and implementing intelligent scaling strategies to minimize costs while maintaining performance SLAs.

## Architecture Overview

### Core Design Principles
- **Cost Optimization**: Multi-tier resource allocation with spot instances for non-critical workloads
- **Auto-Scaling**: Predictive and reactive scaling based on metrics
- **High Availability**: Multi-AZ deployment with automated failover
- **Security**: Defense in depth with VPC isolation and IAM policies
- **Operational Excellence**: Managed services to reduce operational overhead

## Service Architecture

### 1. Container Orchestration - Amazon EKS

**Cluster Configuration**:
- **Control Plane**: Managed EKS in 3 AZs
- **Node Groups**:
  - **System Node Group**: t3a.medium (2-4 nodes) for system pods
  - **Application Node Group**: c6i.xlarge (3-9 nodes) with mixed instances
  - **GPU Node Group**: g4dn.xlarge (1-5 nodes) for ML workloads
  - **Spot Node Group**: Mixed t3a/t3 instances (0-10 nodes) for non-critical workloads

**Cost Optimization**:
- Spot instances for 40% of non-GPU workloads (70% cost savings)
- Reserved Instances for baseline capacity (30% savings)
- Cluster Autoscaler with priority-based scaling
- Karpenter for intelligent node provisioning

### 2. Database Layer

**Amazon RDS for PostgreSQL**:
- **Instance Type**: db.r6g.xlarge with pgvector support
- **Multi-AZ**: Enabled for high availability
- **Storage**: 500GB GP3 with auto-scaling to 2TB
- **Read Replicas**: 1-2 replicas for read-heavy workloads
- **Backup**: Automated backups with 7-day retention

**Amazon ElastiCache for Redis**:
- **Node Type**: cache.r6g.large (production)
- **Cluster Mode**: Enabled with 3 shards
- **Replication**: 1 replica per shard
- **Eviction Policy**: allkeys-lru
- **Reserved Nodes**: 1-year term for 30% savings

### 3. ML Infrastructure

**Option A: EKS-based TorchServe**:
- GPU instances with automatic scaling (1-10 nodes)
- Spot GPU instances for training workloads
- S3 for model storage with lifecycle policies

**Option B: Amazon SageMaker (Recommended)**:
- **Inference Endpoints**: Multi-model endpoints for cost efficiency
- **Auto-Scaling**: Based on InvocationsPerInstance metric
- **Instance Types**: ml.g4dn.xlarge for inference
- **Cost Optimization**: 
  - Serverless inference for low-traffic periods
  - Batch transform for bulk processing
  - 40% cost reduction vs. dedicated GPU instances

### 4. Application Layer

**Frontend Hosting**:
- **Amazon S3**: Static asset hosting
- **CloudFront**: Global CDN with caching
- **Lambda@Edge**: Dynamic rendering for SEO
- **Cost**: ~$50/month for moderate traffic

**API Gateway**:
- **Application Load Balancer**: For container routing
- **AWS API Gateway**: For serverless endpoints
- **WAF**: Protection against common attacks

### 5. Serverless Components

**AWS Lambda Functions**:
- Image optimization
- Webhook processing
- Scheduled tasks
- Cost: Pay-per-request model

**Step Functions**:
- Complex workflow orchestration
- Error handling and retries
- Visual workflow monitoring

### 6. Storage

**Amazon S3**:
- **Buckets**:
  - `betterprompts-models`: ML model artifacts
  - `betterprompts-assets`: Static assets
  - `betterprompts-backups`: Database backups
  - `betterprompts-logs`: Centralized logging
- **Lifecycle Policies**:
  - Infrequent Access after 30 days
  - Glacier after 90 days for backups
  - Intelligent-Tiering for unknown access patterns

**Amazon EFS**:
- Shared storage for Kubernetes pods
- Infrequent Access mode for cost optimization
- Lifecycle management enabled

### 7. Networking

**VPC Design**:
```
Production VPC (10.0.0.0/16)
├── Public Subnets (10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24)
│   └── ALB, NAT Gateways
├── Private App Subnets (10.0.11.0/24, 10.0.12.0/24, 10.0.13.0/24)
│   └── EKS Worker Nodes
├── Private DB Subnets (10.0.21.0/24, 10.0.22.0/24, 10.0.23.0/24)
│   └── RDS, ElastiCache
└── Private ML Subnets (10.0.31.0/24, 10.0.32.0/24, 10.0.33.0/24)
    └── GPU Nodes, SageMaker
```

**Cost Optimization**:
- NAT Instance instead of NAT Gateway for dev/staging ($45 vs $135/month)
- VPC Endpoints for S3/DynamoDB to reduce data transfer costs
- Transit Gateway for multi-region deployment

### 8. Monitoring & Observability

**AWS Native Stack**:
- **CloudWatch**: Metrics and alarms
- **X-Ray**: Distributed tracing
- **CloudWatch Logs**: Centralized logging
- **Cost Explorer**: Cost tracking and optimization

**Open Source Stack** (Cost-Optimized):
- **Prometheus**: On EKS with EBS volumes
- **Grafana**: Managed Grafana service
- **OpenTelemetry**: Distributed tracing
- **Fluentd**: Log aggregation to S3

### 9. CI/CD Pipeline

**AWS CodePipeline**:
- Source: GitHub integration
- Build: CodeBuild with caching
- Deploy: EKS deployment via CodeDeploy
- Cost: ~$1 per pipeline per month

**Alternative: GitHub Actions with AWS**:
- Self-hosted runners on spot instances
- Direct deployment to EKS
- Cost: Spot instance costs only

## Auto-Scaling Strategy

### Application Auto-Scaling

**EKS Horizontal Pod Autoscaler (HPA)**:
```yaml
Frontend: CPU 70%, Memory 80% (2-10 pods)
Intent Classifier: CPU 60%, Queue depth (3-15 pods)
Technique Selector: CPU 70%, RPS (3-12 pods)
Prompt Generator: GPU utilization 70% (1-8 pods)
```

**Cluster Autoscaler**:
- Scale up when pods pending > 30 seconds
- Scale down when node utilization < 50% for 10 minutes
- Protect GPU nodes from aggressive scale-down

### Database Auto-Scaling

**RDS**:
- Storage auto-scaling: 10% free space threshold
- Read replica auto-scaling based on CPU/connections
- Automated minor version upgrades

**ElastiCache**:
- Auto-discovery for dynamic shard management
- CloudWatch alarms for memory/CPU scaling

### Predictive Scaling

**Target Tracking Policies**:
- Business hours scaling (7 AM - 7 PM weekdays)
- Geographic-based scaling (follow the sun)
- ML-based traffic prediction

## Cost Optimization Strategies

### 1. Compute Optimization
- **Savings Plans**: 1-year compute savings plan (20% discount)
- **Reserved Instances**: RDS and ElastiCache (30% discount)
- **Spot Instances**: 40% of stateless workloads (70% savings)
- **Right-Sizing**: Continuous monitoring and adjustment

### 2. Storage Optimization
- **S3 Intelligent-Tiering**: Automatic cost optimization
- **EBS GP3**: 20% cheaper than GP2
- **Snapshot Lifecycle**: Delete snapshots > 30 days
- **Data Compression**: Enable for all applicable services

### 3. Network Optimization
- **VPC Endpoints**: Reduce NAT Gateway costs
- **CloudFront**: Cache static content aggressively
- **Direct Connect**: For consistent high-volume transfer

### 4. Operational Optimization
- **Automated Shutdown**: Dev/staging environments
- **Resource Tagging**: Track costs by service/team
- **Budget Alerts**: Proactive cost monitoring
- **Cost Anomaly Detection**: AI-powered alerts

## Estimated Monthly Costs

### Production Environment

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| EKS Control Plane | 1 cluster | $72 |
| EKS Worker Nodes | Mixed instances + Spot | $800-1200 |
| GPU Nodes | g4dn.xlarge (1-5) | $400-2000 |
| RDS PostgreSQL | db.r6g.xlarge Multi-AZ | $650 |
| ElastiCache | cache.r6g.large x3 | $450 |
| Application Load Balancer | 1 ALB | $25 |
| S3 Storage | ~1TB | $25 |
| CloudFront | ~5TB transfer | $425 |
| Data Transfer | Inter-AZ/Internet | $200 |
| CloudWatch | Logs/Metrics | $150 |
| **Total (Baseline)** | | **$3,200-4,000** |
| **Total (Peak Load)** | | **$5,000-6,500** |

### Cost Reduction Opportunities
- **With Savings Plans**: -20% on compute = $600-800/month savings
- **With Reserved Instances**: -30% on RDS/Cache = $330/month savings
- **With Spot Instances**: -70% on 40% compute = $350/month savings
- **Total Potential Savings**: $1,280-1,480/month (40% reduction)

### Development Environment
- Use smaller instances (50% of production)
- Shut down nights/weekends (70% reduction)
- Estimated cost: $500-700/month

## Security Architecture

### Network Security
- **VPC Flow Logs**: Monitor all network traffic
- **Security Groups**: Least-privilege access
- **NACLs**: Additional subnet-level protection
- **AWS WAF**: Application-layer protection

### Data Security
- **Encryption at Rest**: All data encrypted with KMS
- **Encryption in Transit**: TLS 1.3 for all connections
- **Secrets Manager**: Centralized secret management
- **Parameter Store**: Configuration management

### Identity & Access
- **IAM Roles**: Service-specific permissions
- **IRSA**: IAM roles for service accounts
- **MFA**: Required for all human users
- **SSO**: Centralized authentication

### Compliance
- **AWS Config**: Continuous compliance monitoring
- **GuardDuty**: Threat detection
- **Security Hub**: Centralized security findings
- **CloudTrail**: Audit logging

## Disaster Recovery

### Backup Strategy
- **RDS**: Automated backups + manual snapshots
- **Application State**: Velero for Kubernetes backups
- **S3 Cross-Region**: Replication for critical data
- **Recovery Time Objective (RTO)**: 1 hour
- **Recovery Point Objective (RPO)**: 15 minutes

### Multi-Region Considerations
- Pilot light DR in us-west-2
- Route 53 health checks for failover
- Cross-region read replicas
- Estimated additional cost: $800/month

## Migration Phases

### Phase 1: Foundation (Week 1-2)
- VPC and networking setup
- EKS cluster deployment
- IAM roles and policies
- Basic monitoring

### Phase 2: Data Layer (Week 3-4)
- RDS deployment and migration
- ElastiCache setup
- S3 buckets and policies
- Backup configuration

### Phase 3: Application Layer (Week 5-6)
- Container migration to EKS
- Load balancer configuration
- Auto-scaling setup
- Integration testing

### Phase 4: ML Services (Week 7-8)
- SageMaker endpoint deployment
- Model migration to S3
- GPU node configuration
- Performance testing

### Phase 5: Optimization (Week 9-10)
- Cost optimization implementation
- Performance tuning
- Security hardening
- Documentation

## Success Metrics

### Performance KPIs
- API Response Time: p95 < 200ms ✓
- ML Inference: p95 < 500ms ✓
- Availability: 99.9% uptime ✓
- Auto-scaling Response: < 2 minutes ✓

### Cost KPIs
- Cost per Request: < $0.001
- Infrastructure Efficiency: > 70% utilization
- Reserved Capacity: 60% of baseline
- Spot Instance Success: > 95%

## Recommendations

1. **Start with SageMaker** for ML serving - significant cost and operational benefits
2. **Implement cost allocation tags** from day one for accurate tracking
3. **Use Infrastructure as Code** (Terraform) for all resources
4. **Enable all cost optimization features** during initial deployment
5. **Set up automated cost reports** and anomaly detection
6. **Consider AWS Activate credits** if eligible (up to $100k)
7. **Engage AWS Solution Architects** for architecture review
8. **Plan for AWS re:Invent announcements** that might reduce costs further

## Next Steps

1. Review and approve architecture design
2. Create detailed Terraform modules
3. Set up AWS Organizations and accounts
4. Deploy foundation infrastructure
5. Begin phased migration

This architecture provides a robust, scalable, and cost-optimized foundation for BetterPrompts on AWS, with the flexibility to adapt as the application grows and evolves.