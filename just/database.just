# Database management commands

# Setup database with initial schema and migrations
setup-db:
    @echo "Setting up database..."
    @docker exec -i betterprompts-postgres psql -U betterprompts -d betterprompts -f - < backend/infrastructure/database/migrations/001_initial_schema.sql
    @echo "✓ Schema created"
    @echo "Running migrations..."
    @docker exec -i betterprompts-postgres psql -U betterprompts -d betterprompts -f - < backend/services/api-gateway/internal/migrations/sql/002_fix_user_schema.sql
    @echo "✓ Database ready with all migrations"

# Reset database (drop and recreate)
reset-db:
    @echo "Resetting database..."
    @docker exec betterprompts-postgres psql -U betterprompts -d betterprompts -c "DROP SCHEMA IF EXISTS auth,prompts,analytics CASCADE;"
    @just setup-db

# Check database status
db-status:
    @docker exec betterprompts-postgres psql -U betterprompts -d betterprompts -c "\dn"

# Connect to database
db-shell:
    docker exec -it betterprompts-postgres psql -U betterprompts -d betterprompts

# Run migrations
migrate:
    @echo "Running database migrations..."
    @docker exec -i betterprompts-postgres psql -U betterprompts -d betterprompts -f - < backend/infrastructure/database/migrations/001_initial_schema.sql
    @docker exec -i betterprompts-postgres psql -U betterprompts -d betterprompts -f - < backend/services/api-gateway/internal/migrations/sql/002_fix_user_schema.sql
    @echo "✓ Migrations complete"