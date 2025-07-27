#!/bin/bash

# Teardown script for E2E test environment

echo "🧹 Tearing down E2E test environment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}📍 Working from: $PROJECT_ROOT${NC}"

# Stop Docker services
echo -e "${YELLOW}🐳 Stopping Docker services...${NC}"
docker compose -f docker-compose.e2e.yml down

# Remove volumes if requested
if [ "$1" == "--volumes" ] || [ "$1" == "-v" ]; then
    echo -e "${YELLOW}🗑️ Removing Docker volumes...${NC}"
    docker compose -f docker-compose.e2e.yml down -v
fi

# Clean up test results
if [ -d "e2e/phase2/test-results" ]; then
    echo -e "${YELLOW}📁 Cleaning up test results...${NC}"
    rm -rf e2e/phase2/test-results
fi

# Clean up playwright downloads if requested
if [ "$1" == "--clean-all" ]; then
    echo -e "${YELLOW}🎭 Cleaning up Playwright downloads...${NC}"
    cd e2e/frontend
    npx playwright clean-deps
    cd "$PROJECT_ROOT"
fi

echo -e "${GREEN}✅ E2E test environment teardown complete!${NC}"

if [ "$1" != "--volumes" ] && [ "$1" != "-v" ]; then
    echo ""
    echo "Note: Database volumes were preserved."
    echo "To remove volumes as well, run: $0 --volumes"
fi