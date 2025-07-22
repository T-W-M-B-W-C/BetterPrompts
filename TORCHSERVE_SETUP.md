# TorchServe Configuration Guide

## Current Setup

We now have a **dual configuration system** that allows fast development while preserving production settings.

### Configuration Files

1. **Development** (`config.properties.dev`):
   - Single worker, no batching
   - Minimal latency (batch_delay=0)
   - Lower memory usage (1GB)
   - Fast startup and response

2. **Production** (`config.properties.prod`):
   - Multiple workers (2-4)
   - Batch processing enabled
   - Higher memory (4GB)
   - Optimized for throughput

3. **Active Config** (`config.properties`):
   - Symbolic link pointing to either dev or prod
   - Currently points to: **development**

## Quick Start

### 1. Ensure Development Mode is Active
```bash
# Check current configuration
./scripts/switch-torchserve-env.sh status

# Switch to development if needed
./scripts/switch-torchserve-env.sh dev
```

### 2. Restart TorchServe with New Config
```bash
# Restart the service
docker compose restart torchserve

# Wait for it to be ready
sleep 10

# Verify it's working
curl http://localhost:8080/ping
```

### 3. Initialize the Model
```bash
# Run the v2 initialization script
./infrastructure/model-serving/scripts/init_local_model_v2.sh
```

### 4. Test Performance
```bash
# Run performance test
./scripts/test-torchserve-performance.sh
```

You should now see response times under 200ms!

## Switching Environments

### For Development (Fast)
```bash
./scripts/switch-torchserve-env.sh dev
docker compose restart torchserve
```

### For Production (Scalable)
```bash
./scripts/switch-torchserve-env.sh prod
docker compose restart torchserve
```

## Key Differences

| Feature | Development | Production |
|---------|------------|------------|
| Workers | 1 | 2-4 |
| Batching | Disabled | Enabled (size=8) |
| Batch Delay | 0ms | 100ms |
| Memory | 1GB | 4GB |
| Response Time | <200ms | <500ms |
| Throughput | Low | High |
| GPU Support | No | Yes |

## Performance Comparison

### Before (Production Config in Dev)
- Response time: 2-5 seconds
- High memory usage
- Waiting for batch timeout

### After (Development Config)
- Response time: 50-200ms
- Low memory usage
- Instant response

## Troubleshooting

### Still Slow?
1. Check config is active: `ls -la infrastructure/model-serving/torchserve/config/config.properties`
2. Ensure container restarted: `docker compose ps torchserve`
3. Check logs: `docker compose logs --tail=50 torchserve`
4. Re-initialize model: `./infrastructure/model-serving/scripts/init_local_model_v2.sh`

### Can't Switch Configs?
```bash
# Manually fix symbolic link
cd infrastructure/model-serving/torchserve/config
rm -f config.properties
ln -sf config.properties.dev config.properties
```

## Docker Compose Override

The environment switcher also creates `docker-compose.override.yml` with environment-specific settings:

- **Development**: Lower memory, debug logging
- **Production**: Higher memory, GPU support, info logging

This file is automatically applied when you run `docker compose` commands.

## Best Practices

1. **Always use dev mode for local development**
   - 10-50x faster response times
   - Lower resource usage
   - Faster iteration

2. **Switch to prod mode only when**:
   - Testing production scenarios
   - Benchmarking throughput
   - Using real GPU models

3. **After switching environments**:
   - Always restart TorchServe
   - Re-initialize models if needed
   - Run performance test to verify

## Next Steps

1. Continue with development using the fast config
2. Implement the prompt generation techniques
3. Complete frontend-backend integration
4. When ready for production, switch to prod config and deploy real models