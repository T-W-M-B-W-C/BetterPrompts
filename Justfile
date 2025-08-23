# BetterPrompts Testing & Development Commands
# Usage: just <command>

# Default recipe - show available commands
default:
    @just --list

# Import database commands
import 'database.just'

# Test authentication API
test-auth:
    @echo "Testing authentication API..."
    @/usr/bin/python3 -m pip install --user -q pytest requests 2>/dev/null || true
    @/usr/bin/python3 -m pytest tests/test_auth_api.py tests/test_auth_flow.py -v --tb=short

# Quick auth test
test-auth-quick:
    @pip install -q pytest requests
    @python -m pytest tests/test_auth_api.py::TestAuth::test_login -v

# === Service Management ===

# Start all services
up:
    docker compose up -d
    @echo "✅ Services started"

# Stop all services
down:
    docker compose down
    @echo "🛑 Services stopped"

# Restart specific service(s)
restart service="all":
    #!/bin/bash
    if [ "{{service}}" = "all" ]; then
        docker compose restart
    else
        docker compose restart {{service}}
    fi
    @echo "🔄 Restarted {{service}}"

# View logs for a service
logs service="all" lines="50":
    #!/bin/bash
    if [ "{{service}}" = "all" ]; then
        docker compose logs --tail={{lines}}
    else
        docker compose logs {{service}} --tail={{lines}}
    fi

# === Technique Selector Tests ===

# Test technique selector with different intents
test-selector intent="code_generation" complexity="moderate" text="Write a function":
    @echo "🔍 Testing Technique Selector..."
    @echo "Intent: {{intent}}, Complexity: {{complexity}}"
    @curl -s -X POST http://localhost:8002/api/v1/select \
        -H "Content-Type: application/json" \
        -d '{"text": "{{text}}", "intent": "{{intent}}", "complexity": "{{complexity}}"}' \
        | jq '.'

# Quick test selector for code generation
test-selector-code:
    @just test-selector "code_generation" "moderate" "Write a fibonacci function"

# Test selector with all complexity levels
test-selector-all-complexity intent="code_generation":
    #!/bin/bash
    echo "📊 Testing all complexity levels for {{intent}}..."
    for level in simple moderate complex; do
        echo -e "\n=== Complexity: $level ==="
        curl -s -X POST http://localhost:8002/api/v1/select \
            -H "Content-Type: application/json" \
            -d "{\"text\": \"Test prompt\", \"intent\": \"{{intent}}\", \"complexity\": \"$level\"}" \
            | jq -c '{techniques: [.techniques[].name], confidence}'
    done

# === Prompt Generator Tests ===

# Test prompt generator with auto-selection
test-generator text="Write a function" intent="code_generation" complexity="moderate":
    @echo "🤖 Testing Prompt Generator with auto-selection..."
    @curl -s -X POST http://localhost:8003/api/v1/generate \
        -H "Content-Type: application/json" \
        -d '{"text": "{{text}}", "intent": "{{intent}}", "complexity": "{{complexity}}"}' \
        | jq '{techniques_applied, confidence_score, generation_time_ms}'

# Test prompt generator with manual technique selection
test-generator-manual text="Explain this" technique="analogical" intent="explanation" complexity="simple":
    @echo "🎯 Testing Prompt Generator with manual technique..."
    @curl -s -X POST http://localhost:8003/api/v1/generate \
        -H "Content-Type: application/json" \
        -d '{"text": "{{text}}", "intent": "{{intent}}", "complexity": "{{complexity}}", "techniques": ["{{technique}}"]}' \
        | jq '{techniques_applied, confidence_score}'

# === Integration Tests ===

# Run full integration test
test-integration:
    @echo "🔗 Running Integration Tests..."
    @echo "\n1️⃣ Technique Selector Response:"
    @curl -s -X POST http://localhost:8002/api/v1/select \
        -H "Content-Type: application/json" \
        -d '{"text": "Build a REST API", "intent": "code_generation", "complexity": "moderate"}' \
        | jq -c '[.techniques[].name]'
    @echo "\n2️⃣ Prompt Generator Auto-Selection:"
    @curl -s -X POST http://localhost:8003/api/v1/generate \
        -H "Content-Type: application/json" \
        -d '{"text": "Build a REST API", "intent": "code_generation", "complexity": "moderate"}' \
        | jq '{techniques_applied, confidence_score}'
    @echo "\n3️⃣ Manual Override:"
    @curl -s -X POST http://localhost:8003/api/v1/generate \
        -H "Content-Type: application/json" \
        -d '{"text": "Build a REST API", "intent": "code_generation", "complexity": "moderate", "techniques": ["zero_shot"]}' \
        | jq '{techniques_applied, confidence_score}'

