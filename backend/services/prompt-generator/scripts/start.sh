#!/bin/bash

# Start script for Prompt Generation Service

# Set environment defaults
export PYTHONUNBUFFERED=1
export PYTHONPATH=/app:$PYTHONPATH

# Wait for dependencies
echo "Waiting for dependencies..."

# Wait for database (if DATABASE_URL is set)
if [ ! -z "$DATABASE_URL" ]; then
    echo "Waiting for database..."
    # Add database wait logic here
fi

# Wait for Redis (if REDIS_URL is set)
if [ ! -z "$REDIS_URL" ]; then
    echo "Waiting for Redis..."
    # Add Redis wait logic here
fi

# Download any required models or data
if [ ! -d "/app/models/cache" ]; then
    echo "Setting up model cache directory..."
    mkdir -p /app/models/cache
fi

# Start the application
echo "Starting Prompt Generation Service..."

if [ "$DEBUG" = "true" ]; then
    # Development mode with auto-reload
    exec python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port ${PORT:-8003} \
        --reload \
        --log-level debug
else
    # Production mode
    exec python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port ${PORT:-8003} \
        --workers ${WORKERS:-4} \
        --log-level ${LOG_LEVEL:-info}
fi