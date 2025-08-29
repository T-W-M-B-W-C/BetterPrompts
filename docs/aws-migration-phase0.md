# AWS Phase 0 Migration Guide - BetterPrompts MVP

## Overview
Minimal AWS setup for faster development. No production features, just speed.

**Goal**: Get BetterPrompts running on AWS in <2 hours for development purposes.

**What we're NOT doing**:
- No auto-scaling
- No multi-AZ redundancy
- No CloudFront CDN
- No fancy monitoring
- No Kubernetes/ECS

**What we ARE doing**:
- Single EC2 instance with Docker
- Managed PostgreSQL (RDS)
- Managed Redis (ElastiCache)
- Simple networking
- Direct deployment

## Prerequisites

```bash
# Install AWS CLI
brew install awscli

# Configure AWS credentials
aws configure

# Install required tools
brew install jq
```

## Phase 0 Architecture

```
┌─────────────────┐
│   Developer     │
│   Laptop        │
└────────┬────────┘
         │ SSH
         ▼
┌─────────────────┐     ┌─────────────────┐
│  EC2 Instance   │────▶│  RDS PostgreSQL │
│  (t3.xlarge)    │     │  (db.t3.medium) │
│                 │     └─────────────────┘
│  Docker Compose │
│  - Frontend     │     ┌─────────────────┐
│  - Backend APIs │────▶│  ElastiCache    │
│  - Nginx        │     │  Redis          │
└─────────────────┘     └─────────────────┘
```

## Step 1: Create AWS Resources (15 minutes)

### 1.1 Create VPC and Security Group

```bash
# Create VPC
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=betterprompts-dev}]' \
  --query 'Vpc.VpcId' --output text > vpc-id.txt

VPC_ID=$(cat vpc-id.txt)

# Enable DNS
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames

# Create subnet
aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=betterprompts-dev-subnet}]' \
  --query 'Subnet.SubnetId' --output text > subnet-id.txt

SUBNET_ID=$(cat subnet-id.txt)

# Create Internet Gateway
aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=betterprompts-dev-igw}]' \
  --query 'InternetGateway.InternetGatewayId' --output text > igw-id.txt

IGW_ID=$(cat igw-id.txt)

# Attach to VPC
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID

# Create route table
aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=betterprompts-dev-rt}]' \
  --query 'RouteTable.RouteTableId' --output text > rt-id.txt

RT_ID=$(cat rt-id.txt)

# Add route to internet
aws ec2 create-route --route-table-id $RT_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID

# Associate with subnet
aws ec2 associate-route-table --subnet-id $SUBNET_ID --route-table-id $RT_ID

# Create security group
aws ec2 create-security-group \
  --group-name betterprompts-dev \
  --description "BetterPrompts development" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text > sg-id.txt

SG_ID=$(cat sg-id.txt)

# Allow SSH and web traffic
aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 22 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 3000 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 3001 --cidr 0.0.0.0/0
```

### 1.2 Create RDS PostgreSQL

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name betterprompts-dev \
  --db-subnet-group-description "BetterPrompts dev subnet group" \
  --subnet-ids $SUBNET_ID

# Create RDS instance (with pgvector)
aws rds create-db-instance \
  --db-instance-identifier betterprompts-dev \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 16.2 \
  --master-username betterprompts \
  --master-user-password 'BetterPrompts2025!' \
  --allocated-storage 20 \
  --vpc-security-group-ids $SG_ID \
  --db-subnet-group-name betterprompts-dev \
  --backup-retention-period 0 \
  --no-multi-az \
  --publicly-accessible \
  --storage-encrypted

# Wait for creation (this takes ~5 minutes)
aws rds wait db-instance-available --db-instance-identifier betterprompts-dev

# Get endpoint
aws rds describe-db-instances \
  --db-instance-identifier betterprompts-dev \
  --query 'DBInstances[0].Endpoint.Address' --output text > rds-endpoint.txt

RDS_ENDPOINT=$(cat rds-endpoint.txt)
```

### 1.3 Create ElastiCache Redis

```bash
# Create cache subnet group
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name betterprompts-dev \
  --cache-subnet-group-description "BetterPrompts dev cache subnet" \
  --subnet-ids $SUBNET_ID

# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id betterprompts-dev \
  --engine redis \
  --engine-version 7.0 \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1 \
  --cache-subnet-group-name betterprompts-dev \
  --security-group-ids $SG_ID

# Wait for creation
aws elasticache wait cache-cluster-available --cache-cluster-id betterprompts-dev

# Get endpoint
aws elasticache describe-cache-clusters \
  --cache-cluster-id betterprompts-dev \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' --output text > redis-endpoint.txt

REDIS_ENDPOINT=$(cat redis-endpoint.txt)
```

### 1.4 Launch EC2 Instance

```bash
# Create key pair
aws ec2 create-key-pair \
  --key-name betterprompts-dev \
  --query 'KeyMaterial' --output text > betterprompts-dev.pem

chmod 600 betterprompts-dev.pem

# Launch EC2 (Ubuntu 22.04)
aws ec2 run-instances \
  --image-id ami-0866a3c8686eaeeba \
  --instance-type t3.xlarge \
  --key-name betterprompts-dev \
  --security-group-ids $SG_ID \
  --subnet-id $SUBNET_ID \
  --associate-public-ip-address \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=100,VolumeType=gp3}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=betterprompts-dev}]' \
  --user-data '#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose git
usermod -aG docker ubuntu
systemctl enable docker
systemctl start docker' \
  --query 'Instances[0].InstanceId' --output text > instance-id.txt

INSTANCE_ID=$(cat instance-id.txt)

# Wait for instance
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text > instance-ip.txt

INSTANCE_IP=$(cat instance-ip.txt)

echo "EC2 Instance IP: $INSTANCE_IP"
```

## Step 2: Deploy Application (30 minutes)

### 2.1 Connect and Setup

```bash
# SSH to instance
ssh -i betterprompts-dev.pem ubuntu@$INSTANCE_IP

# On the EC2 instance:
# Clone repository
git clone https://github.com/your-org/BetterPrompts.git
cd BetterPrompts

# Create .env file
cat > .env << EOF
# Database
DATABASE_URL=postgresql://betterprompts:BetterPrompts2025!@$RDS_ENDPOINT:5432/betterprompts

# Redis
REDIS_URL=redis://$REDIS_ENDPOINT:6379

# API Keys (copy from local)
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# JWT
JWT_SECRET=dev-jwt-secret-change-in-production

# Environment
NODE_ENV=development
ENVIRONMENT=development
EOF
```

### 2.2 Quick Fixes for AWS

```bash
# Update docker-compose.yml for AWS
cat > docker-compose.override.yml << 'EOF'
services:
  # Remove local postgres - using RDS
  postgres:
    deploy:
      replicas: 0

  # Remove local redis - using ElastiCache
  redis:
    deploy:
      replicas: 0

  # Update API URL for frontend
  frontend:
    environment:
      - NEXT_PUBLIC_API_URL=http://${INSTANCE_IP}/api/v1

  # Update all services to use AWS resources
  intent-classifier:
    environment:
      - DATABASE_URL=postgresql://betterprompts:BetterPrompts2025!@${RDS_ENDPOINT}:5432/betterprompts
      - REDIS_URL=redis://${REDIS_ENDPOINT}:6379/0

  technique-selector:
    environment:
      - DATABASE_URL=postgresql://betterprompts:BetterPrompts2025!@${RDS_ENDPOINT}:5432/betterprompts
      - REDIS_URL=redis://${REDIS_ENDPOINT}:6379/1

  prompt-generator:
    environment:
      - DATABASE_URL=postgresql://betterprompts:BetterPrompts2025!@${RDS_ENDPOINT}:5432/betterprompts
      - REDIS_URL=redis://${REDIS_ENDPOINT}:6379/2
EOF
```

### 2.3 Initialize Database

```bash
# Install PostgreSQL client
sudo apt-get update
sudo apt-get install -y postgresql-client

# Create database and extensions
PGPASSWORD='BetterPrompts2025!' psql -h $RDS_ENDPOINT -U betterprompts -d postgres << EOF
CREATE DATABASE betterprompts;
\c betterprompts
CREATE EXTENSION IF NOT EXISTS vector;
EOF

