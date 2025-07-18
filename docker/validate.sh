#!/bin/bash

# Docker Configuration Validation Script
set -e

echo "🔍 Validating Docker configurations..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validation results
ERRORS=0
WARNINGS=0

# Function to check if file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} Found: $1"
    else
        echo -e "${RED}✗${NC} Missing: $1"
        ((ERRORS++))
    fi
}

# Function to validate Dockerfile
validate_dockerfile() {
    echo -e "\n📋 Validating: $1"
    
    if [ -f "$1" ]; then
        # Check for required elements
        if grep -q "FROM" "$1"; then
            echo -e "${GREEN}✓${NC} Has FROM instruction"
        else
            echo -e "${RED}✗${NC} Missing FROM instruction"
            ((ERRORS++))
        fi
        
        if grep -q "HEALTHCHECK" "$1"; then
            echo -e "${GREEN}✓${NC} Has HEALTHCHECK"
        else
            echo -e "${YELLOW}⚠${NC} Missing HEALTHCHECK (recommended)"
            ((WARNINGS++))
        fi
        
        if grep -q "USER" "$1"; then
            echo -e "${GREEN}✓${NC} Runs as non-root user"
        else
            echo -e "${YELLOW}⚠${NC} No USER instruction (runs as root)"
            ((WARNINGS++))
        fi
        
        # Lint with hadolint if available
        if command -v hadolint &> /dev/null; then
            echo "Running hadolint..."
            hadolint "$1" || echo -e "${YELLOW}⚠${NC} Hadolint found issues"
        fi
    fi
}

# Function to validate docker-compose file
validate_compose() {
    echo -e "\n📋 Validating: $1"
    
    if [ -f "$1" ]; then
        # Check syntax
        docker compose -f "$1" config > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} Valid syntax"
        else
            echo -e "${RED}✗${NC} Invalid syntax"
            ((ERRORS++))
            return
        fi
        
        # Check for required services
        services=$(docker compose -f "$1" config --services)
        required_services=("frontend" "intent-classifier" "technique-selector" "prompt-generator" "nginx" "postgres" "redis")
        
        for service in "${required_services[@]}"; do
            if echo "$services" | grep -q "^$service$"; then
                echo -e "${GREEN}✓${NC} Service defined: $service"
            else
                echo -e "${RED}✗${NC} Missing service: $service"
                ((ERRORS++))
            fi
        done
    fi
}

echo "🏗️  Checking Docker configuration structure..."

# Check directory structure
check_file "docker/frontend/Dockerfile"
check_file "docker/frontend/.dockerignore"
check_file "docker/backend/intent-classifier/Dockerfile"
check_file "docker/backend/intent-classifier/.dockerignore"
check_file "docker/backend/technique-selector/Dockerfile"
check_file "docker/backend/technique-selector/.dockerignore"
check_file "docker/backend/prompt-generator/Dockerfile"
check_file "docker/backend/prompt-generator/.dockerignore"
check_file "docker/nginx/Dockerfile"
check_file "docker/nginx/nginx.conf"
check_file "docker/nginx/conf.d/api.conf"
check_file "docker-compose.yml"
check_file "docker-compose.prod.yml"
check_file ".env.example"

echo -e "\n🐳 Validating Dockerfiles..."

# Validate each Dockerfile
validate_dockerfile "docker/frontend/Dockerfile"
validate_dockerfile "docker/backend/intent-classifier/Dockerfile"
validate_dockerfile "docker/backend/technique-selector/Dockerfile"
validate_dockerfile "docker/backend/prompt-generator/Dockerfile"
validate_dockerfile "docker/nginx/Dockerfile"

echo -e "\n🔧 Validating Docker Compose files..."

# Validate docker-compose files
validate_compose "docker-compose.yml"
validate_compose "docker-compose.prod.yml"

echo -e "\n📊 Validation Summary:"
echo -e "Errors: ${ERRORS}"
echo -e "Warnings: ${WARNINGS}"

if [ $ERRORS -eq 0 ]; then
    echo -e "\n${GREEN}✅ All Docker configurations are valid!${NC}"
    
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  There are $WARNINGS warnings to review.${NC}"
    fi
    
    echo -e "\n📝 Next steps:"
    echo "1. Copy .env.example to .env and configure your environment variables"
    echo "2. Build the images: docker compose build"
    echo "3. Start the services: docker compose up -d"
    echo "4. Check service health: docker compose ps"
    
    exit 0
else
    echo -e "\n${RED}❌ Found $ERRORS errors that need to be fixed.${NC}"
    exit 1
fi