# BetterPrompts Architecture Overview

## System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        CLIENT[API Clients<br/>curl/httpx/requests]
        CLIENT --> |HTTP Requests| NGINX
    end
    
    subgraph "API Gateway"
        NGINX[NGINX<br/>:80]
    end
    
    subgraph "Microservices Layer"
        NGINX --> IC[Intent Classifier<br/>Python/FastAPI<br/>:8001]
        NGINX --> TS[Technique Selector<br/>Go/Gin<br/>:8002]
        NGINX --> PG[Prompt Generator<br/>Python/FastAPI<br/>:8003]
        
        PG -.->|Auto-select<br/>techniques| TS
    end
    
    subgraph "Data Layer"
        IC --> ML[DistilBERT Model<br/>models/]
        TS --> RULES[rules.yaml<br/>configs/]
        PG --> TECH[Technique<br/>Templates]
    end
    
    subgraph "Infrastructure"
        DOCKER[Docker Compose]
        DOCKER --> |Orchestrates| NGINX
        DOCKER --> |Orchestrates| IC
        DOCKER --> |Orchestrates| TS
        DOCKER --> |Orchestrates| PG
    end
```

## Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant NGINX
    participant IntentClassifier
    participant TechniqueSelector
    participant PromptGenerator
    
    Client->>NGINX: POST /api/v1/classify
    NGINX->>IntentClassifier: Classify intent
    IntentClassifier-->>NGINX: Return intent
    NGINX-->>Client: Intent classification
    
    alt Automatic Selection
        Client->>NGINX: POST /api/v1/generate (no techniques)
        NGINX->>PromptGenerator: Generate request
        PromptGenerator->>TechniqueSelector: POST /api/v1/select
        TechniqueSelector-->>PromptGenerator: Return techniques
        PromptGenerator-->>NGINX: Enhanced prompt
        NGINX-->>Client: Response with auto-selected techniques
    else Manual Selection
        Client->>NGINX: POST /api/v1/generate (with techniques)
        NGINX->>PromptGenerator: Generate with specified techniques
        PromptGenerator-->>NGINX: Enhanced prompt
        NGINX-->>Client: Response with manual techniques
    end
```

## Directory Structure

```
BetterPrompts/
│
├── backend/
│   └── services/
│       ├── intent-classifier/   # Python/FastAPI Service
│       │   ├── app/
│       │   │   ├── main.py     # FastAPI app
│       │   │   ├── models.py   # Data models
│       │   │   └── classifier.py # ML logic
│       │   ├── models/         # DistilBERT model
│       │   └── Dockerfile
│       │
│       ├── technique-selector/  # Go/Gin Service
│       │   ├── cmd/            # Main application
│       │   ├── internal/       # Business logic
│       │   │   ├── handlers/   # HTTP handlers
│       │   │   ├── rules/      # Selection engine
│       │   │   └── models/     # Data structures
│       │   ├── configs/
│       │   │   └── rules.yaml  # Selection rules
│       │   └── Dockerfile
│       │
│       └── prompt-generator/    # Python/FastAPI Service
│           ├── app/
│           │   ├── main.py     # FastAPI app
│           │   ├── engine.py   # Generation logic
│           │   ├── models.py   # Request/Response
│           │   └── techniques/ # Technique implementations
│           └── Dockerfile
│
├── docker/
│   └── nginx/
│       └── conf.d/
│           └── api.conf        # Routing rules
│
├── docker-compose.yml          # Service orchestration
│
├── scripts/                     # Utility scripts
│   └── setup_git_lfs.sh
│
├── Justfile                    # Main test commands
├── test-prompts.just           # Scenario tests
├── diagnostic.just             # Troubleshooting
└── TEST_COMMANDS.md            # Test documentation
```

## Service Details

### 1. Intent Classifier (Port 8001)
```yaml
Technology: Python 3.11, FastAPI, PyTorch
Model: DistilBERT (fine-tuned)
Purpose: Classify user intent from text
Endpoints:
  - POST /classify
  - GET /health
Response Time: ~200ms
```

### 2. Technique Selector (Port 8002)
```yaml
Technology: Go 1.21, Gin Framework
Configuration: YAML-based rules engine
Purpose: Select optimal prompt techniques
Endpoints:
  - POST /api/v1/select
  - GET /health
Features:
  - Score-based selection
  - Complexity filtering
  - Confidence thresholds
Response Time: ~50ms
```

### 3. Prompt Generator (Port 8003)
```yaml
Technology: Python 3.11, FastAPI
Integration: Calls Technique Selector
Purpose: Apply techniques to enhance prompts
Endpoints:
  - POST /api/v1/generate
  - GET /api/v1/techniques
  - GET /health
Techniques:
  - zero_shot
  - few_shot
  - chain_of_thought
  - structured_output
  - self_consistency
  - analogical
Response Time: ~100-300ms
```

## Data Flow

```mermaid
graph LR
    subgraph "Input Processing"
        A[User Input] --> B[Intent Classification]
        B --> C{Has Techniques?}
    end
    
    subgraph "Technique Selection"
        C -->|No| D[Auto-Select]
        D --> E[Score Techniques]
        E --> F[Filter by Confidence]
        F --> G[Apply Thresholds]
    end
    
    subgraph "Prompt Generation"
        C -->|Yes| H[Manual Techniques]
        G --> I[Merge Techniques]
        H --> I
        I --> J[Apply Templates]
        J --> K[Generate Output]
    end
    
    K --> L[Enhanced Prompt]
```

## Configuration

### Docker Compose Services
```yaml
services:
  nginx:             # Port 80
  intent-classifier: # Port 8001
  technique-selector: # Port 8002  
  prompt-generator:   # Port 8003
```

### NGINX Routing
```nginx
/api/intent → intent-classifier:8001
/api/techniques → technique-selector:8002
/api/enhance → prompt-generator:8003
```

## Testing Infrastructure

```mermaid
graph TD
    subgraph "Test Commands"
        J[Justfile] --> |orchestrates| TC[Test Commands]
        TC --> ST[Smoke Tests]
        TC --> IT[Integration Tests]
        TC --> PT[Performance Tests]
    end
    
    subgraph "Diagnostic Tools"
        D[diagnostic.just] --> |troubleshooting| DT[Debug Tools]
        DT --> TS[Technique Debug]
        DT --> CM[Communication Check]
        DT --> SR[System Report]
    end
    
    subgraph "Scenario Tests"
        TP[test-prompts.just] --> |scenarios| SC[Test Scenarios]
        SC --> CI[Code Intent]
        SC --> RI[Reasoning Intent]
        SC --> CW[Creative Writing]
    end
```

## Key Integration Points

1. **Prompt Generator ↔ Technique Selector**
   - Automatic technique selection when not specified
   - Fallback to zero_shot on failure
   - Filters unknown techniques

2. **Client ↔ Backend Services**
   - All traffic routed through NGINX
   - RESTful API communication
   - JSON request/response format
   - Tested via curl/Just commands

3. **Service Discovery**
   - Docker Compose internal networking
   - Service names as hostnames
   - Health checks for availability

## Deployment

```bash
# Development
docker compose up -d

# Testing
just test-integration

# Monitoring
just health
just logs [service]
```