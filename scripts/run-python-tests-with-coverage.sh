#!/bin/bash

# Run Python tests with coverage for BetterPrompts services
# This script runs tests for intent-classifier and prompt-generator services with coverage reporting

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to run tests for a service
run_service_tests() {
    local service_name=$1
    local service_path=$2
    local coverage_threshold=${3:-85}
    
    print_status "Running tests for $service_name..."
    
    cd "$service_path"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        if [ -f "requirements-test.txt" ]; then
            pip install -r requirements-test.txt
        fi
    else
        source venv/bin/activate
    fi
    
    # Install coverage tools if not already installed
    pip install pytest pytest-cov pytest-asyncio pytest-mock coverage
    
    # Run tests with coverage
    print_status "Running unit tests..."
    pytest tests/unit/ -v --cov=app --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml
    
    # Run integration tests separately
    if [ -d "tests/integration" ]; then
        print_status "Running integration tests..."
        pytest tests/integration/ -v --cov=app --cov-append --cov-report=term-missing
    fi
    
    # Generate coverage report
    coverage report --precision=2
    
    # Check coverage threshold
    coverage_percentage=$(coverage report --precision=2 | grep TOTAL | awk '{print $4}' | sed 's/%//')
    
    if [ -n "$coverage_percentage" ]; then
        if (( $(echo "$coverage_percentage >= $coverage_threshold" | bc -l) )); then
            print_status "$service_name coverage: ${coverage_percentage}% (meets threshold of ${coverage_threshold}%)"
        else
            print_error "$service_name coverage: ${coverage_percentage}% (below threshold of ${coverage_threshold}%)"
            return 1
        fi
    else
        print_error "Could not determine coverage percentage"
        return 1
    fi
    
    deactivate
    cd - > /dev/null
    
    return 0
}

# Main execution
main() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local project_root="$(dirname "$script_dir")"
    
    print_status "Starting Python test coverage analysis..."
    
    # Run tests for intent-classifier
    if ! run_service_tests "Intent Classifier" "$project_root/backend/services/intent-classifier" 85; then
        print_error "Intent Classifier tests failed"
        exit 1
    fi
    
    print_status "----------------------------------------"
    
    # Run tests for prompt-generator
    if ! run_service_tests "Prompt Generator" "$project_root/backend/services/prompt-generator" 85; then
        print_error "Prompt Generator tests failed"
        exit 1
    fi
    
    print_status "----------------------------------------"
    print_status "All tests completed successfully!"
    
    # Generate combined coverage report
    print_status "Generating combined coverage report..."
    
    # Create coverage report directory
    mkdir -p "$project_root/coverage-reports"
    
    # Copy individual reports
    cp -r "$project_root/backend/services/intent-classifier/htmlcov" "$project_root/coverage-reports/intent-classifier"
    cp -r "$project_root/backend/services/prompt-generator/htmlcov" "$project_root/coverage-reports/prompt-generator"
    
    print_status "Coverage reports available at:"
    print_status "  - Intent Classifier: $project_root/coverage-reports/intent-classifier/index.html"
    print_status "  - Prompt Generator: $project_root/coverage-reports/prompt-generator/index.html"
}

# Run main function
main "$@"