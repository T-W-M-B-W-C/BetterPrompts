#!/bin/bash
# Run all tests across all services with coverage reporting

set -e

echo "🧪 BetterPrompts Test Suite Runner"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COVERAGE_DIR="/app/coverage"
RESULTS_DIR="/app/test-results"
PARALLEL_TESTS="${PARALLEL_TESTS:-true}"
TEST_TIMEOUT="${TEST_TIMEOUT:-30m}"

# Create directories
mkdir -p "$COVERAGE_DIR" "$RESULTS_DIR"

# Function to check service health
check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo -n "Waiting for $service..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e " ${RED}✗${NC}"
    return 1
}

# Wait for services to be ready
echo "Checking service health..."
check_service "PostgreSQL" "http://test-postgres:5432" || true
check_service "Redis" "http://test-redis:6379" || true
check_service "Mock TorchServe" "http://mock-torchserve:8080/ping" || true

# Run database migrations
echo -e "\n📦 Running database migrations..."
cd /app/backend/services/api-gateway
if [ -f "./scripts/migrate.sh" ]; then
    ./scripts/migrate.sh
fi

# Function to run tests for a service
run_service_tests() {
    local service=$1
    local type=$2
    local path=$3
    
    echo -e "\n🔧 Testing $service..."
    
    case $type in
        "go")
            cd "$path"
            go test -v -race -coverprofile="$COVERAGE_DIR/${service}.coverage" ./... \
                -timeout="$TEST_TIMEOUT" \
                | tee "$RESULTS_DIR/${service}-results.txt"
            ;;
        "python")
            cd "$path"
            python -m pytest tests/ \
                -v \
                --cov=app \
                --cov-report=xml:"$COVERAGE_DIR/${service}.xml" \
                --cov-report=term \
                --junit-xml="$RESULTS_DIR/${service}-results.xml" \
                --timeout=300
            ;;
        "node")
            cd "$path"
            npm test -- \
                --coverage \
                --coverageDirectory="$COVERAGE_DIR/${service}" \
                --testResultsProcessor="jest-junit" \
                --reporters=default \
                --reporters=jest-junit
            ;;
    esac
    
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ $service tests passed${NC}"
    else
        echo -e "${RED}✗ $service tests failed${NC}"
        return $exit_code
    fi
}

# Run tests based on parallel configuration
if [ "$PARALLEL_TESTS" = "true" ]; then
    echo -e "\n🚀 Running tests in parallel..."
    
    # Run Go service tests in parallel
    (run_service_tests "api-gateway" "go" "/app/backend/services/api-gateway") &
    PID_API_GATEWAY=$!
    
    (run_service_tests "technique-selector" "go" "/app/backend/services/technique-selector") &
    PID_TECHNIQUE=$!
    
    # Run Python service tests in parallel
    (run_service_tests "intent-classifier" "python" "/app/backend/services/intent-classifier") &
    PID_INTENT=$!
    
    (run_service_tests "prompt-generator" "python" "/app/backend/services/prompt-generator") &
    PID_PROMPT=$!
    
    # Run frontend tests
    (run_service_tests "frontend" "node" "/app/frontend") &
    PID_FRONTEND=$!
    
    # Wait for all tests to complete
    wait $PID_API_GATEWAY
    API_GATEWAY_EXIT=$?
    
    wait $PID_TECHNIQUE
    TECHNIQUE_EXIT=$?
    
    wait $PID_INTENT
    INTENT_EXIT=$?
    
    wait $PID_PROMPT
    PROMPT_EXIT=$?
    
    wait $PID_FRONTEND
    FRONTEND_EXIT=$?
    
    # Check if any tests failed
    if [ $API_GATEWAY_EXIT -ne 0 ] || [ $TECHNIQUE_EXIT -ne 0 ] || \
       [ $INTENT_EXIT -ne 0 ] || [ $PROMPT_EXIT -ne 0 ] || [ $FRONTEND_EXIT -ne 0 ]; then
        TESTS_FAILED=1
    else
        TESTS_FAILED=0
    fi
else
    echo -e "\n🚶 Running tests sequentially..."
    
    TESTS_FAILED=0
    
    run_service_tests "api-gateway" "go" "/app/backend/services/api-gateway" || TESTS_FAILED=1
    run_service_tests "technique-selector" "go" "/app/backend/services/technique-selector" || TESTS_FAILED=1
    run_service_tests "intent-classifier" "python" "/app/backend/services/intent-classifier" || TESTS_FAILED=1
    run_service_tests "prompt-generator" "python" "/app/backend/services/prompt-generator" || TESTS_FAILED=1
    run_service_tests "frontend" "node" "/app/frontend" || TESTS_FAILED=1
fi

# Generate coverage report
echo -e "\n📊 Generating coverage report..."
cd "$COVERAGE_DIR"

# Merge coverage reports
if command -v coverage &> /dev/null; then
    coverage combine || true
    coverage html -d "$COVERAGE_DIR/html" || true
    coverage report > "$RESULTS_DIR/coverage-summary.txt" || true
fi

# Calculate total coverage (simplified)
echo -e "\n📈 Coverage Summary:"
echo "==================="
if [ -f "$RESULTS_DIR/coverage-summary.txt" ]; then
    cat "$RESULTS_DIR/coverage-summary.txt"
else
    echo "Coverage reports available in: $COVERAGE_DIR"
fi

# Final status
echo -e "\n=================================="
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    echo "Check the results in: $RESULTS_DIR"
    exit 1
fi