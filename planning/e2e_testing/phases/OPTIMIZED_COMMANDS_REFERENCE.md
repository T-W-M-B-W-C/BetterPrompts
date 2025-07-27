# SuperClaude Optimized Commands Reference

## Overview
This document provides a quick reference for all optimized SuperClaude commands across the E2E testing phases. Each command has been optimized following best practices for the SuperClaude framework.

## Command Summary Table

| Phase | Focus | Primary Command | Key Personas | MCP Servers | Complexity |
|-------|-------|----------------|--------------|-------------|------------|
| 00 | Foundation Architecture | `/sc:analyze` | architect, analyzer, qa | seq, c7 | High - Wave |
| 01 | Anonymous Enhancement | `/sc:test e2e` | qa | play | Low |
| 02 | User Registration | `/sc:test e2e` | qa, security | play, seq | Medium |
| 03 | Login & Session | `/sc:test e2e` | qa, security, backend | play, seq, c7 | Medium |
| 04 | Auth Enhancement History | `/sc:test e2e` | qa, backend | seq, play, c7 | High - Wave |
| 05 | Technique Education | `/sc:test e2e` | qa, frontend | play, magic | Low |
| 06 | Batch Processing | `/sc:test e2e` | qa, performance, backend | play, seq, c7 | High - Wave |
| 07 | API Integration | `/sc:test e2e` | qa, backend, security, devops | play, seq, c7 | High |
| 08 | Performance Load | `/sc:test performance` | qa, performance, devops | play, seq, c7 | High - Wave |
| 09 | Input Validation | `/sc:test e2e` | qa, security | play, seq, c7 | Medium |
| 10 | Rate Limiting | `/sc:test e2e` | qa, performance, security, backend | play, seq | Medium |
| 11 | Security Testing | `/sc:test security` | security, qa, backend | play, seq, c7 | High |
| 12 | Mobile Accessibility | `/sc:test e2e` | qa, frontend | play, magic, c7 | Medium |
| 13 | Complete Journeys | `/sc:test e2e` | qa, architect, frontend, backend | all-mcp | High - Wave |
| 14 | Production Smoke | `/sc:test e2e` | qa, devops | play, seq | Low |

## Common Flags Used

### Thinking Flags
- `--think`: Basic analysis (Phases 1, 5, 14)
- `--think-hard`: Deep analysis (Phases 0, 6, 7, 8, 10, 13)
- `--ultrathink`: Critical analysis (Phase 11 - Security)

### Validation & Safety
- `--validate`: Pre-execution validation (all phases)
- `--safe-mode`: Production safety (Phase 14)

### Performance & Efficiency
- `--uc`: Ultra-compressed mode (Phase 14)
- `--delegate auto`: Parallel processing (Phases 6, 7, 13)

### Wave Orchestration
- `--wave-mode force`: Complex multi-stage operations
- `--wave-strategy systematic`: Methodical analysis
- `--wave-strategy progressive`: Iterative enhancement
- Used in Phases: 0, 4, 6, 8, 13

### MCP Server Flags
- `--play`: Playwright for E2E testing (all test phases)
- `--seq`: Sequential for complex analysis
- `--c7`: Context7 for documentation/patterns
- `--magic`: Magic for UI components (Phases 5, 12)
- `--all-mcp`: All servers (Phase 13)

## Optimization Patterns Applied

### 1. Command Selection
- `/sc:test e2e` for E2E testing scenarios
- `/sc:test performance` for load testing
- `/sc:test security` for security audits
- `/sc:analyze` for architectural analysis

### 2. Persona Activation
- QA persona as primary for all test phases
- Domain-specific personas based on phase focus
- Multiple personas for complex scenarios

### 3. Structured JSON Arguments
All commands now use structured JSON for:
- Requirements specification
- Test scenarios definition
- Deliverables listing
- Validation gates
- Dependencies tracking

### 4. Complexity-Based Configuration
- **Low Complexity**: Minimal flags, single persona
- **Medium Complexity**: Multiple personas, sequential processing
- **High Complexity**: Wave mode, delegation, all MCP servers

### 5. Phase-Specific Optimizations
- **Auth Phases (2-4)**: Security persona, JWT focus
- **UI Phases (5, 12)**: Frontend persona, Magic server
- **Performance (6, 8, 10)**: Performance persona, metrics focus
- **Security (11)**: Ultrathink, comprehensive scanning
- **Integration (7, 13)**: Multiple domains, all servers

## Quick Copy Commands

### Phase 01 - Anonymous Enhancement (Simplest)
```bash
/sc:test e2e --persona-qa --play --think --validate --scope module --focus testing "E2E tests for US-001: Anonymous prompt enhancement flow"
```

### Phase 04 - Auth Enhancement History (Complex Integration)
```bash
/sc:test e2e @planning/e2e_testing/phases/phase_04_auth_enhancement_history.md --persona-qa --persona-backend --seq --play --c7 --think-hard --validate --scope module --focus testing --wave-mode force --wave-strategy systematic --wave-delegation tasks "E2E tests for US-002 + US-007: Authenticated enhancement with persistent history"
```

### Phase 08 - Performance Load (Specialized)
```bash
/sc:test performance --persona-qa --persona-performance --persona-devops --play --seq --c7 --think-hard --validate --scope system --focus performance --wave-mode force --wave-strategy systematic --delegate tasks "E2E tests for US-005 + PS-01: Performance metrics and load testing at scale"
```

### Phase 13 - Complete Journeys (Most Complex)
```bash
/sc:test e2e --persona-qa --persona-architect --persona-frontend --persona-backend --all-mcp --think-hard --validate --scope system --focus testing --wave-mode force --wave-strategy adaptive --delegate auto --concurrency 10 "E2E tests for US-014: Complete user journeys across all features"
```

## Best Practices Summary

1. **Always include** `--validate` for risk assessment
2. **Use wave mode** for complexity score >0.7 AND files >20
3. **Activate multiple personas** for cross-domain testing
4. **Structure all data** in JSON format for better parsing
5. **Include validation gates** for quality assurance
6. **Specify dependencies** explicitly for blocked phases
7. **Tag appropriately** for tracking and organization
8. **Set priority** based on critical path and dependencies

---

*Generated: 2025-07-27*
*Framework: SuperClaude v2.0*