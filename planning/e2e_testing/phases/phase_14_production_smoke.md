# Phase 14: Production Smoke Tests

## Overview
- **User Story**: "Continuous validation in production environment"
- **Duration**: 2 days
- **Complexity**: Low - Read-only tests, monitoring integration
- **Status**: 🔒 BLOCKED (Requires Phase 13)

## Dependencies
- **Depends On**: Phase 13 (Complete User Journeys)
- **Enables**: Production monitoring and alerting
- **Can Run In Parallel With**: None (final phase)

## Why This Next
- Final safety net
- Continuous validation
- Early issue detection
- SLA monitoring

## Implementation Command
```bash
/sc:test e2e \
  --persona-devops \
  --persona-qa \
  --play --seq \
  --validate --safe-mode \
  --uc \
  --phase-config '{
    "phase": 14,
    "name": "Production Smoke Tests",
    "focus": ["monitoring", "stability"],
    "environment": "production",
    "duration": "2 days",
    "complexity": "low",
    "safety": "read_only",
    "dependencies": ["phase_13"]
  }' \
  --test-requirements '{
    "smoke_tests": {
      "health_checks": {
        "endpoints": ["/health", "/api/v1/health", "/api/v1/status"],
        "expected_response": {
          "status": "healthy",
          "services": ["database", "redis", "ml_service"],
          "response_time": "<100ms"
        }
      },
      "core_flows": {
        "homepage_load": {
          "target": "<3s",
          "elements": "all_visible",
          "console_errors": 0
        },
        "anonymous_enhancement": {
          "test_prompt": "safe_test_prompt",
          "response_required": true,
          "no_data_saved": true
        },
        "login_flow": {
          "test_account": "smoke-test-basic@betterprompts.com",
          "immediate_logout": true,
          "no_side_effects": true
        },
        "api_health": {
          "endpoint": "/api/v1/test",
          "response_time": "<200ms",
          "rate_limits": "active"
        }
      },
      "execution": {
        "frequency": "every_30_minutes",
        "timeout": "30s",
        "retry_policy": "exponential_backoff",
        "regions": ["us-east-1", "us-west-2", "eu-west-1"]
      }
    },
    "monitoring_integration": {
      "metrics": {
        "smoke_test.duration": "execution_time",
        "smoke_test.success": "pass_rate",
        "smoke_test.homepage_load": "page_load_time",
        "smoke_test.api_response": "api_latency"
      },
      "services": ["datadog", "new_relic", "cloudwatch"],
      "dashboards": ["production_health", "smoke_test_status"]
    },
    "alerting": {
      "critical": {
        "condition": "success_rate < 0.9",
        "window": "5_minutes",
        "notify": ["oncall@betterprompts.com", "slack:#alerts"]
      },
      "warning": {
        "condition": "api_response > 500ms",
        "window": "10_minutes",
        "notify": ["team@betterprompts.com"]
      }
    }
  }' \
  --test-patterns '{
    "safety_rules": {
      "no_writes": "GET_requests_only",
      "test_accounts": "dedicated_smoke_accounts",
      "rate_limits": "stay_under_10%",
      "cleanup": "logout_after_test",
      "error_handling": "never_expose"
    },
    "scheduling": {
      "github_actions": "cron: */30 * * * *",
      "aws_lambda": "cloudwatch_events",
      "kubernetes": "cronjob",
      "external": ["pingdom", "statuscake"]
    }
  }' \
  --deliverables '{
    "test_files": [
      "production-smoke.spec.ts",
      "production-health-checks.spec.ts"
    ],
    "configurations": [
      "production-test.config.ts",
      "monitoring-integration.yaml",
      "alert-rules.yaml",
      "cron-schedule.yaml"
    ],
    "utilities": [
      "production-safe-helper.ts",
      "monitoring-reporter.ts",
      "test-account-manager.ts"
    ],
    "documentation": [
      "smoke-test-runbook.md",
      "alert-response-guide.md",
      "production-test-strategy.md"
    ]
  }' \
  --validation-gates '{
    "safety": {
      "zero_production_impact": true,
      "read_only_verified": true,
      "test_isolation": true
    },
    "reliability": {
      "99.9%_success_rate": true,
      "false_positive_rate": "<1%",
      "execution_time": "<30s"
    },
    "monitoring": {
      "metrics_published": true,
      "alerts_configured": true,
      "dashboards_updated": true
    }
  }' \
  --output-dir "e2e/phase14"
```

