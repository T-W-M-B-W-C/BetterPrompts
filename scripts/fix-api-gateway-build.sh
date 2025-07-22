#!/bin/bash

# Quick fix for API Gateway build issues
echo "🔧 Fixing API Gateway Build Issues"
echo "=================================="

cd /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts/backend/services/api-gateway

# Fix 1: Update database.go to use IntentConfidence instead of Confidence
echo "Fixing database.go..."
sed -i '' 's/entry\.Confidence/entry.IntentConfidence.Float64/g' internal/services/database.go

# Fix 2: Update database_complete.go to use Roles instead of Role
echo "Fixing database_complete.go..."
sed -i '' 's/user\.Role/user.Roles[0]/g' internal/services/database_complete.go

# Fix 3: Fix ShareToken comparison
echo "Fixing ShareToken comparison..."
sed -i '' 's/saved\.ShareToken == ""/!saved.ShareToken.Valid || saved.ShareToken.String == ""/g' internal/services/database_complete.go

# Fix 4: Fix ShareToken assignment
sed -i '' 's/saved\.ShareToken = uuid\.New()\.String()/saved.ShareToken = sql.NullString{String: uuid.New().String(), Valid: true}/g' internal/services/database_complete.go

echo ""
echo "✅ Fixes applied. Now rebuilding..."
cd ../../..
docker compose build api-gateway