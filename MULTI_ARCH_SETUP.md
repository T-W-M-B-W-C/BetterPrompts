# Multi-Architecture Docker Setup

This document explains how to run BetterPrompts on both Intel and ARM-based Macs without architecture conflicts.

## Quick Start

### 1. Initial Setup
```bash
# Clone and enter the repository
git clone <repository-url>
cd BetterPrompts

# Run platform detection and configuration
./scripts/setup-platform.sh

# Start the application
docker compose up -d
```

That's it! The setup script automatically detects your Mac type and configures everything appropriately.

## How It Works

### Platform Detection
The `setup-platform.sh` script automatically:
- Detects your Mac architecture (Intel x86_64 vs Apple Silicon ARM64)
- Copies the appropriate environment file (`.env.intel` or `.env.arm64`)
- Sets up Docker buildx for multi-platform builds
- Configures platform-specific Docker settings

### Architecture-Specific Configurations

#### Intel Macs (x86_64)
- Uses `linux/amd64` platform
- PyTorch with CPU optimizations via index URL
- Higher memory allocation (2GB) for TorchServe
- Optimized build settings for x86 architecture

#### Apple Silicon Macs (ARM64)
- Uses `linux/arm64` platform  
- PyTorch with default installation (ARM64 compatible)
- Reduced memory allocation (1GB) for TorchServe
- ARM-optimized build settings

## Available Scripts

### Platform Setup
```bash
./scripts/setup-platform.sh
```
Automatically detects and configures your platform.

### Building Images
```bash
# Build all services
./scripts/build.sh

# Build specific service
./scripts/build.sh --target api-gateway

# Build and push to registry
./scripts/build.sh --push --registry your-registry.com

# Build with specific version
./scripts/build.sh --version v1.0.0
```

### Starting Services
```bash
# Option 1: Use the configured compose command from setup-platform.sh
docker compose up -d

# Option 2: Manual override (if you know your architecture)
# For Intel:
docker compose -f docker-compose.yml -f docker-compose.intel.yml up -d

# For ARM:
docker compose -f docker-compose.yml -f docker-compose.arm64.yml up -d
```

## File Structure

```
├── .env.intel              # Intel Mac environment config
├── .env.arm64              # ARM Mac environment config  
├── docker-compose.yml      # Base compose configuration
├── docker-compose.intel.yml # Intel-specific overrides
├── docker-compose.arm64.yml # ARM-specific overrides
├── scripts/
│   ├── setup-platform.sh   # Platform detection script
│   └── build.sh            # Multi-arch build script
```

## Configuration Details

### Environment Variables
The platform setup automatically configures:

- `DOCKER_PLATFORM`: Target platform (linux/amd64 or linux/arm64)
- `PYTORCH_INDEX_URL`: PyTorch installation source (Intel-specific or default)
- `JAVA_OPTS`: Memory settings optimized for architecture
- `TORCHSERVE_TYPE`: CPU-only for development compatibility

### Docker Compose Overrides
Each architecture has specific overrides:

**Intel (.intel.yml)**:
- Platform: `linux/amd64`
- TorchServe memory: 2GB
- PyTorch: CPU-optimized index

**ARM (.arm64.yml)**:
- Platform: `linux/arm64`  
- TorchServe memory: 1GB
- PyTorch: Default installation

## Troubleshooting

### "No matching manifest" errors
```bash
# Re-run platform setup
./scripts/setup-platform.sh

# Ensure buildx is configured
docker buildx ls
```

### Build failures
```bash
# Clean Docker cache
docker system prune -a

# Rebuild with no cache
./scripts/build.sh --target <service> --no-cache
```

### Platform detection issues
Check your platform manually:
```bash
echo "OS: $(uname -s)"
echo "Architecture: $(uname -m)"
```

### Memory issues on ARM
If TorchServe fails to start, reduce memory further in `.env.arm64`:
```bash
JAVA_OPTS=-Xmx512m -Xms256m -XX:+UseG1GC
```

## Development Workflow

### Team Collaboration
1. Each developer runs `./scripts/setup-platform.sh` once
2. Platform-specific `.env` files are created locally (not committed)
3. All Docker builds work regardless of Mac type
4. No manual configuration needed

### CI/CD Considerations
For production deployment:
```bash
# Build for both architectures
docker buildx build --platform linux/amd64,linux/arm64 .

# Or target specific production architecture
docker buildx build --platform linux/amd64 .
```

## Technical Implementation

### Key Changes Made

1. **Platform Detection**: Automatic architecture detection in setup script
2. **Docker Compose**: Platform specifications for all services
3. **Dockerfile Updates**: Conditional PyTorch installation
4. **TorchServe**: Flexible base image selection (CPU vs GPU)
5. **Build Scripts**: Architecture-aware build process

### Supported Platforms
- ✅ Intel Mac (x86_64)
- ✅ Apple Silicon Mac (ARM64)
- ✅ Linux x86_64
- ✅ Linux ARM64 (experimental)

## Performance Notes

### Intel Macs
- Full feature support
- Optimized PyTorch with CPU extensions
- Higher memory allocation for models

### Apple Silicon Macs  
- CPU-only operation (no GPU acceleration)
- Reduced memory footprint
- Native ARM64 performance benefits

## FAQ

**Q: Do I need to configure anything manually?**
A: No, just run `./scripts/setup-platform.sh` once.

**Q: Can Intel and ARM developers work on the same project?**
A: Yes, each developer's setup is automatically configured for their platform.

**Q: What about production deployment?**
A: Use the build scripts with `--platform` flags to target your production architecture.

**Q: Are there performance differences?**
A: Apple Silicon runs natively but CPU-only. Intel has more memory allocated by default.

**Q: Can I override the automatic configuration?**
A: Yes, manually edit your `.env` file or use specific compose override files.