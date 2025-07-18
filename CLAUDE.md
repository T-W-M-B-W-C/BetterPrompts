# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BetterPrompts is a Prompt Engineering Assistant project designed to democratize advanced prompt engineering techniques for non-technical users. The system analyzes natural language input and automatically suggests or applies optimal prompting strategies (Chain of Thought, Tree of Thoughts, Few-shot learning, etc.) without requiring users to understand the underlying techniques.

## Project Status

Currently in the planning phase with comprehensive architecture and implementation roadmap documents. No code implementation has started yet.

## Repository Structure

```
BetterPrompts/
├── planning/              # Architecture and design documents
│   ├── prompt-engineering-assistant-plan.md        # Project vision and development phases
│   ├── prompt-engineering-assistant-architecture.md # Detailed system architecture
│   ├── implementation-roadmap.md                   # Wave-based implementation strategy
│   ├── assistant-api-design.md                    # API specification
│   ├── prompt-classifier-component-design.md      # ML classification component
│   ├── prompt-patterns-database-design.md         # Database schema design
│   └── user-interface-component-design.md         # Frontend component design
└── .gitignore
```

## Key Architecture Decisions

### Technology Stack
- **Frontend**: Next.js 14+ with TypeScript, React 18+, Tailwind CSS
- **Backend Services**:
  - Intent Classification Service: Python 3.11+ with FastAPI
  - Technique Selection Engine: Go 1.21+ with Gin
  - Prompt Generation Service: Python 3.11+ with FastAPI
- **Databases**: PostgreSQL (primary) with pgvector, Redis (cache), Pinecone (vector DB)
- **ML Framework**: Transformers, PyTorch, Fine-tuned DeBERTa-v3
- **Infrastructure**: Kubernetes, Docker, AWS/GCP
- **Message Queue**: RabbitMQ/Kafka

### Core Components
1. **Intent Classification Engine**: Analyzes user input to identify task type and complexity
2. **Technique Selection Engine**: Matches intents to optimal prompt engineering techniques
3. **Prompt Generation Service**: Applies techniques to generate enhanced prompts
4. **User Interface**: Simple input with technique suggestions and educational tooltips
5. **Learning Component**: Tracks technique effectiveness and personalizes recommendations

## Development Commands

### Initial Setup (When Implementation Begins)
```bash
# These commands are planned but not yet implemented
# Infrastructure setup
terraform init
terraform apply

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
```

### Development Workflow (Future)
```bash
# Backend services
cd backend/services/intent-classifier
python -m uvicorn main:app --reload

# Frontend
cd frontend
npm run dev

# Run tests (when implemented)
pytest backend/tests
npm run test frontend
```

## Implementation Phases

The project follows a wave-based implementation strategy:

1. **Wave 1 (Weeks 1-6)**: Foundation - Core infrastructure, ML pipeline, basic API, MVP UI
2. **Wave 2 (Weeks 7-12)**: Enhanced Capabilities - Advanced ML, UX improvements, performance optimization
3. **Wave 3 (Weeks 13-18)**: Enterprise Features - Security, team collaboration, compliance
4. **Wave 4 (Weeks 19-24)**: Market Expansion - Public launch, community building

## Key Design Patterns

### Domain-Driven Design
The system is organized into bounded contexts:
- **UserManagement**: Authentication, profiles, preferences
- **PromptEngineering**: Intent classification, technique selection, prompt generation
- **Learning**: Feedback processing, personalization, model training
- **Analytics**: Metrics, reporting, business intelligence

### API Design
RESTful endpoints with potential GraphQL layer:
- `POST /api/v1/enhance` - Main enhancement endpoint
- `POST /api/v1/analyze` - Intent analysis
- `GET /api/v1/techniques` - Available techniques

### Security Considerations
- JWT authentication with refresh tokens
- End-to-end encryption for sensitive data
- Role-based access control (RBAC)
- API rate limiting by tier
- SOC 2 compliance target

## Performance Requirements

- **API Response Time**: p95 < 200ms
- **Model Inference**: p95 < 500ms
- **Availability**: 99.9% uptime SLA
- **Throughput**: 10,000 sustained RPS

## ML Model Management

- Intent classifier based on fine-tuned DeBERTa-v3
- Initial target: 80% accuracy, improving to 90%+ 
- A/B testing framework for model improvements
- Drift detection and monitoring

## Testing Strategy

When implemented, the project will include:
- Unit tests for all services
- Integration tests for API endpoints
- E2E tests for critical user flows
- ML model validation pipeline
- Performance benchmarking

## Important Notes

1. This is a greenfield project in planning phase - no code exists yet
2. All technology decisions are documented but subject to change during implementation
3. The planning documents contain SuperClaude commands for future development phases
4. Budget estimation: ~$1.3M for 6-month development, $245K/month ongoing costs
5. Target: 10,000 active users within 6 months of launch