# Just Command Modules

This directory contains modular Just files for organizing project commands.

## Structure

```
just/
├── database.just    # Database management commands
├── docker.just      # Docker service management
├── health.just      # Health checks and monitoring
├── performance.just # Performance testing and benchmarks
├── services.just    # Service-specific testing
└── test.just        # General testing commands
```

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

## Usage

All commands are available from the project root:

```bash
# Show all available commands
just

# Start services
just up

# Run auth tests
just test-auth

# Check health
just health
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