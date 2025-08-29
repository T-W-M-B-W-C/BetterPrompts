#!/bin/bash
# Deployment script for TorchServe infrastructure

set -euo pipefail

# Configuration
ENVIRONMENT="${1:-staging}"
MODEL_VERSION="${2:-latest}"
DEPLOYMENT_STRATEGY="${3:-rolling}"
NAMESPACE="model-serving"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check required tools
    for tool in kubectl kustomize aws docker; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool is required but not installed"
            exit 1
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured"
        exit 1
    fi
    
    # Check kubectl context
    if ! kubectl config current-context &> /dev/null; then
        log_error "kubectl context not configured"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    # Build image
    docker build \
        -t betterprompts/torchserve:${MODEL_VERSION} \
        -f infrastructure/model-serving/docker/Dockerfile.torchserve \
        infrastructure/model-serving/
    
    # Tag and push to ECR
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"
    
    aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $ECR_REGISTRY
    
    docker tag betterprompts/torchserve:${MODEL_VERSION} ${ECR_REGISTRY}/betterprompts/torchserve:${MODEL_VERSION}
    docker push ${ECR_REGISTRY}/betterprompts/torchserve:${MODEL_VERSION}
    
    log_info "Image pushed successfully"
}

deploy_infrastructure() {
    log_info "Deploying infrastructure to ${ENVIRONMENT}..."
    
    cd infrastructure/model-serving/kubernetes/overlays/${ENVIRONMENT}
    
    # Update image tag
    kustomize edit set image betterprompts/torchserve=betterprompts/torchserve:${MODEL_VERSION}
    
    # Dry run first
    log_info "Running dry-run..."
    kubectl apply -k . --dry-run=client
    
    # Apply based on strategy
    case $DEPLOYMENT_STRATEGY in
        rolling)
            log_info "Performing rolling deployment..."
            kubectl apply -k .
            kubectl rollout status deployment/torchserve -n $NAMESPACE --timeout=10m
            ;;
        canary)
            log_info "Performing canary deployment..."
            # Implement canary deployment logic
            kubectl apply -k . --selector="app=torchserve,canary=true"
            sleep 30
            # Monitor metrics before full rollout
            kubectl apply -k .
            ;;
        blue-green)
            log_info "Performing blue-green deployment..."
            # Implement blue-green deployment logic
            kubectl apply -k . --selector="app=torchserve,version=blue"
            kubectl wait --for=condition=ready pod -l app=torchserve,version=blue -n $NAMESPACE --timeout=5m
            # Switch traffic
            kubectl patch service torchserve -n $NAMESPACE -p '{"spec":{"selector":{"version":"blue"}}}'
            ;;
    esac
    
    log_info "Deployment completed"
}

run_smoke_tests() {
    log_info "Running smoke tests..."
    
    # Get service endpoint
    if [ "$ENVIRONMENT" = "production" ]; then
        ENDPOINT="https://models.betterprompts.com"
    else
        ENDPOINT=$(kubectl get ingress torchserve -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    fi
    
    # Health check
    if ! curl -f ${ENDPOINT}/health; then
        log_error "Health check failed"
        return 1
    fi
    
    # Test inference
    RESPONSE=$(curl -s -X POST ${ENDPOINT}/predictions/intent_classifier \
        -H "Content-Type: application/json" \
        -d '{"text": "How do I create a React component?"}')
    
    if ! echo $RESPONSE | jq -e '.intent'; then
        log_error "Inference test failed"
        return 1
    fi
    
    log_info "Smoke tests passed"
}

update_monitoring() {
    log_info "Updating monitoring configuration..."
    
    # Apply monitoring resources
    kubectl apply -f infrastructure/model-serving/monitoring/
    
    # Reload Prometheus configuration
    kubectl rollout restart deployment/prometheus -n monitoring
    
    log_info "Monitoring updated"
}

main() {
    log_info "Starting deployment process..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Model Version: $MODEL_VERSION"
    log_info "Strategy: $DEPLOYMENT_STRATEGY"
    
    check_prerequisites
    build_and_push_image
    deploy_infrastructure
    
    # Wait for pods to be ready
    log_info "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod -l app=torchserve -n $NAMESPACE --timeout=5m
    
    # Run tests
    if run_smoke_tests; then
        log_info "Deployment successful!"
        update_monitoring
    else
        log_error "Deployment failed smoke tests"
        log_warn "Rolling back..."
        kubectl rollout undo deployment/torchserve -n $NAMESPACE
        exit 1
    fi
}

# Run main function
main