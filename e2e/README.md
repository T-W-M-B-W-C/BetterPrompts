# BetterPrompts E2E Tests

End-to-end tests for the BetterPrompts application using Playwright.

## Test Phases

### Phase 2 - Live Application Testing
Location: `phase2/`

Phase 2 tests run against the actual BetterPrompts application with real services:
- Real PostgreSQL database (separate E2E instance)
- Real Redis cache
- MailHog for email testing
- Live API Gateway and Frontend services

## Quick Start

### Run Phase 2 Tests (Live)
```bash
# Run all tests with automatic setup/teardown
./run-tests.sh

# Keep services running for debugging
./run-tests.sh --skip-teardown

# Run if services already running
./run-tests.sh --skip-setup
```

### Manual Control
```bash
# Setup test environment
./setup-test-env.sh

# Run tests
cd frontend && npm test

# Teardown environment
cd .. && ./teardown-test-env.sh
```

## Test Environment

### Services (E2E)
- **Frontend**: http://localhost
- **API Gateway**: http://localhost/api/v1
- **MailHog UI**: http://localhost:8025
- **PostgreSQL**: localhost:5433 (test DB)
- **Redis**: localhost:6380 (test cache)

### Test Helpers
Located in `test-helpers/`:
- `database.ts` - Database utilities (cleanup, user queries)
- `mailhog.ts` - Email testing utilities

## Writing Tests

1. **Page Objects**: Use page objects pattern for UI interaction
2. **Test Isolation**: Clean database/emails in beforeEach
3. **Real Services**: Tests interact with actual API and database
4. **Email Testing**: Verify emails via MailHog API

## Debugging

### View Emails
Open http://localhost:8025 to see all test emails.

### Database Access
```bash
docker exec -it betterprompts-postgres-e2e psql -U betterprompts betterprompts_e2e
```

### Test Reports
```bash
open phase2/test-results/html/index.html
```

## Directory Structure

```
e2e/
├── phase2/                    # Live application tests
│   ├── tests/                # Test specifications
│   ├── pages/                # Page objects
│   ├── utils/                # Test utilities
│   └── playwright.config.ts  # Playwright config
├── test-helpers/             # Shared test utilities
├── docker-compose.e2e.yml    # E2E Docker services
├── setup-test-env.sh         # Environment setup
├── teardown-test-env.sh      # Environment cleanup
└── run-tests.sh              # Test runner script
```