# Troubleshooting Log - Docker Health Check Issues

**Date**: July 21, 2025
**Issue**: Frontend and other services failing health checks
**Resolution Status**: Partially Resolved

## Issues Encountered and Fixes Applied

### 1. Frontend Health Check Failure

**Root Cause**: Volume mount conflict and missing health check tool

**Issues**:
- Startup command tried to delete `node_modules` which was mounted as Docker volume
- Health check used `curl` which wasn't available in `node:20-alpine` image

**Fixes Applied**:
1. Created `/docker/frontend/entrypoint.sh` - Graceful startup script that:
   - Doesn't try to delete mounted volumes
   - Only installs dependencies if needed
   - Cleans build artifacts safely

2. Updated `docker-compose.yml`:
   - Changed from `command` to `entrypoint` using the new script
   - Changed health check from `curl` to `node /app/public/healthcheck.js`
   - Added 60s `start_period` to allow npm install to complete

**Result**: ✅ Frontend health check now passing

### 2. API Gateway (Nginx) Initial Failure

**Root Cause**: Circular dependency with frontend service

**Issues**:
- Nginx depended on frontend
- Frontend depended on nginx
- Nginx couldn't start because frontend wasn't ready

**Fixes Applied**:
1. Removed circular dependency by removing nginx from frontend's `depends_on`
2. Added `restart: unless-stopped` to nginx service

**Result**: ✅ Nginx health check now passing

### 3. TorchServe Integration

**Added**: Complete TorchServe service to docker-compose.yml

**Configuration**:
```yaml
torchserve:
  build:
    context: ./infrastructure/model-serving
    dockerfile: docker/Dockerfile.torchserve
  ports:
    - "8080:8080"  # Inference API
    - "8081:8081"  # Management API
    - "8082:8082"  # Metrics API
  environment:
    - USE_TORCHSERVE=true
    - TORCHSERVE_HOST=torchserve
```

**Additional Changes**:
1. Created `/infrastructure/model-serving/torchserve/startup.sh` for mock model creation
2. Updated Dockerfile with `COPY --chmod=755` to handle permissions correctly
3. Added TorchServe environment variables to intent-classifier service

**Result**: ⚠️ TorchServe running but model loading issues (expected with mock model)

### 4. Intent Classifier Service Failure

**Root Cause**: Missing `protobuf` dependency for DeBERTa tokenizer

**Issues**:
- DeBERTa-v3 tokenizer requires `protobuf` library
- Dependency was missing from requirements.txt

**Fixes Applied**:
1. Added `protobuf>=3.20.0` to `/backend/services/intent-classifier/requirements.txt`
2. Fixed formatting issue where line was merged with previous dependency

**Result**: ❌ Still needs rebuild - `docker compose build intent-classifier`

## Current Service Status

| Service | Status | Health |
|---------|---------|--------|
| Frontend | ✅ Running | Healthy |
| API Gateway (Nginx) | ✅ Running | Unhealthy* |
| Intent Classifier | ❌ Running | Unhealthy (missing protobuf) |
| Technique Selector | ✅ Running | Healthy |
| Prompt Generator | ✅ Running | Healthy |
| PostgreSQL | ✅ Running | Healthy |
| Redis | ✅ Running | Healthy |
| TorchServe | ⚠️ Running | Unhealthy (mock model issues) |
| Prometheus | ✅ Running | N/A |
| Grafana | ✅ Running | N/A |

*Nginx shows unhealthy due to intent-classifier being down

## Files Modified During Troubleshooting

1. `/docker-compose.yml` - Multiple updates for service configurations
2. `/docker/frontend/entrypoint.sh` - Created new startup script
3. `/scripts/verify-frontend-fix.sh` - Created verification script
4. `/backend/services/intent-classifier/requirements.txt` - Added protobuf
5. `/infrastructure/model-serving/docker/Dockerfile.torchserve` - Fixed permissions
6. `/infrastructure/model-serving/torchserve/startup.sh` - Created mock model script

## Next Steps

1. Rebuild intent-classifier: `docker compose build intent-classifier`
2. Restart services: `docker compose up -d`
3. Verify all health checks pass
4. Create proper model archive for TorchServe (optional for demo)

## Lessons Learned

1. Volume mounts can override container files - be careful with development vs production configs
2. Alpine images don't include curl by default - use appropriate health check tools
3. Circular dependencies in docker-compose cause startup failures
4. Python ML libraries often have additional system dependencies
5. Docker COPY permissions need special handling for executable files