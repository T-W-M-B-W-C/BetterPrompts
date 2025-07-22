# BetterPrompts Test Infrastructure Guide

## Overview

This guide provides detailed instructions for using the BetterPrompts test infrastructure, including setup, execution, and maintenance of tests across all system components.

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- Go 1.23+, Node.js 20+, Python 3.11+ for local development
- 8GB+ RAM recommended for running full test suite

### Running Tests Locally

```bash
# Run all tests in Docker
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Run specific service tests
docker compose -f docker-compose.test.yml run --rm test-runner ./scripts/test-service.sh api-gateway

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration

# Run E2E tests with UI
HEADLESS=false docker compose -f docker-compose.test.yml run --rm playwright
```

## Test Infrastructure Components

### 1. Mock Services

#### Mock TorchServe
Simulates ML model inference with configurable latency and error rates.

**Configuration**:
```yaml
environment:
  MOCK_LATENCY_MS: 100  # Simulated inference time
  MOCK_ERROR_RATE: 0     # Error rate (0-1)
  MOCK_RESPONSES_FILE: /app/responses.json
```

**Usage in tests**:
```python
# Python example
@pytest.fixture
def mock_torchserve(mocker):
    return mocker.patch(
        'app.services.torchserve_client.predict',
        return_value={'intent': 'code_generation', 'confidence': 0.95}
    )
```

#### WireMock
Provides mock external API responses with request matching.

**Setup stubs**:
```json
// tests/mocks/wiremock/mappings/openai-completion.json
{
  "request": {
    "method": "POST",
    "urlPath": "/v1/completions"
  },
  "response": {
    "status": 200,
    "jsonBody": {
      "choices": [{
        "text": "Enhanced prompt with Chain of Thought..."
      }]
    },
    "transformers": ["response-template"]
  }
}
```

### 2. Test Databases

#### PostgreSQL Test Instance
- Port: 5433 (to avoid conflicts)
- Database: `betterprompts_test`
- Auto-migrated with test schema

#### Redis Test Instance
- Port: 6380 (to avoid conflicts)
- Persistence disabled for speed
- Flushed between test suites

### 3. Test Data Management

#### Fixtures
```python
# backend/services/intent-classifier/tests/fixtures.py
import pytest
from app.models import Intent

@pytest.fixture
def sample_intents():
    return [
        Intent(text="Write a Python function", label="code_generation"),
        Intent(text="Explain quantum computing", label="explanation"),
        Intent(text="Debug this code", label="debugging")
    ]
```

#### Factories
```go
// backend/services/api-gateway/tests/factories/user.go
package factories

import (
    "github.com/brianvoe/gofakeit/v6"
    "betterprompts/models"
)

func NewUser() *models.User {
    return &models.User{
        Email:    gofakeit.Email(),
        Username: gofakeit.Username(),
        Role:     "user",
    }
}
```

#### Seeders
```typescript
// frontend/tests/seeders/prompt-seeder.ts
export class PromptSeeder {
  static async seedDatabase() {
    const prompts = [
      { text: "Test prompt 1", techniques: ["cot"] },
      { text: "Test prompt 2", techniques: ["few_shot", "tot"] }
    ];
    
    for (const prompt of prompts) {
      await api.post('/prompts', prompt);
    }
  }
}
```

## Testing Patterns & Best Practices

### 1. Unit Testing

#### Go Services
```go
// backend/services/api-gateway/handlers/enhance_test.go
package handlers_test

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

func TestEnhanceHandler_Success(t *testing.T) {
    // Arrange
    mockClassifier := new(mocks.ClassifierService)
    mockClassifier.On("Classify", mock.Anything).Return(&Classification{
        Intent: "code_generation",
        Confidence: 0.95,
    }, nil)
    
    handler := NewEnhanceHandler(mockClassifier)
    
    // Act
    resp := handler.Enhance(context.Background(), &EnhanceRequest{
        Prompt: "Write a function to sort an array",
    })
    
    // Assert
    assert.NoError(t, resp.Error)
    assert.Equal(t, "code_generation", resp.Intent)
    mockClassifier.AssertExpectations(t)
}
```

#### Python Services
```python
# backend/services/prompt-generator/tests/test_generator.py
import pytest
from unittest.mock import AsyncMock
from app.services.generator import PromptGenerator

@pytest.mark.asyncio
async def test_generate_with_cot():
    # Arrange
    generator = PromptGenerator()
    generator.llm_client = AsyncMock()
    generator.llm_client.complete.return_value = "Step 1: Understand...\nStep 2: Plan..."
    
    # Act
    result = await generator.generate(
        prompt="Solve this problem",
        techniques=["chain_of_thought"]
    )
    
    # Assert
    assert "Step 1:" in result
    assert "Step 2:" in result
    generator.llm_client.complete.assert_called_once()
```

