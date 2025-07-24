#!/bin/bash
# BetterPrompts Demo Runner Script
# This script provides an easy way to run various demo scenarios

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Demo credentials
DEMO_USER="demo"
DEMO_PASS="DemoPass123!"
API_URL="http://localhost/api/v1"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if services are running
check_services() {
    print_info "Checking if services are running..."
    
    if ! docker compose ps | grep -q "Up"; then
        print_error "Services are not running. Starting them now..."
        docker compose up -d
        print_info "Waiting 30 seconds for services to start..."
        sleep 30
    else
        print_success "Services are running"
    fi
}

# Function to get auth token
get_auth_token() {
    print_info "Authenticating with demo user..."
    
    # Create temp file for login payload
    cat > /tmp/login.json << EOF
{
    "email_or_username": "$DEMO_USER",
    "password": "$DEMO_PASS"
}
EOF
    
    # Attempt login
    RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d @/tmp/login.json)
    
    # Extract token
    TOKEN=$(echo "$RESPONSE" | jq -r '.access_token' 2>/dev/null || echo "")
    
    if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        print_error "Failed to authenticate. Response: $RESPONSE"
        rm -f /tmp/login.json
        return 1
    fi
    
    print_success "Authentication successful"
    rm -f /tmp/login.json
    echo "$TOKEN"
}

# Demo 1: Basic Enhancement
demo_basic_enhancement() {
    echo ""
    echo "========================================="
    echo "DEMO 1: Basic Prompt Enhancement"
    echo "========================================="
    
    TOKEN=$(get_auth_token)
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    print_info "Enhancing prompt: 'explain quantum computing to a 5 year old'"
    
    RESPONSE=$(curl -s -X POST "$API_URL/enhance" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "text": "explain quantum computing to a 5 year old"
        }')
    
    echo ""
    echo "Response:"
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
}

# Demo 2: Context-Aware Enhancement
demo_context_enhancement() {
    echo ""
    echo "========================================="
    echo "DEMO 2: Context-Aware Enhancement"
    echo "========================================="
    
    TOKEN=$(get_auth_token)
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    print_info "Enhancing prompt with context: 'write a function to calculate fibonacci'"
    
    RESPONSE=$(curl -s -X POST "$API_URL/enhance" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "text": "write a function to calculate fibonacci",
            "context": {
                "language": "python",
                "level": "beginner"
            }
        }')
    
    echo ""
    echo "Response:"
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
}

# Demo 3: Multiple Enhancement Examples
demo_multiple_enhancements() {
    echo ""
    echo "========================================="
    echo "DEMO 3: Multiple Enhancement Examples"
    echo "========================================="
    
    TOKEN=$(get_auth_token)
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    PROMPTS=(
        "how do I learn machine learning"
        "debug this code"
        "explain recursion"
        "write unit tests"
        "optimize database queries"
    )
    
    for prompt in "${PROMPTS[@]}"; do
        print_info "Enhancing: '$prompt'"
        
        RESPONSE=$(curl -s -X POST "$API_URL/enhance" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{\"text\": \"$prompt\"}")
        
        # Extract enhanced prompt and techniques
        ENHANCED=$(echo "$RESPONSE" | jq -r '.enhanced_prompt' 2>/dev/null || echo "N/A")
        TECHNIQUES=$(echo "$RESPONSE" | jq -r '.techniques[]' 2>/dev/null | tr '\n' ', ' || echo "N/A")
        
        if [ "$ENHANCED" != "N/A" ] && [ "$ENHANCED" != "null" ]; then
            print_success "Enhanced successfully"
            echo "Techniques used: ${TECHNIQUES%,}"
        else
            print_error "Enhancement failed"
            echo "Response: $RESPONSE"
        fi
        echo ""
    done
}

# Demo 4: Service Health Check
demo_health_check() {
    echo ""
    echo "========================================="
    echo "DEMO 4: Service Health Status"
    echo "========================================="
    
    print_info "Checking all service health endpoints..."
    echo ""
    
    # Check main services
    SERVICES=(
        "Frontend|http://localhost:3000/api/healthcheck"
        "API Gateway|$API_URL/health"
        "Nginx|http://localhost/health"
        "Intent Classifier|http://localhost:8001/health"
        "Technique Selector|http://localhost:8002/health"
        "Prompt Generator|http://localhost:8003/health/ready"
    )
    
    for service in "${SERVICES[@]}"; do
        IFS='|' read -r name url <<< "$service"
        printf "%-20s: " "$name"
        
        STATUS=$(curl -s "$url" | jq -r '.status' 2>/dev/null || echo "")
        
        if [ "$STATUS" = "healthy" ] || [ "$STATUS" = "ok" ]; then
            print_success "Healthy"
        else
            print_error "Unhealthy or Not Responding"
        fi
    done
}

# Demo 5: Performance Test
demo_performance() {
    echo ""
    echo "========================================="
    echo "DEMO 5: Performance Test"
    echo "========================================="
    
    TOKEN=$(get_auth_token)
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    print_info "Running 10 enhancement requests to measure performance..."
    
    TOTAL_TIME=0
    SUCCESS_COUNT=0
    
    for i in {1..10}; do
        START=$(date +%s%N)
        
        RESPONSE=$(curl -s -X POST "$API_URL/enhance" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{\"text\": \"test prompt $i\"}" \
            -w "\n%{http_code}")
        
        HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
        END=$(date +%s%N)
        
        DURATION=$((($END - $START) / 1000000))
        TOTAL_TIME=$((TOTAL_TIME + DURATION))
        
        if [ "$HTTP_CODE" = "200" ]; then
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            echo "Request $i: ${DURATION}ms ✓"
        else
            echo "Request $i: Failed (HTTP $HTTP_CODE)"
        fi
    done
    
    AVG_TIME=$((TOTAL_TIME / 10))
    print_info "Average response time: ${AVG_TIME}ms"
    print_info "Success rate: $SUCCESS_COUNT/10"
}

# Interactive menu
show_menu() {
    echo ""
    echo "========================================="
    echo "BetterPrompts Demo Runner"
    echo "========================================="
    echo "1) Basic Enhancement Demo"
    echo "2) Context-Aware Enhancement Demo"
    echo "3) Multiple Enhancement Examples"
    echo "4) Service Health Check"
    echo "5) Performance Test"
    echo "6) Run All Demos"
    echo "7) Exit"
    echo ""
    read -p "Select demo to run (1-7): " choice
}

# Main execution
main() {
    print_info "BetterPrompts Demo Runner"
    check_services
    
    if [ "$1" == "--all" ]; then
        demo_basic_enhancement
        demo_context_enhancement
        demo_multiple_enhancements
        demo_health_check
        demo_performance
        exit 0
    fi
    
    while true; do
        show_menu
        
        case $choice in
            1)
                demo_basic_enhancement
                ;;
            2)
                demo_context_enhancement
                ;;
            3)
                demo_multiple_enhancements
                ;;
            4)
                demo_health_check
                ;;
            5)
                demo_performance
                ;;
            6)
                demo_basic_enhancement
                demo_context_enhancement
                demo_multiple_enhancements
                demo_health_check
                demo_performance
                ;;
            7)
                print_info "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please select 1-7."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main function with all arguments
main "$@"