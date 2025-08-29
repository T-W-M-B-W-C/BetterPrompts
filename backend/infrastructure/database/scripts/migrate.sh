#!/bin/bash

# BetterPrompts Database Migration Runner
# This script manages database migrations

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
DB_NAME="${POSTGRES_DB:-betterprompts}"
DB_USER="${POSTGRES_USER:-betterprompts}"
DB_PASSWORD="${POSTGRES_PASSWORD:-changeme}"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MIGRATIONS_DIR="$SCRIPT_DIR/../migrations"

# Migration tracking
CURRENT_VERSION=0
TARGET_VERSION=0

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

# Function to get current migration version
get_current_version() {
    local version=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c \
        "SELECT COALESCE(MAX(version), 0) FROM public.schema_migrations;" 2>/dev/null || echo "0")
    
    # Trim whitespace
    version=$(echo $version | xargs)
    
    # Return 0 if table doesn't exist
    if [[ "$version" == *"ERROR"* ]] || [[ -z "$version" ]]; then
        echo "0"
    else
        echo "$version"
    fi
}

# Function to get available migrations
get_available_migrations() {
    local migrations=()
    
    for file in "$MIGRATIONS_DIR"/*.sql; do
        if [ -f "$file" ]; then
            # Extract version number from filename (e.g., 001_initial_schema.sql -> 1)
            local filename=$(basename "$file")
            local version=$(echo "$filename" | grep -o '^[0-9]\+' | sed 's/^0*//')
            
            if [ -n "$version" ]; then
                migrations+=("$version:$file")
            fi
        fi
    done
    
    # Sort by version number
    printf '%s\n' "${migrations[@]}" | sort -n -t: -k1
}

# Function to run a single migration
run_migration() {
    local version=$1
    local file=$2
    local filename=$(basename "$file")
    
    print_info "Running migration $version: $filename"
    
    # Begin transaction
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME <<-EOSQL
BEGIN;

-- Run the migration file
\i $file

-- Record the migration
INSERT INTO public.schema_migrations (version, applied_at) 
VALUES ($version, CURRENT_TIMESTAMP);

COMMIT;
EOSQL
    
    if [ $? -eq 0 ]; then
        print_info "✅ Migration $version applied successfully"
        return 0
    else
        print_error "❌ Migration $version failed"
        return 1
    fi
}

# Function to rollback a migration
rollback_migration() {
    local version=$1
    local rollback_file="$MIGRATIONS_DIR/rollback_${version}.sql"
    
    if [ ! -f "$rollback_file" ]; then
        print_error "Rollback file not found: $rollback_file"
        print_warn "Manual rollback may be required"
        return 1
    fi
    
    print_info "Rolling back migration $version"
    
    # Begin transaction
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME <<-EOSQL
BEGIN;

-- Run the rollback file
\i $rollback_file

-- Remove the migration record
DELETE FROM public.schema_migrations WHERE version = $version;

COMMIT;
EOSQL
    
    if [ $? -eq 0 ]; then
        print_info "✅ Migration $version rolled back successfully"
        return 0
    else
        print_error "❌ Rollback of migration $version failed"
        return 1
    fi
}

# Function to create migration tracking table
create_migration_table() {
    print_info "Creating migration tracking table..."
    
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME <<-EOSQL
CREATE TABLE IF NOT EXISTS public.schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
EOSQL
    
    if [ $? -eq 0 ]; then
        print_info "Migration tracking table ready"
    else
        print_error "Failed to create migration tracking table"
        exit 1
    fi
}

# Function to show migration status
show_status() {
    print_section "Migration Status"
    
    CURRENT_VERSION=$(get_current_version)
    print_info "Current version: $CURRENT_VERSION"
    
    print_info "\nApplied migrations:"
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \
        "SELECT version, applied_at FROM public.schema_migrations ORDER BY version;"
    
    print_info "\nAvailable migrations:"
    local migrations=($(get_available_migrations))
    for migration in "${migrations[@]}"; do
        IFS=':' read -r version file <<< "$migration"
        local filename=$(basename "$file")
        
        if [ "$version" -le "$CURRENT_VERSION" ]; then
            echo -e "  ${GREEN}✓${NC} $version: $filename"
        else
            echo -e "  ${YELLOW}○${NC} $version: $filename"
        fi
    done
}

