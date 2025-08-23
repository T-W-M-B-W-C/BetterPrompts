# Quick test recipes for common prompt scenarios
# Usage: just -f test-prompts.just <command>

# Test code generation scenarios
test-code-simple:
    @just test "Write a hello world function" "code_generation" "simple"

test-code-moderate:
    @just test "Implement binary search algorithm" "code_generation" "moderate"

test-code-complex:
    @just test "Design a distributed cache system with Redis" "code_generation" "complex"

# Test reasoning scenarios
test-reasoning-simple:
    @just test "Why is the sky blue?" "reasoning" "simple"

test-reasoning-moderate:
    @just test "Explain how neural networks learn" "reasoning" "moderate"

test-reasoning-complex:
    @just test "Analyze the implications of quantum computing on cryptography" "reasoning" "complex"

# Test different intents quickly
test-all-intents:
    @echo "🎯 Testing All Intents..."
    @echo "\n📝 Code Generation:"
    @just test "Write a sort function" "code_generation" "moderate"
    @echo "\n🧠 Reasoning:"
    @just test "Explain recursion" "reasoning" "moderate"
    @echo "\n❓ Question Answering:"
    @just test "What is Docker?" "question_answering" "simple"
    @echo "\n📊 Data Analysis:"
    @just test "Analyze sales trends" "data_analysis" "moderate"
    @echo "\n✍️ Creative Writing:"
    @just test "Write a tech haiku" "creative_writing" "simple"
    @echo "\n🗣️ Conversation:"
    @just test "Let's discuss AI ethics" "conversation" "moderate"
    @echo "\n📋 Task Planning:"
    @just test "Plan a software project" "task_planning" "complex"
    @echo "\n🔍 Problem Solving:"
    @just test "Debug a memory leak" "problem_solving" "complex"

# Batch test for performance
batch-test count="5":
    @echo "📦 Batch Testing {{count}} prompts..."
    @for i in $(seq 1 {{count}}); do \
        echo "\n--- Test $$i ---"; \
        just test "Test prompt $$i" "code_generation" "moderate"; \
    done

# Test technique combinations
test-combos:
    @echo "🔀 Testing Technique Combinations..."
    @echo "\n1. Chain of Thought + Self Consistency:"
    @curl -s -X POST http://localhost:8003/api/v1/generate \
        -H "Content-Type: application/json" \
        -d '{"text": "Solve a complex math problem", "intent": "reasoning", "complexity": "complex", "techniques": ["chain_of_thought", "self_consistency"]}' \
        | jq '{techniques_applied}'
    @echo "\n2. Few Shot + Structured Output:"
    @curl -s -X POST http://localhost:8003/api/v1/generate \
        -H "Content-Type: application/json" \
        -d '{"text": "Generate JSON data", "intent": "code_generation", "complexity": "moderate", "techniques": ["few_shot", "structured_output"]}' \
        | jq '{techniques_applied}'

# Compare manual vs auto selection
compare-selection prompt="Build a web scraper":
    @echo "🔍 Comparing Selection Methods for: {{prompt}}"
    @echo "\n🤖 Auto-Selected Techniques:"
    @curl -s -X POST http://localhost:8003/api/v1/generate \
        -H "Content-Type: application/json" \
        -d '{"text": "{{prompt}}", "intent": "code_generation", "complexity": "moderate"}' \
        | jq '{techniques: .techniques_applied, score: .confidence_score}'
    @echo "\n📝 Manual Selection (zero_shot):"
    @curl -s -X POST http://localhost:8003/api/v1/generate \
        -H "Content-Type: application/json" \
        -d '{"text": "{{prompt}}", "intent": "code_generation", "complexity": "moderate", "techniques": ["zero_shot"]}' \
        | jq '{techniques: .techniques_applied, score: .confidence_score}'
    @echo "\n📝 Manual Selection (chain_of_thought):"
    @curl -s -X POST http://localhost:8003/api/v1/generate \
        -H "Content-Type: application/json" \
        -d '{"text": "{{prompt}}", "intent": "code_generation", "complexity": "moderate", "techniques": ["chain_of_thought"]}' \
        | jq '{techniques: .techniques_applied, score: .confidence_score}'