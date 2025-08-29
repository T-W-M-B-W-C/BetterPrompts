# BetterPrompts Test Infrastructure

This directory contains the comprehensive test infrastructure for the BetterPrompts project, including unit tests, integration tests, E2E tests, and performance tests.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- 8GB+ RAM available
- Ports 5433, 6380, 8081-8086 available

### Setup
```bash
# Make setup script executable and run it
chmod +x scripts/setup-test-env.sh
./scripts/setup-test-env.sh
```

### Run All Tests
```bash
# Using Docker Compose
docker compose -f docker-compose.test.yml up

# Using Makefile
make -f Makefile.test test
```

## 📂 Directory Structure

```
tests/
├── mocks/                    # Mock services
│   ├── torchserve/          # Mock ML inference server
│   │   ├── Dockerfile
│   │   ├── mock_server.py
│   │   └── responses.json
│   └── wiremock/            # Mock external APIs
│       ├── mappings/        # Request/response mappings
│       └── __files/         # Static response files
├── e2e/                     # End-to-end tests
│   ├── specs/               # Test specifications
│   ├── Dockerfile.playwright
│   └── results/             # Test results
├── performance/             # Performance tests
│   ├── scripts/             # k6 test scripts
│   │   ├── baseline-test.js
│   │   └── load-test.js
│   ├── analyze_results.py
│   └── results/             # Performance test results
├── scripts/                 # Test execution scripts
│   ├── run-all-tests.sh
│   ├── test-service.sh
│   ├── wait-for-services.sh
│   └── coverage-report.sh
├── Dockerfile.testrunner    # Test runner container
└── README.md               # This file
```

## 🧪 Test Types

### Unit Tests
Tests individual components in isolation.

```bash
# Run all unit tests
make -f Makefile.test test-unit

# Run tests for specific service
docker compose -f docker-compose.test.yml run --rm test-runner \
  ./tests/scripts/test-service.sh api-gateway
```

### Integration Tests
Tests interactions between services and external dependencies.

```bash
# Run integration tests
make -f Makefile.test test-integration
```

### E2E Tests
Tests complete user workflows using Playwright.

```bash
# Run E2E tests
make -f Makefile.test test-e2e

# Run with UI (non-headless)
docker compose -f docker-compose.test.yml run --rm \
  -e HEADLESS=false playwright
```

### Performance Tests
Tests system performance using k6.

```bash
# Run performance tests
make -f Makefile.test test-performance

# Run specific performance test
docker compose -f docker-compose.test.yml run --rm k6 \
  run --vus 50 --duration 10m /scripts/load-test.js
```

### Security Tests
Scans for vulnerabilities and security issues.

```bash
# Run security tests
make -f Makefile.test test-security
```

## 🔧 Mock Services

### Mock TorchServe
Simulates ML model inference with configurable behavior.

**Configuration**:
- `MOCK_LATENCY_MS`: Simulated inference latency (default: 100ms)
- `MOCK_ERROR_RATE`: Error rate for testing resilience (0-1)

**Endpoints**:
- `GET /ping` - Health check
- `POST /predictions/intent_classifier` - Classify intent
- `GET /models` - List available models

### WireMock
Mocks external API calls (OpenAI, Anthropic).

**Configuration**:
- Mappings in `tests/mocks/wiremock/mappings/`
- Supports response templating
- Configurable latency and error simulation

## 📊 Coverage Reports

### Generate Coverage Report
```bash
# Generate combined coverage report
make -f Makefile.test coverage

# View HTML report
open coverage/index.html
```

### Coverage Thresholds
- Overall: 80% minimum
- Critical paths: 95% minimum
- New code: 90% minimum

## 🔍 Test Development

### Adding New Tests

#### Unit Test Template (Go)
```go
func TestMyFunction(t *testing.T) {
    // Arrange
    expected := "expected result"
    
    // Act
    result := MyFunction()
    
    // Assert
    assert.Equal(t, expected, result)
}
```

#### Unit Test Template (Python)
```python
def test_my_function():
    # Arrange
    expected = "expected result"
    
    # Act
    result = my_function()
    
    # Assert
    assert result == expected
```

#### E2E Test Template (Playwright)
```typescript
test('should complete user flow', async ({ page }) => {
    await page.goto('/');
    await page.fill('[data-testid="prompt-input"]', 'Test prompt');
    await page.click('[data-testid="enhance-button"]');
    
    await expect(page.locator('[data-testid="result"]')).toBeVisible();
});
```

### Running Tests in Development

#### Watch Mode
```bash
# Run tests in watch mode
make -f Makefile.test test-watch
```

#### Debugging Tests
```bash
# Run with debugging enabled (Go)
docker compose -f docker-compose.test.yml run --rm test-runner \
  dlv test ./backend/services/api-gateway/handlers

# Run with debugging enabled (Python)
docker compose -f docker-compose.test.yml run --rm test-runner \
  python -m pytest --pdb backend/services/intent-classifier/tests/
```

## 🚨 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check for services using test ports
lsof -i :5433  # Test PostgreSQL
lsof -i :6380  # Test Redis
lsof -i :8081  # Mock TorchServe

# Kill conflicting processes
kill -9 <PID>
```

#### Docker Issues
```bash
# Clean up Docker resources
docker compose -f docker-compose.test.yml down -v
docker system prune -f

# Rebuild containers
docker compose -f docker-compose.test.yml build --no-cache
```

#### Test Failures
```bash
# View detailed logs
docker compose -f docker-compose.test.yml logs <service-name>

# Run specific test with verbose output
docker compose -f docker-compose.test.yml run --rm test-runner \
  go test -v ./path/to/test
```

## 📈 Performance Baselines

### Expected Performance Metrics
- API Response Time: p95 < 200ms
- ML Inference: p95 < 500ms
- Database Queries: p95 < 50ms
- Cache Operations: p95 < 10ms

### Load Test Targets
- Sustained: 10,000 RPS
- Burst: 15,000 RPS
- Error Rate: < 0.1%
- Success Rate: > 99.9%

## 🔗 CI/CD Integration

Tests are automatically run in CI/CD pipeline on:
- Every pull request
- Pushes to main branch
- Nightly scheduled runs

See `.github/workflows/test-suite.yml` for configuration.

## 📚 Additional Resources

- [Testing Strategy](../planning/testing-strategy.md)
- [Test Implementation Templates](../planning/test-implementation-templates.md)
- [Test Infrastructure Guide](../planning/test-infrastructure-guide.md)
- [Test Orchestration Guide](../planning/test-orchestration-guide.md)

## 🤝 Contributing

When adding new tests:
1. Follow existing patterns and conventions
2. Ensure tests are deterministic and isolated
3. Add appropriate test data and fixtures
4. Update coverage thresholds if needed
5. Document any new mock services or test utilities

For questions or issues, please refer to the testing documentation or contact the QA team.