#!/bin/bash
# Validate test infrastructure setup

set -e

echo "🔍 Validating BetterPrompts Test Infrastructure"
echo "=============================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 - Missing"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
        return 0
    else
        echo -e "${RED}✗${NC} $1/ - Missing"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check Docker image
check_image() {
    if docker image inspect "$1" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Docker image: $1"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} Docker image not built: $1"
        WARNINGS=$((WARNINGS + 1))
        return 1
    fi
}

echo -e "\n📁 Checking directory structure..."
check_dir "tests"
check_dir "tests/mocks"
check_dir "tests/mocks/torchserve"
check_dir "tests/mocks/wiremock"
check_dir "tests/e2e"
check_dir "tests/performance"
check_dir "tests/scripts"

echo -e "\n📄 Checking essential files..."
check_file "docker-compose.test.yml"
check_file "tests/Dockerfile.testrunner"
check_file "tests/mocks/torchserve/Dockerfile"
check_file "tests/mocks/torchserve/mock_server.py"
check_file "tests/scripts/run-all-tests.sh"
check_file "tests/scripts/wait-for-services.sh"
check_file "tests/scripts/test-service.sh"
check_file "tests/scripts/coverage-report.sh"
check_file ".github/workflows/test-suite.yml"

echo -e "\n🔧 Checking script permissions..."
for script in tests/scripts/*.sh scripts/*.sh; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo -e "${GREEN}✓${NC} $script is executable"
        else
            echo -e "${RED}✗${NC} $script is not executable"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

echo -e "\n🐳 Checking Docker..."
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker is installed"
    docker version --format "   Version: {{.Server.Version}}" 2>/dev/null || echo "   Unable to get version"
else
    echo -e "${RED}✗${NC} Docker is not installed"
    ERRORS=$((ERRORS + 1))
fi

if command -v docker compose &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose is installed"
else
    echo -e "${RED}✗${NC} Docker Compose is not installed"
    ERRORS=$((ERRORS + 1))
fi

echo -e "\n🏗️  Validating Docker Compose configuration..."
if docker compose -f docker-compose.test.yml config > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} docker-compose.test.yml is valid"
else
    echo -e "${RED}✗${NC} docker-compose.test.yml has errors"
    ERRORS=$((ERRORS + 1))
fi

echo -e "\n🖼️  Checking Docker images..."
check_image "betterprompts-test-runner"
check_image "betterprompts-mock-torchserve"

echo -e "\n🔌 Checking port availability..."
PORTS=(5433 6380 8081 8082 8083 8084 8085 8086)
for port in "${PORTS[@]}"; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠${NC} Port $port is in use"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}✓${NC} Port $port is available"
    fi
done

echo -e "\n📊 Summary"
echo "=========="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo "Test infrastructure is ready to use."
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Validation completed with $WARNINGS warnings${NC}"
    echo "Test infrastructure should work but some optional components may be missing."
else
    echo -e "${RED}❌ Validation failed with $ERRORS errors and $WARNINGS warnings${NC}"
    echo "Please fix the errors before running tests."
fi

echo -e "\n📚 Next steps:"
if [ $ERRORS -eq 0 ]; then
    echo "1. Run: docker compose -f docker-compose.test.yml build"
    echo "2. Run: docker compose -f docker-compose.test.yml up"
    echo "3. Or use: make -f Makefile.test test"
else
    echo "1. Fix the errors listed above"
    echo "2. Run: ./scripts/setup-test-env.sh"
    echo "3. Run this validation again"
fi

exit $ERRORS