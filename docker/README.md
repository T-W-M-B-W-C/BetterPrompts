# BetterPrompts Docker Configuration

This directory contains all Docker configurations for the BetterPrompts application, following DevOps best practices for containerization, orchestration, and deployment.

## 🏗️ Architecture Overview

The application uses a microservices architecture with the following components:

- **Frontend**: Next.js application (TypeScript, React 18+)
- **Intent Classifier**: Python/FastAPI service with ML models
- **Technique Selector**: Go/Gin service for technique matching
- **Prompt Generator**: Python/FastAPI service for prompt enhancement
- **API Gateway**: Nginx reverse proxy with rate limiting and caching
- **Database**: PostgreSQL with pgvector extension
- **Cache**: Redis for session and API response caching
- **Monitoring**: Prometheus + Grafana stack

## 📁 Directory Structure

```
docker/
├── frontend/               # Frontend service Docker configs
│   ├── Dockerfile         # Multi-stage build for Next.js
│   └── .dockerignore      # Ignore patterns for build context
├── backend/
│   ├── intent-classifier/ # ML service configs
│   ├── technique-selector/# Go service configs
│   └── prompt-generator/  # Python service configs
├── nginx/                 # API Gateway configs
│   ├── Dockerfile
│   ├── nginx.conf        # Main Nginx configuration
│   └── conf.d/           # Site configurations
└── validate.sh           # Configuration validation script
```

## 🚀 Quick Start

### Prerequisites

- Docker Engine 24.0+
- Docker Compose 2.20+
- 16GB RAM minimum (for ML models)
- 50GB disk space

### Local Development

1. **Clone and setup environment**:
   ```bash
   git clone https://github.com/your-org/betterprompts.git
   cd betterprompts
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Validate configurations**:
   ```bash
   ./docker/validate.sh
   ```

3. **Build and start services**:
   ```bash
   docker compose build
   docker compose up -d
   ```

4. **Check service health**:
   ```bash
   docker compose ps
   docker compose logs -f
   ```

5. **Access the application**:
   - Frontend: http://localhost:3000
   - API: http://localhost/api/v1
   - Grafana: http://localhost:3001 (admin/admin)
   - Prometheus: http://localhost:9090

### Production Deployment

1. **Build and push images**:
   ```bash
   # Build with production tags
   docker compose -f docker-compose.prod.yml build
   
   # Tag and push to registry
   docker tag betterprompts/frontend:latest your-registry/betterprompts/frontend:v1.0.0
   docker push your-registry/betterprompts/frontend:v1.0.0
   ```

2. **Deploy with Docker Swarm**:
   ```bash
   docker stack deploy -c docker-compose.prod.yml betterprompts
   ```

3. **Or deploy with Kubernetes**:
   ```bash
   # Convert to Kubernetes manifests
   kompose convert -f docker-compose.prod.yml
   kubectl apply -f .
   ```

## 🔒 Security Features

- **Non-root containers**: All services run as non-root users
- **Health checks**: Every service has health check endpoints
- **Resource limits**: CPU and memory limits enforced
- **Network isolation**: Services communicate through internal networks
- **Secrets management**: Sensitive data via environment variables
- **SSL/TLS**: Production deployment includes SSL termination

## 🎯 Performance Optimizations

### Build Optimizations
- Multi-stage builds reduce image sizes by 60-80%
- Layer caching for faster rebuilds
- Minimal base images (Alpine Linux where possible)

### Runtime Optimizations
- Horizontal scaling with replicas
- Connection pooling for databases
- Redis caching for API responses
- Nginx caching for static content
- Resource limits prevent memory leaks

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example`):

```bash
# API Configuration
API_URL=https://api.betterprompts.ai/api/v1

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
POSTGRES_USER=betterprompts
POSTGRES_PASSWORD=secure-password

# Redis
REDIS_URL=redis://:password@redis:6379/0
REDIS_PASSWORD=secure-password

# Authentication
JWT_SECRET=your-secret-key

# LLM APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
```

### Service Ports

| Service | Internal Port | External Port (Dev) |
|---------|--------------|-------------------|
| Frontend | 3000 | 3000 |
| Intent Classifier | 8001 | 8001 |
| Technique Selector | 8002 | 8002 |
| Prompt Generator | 8003 | 8003 |
| Nginx | 80/443 | 80/443 |
| PostgreSQL | 5432 | 5432 |
| Redis | 6379 | 6379 |
| Prometheus | 9090 | 9090 |
| Grafana | 3000 | 3001 |

## 📊 Monitoring

### Metrics Collection

All services export Prometheus metrics:

- Request rate, latency, errors
- CPU and memory usage
- Model inference times
- Cache hit rates
- Database connection pools

### Dashboards

Pre-configured Grafana dashboards for:

- Service overview
- API performance
- ML model metrics
- Infrastructure health
- Business metrics

### Logging

Structured JSON logging to ELK stack:

```bash
# View logs
docker compose logs -f [service-name]

# Search logs in Kibana
http://localhost:5601
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Deploy
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build images
        run: docker compose -f docker-compose.prod.yml build
      
      - name: Run tests
        run: docker compose run --rm test
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker compose -f docker-compose.prod.yml push
```

## 🐛 Troubleshooting

### Common Issues

1. **Service won't start**:
   ```bash
   docker compose logs [service-name]
   docker compose exec [service-name] sh
   ```

2. **Database connection errors**:
   ```bash
   # Check if database is ready
   docker compose exec postgres pg_isready
   
   # Run migrations manually
   docker compose exec technique-selector /app/migrate
   ```

3. **ML model loading issues**:
   ```bash
   # Check model cache
   docker compose exec intent-classifier ls -la /app/models
   
   # Force model download
   docker compose exec intent-classifier python -c "from app.models import load_model; load_model()"
   ```

4. **Performance issues**:
   ```bash
   # Check resource usage
   docker stats
   
   # Scale services
   docker compose up -d --scale prompt-generator=3
   ```

### Health Checks

```bash
# Check all service health endpoints
for service in frontend intent-classifier technique-selector prompt-generator; do
  echo "Checking $service..."
  curl -f http://localhost/api/v1/$service/health || echo "Failed"
done
```

## 🚀 Scaling

### Horizontal Scaling

```bash
# Development
docker compose up -d --scale intent-classifier=3

# Production (Swarm)
docker service scale betterprompts_intent-classifier=5

# Production (Kubernetes)
kubectl scale deployment intent-classifier --replicas=5
```

### Database Scaling

For production, consider:
- PostgreSQL read replicas
- Connection pooling with PgBouncer
- Redis Cluster for cache scaling
- Managed services (AWS RDS, ElastiCache)

## 📚 Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [12-Factor App Methodology](https://12factor.net/)
- [Kubernetes Migration Guide](./k8s/README.md)
- [Security Hardening Guide](./security/README.md)

## 🤝 Contributing

1. Validate changes: `./docker/validate.sh`
2. Test locally: `docker compose up`
3. Run integration tests: `docker compose -f docker-compose.test.yml up`
4. Submit PR with validation results