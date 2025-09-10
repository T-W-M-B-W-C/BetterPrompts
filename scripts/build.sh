#!/bin/bash

# BetterPrompts Multi-Architecture Build Script
# Builds Docker images for both Intel and ARM architectures

set -e

echo "🔧 BetterPrompts Multi-Architecture Build Script"
echo "=================================================="

# Default values
BUILD_TARGET="all"
PUSH_IMAGES=false
REGISTRY="docker.io/betterprompts"
VERSION="latest"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --target|-t)
      BUILD_TARGET="$2"
      shift 2
      ;;
    --push|-p)
      PUSH_IMAGES=true
      shift
      ;;
    --registry|-r)
      REGISTRY="$2"
      shift 2
      ;;
    --version|-v)
      VERSION="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --target, -t TARGET     Build target (all|service-name) [default: all]"
      echo "  --push, -p              Push images to registry"
      echo "  --registry, -r REGISTRY Docker registry [default: docker.io/betterprompts]"
      echo "  --version, -v VERSION   Image version tag [default: latest]"
      echo "  --help, -h              Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0                                    # Build all services"
      echo "  $0 --target api-gateway              # Build only API gateway"
      echo "  $0 --push --version v1.0.0           # Build and push with version tag"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Detect platform
ARCH=$(uname -m)
OS=$(uname -s)

echo "🔍 Detected platform: $OS $ARCH"

# Set platform-specific variables
if [[ "$OS" == "Darwin" && "$ARCH" == "arm64" ]]; then
    PRIMARY_PLATFORM="linux/arm64"
    echo "🍎 Building for Apple Silicon (ARM64)"
elif [[ "$OS" == "Darwin" && "$ARCH" == "x86_64" ]]; then
    PRIMARY_PLATFORM="linux/amd64"
    echo "💻 Building for Intel Mac (AMD64)"
elif [[ "$OS" == "Linux" && "$ARCH" == "x86_64" ]]; then
    PRIMARY_PLATFORM="linux/amd64"
    echo "🐧 Building for Linux AMD64"
elif [[ "$OS" == "Linux" && "$ARCH" == "aarch64" ]]; then
    PRIMARY_PLATFORM="linux/arm64"
    echo "🐧 Building for Linux ARM64"
else
    PRIMARY_PLATFORM="linux/amd64"
    echo "⚠️  Unknown platform, defaulting to AMD64"
fi

# Check if buildx is available and setup
if ! docker buildx ls | grep -q multiarch; then
    echo "🔧 Setting up Docker buildx for multi-platform builds..."
    docker buildx create --use --name multiarch --driver docker-container
fi

# Export build variables
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Function to build a service
build_service() {
    local service_name=$1
    local dockerfile_path=$2
    local context_path=$3
    local build_args=$4
    
    echo ""
    echo "🏗️  Building $service_name..."
    echo "   Platform: $PRIMARY_PLATFORM"
    echo "   Context: $context_path"
    echo "   Dockerfile: $dockerfile_path"
    
    # Build command
    local build_cmd="docker buildx build"
    build_cmd="$build_cmd --platform $PRIMARY_PLATFORM"
    build_cmd="$build_cmd --file $dockerfile_path"
    build_cmd="$build_cmd --tag $REGISTRY/$service_name:$VERSION"
    build_cmd="$build_cmd --tag $REGISTRY/$service_name:latest"
    
    # Add build args if provided
    if [[ -n "$build_args" ]]; then
        build_cmd="$build_cmd $build_args"
    fi
    
    # Add push flag if requested
    if [[ "$PUSH_IMAGES" == "true" ]]; then
        build_cmd="$build_cmd --push"
    else
        build_cmd="$build_cmd --load"
    fi
    
    build_cmd="$build_cmd $context_path"
    
    echo "   Command: $build_cmd"
    eval $build_cmd
    
    if [[ $? -eq 0 ]]; then
        echo "✅ Successfully built $service_name"
    else
        echo "❌ Failed to build $service_name"
        exit 1
    fi
}

