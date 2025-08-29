# BetterPrompts AWS Infrastructure

This directory contains Terraform configurations for deploying BetterPrompts on AWS with a cost-optimized, auto-scaling architecture.

## 🏗️ Architecture Overview

The infrastructure includes:
- **Amazon EKS** for container orchestration with multiple node groups (system, application, GPU, spot)
- **Amazon RDS PostgreSQL** with pgvector extension for vector embeddings
- **Amazon ElastiCache** for Redis caching
- **VPC** with public, private, database, and ML subnets across 3 AZs
- **Cost optimization** through spot instances, reserved instances, and savings plans

## 📁 Directory Structure

```
terraform/
├── main.tf                    # Root module configuration
├── variables.tf               # Root module variables
├── terraform.tfvars.example   # Example variables file
├── modules/                   # Reusable Terraform modules
│   ├── vpc/                   # VPC with subnets and networking
│   ├── eks/                   # EKS cluster and node groups
│   ├── rds/                   # RDS PostgreSQL with pgvector
│   ├── elasticache/           # ElastiCache Redis cluster
│   ├── s3/                    # S3 buckets for storage
│   ├── iam/                   # IAM roles and policies
│   ├── monitoring/            # CloudWatch monitoring
│   ├── alb/                   # Application Load Balancer
│   └── cost-optimization/     # Cost optimization resources
└── environments/              # Environment-specific configurations
    ├── development.tfvars     # Development environment
    ├── staging.tfvars         # Staging environment
    └── production.tfvars      # Production environment
```

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.5.0
3. **kubectl** for Kubernetes management
4. **AWS IAM permissions** for creating all required resources

### Initial Setup

1. **Create S3 bucket for Terraform state**:
```bash
aws s3 mb s3://betterprompts-terraform-state --region us-east-1
aws s3api put-bucket-versioning \
  --bucket betterprompts-terraform-state \
  --versioning-configuration Status=Enabled
```

2. **Create DynamoDB table for state locking**:
```bash
aws dynamodb create-table \
  --table-name betterprompts-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region us-east-1
```

3. **Initialize Terraform**:
```bash
cd infrastructure/terraform
terraform init
```

### Deployment

1. **Review and customize the environment file**:
```bash
# Copy the appropriate environment file
cp environments/development.tfvars terraform.tfvars

# Edit with your specific values
vi terraform.tfvars
```

2. **Plan the deployment**:
```bash
terraform plan
```

3. **Apply the configuration**:
```bash
terraform apply
```

4. **Configure kubectl**:
```bash
aws eks update-kubeconfig --name betterprompts-development --region us-east-1
```

## 📊 Cost Optimization Features

### Implemented Optimizations

1. **Spot Instances** (70% savings)
   - 40% of workloads run on spot instances
   - Automatic fallback to on-demand if spot unavailable

2. **Reserved Instances** (30% savings)
   - RDS and ElastiCache reserved capacity
   - 1-year term recommended

3. **Savings Plans** (20% savings)
   - Compute Savings Plan for EC2 instances
   - Covers both on-demand and spot usage

4. **Auto-scaling**
   - Cluster Autoscaler for EKS nodes
   - HPA for pod scaling
   - Scheduled scaling for predictable patterns

5. **VPC Endpoints**
   - S3 and DynamoDB endpoints reduce NAT Gateway costs
   - Save on data transfer charges

### Estimated Monthly Costs

| Environment | Baseline | With Optimizations | Savings |
|------------|----------|-------------------|---------|
| Development | $1,200 | $700 | 42% |
| Staging | $2,500 | $1,500 | 40% |
| Production | $5,000 | $3,000 | 40% |

## 🔧 Module Details

### VPC Module
- Multi-AZ deployment across 3 availability zones
- Separate subnets for public, private, database, and ML workloads
- NAT Gateways for private subnet internet access
- VPC Flow Logs for security monitoring