## Success Metrics
- [ ] 99.9% test success rate
- [ ] <30s total execution
- [ ] Zero production impact
- [ ] Immediate alerting
- [ ] No false positives
- [ ] Clear error reporting

## Progress Tracking
- [ ] Test file created: `production-smoke.spec.ts`
- [ ] Production config separate from dev
- [ ] Test accounts provisioned
- [ ] Health check tests implemented
- [ ] Core flow tests implemented
- [ ] Performance checks added
- [ ] Monitoring integration complete
- [ ] Alert rules configured
- [ ] Schedule automation setup
- [ ] Documentation updated

## Test Scenarios

### Health Check Tests
```javascript
// Endpoint checks
GET /health
GET /api/v1/health
GET /api/v1/status

// Expected responses
{
  "status": "healthy",
  "version": "1.2.3",
  "timestamp": "2024-01-27T10:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "ml_service": "healthy"
  }
}
```

### Core User Flows (Read-Only)
1. **Homepage Load**
   - Load time <3s
   - All elements visible
   - No console errors

2. **Anonymous Enhancement**
   - Use safe test prompt
   - Verify response received
   - No data saved

3. **Login Flow**
   - Test account login
   - Verify redirect
   - Immediate logout

4. **API Health**
   - Test endpoint available
   - Response time <200ms
   - Rate limits active

### Performance Checks
- Page load time
- API response time
- Database query time
- Cache hit rate
- Error rate

### Monitoring Integration
```javascript
// DataDog / New Relic / CloudWatch
const metrics = {
  'smoke_test.duration': executionTime,
  'smoke_test.success': success ? 1 : 0,
  'smoke_test.homepage_load': homepageLoadTime,
  'smoke_test.api_response': apiResponseTime,
};

// Send to monitoring service
monitoring.recordMetrics(metrics);
```

### Alert Configuration
```yaml
alerts:
  - name: smoke_test_failure
    condition: smoke_test.success < 0.9
    window: 5 minutes
    severity: critical
    notify: 
      - oncall@betterprompts.com
      - slack:#alerts

  - name: performance_degradation
    condition: smoke_test.api_response > 500
    window: 10 minutes
    severity: warning
    notify:
      - team@betterprompts.com
```

## Notes & Updates

### Prerequisites
- Production environment deployed
- Test accounts created
- Monitoring service configured
- Alert channels setup

### Production Safety Rules
1. **No Write Operations**: Only GET requests
2. **Use Test Accounts**: Never real user data
3. **Rate Limit Respect**: Stay well under limits
4. **Cleanup**: Logout after each test
5. **Error Handling**: Never expose errors

### Test Account Management
```javascript
// Dedicated smoke test accounts
const testAccounts = {
  basic: {
    email: 'smoke-test-basic@betterprompts.com',
    password: process.env.SMOKE_TEST_PASSWORD
  },
  premium: {
    email: 'smoke-test-premium@betterprompts.com',
    password: process.env.SMOKE_TEST_PASSWORD
  }
};

// Rotate passwords monthly
// Disable features that could affect real users
// Monitor for unauthorized access
```

### Scheduling Options
```bash
# Option 1: GitHub Actions
- cron: '*/30 * * * *'  # Every 30 minutes

# Option 2: AWS Lambda
- CloudWatch Events trigger

# Option 3: Kubernetes CronJob
- schedule: "*/30 * * * *"

# Option 4: External monitoring
- Pingdom, StatusCake, etc.
```

### Common Issues
- **False positives**: Tune thresholds based on baseline
- **Test account locked**: Implement auto-unlock
- **Network issues**: Add retry logic
- **Timing issues**: Account for peak traffic
- **Regional differences**: Run from multiple locations

---

*Last Updated: 2025-01-27*