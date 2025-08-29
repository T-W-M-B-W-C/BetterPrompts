#!/bin/bash

# Fix duplicate RequireRole declaration
echo "🔧 Fixing Duplicate Declaration"
echo "==============================="

cd /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts/backend/services/api-gateway

# Remove the duplicate RequireRole function from request.go
echo "Removing duplicate RequireRole from request.go..."
sed -i '' '/^\/\/ RequireRole middleware/,/^}$/d' internal/middleware/request.go

# Add missing handler functions to stubs.go
echo "Adding missing handler functions..."
cat >> internal/handlers/stubs.go << 'EOF'

func GetDeveloperUsage(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"usage": map[string]interface{}{}})
	}
}

func GetPerformanceMetrics(clients *services.ServiceClients) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"performance": map[string]interface{}{}})
	}
}
EOF

echo ""
echo "✅ Duplicate declaration fixed. Now rebuilding..."
cd ../../..
docker compose build api-gateway