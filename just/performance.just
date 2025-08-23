# Performance Testing Commands

# Benchmark technique selection
bench-selector count="10":
    @echo "⏱️ Benchmarking Technique Selector ({{count}} requests)..."
    @time for i in $(seq 1 {{count}}); do \
        curl -s -X POST http://localhost:8002/api/v1/select \
            -H "Content-Type: application/json" \
            -d '{"text": "Test prompt", "intent": "code_generation", "complexity": "moderate"}' \
            > /dev/null; \
    done

# Benchmark prompt generation
bench-generator count="10":
    @echo "⏱️ Benchmarking Prompt Generator ({{count}} requests)..."
    @time for i in $(seq 1 {{count}}); do \
        curl -s -X POST http://localhost:8003/api/v1/generate \
            -H "Content-Type: application/json" \
            -d '{"text": "Test prompt", "intent": "code_generation", "complexity": "moderate"}' \
            > /dev/null; \
    done

# Benchmark API gateway auth
bench-auth count="10":
    @echo "⏱️ Benchmarking Auth Endpoints ({{count}} requests)..."
    @time for i in $(seq 1 {{count}}); do \
        curl -s -X POST http://localhost:8000/api/v1/auth/login \
            -H "Content-Type: application/json" \
            -d '{"email_or_username": "test", "password": "Test123!"}' \
            > /dev/null; \
    done

# Load test with concurrent requests
load-test service="generator" concurrent="5" requests="20":
    @echo "🔥 Load Testing {{service}} ({{concurrent}} concurrent, {{requests}} total)..."
    @ab -n {{requests}} -c {{concurrent}} -p /tmp/test.json -T application/json \
        http://localhost:8003/api/v1/generate 2>/dev/null || echo "Install apache2-utils for load testing"