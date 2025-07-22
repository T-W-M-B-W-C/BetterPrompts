# Intent Classifier Service Test Documentation

## Overview

This document provides comprehensive documentation for the unit and integration tests of the Intent Classifier Service. The test suite ensures reliability, performance, and correctness of the ML-powered intent classification system.

## Test Structure

```
tests/
├── unit/                           # Unit tests for individual components
│   ├── test_api_endpoints.py       # API endpoint tests
│   ├── test_classifier_model.py    # ML model tests
│   ├── test_torchserve_client_unit.py  # TorchServe client tests
│   ├── test_cache_service.py       # Cache service tests
│   └── test_health_endpoints.py    # Health check tests
├── integration/                    # Integration tests
│   ├── test_classification_flow.py # End-to-end classification tests
│   ├── test_ml_model_integration.py # ML model integration tests
│   └── test_circuit_breaker.py    # Circuit breaker pattern tests
├── conftest.py                     # Shared fixtures and configuration
└── utils/                          # Test utilities
    ├── mocks.py                    # Mock objects
    ├── builders.py                 # Test data builders
    └── constants.py                # Test constants
```

## Test Categories

### 1. Unit Tests

#### API Endpoints (`test_api_endpoints.py`)
- **Purpose**: Test individual API endpoint functionality in isolation
- **Coverage**:
  - `/api/v1/intents/classify` - Single intent classification
  - `/api/v1/intents/classify/batch` - Batch classification
  - `/api/v1/intents/types` - Available intent types
- **Key Test Cases**:
  - Successful classification with and without cache
  - Error handling (TorchServe errors, validation errors)
  - Performance validation (<200ms response time)
  - Cache hit/miss scenarios
  - Batch processing with size limits

#### ML Model (`test_classifier_model.py`)
- **Purpose**: Test the IntentClassifier class functionality
- **Coverage**:
  - Model initialization (TorchServe and local modes)
  - Classification logic
  - Complexity determination
  - Technique mapping
  - Resource cleanup
- **Key Test Cases**:
  - TorchServe mode vs local mode
  - Intent classification accuracy
  - Complexity calculation for different text inputs
  - Proper cleanup of resources (GPU memory)

#### TorchServe Client (`test_torchserve_client_unit.py`)
- **Purpose**: Test TorchServe HTTP client functionality
- **Coverage**:
  - Connection management
  - Health checks
  - Circuit breaker implementation
  - Retry logic with exponential backoff
  - Batch operations
- **Key Test Cases**:
  - Successful inference requests
  - Connection failure handling
  - Circuit breaker triggering and recovery
  - Request retry with backoff
  - Concurrent request handling

#### Cache Service (`test_cache_service.py`)
- **Purpose**: Test Redis-based caching functionality
- **Coverage**:
  - Cache get/set operations
  - TTL management
  - Cache invalidation
  - Error handling
- **Key Test Cases**:
  - Successful cache hits and misses
  - Cache key generation consistency
  - Redis connection failures
  - Batch cache operations

#### Health Endpoints (`test_health_endpoints.py`)
- **Purpose**: Test service health monitoring
- **Coverage**:
  - Basic health check
  - Readiness check (database, model, TorchServe)
  - Liveness check
- **Key Test Cases**:
  - All components healthy
  - Individual component failures
  - Graceful degradation

### 2. Integration Tests

#### Classification Flow (`test_classification_flow.py`)
- **Purpose**: Test complete end-to-end classification workflows
- **Coverage**:
  - Full request/response cycle
  - Cache integration
  - Concurrent request handling
  - Metrics collection
- **Key Test Cases**:
  - Complete flow with cache miss
  - Complete flow with cache hit
  - Batch classification
  - Concurrent classification requests
  - Performance under load

#### ML Model Integration (`test_ml_model_integration.py`)
- **Purpose**: Test ML model with all dependencies
- **Coverage**:
  - Model initialization and inference pipeline
  - Concurrent classification handling
  - Complexity determination accuracy
  - Technique suggestion appropriateness
