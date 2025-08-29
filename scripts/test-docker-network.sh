#!/bin/bash

# Quick Docker Network Test
echo "🔍 Quick Docker Network Test"
echo "==========================="

# Test 1: Basic Docker
echo -n "1. Docker running: "
docker version > /dev/null 2>&1 && echo "✓ YES" || echo "✗ NO"

# Test 2: Internet connectivity
echo -n "2. Internet access: "
ping -c 1 google.com > /dev/null 2>&1 && echo "✓ YES" || echo "✗ NO"

# Test 3: Docker Hub
echo -n "3. Docker Hub access: "
curl -s -o /dev/null -w "%{http_code}" https://hub.docker.com/ | grep -q "200" && echo "✓ YES" || echo "✗ NO"

# Test 4: DNS
echo -n "4. DNS resolution: "
host registry-1.docker.io > /dev/null 2>&1 && echo "✓ YES" || echo "✗ NO"

# Test 5: Try pulling a small image
echo -n "5. Docker pull test: "
docker pull hello-world:latest > /dev/null 2>&1 && echo "✓ YES" || echo "✗ NO"

echo ""
echo "If any tests fail, try:"
echo "1. Restart Docker Desktop"
echo "2. Check Docker Desktop → Preferences → Resources → Network"
echo "3. Reset Docker Desktop to factory defaults"
echo "4. Check if behind a proxy/firewall"