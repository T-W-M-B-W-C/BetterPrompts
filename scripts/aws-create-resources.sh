#!/bin/bash
# AWS Resource Creation Script for BetterPrompts Phase 0
# Creates minimal AWS infrastructure for development

set -e

echo "🚀 Creating AWS resources for BetterPrompts development..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Region (change if needed)
REGION=${AWS_REGION:-us-east-1}
AZ="${REGION}a"

echo -e "${YELLOW}Using region: $REGION${NC}"

# Create VPC
echo "Creating VPC..."
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=betterprompts-dev}]' \
  --query 'Vpc.VpcId' --output text)
echo $VPC_ID > vpc-id.txt

# Enable DNS
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames

# Create subnet
echo "Creating subnet..."
SUBNET_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone $AZ \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=betterprompts-dev-subnet}]' \
  --query 'Subnet.SubnetId' --output text)
echo $SUBNET_ID > subnet-id.txt

# Create second subnet for RDS (required)
SUBNET_ID_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone ${REGION}b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=betterprompts-dev-subnet-2}]' \
  --query 'Subnet.SubnetId' --output text)
echo $SUBNET_ID_2 > subnet-id-2.txt

# Create Internet Gateway
echo "Creating Internet Gateway..."
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=betterprompts-dev-igw}]' \
  --query 'InternetGateway.InternetGatewayId' --output text)
echo $IGW_ID > igw-id.txt

aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID

# Create route table
echo "Setting up routing..."
RT_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=betterprompts-dev-rt}]' \
  --query 'RouteTable.RouteTableId' --output text)
echo $RT_ID > rt-id.txt

aws ec2 create-route --route-table-id $RT_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
aws ec2 associate-route-table --subnet-id $SUBNET_ID --route-table-id $RT_ID
aws ec2 associate-route-table --subnet-id $SUBNET_ID_2 --route-table-id $RT_ID

# Create security group
echo "Creating security group..."
SG_ID=$(aws ec2 create-security-group \
  --group-name betterprompts-dev \
  --description "BetterPrompts development" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)
echo $SG_ID > sg-id.txt

# Configure security group
echo "Configuring security rules..."
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 3000 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 3001 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 5432 --source-group $SG_ID
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 6379 --source-group $SG_ID

# Create key pair
echo "Creating SSH key..."
aws ec2 create-key-pair \
  --key-name betterprompts-dev \
  --query 'KeyMaterial' --output text > betterprompts-dev.pem
chmod 600 betterprompts-dev.pem

# Create DB subnet group
echo "Creating RDS subnet group..."
aws rds create-db-subnet-group \
  --db-subnet-group-name betterprompts-dev \
  --db-subnet-group-description "BetterPrompts dev subnet group" \
  --subnet-ids $SUBNET_ID $SUBNET_ID_2 || true

# Create RDS instance
echo "Creating RDS PostgreSQL (this takes ~5 minutes)..."
aws rds create-db-instance \
  --db-instance-identifier betterprompts-dev \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 16 \
  --master-username betterprompts \
  --master-user-password 'BetterPrompts2025!' \
  --allocated-storage 20 \
  --vpc-security-group-ids $SG_ID \
  --db-subnet-group-name betterprompts-dev \
  --backup-retention-period 0 \
  --no-multi-az \
  --publicly-accessible \
  --storage-encrypted || echo "RDS might already exist"

# Create cache subnet group
echo "Creating ElastiCache subnet group..."
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name betterprompts-dev \
  --cache-subnet-group-description "BetterPrompts dev cache subnet" \
  --subnet-ids $SUBNET_ID $SUBNET_ID_2 || true

# Create Redis cluster
echo "Creating ElastiCache Redis..."
aws elasticache create-cache-cluster \
  --cache-cluster-id betterprompts-dev \
  --engine redis \
  --engine-version 7.0 \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1 \
  --cache-subnet-group-name betterprompts-dev \
  --security-group-ids $SG_ID || echo "Redis might already exist"

# Launch EC2
echo "Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
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
apt-get install -y docker.io docker-compose-v2 git postgresql-client
usermod -aG docker ubuntu
systemctl enable docker
systemctl start docker
# Install docker compose v2
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
ln -s /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose' \
  --query 'Instances[0].InstanceId' --output text)
echo $INSTANCE_ID > instance-id.txt

echo "Waiting for instances to be ready..."

# Wait for RDS
echo "Waiting for RDS..."
aws rds wait db-instance-available --db-instance-identifier betterprompts-dev

# Get RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier betterprompts-dev \
  --query 'DBInstances[0].Endpoint.Address' --output text)
echo $RDS_ENDPOINT > rds-endpoint.txt

# Wait for ElastiCache
echo "Waiting for Redis..."
aws elasticache wait cache-cluster-available --cache-cluster-id betterprompts-dev

# Get Redis endpoint
REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
  --cache-cluster-id betterprompts-dev \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' --output text)
echo $REDIS_ENDPOINT > redis-endpoint.txt

# Wait for EC2
echo "Waiting for EC2..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
INSTANCE_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo $INSTANCE_IP > instance-ip.txt

# Create summary
echo -e "\n${GREEN}✅ AWS Resources Created Successfully!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "EC2 Instance: $INSTANCE_IP"
echo "RDS Endpoint: $RDS_ENDPOINT"
echo "Redis Endpoint: $REDIS_ENDPOINT"
echo "SSH Key: betterprompts-dev.pem"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "1. Wait ~2 minutes for EC2 to fully initialize"
echo "2. SSH to instance: ssh -i betterprompts-dev.pem ubuntu@$INSTANCE_IP"
echo "3. Deploy application using instructions in docs/aws-migration-phase0.md"
echo ""
echo "Files created:"
echo "- vpc-id.txt, subnet-id.txt, sg-id.txt"
echo "- instance-id.txt, instance-ip.txt"
echo "- rds-endpoint.txt, redis-endpoint.txt"
echo "- betterprompts-dev.pem (SSH key)"