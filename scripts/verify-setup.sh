#!/bin/bash

# BetterPrompts Configuration Verification Script
# Verifies that multi-architecture Docker setup is working correctly

set -e

echo "🔍 BetterPrompts Configuration Verification"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [[ "$status" == "PASS" ]]; then
        echo -e "${GREEN}✅ PASS${NC}: $message"
    elif [[ "$status" == "FAIL" ]]; then
        echo -e "${RED}❌ FAIL${NC}: $message"
        return 1
    elif [[ "$status" == "WARN" ]]; then
        echo -e "${YELLOW}⚠️  WARN${NC}: $message"
    else
        echo -e "${BLUE}ℹ️  INFO${NC}: $message"
    fi
}

# Function to run test and capture result
run_test() {
    local test_name=$1
    local test_command=$2
    local expected_output=$3
    
    echo ""
    echo "🧪 Testing: $test_name"
    
    if output=$(eval "$test_command" 2>&1); then
        if [[ -z "$expected_output" ]] || echo "$output" | grep -q "$expected_output"; then
            print_status "PASS" "$test_name"
            return 0
        else
            print_status "FAIL" "$test_name - Expected: $expected_output"
            echo "   Actual output: $output"
            return 1
        fi
    else
        print_status "FAIL" "$test_name - Command failed"
        echo "   Error: $output"
        return 1
    fi
}

# Initialize counters
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Test function wrapper
test_wrapper() {
    local test_name=$1
    local test_command=$2
    local expected_output=$3
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if run_test "$test_name" "$test_command" "$expected_output"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

echo ""
echo "🔍 System Information"
echo "Platform: $(uname -s) $(uname -m)"
echo "Docker version: $(docker --version)"
echo ""

# Test 1: Platform Detection
test_wrapper "Platform detection script exists" "test -x ./scripts/setup-platform.sh" ""

# Test 2: Environment files exist
test_wrapper "Intel environment file exists" "test -f .env.intel" ""
test_wrapper "ARM environment file exists" "test -f .env.arm64" ""

# Test 3: Docker Compose files exist
test_wrapper "Intel compose override exists" "test -f docker-compose.intel.yml" ""
test_wrapper "ARM compose override exists" "test -f docker-compose.arm64.yml" ""

# Test 4: Build script exists
test_wrapper "Build script exists" "test -x ./scripts/build.sh" ""

# Test 5: Docker buildx setup
test_wrapper "Docker buildx multiarch builder exists" "docker buildx ls | grep multiarch" "multiarch"

# Test 6: Environment configuration
if [[ -f .env ]]; then
    test_wrapper "Docker platform variable set" "grep -q 'DOCKER_PLATFORM=' .env" ""
    
    # Check platform-specific settings
    ARCH=$(uname -m)
    if [[ "$ARCH" == "x86_64" ]]; then
        test_wrapper "Intel PyTorch index URL configured" "grep -q 'PYTORCH_INDEX_URL=https://download.pytorch.org/whl/cpu' .env" ""
        test_wrapper "Intel platform configured" "grep -q 'DOCKER_PLATFORM=linux/amd64' .env" ""
    elif [[ "$ARCH" == "arm64" ]]; then
        test_wrapper "ARM PyTorch index URL configured" "grep -q 'PYTORCH_INDEX_URL=$' .env" ""
        test_wrapper "ARM platform configured" "grep -q 'DOCKER_PLATFORM=linux/arm64' .env" ""
    fi
else
    print_status "WARN" ".env file not found - run ./scripts/setup-platform.sh first"
fi

# Test 7: Docker Compose validation
test_wrapper "Docker Compose config validation" "docker compose config > /dev/null" ""

# Test 8: Platform-specific compose validation
ARCH=$(uname -m)
if [[ "$ARCH" == "x86_64" ]]; then
    test_wrapper "Intel compose override validation" "docker compose -f docker-compose.yml -f docker-compose.intel.yml config > /dev/null" ""
elif [[ "$ARCH" == "arm64" ]]; then
    test_wrapper "ARM compose override validation" "docker compose -f docker-compose.yml -f docker-compose.arm64.yml config > /dev/null" ""
fi

# Test 9: Simple build test (optional - only if Docker is available)
if docker info > /dev/null 2>&1; then
    echo ""
    echo "🏗️  Optional: Testing build capability"
    echo "This may take a few minutes..."
    
    if timeout 300 ./scripts/build.sh --target nginx > /tmp/build_test.log 2>&1; then
        test_wrapper "Sample service build" "grep -q 'Successfully built nginx' /tmp/build_test.log" ""
    else
        print_status "WARN" "Build test timed out or failed - check /tmp/build_test.log"
    fi
    rm -f /tmp/build_test.log
else
    print_status "WARN" "Docker daemon not running - skipping build test"
fi

# Summary
echo ""
echo "📊 Test Summary"
echo "==============="
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"

if [[ $TESTS_FAILED -eq 0 ]]; then
    print_status "PASS" "All tests passed! Your system is configured correctly."
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Add your API keys to .env file"
    echo "   2. Run: docker compose up -d"
    echo "   3. Check services: docker compose ps"
    exit 0
else
    print_status "FAIL" "$TESTS_FAILED test(s) failed. Please review the issues above."
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   1. Run: ./scripts/setup-platform.sh"
    echo "   2. Ensure Docker is running"
    echo "   3. Check the MULTI_ARCH_SETUP.md guide"
    exit 1
fi