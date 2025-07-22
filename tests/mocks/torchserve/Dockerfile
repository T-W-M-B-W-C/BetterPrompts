# Mock TorchServe for testing
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn==0.27.0 \
    pydantic==2.5.3 \
    httpx==0.26.0

# Copy mock server implementation
COPY mock_server.py /app/
COPY responses.json /app/

# Expose TorchServe default port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=5s --timeout=3s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/ping').raise_for_status()"

# Run the mock server
CMD ["uvicorn", "mock_server:app", "--host", "0.0.0.0", "--port", "8080"]