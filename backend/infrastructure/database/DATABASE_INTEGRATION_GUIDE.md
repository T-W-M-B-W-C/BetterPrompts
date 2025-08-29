# BetterPrompts Database Integration Guide

This guide provides comprehensive documentation for the BetterPrompts database setup, integration, and testing.

## Overview

BetterPrompts uses a microservices architecture with:
- **PostgreSQL 16** with pgvector extension for primary data storage and vector similarity search
- **Redis 7** for caching and session management
- **Database-per-service pattern** with shared schemas for common data

## Database Architecture

### PostgreSQL Schema Structure

The database is organized into three main schemas:

1. **`auth`** - Authentication and user management
   - `users` - User accounts and profiles
   - `sessions` - JWT refresh tokens and session management
   - `api_keys` - Developer API keys
   - `user_preferences` - User settings and preferences

2. **`prompts`** - Core business logic
   - `history` - Prompt enhancement history
   - `templates` - Prompt templates and techniques
   - `intent_patterns` - ML training data for intent classification
   - `saved_prompts` - User's saved prompts library
   - `collections` - Prompt collections/folders
   - `embeddings` - Vector embeddings for semantic search

3. **`analytics`** - Metrics and insights
   - `technique_effectiveness` - Technique performance metrics
   - `user_activity` - User activity tracking
   - `daily_stats` - Aggregated daily statistics
   - `api_metrics` - API usage metrics

### Redis Cache Structure

Redis is used for:
- **Session Management**: User sessions with 24-hour TTL
- **API Response Caching**: 5-minute cache for common requests
- **ML Prediction Caching**: 1-hour cache for model predictions
- **Rate Limiting**: Sliding window counters
- **Feature Flags**: Real-time feature toggles

## Setup Instructions

### Prerequisites

- Docker and Docker Compose
- PostgreSQL client tools (psql)
- Redis client tools (redis-cli)
- Python 3.11+ (for bcrypt hash generation)
- Go 1.23+ (for Go services)

### Quick Start

1. **Start Infrastructure Services**
   ```bash
   cd backend
   docker compose up -d postgres redis
   ```

2. **Verify Services**
   ```bash
   # PostgreSQL
   docker compose exec postgres pg_isready
   
   # Redis
   docker compose exec redis redis-cli ping
   ```

3. **Load Seed Data** (Optional for development)
   ```bash
   cd infrastructure/database/scripts
   ./seed.sh --clean
   ```

### Manual Setup

1. **Create Database**
   ```sql
   CREATE DATABASE betterprompts;
   CREATE USER betterprompts WITH PASSWORD 'your-secure-password';
   GRANT ALL PRIVILEGES ON DATABASE betterprompts TO betterprompts;
   ```

2. **Run Migrations**
   ```bash
   psql -U betterprompts -d betterprompts \
     -f infrastructure/database/migrations/001_initial_schema.sql
   ```

3. **Configure Redis**
   ```bash
   redis-server infrastructure/redis/redis.conf
   ```

## Service Integration

### Go Services (API Gateway)

```go
// Initialize database
dsn := "postgres://user:pass@localhost/betterprompts?sslmode=disable"
db, err := services.NewCompleteDatabaseService(dsn)

// Initialize Redis
redisConfig := services.RedisConfig{
    Address:    "localhost:6379",
    Password:   "",
    KeyPrefix:  "api-gateway",
    DefaultTTL: 5 * time.Minute,
}
redis, err := services.NewRedisService(redisConfig)
```

### Python Services (Intent Classifier)

```python
# Initialize database
from app.db.database_service import get_database

db = await get_database()

# Initialize Redis
from app.services.redis_service import get_default_redis

redis = get_default_redis()
```

## Common Operations

### User Management

```go
// Create user
user := &models.User{
    Email:        "user@example.com",
    Username:     "username",
    PasswordHash: hashedPassword,
}
err := db.CreateUser(ctx, user)

// Get user
user, err := db.GetUserByEmail(ctx, "user@example.com")
```

### Prompt History

```python
# Save prompt
history_id = await db.save_prompt_history(
    original_input="User's prompt",
    enhanced_output="Enhanced version",
    intent="creative_writing",
    techniques_used=["chain_of_thought"],
    user_id=user_id
)

# Get history
history = await db.get_prompt_history(user_id=user_id)
```

