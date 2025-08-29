#!/bin/bash

# BetterPrompts Database Integration Test Runner
# This script runs all database integration tests

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
TEST_DB_NAME="${TEST_DB_NAME:-betterprompts_test}"
DB_USER="${POSTGRES_USER:-betterprompts}"
DB_PASSWORD="${POSTGRES_PASSWORD:-changeme}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../../../.."

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

# Function to check if database exists
check_database() {
    local db_name=$1
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $db_name
}

# Function to create test database
create_test_database() {
    print_info "Creating test database '$TEST_DB_NAME'..."
    
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres <<-EOSQL
        -- Drop existing test database if exists
        DROP DATABASE IF EXISTS $TEST_DB_NAME;
        
        -- Create test database
        CREATE DATABASE $TEST_DB_NAME 
            WITH OWNER = $DB_USER
            ENCODING = 'UTF8'
            LC_COLLATE = 'en_US.UTF-8'
            LC_CTYPE = 'en_US.UTF-8';
        
        -- Grant permissions
        GRANT ALL PRIVILEGES ON DATABASE $TEST_DB_NAME TO $DB_USER;
EOSQL
    
    print_info "Test database created successfully"
}

# Function to apply migrations to test database
apply_migrations() {
    print_info "Applying migrations to test database..."
    
    # Run migrations
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB_NAME \
        -f "$SCRIPT_DIR/../migrations/001_initial_schema.sql"
    
    print_info "Migrations applied successfully"
}

# Function to load test seed data
load_test_data() {
    print_info "Loading test seed data..."
    
    # Run seed data with modified test-specific values
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB_NAME <<-EOSQL
        -- Insert minimal test data
        INSERT INTO auth.users (id, email, username, password_hash, is_active, is_verified) 
        VALUES 
        ('test-user-001', 'testuser@example.com', 'testuser', 
         '\$2a\$10\$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gOMxlIVTu', true, true);
        
        INSERT INTO prompts.templates (name, slug, technique, template_text, variables) 
        VALUES 
        ('Test Template', 'test-template', 'chain_of_thought', 
         'Test template: {input}', '["input"]'::jsonb);
EOSQL
    
    print_info "Test data loaded successfully"
}

# Function to run Go tests
run_go_tests() {
    print_section "Running Go Integration Tests"
    
    cd "$PROJECT_ROOT/backend/services/api-gateway"
    
    # Export test database URL
    export TEST_DATABASE_URL="postgres://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$TEST_DB_NAME?sslmode=disable"
    
    print_info "Running database integration tests..."
    go test -v ./internal/services/... -run "TestDatabase" -tags=integration || {
        print_error "Go tests failed"
        return 1
    }
    
    print_info "✅ Go tests passed"
}

# Function to run Python tests
run_python_tests() {
    print_section "Running Python Integration Tests"
    
    cd "$PROJECT_ROOT/backend/services/intent-classifier"
    
    # Export test environment variables
    export TEST_DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$TEST_DB_NAME"
    export REDIS_HOST=$REDIS_HOST
    export REDIS_PORT=$REDIS_PORT
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        print_info "Activating Python virtual environment..."
        source venv/bin/activate
    fi
    
    print_info "Running database integration tests..."
    python -m pytest tests/test_database_integration.py -v -s || {
        print_error "Python tests failed"
        return 1
    }
    
    print_info "✅ Python tests passed"
}

# Function to run Redis tests
run_redis_tests() {
    print_section "Testing Redis Connection"
    
    # Test Redis connectivity
    redis-cli -h $REDIS_HOST -p $REDIS_PORT ping > /dev/null 2>&1 || {
        print_error "Redis is not running or not accessible"
        return 1
    }
    
    print_info "✅ Redis connection successful"
}

# Function to generate test report
generate_report() {
    print_section "Test Summary"
    
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB_NAME -t <<-EOSQL
        SELECT 'Test Users: ' || COUNT(*) FROM auth.users
        UNION ALL
        SELECT 'Test Sessions: ' || COUNT(*) FROM auth.sessions
        UNION ALL
        SELECT 'Test Prompts: ' || COUNT(*) FROM prompts.history
        UNION ALL
        SELECT 'Test Patterns: ' || COUNT(*) FROM prompts.intent_patterns;
EOSQL
}

# Parse command line arguments
RUN_GO=true
RUN_PYTHON=true
KEEP_DB=false
SKIP_SETUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --go-only)
            RUN_PYTHON=false
            shift
            ;;
        --python-only)
            RUN_GO=false
            shift
            ;;
        --keep-db)
            KEEP_DB=true
            shift
            ;;
        --skip-setup)
            SKIP_SETUP=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --go-only      Run only Go tests"
            echo "  --python-only  Run only Python tests"
            echo "  --keep-db      Keep test database after tests"
            echo "  --skip-setup   Skip database setup (assume it exists)"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Main execution
print_section "BetterPrompts Database Integration Tests"
print_info "Test Database: $TEST_DB_NAME@$DB_HOST:$DB_PORT"
print_info "Redis: $REDIS_HOST:$REDIS_PORT"

# Setup test database
if [ "$SKIP_SETUP" = false ]; then
    create_test_database
    apply_migrations
    load_test_data
else
    print_warn "Skipping database setup"
fi

# Run tests
TESTS_PASSED=true

# Check Redis
run_redis_tests || TESTS_PASSED=false

# Run Go tests
if [ "$RUN_GO" = true ]; then
    run_go_tests || TESTS_PASSED=false
fi

# Run Python tests
if [ "$RUN_PYTHON" = true ]; then
    run_python_tests || TESTS_PASSED=false
fi

# Generate report
if [ "$TESTS_PASSED" = true ]; then
    generate_report
    print_section "✅ All Tests Passed!"
else
    print_section "❌ Some Tests Failed"
fi

# Cleanup
if [ "$KEEP_DB" = false ] && [ "$SKIP_SETUP" = false ]; then
    print_info "Cleaning up test database..."
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $TEST_DB_NAME;"
    print_info "Test database cleaned up"
else
    print_warn "Test database '$TEST_DB_NAME' preserved"
fi

# Exit with appropriate code
if [ "$TESTS_PASSED" = true ]; then
    exit 0
else
    exit 1
fi