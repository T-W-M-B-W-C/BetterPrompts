# BetterPrompts Backend

Microservices architecture for AI-powered prompt engineering assistance.

## Architecture

The backend consists of multiple microservices:

- **API Gateway**: Main entry point, request routing, authentication
- **Intent Classification Service**: Analyzes user input to identify task type and complexity
- **Technique Selection Engine**: Matches intents to optimal prompt engineering techniques
- **Prompt Generation Service**: Applies techniques to generate enhanced prompts

## Services

### Intent Classification Service (Python/FastAPI)
- Fine-tuned DeBERTa-v3 model for intent classification
- REST API for classification requests
- Model versioning and A/B testing support

### Technique Selection Engine (Go/Gin)
- High-performance rule engine
- Technique matching based on intent and context
- Personalization support

### Prompt Generation Service (Python/FastAPI)
- Template-based prompt generation
- Dynamic technique application
- Output optimization

### API Gateway (Go/Gin)
- Request routing and load balancing
- Authentication and authorization
- Rate limiting and monitoring

## Tech Stack

- **Languages**: Python 3.11+, Go 1.21+
- **Frameworks**: FastAPI, Gin
- **Databases**: PostgreSQL with pgvector, Redis
- **ML**: Transformers, PyTorch
- **Infrastructure**: Docker, Kubernetes
- **Message Queue**: RabbitMQ/Kafka

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Go 1.21+
- PostgreSQL 15+
- Redis 7+

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd backend

# Set up environment variables
cp .env.example .env

# Start infrastructure services
docker-compose up -d postgres redis rabbitmq

# Set up each service (see individual READMEs)
cd services/intent-classifier
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
cd ../../scripts
./migrate.sh

# Start services
./start-dev.sh
```

### Docker Development

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up

# Run tests
docker-compose run --rm test
```

## Project Structure

```
backend/
├── services/              # Microservices
│   ├── api-gateway/      # Main API gateway
│   ├── intent-classifier/ # Intent classification service
│   ├── technique-selector/# Technique selection engine
│   └── prompt-generator/ # Prompt generation service
├── shared/               # Shared components
│   ├── models/          # Shared data models
│   ├── utils/           # Common utilities
│   ├── middleware/      # Shared middleware
│   └── config/          # Configuration management
├── infrastructure/       # Infrastructure as code
│   ├── docker/          # Docker configurations
│   ├── kubernetes/      # K8s manifests
│   └── terraform/       # Cloud infrastructure
├── scripts/             # Utility scripts
├── tests/               # Integration tests
└── docker-compose.yml   # Docker Compose configuration
```

## API Documentation

Once services are running:
- API Gateway: http://localhost:8000/docs
- Intent Classifier: http://localhost:8001/docs
- Technique Selector: http://localhost:8002/docs
- Prompt Generator: http://localhost:8003/docs

## Testing

```bash
# Run unit tests
./scripts/test-unit.sh

# Run integration tests
./scripts/test-integration.sh

# Run all tests
./scripts/test-all.sh
```

## Deployment

See [deployment guide](./docs/deployment.md) for production deployment instructions.

## Performance Requirements

- API Response Time: p95 < 200ms
- Model Inference: p95 < 500ms
- Throughput: 10,000 sustained RPS
- Availability: 99.9% uptime SLA