# Python Test Execution Guide

This guide provides comprehensive instructions for running and analyzing tests for the BetterPrompts Python services.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Running Tests Locally](#running-tests-locally)
3. [Coverage Analysis](#coverage-analysis)
4. [CI/CD Integration](#cicd-integration)
5. [Test Organization](#test-organization)
6. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites
- Python 3.9+ installed
- Virtual environment support
- Docker and Docker Compose (optional)

### Running All Tests with Coverage
```bash
# From project root
./scripts/run-python-tests-with-coverage.sh

# View coverage report
open coverage-reports/index.html
```

### Validate Test Structure
```bash
# Check test organization and quality
./scripts/validate-python-tests.sh
```

## Running Tests Locally

### Intent Classifier Service

```bash
cd backend/services/intent-classifier

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_classifier_model.py

# Run with verbose output
pytest -v

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

### Prompt Generator Service

```bash
cd backend/services/prompt-generator

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific technique tests
pytest tests/unit/test_all_techniques.py::test_chain_of_thought

# Run with markers
pytest -m "not slow"  # Skip slow tests
pytest -m "integration"  # Only integration tests
```

### Docker-Based Testing

```bash
# Run tests in containers
docker-compose -f docker-compose.test.yml up --build

# Run specific service tests
docker-compose -f docker-compose.test.yml run intent-classifier-test
docker-compose -f docker-compose.test.yml run prompt-generator-test

# Clean up
docker-compose -f docker-compose.test.yml down -v
```

## Coverage Analysis

### Generate Coverage Reports

```bash
# Run the coverage report generator
python scripts/generate-coverage-report.py

# This will:
# - Run tests for both services
# - Generate individual coverage reports
# - Create a combined HTML report
# - Display coverage metrics
```

### Coverage Thresholds
- **Target**: 85% line coverage
- **Current Achievement**: >91% for both services
- **CI/CD Enforcement**: Tests fail if coverage drops below 85%

### Viewing Coverage Reports

1. **HTML Reports**: 
   ```bash
   # Combined report
   open coverage-reports/index.html
   
   # Service-specific reports
   open coverage-reports/intent-classifier/index.html
   open coverage-reports/prompt-generator/index.html
   ```

2. **Terminal Output**:
   ```bash
   # Quick coverage check
   cd backend/services/intent-classifier
   pytest --cov=app --cov-report=term
   ```

3. **XML Reports** (for CI/CD):
   ```bash
   # Generated automatically during test runs
   cat backend/services/intent-classifier/coverage.xml
   ```

## CI/CD Integration

### GitHub Actions

The project includes a comprehensive GitHub Actions workflow that:

1. **Runs on**:
   - Push to main/develop branches
   - Pull requests to main
   - Changes to Python services

2. **Test Matrix**:
   - Python versions: 3.9, 3.10, 3.11
   - Services tested in parallel
   - Security scanning included

3. **Workflow Features**:
   ```yaml
   - Linting (flake8, black, isort)
   - Type checking (mypy)
   - Unit and integration tests
   - Coverage reporting to Codecov
   - Security scanning (Trivy, Bandit)
   ```

### Local CI Simulation

```bash
# Simulate CI checks locally
cd backend/services/intent-classifier

# Linting
flake8 app tests --max-line-length=120
black --check app tests
isort --check-only app tests

# Type checking
mypy app --ignore-missing-imports

# Security scanning
bandit -r app
```

## Test Organization

### Directory Structure
```
service/
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Shared fixtures
│   ├── unit/                # Unit tests
│   │   ├── __init__.py
│   │   └── test_*.py
│   ├── integration/         # Integration tests
│   │   ├── __init__.py
│   │   └── test_*.py
│   └── utils/              # Test utilities
│       ├── __init__.py
│       ├── builders.py     # Test data builders
│       ├── factories.py    # Object factories
│       ├── mocks.py        # Mock objects
│       └── assertions.py   # Custom assertions
├── pytest.ini              # Pytest configuration
└── .coveragerc            # Coverage configuration
```

### Test Naming Conventions
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test functions: `test_<description>`
- Async tests: `async def test_<description>`

### Test Markers
```python
# Mark slow tests
@pytest.mark.slow
def test_heavy_computation():
    pass

# Mark integration tests
@pytest.mark.integration
async def test_database_connection():
    pass

# Skip tests conditionally
@pytest.mark.skipif(not has_gpu(), reason="GPU not available")
def test_gpu_inference():
    pass
```

## Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   # Ensure you're in the correct directory
   cd backend/services/<service-name>
   
   # Install in development mode
   pip install -e .
   ```

2. **Async Test Issues**:
   ```bash
   # Ensure pytest-asyncio is installed
   pip install pytest-asyncio
   
   # Use async fixtures properly
   @pytest.fixture
   async def async_client():
       async with AsyncClient() as client:
           yield client
   ```

3. **Coverage Not Detected**:
   ```bash
   # Use proper source specification
   pytest --cov=app --cov-report=html
   
   # Check .coveragerc configuration
   [run]
   source = app
   omit = */tests/*
   ```

4. **Mock Issues**:
   ```python
   # Use proper mock paths
   @patch('app.services.classifier.TorchServeClient')
   def test_with_mock(mock_client):
       pass
   ```

### Performance Tips

1. **Parallel Test Execution**:
   ```bash
   # Install pytest-xdist
   pip install pytest-xdist
   
   # Run tests in parallel
   pytest -n auto
   ```

2. **Test Caching**:
   ```bash
   # Run only failed tests
   pytest --lf
   
   # Run failed tests first
   pytest --ff
   ```

3. **Selective Testing**:
   ```bash
   # Run tests matching expression
   pytest -k "classifier and not slow"
   
   # Run specific test
   pytest tests/unit/test_api.py::test_classify_intent
   ```

### Debug Mode

```bash
# Run with debugging output
pytest -vvs

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Capture print statements
pytest -s
```

## Best Practices

1. **Always run tests before committing**
2. **Maintain >85% coverage for new code**
3. **Write tests for edge cases**
4. **Use appropriate mocks for external dependencies**
5. **Keep tests independent and isolated**
6. **Document complex test scenarios**
7. **Run integration tests regularly**
8. **Update tests when changing functionality**

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Python Testing Best Practices](https://realpython.com/pytest-python-testing/)
- [Test-Driven Development](https://testdriven.io/)