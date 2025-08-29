#!/bin/bash
# One-click deployment script for BetterPrompts to AWS
# Phase 0 - Development environment only

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 BetterPrompts AWS Deployment - Phase 0${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI not found. Please install: brew install awscli${NC}"
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}AWS credentials not configured. Run: aws configure${NC}"
    exit 1
fi

# Step 1: Create AWS resources
if [ ! -f "instance-ip.txt" ]; then
    echo -e "\n${YELLOW}Step 1: Creating AWS resources...${NC}"
    ./scripts/aws-create-resources.sh
else
    echo -e "\n${YELLOW}AWS resources already exist. Skipping creation.${NC}"
fi

# Load resource IDs
INSTANCE_IP=$(cat instance-ip.txt)
RDS_ENDPOINT=$(cat rds-endpoint.txt)
REDIS_ENDPOINT=$(cat redis-endpoint.txt)

# Step 2: Wait for instance to be ready
echo -e "\n${YELLOW}Step 2: Waiting for EC2 to initialize...${NC}"
sleep 90

# Step 3: Prepare deployment files
echo -e "\n${YELLOW}Step 3: Preparing deployment files...${NC}"

# Create .env file
cat > .env.aws << EOF
# Database
DATABASE_URL=postgresql://betterprompts:BetterPrompts2025!@$RDS_ENDPOINT:5432/betterprompts

# Redis
REDIS_URL=redis://$REDIS_ENDPOINT:6379

# API Keys (update these!)
OPENAI_API_KEY=${OPENAI_API_KEY:-your-openai-key}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-your-anthropic-key}

# JWT
JWT_SECRET=dev-jwt-secret-change-in-production

# Environment
NODE_ENV=development
ENVIRONMENT=development

# URLs
NEXT_PUBLIC_API_URL=http://$INSTANCE_IP/api/v1
EOF

# Create docker-compose override
cat > docker-compose.aws.yml << EOF
services:
  # Remove local databases
  postgres:
    deploy:
      replicas: 0
  
  redis:
    deploy:
      replicas: 0

  # Update frontend URL
  frontend:
    environment:
      - NEXT_PUBLIC_API_URL=http://$INSTANCE_IP/api/v1

  # Update all services to use AWS resources
  intent-classifier:
    environment:
      - DATABASE_URL=postgresql://betterprompts:BetterPrompts2025!@$RDS_ENDPOINT:5432/betterprompts
      - REDIS_URL=redis://$REDIS_ENDPOINT:6379/0
    depends_on: []

  technique-selector:
    environment:
      - DATABASE_URL=postgresql://betterprompts:BetterPrompts2025!@$RDS_ENDPOINT:5432/betterprompts
      - REDIS_URL=redis://$REDIS_ENDPOINT:6379/1
    depends_on: []

  prompt-generator:
    environment:
      - DATABASE_URL=postgresql://betterprompts:BetterPrompts2025!@$RDS_ENDPOINT:5432/betterprompts
      - REDIS_URL=redis://$REDIS_ENDPOINT:6379/2
    depends_on:
      - technique-selector

  nginx:
    depends_on:
      - intent-classifier
      - technique-selector
      - prompt-generator
EOF

# Step 4: Deploy to EC2
echo -e "\n${YELLOW}Step 4: Deploying to EC2...${NC}"

# Test SSH connection
if ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i betterprompts-dev.pem ubuntu@$INSTANCE_IP "echo 'SSH OK'" &> /dev/null; then
    echo -e "${RED}Cannot connect to EC2. Waiting 30 more seconds...${NC}"
    sleep 30
fi

# Copy files and deploy
echo "Copying files to EC2..."
scp -o StrictHostKeyChecking=no -i betterprompts-dev.pem .env.aws ubuntu@$INSTANCE_IP:~/.env
scp -o StrictHostKeyChecking=no -i betterprompts-dev.pem docker-compose.aws.yml ubuntu@$INSTANCE_IP:~/

echo "Deploying application..."
ssh -o StrictHostKeyChecking=no -i betterprompts-dev.pem ubuntu@$INSTANCE_IP 'bash -s' << 'ENDSSH'
set -e

# Clone or update repository
if [ ! -d "BetterPrompts" ]; then
    git clone https://github.com/your-org/BetterPrompts.git
    cd BetterPrompts
else
    cd BetterPrompts
    git pull
fi

# Setup environment
cp ~/.env .env
cp ~/docker-compose.aws.yml docker-compose.override.yml

# Initialize database
echo "Initializing database..."
PGPASSWORD='BetterPrompts2025!' psql -h $(cat ~/rds-endpoint.txt) -U betterprompts -d postgres << EOF
CREATE DATABASE betterprompts;
EOF

# Run migrations
for migration in backend/migrations/up/*.sql; do
    echo "Running migration: $migration"
    PGPASSWORD='BetterPrompts2025!' psql -h $(cat ~/rds-endpoint.txt) -U betterprompts -d betterprompts < "$migration" || true
done

# Build and start services
echo "Building and starting services..."
docker compose build
docker compose up -d

# Wait for services
sleep 30

# Check status
docker compose ps
ENDSSH

# Step 5: Verify deployment
echo -e "\n${YELLOW}Step 5: Verifying deployment...${NC}"

# Test endpoints
if curl -s -f "http://$INSTANCE_IP/health" > /dev/null; then
    echo -e "${GREEN}✅ API Gateway is healthy${NC}"
else
    echo -e "${RED}❌ API Gateway health check failed${NC}"
fi

# Final summary
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "🌐 Frontend: http://$INSTANCE_IP:3000"
echo "🔌 API: http://$INSTANCE_IP/api/v1"
echo "📊 Grafana: http://$INSTANCE_IP:3001"
echo ""
echo "SSH Access: ssh -i betterprompts-dev.pem ubuntu@$INSTANCE_IP"
echo ""
echo -e "${YELLOW}⚠️  Remember to update API keys in .env.aws${NC}"
echo ""
echo "Next steps:"
echo "1. Test the application at http://$INSTANCE_IP:3000"
echo "2. View logs: ssh to instance and run 'docker compose logs -f'"
echo "3. When done, run: ./scripts/teardown-aws.sh"