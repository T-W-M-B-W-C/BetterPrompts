#!/bin/bash
# migrate.sh - Database migration runner for BetterPrompts
# Usage: ./migrate.sh [up|down|status] [version]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-betterprompts}"
DB_USER="${DB_USER:-betterprompts}"
DB_PASSWORD="${DB_PASSWORD:-betterprompts}"

# Migration directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATIONS_DIR="$(dirname "$SCRIPT_DIR")"
UP_DIR="$MIGRATIONS_DIR/up"
DOWN_DIR="$MIGRATIONS_DIR/down"

# Ensure directories exist
if [[ ! -d "$UP_DIR" ]]; then
    echo -e "${RED}Error: Migrations up directory not found: $UP_DIR${NC}"
    exit 1
fi

if [[ ! -d "$DOWN_DIR" ]]; then
    echo -e "${RED}Error: Migrations down directory not found: $DOWN_DIR${NC}"
    exit 1
fi

# Build connection string
export PGPASSWORD="$DB_PASSWORD"
PSQL="psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"

# Function to check database connection
check_connection() {
    echo -e "${BLUE}Checking database connection...${NC}"
    if ! $PSQL -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${RED}Error: Cannot connect to database${NC}"
        echo "Please check your database configuration:"
        echo "  DB_HOST=$DB_HOST"
        echo "  DB_PORT=$DB_PORT"
        echo "  DB_NAME=$DB_NAME"
        echo "  DB_USER=$DB_USER"
        exit 1
    fi
    echo -e "${GREEN}Database connection successful${NC}"
}

# Function to create migration tracking table if not exists
init_migrations() {
    echo -e "${BLUE}Initializing migration tracking...${NC}"
    $PSQL -q <<EOF
CREATE TABLE IF NOT EXISTS public.schema_migrations (
    version INTEGER PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64)
);
EOF
}

# Function to get current version
get_current_version() {
    local version=$($PSQL -t -c "SELECT COALESCE(MAX(version), 0) FROM public.schema_migrations" 2>/dev/null || echo "0")
    echo "$version" | tr -d ' '
}

# Function to get all applied migrations
get_applied_migrations() {
    $PSQL -t -c "SELECT version, description, applied_at FROM public.schema_migrations ORDER BY version" 2>/dev/null || true
}

# Function to apply a migration
apply_migration() {
    local version=$1
    local direction=$2
    local file=""
    
    if [[ "$direction" == "up" ]]; then
        file=$(find "$UP_DIR" -name "${version}_*.sql" | head -1)
    else
        file=$(find "$DOWN_DIR" -name "${version}_*.sql" | head -1)
    fi
    
    if [[ -z "$file" ]]; then
        echo -e "${RED}Error: Migration file not found for version $version${NC}"
        return 1
    fi
    
    local filename=$(basename "$file")
    local description=$(echo "$filename" | sed -E 's/^[0-9]+_(.*)\.sql$/\1/' | tr '_' ' ')
    
    echo -e "${BLUE}Applying migration $version ($direction): $description${NC}"
    
    # Apply the migration
    if $PSQL -f "$file" > /dev/null 2>&1; then
        if [[ "$direction" == "up" ]]; then
            # Record the migration (the migration file should do this, but fallback)
            $PSQL -q -c "INSERT INTO public.schema_migrations (version, description) VALUES ($version, '$description') ON CONFLICT (version) DO NOTHING"
        else
            # Remove the migration record
            $PSQL -q -c "DELETE FROM public.schema_migrations WHERE version = $version"
        fi
        echo -e "${GREEN}✓ Migration $version applied successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ Migration $version failed${NC}"
        # Show the actual error
        $PSQL -f "$file"
        return 1
    fi
}

