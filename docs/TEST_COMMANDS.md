# BetterPrompts Test Commands

Quick reference for testing the integrated Technique Selector and Prompt Generator services.

## Prerequisites

- Install [Just](https://github.com/casey/just): `brew install just` (macOS) or check [installation guide](https://github.com/casey/just#installation)
- Services running: `docker compose up -d`

## Main Test Commands

### Quick Tests

```bash
# Show all available commands
just

# Quick smoke test - checks if everything works
just smoke-test

# Test the full integration
just test-integration

# Test with a custom prompt
just test "Your prompt here" "intent" "complexity"
```

### Service Management

```bash
# Start services
just up

# Stop services
just down

# Restart a specific service
just restart technique-selector
just restart prompt-generator

# View logs
just logs technique-selector
just logs prompt-generator 100  # last 100 lines

# Check health
just health
```

### Testing Technique Selection

```bash
# Test selector with default parameters
just test-selector-code

# Test with custom parameters
just test-selector "reasoning" "complex" "Explain quantum physics"

# Test all complexity levels
just test-selector-all-complexity

# Test different intents
just test-selector "code_generation" "moderate" "Build an API"
just test-selector "reasoning" "complex" "Analyze this problem"
just test-selector "creative_writing" "simple" "Write a story"
```

### Testing Prompt Generation

```bash
# Test auto-selection (techniques chosen automatically)
just test-generator "Write a function" "code_generation" "moderate"

# Test manual technique selection
just test-generator-manual "Explain this" "analogical" "explanation" "simple"

# Test end-to-end scenarios
just test-e2e
```

## Specialized Test Scripts

### Test Different Scenarios
```bash
# Test various prompt types
just -f test-prompts.just test-code-simple
just -f test-prompts.just test-code-complex
just -f test-prompts.just test-reasoning-moderate
just -f test-prompts.just test-all-intents

# Compare auto vs manual selection
just -f test-prompts.just compare-selection "Build a web scraper"
```

### Diagnostics & Troubleshooting
```bash
# Check which techniques are available for an intent
just -f diagnostic.just check-intent "code_generation"

# Debug why a technique isn't selected
just -f diagnostic.just debug-selection "chain_of_thought" "code_generation"

# Check if services are communicating
just -f diagnostic.just check-communication

# Check technique synchronization between services
just -f diagnostic.just check-technique-sync

# Generate system report
just -f diagnostic.just system-report

# Monitor errors in real-time
just -f diagnostic.just monitor-errors
```

## Common Test Scenarios

### 1. Test Code Generation
```bash
# Simple
just test "Write a hello world function" "code_generation" "simple"

# Moderate
just test "Implement binary search" "code_generation" "moderate"

# Complex
just test "Design a microservice architecture" "code_generation" "complex"
```

### 2. Test Reasoning
```bash
just test "Why does water boil?" "reasoning" "simple"
just test "Explain machine learning" "reasoning" "moderate"
just test "Analyze climate change impacts" "reasoning" "complex"
```

### 3. Test Creative Writing
```bash
just test "Write a haiku" "creative_writing" "simple"
just test "Create a short story" "creative_writing" "moderate"
```

## Performance Testing

```bash
# Benchmark technique selector (10 requests)
just bench-selector 10

# Benchmark prompt generator (10 requests)
just bench-generator 10
```

## Understanding the Output

### Technique Selector Response
```json
{
  "techniques": [
    {"id": "few_shot", "name": "Few-Shot Learning", "score": 53},
    {"id": "structured_output", "name": "Structured Output", "score": 41}
  ],
  "primary_technique": "few_shot",
  "confidence": 0.47
}
```

### Prompt Generator Response
```json
{
  "techniques_applied": ["few_shot", "structured_output"],
  "confidence_score": 0.87,
  "generation_time_ms": 56.13
}
```

## Troubleshooting

### Services Not Responding
```bash
# Check if services are running
docker compose ps

# Check health
just health

# Restart services
just restart all
```

### Techniques Not Being Selected
```bash
# Check minimum confidence threshold
just -f diagnostic.just check-config

# Debug specific technique
just -f diagnostic.just debug-selection "technique_name" "intent"

# Check available techniques
just list-techniques
```

### Integration Not Working
```bash
# Check communication between services
just -f diagnostic.just check-communication

# Monitor logs for errors
just watch-errors

# Check technique synchronization
just -f diagnostic.just check-technique-sync
```

## Key Insights

1. **Minimum Confidence**: Set to 0.3 (30%) for techniques to be selected
2. **Auto-Selection**: If no techniques specified, Prompt Generator calls Technique Selector
3. **Fallback**: If selector fails, defaults to "zero_shot" technique
4. **Filtering**: Unknown techniques are filtered out gracefully
5. **Manual Override**: You can always specify techniques manually

## Quick Reference

| Command | Purpose |
|---------|---------|
| `just smoke-test` | Quick health check |
| `just test-integration` | Full integration test |
| `just test "prompt" "intent" "complexity"` | Custom test |
| `just health` | Service health status |
| `just logs service` | View service logs |
| `just test-e2e` | End-to-end test suite |