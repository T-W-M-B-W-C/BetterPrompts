#!/bin/bash

# Fix handler-level issues for API Gateway
echo "🔧 Fixing API Gateway Handler Issues V2"
echo "======================================="

cd /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts/backend/services/api-gateway

# Fix 1: history.go - services.Clients undefined
echo "Fixing history.go services.Clients issues..."
# Check if it's supposed to be h.clients instead
sed -i '' 's/services\.Clients/h.clients/g' internal/handlers/history.go

# Fix 2: auth.go - sql.NullTime comparison issues
echo "Fixing auth.go LockedUntil issues..."
# Fix user.LockedUntil != nil to user.LockedUntil.Valid
sed -i '' 's/user\.LockedUntil != nil/user.LockedUntil.Valid/g' internal/handlers/auth.go
# Fix user.LockedUntil.After to user.LockedUntil.Time.After
sed -i '' 's/user\.LockedUntil\.After/user.LockedUntil.Time.After/g' internal/handlers/auth.go
# Fix user.LockedUntil.Format to user.LockedUntil.Time.Format
sed -i '' 's/user\.LockedUntil\.Format/user.LockedUntil.Time.Format/g' internal/handlers/auth.go

# Fix 3: auth.go - UpdateLastLogin to UpdateLastLoginAt
echo "Fixing UpdateLastLogin method name..."
sed -i '' 's/\.UpdateLastLogin(/.UpdateLastLoginAt(/g' internal/handlers/auth.go

# Fix 4: enhance.go - fix err declaration on line 67
echo "Fixing enhance.go error declaration..."
# Change line 67 to declare err properly
sed -i '' '67s/intentResult, err = clients/var err error\
\t\t\tintentResult, err = clients/g' internal/handlers/enhance.go

# Fix 5: Fix clients references in enhance.go
echo "Fixing enhance.go clients references..."
# Replace standalone 'clients' with 'h.clients'
sed -i '' 's/\bclients\./h.clients./g' internal/handlers/enhance.go

# Fix 6: history.go field names
echo "Fixing history.go field names..."
# Fix Confidence to IntentConfidence
sed -i '' 's/\.Confidence/.IntentConfidence/g' internal/handlers/history.go
# Fix Complexity to be a string (if it's being used as float64)
# This might need more context-specific fixes

echo ""
echo "✅ Handler fixes applied. Now rebuilding..."
cd ../../..
docker compose build api-gateway