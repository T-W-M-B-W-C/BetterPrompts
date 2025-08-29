#!/bin/bash

# BetterPrompts Comprehensive Test Suite Runner
# This script runs all available tests for the prompt classification system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧪 BetterPrompts Test Suite Runner"
echo "=================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run tests and report results
run_test_suite() {
    local suite_name=$1
    local test_command=$2
    
    echo -e "${YELLOW}Running $suite_name...${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ $suite_name passed${NC}"
        return 0
    else
        echo -e "${RED}❌ $suite_name failed${NC}"
        return 1
    fi
}

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

# 1. Start services if not running
echo "🚀 Starting services..."
cd "$PROJECT_ROOT"
docker compose up -d --build
echo "Waiting for services to be ready..."
sleep 10

# 2. Run Go unit tests for API Gateway
echo ""
echo "📦 Running API Gateway tests..."
if docker compose exec -T api-gateway go test ./... -v; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# 3. Run Python unit tests for Intent Classifier
echo ""
echo "🧠 Running Intent Classifier tests..."
if docker compose exec -T intent-classifier python -m pytest tests/ -v; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# 4. Run Python unit tests for Prompt Generator
echo ""
echo "✨ Running Prompt Generator tests..."
if docker compose exec -T prompt-generator python -m pytest tests/ -v; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# 5. Run Go unit tests for Technique Selector
echo ""
echo "🎯 Running Technique Selector tests..."
if docker compose exec -T technique-selector go test ./... -v; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# 6. Install and run Playwright E2E tests
echo ""
echo "🎭 Setting up Playwright tests..."
cd "$PROJECT_ROOT/tests/e2e"
if [ ! -d "node_modules" ]; then
    npm install
fi

echo "Running E2E tests..."
if npx playwright test; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# 7. Generate test report
echo ""
echo "📊 Test Summary"
echo "==============="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

# 8. Coverage report (if available)
echo ""
echo "📈 Coverage Reports"
echo "==================="

# Go coverage
echo "API Gateway coverage:"
docker compose exec -T api-gateway go test ./... -cover || true

echo ""
echo "Technique Selector coverage:"
docker compose exec -T technique-selector go test ./... -cover || true

# Python coverage
echo ""
echo "Intent Classifier coverage:"
docker compose exec -T intent-classifier python -m pytest tests/ --cov=app --cov-report=term-missing || true

echo ""
echo "Prompt Generator coverage:"
docker compose exec -T prompt-generator python -m pytest tests/ --cov=app --cov-report=term-missing || true

# 9. Show Playwright report
echo ""
echo "🎭 Playwright Report"
echo "===================="
echo "To view the Playwright HTML report, run:"
echo "  cd tests/e2e && npx playwright show-report"

# Exit with appropriate code
if [ $TESTS_FAILED -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ Test suite failed with $TESTS_FAILED failures${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
fi