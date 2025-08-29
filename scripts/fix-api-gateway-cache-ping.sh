#!/bin/bash

# Final fix for CacheService Ping method
echo "🔧 Fixing CacheService Ping Method"
echo "=================================="

cd /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts/backend/services/api-gateway

# Add Ping method to cache.go
echo "Adding Ping method to CacheService..."
cat >> internal/services/cache.go << 'EOF'

// Ping tests the cache connection
func (c *CacheService) Ping(ctx context.Context) error {
	return c.client.Ping(ctx).Err()
}
EOF

echo ""
echo "✅ CacheService Ping method added. Now rebuilding..."
cd ../../..
docker compose build api-gateway