# Run migrations
PGPASSWORD='BetterPrompts2025!' psql -h $RDS_ENDPOINT -U betterprompts -d betterprompts < backend/migrations/up/001_initial_schema.sql
PGPASSWORD='BetterPrompts2025!' psql -h $RDS_ENDPOINT -U betterprompts -d betterprompts < backend/migrations/up/004_seed_data.sql
```

### 2.4 Launch Services

```bash
# Build and start
docker-compose build
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Step 3: Access and Test (5 minutes)

```bash
# From your local machine:
echo "Frontend: http://$INSTANCE_IP:3000"
echo "API Gateway: http://$INSTANCE_IP"
echo "Grafana: http://$INSTANCE_IP:3001"

# Test API
curl http://$INSTANCE_IP/health

# Test enhancement
curl -X POST http://$INSTANCE_IP/api/v1/enhance \
  -H "Content-Type: application/json" \
  -d '{"text": "explain quantum computing"}'
```

## Cost Breakdown (Monthly)

```
EC2 t3.xlarge:         ~$120
RDS db.t3.medium:      ~$60
ElastiCache t3.micro:  ~$15
Storage & Network:     ~$20
------------------------
Total:                 ~$215/month
```

## Faster Development Benefits

1. **No Docker build times** - Images cached on EC2
2. **Better network** - AWS internal networking
3. **Managed databases** - No container overhead
4. **Persistent storage** - Survives restarts
5. **Team access** - Multiple developers can connect

## Quick Commands Reference

```bash
# SSH to instance
ssh -i betterprompts-dev.pem ubuntu@$INSTANCE_IP

# Restart services
docker-compose restart

# Update code
git pull && docker-compose up -d --build

# View logs
docker-compose logs -f [service-name]

# Connect to RDS
PGPASSWORD='BetterPrompts2025!' psql -h $RDS_ENDPOINT -U betterprompts -d betterprompts

# Monitor Redis
redis-cli -h $REDIS_ENDPOINT
```

## Teardown (When Done)

```bash
# Save this for easy cleanup
cat > teardown.sh << 'EOF'
#!/bin/bash
# Terminate EC2
aws ec2 terminate-instances --instance-ids $(cat instance-id.txt)

# Delete RDS (after final snapshot)
aws rds delete-db-instance \
  --db-instance-identifier betterprompts-dev \
  --skip-final-snapshot

# Delete ElastiCache
aws elasticache delete-cache-cluster \
  --cache-cluster-id betterprompts-dev

# Wait for deletions
sleep 300

# Clean up networking
aws ec2 delete-security-group --group-id $(cat sg-id.txt)
aws ec2 delete-subnet --subnet-id $(cat subnet-id.txt)
aws ec2 detach-internet-gateway --vpc-id $(cat vpc-id.txt) --internet-gateway-id $(cat igw-id.txt)
aws ec2 delete-internet-gateway --internet-gateway-id $(cat igw-id.txt)
aws ec2 delete-route-table --route-table-id $(cat rt-id.txt)
aws ec2 delete-vpc --vpc-id $(cat vpc-id.txt)

# Delete key pair
aws ec2 delete-key-pair --key-name betterprompts-dev
rm -f betterprompts-dev.pem

echo "Cleanup complete!"
EOF

chmod +x teardown.sh
```

## Next Steps (Phase 1 - When Ready)

- Add Application Load Balancer
- Enable auto-scaling
- Set up CloudFront CDN
- Configure Route53 domain
- Add CloudWatch monitoring
- Implement backup strategies
- Set up CI/CD pipeline

## Troubleshooting

**Services can't connect to RDS/Redis:**
- Check security group rules
- Verify endpoints in .env file
- Test connectivity: `nc -zv $RDS_ENDPOINT 5432`

**Out of memory:**
- Upgrade to t3.2xlarge
- Enable swap: `sudo fallocate -l 4G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`

**Slow builds:**
- Pre-pull images: `docker-compose pull`
- Use ECR for custom images
- Enable BuildKit: `export DOCKER_BUILDKIT=1`

---

*This guide prioritizes speed over security and scalability. DO NOT use for production.*