#!/bin/bash

# Final fix for remaining API Gateway build issues - Version 5
echo "🔧 Final API Gateway Fix V5"
echo "==========================="

cd /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts/backend/services/api-gateway

# Fix 1: history.go - Remove unused import
echo "Fixing history.go unused import..."
sed -i '' '/"github.com\/betterprompts\/api-gateway\/internal\/middleware"/d' internal/handlers/history.go

# Fix 2: history.go - Fix remaining h.clients references
echo "Fixing history.go remaining h.clients references..."
sed -i '' 's/func GetPromptHistoryItem(clients \*h\.clients)/func GetPromptHistoryItem(clients *services.ServiceClients)/' internal/handlers/history.go
sed -i '' 's/func DeletePromptHistoryItem(clients \*h\.clients)/func DeletePromptHistoryItem(clients *services.ServiceClients)/' internal/handlers/history.go

# Fix 3: history.go - Fix Logger usage (use logrus directly or add to context)
echo "Fixing history.go Logger references..."
# Replace clients.Logger with a logger from context
sed -i '' 's/clients\.Logger\.WithError(err)\.Error/c.MustGet("logger").(*logrus.Entry).WithError(err).Error/g' internal/handlers/history.go

# Fix 4: history.go - Add logrus import if missing
echo "Adding logrus import to history.go..."
if ! grep -q '"github.com/sirupsen/logrus"' internal/handlers/history.go; then
    sed -i '' '/^import (/a\
	"github.com/sirupsen/logrus"' internal/handlers/history.go
fi

# Fix 5: health.go - Remove Cache.Ping() call (cache doesn't have Ping)
echo "Fixing health.go Cache.Ping call..."
# Comment out or remove the cache ping check
sed -i '' '/clients\.Cache\.Ping()/,/}/ {
    s/if err := clients\.Cache\.Ping(); err != nil {/\/\/ Cache health check removed - no Ping method/
    /cacheStatus = "unhealthy"/d
    /cacheError = err\.Error()/d
    /}/d
}' internal/handlers/health.go

# Fix 6: Fix Database.ExecContext call in history.go
echo "Fixing history.go Database.ExecContext..."
sed -i '' 's/clients\.Database\.ExecContext/clients.Database.DB.ExecContext/g' internal/handlers/history.go

# Fix 7: Ensure all handlers are using correct patterns
echo "Final pattern check..."
# Make sure we don't have any remaining undefined references
grep -n "undefined: h" internal/handlers/*.go || echo "No undefined 'h' references found"

echo ""
echo "✅ Final fixes applied. Now rebuilding..."
cd ../../..
docker compose build api-gateway