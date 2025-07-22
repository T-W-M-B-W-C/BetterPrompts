#!/bin/bash

# Final comprehensive fix for all API Gateway build issues - Version 4
echo "🔧 Final API Gateway Fix V4"
echo "==========================="

cd /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts/backend/services/api-gateway

# Fix 1: history.go - Fix handler signature
echo "Fixing history.go handler signature and references..."
# Fix the function parameter from *h.clients to *services.ServiceClients
sed -i '' 's/func GetPromptHistory(clients \*h\.clients)/func GetPromptHistory(clients *services.ServiceClients)/' internal/handlers/history.go
sed -i '' 's/func GetPromptDetail(clients \*h\.clients)/func GetPromptDetail(clients *services.ServiceClients)/' internal/handlers/history.go
sed -i '' 's/func GetUserStatistics(clients \*h\.clients)/func GetUserStatistics(clients *services.ServiceClients)/' internal/handlers/history.go

# Fix 2: enhance.go - Fix type issues with proper imports first
echo "Fixing enhance.go imports..."
# Add missing imports
sed -i '' '/^import (/,/^)/ {
/^)/ i\
	"database/sql"\
	"fmt"
}' internal/handlers/enhance.go

# Fix 3: enhance.go - Fix the historyEntry struct creation around line 122-136
echo "Fixing enhance.go historyEntry creation..."
# Create a temporary file with the fixes
cat > /tmp/enhance_fix.sed << 'EOF'
/historyEntry := models.PromptHistory{/,/}/ {
    s/UserID:         userID,/UserID:         sql.NullString{String: func() string { if uid, ok := userID.(string); ok { return uid } else { return "" } }(), Valid: userID != nil},/
    s/SessionID:      sessionID,/SessionID:      sql.NullString{String: sessionID, Valid: sessionID != ""},/
    s/Intent:         intentResult.Intent,/Intent:         sql.NullString{String: intentResult.Intent, Valid: true},/
    s/Complexity:     intentResult.Complexity,/Complexity:     sql.NullString{String: fmt.Sprintf("%.2f", intentResult.Complexity), Valid: true},/
    s/Confidence:     intentResult.Confidence,/IntentConfidence: sql.NullFloat64{Float64: intentResult.Confidence, Valid: true},/
}
EOF
sed -i '' -f /tmp/enhance_fix.sed internal/handlers/enhance.go
rm /tmp/enhance_fix.sed

# Fix 4: enhance.go - Fix response Complexity type
echo "Fixing enhance.go response Complexity..."
# Find the line with response creation and fix Complexity field
sed -i '' '/response := EnhanceResponse{/,/}/ {
    s/Complexity:     intentResult.Complexity,/Complexity:     fmt.Sprintf("%.2f", intentResult.Complexity),/
}' internal/handlers/enhance.go

# Fix 5: health.go - Fix Database.Ping call
echo "Fixing health.go Database.Ping call..."
sed -i '' 's/clients\.Database\.Ping(c\.Request\.Context())/clients.Database.Ping()/' internal/handlers/health.go

# Fix 6: Fix remaining 'clients' references to use proper receiver
echo "Fixing remaining handler client references..."
# In enhance.go, the clients parameter is already correct from the function signature
# Just need to ensure we're not adding h. prefix where it shouldn't be
sed -i '' 's/h\.clients\./clients./g' internal/handlers/enhance.go

# Fix 7: Ensure database.go has Ping() method without context
echo "Checking database.go Ping method..."
if ! grep -q "func.*Ping()" internal/services/database.go; then
    echo "Adding Ping() method to database.go..."
    # Add the method if it doesn't exist
    cat >> internal/services/database.go << 'EOF'

// Ping tests the database connection
func (s *DatabaseService) Ping() error {
	return s.DB.Ping()
}
EOF
fi

echo ""
echo "✅ All fixes applied. Now rebuilding..."
cd ../../..
docker compose build api-gateway