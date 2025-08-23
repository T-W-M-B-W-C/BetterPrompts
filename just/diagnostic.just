# Diagnostic commands for troubleshooting the system
# Usage: just -f diagnostic.just <command>

# Check which techniques are available for an intent
check-intent intent="code_generation":
    @echo "🔍 Checking techniques for intent: {{intent}}"
    @for complexity in simple moderate complex; do \
        echo "\n📊 Complexity: $$complexity"; \
        curl -s -X POST http://localhost:8002/api/v1/select \
            -H "Content-Type: application/json" \
            -d "{\"text\": \"test\", \"intent\": \"{{intent}}\", \"complexity\": \"$$complexity\"}" \
            | jq -c '{count: .metadata.techniques_evaluated, selected: [.techniques[].name], confidence}'; \
    done

# Debug why a technique isn't being selected
debug-selection technique="chain_of_thought" intent="code_generation":
    @echo "🐛 Debugging {{technique}} for {{intent}}..."
    @curl -s -X POST http://localhost:8002/api/v1/select \
        -H "Content-Type: application/json" \
        -d '{"text": "test prompt with keywords", "intent": "{{intent}}", "complexity": "moderate"}' \
        | jq '.techniques[] | select(.id == "{{technique}}") // {message: "Technique not selected"}'

# Show what the selector evaluates
show-evaluation intent="code_generation" text="Write a function":
    @echo "📋 Evaluation Details:"
    @curl -s -X POST http://localhost:8002/api/v1/select \
        -H "Content-Type: application/json" \
        -d '{"text": "{{text}}", "intent": "{{intent}}", "complexity": "moderate"}' \
        | jq '{metadata, reasoning, techniques: [.techniques[] | {name, score, confidence, reasoning}]}'

# Check if services are communicating
check-communication:
    @echo "🔗 Checking Service Communication..."
    @echo "\n1. Selector standalone:"
    @curl -s -X POST http://localhost:8002/api/v1/select \
        -H "Content-Type: application/json" \
        -d '{"text": "test", "intent": "code_generation", "complexity": "moderate"}' \
        | jq -c '{status: "ok", techniques: [.techniques[].id]}' || echo '{"status": "failed"}'
    @echo "\n2. Generator calling selector:"
    @curl -s -X POST http://localhost:8003/api/v1/generate \
        -H "Content-Type: application/json" \
        -d '{"text": "test", "intent": "code_generation", "complexity": "moderate"}' \
        | jq -c '{status: "ok", auto_selected: .techniques_applied}' || echo '{"status": "failed"}'

# Monitor service logs for errors
monitor-errors:
    @echo "🚨 Monitoring for errors (Ctrl+C to stop)..."
    @docker compose logs -f --tail=0 | grep -E "error|ERROR|fail|FAIL|warning|WARNING"

# Show current configuration
show-rules:
    @echo "📜 Current Technique Rules (first 100 lines):"
    @docker exec betterprompts-technique-selector cat /app/configs/rules.yaml | head -100

# Test if techniques exist in both services
check-technique-sync:
    @echo "🔄 Checking Technique Synchronization..."
    @echo "\n📦 Selector techniques:"
    @docker exec betterprompts-technique-selector cat /app/configs/rules.yaml | grep "^  - id:" | cut -d'"' -f2
    @echo "\n📦 Generator supported techniques:"
    @curl -s http://localhost:8003/api/v1/techniques | jq -r '.techniques[].id'

# Quick system report
system-report:
    @echo "📊 System Report"
    @echo "================"
    @echo "\n🏥 Health Status:"
    @just health
    @echo "\n📈 Technique Selection Stats:"
    @just check-intent "code_generation"
    @echo "\n🔗 Communication Check:"
    @just check-communication
    @echo "\n✅ Report Complete"

# Check for configuration issues
check-config:
    @echo "⚙️ Configuration Check..."
    @echo "\n1. Min confidence threshold:"
    @docker exec betterprompts-technique-selector cat /app/configs/rules.yaml | grep "min_confidence:"
    @echo "\n2. Max techniques:"
    @docker exec betterprompts-technique-selector cat /app/configs/rules.yaml | grep "max_techniques:"
    @echo "\n3. Techniques with code_generation intent:"
    @docker exec betterprompts-technique-selector cat /app/configs/rules.yaml | grep -B5 "code_generation" | grep "id:" | head -5