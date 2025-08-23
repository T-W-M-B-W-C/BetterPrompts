# Service-specific Testing Commands

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

# Test specific technique scoring
debug-technique technique="chain_of_thought" text="Explain step by step":
    @echo "🔬 Debugging technique: {{technique}}"
    @curl -s -X POST http://localhost:8002/api/v1/select \
        -H "Content-Type: application/json" \
        -d '{"text": "{{text}}", "intent": "reasoning", "complexity": "moderate"}' \
        | jq '.techniques[] | select(.id == "{{technique}}")'

# List available techniques in prompt generator
list-techniques:
    @echo "📋 Available Techniques:"
    @curl -s http://localhost:8003/api/v1/techniques | jq '.techniques[].id'