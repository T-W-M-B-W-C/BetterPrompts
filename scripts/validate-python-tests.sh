#!/bin/bash

# Validate Python test structure and quality
# This script checks test organization, naming conventions, and best practices

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Function to check test structure
check_test_structure() {
    local service_path=$1
    local service_name=$2
    local errors=0
    
    print_info "Checking test structure for $service_name..."
    
    # Check if test directories exist
    if [ ! -d "$service_path/tests" ]; then
        print_error "Missing tests directory"
        ((errors++))
    else
        print_status "tests directory exists"
    fi
    
    if [ ! -d "$service_path/tests/unit" ]; then
        print_error "Missing tests/unit directory"
        ((errors++))
    else
        print_status "tests/unit directory exists"
    fi
    
    if [ ! -d "$service_path/tests/integration" ]; then
        print_warning "Missing tests/integration directory (optional)"
    else
        print_status "tests/integration directory exists"
    fi
    
    # Check for conftest.py
    if [ ! -f "$service_path/tests/conftest.py" ]; then
        print_error "Missing tests/conftest.py"
        ((errors++))
    else
        print_status "tests/conftest.py exists"
    fi
    
    # Check for __init__.py files
    if [ ! -f "$service_path/tests/__init__.py" ]; then
        print_warning "Missing tests/__init__.py"
    fi
    
    # Check for test utilities
    if [ ! -d "$service_path/tests/utils" ]; then
        print_warning "Missing tests/utils directory (recommended)"
    else
        print_status "tests/utils directory exists"
    fi
    
    # Check pytest configuration
    if [ ! -f "$service_path/pytest.ini" ]; then
        print_warning "Missing pytest.ini configuration"
    else
        print_status "pytest.ini exists"
    fi
    
    return $errors
}

# Function to check test naming conventions
check_test_naming() {
    local service_path=$1
    local service_name=$2
    local errors=0
    
    print_info "Checking test naming conventions for $service_name..."
    
    # Find all test files
    local test_files=$(find "$service_path/tests" -name "test_*.py" -type f 2>/dev/null | wc -l)
    local bad_names=$(find "$service_path/tests" -name "*.py" -type f ! -name "test_*" ! -name "__init__.py" ! -name "conftest.py" ! -path "*/utils/*" 2>/dev/null | wc -l)
    
    if [ $test_files -eq 0 ]; then
        print_error "No test files found (test_*.py)"
        ((errors++))
    else
        print_status "Found $test_files test files"
    fi
    
    if [ $bad_names -gt 0 ]; then
        print_warning "Found $bad_names Python files not following test naming convention"
    fi
    
    return $errors
}

# Function to check test quality
check_test_quality() {
    local service_path=$1
    local service_name=$2
    local errors=0
    
    print_info "Checking test quality for $service_name..."
    
    # Check for docstrings in test files
    local test_files_with_docstrings=$(find "$service_path/tests" -name "test_*.py" -type f -exec grep -l '"""' {} \; 2>/dev/null | wc -l)
    local total_test_files=$(find "$service_path/tests" -name "test_*.py" -type f 2>/dev/null | wc -l)
    
    if [ $total_test_files -gt 0 ]; then
        local docstring_percentage=$((test_files_with_docstrings * 100 / total_test_files))
        if [ $docstring_percentage -lt 50 ]; then
            print_warning "Only $docstring_percentage% of test files have docstrings"
        else
            print_status "$docstring_percentage% of test files have docstrings"
        fi
    fi
    
    # Check for assertions
    local files_without_assertions=$(find "$service_path/tests" -name "test_*.py" -type f -exec sh -c 'grep -L "assert\|self.assert\|pytest.raises" "$1" 2>/dev/null' _ {} \; | wc -l)
    
    if [ $files_without_assertions -gt 0 ]; then
        print_warning "Found $files_without_assertions test files without assertions"
    else
        print_status "All test files contain assertions"
    fi
    
    # Check for proper async test handling
    local async_tests=$(find "$service_path/tests" -name "test_*.py" -type f -exec grep -l "async def test_" {} \; 2>/dev/null | wc -l)
    if [ $async_tests -gt 0 ]; then
        print_status "Found $async_tests files with async tests"
    fi
    
    return $errors
}

# Function to generate test summary
generate_summary() {
    local service_path=$1
    local service_name=$2
    
    print_info "\nTest Summary for $service_name:"
    
    # Count test files and functions
    local unit_tests=$(find "$service_path/tests/unit" -name "test_*.py" -type f 2>/dev/null | wc -l)
    local integration_tests=$(find "$service_path/tests/integration" -name "test_*.py" -type f 2>/dev/null | wc -l)
    local test_functions=$(find "$service_path/tests" -name "test_*.py" -type f -exec grep -c "def test_" {} \; 2>/dev/null | awk '{sum+=$1} END {print sum}')
    
    echo "  Unit test files: $unit_tests"
    echo "  Integration test files: $integration_tests"
    echo "  Total test functions: ${test_functions:-0}"
}

# Main execution
main() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local project_root="$(dirname "$script_dir")"
    
    echo "Python Test Validation Report"
    echo "============================"
    echo ""
    
    local total_errors=0
    
    # Check Intent Classifier
    echo "Intent Classifier Service"
    echo "------------------------"
    local intent_path="$project_root/backend/services/intent-classifier"
    local intent_errors=0
    
    check_test_structure "$intent_path" "Intent Classifier"
    intent_errors=$((intent_errors + $?))
    
    check_test_naming "$intent_path" "Intent Classifier"
    intent_errors=$((intent_errors + $?))
    
    check_test_quality "$intent_path" "Intent Classifier"
    intent_errors=$((intent_errors + $?))
    
    generate_summary "$intent_path" "Intent Classifier"
    
    total_errors=$((total_errors + intent_errors))
    
    echo ""
    echo "Prompt Generator Service"
    echo "-----------------------"
    local prompt_path="$project_root/backend/services/prompt-generator"
    local prompt_errors=0
    
    check_test_structure "$prompt_path" "Prompt Generator"
    prompt_errors=$((prompt_errors + $?))
    
    check_test_naming "$prompt_path" "Prompt Generator"
    prompt_errors=$((prompt_errors + $?))
    
    check_test_quality "$prompt_path" "Prompt Generator"
    prompt_errors=$((prompt_errors + $?))
    
    generate_summary "$prompt_path" "Prompt Generator"
    
    total_errors=$((total_errors + prompt_errors))
    
    # Final summary
    echo ""
    echo "============================"
    echo "Validation Summary"
    echo "============================"
    
    if [ $total_errors -eq 0 ]; then
        print_status "All validation checks passed!"
        exit 0
    else
        print_error "Found $total_errors validation errors"
        exit 1
    fi
}

# Run main function
main "$@"