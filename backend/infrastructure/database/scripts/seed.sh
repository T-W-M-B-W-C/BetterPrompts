#!/bin/bash

# BetterPrompts Database Seeding Script
# This script loads seed data into the database

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-betterprompts}"
DB_USER="${POSTGRES_USER:-betterprompts}"
DB_PASSWORD="${POSTGRES_PASSWORD:-changeme}"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SEEDS_DIR="$SCRIPT_DIR/../seeds"

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

# Function to check if database exists
check_database() {
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME
}

# Function to run a SQL file
run_sql_file() {
    local file=$1
    print_info "Running $file..."
    
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$file"
    
    if [ $? -eq 0 ]; then
        print_info "Successfully executed $file"
    else
        print_error "Failed to execute $file"
        exit 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            DB_HOST="$2"
            shift 2
            ;;
        --port)
            DB_PORT="$2"
            shift 2
            ;;
        --database)
            DB_NAME="$2"
            shift 2
            ;;
        --user)
            DB_USER="$2"
            shift 2
            ;;
        --password)
            DB_PASSWORD="$2"
            shift 2
            ;;
        --clean)
            CLEAN_FIRST=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --host       Database host (default: localhost)"
            echo "  --port       Database port (default: 5432)"
            echo "  --database   Database name (default: betterprompts)"
            echo "  --user       Database user (default: betterprompts)"
            echo "  --password   Database password (default: changeme)"
            echo "  --clean      Clean existing data before seeding"
            echo "  --help       Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_info "Starting database seeding process..."
print_info "Database: $DB_NAME@$DB_HOST:$DB_PORT"

# Check if database exists
if ! check_database; then
    print_error "Database '$DB_NAME' does not exist!"
    exit 1
fi

# Clean existing data if requested
if [ "$CLEAN_FIRST" = true ]; then
    print_warn "Cleaning existing data..."
    
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME <<-EOSQL
        -- Delete in reverse order of dependencies
        DELETE FROM analytics.api_metrics;
        DELETE FROM analytics.daily_stats;
        DELETE FROM analytics.user_activity;
        DELETE FROM analytics.technique_effectiveness;
        
        DELETE FROM prompts.embeddings;
        DELETE FROM prompts.collection_prompts;
        DELETE FROM prompts.collections;
        DELETE FROM prompts.saved_prompts;
        DELETE FROM prompts.history;
        DELETE FROM prompts.intent_patterns;
        DELETE FROM prompts.templates WHERE created_by IS NOT NULL;
        
        DELETE FROM auth.api_keys;
        DELETE FROM auth.user_preferences;
        DELETE FROM auth.sessions;
        DELETE FROM auth.users WHERE email != 'admin@betterprompts.com';
EOSQL
    
    print_info "Existing data cleaned"
fi

# Run seed files in order
for seed_file in "$SEEDS_DIR"/*.sql; do
    if [ -f "$seed_file" ]; then
        run_sql_file "$seed_file"
    fi
done

# Generate bcrypt password hash for test users
print_info "Generating password hashes..."

# Check if Python is available for bcrypt
if command -v python3 &> /dev/null; then
    python3 <<-EOF
import bcrypt
password = b"TestPassword123!"
hash = bcrypt.hashpw(password, bcrypt.gensalt(10))
print(f"Test user password hash: {hash.decode()}")
print("You can update the seed file with this hash if needed")
EOF
else
    print_warn "Python not found. Using placeholder password hash."
    print_warn "Remember to generate proper bcrypt hashes for production!"
fi

print_info "Database seeding completed successfully!"

# Display some statistics
print_info "Verifying seed data..."

PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t <<-EOSQL
    SELECT 'Users: ' || COUNT(*) FROM auth.users
    UNION ALL
    SELECT 'Intent Patterns: ' || COUNT(*) FROM prompts.intent_patterns
    UNION ALL
    SELECT 'Prompt History: ' || COUNT(*) FROM prompts.history
    UNION ALL
    SELECT 'Templates: ' || COUNT(*) FROM prompts.templates;
EOSQL

print_info "✅ Database is ready for development!"