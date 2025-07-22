#!/bin/bash

# Docker Network Connectivity Fix Script
# Resolves common Docker Desktop DNS and network issues

echo "🔧 Docker Network Troubleshooting"
echo "================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "1. Checking Docker status..."
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker is running"
else
    echo -e "${RED}✗${NC} Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo ""
echo "2. Testing Docker Hub connectivity..."
if curl -s https://registry-1.docker.io/v2/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Can reach Docker Hub via curl"
else
    echo -e "${RED}✗${NC} Cannot reach Docker Hub - network issue detected"
fi

echo ""
echo "3. Testing DNS resolution..."
if nslookup registry-1.docker.io > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} DNS resolution working"
else
    echo -e "${RED}✗${NC} DNS resolution failing"
fi

echo ""
echo "4. Attempting fixes..."

# Fix 1: Restart Docker networking
echo -e "${YELLOW}→${NC} Restarting Docker Desktop networking..."
osascript -e 'quit app "Docker"' 2>/dev/null || true
sleep 3
open -a Docker
echo "   Waiting for Docker to restart (30 seconds)..."
sleep 30

# Wait for Docker to be ready
for i in {1..30}; do
    if docker info > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Docker is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗${NC} Docker failed to start"
        exit 1
    fi
    sleep 1
done

# Fix 2: Reset Docker DNS
echo ""
echo -e "${YELLOW}→${NC} Resetting Docker DNS settings..."
cat > ~/.docker/daemon.json << EOF
{
  "dns": ["8.8.8.8", "8.8.4.4", "1.1.1.1"],
  "debug": false,
  "experimental": false
}
EOF

echo ""
echo "5. Testing Docker pull..."
if docker pull alpine:latest > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker pull successful!"
    
    echo ""
    echo "6. Building API Gateway..."
    cd /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts
    if docker compose build api-gateway; then
        echo -e "${GREEN}✓${NC} API Gateway build successful!"
    else
        echo -e "${RED}✗${NC} Build still failing"
    fi
else
    echo -e "${RED}✗${NC} Docker pull still failing"
    
    echo ""
    echo "Additional troubleshooting steps:"
    echo "1. Check your internet connection"
    echo "2. Check if you're behind a corporate proxy"
    echo "3. Try: docker logout && docker login"
    echo "4. Reset Docker Desktop to factory defaults:"
    echo "   - Docker Desktop → Preferences → Reset → Reset to factory defaults"
fi

echo ""
echo "Current Docker configuration:"
docker info | grep -E "Registry|Server Version|Storage Driver"