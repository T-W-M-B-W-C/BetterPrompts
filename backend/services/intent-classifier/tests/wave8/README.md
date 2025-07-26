# Wave 8: Comprehensive Testing and Validation

## Overview

Wave 8 implements a comprehensive testing suite for the BetterPrompts intent classifier, validating accuracy, performance, scalability, reliability, and user experience across multiple dimensions.

## Test Suites

### 1. Accuracy Testing (`test_comprehensive_accuracy.py`)
- **Purpose**: Validate classification accuracy across all 10 intent types
- **Coverage**: 235 test cases including edge cases and ambiguous examples
- **Metrics**: Overall accuracy, per-intent accuracy, audience/complexity detection
- **Target**: >90% overall accuracy

### 2. Performance Benchmarking (`test_performance_benchmark.py`)
- **Purpose**: Measure latency and throughput under various loads
- **Configurations**: Single-threaded, moderate load, high load, stress test
- **Metrics**: P50/P95/P99 latencies, throughput, model distribution
- **Targets**: 
  - Rules: <50ms p95
  - Zero-shot: <200ms p95
  - DistilBERT: <100ms p95
  - Hybrid: <75ms p95

### 3. Load Testing (`test_load_testing.py`)
- **Purpose**: Test system behavior under extreme concurrent load
- **Scenarios**: 
  - Gradual ramp-up (10 → 1000 users)
  - Spike test (50 → 1000 users)
  - Sustained load (1000 users for 5 min)
  - Stress test (up to 2000 users)
- **Metrics**: Success rate, latency, throughput, system resources
- **Target**: Handle 1000 concurrent users with >99% success rate

### 4. Failure Mode Testing (`test_failure_modes.py`)
- **Purpose**: Validate graceful degradation and recovery
- **Scenarios**: 
  - Redis failure
  - Database failure
  - TorchServe unavailability
  - Cascading failures
- **Metrics**: Degradation handling, recovery time, data loss
- **Target**: >90% graceful degradation, <10s recovery

### 5. A/B Model Comparison (`test_ab_comparison.py`)
- **Purpose**: Compare different routing strategies and model configurations
- **Variants**: 
  - Baseline adaptive routing
  - Performance-first (rules priority)
  - Quality-first (DistilBERT priority)
  - Aggressive routing (higher thresholds)
  - Conservative routing (lower thresholds)
- **Metrics**: Accuracy, latency, user satisfaction
- **Output**: Statistical comparison and recommendations

## Quick Start

### Prerequisites
```bash
# Ensure the intent classifier service is running
docker compose up -d intent-classifier redis postgres

# Install test dependencies
pip install matplotlib seaborn scipy numpy psutil docker
```

### Running Individual Tests

```bash
# Run accuracy tests (5-10 min)
python test_comprehensive_accuracy.py

# Run performance benchmarks (30-40 min)
python test_performance_benchmark.py

# Run load tests (20-30 min)
python test_load_testing.py

# Run A/B comparison (10-15 min)
python test_ab_comparison.py

# Run failure tests (requires confirmation)
python test_failure_modes.py
```

### Running All Tests

```bash
# Run all automated tests (skip manual confirmation tests)
python run_all_tests.py

# Include all tests (including failure mode tests)
python run_all_tests.py --include-manual
```

## Output Files

Each test suite generates specific output files:

- `accuracy_test_results.json` - Detailed accuracy metrics
- `performance_benchmark_results.json` - Performance data
- `load_test_results.json` - Load testing metrics
- `failure_mode_results.json` - Failure handling results
- `ab_comparison_results.json` - A/B test comparison data
- `wave8_test_report_[timestamp].txt` - Comprehensive report
- `wave8_test_summary.json` - Summary metrics
- Various `.png` files - Visualization plots

## Interpreting Results

### Success Criteria

The tests validate against these targets:

1. **Accuracy**
   - Overall: ≥90%
   - Audience detection: ≥92%
   - Complexity detection: ≥88%

2. **Performance**
   - Rules-based: <50ms p95
   - Zero-shot: <200ms p95
   - DistilBERT: <100ms p95
   - Hybrid average: <75ms p95

3. **Scalability**
   - 1000 concurrent users
   - >99% success rate under load
   - <200ms p95 latency at scale

4. **Reliability**
   - >90% graceful degradation
   - <10s recovery time
   - No data loss

### Reading the Report

The comprehensive report includes:

1. **Executive Summary** - High-level pass/fail status
2. **Detailed Results** - Metrics from each test suite
3. **Target Achievement** - Comparison against success criteria
4. **Recommendations** - Actionable next steps

### Common Issues

1. **Test Timeouts**: Some tests take 30+ minutes. Ensure sufficient time.
2. **Resource Constraints**: Load tests require significant resources.
3. **Service Dependencies**: Ensure all services (Redis, PostgreSQL) are running.
4. **Model Loading**: First run may be slower due to model initialization.

## Advanced Usage

### Custom Test Configuration

Edit test parameters in individual test files:

```python
# In test_load_testing.py
self.load_scenarios = [
    {
        "name": "Custom Scenario",
        "phases": [
            {"duration": 60, "concurrent_users": 500},
            {"duration": 120, "concurrent_users": 1500},
        ]
    }
]
```

### Continuous Integration

Example GitHub Actions workflow:

```yaml
- name: Run Wave 8 Tests
  run: |
    cd backend/services/intent-classifier/tests/wave8
    python run_all_tests.py
    
- name: Upload Test Results
  uses: actions/upload-artifact@v2
  with:
    name: wave8-results
    path: |
      backend/services/intent-classifier/tests/wave8/*.json
      backend/services/intent-classifier/tests/wave8/*.txt
      backend/services/intent-classifier/tests/wave8/*.png
```

## Troubleshooting

### Service Not Responding
```bash
# Check service health
curl http://localhost:8001/health/ready

# Check logs
docker compose logs intent-classifier
```

### Tests Failing
1. Verify all services are running
2. Check available system resources
3. Review service logs for errors
4. Ensure models are properly loaded

### Performance Issues
1. Warm up the service before testing
2. Check Redis connectivity
3. Monitor system resources during tests
4. Adjust concurrency levels if needed

## Next Steps

After successful Wave 8 testing:

1. **Deploy Recommended Configuration**: Implement the A/B test winner
2. **Set Up Monitoring**: Use metrics from tests to configure alerts
3. **Plan Scaling**: Use load test results for capacity planning
4. **Continuous Testing**: Integrate tests into CI/CD pipeline
5. **Production Validation**: Verify results in production environment