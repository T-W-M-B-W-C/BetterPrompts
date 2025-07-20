# Database Migrations

This directory contains all database migrations for the BetterPrompts application.

## Structure

```
migrations/
├── up/              # Forward migrations (apply changes)
├── down/            # Rollback migrations (undo changes)
├── scripts/         # Migration runner scripts
└── README.md        # This file
```

## Migration Files

### Naming Convention
Migrations follow the pattern: `{number}_{description}.sql`
- `001_initial_schema.sql` - Base schema with users, sessions, prompts
- `002_roles_permissions.sql` - RBAC tables and relationships
- `003_indexes_constraints.sql` - Performance indexes and constraints
- `004_seed_data.sql` - Initial data (roles, permissions, templates)

### Applied Migrations

| Version | Description | Applied At | Status |
|---------|-------------|------------|---------|
| 001 | Initial schema | Pending | ⏳ |
| 002 | Roles & Permissions | Pending | ⏳ |
| 003 | Indexes & Constraints | Pending | ⏳ |
| 004 | Seed Data | Pending | ⏳ |

## Usage

### Apply All Migrations
```bash
cd backend/migrations
./scripts/migrate.sh up
```

### Apply Specific Migration
```bash
./scripts/migrate.sh up 001
```

### Rollback Last Migration
```bash
./scripts/migrate.sh down
```

### Rollback to Specific Version
```bash
./scripts/migrate.sh down 002
```

### Check Migration Status
```bash
./scripts/migrate.sh status
```

## Environment Variables

Required environment variables:
- `DB_HOST` - PostgreSQL host (default: localhost)
- `DB_PORT` - PostgreSQL port (default: 5432)
- `DB_NAME` - Database name (default: betterprompts)
- `DB_USER` - Database user (default: betterprompts)
- `DB_PASSWORD` - Database password

## Schema Overview

### Schemas
- `public` - System tables and extensions
- `auth` - Authentication and authorization
- `prompts` - Core business logic
- `analytics` - Metrics and reporting

### Key Tables
- `auth.users` - User accounts with roles array
- `auth.roles` - System roles
- `auth.permissions` - Granular permissions
- `auth.sessions` - JWT refresh tokens
- `prompts.history` - Prompt enhancement history
- `prompts.templates` - Reusable prompt templates
- `analytics.technique_effectiveness` - Performance metrics

## Development

### Creating New Migrations
1. Create UP migration in `up/00X_description.sql`
2. Create DOWN migration in `down/00X_description.sql`
3. Test both directions locally
4. Update this README with migration details

### Best Practices
- Always include IF NOT EXISTS/IF EXISTS clauses
- Make migrations idempotent
- Test rollback before committing
- Include meaningful comments in SQL
- Keep migrations focused and atomic