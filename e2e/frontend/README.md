# BetterPrompts E2E Testing Framework

This directory contains the Playwright-based end-to-end testing framework for BetterPrompts, implementing the Wave 2 specifications from the E2E Testing Implementation Plan.

## 🏗️ Architecture Overview

```
e2e/frontend/
├── fixtures/           # Test data (users, prompts)
├── pages/             # Page Object Models
│   ├── auth/          # Authentication pages
│   ├── base.page.ts   # Base page with common functionality
│   └── *.page.ts      # Individual page objects
├── tests/             # Test suites
│   ├── personas/      # Tests organized by user persona
│   └── cross-cutting/ # Cross-persona tests
├── utils/             # Helper functions and utilities
├── playwright.config.ts # Playwright configuration
└── package.json       # Dependencies and scripts
```

## 🚀 Quick Start

### Installation
```bash
cd e2e/frontend
npm install
npx playwright install --with-deps
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests for specific persona
npm run test:sarah
npm run test:alex
npm run test:chen
npm run test:maria
npm run test:techcorp

# Run tests in headed mode (see browser)
npm run test:headed

# Run tests in UI mode (interactive)
npm run test:ui

# Run specific test categories
npm run test:smoke      # Quick smoke tests
npm run test:critical   # Critical path tests
npm run test:regression # Full regression suite
```

### Browser Testing
```bash
# Test specific browsers
npm run test:chrome
npm run test:firefox
npm run test:webkit

# Test mobile viewports
npm run test:mobile
```

## 👥 Test Personas

### 1. Sarah - Marketing Manager (Basic User)
- **Focus**: Simple prompt enhancement, user-friendly features
- **Test Files**: `sarah-marketing.spec.ts`
- **User Stories**: US-001, US-002, US-003

### 2. Alex - Software Developer (Power User)
- **Focus**: API integration, code enhancement, advanced features
- **Test Files**: `alex-developer.spec.ts`
- **User Stories**: US-004, US-005, US-006

### 3. Dr. Chen - Data Scientist (Power User)
- **Focus**: Batch processing, data analysis, metrics
- **Test Files**: `chen-scientist.spec.ts`
- **User Stories**: US-007, US-008, US-009

### 4. Maria - Content Creator (Power User)
- **Focus**: Templates, bulk operations, team features
- **Test Files**: `maria-content.spec.ts`
- **User Stories**: US-010, US-011, US-012

### 5. TechCorp - Enterprise Admin
- **Focus**: SSO, compliance, team management
- **Test Files**: `techcorp-enterprise.spec.ts`
- **User Stories**: US-013, US-014, US-015, US-016

## 📊 Test Coverage

### Current Implementation Status
- ✅ Playwright configuration
- ✅ Page Object Models (7 pages)
- ✅ Test fixtures and data factories
- ✅ Helper utilities
- ✅ Sarah persona tests (12 test cases)
- ✅ Alex persona tests (14 test cases)
- 🔄 Dr. Chen tests (pending)
- 🔄 Maria tests (pending)
- 🔄 TechCorp tests (pending)
- 🔄 Cross-cutting tests (pending)

### Test Categories
- **@smoke**: Quick validation tests (<5 min)
- **@critical**: Essential user journeys
- **@regression**: Comprehensive test suite
- **@performance**: Performance validation
- **@accessibility**: A11y compliance
- **@visual**: Visual regression tests
- **@api**: API integration tests

## 🛠️ Page Object Model

Each page has a corresponding Page Object Model in the `pages/` directory:

```typescript
// Example usage
import { EnhancePage } from './pages/enhance.page';

const enhancePage = new EnhancePage(page);
await enhancePage.goto();
await enhancePage.enhancePrompt('My prompt text', 'Chain of Thought');
```

### Available Page Objects
- `HomePage`: Landing page interactions
- `LoginPage`: Authentication flows
- `RegisterPage`: New user registration
- `DashboardPage`: User dashboard
- `EnhancePage`: Core enhancement functionality
- `HistoryPage`: Enhancement history
- More coming in future waves...

## 🔧 Test Data Management

### User Fixtures
```typescript
import { testUsers } from './fixtures/users';

const sarah = testUsers.sarah; // Marketing manager
const alex = testUsers.alex;   // Developer
```

### Prompt Fixtures
```typescript
import { testPrompts } from './fixtures/prompts';

const marketingPrompt = testPrompts.sarahSimple;
const codePrompt = testPrompts.alexComplex;
```

## 📸 Visual Regression Testing

Visual regression tests use Playwright's built-in screenshot comparison:

```typescript
await helpers.compareScreenshots(page, 'test-name', {
  fullPage: true,
  mask: ['.dynamic-element'],
  maxDiffPixels: 100,
  threshold: 0.2
});
```

Update baseline screenshots:
```bash
npm run visual:update
```

## ♿ Accessibility Testing

All tests include accessibility validation using axe-core:

```typescript
await helpers.checkAccessibility(page, {
  includedImpacts: ['critical', 'serious'],
  detailedReport: true
});
```

## 🚄 Performance Testing

Performance metrics are captured for critical user journeys:

```typescript
await helpers.checkPerformance(page, {
  lcp: 2500,  // Largest Contentful Paint < 2.5s
  fid: 100,   // First Input Delay < 100ms
  cls: 0.1,   // Cumulative Layout Shift < 0.1
  ttfb: 800   // Time to First Byte < 800ms
});
```

## 🔍 Debugging Tests

### Debug Mode
```bash
npm run test:debug
```

### View Test Reports
```bash
npm run report
```

### Generate New Tests
```bash
npx playwright codegen https://app.betterprompts.com
```

## 📈 CI/CD Integration

Tests are configured to run in GitHub Actions:

```yaml
- name: Run E2E Tests
  run: |
    cd e2e/frontend
    npm ci
    npx playwright install --with-deps
    npm test
  env:
    BASE_URL: ${{ secrets.STAGING_URL }}
```

## 🏆 Best Practices

1. **Use Page Objects**: All page interactions through POMs
2. **Data Independence**: Each test creates its own data
3. **Parallel Execution**: Tests run independently
4. **Meaningful Assertions**: Test business logic, not implementation
5. **Stable Selectors**: Use data-testid attributes
6. **Error Handling**: Graceful failure with clear messages
7. **Performance Awareness**: Monitor test execution time

## 🔮 Future Enhancements

### Wave 3: Advanced API Testing
- GraphQL testing support
- WebSocket testing
- Advanced mocking strategies

### Wave 4: Performance Testing
- K6 integration for load testing
- Lighthouse integration
- Custom performance metrics

### Wave 5: Security Testing
- OWASP ZAP integration
- Security scanning automation
- Penetration test scenarios

## 📞 Support

For questions or issues:
- Check the [Wave 1 Test Architecture](../wave1-test-architecture.md)
- Review the [E2E Testing Implementation Plan](../../planning/E2E_TESTING_IMPLEMENTATION_PLAN.md)
- Contact the QA team lead

---

*Last Updated: January 2025*
*Wave 2 Implementation - In Progress*