### EKS Module
- Managed node groups with automatic scaling
- GPU nodes with proper taints for ML workloads
- Spot instance integration for cost savings
- IRSA (IAM Roles for Service Accounts) enabled

### RDS Module
- PostgreSQL 16 with pgvector extension
- Multi-AZ deployment in production
- Automated backups and snapshots
- Performance Insights and Enhanced Monitoring
- Read replicas for scaling read operations

### ElastiCache Module
- Redis 7 cluster mode enabled
- Multi-AZ with automatic failover
- Parameter groups optimized for caching

## 🛠️ Common Operations

### Scaling Operations

**Scale EKS nodes**:
```bash
# Update the desired capacity in terraform.tfvars
# application_node_group_config.scaling_config.desired_size = 5
terraform apply -target=module.eks
```

**Add read replicas**:
```bash
# Set in terraform.tfvars
# create_read_replica = true
# read_replica_count = 2
terraform apply -target=module.rds
```

### Cost Management

**Enable auto-shutdown for development**:
```bash
# The cost-optimization module handles this automatically
# Shuts down at 8 PM, starts at 8 AM on weekdays
```

**Review costs**:
```bash
# Check the CloudWatch dashboard created by the monitoring module
# URL will be in terraform output: monitoring_dashboard_url
```

### Maintenance

**Update EKS cluster version**:
```bash
# Update eks_cluster_version in terraform.tfvars
# Follow AWS EKS upgrade guide for node groups
terraform apply -target=module.eks.aws_eks_cluster.main
```

**Apply security patches**:
```bash
# RDS and ElastiCache handle patches automatically during maintenance windows
# For EKS nodes, update the AMI version and roll nodes
```

## 🔒 Security Features

- **Encryption at rest** using AWS KMS for all data
- **Network isolation** with private subnets
- **IAM roles** with least privilege access
- **Security groups** with minimal required access
- **AWS WAF** integration for web application firewall
- **VPC Flow Logs** for network monitoring

## 🚨 Monitoring and Alerts

The monitoring module creates:
- CloudWatch dashboards for all services
- Alarms for CPU, memory, and disk usage
- Cost anomaly detection
- SNS topics for alert notifications

## 📝 Backup and Recovery

- **RDS**: Automated daily backups with 7-day retention
- **EKS**: Velero can be installed for cluster backup
- **S3**: Versioning enabled on critical buckets
- **Disaster Recovery**: Multi-region setup possible

## 🔄 CI/CD Integration

Example GitHub Actions workflow:
```yaml
name: Deploy Infrastructure
on:
  push:
    branches: [main]
    paths:
      - 'infrastructure/terraform/**'

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2
      - name: Terraform Init
        run: terraform init
      - name: Terraform Plan
        run: terraform plan -var-file=environments/production.tfvars
      - name: Terraform Apply
        if: github.ref == 'refs/heads/main'
        run: terraform apply -auto-approve -var-file=environments/production.tfvars
```

## 🆘 Troubleshooting

### Common Issues

1. **Spot instance unavailable**:
   - The ASG will automatically try different instance types
   - Check CloudWatch logs for the Auto Scaling Group

2. **RDS connection issues**:
   - Verify security group rules
   - Check that pgvector extension is enabled
   - Review CloudWatch logs

3. **High costs**:
   - Review Cost Explorer for unexpected usage
   - Check for unattached EBS volumes
   - Verify spot instances are being used

### Debug Commands

```bash
# Check EKS cluster status
aws eks describe-cluster --name betterprompts-production

# View RDS logs
aws rds describe-db-log-files --db-instance-identifier betterprompts-production

# Check spot instance usage
aws ec2 describe-spot-instance-requests --filters "Name=state,Values=active"
```

## 📚 Additional Resources

- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [RDS PostgreSQL with pgvector](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.html)
- [Cost Optimization Checklist](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)
- [Terraform AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest)

## 📄 License

This infrastructure code is part of the BetterPrompts project and follows the same licensing terms.