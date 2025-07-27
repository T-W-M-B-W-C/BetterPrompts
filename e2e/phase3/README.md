# Phase 3 E2E Tests - Login and Session Management

This directory contains comprehensive End-to-End tests for US-013: User login and session management functionality in the BetterPrompts application.

## Test Coverage

### Authentication Tests
- ✅ Login form display and validation
- ✅ Successful login with valid credentials
- ✅ Failed login with invalid password
- ✅ Failed login with non-existent user
- ✅ Unverified account handling
- ✅ Disabled account handling

### Session Management Tests
- ✅ Session persistence with "Remember Me"
- ✅ Session clearing without "Remember Me"
- ✅ Session timeout handling
- ✅ Multi-tab session synchronization
- ✅ Token refresh mechanism

### Protected Routes Tests
- ✅ Redirect to login for unauthenticated access
- ✅ Deep linking with authentication
- ✅ Return to intended page after login
- ✅ Expired token handling on protected routes

### Security Tests
- ✅ Rate limiting on login attempts
- ✅ SQL injection prevention
- ✅ XSS prevention in error messages
- ✅ No sensitive information exposure in errors
- ✅ Token tampering detection

### Logout Tests
- ✅ Complete session cleanup on logout
- ✅ Multi-tab logout synchronization

### Performance Tests
- ✅ Login completion within performance budget
- ✅ Browser password manager integration

## Setup

1. Install dependencies:
```bash
npm install
```

2. Ensure the BetterPrompts application is running with test configuration:
```bash
cd ../..
# Use test configuration with optimized rate limiting
docker compose -f docker-compose.yml -f e2e/phase3/docker-compose.test.yml up -d
```

**Note**: The test configuration automatically applies optimized rate limiting settings (1000 requests/minute vs 100 for production) to prevent test failures due to rate limiting during rapid test execution.

## Running Tests

### Run all tests:
```bash
npm test
```

### Run tests in headed mode (see browser):
```bash
npm run test:headed
```

### Debug tests:
```bash
npm run test:debug
```

### Run tests with UI mode:
```bash
npm run test:ui
```

### View test report:
```bash
npm run test:report
```

## Test Architecture

### Page Objects
- **LoginPage**: Enhanced login page object with comprehensive interaction methods
- **BasePage**: Inherited from frontend test infrastructure

### Utilities
- **AuthHelpers**: JWT token management and validation utilities
- **Test Helpers**: Shared testing utilities from frontend tests

### Key Features
1. **Smart Waiting**: No fixed timeouts, uses Playwright's intelligent waiting
2. **API Response Synchronization**: Tests wait for actual API responses
3. **Token Management**: Comprehensive JWT token handling and validation
4. **Security Testing**: SQL injection, XSS, and token tampering tests
5. **Performance Monitoring**: Login flow performance metrics

## Test Patterns

### Authentication Flow
```typescript
const result = await loginPage.login({
  email: 'user@example.com',
  password: 'password123',
  rememberMe: true
});

expect(result.status).toBe(200);
await loginPage.waitForLoginSuccess();
```

### Token Verification
```typescript
const tokens = await authHelpers.getStoredTokens();
expect(tokens).toBeTruthy();
expect(authHelpers.isTokenExpired(tokens.accessToken)).toBe(false);
```

### Protected Route Testing
```typescript
await verifyProtectedRoute(page, '/dashboard', '/login');
```

### Session Management
```typescript
// Test multi-tab sync
const synced = await authHelpers.verifyMultiTabSync(otherPage);
expect(synced).toBe(true);
```

## Backend Integration

Tests use **real backend integration** (no mocking) for authentic testing:

```typescript
// Real API call to backend service
const result = await loginPage.login({
  email: 'test@example.com',
  password: 'Test123!@#'
});

// Verify actual API response
expect(result.status).toBe(200);
expect(result.data.access_token).toBeTruthy();
```

### Test Environment Configuration

The test environment includes:
- **Rate Limiting**: Optimized limits (1000 req/min vs 100 for production)
- **Environment Detection**: Automatic `e2e` environment detection
- **Test Database**: Uses real PostgreSQL with test user data
- **Redis Cache**: Fast cache eviction for tests (256mb vs 512mb)

### Rate Limiting Fix

The implementation automatically detects test/e2e environments and applies:
- Higher rate limits (1000 vs 100 requests/minute)
- Test-specific cache keys (`test_user:` vs `user:`)
- Disabled rate limiting for login endpoints during tests

## Security Considerations

1. **Rate Limiting**: Tests verify rate limiting after 5 failed attempts
2. **Token Security**: Tests verify proper token handling and tampering detection
3. **Input Validation**: SQL injection and XSS prevention tests
4. **Error Messages**: Verify no sensitive information leakage

## Performance Targets

- Form fill: < 500ms
- API response: < 1000ms
- Total login flow: < 3000ms

## CI/CD Integration

Tests are configured to run in CI with:
- Retry logic for flaky tests
- Video and screenshot capture on failure
- JUnit and JSON reporting
- Parallel execution across browsers

## Troubleshooting

### Common Issues

1. **JWT Import Error**: Ensure `npm install` has been run
2. **Connection Refused**: Check if application is running on localhost:3000
3. **Token Validation Failures**: Verify mock token secret matches application

### Debug Mode

Use debug mode to step through tests:
```bash
npm run test:debug
```

### View Failed Test Artifacts

After test failure, check:
- `test-results/` - Screenshots and videos
- `playwright-report/` - HTML report with traces