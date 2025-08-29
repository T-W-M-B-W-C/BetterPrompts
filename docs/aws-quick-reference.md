# AWS Phase 0 Quick Reference Card

## 🚀 2-Hour AWS Setup

### Prerequisites
```bash
aws configure  # Set up AWS credentials
```

### One-Click Deploy Script
```bash
# Save as deploy-aws.sh
#!/bin/bash
set -e

echo "🚀 Deploying BetterPrompts to AWS..."

# 1. Create all AWS resources
./scripts/aws-create-resources.sh

# 2. Get connection info
INSTANCE_IP=$(cat instance-ip.txt)
RDS_ENDPOINT=$(cat rds-endpoint.txt)
REDIS_ENDPOINT=$(cat redis-endpoint.txt)

# 3. Wait for instance to be ready
sleep 60

# 4. Deploy application
scp -i betterprompts-dev.pem .env ubuntu@$INSTANCE_IP:~/
ssh -i betterprompts-dev.pem ubuntu@$INSTANCE_IP 'bash -s' << 'ENDSSH'
  git clone https://github.com/your-org/BetterPrompts.git
  cd BetterPrompts
  cp ~/.env .
  docker-compose up -d
ENDSSH

echo "✅ Deployment complete!"
echo "Frontend: http://$INSTANCE_IP:3000"
echo "API: http://$INSTANCE_IP"
```

## Essential Commands

### Connect to AWS Instance
```bash
ssh -i betterprompts-dev.pem ubuntu@$(cat instance-ip.txt)
```

### Update Application
```bash
# On EC2 instance
cd BetterPrompts
git pull
docker-compose up -d --build
```

### View Logs
```bash
docker-compose logs -f frontend
docker-compose logs -f prompt-generator
```

### Database Access
```bash
PGPASSWORD='BetterPrompts2025!' psql \
  -h $(cat rds-endpoint.txt) \
  -U betterprompts -d betterprompts
```

### Quick Restart
```bash
docker-compose restart
```

### Emergency Stop
```bash
docker-compose down
```

## URLs
- Frontend: `http://[EC2-IP]:3000`
- API: `http://[EC2-IP]/api/v1`
- Grafana: `http://[EC2-IP]:3001`

## Costs
- **Daily**: ~$7
- **Weekly**: ~$50
- **Monthly**: ~$215

## Cleanup
```bash
./teardown.sh  # Deletes everything
```