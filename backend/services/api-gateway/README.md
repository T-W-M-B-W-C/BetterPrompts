# BetterPrompts API Gateway

The main API Gateway service for the BetterPrompts platform, handling authentication, request routing, and service orchestration.

## Features

- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- Session management with Redis
- Rate limiting (user, IP, and endpoint-based)
- Request/response caching
- Service orchestration for microservices
- Comprehensive logging and monitoring

## Architecture

The API Gateway acts as the single entry point for all client requests and routes them to appropriate backend services:

- **Intent Classification Service** (Python/FastAPI)
- **Technique Selection Engine** (Go/Gin)
- **Prompt Generation Service** (Python/FastAPI)

## Authentication & Authorization

### JWT Authentication
- Access tokens (15 min default expiry)
- Refresh tokens (7 days expiry)
- Remember me functionality (30 days)
- Secure token generation and validation

### User Roles
- **user**: Basic access to personal prompts
- **developer**: API access and usage metrics
- **admin**: Full system access

### Password Security
- Bcrypt hashing with cost factor 12
- Password strength validation
- Common password prevention
- Account lockout after failed attempts

## API Endpoints

### Public Endpoints
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/verify-email` - Email verification
- `GET /api/v1/health` - Health check
- `GET /api/v1/ready` - Readiness check

### Protected Endpoints
- `GET /api/v1/auth/profile` - Get user profile
- `PUT /api/v1/auth/profile` - Update profile
- `POST /api/v1/auth/change-password` - Change password
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/enhance` - Main prompt enhancement endpoint
- `GET /api/v1/history` - Get prompt history
- `GET /api/v1/techniques` - Get available techniques

### Admin Endpoints
- `GET /api/v1/admin/users` - List users
- `GET /api/v1/admin/metrics` - System metrics
- `POST /api/v1/admin/cache/clear` - Clear cache

### Developer Endpoints
- `POST /api/v1/dev/api-keys` - Create API key
- `GET /api/v1/dev/analytics/usage` - Usage analytics

## Configuration

Environment variables:
```bash
# Server
PORT=8080
LOG_LEVEL=info

# Database
DATABASE_URL=postgres://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis:6379
REDIS_PASSWORD=

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_REFRESH_SECRET_KEY=your-refresh-secret

# Service URLs
INTENT_CLASSIFIER_URL=http://intent-classifier:8001
TECHNIQUE_SELECTOR_URL=http://technique-selector:8002
PROMPT_GENERATOR_URL=http://prompt-generator:8003
```

## Development

### Prerequisites
- Go 1.21+
- PostgreSQL 15+
- Redis 7+

### Running Locally
```bash
# Install dependencies
go mod download

# Run migrations
psql -U postgres -d betterprompts -f migrations/001_create_tables.sql
psql -U postgres -d betterprompts -f migrations/002_add_users_table.sql

# Run the server
go run cmd/server/main.go
```

### Building
```bash
go build -o api-gateway cmd/server/main.go
```

## Security Features

1. **Authentication**
   - JWT tokens with secure signing
   - Refresh token rotation
   - Session management

2. **Authorization**
   - Role-based access control
   - Permission-based endpoints
   - Resource ownership validation

3. **Rate Limiting**
   - Per-user limits
   - IP-based limits
   - Endpoint-specific limits

4. **Input Validation**
   - Request body validation
   - SQL injection prevention
   - XSS protection

5. **Password Security**
   - Strong password requirements
   - Bcrypt hashing
   - Account lockout protection

## Monitoring

The service provides:
- Structured JSON logging
- Request/response logging
- Performance metrics
- Error tracking
- Health checks

## Testing

```bash
# Run unit tests
go test ./...

# Run integration tests
go test -tags=integration ./...

# Run with coverage
go test -cover ./...
```

## Deployment

The service is designed to run in Kubernetes with:
- Horizontal pod autoscaling
- Liveness/readiness probes
- ConfigMaps for configuration
- Secrets for sensitive data

## License

Proprietary - BetterPrompts