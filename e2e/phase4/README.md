# Phase 4: Authenticated Enhancement with History Tests

## Overview

This test suite validates the complete flow of authenticated users enhancing prompts with automatic history persistence. It combines US-002 (authenticated enhancement) and US-007 (enhancement history) into comprehensive E2E tests.

## Prerequisites

1. **Environment Setup**
   ```bash
   # Copy environment configuration
   cp .env.example .env
   # Edit .env with your specific values
   
   # Install dependencies
   npm install
   ```

2. **Database Setup**
   - Ensure PostgreSQL is running with test database
   - Test users must exist in the database:
     - `test@example.com` (regular user with history)
     - `power@example.com` (power user with extensive history)
     - `new@example.com` (new user with no history)

3. **Services Running**
   ```bash
   # From project root
   docker compose up -d
   ```

## Test Structure

```
phase4/
├── pages/                     # Page Object Models
│   ├── BasePage.ts           # Common page functionality
│   ├── EnhancementPage.ts    # Enhancement UI interactions
│   ├── HistoryPage.ts        # History listing and filters
│   └── EnhancementDetailsPage.ts  # Individual enhancement details
├── utils/                     # Test utilities
│   ├── AuthHelper.ts         # Authentication helpers (no mocks)
│   ├── HistoryDataGenerator.ts    # Test data generation
│   └── SearchTestUtils.ts    # Search and filter helpers
├── fixtures/                  # Test data
│   ├── user-with-history.json     # Sample user data
│   └── enhancement-samples.json   # Enhancement examples
├── us-002-007-auth-enhancement-history.spec.ts  # Main test suite
├── history-performance.spec.ts    # Performance tests
├── test-plan.md              # Detailed test plan
└── playwright.config.ts      # Test configuration
```

## Running Tests

### All Tests
```bash
npm test
```

### Specific Test File
```bash
npm test us-002-007-auth-enhancement-history.spec.ts
npm test history-performance.spec.ts
```

### Debug Mode
```bash
npm run test:debug
```

### Headed Mode (see browser)
```bash
npm run test:headed
```

### UI Mode (interactive)
```bash
npm run test:ui
```

## Test Scenarios

### 1. Authenticated Enhancement Flow
- Login and enhance prompts
- Verify automatic history saving
- Test with special characters and edge cases
- Validate user context persistence

### 2. History Display
- Empty state for new users
- Paginated display for users with history
- Metadata display (intent, techniques, confidence)
- Sorting by date (newest first)

### 3. Search and Filter
- Search by prompt content
- Filter by intent
- Filter by technique
- Combined filters
- No results handling

### 4. Enhancement Details
- View individual enhancement details
- Copy original/enhanced prompts
- Re-run with consistency check
- Delete enhancements

### 5. Performance Tests
- Page load times < 2s
- Search response < 500ms
- Pagination < 200ms
- Concurrent operations
- Memory leak prevention

## Performance SLAs

| Operation | Target | Critical |
|-----------|--------|----------|
| History Load | < 2s | < 3s |
| Search Response | < 500ms | < 1s |
| Page Switch | < 200ms | < 500ms |
| Details Load | < 1s | < 2s |
| Enhancement Save | < 1s | < 2s |

## Troubleshooting

### Authentication Issues
- Verify test users exist in database
- Check JWT secret matches backend
- Clear browser storage between tests

### Performance Test Failures
- Ensure services are warmed up
- Check database indexes are created
- Verify Redis cache is working

### Flaky Tests
- Increase timeouts in playwright.config.ts
- Add explicit waits for dynamic content
- Check for race conditions

## CI/CD Integration

```yaml
# Example GitHub Actions configuration
- name: Run Phase 4 Tests
  run: |
    docker compose up -d
    npm install
    npm test
  env:
    E2E_BASE_URL: http://localhost:3000
    API_URL: http://localhost/api/v1
```

## Reporting

Test results are generated in multiple formats:
- HTML Report: `test-results/html/index.html`
- JUnit XML: `test-results/junit.xml`
- JSON: `test-results/results.json`

View HTML report:
```bash
npm run test:report
```

## Best Practices

1. **No Mocks**: All tests use real backend services
2. **Data Isolation**: Each test cleans up after itself
3. **Deterministic**: Tests produce consistent results
4. **Performance**: Track and alert on degradation
5. **Documentation**: Keep test plan updated

---

*Phase 4 Test Suite v1.0*  
*Last Updated: 2025-01-27*