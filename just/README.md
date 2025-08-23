# Just Command Modules

This directory contains modular Just files for organizing project commands.

## Structure

```
just/
├── first-time.just  # Complete first-time setup
├── up.just          # Start application (various modes)
├── down.just        # Stop application (various modes)
├── database.just    # Database management commands
├── diagnostic.just  # Troubleshooting and debugging
├── docker.just      # Docker service management
├── health.just      # Health checks and monitoring
├── performance.just # Performance testing and benchmarks
├── prompts.just     # Prompt testing scenarios
├── services.just    # Service-specific testing
└── test.just        # General testing commands
```

## 🎯 Primary Commands

### 🚀 first-time.just
**Complete first-time setup for new developers**
- `first-time` - Run complete setup (checks, deps, build, db, tests)
- `check-requirements` - Verify system requirements
- `install-deps` - Install Python dependencies
- `setup-env` - Create .env file
- `build-all` - Build all Docker images
- `setup-database` - Initialize PostgreSQL with migrations
- `run-tests` - Run smoke tests
- `clean-first-time` - Clean everything for fresh start

### ⬆️ up.just
**Start the application with various options**
- `up` - Start with health checks (recommended)
- `up-fast` - Quick start without checks
- `up-attached` - Start with live logs
- `up-dev` - Development mode with hot reload
- `up-prod` - Production mode
- `up-build` - Rebuild and start
- `up-fresh` - Start with clean database
- `up-monitor` - Start with Grafana dashboard

### ⬇️ down.just
**Stop the application with cleanup options**
- `down` - Graceful stop (default)
- `down-clean` - Stop and remove containers
- `down-all` - Remove everything including volumes
- `down-backup` - Backup data before stopping
- `down-force` - Emergency force stop
- `pause/resume` - Pause and resume services
- `restart` - Quick restart
- `restart-full` - Full restart with new containers

## Modules

### 🐳 docker.just
- Service lifecycle (up/down/restart)
- Log management
- Container rebuilding
- Configuration viewing

### 💾 database.just
- Database setup and migrations
- Schema management
- Database shell access
- Reset and cleanup

### 🧪 test.just
- Authentication testing
- Integration tests
- End-to-end tests
- Smoke tests

### 🔧 services.just
- Technique selector testing
- Prompt generator testing
- Service-specific debugging
- Technique listing

### 🏥 health.just
- Service health checks
- Status monitoring
- Resource usage tracking

### ⚡ performance.just
- Service benchmarking
- Load testing
- Performance metrics

### 🔍 diagnostic.just
- System troubleshooting
- Service debugging
- Communication testing
- Configuration validation

### 📝 prompts.just
- Scenario-based testing
- Intent-specific tests
- Complexity variations
- Real-world examples

## Usage

All commands are available from the project root:

```bash
# First-time setup (run this once)
just first-time

# Daily workflow
just up          # Start everything
just health      # Check status
just down        # Stop when done

# Testing
just test-auth   # Test authentication
just smoke-test  # Quick validation

# Maintenance
just restart     # Quick restart
just down-backup # Stop with backup
```

## Adding New Modules

1. Create a new `.just` file in this directory
2. Add commands following the existing patterns
3. Import the module in the main `Justfile`:
   ```just
   import 'just/your-module.just'
   ```

## Best Practices

- Use descriptive command names
- Add helpful echo statements
- Include default parameter values
- Group related commands together
- Add comments for complex operations