# Function to set architecture-specific build args
get_build_args() {
    local service_name=$1
    local args=""
    
    case $service_name in
        "intent-classifier")
            if [[ "$PRIMARY_PLATFORM" == "linux/amd64" ]]; then
                args="--build-arg PYTORCH_INDEX_URL=https://download.pytorch.org/whl/cpu"
            else
                args="--build-arg PYTORCH_INDEX_URL="
            fi
            ;;
        "torchserve")
            args="--build-arg TORCHSERVE_VERSION=0.9.0 --build-arg BASE_IMAGE_TYPE=cpu"
            ;;
    esac
    
    echo "$args"
}

# Build services based on target
case $BUILD_TARGET in
    "all")
        echo "🚀 Building all services for $PRIMARY_PLATFORM..."
        
        # Build backend services
        build_service "api-gateway" \
            "./backend/services/api-gateway/Dockerfile" \
            "./backend/services/api-gateway" \
            "$(get_build_args api-gateway)"
            
        build_service "intent-classifier" \
            "./backend/services/intent-classifier/Dockerfile" \
            "./backend/services/intent-classifier" \
            "$(get_build_args intent-classifier)"
            
        build_service "technique-selector" \
            "./docker/backend/technique-selector/Dockerfile" \
            "./backend/services/technique-selector" \
            "$(get_build_args technique-selector)"
            
        build_service "prompt-generator" \
            "./docker/backend/prompt-generator/Dockerfile" \
            "." \
            "$(get_build_args prompt-generator)"
            
        # Build infrastructure services
        build_service "torchserve" \
            "./infrastructure/model-serving/docker/Dockerfile.torchserve" \
            "./infrastructure/model-serving" \
            "$(get_build_args torchserve)"
            
        build_service "nginx" \
            "./docker/nginx/Dockerfile" \
            "./docker/nginx" \
            "$(get_build_args nginx)"
        ;;
        
    "api-gateway")
        build_service "api-gateway" \
            "./backend/services/api-gateway/Dockerfile" \
            "./backend/services/api-gateway" \
            "$(get_build_args api-gateway)"
        ;;
        
    "intent-classifier")
        build_service "intent-classifier" \
            "./backend/services/intent-classifier/Dockerfile" \
            "./backend/services/intent-classifier" \
            "$(get_build_args intent-classifier)"
        ;;
        
    "technique-selector")
        build_service "technique-selector" \
            "./docker/backend/technique-selector/Dockerfile" \
            "./backend/services/technique-selector" \
            "$(get_build_args technique-selector)"
        ;;
        
    "prompt-generator")
        build_service "prompt-generator" \
            "./docker/backend/prompt-generator/Dockerfile" \
            "." \
            "$(get_build_args prompt-generator)"
        ;;
        
    "torchserve")
        build_service "torchserve" \
            "./infrastructure/model-serving/docker/Dockerfile.torchserve" \
            "./infrastructure/model-serving" \
            "$(get_build_args torchserve)"
        ;;
        
    "nginx")
        build_service "nginx" \
            "./docker/nginx/Dockerfile" \
            "./docker/nginx" \
            "$(get_build_args nginx)"
        ;;
        
    *)
        echo "❌ Unknown build target: $BUILD_TARGET"
        echo "Available targets: all, api-gateway, intent-classifier, technique-selector, prompt-generator, torchserve, nginx"
        exit 1
        ;;
esac

echo ""
echo "🎉 Build completed successfully!"

if [[ "$PUSH_IMAGES" == "true" ]]; then
    echo "📤 Images have been pushed to $REGISTRY"
else
    echo "💾 Images are available locally"
    echo "🚀 To start the application:"
    echo "   ./scripts/setup-platform.sh && docker compose up -d"
fi

echo ""
echo "📊 Build Summary:"
echo "   Target: $BUILD_TARGET"
echo "   Platform: $PRIMARY_PLATFORM"
echo "   Registry: $REGISTRY"
echo "   Version: $VERSION"
echo "   Pushed: $PUSH_IMAGES"