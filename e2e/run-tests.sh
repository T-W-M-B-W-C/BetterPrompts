#!/bin/bash

# Run E2E tests with proper setup and teardown

echo "🚀 Running E2E tests for BetterPrompts..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Navigate to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Parse command line arguments
SKIP_SETUP=false
SKIP_TEARDOWN=false
TEST_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-setup)
            SKIP_SETUP=true
            shift
            ;;
        --skip-teardown)
            SKIP_TEARDOWN=true
            shift
            ;;
        *)
            TEST_ARGS="$TEST_ARGS $1"
            shift
            ;;
    esac
done

# Setup environment if not skipped
if [ "$SKIP_SETUP" != true ]; then
    echo -e "${YELLOW}🔧 Setting up test environment...${NC}"
    ./setup-test-env.sh
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Setup failed. Exiting.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⏭️ Skipping setup (--skip-setup flag)${NC}"
fi

# Run tests
echo -e "${YELLOW}🧪 Running tests...${NC}"
cd frontend
npm test -- $TEST_ARGS
TEST_EXIT_CODE=$?

# Return to e2e directory
cd ..

# Teardown if not skipped and tests passed
if [ "$SKIP_TEARDOWN" != true ]; then
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo -e "${YELLOW}🧹 Tearing down test environment...${NC}"
        ./teardown-test-env.sh
    else
        echo -e "${YELLOW}⚠️ Tests failed. Keeping environment up for debugging.${NC}"
        echo "To teardown manually, run: ./teardown-test-env.sh"
    fi
else
    echo -e "${YELLOW}⏭️ Skipping teardown (--skip-teardown flag)${NC}"
fi

# Exit with test exit code
exit $TEST_EXIT_CODE