# Function to generate new migration
generate_migration() {
    local name=$1
    
    if [ -z "$name" ]; then
        print_error "Migration name required"
        echo "Usage: $0 generate <migration_name>"
        exit 1
    fi
    
    # Get next version number
    local last_version=$(ls "$MIGRATIONS_DIR"/*.sql 2>/dev/null | \
        grep -o '[0-9]\{3\}' | sort -n | tail -1 || echo "000")
    local next_version=$(printf "%03d" $((10#$last_version + 1)))
    
    # Sanitize name
    local safe_name=$(echo "$name" | tr ' ' '_' | tr '[:upper:]' '[:lower:]' | \
        sed 's/[^a-z0-9_]//g')
    
    local filename="${next_version}_${safe_name}.sql"
    local filepath="$MIGRATIONS_DIR/$filename"
    
    print_info "Generating migration: $filename"
    
    cat > "$filepath" <<-EOF
-- Migration: $name
-- Version: $next_version
-- Date: $(date '+%Y-%m-%d')
-- Description: TODO: Add description here

-- =====================================================
-- UP Migration
-- =====================================================

-- TODO: Add your migration SQL here
-- Example:
-- ALTER TABLE prompts.history ADD COLUMN new_field VARCHAR(255);
-- CREATE INDEX idx_history_new_field ON prompts.history(new_field);


-- =====================================================
-- Migration Verification (Optional)
-- =====================================================

-- Add any verification queries here
-- Example:
-- DO \$\$
-- BEGIN
--     IF NOT EXISTS (
--         SELECT 1 FROM information_schema.columns 
--         WHERE table_schema = 'prompts' 
--         AND table_name = 'history' 
--         AND column_name = 'new_field'
--     ) THEN
--         RAISE EXCEPTION 'Migration failed: new_field column not created';
--     END IF;
-- END \$\$;
EOF
    
    # Create rollback template
    local rollback_filepath="$MIGRATIONS_DIR/rollback_${next_version}.sql"
    
    cat > "$rollback_filepath" <<-EOF
-- Rollback Migration: $name
-- Version: $next_version
-- Date: $(date '+%Y-%m-%d')
-- Description: Rollback script for ${filename}

-- =====================================================
-- DOWN Migration
-- =====================================================

-- TODO: Add your rollback SQL here
-- Example:
-- ALTER TABLE prompts.history DROP COLUMN IF EXISTS new_field;

EOF
    
    print_info "✅ Migration generated: $filepath"
    print_info "✅ Rollback template: $rollback_filepath"
    print_warn "Remember to implement both migration and rollback logic!"
}

# Main command handling
case "${1:-}" in
    up)
        # Run all pending migrations
        print_section "Running Migrations"
        
        create_migration_table
        CURRENT_VERSION=$(get_current_version)
        
        print_info "Current version: $CURRENT_VERSION"
        
        # Get available migrations
        migrations=($(get_available_migrations))
        pending_count=0
        
        for migration in "${migrations[@]}"; do
            IFS=':' read -r version file <<< "$migration"
            
            if [ "$version" -gt "$CURRENT_VERSION" ]; then
                ((pending_count++))
                run_migration "$version" "$file" || exit 1
            fi
        done
        
        if [ $pending_count -eq 0 ]; then
            print_info "No pending migrations"
        else
            print_info "✅ Applied $pending_count migration(s)"
        fi
        ;;
        
    down)
        # Rollback last migration
        print_section "Rolling Back Migration"
        
        CURRENT_VERSION=$(get_current_version)
        
        if [ "$CURRENT_VERSION" -eq 0 ]; then
            print_warn "No migrations to rollback"
            exit 0
        fi
        
        rollback_migration "$CURRENT_VERSION"
        ;;
        
    rollback)
        # Rollback to specific version
        TARGET_VERSION="${2:-}"
        
        if [ -z "$TARGET_VERSION" ]; then
            print_error "Target version required"
            echo "Usage: $0 rollback <version>"
            exit 1
        fi
        
        print_section "Rolling Back to Version $TARGET_VERSION"
        
        CURRENT_VERSION=$(get_current_version)
        
        if [ "$TARGET_VERSION" -ge "$CURRENT_VERSION" ]; then
            print_error "Target version must be less than current version ($CURRENT_VERSION)"
            exit 1
        fi
        
        # Rollback each migration in reverse order
        for ((v=$CURRENT_VERSION; v>$TARGET_VERSION; v--)); do
            rollback_migration "$v" || exit 1
        done
        ;;
        
    status)
        # Show migration status
        show_status
        ;;
        
    generate)
        # Generate new migration
        generate_migration "${2:-}"
        ;;
        
    version)
        # Show current version
        CURRENT_VERSION=$(get_current_version)
        echo $CURRENT_VERSION
        ;;
        
    help|--help|-h|"")
        # Show help
        echo "BetterPrompts Database Migration Tool"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  up                Run all pending migrations"
        echo "  down              Rollback the last migration"
        echo "  rollback <ver>    Rollback to specific version"
        echo "  status            Show migration status"
        echo "  generate <name>   Generate a new migration"
        echo "  version           Show current version"
        echo "  help              Show this help message"
        echo ""
        echo "Environment Variables:"
        echo "  POSTGRES_HOST     Database host (default: localhost)"
        echo "  POSTGRES_PORT     Database port (default: 5432)"
        echo "  POSTGRES_DB       Database name (default: betterprompts)"
        echo "  POSTGRES_USER     Database user (default: betterprompts)"
        echo "  POSTGRES_PASSWORD Database password (default: changeme)"
        ;;
        
    *)
        print_error "Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac