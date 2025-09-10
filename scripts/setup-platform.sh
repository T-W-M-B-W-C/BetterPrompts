#!/bin/bash

# BetterPrompts Platform Detection and Setup Script
# Automatically configures Docker environment for Intel vs ARM Macs

set -e

echo "🔍 Detecting platform and configuring Docker environment..."

# Detect architecture and OS
ARCH=$(uname -m)
OS=$(uname -s)

echo "Detected: $OS $ARCH"

# Set platform-specific variables
if [[ "$OS" == "Darwin" && "$ARCH" == "arm64" ]]; then
    echo "🍎 Apple Silicon Mac detected"
    DOCKER_PLATFORM="linux/arm64"
    PYTORCH_INDEX_URL=""
    ENV_FILE=".env.arm64"
    COMPOSE_OVERRIDE="docker-compose.arm64.yml"
    
elif [[ "$OS" == "Darwin" && "$ARCH" == "x86_64" ]]; then
    echo "💻 Intel Mac detected" 
    DOCKER_PLATFORM="linux/amd64"
    PYTORCH_INDEX_URL="https://download.pytorch.org/whl/cpu"
    ENV_FILE=".env.intel"
    COMPOSE_OVERRIDE="docker-compose.intel.yml"
    
elif [[ "$OS" == "Linux" && "$ARCH" == "x86_64" ]]; then
    echo "🐧 Linux x86_64 detected"
    DOCKER_PLATFORM="linux/amd64" 
    PYTORCH_INDEX_URL="https://download.pytorch.org/whl/cpu"
    ENV_FILE=".env.intel"
    COMPOSE_OVERRIDE="docker-compose.intel.yml"
    
elif [[ "$OS" == "Linux" && "$ARCH" == "aarch64" ]]; then
    echo "🐧 Linux ARM64 detected"
    DOCKER_PLATFORM="linux/arm64"
    PYTORCH_INDEX_URL=""
    ENV_FILE=".env.arm64" 
    COMPOSE_OVERRIDE="docker-compose.arm64.yml"
    
else
    echo "⚠️  Unknown platform: $OS $ARCH"
    echo "Defaulting to x86_64 configuration"
    DOCKER_PLATFORM="linux/amd64"
    PYTORCH_INDEX_URL="https://download.pytorch.org/whl/cpu"
    ENV_FILE=".env.intel"
    COMPOSE_OVERRIDE="docker-compose.intel.yml"
fi

# Check if architecture-specific env file exists
if [[ ! -f "$ENV_FILE" ]]; then
    echo "📝 Creating $ENV_FILE from template..."
    if [[ -f ".env.example" ]]; then
        cp .env.example "$ENV_FILE"
    else
        echo "❌ Error: .env.example not found"
        exit 1
    fi
fi

# Copy architecture-specific env to main .env
echo "📋 Configuring .env for $ARCH architecture..."
cp "$ENV_FILE" .env

# Add platform-specific variables to .env
echo "" >> .env
echo "# Platform Configuration (auto-generated)" >> .env
echo "DOCKER_PLATFORM=$DOCKER_PLATFORM" >> .env
echo "PYTORCH_INDEX_URL=$PYTORCH_INDEX_URL" >> .env
echo "COMPOSE_OVERRIDE=$COMPOSE_OVERRIDE" >> .env

# Enable Docker buildx if not already enabled
if ! docker buildx ls | grep -q multiarch; then
    echo "🔧 Setting up Docker buildx for multi-platform builds..."
    docker buildx create --use --name multiarch --driver docker-container || true
fi

# Create docker-compose override command
COMPOSE_CMD="docker compose"
if [[ -f "$COMPOSE_OVERRIDE" ]]; then
    COMPOSE_CMD="docker compose -f docker-compose.yml -f $COMPOSE_OVERRIDE"
fi

echo ""
echo "✅ Platform configuration complete!"
echo ""
echo "📊 Configuration Summary:"
echo "  Platform: $DOCKER_PLATFORM"
echo "  Environment: $ENV_FILE"
echo "  Override: $COMPOSE_OVERRIDE"
echo ""
echo "🚀 To start the application:"
echo "  $COMPOSE_CMD up -d"
echo ""
echo "🔍 To check service status:"
echo "  $COMPOSE_CMD ps"
echo ""
echo "📝 Your .env file has been configured for your platform."
echo "   Edit it to add your API keys and customize settings."