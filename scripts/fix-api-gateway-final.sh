#!/bin/bash

# Final comprehensive fix for API Gateway build issues
echo "🔧 Final API Gateway Fix"
echo "========================"

cd /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts/backend/services/api-gateway

# Fix 1: user.go - Fix FirstName and LastName assignments for struct literals
echo "Fixing user.go struct literal issues..."
# Lines 55-56: Fix struct literal for req.FirstName and req.LastName
sed -i '' '55s/FirstName:        req\.FirstName,/FirstName:        sql.NullString{String: req.FirstName, Valid: req.FirstName != ""},/' internal/services/user.go
sed -i '' '56s/LastName:         req\.LastName,/LastName:         sql.NullString{String: req.LastName, Valid: req.LastName != ""},/' internal/services/user.go

# Fix 2: user.go - Fix field names (PasswordResetExpiry -> PasswordResetExpires, LastLogin -> LastLoginAt)
echo "Fixing field name mismatches..."
# Replace all occurrences of PasswordResetExpiry with PasswordResetExpires
sed -i '' 's/PasswordResetExpiry/PasswordResetExpires/g' internal/services/user.go
# Replace all occurrences of LastLogin with LastLoginAt
sed -i '' 's/LastLogin/LastLoginAt/g' internal/services/user.go

# Fix 3: user.go - Fix pointer dereference assignments for FirstName and LastName
echo "Fixing pointer dereference assignments..."
# Line 246: user.FirstName = *req.FirstName
sed -i '' '246s/user\.FirstName = \*req\.FirstName/user.FirstName = sql.NullString{String: *req.FirstName, Valid: *req.FirstName != ""}/' internal/services/user.go
# Line 249: user.LastName = *req.LastName
sed -i '' '249s/user\.LastName = \*req\.LastName/user.LastName = sql.NullString{String: *req.LastName, Valid: *req.LastName != ""}/' internal/services/user.go

# Fix 4: user.go - Fix SQL column names in queries
echo "Fixing SQL column names..."
# Replace is_email_verified with is_verified in SQL queries
sed -i '' 's/is_email_verified/is_verified/g' internal/services/user.go
# Replace last_login with last_login_at in SQL queries
sed -i '' 's/last_login/last_login_at/g' internal/services/user.go
# Replace password_reset_expiry with password_reset_expires in SQL queries
sed -i '' 's/password_reset_expiry/password_reset_expires/g' internal/services/user.go

# Fix 5: database_complete.go - Fix any remaining ShareToken issues
echo "Final check for ShareToken issues..."
if grep -q 'collection\.ShareToken == ""' internal/services/database_complete.go; then
    sed -i '' 's/collection\.ShareToken == ""/!collection.ShareToken.Valid || collection.ShareToken.String == ""/g' internal/services/database_complete.go
fi
if grep -q 'collection\.ShareToken = uuid\.New()\.String()' internal/services/database_complete.go; then
    sed -i '' 's/collection\.ShareToken = uuid\.New()\.String()/collection.ShareToken = sql.NullString{String: uuid.New().String(), Valid: true}/g' internal/services/database_complete.go
fi

echo ""
echo "✅ All fixes applied. Now rebuilding..."
cd ../../..
docker compose build api-gateway