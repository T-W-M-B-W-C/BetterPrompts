# BetterPrompts

A Prompt Engineering Assistant that democratizes advanced prompt engineering techniques for non-technical users. The system analyzes natural language input and automatically suggests or applies optimal prompting strategies without requiring users to understand the underlying techniques.

## 🚀 Features

- **Intelligent Intent Classification**: Automatically identifies the type and complexity of user tasks
- **12 Prompt Engineering Techniques**: Including Chain of Thought, Few-shot Learning, Tree of Thoughts, and more
- **Real-time Enhancement**: Streaming progress indicators for instant feedback
- **Personalized Recommendations**: Learns from user preferences and technique effectiveness
- **Beautiful UI**: Modern, responsive interface with dark mode support
- **Enterprise-Ready**: Scalable architecture with monitoring and analytics

## 🛠️ Technology Stack

- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS v4
- **Backend Services**:
  - API Gateway: Go + Gin (JWT auth, rate limiting)
  - Intent Classifier: Python + FastAPI + DeBERTa-v3
  - Technique Selector: Go + Gin
  - Prompt Generator: Python + FastAPI
- **Databases**: PostgreSQL 16 with pgvector, Redis 7
- **ML Infrastructure**: TorchServe with GPU support
- **Monitoring**: Prometheus + Grafana
- **Container Orchestration**: Docker Compose (Kubernetes ready)

## 📋 Prerequisites

- Docker Desktop 4.0+ with Docker Compose v2
- 16GB RAM minimum (for ML models)
- 20GB free disk space
- API Keys:
  - OpenAI API key (for GPT integration)
  - Anthropic API key (for Claude integration)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/betterprompts.git
cd betterprompts
```

### 2. Environment Setup
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys and configuration
# Required: OPENAI_API_KEY, ANTHROPIC_API_KEY
```

### 3. Start Services

#### Local Development (CPU-only, Fast)
```bash
# Starts all services with CPU-only PyTorch (fast builds)
docker compose up -d

# View logs
docker compose logs -f

# Check service health
docker compose ps
```

#### Production Mode (GPU-enabled)
```bash
# For AWS/Cloud deployment with GPU support
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost/api/v1
- **API Docs**: http://localhost/api/v1/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│    Frontend     │────▶│   API Gateway   │────▶│     Redis       │
│   (Next.js)     │     │    (Go/Gin)     │     │    (Cache)      │
│                 │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼──────┐ ┌──▼──────┐ ┌──▼──────────┐
              │   Intent    │ │Technique│ │   Prompt    │
              │ Classifier  │ │Selector │ │ Generator   │
              │  (Python)   │ │  (Go)   │ │  (Python)   │
              └─────┬───────┘ └────┬────┘ └──────┬──────┘
                    │              │              │
                    └──────────────┴──────────────┘
                                   │
                            ┌──────▼──────┐
                            │ PostgreSQL  │
                            │ + pgvector  │
                            └─────────────┘
```

## 🔧 Configuration

### PyTorch CPU/GPU Configuration

The prompt-generator service supports both CPU-only and GPU-enabled PyTorch to optimize for different environments:

#### Local Development (Default)
- Uses CPU-only PyTorch automatically
- Downloads ~140MB instead of >1GB
- Builds in 2-3 minutes instead of 12+ minutes
- Perfect for development and testing

#### Production Deployment
- Full GPU support for AWS EC2 GPU instances
- Automatic GPU detection and allocation
- Optimized for high-throughput inference

#### Manual Configuration
```bash
# Build CPU version (fast, for local dev)
docker build --build-arg PYTORCH_VARIANT=cpu -t prompt-generator:cpu .

# Build GPU version (for production)
docker build --build-arg PYTORCH_VARIANT=gpu -t prompt-generator:gpu .
```

### Environment Variables

Key environment variables in `.env`:
```bash
# API Keys (Required)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Database
POSTGRES_USER=betterprompts
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=betterprompts

# Security
JWT_SECRET=your_jwt_secret

# Optional
LOG_LEVEL=DEBUG  # Set to INFO for production
```

## 📚 API Documentation

### Core Endpoints

#### Enhance Prompt
```bash
POST /api/v1/enhance
Content-Type: application/json

{
  "prompt": "Help me write a blog post about AI",
  "context": "Technical audience",
  "techniques": ["chain_of_thought", "few_shot"]
}
```

#### Get Techniques
```bash
GET /api/v1/techniques
```

#### Prompt History
```bash
GET /api/v1/history?page=1&limit=10
```

## 🧪 Development

### Running Tests
```bash
# Backend tests
cd backend/services/api-gateway
go test ./...

# Frontend tests
cd frontend
npm test
```

### Code Quality
```bash
# Lint Go code
golangci-lint run

# Lint Frontend
cd frontend
npm run lint
```

### Database Migrations
```bash
# Run migrations
cd backend
./scripts/migrate.sh up

# Rollback
./scripts/migrate.sh down
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Docker Build Slow
- **Symptom**: Downloading large CUDA libraries
- **Solution**: Ensure you're using `docker compose up` (not prod mode) for local development

#### 2. Services Not Connecting
- **Symptom**: API calls failing
- **Solution**: Check all services are healthy with `docker compose ps`

#### 3. Out of Memory
- **Symptom**: Containers crashing
- **Solution**: Increase Docker Desktop memory to 8GB minimum

### Logs and Debugging
```bash
# View all logs
docker compose logs

# View specific service
docker compose logs prompt-generator

# Follow logs
docker compose logs -f api-gateway
```

## 📈 Monitoring

Access Grafana at http://localhost:3001 for:
- API response times
- Model inference latency
- Success/error rates
- Resource utilization

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT models
- Anthropic for Claude
- Hugging Face for DeBERTa-v3
- The open-source community

## 📞 Support

- Documentation: [docs/](./docs)
- Issues: [GitHub Issues](https://github.com/your-org/betterprompts/issues)
- Email: support@betterprompts.ai

---

Built with ❤️ by the BetterPrompts team