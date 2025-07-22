#!/bin/bash

# Fix syntax error in history.go
echo "🔧 Fixing API Gateway Syntax Error"
echo "=================================="

cd /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts/backend/services/api-gateway

# Fix the malformed import line in history.go
echo "Fixing history.go import syntax..."
# Line 4 has merged imports incorrectly
sed -i '' '4s/"github.com\/sirupsen\/logrus"[[:space:]]*"net\/http"/"github.com\/sirupsen\/logrus"\
	"net\/http"/' internal/handlers/history.go

echo ""
echo "✅ Syntax fix applied. Now rebuilding..."
cd ../../..
docker compose build api-gateway