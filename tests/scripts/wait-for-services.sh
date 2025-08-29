#!/bin/bash
# Wait for all services to be healthy before running tests

set -e

echo "⏳ Waiting for services to be ready..."

# Configuration
MAX_WAIT=300  # 5 minutes
SLEEP_TIME=2

# Services to check
declare -A SERVICES=(
    ["PostgreSQL"]="test-postgres:5432"
    ["Redis"]="test-redis:6379"
    ["API Gateway"]="api-gateway:8080/health"
    ["Intent Classifier"]="intent-classifier:8001/health"
    ["Technique Selector"]="technique-selector:8002/health"
    ["Prompt Generator"]="prompt-generator:8003/health"
    ["Frontend"]="frontend-test:3000"
    ["Mock TorchServe"]="mock-torchserve:8080/ping"
)

# Function to check if a service is ready
check_service() {
    local name=$1
    local endpoint=$2
    
    if [[ $endpoint == *":"* ]] && [[ $endpoint != *"/"* ]]; then
        # It's a host:port combination, use nc
        local host=$(echo $endpoint | cut -d: -f1)
        local port=$(echo $endpoint | cut -d: -f2)
        nc -z "$host" "$port" 2>/dev/null
    else
        # It's an HTTP endpoint, use curl
        curl -s -f "http://$endpoint" > /dev/null 2>&1
    fi
}

# Check each service
TOTAL_WAIT=0
ALL_READY=false

while [ $TOTAL_WAIT -lt $MAX_WAIT ]; do
    ALL_SERVICES_UP=true
    
    for service in "${!SERVICES[@]}"; do
        endpoint="${SERVICES[$service]}"
        
        if check_service "$service" "$endpoint"; then
            echo "✅ $service is ready"
        else
            echo "⏳ Waiting for $service..."
            ALL_SERVICES_UP=false
        fi
    done
    
    if [ "$ALL_SERVICES_UP" = true ]; then
        ALL_READY=true
        break
    fi
    
    sleep $SLEEP_TIME
    TOTAL_WAIT=$((TOTAL_WAIT + SLEEP_TIME))
    echo "Waited ${TOTAL_WAIT}s..."
done

if [ "$ALL_READY" = true ]; then
    echo "✅ All services are ready!"
    exit 0
else
    echo "❌ Timeout waiting for services after ${MAX_WAIT}s"
    echo "Check docker compose logs for more information"
    exit 1
fi