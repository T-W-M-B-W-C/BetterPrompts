# Prompt Generation Service

The Prompt Generation Service is responsible for applying advanced prompt engineering techniques to transform user inputs into optimized prompts for various Large Language Models (LLMs).

## Features

- **10 Prompt Engineering Techniques**: Chain of Thought, Tree of Thoughts, Few-Shot, Zero-Shot, Role Play, Step-by-Step, Structured Output, Emotional Appeal, Constraints, and Analogical Reasoning
- **Intelligent Technique Selection**: Automatically applies appropriate techniques based on intent and complexity
- **Validation & Scoring**: Validates prompts and provides quality metrics
- **Batch Processing**: Support for processing multiple prompts efficiently
- **Extensible Architecture**: Easy to add new techniques through the plugin system

## Architecture

The service is built with FastAPI and follows a modular architecture:

```
app/
├── main.py              # FastAPI application and endpoints
├── engine.py            # Core prompt generation engine
├── validators.py        # Prompt validation and scoring
├── models.py            # Pydantic models
├── config.py            # Configuration management
├── health.py            # Health check endpoints
└── techniques/          # Prompt engineering techniques
    ├── base.py          # Base technique class and registry
    ├── chain_of_thought.py
    ├── tree_of_thoughts.py
    ├── few_shot.py
    ├── zero_shot.py
    ├── role_play.py
    ├── step_by_step.py
    ├── structured_output.py
    ├── emotional_appeal.py
    ├── constraints.py
    └── analogical.py
```

## API Endpoints

### Generate Enhanced Prompt
```http
POST /api/v1/generate
Content-Type: application/json

{
  "text": "Explain quantum computing",
  "intent": "explanation",
  "complexity": 0.7,
  "techniques": ["chain_of_thought", "analogical"],
  "context": {
    "audience": "beginners",
    "max_length": 500
  }
}
```

Response:
```json
{
  "text": "Enhanced prompt with techniques applied...",
  "model_version": "0.1.0",
  "tokens_used": 150
}
```

### Batch Generation
```http
POST /api/v1/generate/batch
Content-Type: application/json

{
  "prompts": [
    {
      "text": "First prompt",
      "intent": "analysis",
      "complexity": 0.5,
      "techniques": ["step_by_step"]
    },
    {
      "text": "Second prompt",
      "intent": "creative",
      "complexity": 0.3,
      "techniques": ["role_play", "emotional_appeal"]
    }
  ]
}
```

### List Available Techniques
```http
GET /api/v1/techniques
```

### Health Checks
```http
GET /health/           # Basic health check
GET /health/live       # Kubernetes liveness probe
GET /health/ready      # Kubernetes readiness probe
GET /health/detailed   # Detailed system information
```

## Prompt Engineering Techniques

### 1. Chain of Thought (CoT)
Encourages step-by-step reasoning by explicitly asking the model to show its thinking process.

**Best for**: Complex reasoning, problem solving, analysis
**Example**: "Let's approach this step-by-step..."

### 2. Tree of Thoughts (ToT)
Explores multiple reasoning paths and evaluates different approaches before selecting the best solution.

**Best for**: Complex problems, optimization, strategic planning
**Example**: "Let's explore multiple approaches to this problem..."

### 3. Few-Shot Learning
Provides examples of input-output pairs to guide the model's behavior.

**Best for**: Pattern matching, formatting, classification
**Example**: Includes 2-5 examples before the actual prompt

### 4. Zero-Shot Learning
Provides clear instructions without examples, relying on the model's pre-trained knowledge.

**Best for**: Straightforward tasks, general queries
**Example**: Direct instructions with constraints

### 5. Role Playing
Assigns a specific role or persona to the model to influence its responses.

**Best for**: Expert advice, specialized knowledge
**Example**: "You are an expert data scientist..."

### 6. Step-by-Step
Breaks down complex tasks into clear, sequential steps.

**Best for**: Procedures, tutorials, workflows
**Example**: "Step 1: ... Step 2: ..."

### 7. Structured Output
Requests responses in specific formats like JSON, tables, or markdown.

**Best for**: Data extraction, formatting, organization
**Example**: "Provide your response in JSON format..."

### 8. Emotional Appeal
Adds emotional context to motivate more engaged responses.

**Best for**: Creative tasks, persuasion
**Example**: "This is really important to me..."

### 9. Constraints
Adds specific requirements and boundaries to guide responses.

**Best for**: Precision tasks, compliance
**Example**: "Ensure your response: 1. Is under 200 words..."

### 10. Analogical Reasoning
Uses analogies to explain complex concepts.

**Best for**: Explanation, teaching, understanding
**Example**: "Think of it like..."

## Configuration

The service can be configured through environment variables:

```bash
# Server
PORT=8003
HOST=0.0.0.0
WORKERS=4

# Model Settings
MAX_PROMPT_LENGTH=4096
DEFAULT_TEMPERATURE=0.7

# Features
ENABLE_CACHING=true
ENABLE_METRICS=true
ENABLE_VALIDATION=true

# External Services
INTENT_CLASSIFIER_URL=http://intent-classifier:8001
TECHNIQUE_SELECTOR_URL=http://technique-selector:8002
```

## Development

### Prerequisites
- Python 3.11+
- Poetry or pip for dependency management

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python -m uvicorn app.main:app --reload --port 8003
```

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app
```

### Docker
```bash
# Build image
docker build -t prompt-generator:latest .

# Run container
docker run -p 8003:8003 prompt-generator:latest
```

## Performance Metrics

The service includes Prometheus metrics:
- Request count and duration
- Prompt generation duration by technique
- System resource usage

Access metrics at `/metrics` endpoint.

## Integration

The service integrates with:
- **Intent Classification Service**: To understand user intent
- **Technique Selection Engine**: For optimal technique selection
- **API Gateway**: For authentication and routing

## License

Proprietary - BetterPrompts