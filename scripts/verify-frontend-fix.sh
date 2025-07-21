#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔍 Verifying Frontend Health Check Fix${NC}"
echo "======================================="

# Check if entrypoint script exists and is executable
if [ -f "docker/frontend/entrypoint.sh" ] && [ -x "docker/frontend/entrypoint.sh" ]; then
    echo -e "${GREEN}✅ Entrypoint script exists and is executable${NC}"
else
    echo -e "${RED}❌ Entrypoint script missing or not executable${NC}"
    exit 1
fi

# Check docker-compose.yml changes
if grep -q "entrypoint.*entrypoint.sh" docker-compose.yml; then
    echo -e "${GREEN}✅ Docker-compose using entrypoint script${NC}"
else
    echo -e "${RED}❌ Docker-compose not updated correctly${NC}"
    exit 1
fi

# Check health check configuration
if grep -q "node.*healthcheck.js" docker-compose.yml; then
    echo -e "${GREEN}✅ Health check using Node.js script${NC}"
else
    echo -e "${RED}❌ Health check configuration incorrect${NC}"
    exit 1
fi

# Check start_period in health check
if grep -A5 "healthcheck:" docker-compose.yml | grep -q "start_period"; then
    echo -e "${GREEN}✅ Health check has start_period configured${NC}"
else
    echo -e "${RED}❌ Health check missing start_period${NC}"
    exit 1
fi

echo -e "\n${GREEN}🎉 All checks passed! The frontend health check issue should be resolved.${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Stop any running containers: docker compose down"
echo "2. Rebuild the frontend: docker compose build frontend"
echo "3. Start services: docker compose up -d"
echo "4. Check health status: docker compose ps"
echo "5. Monitor logs: docker compose logs -f frontend"