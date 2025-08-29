#!/bin/bash
# Switch TorchServe between development and production configurations

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

CONFIG_DIR="infrastructure/model-serving/torchserve/config"

# Check current configuration
check_current() {
    if [ -L "$CONFIG_DIR/config.properties" ]; then
        CURRENT=$(readlink "$CONFIG_DIR/config.properties" | xargs basename)
        case $CURRENT in
            config.properties.dev) echo "development" ;;
            config.properties.prod) echo "production" ;;
            *) echo "unknown" ;;
        esac
    else
        echo "unknown"
    fi
}

# Switch to development
switch_to_dev() {
    log_info "Switching to DEVELOPMENT configuration..."
    
    cd "$CONFIG_DIR"
    rm -f config.properties
    ln -sf config.properties.dev config.properties
    cd - > /dev/null
    
    log_info "Updated symbolic link to development config"
    
    # Update docker-compose.override.yml for dev settings
    cat > docker-compose.override.yml << 'EOF'
# Development overrides for TorchServe
version: '3.8'

services:
  torchserve:
    environment:
      # Development: Lower memory usage
      - JAVA_OPTS=-Xmx1g -Xms512m -XX:+UseG1GC -XX:MaxGCPauseMillis=100
      - ENVIRONMENT=development
      # Enable debug logging in dev
      - LOG_LEVEL=DEBUG
EOF
    
    log_info "Created docker-compose.override.yml for development"
    log_info "Development config features:"
    echo "  - Single worker (no batching)"
    echo "  - Minimal latency (batch_delay=0)"
    echo "  - Reduced memory (1GB max)"
    echo "  - Fast startup"
}

# Switch to production
switch_to_prod() {
    log_info "Switching to PRODUCTION configuration..."
    
    cd "$CONFIG_DIR"
    rm -f config.properties
    ln -sf config.properties.prod config.properties
    cd - > /dev/null
    
    log_info "Updated symbolic link to production config"
    
    # Update docker-compose.override.yml for prod settings
    cat > docker-compose.override.yml << 'EOF'
# Production overrides for TorchServe
version: '3.8'

services:
  torchserve:
    environment:
      # Production: Higher memory for better performance
      - JAVA_OPTS=-Xmx4g -Xms2g -XX:+UseG1GC
      - ENVIRONMENT=production
      # Standard logging in prod
      - LOG_LEVEL=INFO
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
EOF
    
    log_info "Created docker-compose.override.yml for production"
    log_info "Production config features:"
    echo "  - Multiple workers (2-4)"
    echo "  - Batch processing enabled"
    echo "  - Higher memory (4GB)"
    echo "  - GPU support"
}

# Show configuration details
show_config() {
    local ENV=$1
    echo -e "\n${BLUE}Configuration Details:${NC}"
    
    if [ "$ENV" = "development" ]; then
        echo "📋 Development Configuration:"
        grep -E "(batch_size|max_batch_delay|Workers|timeout)" "$CONFIG_DIR/config.properties.dev" | head -6
    else
        echo "📋 Production Configuration:"
        grep -E "(batch_size|max_batch_delay|Workers|timeout)" "$CONFIG_DIR/config.properties.prod" | head -6
    fi
}

# Main logic
CURRENT=$(check_current)
echo -e "${BLUE}TorchServe Configuration Manager${NC}"
echo -e "Current configuration: ${YELLOW}$CURRENT${NC}"

if [ $# -eq 0 ]; then
    echo -e "\nUsage: $0 [dev|prod|status]"
    echo "  dev    - Switch to development configuration"
    echo "  prod   - Switch to production configuration"
    echo "  status - Show current configuration"
    exit 0
fi

case "$1" in
    dev|development)
        if [ "$CURRENT" = "development" ]; then
            log_warn "Already using development configuration"
            show_config "development"
        else
            switch_to_dev
            show_config "development"
            echo -e "\n${GREEN}Next steps:${NC}"
            echo "1. Restart TorchServe: docker compose restart torchserve"
            echo "2. Wait ~10 seconds for startup"
            echo "3. Test performance: ./scripts/test-ml-integration.sh"
        fi
        ;;
    
    prod|production)
        if [ "$CURRENT" = "production" ]; then
            log_warn "Already using production configuration"
            show_config "production"
        else
            switch_to_prod
            show_config "production"
            echo -e "\n${GREEN}Next steps:${NC}"
            echo "1. Restart TorchServe: docker compose restart torchserve"
            echo "2. Wait ~30 seconds for startup"
            echo "3. Run health checks: curl http://localhost:8080/ping"
        fi
        ;;
    
    status)
        echo -e "\n${BLUE}Current Status:${NC}"
        echo "Configuration: $CURRENT"
        show_config "$CURRENT"
        
        # Check if TorchServe is running
        if docker compose ps torchserve | grep -q "Up"; then
            echo -e "\n${GREEN}TorchServe is running${NC}"
            
            # Test inference speed
            echo -e "\nTesting inference speed..."
            START=$(date +%s.%N)
            curl -s -X POST http://localhost:8080/predictions/intent_classifier \
                -H "Content-Type: application/json" \
                -d '{"text": "test"}' > /dev/null 2>&1
            END=$(date +%s.%N)
            TIME=$(echo "$END - $START" | bc)
            echo "Inference time: ${TIME}s"
        else
            echo -e "\n${RED}TorchServe is not running${NC}"
        fi
        ;;
    
    *)
        log_error "Invalid option: $1"
        echo "Use: $0 [dev|prod|status]"
        exit 1
        ;;
esac