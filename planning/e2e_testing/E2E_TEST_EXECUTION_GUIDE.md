# E2E Test Execution Guide

## Overview

This guide provides detailed instructions for executing and validating the E2E tests implemented across all 8 waves of the BetterPrompts testing strategy. Each wave includes specific execution commands, validation criteria, and success metrics.

## Pre-requisites

### Environment Setup
```bash
# Clone repository
git clone https://github.com/your-org/betterprompts.git
cd betterprompts

# Install global dependencies
npm install -g playwright k6
docker pull owasp/zap2docker-stable

# Setup environment variables
cp .env.example .env.test
# Edit .env.test with test credentials
```

### Test Accounts
Create dedicated test accounts for each persona:
- `sarah.test@example.com` - Basic user
- `alex.test@example.com` - Developer with API access
- `chen.test@example.com` - Data scientist
- `maria.test@example.com` - Content creator
- `techcorp.test@example.com` - Enterprise admin

## Wave-by-Wave Execution Guide

### Wave 1: Test Architecture (✅ COMPLETED)
No execution needed - documentation phase completed.

### Wave 2: Frontend UI Tests (✅ COMPLETED)

**Execution Time**: ~30 minutes for full suite

```bash
cd e2e/frontend

# First-time setup
npm install
npx playwright install --with-deps

# Run all tests
npm test

# Run by category
npm run test:smoke      # Quick validation (5 min)
npm run test:critical   # Critical paths (10 min)
npm run test:regression # Full suite (30 min)

# Run by persona
npm run test:sarah      # Marketing manager tests
npm run test:alex       # Developer tests

# Generate reports
npm run test -- --reporter=html
npx playwright show-report
```

**Success Metrics**:
- All tests pass (100% success rate)
- Execution time <30 minutes
- No flaky tests (retry rate <5%)
- Visual regression baselines established

### Wave 3: API Integration Tests (⏳ PENDING)

**Execution Time**: ~20 minutes

```bash
cd e2e/api

# Setup
npm install

# Run by service
npm run test:gateway
npm run test:classifier
npm run test:selector
npm run test:generator

# Run integration tests
npm run test:integration

# Run contract tests
npm run test:pact

# Performance baseline
npm run test:perf:baseline
```

**Success Metrics**:
- 100% endpoint coverage
- All contracts valid
- p95 latency <200ms
- No breaking changes

### Wave 4: Cross-Service Workflows (⏳ PENDING)

**Execution Time**: ~25 minutes

```bash
cd e2e/workflows

# Start all services
docker-compose up -d

# Run workflow tests
npm run test:workflows:all

# Run specific personas
npm run test:workflow:sarah
npm run test:workflow:alex

# Validate tracing
npm run test:tracing
```

**Success Metrics**:
- All workflows complete E2E
- Trace continuity 100%
- Error recovery validated
- Data consistency maintained

### Wave 5: Performance Testing (⏳ PENDING)

**Execution Time**: 2-24 hours depending on tests

```bash
cd e2e/performance

# Quick performance check (30 min)
k6 run load-tests/baseline.js

# Full performance suite (2 hours)
npm run test:perf:full

# Sustained load test (24 hours)
k6 run --duration=24h load-tests/sustained.js

# Generate report
k6 report < results.json > perf-report.html
```

**Success Metrics**:
- 10,000 RPS sustained
- p95 latency <200ms
- <1% error rate
- Auto-scaling works

### Wave 6: Security Testing (⏳ PENDING)

**Execution Time**: ~45 minutes

```bash
cd e2e/security

# OWASP ZAP scan
docker run -t owasp/zap2docker-stable \
  zap-baseline.py -t https://app.betterprompts.com

# Run security test suite
npm run test:security:all

# Edge case testing
npm run test:edge:all

# Generate report
npm run report:security
```

**Success Metrics**:
- Zero critical vulnerabilities
- OWASP Top 10 covered
- Rate limiting effective
- All edge cases handled

### Wave 7: Monitoring Validation (⏳ PENDING)

**Execution Time**: 24+ hours for full validation

```bash
cd e2e/monitoring

# Deploy synthetics
npm run deploy:synthetics

# Test alerts (1 hour)
npm run test:alerts:all

# 24-hour validation
npm run test:monitoring:24h
```

**Success Metrics**:
- All alerts trigger correctly
- <5 minute detection time
- Zero false positives
- Dashboards accurate

### Wave 8: Production Testing (⏳ PENDING)

**Execution Time**: Continuous

```bash
cd e2e/production

# Deploy continuous testing
gh workflow enable continuous-testing.yml

# Initial validation
npm run test:smoke:prod

# Monitor success rate
npm run monitor:production
```

**Success Metrics**:
- 99.9% smoke test success
- Zero production impact
- Continuous monitoring active

## Consolidated Test Execution

### Daily Test Suite
Run these tests daily in CI/CD:

```bash
# Morning test suite (~1 hour)
./scripts/daily-tests.sh

# Includes:
# - Smoke tests (5 min)
# - Critical paths (15 min)
# - API tests (20 min)
# - Basic performance (20 min)
```

### Weekly Test Suite
Run comprehensive tests weekly:

```bash
# Weekend test suite (~4 hours)
./scripts/weekly-tests.sh

# Includes:
# - Full regression (1 hour)
# - Security scan (45 min)
# - Performance tests (2 hours)
# - Visual regression (15 min)
```

### Release Test Suite
Run before each release:

```bash
# Pre-release validation (~6 hours)
./scripts/release-tests.sh

# Includes:
# - All test suites
# - Load testing
# - Security validation
# - Production smoke tests
```

## Test Reporting

### Automated Reports
Reports are generated automatically:
- HTML reports in `test-results/`
- JSON metrics in `test-metrics/`
- Screenshots in `test-screenshots/`

### Dashboards
Monitor test health at:
- **Local**: http://localhost:3001/e2e-dashboard
- **CI/CD**: GitHub Actions summary
- **Production**: Datadog E2E Dashboard

### Metrics Tracking
Key metrics tracked:
- Test execution time
- Pass/fail rates
- Flaky test detection
- Coverage trends
- Performance baselines

## Troubleshooting

### Common Issues

**Playwright Tests Failing**
```bash
# Update browsers
npx playwright install --force

# Clear test cache
rm -rf test-results/

# Run in debug mode
PWDEBUG=1 npm test
```

**API Tests Timeout**
```bash
# Check service health
docker-compose ps
docker-compose logs api-gateway

# Increase timeout
JEST_TIMEOUT=30000 npm test
```

**Performance Tests OOM**
```bash
# Increase K6 memory
k6 run --max-vus=1000 --batch=10 load-test.js

# Use cloud execution
k6 cloud load-test.js
```

## Best Practices

1. **Run Tests in Isolation**
   - Use fresh test data
   - Clean up after tests
   - Don't depend on test order

2. **Monitor Test Health**
   - Track flaky tests
   - Review execution times
   - Update baselines regularly

3. **Maintain Test Data**
   - Use factories for test data
   - Keep fixtures up to date
   - Version control test accounts

4. **Review Test Results**
   - Check reports after each run
   - Investigate failures immediately
   - Update tests with code changes

## Continuous Improvement

### Monthly Review
- Analyze test metrics
- Update performance baselines
- Review and remove obsolete tests
- Add tests for new features

### Quarterly Planning
- Evaluate tool effectiveness
- Plan test infrastructure upgrades
- Review test strategy alignment
- Update documentation

---

**Last Updated**: January 26, 2025
**Next Review**: February 2025