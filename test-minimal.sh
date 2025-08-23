#!/bin/bash
# Minimal test script - only infrastructure and Go services

set -e

echo "🚀 Testing minimal BetterPrompts setup..."

# Start only infrastructure
echo "🏗️  Starting infrastructure..."
docker compose -f docker-compose.local.yml up -d postgres redis nginx

# Wait for database
echo "⏳ Waiting for database..."
sleep 15

# Check database connection
echo "🔍 Testing database connection..."
docker compose -f docker-compose.local.yml exec -T postgres pg_isready -U betterprompts || echo "Database not ready"

# Check Redis
echo "🔍 Testing Redis connection..."
docker compose -f docker-compose.local.yml exec -T redis redis-cli ping || echo "Redis not ready"

# Build and start only Go services (they're fast)
echo "🔧 Building Go services..."
docker compose -f docker-compose.local.yml build api-gateway technique-selector
docker compose -f docker-compose.local.yml up -d api-gateway technique-selector

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 10

# Test endpoints
echo ""
echo "🔍 Testing service endpoints..."
echo "API Gateway health:"
curl -s http://localhost:8090/health || echo "API Gateway not responding"
echo ""
echo "Technique Selector health:"
curl -s http://localhost:8002/health || echo "Technique Selector not responding"

echo ""
echo "📊 Service status:"
docker compose -f docker-compose.local.yml ps

echo ""
echo "✅ Test complete!"
echo ""
echo "To stop services: docker compose -f docker-compose.local.yml down"