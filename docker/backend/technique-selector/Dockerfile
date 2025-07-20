# Technique Selection Engine - Go/Gin
# Build stage
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache gcc musl-dev sqlite-dev

# Set working directory
WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application with optimizations
RUN CGO_ENABLED=1 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s -extldflags '-static'" \
    -a -installsuffix cgo \
    -o technique-selector \
    ./cmd/server

# Production stage
FROM alpine:3.19

# Install runtime dependencies
RUN apk add --no-cache \
    ca-certificates \
    tzdata \
    curl

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S -u 1001 -G appgroup appuser

WORKDIR /app

# Copy binary from builder to a specific location
COPY --from=builder /app/technique-selector /usr/local/bin/technique-selector

# Copy configuration files if they exist
COPY --chown=appuser:appgroup configs* ./configs/

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appgroup /app

# Set environment variables
ENV GIN_MODE=release \
    PORT=8002 \
    TZ=UTC

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Start the application
CMD ["/usr/local/bin/technique-selector"]