### Caching

```go
// Cache API response
err := redis.CacheAPIResponse(ctx, "/api/v1/enhance", "params", response)

// Get cached response
var cached EnhanceResponse
err := redis.GetCachedAPIResponse(ctx, "/api/v1/enhance", "params", &cached)
```

## Testing

### Run All Tests

```bash
cd infrastructure/database/scripts
./run_tests.sh
```

### Run Specific Tests

```bash
# Go tests only
./run_tests.sh --go-only

# Python tests only
./run_tests.sh --python-only

# Keep test database after tests
./run_tests.sh --keep-db
```

### Test Database

Tests use a separate `betterprompts_test` database that is created and destroyed automatically.

## Migrations

### Create New Migration

```bash
cd infrastructure/database/migrations
touch 002_add_new_feature.sql
```

### Migration Template

```sql
-- Migration: Add new feature
-- Version: 002
-- Description: Add support for XYZ feature

-- Add new columns
ALTER TABLE prompts.history 
ADD COLUMN new_feature_flag BOOLEAN DEFAULT false;

-- Create new tables
CREATE TABLE IF NOT EXISTS prompts.new_feature (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- columns...
);

-- Update existing data if needed
UPDATE prompts.history 
SET new_feature_flag = true 
WHERE created_at > '2024-01-01';
```

## Performance Optimization

### PostgreSQL Tuning

Key indexes are already created for:
- User lookups by email/username
- Session lookups by token
- Prompt history by user and date
- Vector similarity search

### Connection Pooling

- **Go**: 25 max connections, 5 idle
- **Python**: 20 max connections, 5 min
- **Redis**: 100 connections default pool

### Query Optimization

1. Use prepared statements
2. Batch operations when possible
3. Leverage indexes effectively
4. Monitor slow query log

## Monitoring

### Database Health

```sql
-- Check database size
SELECT pg_database_size('betterprompts');

-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Slow queries
SELECT query, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

### Redis Monitoring

```bash
# Memory usage
redis-cli info memory

# Connected clients
redis-cli info clients

# Cache hit rate
redis-cli info stats
```

## Security

### Best Practices

1. **Never store plain passwords** - Always use bcrypt
2. **Use prepared statements** - Prevent SQL injection
3. **Encrypt sensitive data** - PII should be encrypted at rest
4. **Rotate credentials** - Regular password/key rotation
5. **Audit access** - Log all database access

### Generate Password Hashes

```bash
cd infrastructure/database/scripts
./generate_password_hash.py "YourSecurePassword"
```

## Troubleshooting

### Common Issues

1. **Connection refused**
   - Check if services are running
   - Verify host/port configuration
   - Check firewall rules

2. **Authentication failed**
   - Verify credentials
   - Check user permissions
   - Ensure database exists

3. **Migration errors**
   - Check for existing objects
   - Verify schema permissions
   - Review migration order

4. **Performance issues**
   - Check connection pool exhaustion
   - Review slow query log
   - Monitor cache hit rates

### Debug Commands

```bash
# Check PostgreSQL logs
docker compose logs postgres

# Check Redis logs
docker compose logs redis

# Connect to PostgreSQL
docker compose exec postgres psql -U betterprompts

# Connect to Redis
docker compose exec redis redis-cli
```

## Backup and Recovery

### PostgreSQL Backup

```bash
# Backup
pg_dump -U betterprompts -h localhost betterprompts > backup.sql

# Restore
psql -U betterprompts -h localhost betterprompts < backup.sql
```

### Redis Backup

```bash
# Save snapshot
redis-cli BGSAVE

# Copy dump file
docker cp betterprompts-redis:/data/dump.rdb ./redis-backup.rdb
```

## Production Considerations

1. **Use connection pooling** - PgBouncer for PostgreSQL
2. **Enable SSL/TLS** - Encrypt all connections
3. **Set up replication** - PostgreSQL streaming replication
4. **Configure backups** - Automated daily backups
5. **Monitor performance** - Prometheus + Grafana
6. **Plan capacity** - Monitor growth trends

## References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/16/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Redis Documentation](https://redis.io/documentation)
- [Go Database/SQL Tutorial](https://go.dev/doc/database/tutorial)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)