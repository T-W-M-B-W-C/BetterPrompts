# E2E Tests - Phase 1: US-001 Anonymous Enhancement Flow

## Overview
This directory contains the E2E tests for User Story US-001: Anonymous prompt enhancement flow. These tests verify the simplest user journey where anonymous users can enter a prompt and receive an enhanced version.

## Test Structure

### Files
- `us-001-anonymous-enhancement.spec.ts` - Main test suite
- `test-data-anonymous.ts` - Test data including 10 sample prompts
- `performance-baseline-metrics.md` - Performance tracking documentation

### Page Objects
- `HomePage` - Landing page interactions (existing)
- `EnhanceSection` - Enhancement section for anonymous users (new)

## Test Coverage

### 1. Homepage Navigation
- ✅ Homepage loads with prompt input visible
- ✅ Mobile viewport compatibility
- ✅ Desktop viewport compatibility

### 2. Prompt Input Validation
- ✅ Empty prompt handling
- ✅ Valid prompt acceptance
- ✅ 2000 character limit enforcement
- ✅ Real-time character counting

### 3. Enhancement API Integration
- ✅ Successful enhancement of simple prompts
- ✅ Multiple enhancement requests handling

### 4. Loading States & Error Handling
- ✅ Loading spinner during enhancement
- ✅ Network error handling
- ✅ Retry functionality after errors

### 5. Response Display
- ✅ Enhanced prompt display
- ✅ Technique explanation visibility
- ✅ Copy functionality
- ✅ Sign-up CTA display

### 6. Performance Requirements
- ✅ < 2 second response time for all enhancements
- ✅ Performance consistency across prompt complexity
- ✅ Page load performance metrics

## Running the Tests

### Prerequisites
```bash
cd e2e/frontend
npm install
```

### Run All US-001 Tests
```bash
npx playwright test phase1/us-001-anonymous-enhancement.spec.ts
```

### Run Specific Test Groups
```bash
# Homepage navigation tests only
npx playwright test phase1/us-001-anonymous-enhancement.spec.ts --grep "Homepage Navigation"

# Performance tests only
npx playwright test phase1/us-001-anonymous-enhancement.spec.ts --grep "Performance Requirements"

# Run with UI mode for debugging
npx playwright test phase1/us-001-anonymous-enhancement.spec.ts --ui
```

### Run on Specific Browsers
```bash
# Chrome only
npx playwright test phase1/us-001-anonymous-enhancement.spec.ts --project=chromium

# All browsers
npx playwright test phase1/us-001-anonymous-enhancement.spec.ts --project=chromium --project=firefox --project=webkit
```

### Generate Test Report
```bash
# Run tests with HTML reporter
npx playwright test phase1/us-001-anonymous-enhancement.spec.ts --reporter=html

# Open report
npx playwright show-report
```

## Test Data

The test suite uses 10 predefined prompts covering:
- 5 valid prompts (various use cases)
- 3 edge cases (short, special chars, multi-language)
- 2 boundary cases (near limit, empty)

Access test data:
```typescript
import { anonymousTestPrompts, getPromptsByCategory } from './test-data-anonymous';
```

## Performance Monitoring

Performance baselines are tracked in `performance-baseline-metrics.md`. Update after:
- Initial test runs to establish baselines
- Major feature releases
- Infrastructure changes

## Debugging Tips

1. **Screenshots on Failure**
   - Playwright automatically captures screenshots on test failure
   - Find them in `test-results/` directory

2. **Video Recording**
   - Enable in playwright.config.ts:
   ```typescript
   use: {
     video: 'on-first-retry'
   }
   ```

3. **Slow Motion Mode**
   ```bash
   npx playwright test --headed --slow-mo=1000
   ```

4. **Debug Mode**
   ```bash
   npx playwright test --debug
   ```

## CI/CD Integration

For GitHub Actions:
```yaml
- name: Run US-001 Tests
  run: |
    cd e2e/frontend
    npx playwright test phase1/us-001-anonymous-enhancement.spec.ts
```

## Next Steps

After US-001 is complete and passing:
1. Run performance baseline collection
2. Set up monitoring for production
3. Implement US-002: Authenticated user flows
4. Add visual regression tests