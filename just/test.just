# Testing Commands

# Test authentication API
test-auth:
    @echo "Testing authentication API..."
    @/usr/bin/python3 -m pip install --user -q pytest requests 2>/dev/null || true
    @/usr/bin/python3 -m pytest tests/test_auth_api.py tests/test_auth_flow.py -v --tb=short

# Quick auth test
test-auth-quick:
    @pip install -q pytest requests
    @python -m pytest tests/test_auth_api.py::TestAuth::test_login -v

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