# Test end-to-end flow with different scenarios
test-e2e:
    @echo "🎯 End-to-End Test Suite"
    @echo "\n=== Test 1: Simple Code Generation ==="
    @just test-generator "Sort an array" "code_generation" "simple"
    @echo "\n=== Test 2: Complex Code Generation ==="
    @just test-generator "Build microservice architecture" "code_generation" "complex"
    @echo "\n=== Test 3: Reasoning Task ==="
    @just test-generator "Why does water boil at 100°C?" "reasoning" "moderate"
    @echo "\n=== Test 4: Creative Writing ==="
    @just test-generator "Write a haiku about coding" "creative_writing" "simple"

# === Health Checks ===

# Check health of all services
health:
    @echo "🏥 Health Check Status:"
    @echo -n "Intent Classifier: "
    @curl -s http://localhost:8001/health 2>/dev/null | jq -r '.status' 2>/dev/null || echo "❌ Down"
    @echo -n "Technique Selector: "
    @curl -s http://localhost:8002/health 2>/dev/null | jq -r '.status' 2>/dev/null || echo "❌ Down"
    @echo -n "Prompt Generator: "
    @curl -s http://localhost:8003/health/live 2>/dev/null | jq -r '.status' 2>/dev/null || echo "✅ Up"

# === Utility Commands ===

# List available techniques in prompt generator
list-techniques:
    @echo "📋 Available Techniques:"
    @curl -s http://localhost:8003/api/v1/techniques | jq '.techniques[].id'

# Test specific technique scoring
debug-technique technique="chain_of_thought" text="Explain step by step":
    @echo "🔬 Debugging technique: {{technique}}"
    @curl -s -X POST http://localhost:8002/api/v1/select \
        -H "Content-Type: application/json" \
        -d '{"text": "{{text}}", "intent": "reasoning", "complexity": "moderate"}' \
        | jq '.techniques[] | select(.id == "{{technique}}")'

# Show service configuration
show-config service="technique-selector":
    @echo "⚙️ Configuration for {{service}}:"
    @docker exec betterprompts-{{service}} cat /app/configs/*.yaml | head -50

# === Performance Tests ===

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

# === Development Helpers ===

# Watch logs for errors
watch-errors:
    docker compose logs -f | grep -E "error|ERROR|Error|fail|FAIL|Fail"

# Clear all logs
clear-logs:
    docker compose logs --tail=0 -f > /dev/null &
    @echo "📝 Logs cleared"

# Rebuild services
rebuild service="all":
    #!/bin/bash
    if [ "{{service}}" = "all" ]; then
        docker compose build --no-cache
    else
        docker compose build --no-cache {{service}}
    fi
    @echo "🔨 Rebuilt {{service}}"

# === Quick Tests ===

# Quick smoke test
smoke-test:
    @just health
    @echo "\n🔥 Running smoke tests..."
    @just test-selector-code > /dev/null && echo "✅ Selector works" || echo "❌ Selector failed"
    @just test-generator "test" "reasoning" "simple" > /dev/null && echo "✅ Generator works" || echo "❌ Generator failed"
    @echo "✨ Smoke test complete"

# Test with custom prompt
test prompt intent="code_generation" complexity="moderate":
    @echo "📝 Custom Test: {{prompt}}"
    @echo "\n🔍 Selector suggests:"
    @curl -s -X POST http://localhost:8002/api/v1/select \
        -H "Content-Type: application/json" \
        -d '{"text": "{{prompt}}", "intent": "{{intent}}", "complexity": "{{complexity}}"}' \
        | jq -c '[.techniques[].name]'
    @echo "\n🤖 Generator produces:"
    @curl -s -X POST http://localhost:8003/api/v1/generate \
        -H "Content-Type: application/json" \
        -d '{"text": "{{prompt}}", "intent": "{{intent}}", "complexity": "{{complexity}}"}' \
        | jq '.techniques_applied'