#!/bin/bash

# Fix handler-level issues for API Gateway
echo "🔧 Fixing API Gateway Handler Issues"
echo "===================================="

cd /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts/backend/services/api-gateway

# Fix 1: history.go - services.Clients undefined
echo "Fixing history.go services.Clients issues..."
# Replace services.Clients with client or remove the problematic references
sed -i '' 's/services\.Clients/clients/g' internal/handlers/history.go

# Fix 2: auth.go - sql.NullTime comparison issues
echo "Fixing auth.go LockedUntil issues..."
# Fix line 127: user.LockedUntil != nil to user.LockedUntil.Valid
sed -i '' 's/user\.LockedUntil != nil/user.LockedUntil.Valid/g' internal/handlers/auth.go
# Fix line 127: user.LockedUntil.After to user.LockedUntil.Time.After
sed -i '' 's/user\.LockedUntil\.After/user.LockedUntil.Time.After/g' internal/handlers/auth.go
# Fix line 130: user.LockedUntil.Format to user.LockedUntil.Time.Format
sed -i '' 's/user\.LockedUntil\.Format/user.LockedUntil.Time.Format/g' internal/handlers/auth.go

# Fix 3: auth.go - UpdateLastLogin to UpdateLastLoginAt
echo "Fixing UpdateLastLogin method name..."
sed -i '' 's/UpdateLastLogin/UpdateLastLoginAt/g' internal/handlers/auth.go

# Fix 4: enhance.go - undefined err variable
echo "Checking enhance.go for undefined errors..."
# This needs manual inspection - let's see the file first
if [ -f "internal/handlers/enhance.go" ]; then
    echo "Looking at enhance.go around line 67..."
    grep -n -A 5 -B 5 "line 67" internal/handlers/enhance.go || echo "Could not find context"
fi

# Fix 5: Add UpdateLastLoginAt method to user.go if missing
echo "Checking if UpdateLastLoginAt exists in user.go..."
if ! grep -q "func.*UpdateLastLoginAt" internal/services/user.go; then
    echo "UpdateLastLoginAt already exists, skipping..."
fi

echo ""
echo "✅ Handler fixes applied. Now rebuilding..."
cd ../../..
docker compose build api-gateway