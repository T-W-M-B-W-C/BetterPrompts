#!/bin/bash

# Comprehensive fix for all API Gateway build issues - Version 3
echo "🔧 Comprehensive API Gateway Fix V3"
echo "==================================="

cd /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts/backend/services/api-gateway

# Fix 1: history.go - Fix undefined 'h' by replacing with correct handler structure
echo "Fixing history.go handler references..."
# First, let's check what the actual handler pattern is
grep -n "func.*gin.HandlerFunc" internal/handlers/history.go | head -5
# Replace h.clients with clients (assuming it's passed as parameter)
sed -i '' 's/\bh\.clients\./clients./g' internal/handlers/history.go

# Fix 2: enhance.go - Fix sql.NullString type assertions
echo "Fixing enhance.go type issues..."
# Line 124: userID type assertion
sed -i '' '124s/UserID:         userID,/UserID:         sql.NullString{String: userID.(string), Valid: userID != nil},/' internal/handlers/enhance.go
# Line 125: sessionID to sql.NullString
sed -i '' '125s/SessionID:      sessionID,/SessionID:      sql.NullString{String: sessionID, Valid: sessionID != ""},/' internal/handlers/enhance.go
# Line 128: Intent to sql.NullString
sed -i '' '128s/Intent:         intentResult.Intent,/Intent:         sql.NullString{String: intentResult.Intent, Valid: true},/' internal/handlers/enhance.go
# Line 129: Complexity to sql.NullString (converting float64 to string)
sed -i '' '129s/Complexity:     intentResult.Complexity,/Complexity:     sql.NullString{String: fmt.Sprintf("%.2f", intentResult.Complexity), Valid: true},/' internal/handlers/enhance.go
# Line 131: Change Confidence to IntentConfidence
sed -i '' '131s/Confidence:/IntentConfidence: sql.NullFloat64{Float64:/' internal/handlers/enhance.go
sed -i '' '131s/intentResult.Confidence,/intentResult.Confidence, Valid: true},/' internal/handlers/enhance.go

# Fix 3: enhance.go - Fix response Complexity type (line 150)
echo "Fixing enhance.go response Complexity..."
sed -i '' '150s/Complexity:     intentResult.Complexity,/Complexity:     fmt.Sprintf("%.2f", intentResult.Complexity),/' internal/handlers/enhance.go

# Fix 4: enhance.go - Add fmt import if missing
echo "Adding fmt import to enhance.go..."
if ! grep -q '"fmt"' internal/handlers/enhance.go; then
    sed -i '' '/^import (/a\
	"fmt"' internal/handlers/enhance.go
fi

# Fix 5: enhance.go - Add database/sql import if missing
echo "Adding database/sql import to enhance.go..."
if ! grep -q '"database/sql"' internal/handlers/enhance.go; then
    sed -i '' '/^import (/a\
	"database/sql"' internal/handlers/enhance.go
fi

# Fix 6: health.go - Fix Database.Ping call
echo "Fixing health.go Database.Ping call..."
sed -i '' 's/clients\.Database\.Ping(c\.Request\.Context())/clients.Database.Ping()/' internal/handlers/health.go

# Fix 7: Fix history.go Confidence field
echo "Fixing history.go Confidence references..."
sed -i '' 's/entry\.IntentConfidence/entry.IntentConfidence.Float64/g' internal/handlers/history.go

# Fix 8: Fix any remaining clients references in enhance.go
echo "Fixing remaining clients references in enhance.go..."
# Already fixed in previous script, but let's ensure it's correct
sed -i '' 's/\bclients\./h.clients./g' internal/handlers/enhance.go

echo ""
echo "✅ All comprehensive fixes applied. Now rebuilding..."
cd ../../..
docker compose build api-gateway