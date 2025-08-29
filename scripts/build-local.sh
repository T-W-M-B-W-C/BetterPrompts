#!/bin/bash
# Build script for local development
# This script builds all services for the BetterPrompts application

set -e

echo "🚀 Starting BetterPrompts local build..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your API keys if needed"
fi

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker compose -f docker-compose.local.yml down -v 2>/dev/null || true

# Build infrastructure services first (fastest)
echo "🏗️  Building infrastructure services..."
docker compose -f docker-compose.local.yml build \
    --parallel \
    postgres \
    redis \
    nginx \
    prometheus \
    grafana

# Build Go services
echo "🔧 Building Go services..."
docker compose -f docker-compose.local.yml build \
    --parallel \
    api-gateway \
    technique-selector

# Build Python services (can be slower due to ML dependencies)
echo "🐍 Building Python services (this may take a while)..."
docker compose -f docker-compose.local.yml build \
    --progress=plain \
    intent-classifier \
    prompt-generator

echo "✅ Build complete!"
echo ""
echo "To start the services, run:"
echo "  docker compose -f docker-compose.local.yml up -d"
echo ""
echo "To view logs:"
echo "  docker compose -f docker-compose.local.yml logs -f"
echo ""
echo "Service URLs:"
echo "  - API Gateway: http://localhost/api/v1"
echo "  - API Gateway (direct): http://localhost:8090"
echo "  - Intent Classifier: http://localhost:8001"
echo "  - Technique Selector: http://localhost:8002"
echo "  - Prompt Generator: http://localhost:8003"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3001 (admin/admin)"