- **Key Test Cases**:
  - Full initialization and cleanup cycle
  - Concurrent request processing
  - Intent-specific technique mapping
  - Performance metric collection

#### Circuit Breaker (`test_circuit_breaker.py`)
- **Purpose**: Test circuit breaker pattern implementation
- **Coverage**:
  - Circuit breaker state transitions
  - Failure threshold enforcement
  - Recovery timeout
  - Half-open state behavior
- **Key Test Cases**:
  - Circuit opens after threshold failures
  - Circuit recovery after timeout
  - Gradual recovery pattern
  - Concurrent request behavior

## Test Fixtures

### Core Fixtures (from `conftest.py`)

```python
@pytest.fixture
async def mock_torchserve_client()
    # Provides mocked TorchServe client with configurable responses

@pytest.fixture
async def mock_cache_service()
    # Provides mocked Redis cache service

@pytest.fixture
def mock_settings()
    # Provides test configuration settings

@pytest.fixture
def sample_intents()
    # Provides sample classification test data

@pytest.fixture
def performance_threshold()
    # Defines performance requirements for tests
```

## Running Tests

### Run All Tests
```bash
# From the intent-classifier directory
pytest

# With coverage
pytest --cov=app --cov-report=html

# With verbose output
pytest -v
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_api_endpoints.py

# Specific test case
pytest tests/unit/test_api_endpoints.py::TestClassifyIntentEndpoint::test_classify_intent_success
```

### Test Markers
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only TorchServe tests (requires TorchServe)
pytest -m torchserve

# Skip slow tests
pytest -m "not slow"

# Run critical tests only
pytest -m critical
```

## Performance Requirements

All tests validate against these performance targets:

- **API Response Time**: p95 < 200ms
- **Model Inference**: p95 < 500ms
- **Cache Operations**: < 10ms
- **Batch Processing**: < 2s for 100 items

## Test Coverage Goals

- **Overall Coverage**: ≥ 90%
- **Critical Paths**: 100%
- **Error Handling**: 100%
- **Edge Cases**: ≥ 80%

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Intent Classifier Tests
  run: |
    cd backend/services/intent-classifier
    pytest --cov=app --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Pre-commit Hooks
```yaml
repos:
  - repo: local
    hooks:
      - id: intent-classifier-tests
        name: Intent Classifier Tests
        entry: pytest tests/unit/
        language: system
        pass_filenames: false
        files: ^backend/services/intent-classifier/
```

## Debugging Failed Tests

### Common Issues and Solutions

1. **TorchServe Connection Errors**
   - Ensure TorchServe mock is properly configured
   - Check circuit breaker state
   - Verify timeout settings

2. **Cache Test Failures**
   - Clear Redis test instance
   - Check mock Redis client configuration
   - Verify TTL settings

3. **Performance Test Failures**
   - Check system load during tests
   - Verify mock delays are reasonable
   - Consider increasing thresholds for CI environments

### Debug Commands
```bash
# Run with debug output
pytest -vvs

# Run with breakpoint debugging
pytest --pdb

# Run specific test with logging
pytest -s tests/unit/test_api_endpoints.py::test_classify_intent_success
```

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on others
2. **Mock External Dependencies**: Always mock TorchServe, Redis, and database connections
3. **Use Fixtures**: Leverage pytest fixtures for reusable test setup
4. **Assert Comprehensively**: Check all relevant aspects of responses, not just status codes
5. **Test Edge Cases**: Include tests for empty inputs, large inputs, and boundary conditions
6. **Performance Testing**: Include timing assertions for critical paths
7. **Error Scenarios**: Test all error paths and exception handling

## Future Test Additions

1. **Load Testing**: Add performance tests with locust or similar
2. **Security Testing**: Add tests for JWT validation and rate limiting
3. **Model Accuracy**: Add tests comparing model outputs against ground truth
4. **Monitoring Integration**: Test Prometheus metrics collection
5. **A/B Testing**: Add tests for model versioning and rollback