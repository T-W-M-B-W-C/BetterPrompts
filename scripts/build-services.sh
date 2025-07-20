#!/bin/bash

# Build services script for BetterPrompts
# This script builds services incrementally to identify and fix issues

set -e

echo "🔨 Building BetterPrompts services..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to build a service
build_service() {
    local service=$1
    echo -e "${YELLOW}Building $service...${NC}"
    
    if docker compose build $service 2>&1 | tee build-$service.log; then
        echo -e "${GREEN}✅ $service built successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ $service build failed${NC}"
        return 1
    fi
}

# Create logs directory
mkdir -p logs

# Build services one by one
services=(
    "nginx"
    "postgres"
    "redis"
    "technique-selector"
    "api-gateway"
    "frontend"
    "intent-classifier"
    "prompt-generator"
)

successful=()
failed=()

for service in "${services[@]}"; do
    if build_service $service; then
        successful+=($service)
    else
        failed+=($service)
    fi
    echo ""
done

# Summary
echo "🎯 Build Summary:"
echo -e "${GREEN}Successful builds (${#successful[@]}):${NC}"
for s in "${successful[@]}"; do
    echo "  ✅ $s"
done

if [ ${#failed[@]} -gt 0 ]; then
    echo -e "${RED}Failed builds (${#failed[@]}):${NC}"
    for f in "${failed[@]}"; do
        echo "  ❌ $f"
    done
fi

# Next steps
echo ""
echo "📋 Next Steps:"
if [ ${#failed[@]} -gt 0 ]; then
    echo "1. Check the build logs for failed services:"
    for f in "${failed[@]}"; do
        echo "   cat build-$f.log"
    done
    echo "2. Fix the issues and run this script again"
else
    echo "1. All services built successfully!"
    echo "2. Run 'docker compose up -d' to start the services"
    echo "3. Check service health with 'docker compose ps'"
fi