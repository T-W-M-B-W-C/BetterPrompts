#!/bin/bash

# Start development script for BetterPrompts backend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Starting BetterPrompts Backend Development Environment..."

cd "$PROJECT_ROOT"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
fi

# Start infrastructure services
echo "🏗️  Starting infrastructure services..."
docker-compose up -d postgres redis rabbitmq

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are healthy
echo "🏥 Checking service health..."
docker-compose ps

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec -T postgres psql -U betterprompts -d betterprompts < infrastructure/docker/postgres/init.sql || true

# Start application services
echo "🚀 Starting application services..."
docker-compose up -d api-gateway intent-classifier

echo "✅ Backend services started!"
echo ""
echo "📚 Service URLs:"
echo "   - API Gateway: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Intent Classifier: http://localhost:8001"
echo "   - PgAdmin: http://localhost:5050 (profile: dev)"
echo "   - RabbitMQ Management: http://localhost:15672"
echo ""
echo "📋 Useful commands:"
echo "   - View logs: docker-compose logs -f [service-name]"
echo "   - Stop services: docker-compose down"
echo "   - Rebuild services: docker-compose build"
echo ""
echo "🎉 Happy coding!"