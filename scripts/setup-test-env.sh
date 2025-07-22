#!/bin/bash
# Setup test environment for BetterPrompts

set -e

echo "🚀 Setting up BetterPrompts test environment..."
echo "============================================"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating test directories..."
mkdir -p tests/mocks/wiremock/{mappings,__files}
mkdir -p tests/e2e/{specs,results,playwright-report}
mkdir -p tests/performance/{scripts,results}
mkdir -p tests/scripts
mkdir -p coverage
mkdir -p test-results

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x tests/scripts/*.sh
chmod +x scripts/*.sh
chmod +x tests/performance/analyze_results.py

# Build test infrastructure
echo "🏗️  Building test infrastructure..."
docker compose -f docker-compose.test.yml build

# Pull required images
echo "📥 Pulling required Docker images..."
docker pull wiremock/wiremock:3.3.1
docker pull grafana/k6:latest
docker pull mcr.microsoft.com/playwright:v1.41.0-focal

# Validate configuration
echo "✅ Validating test configuration..."
docker compose -f docker-compose.test.yml config > /dev/null

# Create .env.test file if it doesn't exist
if [ ! -f .env.test ]; then
    echo "📝 Creating .env.test file..."
    cat > .env.test << EOF
# Test Environment Configuration
NODE_ENV=test
ENV=test

# Database
DB_HOST=test-postgres
DB_PORT=5432
DB_USER=test_user
DB_PASSWORD=test_password
DB_NAME=betterprompts_test

# Redis
REDIS_HOST=test-redis
REDIS_PORT=6379

# Services
TORCHSERVE_URL=http://mock-torchserve:8080
API_GATEWAY_URL=http://api-gateway:8080

# Test Configuration
COVERAGE_ENABLED=true
PARALLEL_TESTS=true
TEST_TIMEOUT=30m
COVERAGE_THRESHOLD=80

# Mock Configuration
MOCK_LATENCY_MS=100
MOCK_ERROR_RATE=0
MOCK_LLM_ENABLED=true
EOF
fi

echo ""
echo "✅ Test environment setup complete!"
echo ""
echo "📋 Quick Start Commands:"
echo "  - Run all tests:        docker compose -f docker-compose.test.yml up"
echo "  - Run specific service: docker compose -f docker-compose.test.yml run --rm test-runner ./scripts/test-service.sh <service>"
echo "  - View coverage:        docker compose -f docker-compose.test.yml run --rm test-runner ./scripts/coverage-report.sh"
echo "  - Run E2E tests:        docker compose -f docker-compose.test.yml run --rm playwright"
echo "  - Run load tests:       docker compose -f docker-compose.test.yml run --rm k6"
echo ""
echo "📚 Documentation:"
echo "  - Test Strategy:        planning/testing-strategy.md"
echo "  - Test Templates:       planning/test-implementation-templates.md"
echo "  - Infrastructure Guide: planning/test-infrastructure-guide.md"
echo ""