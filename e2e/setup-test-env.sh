#!/bin/bash

# Setup script for E2E test environment

echo "🔧 Setting up E2E test environment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Docker
if ! command_exists docker; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check for Docker Compose
if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check for Node.js
if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js first.${NC}"
    exit 1
fi

# Navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}📍 Working from: $PROJECT_ROOT${NC}"

# Install test-helpers dependencies
echo -e "${YELLOW}📦 Installing test-helpers dependencies...${NC}"
cd e2e/test-helpers
npm install
cd "$PROJECT_ROOT"

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    cd frontend
    npm install
    cd "$PROJECT_ROOT"
fi

# Start Docker services
echo -e "${YELLOW}🐳 Starting E2E Docker services...${NC}"
docker compose -f docker-compose.e2e.yml up -d

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"

# Function to check if a service is ready
wait_for_service() {
    local service_name=$1
    local check_command=$2
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if eval "$check_command" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service_name failed to start${NC}"
    return 1
}

# Wait for PostgreSQL
wait_for_service "PostgreSQL" "docker exec betterprompts-postgres-e2e pg_isready -U betterprompts"

# Wait for MailHog
wait_for_service "MailHog" "curl -s http://localhost:8025/api/v2/messages"

# Wait for API Gateway
wait_for_service "API Gateway" "curl -s http://localhost/api/v1/health"

# Wait for Frontend
wait_for_service "Frontend" "curl -s http://localhost"

echo -e "${GREEN}✅ E2E test environment is ready!${NC}"
echo ""
echo "Services running:"
echo "  - Frontend: http://localhost"
echo "  - API Gateway: http://localhost/api/v1"
echo "  - MailHog UI: http://localhost:8025"
echo "  - PostgreSQL: localhost:5433"
echo ""
echo "To run tests:"
echo "  cd e2e/frontend && npm test"
echo ""
echo "To stop services:"
echo "  docker compose -f docker-compose.e2e.yml down"