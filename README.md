# BetterPrompts

AI-powered prompt enhancement platform that transforms basic prompts into optimized, technique-driven queries for better AI responses.

## ✨ Features

- **Intelligent Intent Classification**: ML-powered detection of user intent using DeBERTa models
- **Smart Technique Selection**: Rule-based engine that selects optimal prompt techniques
- **Template-Based Enhancement**: Apply proven prompt engineering techniques automatically
- **JWT Authentication**: Secure user authentication with refresh tokens
- **Microservices Architecture**: Scalable, maintainable service-oriented design
- **Redis Caching**: High-performance caching for improved response times
- **PostgreSQL with pgvector**: Advanced database with vector similarity search

## 🏗️ Architecture

See [Architecture Documentation](docs/ARCHITECTURE_v1.md) for detailed system design.

### Services

- **API Gateway** (Go/Gin) - Authentication, routing, rate limiting
- **Intent Classifier** (Python) - ML-powered intent detection using DeBERTa
- **Technique Selector** (Go) - Rule engine for technique selection
- **Prompt Generator** (Python) - Template-based prompt enhancement
- **PostgreSQL** - Primary database with pgvector extension
- **Redis** - Caching and session management
- **TorchServe** - ML model serving (optional)

## 🚀 Getting Started

### Prerequisites

- Docker Desktop with Compose v2
- Python 3.8+
- 4GB free RAM
- 2GB free disk space

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/CodeBlackwell/BetterPrompts.git
cd BetterPrompts

# 2. First-time setup (do this once)
just first-time

# 3. Daily usage
just up      # Start all services
just health  # Check service health
just down    # Stop all services
```

That's it! The application will be running at:
- API Gateway: http://localhost:8000
- Intent Classifier: http://localhost:8001
- Technique Selector: http://localhost:8002
- Prompt Generator: http://localhost:8003
- PostgreSQL: http://localhost:5432
- Redis: http://localhost:6379

### Manual Setup (if not using Just)

```bash
# Install Python dependencies
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Build and start services
docker compose build
docker compose up -d

# Initialize database
docker compose exec -T postgres psql -U betterprompts -d betterprompts < backend/infrastructure/database/migrations/001_initial_schema.sql
docker compose exec -T postgres psql -U betterprompts -d betterprompts < backend/services/api-gateway/internal/migrations/sql/002_fix_user_schema.sql

# Check health
curl http://localhost:8000/api/v1/health
```

## 📁 Project Structure

```
BetterPrompts/
├── backend/
│   ├── services/
│   │   ├── api-gateway/        # Go API Gateway
│   │   ├── intent-classifier/   # Python ML Service
│   │   ├── technique-selector/  # Go Rules Engine
│   │   └── prompt-generator/    # Python Generator
│   └── infrastructure/
│       └── database/            # DB schemas & migrations
├── ml-pipeline/                 # ML models & configurations
├── docker/                      # Docker configurations
├── just/                        # Just command modules
├── tests/                       # Integration tests
└── docker-compose.yml          # Service orchestration
```

## 🧪 Testing

```bash
# Run all tests
just test-all

# Specific test suites
just test-auth        # Authentication tests
just test-integration # Integration tests
just smoke-test      # Quick smoke tests
```

## 📊 Available Commands

The project uses [Just](https://github.com/casey/just) for task automation:

```bash
just              # Show all commands
just first-time   # Complete setup for new developers
just up           # Start services
just down         # Stop services
just health       # Check service health
just logs         # View logs
just restart      # Restart service(s)
just rebuild      # Rebuild service(s)
just status       # Show service status

# Testing Commands
just test-auth    # Run authentication tests
just test-integration # Run integration tests
just test-e2e     # Run end-to-end tests
just smoke-test   # Quick smoke test
just test-all     # Run all tests

# Database Commands
just setup-db     # Setup database with migrations
just reset-db     # Reset database
just migrate      # Run migrations
just db-shell     # Connect to database

# Performance Testing
just bench-selector  # Benchmark selector
just bench-generator # Benchmark generator
just bench-auth     # Benchmark auth
```

Run `just --list` for complete command list.

## 🔧 Development

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```env
# Core Configuration
ENVIRONMENT=development
DATABASE_URL=postgresql://betterprompts:betterprompts@localhost:5432/betterprompts
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET_KEY=dev-secret-change-in-production
JWT_REFRESH_SECRET_KEY=dev-refresh-secret-change-in-production

# Optional: LLM API Keys (for enhanced generation)
OPENAI_API_KEY=your-key-here        # Optional
ANTHROPIC_API_KEY=your-key-here     # Optional

# Service URLs (for microservice communication)
INTENT_CLASSIFIER_URL=http://intent-classifier:8001
TECHNIQUE_SELECTOR_URL=http://technique-selector:8002
PROMPT_GENERATOR_URL=http://prompt-generator:8003
```

### Adding New Services

1. Create service directory in `backend/services/`
2. Add to `docker-compose.yml`
3. Create Dockerfile
4. Add health check endpoint
5. Update gateway routing

### Database Migrations

```bash
# Create new migration
echo "-- Your SQL here" > backend/services/api-gateway/internal/migrations/sql/003_your_migration.sql

# Apply migrations
just migrate
```

## 🚢 Deployment

The application is containerized and ready for deployment:

```bash
# Production build
docker compose -f docker-compose.yml build

# The application runs in Docker containers and can be deployed to:
# - Any Docker-compatible hosting platform
# - Cloud providers with container support
# - Self-hosted servers with Docker installed
```

## 📝 API Documentation

### Core Endpoints

#### Authentication
```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Test123!@#"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Test123!@#"}'

# Refresh token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Authorization: Bearer YOUR_REFRESH_TOKEN"
```

#### Prompt Enhancement
```bash
# Enhance a prompt
curl -X POST http://localhost:8000/api/v1/enhance \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"explain AI"}'

# Get prompt history  
curl -X GET http://localhost:8000/api/v1/prompts/history \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Health & Status
```bash
# Check service health
curl http://localhost:8000/api/v1/health

# Individual service health checks
curl http://localhost:8001/health  # Intent Classifier
curl http://localhost:8002/health  # Technique Selector
curl http://localhost:8003/health  # Prompt Generator
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## 🙏 Acknowledgments

- DeBERTa model by Microsoft
- TorchServe by PyTorch team
- All open-source contributors

---

Built with ❤️ by Christopher Blackwell