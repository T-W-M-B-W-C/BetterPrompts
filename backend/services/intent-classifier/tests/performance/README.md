# Intent Classifier Performance Tests

This directory contains performance testing scripts for analyzing the cache impact and load testing the intent classifier service.

## Prerequisites

```bash
pip install httpx click rich
```

## Available Tests

### 1. Cache Performance Test (`test_cache_performance.py`)

This script measures the performance impact of Redis caching on the intent classifier.

#### Features:
- **Cold Cache Test**: Measures response times with no cached data
- **Warm Cache Test**: Measures response times with pre-cached data
- **Mixed Cache Test**: Tests with 50% cached and 50% new requests
- **Concurrent Request Test**: Tests parallel request handling
- **Detailed Metrics**: Response times (avg, p95, p99), cache hit rates, speedup factors

#### Usage:
```bash
# Basic test (requires intent classifier running on localhost:8001)
python test_cache_performance.py

# Test against different URL
python test_cache_performance.py --base-url http://your-service:8001

# Run extended tests
python test_cache_performance.py --full-test
```

#### Example Output:
```
🚀 Speedup Factor: 5.2x
📈 Performance Improvement: 80.7%
❄️  Cold Cache Avg: 125.3ms
🔥 Warm Cache Avg: 24.2ms
```

### 2. Load Test (`load_test.py`)

Continuous load testing script with real-time statistics display.

#### Features:
- **Configurable Load**: Set target requests per second (RPS)
- **Real-time Monitoring**: Live statistics update
- **Cache Hit Tracking**: Monitors cache effectiveness under load
- **Response Time Metrics**: Tracks p95 and p99 latencies
- **Connection Pooling**: Efficient HTTP client usage

#### Usage:
```bash
# Default: 10 RPS for 60 seconds
python load_test.py

# Custom load: 50 RPS for 5 minutes
python load_test.py --rps 50 --duration 300

# Test against different URL
python load_test.py --base-url http://your-service:8001 --rps 20
```

## Running Tests with Docker

If the intent classifier is running in Docker:

```bash
# Ensure services are running
docker compose up -d

# Run cache performance test
docker compose exec intent-classifier python tests/performance/test_cache_performance.py

# Run load test
docker compose exec intent-classifier python tests/performance/load_test.py --rps 20
```

## Interpreting Results

### Cache Performance Metrics:
- **Speedup Factor**: How many times faster cached responses are (e.g., 5x means 5 times faster)
- **Performance Improvement %**: Percentage reduction in response time
- **P95/P99 Response Times**: 95th and 99th percentile response times (important for SLA)

### Load Test Metrics:
- **Requests/sec**: Actual throughput achieved
- **Success Rate**: Percentage of successful requests
- **Cache Hit Rate**: Percentage of requests served from cache
- **Response Times**: Average and percentile latencies

## Best Practices

1. **Warm Up**: Run a short test first to warm up the service
2. **Baseline**: Always test without cache first to establish baseline
3. **Realistic Load**: Use RPS values that match expected production load
4. **Multiple Runs**: Run tests multiple times and average results
5. **Monitor Resources**: Watch CPU/memory usage during tests

## Troubleshooting

### Service Not Responding
```bash
# Check if service is running
curl http://localhost:8001/health

# Check Docker logs
docker compose logs intent-classifier
```

### High Error Rate
- Reduce RPS to avoid overwhelming the service
- Check service logs for specific errors
- Ensure Redis is running and accessible

### Inconsistent Results
- Clear Redis cache between test runs
- Ensure no other load on the system
- Run tests multiple times and use average values