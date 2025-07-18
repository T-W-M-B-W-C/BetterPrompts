# Technique Selection Engine

The Technique Selection Engine is a rule-based service that selects appropriate prompt engineering techniques based on user intent, text complexity, and other contextual factors.

## Features

- **Rule-Based Selection**: Uses configurable rules to match techniques to requests
- **Multi-Technique Support**: Can suggest multiple compatible techniques
- **Complexity Analysis**: Calculates text complexity for better technique matching
- **Intent-Aware**: Prioritizes techniques based on detected intent
- **Confidence Scoring**: Provides confidence scores for each selected technique
- **RESTful API**: Easy integration with other services

## Architecture

### Components

1. **Rules Engine**: Core logic for technique selection
2. **Configuration**: YAML-based rules and technique definitions
3. **REST API**: Gin-based HTTP server
4. **Models**: Data structures for requests and responses

### Supported Techniques

- **Chain of Thought**: Step-by-step reasoning
- **Tree of Thoughts**: Multiple reasoning paths
- **Few-Shot Learning**: Example-based guidance
- **Zero-Shot Learning**: Direct task completion
- **Self-Consistency**: Multiple attempts with verification
- **Constitutional AI**: Ethical considerations
- **Iterative Refinement**: Progressive improvement
- **Role-Based**: Expertise simulation
- **Structured Output**: Formatted responses
- **Metacognitive**: Reflective problem-solving

## API Endpoints

### Select Techniques
```
POST /api/v1/select
Content-Type: application/json

{
  "text": "How do I implement a binary search tree?",
  "intent": "code_generation",
  "complexity": 0.7,
  "max_techniques": 3
}

Response:
{
  "techniques": [
    {
      "id": "chain_of_thought",
      "name": "Chain of Thought",
      "description": "Step-by-step reasoning...",
      "score": 85.0,
      "confidence": 0.85,
      "reasoning": "matches intent 'code_generation', complexity 0.70 >= 0.50"
    }
  ],
  "primary_technique": "chain_of_thought",
  "confidence": 0.85,
  "reasoning": "Based on intent 'code_generation' and complexity 0.70..."
}
```

### List Techniques
```
GET /api/v1/techniques

Response:
{
  "techniques": [...],
  "total": 10
}
```

### Get Technique Details
```
GET /api/v1/techniques/:id

Response:
{
  "id": "chain_of_thought",
  "name": "Chain of Thought",
  "description": "...",
  "examples": [...],
  "use_cases": [...]
}
```

## Configuration

The service is configured through `configs/rules.yaml`:

```yaml
techniques:
  - id: "chain_of_thought"
    name: "Chain of Thought"
    conditions:
      intents: ["reasoning", "problem_solving"]
      complexity_threshold: 0.5
      keywords: ["explain", "why", "how"]
    template: |
      I'll work through this step-by-step...

selection_rules:
  max_techniques: 3
  min_confidence: 0.7
  compatible_combinations:
    - ["chain_of_thought", "self_consistency"]
```

## Development

### Prerequisites
- Go 1.21+
- Docker (optional)

### Running Locally
```bash
# Install dependencies
go mod download

# Copy environment variables
cp .env.example .env

# Run the service
go run cmd/server/main.go
```

### Building
```bash
# Build binary
go build -o technique-selector cmd/server/main.go

# Build Docker image
docker build -t technique-selector .
```

### Testing
```bash
# Run tests
go test ./...

# Test the API
curl -X POST http://localhost:8002/api/v1/select \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Explain how photosynthesis works",
    "intent": "question_answering",
    "complexity": 0.6
  }'
```

## Integration

The Technique Selection Engine integrates with:
- **Intent Classifier**: Receives intent classifications
- **API Gateway**: Provides technique selection as part of the enhancement flow
- **Prompt Generator**: Selected techniques guide prompt generation

## Environment Variables

- `PORT`: Server port (default: 8002)
- `GIN_MODE`: Gin framework mode (debug/release)
- `LOG_LEVEL`: Logging level (debug/info/warn/error)
- `RULES_CONFIG_PATH`: Path to rules configuration file
- `METRICS_ENABLED`: Enable Prometheus metrics
- `METRICS_PORT`: Metrics server port

## Monitoring

The service exposes:
- Health check: `/health`
- Readiness check: `/ready`
- Prometheus metrics: `:9092/metrics` (when enabled)