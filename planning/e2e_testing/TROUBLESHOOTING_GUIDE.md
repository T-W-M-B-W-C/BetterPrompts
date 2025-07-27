# E2E Testing Troubleshooting Guide

## Common Issues and Solutions

### Setup Issues

#### Docker Services Not Starting
**Problem**: Services fail to start or containers exit immediately

**Solutions**:
```bash
# Check Docker daemon is running
docker info

# Check service logs
docker compose logs api-gateway
docker compose logs frontend

# Rebuild containers
docker compose down
docker compose build --no-cache
docker compose up -d

# Check port conflicts
lsof -i :3000  # Frontend
lsof -i :8080  # API Gateway
```

#### Database Connection Errors
**Problem**: Tests fail with "connection refused" or "database does not exist"

**Solutions**:
```bash
# Check database is running
docker compose ps postgres

# Check database logs
docker compose logs postgres

# Manually create test database
docker compose exec postgres psql -U betterprompts -c "CREATE DATABASE betterprompts_test;"

# Run migrations
docker compose exec api-gateway ./migrate up
```

### Test Execution Issues

#### Element Not Found Errors
**Problem**: Playwright can't find elements on page

**Solutions**:
```javascript
// Add data-testid attributes to elements
<button data-testid="submit-button">Submit</button>

// Use more specific selectors
await page.locator('[data-testid="submit-button"]').click();

// Add explicit waits
await page.waitForSelector('[data-testid="submit-button"]', { timeout: 5000 });

// Debug with screenshots
await page.screenshot({ path: 'debug.png' });
```

#### Timeout Errors
**Problem**: Tests timeout waiting for elements or actions

**Solutions**:
```javascript
// Increase test timeout
test('my test', async ({ page }) => {
  test.setTimeout(30000); // 30 seconds
  // test code
});

// Increase action timeout
await page.click('button', { timeout: 10000 });

// Wait for network idle
await page.waitForLoadState('networkidle');

// Wait for specific conditions
await page.waitForFunction(() => document.readyState === 'complete');
```

#### Flaky Tests
**Problem**: Tests pass sometimes but fail randomly

**Solutions**:
```javascript
// Add retry logic
test.describe('flaky feature', () => {
  test.describe.configure({ retries: 2 });
  
  test('unstable test', async ({ page }) => {
    // test code
  });
});

// Use proper wait strategies
// Bad: Hard-coded wait
await page.waitForTimeout(2000);

// Good: Wait for specific condition
await page.waitForSelector('.success-message');

// Add stability checks
await expect(page.locator('.loading')).not.toBeVisible();
```

### Authentication Issues

#### Login Fails in Tests
**Problem**: Can't login with test credentials

**Solutions**:
```javascript
// Create test user in beforeEach
beforeEach(async () => {
  await createTestUser({
    email: 'test@example.com',
    password: 'TestPass123!',
    verified: true
  });
});

// Clear cookies between tests
await context.clearCookies();

// Check JWT token handling
const token = await page.evaluate(() => localStorage.getItem('token'));
console.log('Token:', token);
```

#### Session Not Persisting
**Problem**: User gets logged out between actions

**Solutions**:
```javascript
// Save and restore auth state
const authFile = 'playwright/.auth/user.json';

// After login
await page.context().storageState({ path: authFile });

// In other tests
const context = await browser.newContext({
  storageState: authFile
});
```

### API Integration Issues

#### CORS Errors
**Problem**: API requests blocked by CORS policy

**Solutions**:
```nginx
# Update nginx.conf
location /api {
    add_header 'Access-Control-Allow-Origin' '*';
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
    add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type';
}

# Or update API Gateway CORS middleware
cors.AllowOrigins = []string{"http://localhost:3000"}
```

#### API Rate Limiting in Tests
**Problem**: Tests hit rate limits

**Solutions**:
```javascript
// Add delays between requests
await page.waitForTimeout(100);

// Use different API keys for parallel tests
const apiKey = `test-key-${Date.now()}`;

// Disable rate limiting for test environment
if (process.env.NODE_ENV === 'test') {
  rateLimiter.disable();
}
```

### Performance Issues

#### Tests Running Slowly
**Problem**: Test suite takes too long to execute

**Solutions**:
```javascript
// Run tests in parallel
export default {
  workers: 4,
  fullyParallel: true,
};

// Reuse browser context
let context;
test.beforeAll(async ({ browser }) => {
  context = await browser.newContext();
});

// Use API calls for setup
await api.createUser(testUser); // Faster than UI
```

#### Memory Leaks
**Problem**: Tests consume increasing memory

**Solutions**:
```javascript
// Close pages properly
afterEach(async ({ page }) => {
  await page.close();
});

// Clear large variables
let largeData = null;

// Monitor memory usage
console.log('Memory:', process.memoryUsage());
```

### Environment-Specific Issues

#### Different Behavior in CI
**Problem**: Tests pass locally but fail in CI

**Solutions**:
```yaml
# Use same container images
services:
  frontend:
    image: betterprompts/frontend:${VERSION}

# Set consistent timezone
environment:
  - TZ=UTC

# Disable animations
test.use({
  // Disable animations
  launchOptions: {
    args: ['--disable-animations']
  }
});
```

#### Screenshot/Video Issues
**Problem**: Can't see what's happening in CI

**Solutions**:
```javascript
// playwright.config.js
export default {
  use: {
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },
};

// In GitHub Actions
- uses: actions/upload-artifact@v3
  if: failure()
  with:
    name: test-artifacts
    path: test-results/
```

## Quick Fixes

### Reset Everything
```bash
# Nuclear option - reset all
docker compose down -v
docker system prune -af
rm -rf node_modules
npm install
docker compose up -d
```

### Check Service Health
```bash
# Quick health check
curl http://localhost/api/v1/health
curl http://localhost:3000

# Check all services
docker compose ps
docker compose logs --tail=50
```

### Debug Mode
```javascript
// Run single test in debug mode
npx playwright test path/to/test.spec.ts --debug

// Run with headed browser
npx playwright test --headed

// Slow down execution
test.use({ slowMo: 500 });
```

## Prevention Strategies

### Best Practices
1. **Use data-testid**: Consistent element selection
2. **Avoid hard waits**: Use explicit conditions
3. **Clean test data**: Reset state between tests
4. **Mock external services**: Reduce flakiness
5. **Parallel-safe tests**: No shared state

### Monitoring
```javascript
// Add test metrics
const startTime = Date.now();
// ... test code ...
console.log(`Test duration: ${Date.now() - startTime}ms`);

// Track flaky tests
if (testInfo.retry > 0) {
  console.warn(`Test retried ${testInfo.retry} times`);
}
```

### Regular Maintenance
- Update dependencies monthly
- Review and remove obsolete tests
- Refactor complex test code
- Update selectors when UI changes
- Monitor test execution trends

---

*Keep this guide updated with new issues and solutions discovered during implementation*