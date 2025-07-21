#!/bin/bash

# BetterPrompts Health Check Script
# Checks the health status of all Docker services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check HTTP endpoint
check_http_endpoint() {
    local name=$1
    local url=$2
    # Follow redirects with -L flag and get final status code
    local response=$(curl -L -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓${NC} $name: Healthy"
        return 0
    else
        echo -e "${RED}✗${NC} $name: Unhealthy (HTTP $response)"
        return 1
    fi
}

# Function to check PostgreSQL
check_postgres() {
    if docker exec betterprompts-postgres pg_isready -U betterprompts >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} PostgreSQL: Healthy"
        return 0
    else
        echo -e "${RED}✗${NC} PostgreSQL: Unhealthy"
        return 1
    fi
}

# Function to check Redis
check_redis() {
    if docker exec betterprompts-redis redis-cli ping >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Redis: Healthy"
        return 0
    else
        echo -e "${RED}✗${NC} Redis: Unhealthy"
        return 1
    fi
}

# Function to check Docker container status
check_container_status() {
    echo -e "\n${YELLOW}Docker Container Status:${NC}"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Service}}"
}

# Main health check
echo "========================================"
echo "BetterPrompts Service Health Check"
echo "========================================"
echo "Time: $(date)"
echo ""

# Check if Docker Compose is running
if ! docker compose ps >/dev/null 2>&1; then
    echo -e "${RED}Error: Docker Compose is not running${NC}"
    exit 1
fi

# Check container status
check_container_status

# Check individual services
echo -e "\n${YELLOW}Service Health Checks:${NC}"
failed_checks=0

# Direct service endpoints
check_http_endpoint "Frontend" "http://localhost:3000/api/healthcheck" || ((failed_checks++))
check_http_endpoint "API Gateway (Nginx)" "http://localhost/health" || ((failed_checks++))
check_http_endpoint "Intent Classifier" "http://localhost:8001/health" || ((failed_checks++))
check_http_endpoint "Technique Selector" "http://localhost:8002/health" || ((failed_checks++))
check_http_endpoint "Prompt Generator" "http://localhost:8003/health" || ((failed_checks++))

# Via Gateway endpoints
echo -e "\n${YELLOW}Gateway Proxy Health Checks:${NC}"
check_http_endpoint "Intent Classifier (via Gateway)" "http://localhost/api/v1/intent/health" || ((failed_checks++))
check_http_endpoint "Technique Selector (via Gateway)" "http://localhost/api/v1/technique/health" || ((failed_checks++))
check_http_endpoint "Prompt Generator (via Gateway)" "http://localhost/api/v1/prompt/health" || ((failed_checks++))

# Database and cache
echo -e "\n${YELLOW}Database and Cache:${NC}"
check_postgres || ((failed_checks++))
check_redis || ((failed_checks++))

# Monitoring
echo -e "\n${YELLOW}Monitoring Services:${NC}"
check_http_endpoint "Prometheus" "http://localhost:9090/-/healthy" || ((failed_checks++))
check_http_endpoint "Grafana" "http://localhost:3001/api/health" || ((failed_checks++))

# Summary
echo ""
echo "========================================"
if [ $failed_checks -eq 0 ]; then
    echo -e "${GREEN}All services are healthy!${NC}"
    exit 0
else
    echo -e "${RED}$failed_checks service(s) are unhealthy${NC}"
    
    # Provide troubleshooting tips
    echo -e "\n${YELLOW}Troubleshooting tips:${NC}"
    echo "1. Check logs: docker compose logs [service-name]"
    echo "2. Restart unhealthy services: docker compose restart [service-name]"
    echo "3. Check service configuration in docker-compose.yml"
    echo "4. Ensure all required environment variables are set"
    
    # Specific service tips
    echo -e "\n${YELLOW}Service-specific checks:${NC}"
    echo "- Frontend: Check if Next.js build completed successfully"
    echo "- Python services: Check if dependencies installed correctly"
    echo "- Nginx: Check upstream service availability"
    echo "- Databases: Check connection strings and credentials"
    exit 1
fi