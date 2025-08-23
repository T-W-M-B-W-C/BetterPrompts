#!/bin/bash
# Quick start for local development without heavy ML dependencies

set -e

echo "🚀 Starting BetterPrompts (Minimal Local Development Mode)..."

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
fi

# Start only the essential services first
echo "🏗️  Starting infrastructure services..."
docker compose -f docker-compose.local.yml up -d postgres redis nginx

# Wait for database to be ready
echo "⏳ Waiting for database..."
sleep 10

# Build and start Go services (they build fast)
echo "🔧 Building Go services..."
docker compose -f docker-compose.local.yml build api-gateway technique-selector
docker compose -f docker-compose.local.yml up -d api-gateway technique-selector

# Start Python services without building (use pre-built images)
echo "🐍 Starting Python services with minimal dependencies..."
docker compose -f docker-compose.local.yml up -d prompt-generator

# Skip intent-classifier for now (requires ML dependencies)
echo "⚠️  Skipping intent-classifier (requires ML dependencies)"

# Check status
echo ""
echo "📊 Service status:"
docker compose -f docker-compose.local.yml ps

echo ""
echo "✅ Core services are running!"
echo ""
echo "Available services:"
echo "  - API Gateway: http://localhost/api/v1"
echo "  - API Gateway (direct): http://localhost:8090"
echo "  - Technique Selector: http://localhost:8002"
echo "  - Prompt Generator: http://localhost:8003"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "To view logs: docker compose -f docker-compose.local.yml logs -f"
echo "To stop: docker compose -f docker-compose.local.yml down"
echo ""
echo "Note: Intent classifier is disabled in this minimal setup."
echo "For full ML support, use production Docker setup or install dependencies locally."