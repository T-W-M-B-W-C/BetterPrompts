#!/bin/bash
# Run tests for a specific service

set -e

# Check if service name is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <service-name>"
    echo "Available services: api-gateway, intent-classifier, technique-selector, prompt-generator, frontend"
    exit 1
fi

SERVICE=$1
COVERAGE_DIR="${COVERAGE_DIR:-/app/coverage}"
RESULTS_DIR="${RESULTS_DIR:-/app/test-results}"

# Create directories
mkdir -p "$COVERAGE_DIR" "$RESULTS_DIR"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🧪 Running tests for $SERVICE..."

case $SERVICE in
    "api-gateway"|"technique-selector")
        cd "/app/backend/services/$SERVICE"
        echo "Running Go tests..."
        go test -v -race -coverprofile="$COVERAGE_DIR/${SERVICE}.coverage" ./... \
            | tee "$RESULTS_DIR/${SERVICE}-results.txt"
        ;;
    
    "intent-classifier"|"prompt-generator")
        cd "/app/backend/services/$SERVICE"
        echo "Running Python tests..."
        python -m pytest tests/ \
            -v \
            --cov=app \
            --cov-report=xml:"$COVERAGE_DIR/${SERVICE}.xml" \
            --cov-report=term \
            --junit-xml="$RESULTS_DIR/${SERVICE}-results.xml"
        ;;
    
    "frontend")
        cd "/app/frontend"
        echo "Running Node.js tests..."
        npm test -- \
            --coverage \
            --coverageDirectory="$COVERAGE_DIR/${SERVICE}" \
            --testResultsProcessor="jest-junit"
        ;;
    
    "ml-pipeline")
        cd "/app/ml-pipeline"
        echo "Running ML pipeline tests..."
        python -m pytest tests/ \
            -v \
            --cov=. \
            --cov-report=xml:"$COVERAGE_DIR/${SERVICE}.xml" \
            --junit-xml="$RESULTS_DIR/${SERVICE}-results.xml"
        ;;
    
    *)
        echo -e "${RED}Unknown service: $SERVICE${NC}"
        exit 1
        ;;
esac

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✅ $SERVICE tests passed!${NC}"
else
    echo -e "\n${RED}❌ $SERVICE tests failed!${NC}"
fi

# Show coverage summary
echo -e "\n📊 Coverage Summary for $SERVICE:"
if [ -f "$COVERAGE_DIR/${SERVICE}.coverage" ]; then
    go tool cover -func="$COVERAGE_DIR/${SERVICE}.coverage" | tail -1
elif [ -f "$COVERAGE_DIR/${SERVICE}.xml" ]; then
    grep -oP 'line-rate="\K[^"]+' "$COVERAGE_DIR/${SERVICE}.xml" | head -1 | awk '{printf "Total coverage: %.1f%%\n", $1 * 100}'
fi

exit $EXIT_CODE