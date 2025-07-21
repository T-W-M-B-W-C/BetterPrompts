#!/bin/bash
# Teardown script for BetterPrompts AWS Phase 0
# Deletes all AWS resources created for development

set -e

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}⚠️  AWS Resource Teardown${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "This will DELETE all AWS resources for BetterPrompts"
echo ""

# Confirm
read -p "Are you sure? Type 'DELETE' to confirm: " confirm
if [ "$confirm" != "DELETE" ]; then
    echo "Teardown cancelled."
    exit 0
fi

echo -e "\n${YELLOW}Starting teardown...${NC}"

# Load resource IDs
if [ ! -f "instance-id.txt" ]; then
    echo -e "${RED}No resource files found. Nothing to delete.${NC}"
    exit 0
fi

INSTANCE_ID=$(cat instance-id.txt 2>/dev/null || echo "")
VPC_ID=$(cat vpc-id.txt 2>/dev/null || echo "")
SUBNET_ID=$(cat subnet-id.txt 2>/dev/null || echo "")
SUBNET_ID_2=$(cat subnet-id-2.txt 2>/dev/null || echo "")
SG_ID=$(cat sg-id.txt 2>/dev/null || echo "")
IGW_ID=$(cat igw-id.txt 2>/dev/null || echo "")
RT_ID=$(cat rt-id.txt 2>/dev/null || echo "")

# Step 1: Terminate EC2 instance
if [ -n "$INSTANCE_ID" ]; then
    echo "Terminating EC2 instance..."
    aws ec2 terminate-instances --instance-ids $INSTANCE_ID || true
fi

# Step 2: Delete RDS instance
echo "Deleting RDS instance (this may take a few minutes)..."
aws rds delete-db-instance \
    --db-instance-identifier betterprompts-dev \
    --skip-final-snapshot \
    --delete-automated-backups || true

# Step 3: Delete ElastiCache cluster
echo "Deleting ElastiCache Redis..."
aws elasticache delete-cache-cluster \
    --cache-cluster-id betterprompts-dev || true

# Wait for resources to delete
echo -e "\n${YELLOW}Waiting for resources to be deleted (this takes 3-5 minutes)...${NC}"

# Wait for EC2 termination
if [ -n "$INSTANCE_ID" ]; then
    echo "Waiting for EC2 to terminate..."
    aws ec2 wait instance-terminated --instance-ids $INSTANCE_ID || true
fi

# Wait for RDS deletion (with timeout)
echo "Waiting for RDS to delete..."
timeout 300 aws rds wait db-instance-deleted --db-instance-identifier betterprompts-dev || true

# Wait for ElastiCache deletion
echo "Waiting for Redis to delete..."
for i in {1..30}; do
    if ! aws elasticache describe-cache-clusters --cache-cluster-id betterprompts-dev &>/dev/null; then
        break
    fi
    sleep 10
done

# Step 4: Delete DB subnet group
echo "Deleting DB subnet group..."
aws rds delete-db-subnet-group --db-subnet-group-name betterprompts-dev || true

# Step 5: Delete cache subnet group
echo "Deleting cache subnet group..."
aws elasticache delete-cache-subnet-group --cache-subnet-group-name betterprompts-dev || true

# Step 6: Delete security group
if [ -n "$SG_ID" ]; then
    echo "Deleting security group..."
    # Wait a bit for ENIs to detach
    sleep 30
    aws ec2 delete-security-group --group-id $SG_ID || true
fi

# Step 7: Delete networking resources
if [ -n "$SUBNET_ID" ]; then
    echo "Deleting subnets..."
    aws ec2 delete-subnet --subnet-id $SUBNET_ID || true
fi

if [ -n "$SUBNET_ID_2" ]; then
    aws ec2 delete-subnet --subnet-id $SUBNET_ID_2 || true
fi

if [ -n "$IGW_ID" ] && [ -n "$VPC_ID" ]; then
    echo "Detaching and deleting internet gateway..."
    aws ec2 detach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID || true
    aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID || true
fi

if [ -n "$RT_ID" ]; then
    echo "Deleting route table..."
    aws ec2 delete-route-table --route-table-id $RT_ID || true
fi

if [ -n "$VPC_ID" ]; then
    echo "Deleting VPC..."
    # Final wait for everything to clear
    sleep 30
    aws ec2 delete-vpc --vpc-id $VPC_ID || true
fi

# Step 8: Delete key pair
echo "Deleting SSH key pair..."
aws ec2 delete-key-pair --key-name betterprompts-dev || true

# Step 9: Clean up local files
echo "Cleaning up local files..."
rm -f vpc-id.txt subnet-id.txt subnet-id-2.txt sg-id.txt igw-id.txt rt-id.txt
rm -f instance-id.txt instance-ip.txt
rm -f rds-endpoint.txt redis-endpoint.txt
rm -f betterprompts-dev.pem
rm -f .env.aws docker-compose.aws.yml

echo -e "\n${GREEN}✅ Teardown complete!${NC}"
echo "All AWS resources have been deleted."
echo ""
echo "Estimated savings: ~$7/day"