# Function to migrate up
migrate_up() {
    local target_version=$1
    local current_version=$(get_current_version)
    
    echo -e "${BLUE}Current version: $current_version${NC}"
    
    # Get all available migrations
    local migrations=()
    for file in "$UP_DIR"/*.sql; do
        if [[ -f "$file" ]]; then
            local version=$(basename "$file" | cut -d'_' -f1)
            migrations+=("$version")
        fi
    done
    
    # Sort migrations
    IFS=$'\n' sorted=($(sort -n <<<"${migrations[*]}"))
    unset IFS
    
    # Apply migrations
    local applied=0
    for version in "${sorted[@]}"; do
        if [[ -z "$target_version" ]] || [[ "$version" -le "$target_version" ]]; then
            if [[ "$version" -gt "$current_version" ]]; then
                if apply_migration "$version" "up"; then
                    ((applied++))
                else
                    echo -e "${RED}Migration failed, stopping${NC}"
                    exit 1
                fi
            fi
        fi
    done
    
    if [[ "$applied" -eq 0 ]]; then
        echo -e "${YELLOW}No new migrations to apply${NC}"
    else
        echo -e "${GREEN}Applied $applied migration(s)${NC}"
    fi
}

# Function to migrate down
migrate_down() {
    local target_version=${1:-0}
    local current_version=$(get_current_version)
    
    echo -e "${BLUE}Current version: $current_version${NC}"
    
    if [[ "$current_version" -eq 0 ]]; then
        echo -e "${YELLOW}No migrations to rollback${NC}"
        return
    fi
    
    # Get all applied migrations in reverse order
    local migrations=()
    for version in $(seq "$current_version" -1 1); do
        if [[ "$version" -gt "$target_version" ]]; then
            migrations+=("$version")
        fi
    done
    
    # Apply rollbacks
    local rolled_back=0
    for version in "${migrations[@]}"; do
        if apply_migration "$version" "down"; then
            ((rolled_back++))
        else
            echo -e "${RED}Rollback failed, stopping${NC}"
            exit 1
        fi
    done
    
    if [[ "$rolled_back" -eq 0 ]]; then
        echo -e "${YELLOW}No migrations to rollback${NC}"
    else
        echo -e "${GREEN}Rolled back $rolled_back migration(s)${NC}"
    fi
}

# Function to show migration status
show_status() {
    echo -e "${BLUE}Migration Status${NC}"
    echo -e "${BLUE}================${NC}"
    
    local current_version=$(get_current_version)
    echo -e "Current version: ${GREEN}$current_version${NC}"
    echo ""
    
    echo -e "${BLUE}Applied migrations:${NC}"
    local applied=$(get_applied_migrations)
    if [[ -z "$applied" ]]; then
        echo "  None"
    else
        echo "$applied" | while IFS='|' read -r version desc applied_at; do
            version=$(echo "$version" | tr -d ' ')
            desc=$(echo "$desc" | tr -d ' ')
            applied_at=$(echo "$applied_at" | tr -d ' ')
            printf "  %03d - %-40s %s\n" "$version" "$desc" "$applied_at"
        done
    fi
    echo ""
    
    echo -e "${BLUE}Available migrations:${NC}"
    for file in "$UP_DIR"/*.sql; do
        if [[ -f "$file" ]]; then
            local filename=$(basename "$file")
            local version=$(echo "$filename" | cut -d'_' -f1)
            local desc=$(echo "$filename" | sed -E 's/^[0-9]+_(.*)\.sql$/\1/' | tr '_' ' ')
            
            if [[ "$version" -gt "$current_version" ]]; then
                printf "  ${YELLOW}%03d - %-40s (pending)${NC}\n" "$version" "$desc"
            else
                printf "  ${GREEN}%03d - %-40s (applied)${NC}\n" "$version" "$desc"
            fi
        fi
    done
}

# Main script logic
main() {
    local command=${1:-status}
    local version=$2
    
    check_connection
    init_migrations
    
    case "$command" in
        up)
            migrate_up "$version"
            ;;
        down)
            migrate_down "$version"
            ;;
        status)
            show_status
            ;;
        *)
            echo "Usage: $0 [up|down|status] [version]"
            echo ""
            echo "Commands:"
            echo "  up [version]     - Apply migrations up to version (or all if not specified)"
            echo "  down [version]   - Rollback migrations down to version (or all if not specified)"
            echo "  status           - Show current migration status"
            echo ""
            echo "Environment variables:"
            echo "  DB_HOST          - Database host (default: localhost)"
            echo "  DB_PORT          - Database port (default: 5432)"
            echo "  DB_NAME          - Database name (default: betterprompts)"
            echo "  DB_USER          - Database user (default: betterprompts)"
            echo "  DB_PASSWORD      - Database password"
            exit 1
            ;;
    esac
}

# Run the script
main "$@"