#### Frontend Components
```typescript
// frontend/tests/components/PromptInput.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { PromptInput } from '@/components/PromptInput';

describe('PromptInput', () => {
  it('should call onSubmit with input value', async () => {
    // Arrange
    const mockSubmit = jest.fn();
    render(<PromptInput onSubmit={mockSubmit} />);
    
    // Act
    const input = screen.getByPlaceholderText('Enter your prompt...');
    fireEvent.change(input, { target: { value: 'Test prompt' } });
    fireEvent.submit(screen.getByRole('form'));
    
    // Assert
    expect(mockSubmit).toHaveBeenCalledWith('Test prompt');
  });
});
```

### 2. Integration Testing

#### Service-to-Service
```python
# tests/integration/test_api_to_classifier.py
import pytest
from httpx import AsyncClient

@pytest.mark.integration
async def test_enhance_flow_integration():
    async with AsyncClient(base_url="http://api-gateway:8080") as client:
        # Test full enhancement flow
        response = await client.post("/api/v1/enhance", json={
            "prompt": "Write a sorting algorithm",
            "user_id": "test-user"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "code_generation"
        assert len(data["techniques"]) > 0
        assert "enhanced_prompt" in data
```

#### Database Integration
```go
// tests/integration/database_test.go
func TestUserRepository_Integration(t *testing.T) {
    if testing.Short() {
        t.Skip("Skipping integration test")
    }
    
    // Setup test database
    db := setupTestDB(t)
    defer cleanupTestDB(t, db)
    
    repo := repositories.NewUserRepository(db)
    
    // Test Create
    user := &models.User{Email: "test@example.com"}
    err := repo.Create(context.Background(), user)
    assert.NoError(t, err)
    assert.NotZero(t, user.ID)
    
    // Test Find
    found, err := repo.FindByEmail(context.Background(), "test@example.com")
    assert.NoError(t, err)
    assert.Equal(t, user.ID, found.ID)
}
```

### 3. End-to-End Testing

#### Playwright Tests
```typescript
// tests/e2e/specs/enhancement-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Enhancement Flow', () => {
  test('should enhance a prompt with multiple techniques', async ({ page }) => {
    // Navigate to app
    await page.goto('/');
    
    // Input prompt
    await page.fill('[data-testid="prompt-input"]', 'Explain recursion');
    await page.click('[data-testid="enhance-button"]');
    
    // Wait for classification
    await expect(page.locator('[data-testid="intent-display"]'))
      .toContainText('explanation');
    
    // Select techniques
    await page.check('[data-testid="technique-cot"]');
    await page.check('[data-testid="technique-examples"]');
    
    // Apply enhancement
    await page.click('[data-testid="apply-button"]');
    
    // Verify enhanced prompt
    await expect(page.locator('[data-testid="enhanced-prompt"]'))
      .toContainText('Step 1:');
    await expect(page.locator('[data-testid="enhanced-prompt"]'))
      .toContainText('Example:');
  });
});
```

### 4. Performance Testing

#### k6 Load Tests
```javascript
// tests/performance/scripts/load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 200 },  // Ramp to 200
    { duration: '5m', target: 200 },  // Stay at 200
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    errors: ['rate<0.01'],            // Error rate under 1%
  },
};

export default function () {
  const payload = JSON.stringify({
    prompt: 'Write a function to calculate fibonacci',
    user_id: `user_${__VU}`,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${__ENV.API_TOKEN}`,
    },
  };

  const res = http.post(`${__ENV.API_URL}/api/v1/enhance`, payload, params);
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
    'has enhanced_prompt': (r) => JSON.parse(r.body).enhanced_prompt !== undefined,
  });

  errorRate.add(res.status !== 200);
  sleep(1);
}
```

## Test Execution Strategies

### Local Development
```bash
# Run tests while developing
npm run test:watch          # Frontend
go test ./... -v           # Go services
pytest --watch             # Python services

# Run with debugging
dlv test ./handlers        # Go debugger
pytest --pdb              # Python debugger
npm run test:debug        # Node debugger
```

### CI/CD Pipeline
Tests run automatically on:
- Every pull request
- Pushes to main branch
- Scheduled nightly runs

### Test Parallelization
```yaml
# Frontend parallel execution
jest.config.js:
  maxWorkers: '50%'

# Go parallel execution
go test -parallel 4 ./...

# Python parallel execution
pytest -n auto

# E2E parallel execution
playwright.config.ts:
  workers: process.env.CI ? 2 : 4
```

## Debugging Failed Tests

### 1. Accessing Test Artifacts
```bash
# Download artifacts from CI
gh run download <run-id> -n test-results

# View local artifacts
open coverage/index.html
open test-results/report.html
```

### 2. Reproducing CI Failures Locally
```bash
# Use exact same environment as CI
docker compose -f docker-compose.test.yml run \
  --rm \
  -e CI=true \
  test-runner ./scripts/test-service.sh <service>
```

### 3. Common Issues & Solutions

#### Port Conflicts
```bash
# Check for conflicting services
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8080  # Services

# Use test-specific ports
export TEST_DB_PORT=5433
export TEST_REDIS_PORT=6380
```

#### Flaky Tests
```javascript
// Add retries for flaky tests
test.describe('Flaky Feature', () => {
  test.describe.configure({ retries: 2 });
  
  test('sometimes fails', async ({ page }) => {
    // Test implementation
  });
});
```

#### Timeout Issues
```python
# Increase timeout for slow operations
@pytest.mark.timeout(30)  # 30 seconds
async def test_slow_operation():
    # Test implementation
    pass
```

## Test Maintenance

### 1. Updating Mock Data
```bash
# Update TorchServe mock responses
vim tests/mocks/torchserve/responses.json

# Update WireMock stubs
vim tests/mocks/wiremock/mappings/*.json

# Regenerate fixtures
make generate-fixtures
```

### 2. Test Database Migrations
```bash
# Apply migrations to test database
docker compose -f docker-compose.test.yml run \
  --rm \
  api-gateway \
  ./scripts/migrate.sh
```

### 3. Coverage Reports
```bash
# Generate combined coverage report
./scripts/coverage-report.sh

# View coverage gaps
open coverage/index.html

# Check specific service coverage
go tool cover -html=coverage.out
```

## Best Practices

### 1. Test Naming
```python
# Good: Descriptive and specific
def test_enhance_with_invalid_prompt_returns_400():
    pass

# Bad: Vague
def test_enhance():
    pass
```

### 2. Test Isolation
```go
// Good: Each test sets up its own data
func TestHandler(t *testing.T) {
    t.Run("success case", func(t *testing.T) {
        // Independent setup
        db := setupTestDB(t)
        defer cleanupTestDB(t, db)
        // Test implementation
    })
}
```

### 3. Assertion Messages
```typescript
// Good: Clear failure messages
expect(response.status, 'API should return success status').toBe(200);

// Bad: No context
expect(response.status).toBe(200);
```

### 4. Test Data Builders
```python
# Good: Flexible test data creation
class PromptBuilder:
    def __init__(self):
        self._prompt = {
            "text": "Default prompt",
            "user_id": "test-user",
            "techniques": []
        }
    
    def with_text(self, text):
        self._prompt["text"] = text
        return self
    
    def with_techniques(self, techniques):
        self._prompt["techniques"] = techniques
        return self
    
    def build(self):
        return self._prompt

# Usage
prompt = PromptBuilder()
    .with_text("Complex prompt")
    .with_techniques(["cot", "few_shot"])
    .build()
```

## Continuous Improvement

### 1. Test Metrics Dashboard
Access at: `http://localhost:3002/dashboard/test-metrics`
- Test execution times
- Flaky test tracking
- Coverage trends
- Failure analysis

### 2. Regular Test Reviews
- Weekly: Review and fix flaky tests
- Monthly: Update test data and mocks
- Quarterly: Refactor test architecture

### 3. Test Performance Optimization
```bash
# Profile slow tests
go test -cpuprofile cpu.prof -memprofile mem.prof
pytest --profile

# Optimize test database
docker compose -f docker-compose.test.yml exec test-postgres \
  psql -U test_user -c "VACUUM ANALYZE;"
```

## Troubleshooting

### Common Error Messages

#### "Connection refused" errors
```bash
# Ensure services are running
docker compose -f docker-compose.test.yml ps

# Check service health
docker compose -f docker-compose.test.yml exec api-gateway curl localhost:8080/health
```

#### "Database migration pending"
```bash
# Run migrations
docker compose -f docker-compose.test.yml run --rm api-gateway ./scripts/migrate.sh
```

#### "Mock service not responding"
```bash
# Restart mock services
docker compose -f docker-compose.test.yml restart mock-torchserve wiremock

# Check mock service logs
docker compose -f docker-compose.test.yml logs mock-torchserve
```

## Support

For test infrastructure issues:
1. Check this guide first
2. Search existing issues: `github.com/betterprompts/issues`
3. Contact the QA team: `qa@betterprompts.com`
4. Emergency: Page the on-call engineer

Remember: A well-tested system is a reliable system. Invest in tests today to save debugging time tomorrow!