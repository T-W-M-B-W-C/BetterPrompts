#!/bin/bash

# Comprehensive fix for API Gateway build issues
echo "🔧 Comprehensive API Gateway Fix"
echo "================================="

cd /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts/backend/services/api-gateway

# Fix 1: database_complete.go - ShareToken comparison and assignment
echo "Fixing database_complete.go ShareToken issues..."
# Fix comparison
sed -i '' 's/collection\.ShareToken == ""/!collection.ShareToken.Valid || collection.ShareToken.String == ""/g' internal/services/database_complete.go
# Fix assignment
sed -i '' 's/collection\.ShareToken = uuid\.New()\.String()/collection.ShareToken = sql.NullString{String: uuid.New().String(), Valid: true}/g' internal/services/database_complete.go

# Fix 2: user.go - sql.NullString fields
echo "Fixing user.go sql.NullString issues..."
# Fix FirstName
sed -i '' 's/FirstName: req\.FirstName,/FirstName: sql.NullString{String: req.FirstName, Valid: req.FirstName != ""},/g' internal/services/user.go
# Fix LastName
sed -i '' 's/LastName: req\.LastName,/LastName: sql.NullString{String: req.LastName, Valid: req.LastName != ""},/g' internal/services/user.go
# Fix EmailVerifyToken
sed -i '' 's/EmailVerifyToken: verifyToken,/EmailVerifyToken: sql.NullString{String: verifyToken, Valid: true},/g' internal/services/user.go

# Fix 3: user.go - IsEmailVerified to IsVerified
echo "Fixing IsEmailVerified to IsVerified..."
sed -i '' 's/IsEmailVerified/IsVerified/g' internal/services/user.go

# Fix 4: user.go - s.db.db to s.db.DB
echo "Fixing database field access..."
sed -i '' 's/s\.db\.db/s.db.DB/g' internal/services/user.go

# Fix 5: Check if there are any more ShareToken issues in saved.go context
echo "Checking for more ShareToken issues..."
if grep -q 'saved\.ShareToken == ""' internal/services/database_complete.go; then
    echo "Fixing saved.ShareToken comparison..."
    sed -i '' 's/saved\.ShareToken == ""/!saved.ShareToken.Valid || saved.ShareToken.String == ""/g' internal/services/database_complete.go
fi

if grep -q 'saved\.ShareToken = uuid\.New()\.String()' internal/services/database_complete.go; then
    echo "Fixing saved.ShareToken assignment..."
    sed -i '' 's/saved\.ShareToken = uuid\.New()\.String()/saved.ShareToken = sql.NullString{String: uuid.New().String(), Valid: true}/g' internal/services/database_complete.go
fi

echo ""
echo "✅ All fixes applied. Now rebuilding..."
cd ../../..
docker compose build api-gateway