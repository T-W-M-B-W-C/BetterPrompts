#!/bin/bash
# Quick start script for local development

set -e

echo "🚀 Starting BetterPrompts local development environment..."

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
fi

# Build and start services
echo "🏗️  Building services (this may take a while on first run)..."
docker compose -f docker-compose.local.yml --progress=plain build

echo "🚀 Starting services..."
docker compose -f docker-compose.local.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo "📊 Service status:"
docker compose -f docker-compose.local.yml ps

echo ""
echo "✅ BetterPrompts is starting up!"
echo ""
echo "Service URLs:"
echo "  - API Gateway: http://localhost/api/v1"
echo "  - Health Check: http://localhost/health"
echo "  - Intent Classifier: http://localhost:8001"
echo "  - Technique Selector: http://localhost:8002"
echo "  - Prompt Generator: http://localhost:8003"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3001 (admin/admin)"
echo ""
echo "To view logs: docker compose -f docker-compose.local.yml logs -f"
echo "To stop: docker compose -f docker-compose.local.yml down"