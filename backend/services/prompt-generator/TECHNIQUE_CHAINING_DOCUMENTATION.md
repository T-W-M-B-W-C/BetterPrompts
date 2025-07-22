# Technique Chaining Implementation

## Overview

The technique chaining system enables multiple prompt engineering techniques to work together in sequence, with each technique able to see and build upon the work of previous techniques. This creates a compound intelligence effect where techniques can coordinate and enhance each other's contributions.

## Architecture

### Core Components

1. **ChainContext**: A state management class that tracks the entire chain execution
2. **Enhanced Engine**: Modified prompt generation engine with chaining support
3. **Context Passing**: Mechanism for techniques to share information
4. **Metadata Tracking**: Comprehensive tracking of each technique's contribution

### How It Works

```python
# Chain execution flow
1. Initialize ChainContext with base context
2. For each technique in the chain:
   a. Get enhanced context (base + accumulated + chain info)
   b. Apply technique with enhanced context
   c. Extract metadata and context updates
   d. Record technique application
   e. Pass enhanced text to next technique
3. Return final result with complete chain metadata
```

## ChainContext Class

The `ChainContext` dataclass manages the state throughout the chain execution:

```python
@dataclass
class ChainContext:
    # Core state
    base_context: Dict[str, Any]          # Initial context
    original_text: str                    # Original input
    current_text: str                     # Current enhanced text
    
    # Chain tracking
    applied_techniques: List[str]         # Techniques applied in order
    technique_outputs: Dict[str, str]     # Output from each technique
    technique_metadata: Dict[str, Dict]   # Metadata from each technique
    
    # Context accumulation
    accumulated_context: Dict[str, Any]   # Context built up through chain
    
    # Error handling
    errors: List[Dict[str, Any]]         # Errors encountered
    warnings: List[str]                  # Warning messages
    
    # Performance
    technique_timings: Dict[str, float]  # Execution time per technique
```

## Context Passing Mechanism

### 1. Base Context
Every technique receives the original context including:
- Intent
- Complexity
- Target model
- User-provided parameters

### 2. Chain Information
Each technique also receives:
```python
"chain_info": {
    "previous_techniques": ["chain_of_thought", "few_shot"],
    "technique_outputs": {
        "chain_of_thought": "enhanced text from CoT...",
        "few_shot": "enhanced text from few-shot..."
    },
    "current_position": 3,
    "original_text": "original user prompt"
}
```

### 3. Accumulated Context
Techniques can contribute to accumulated context via `extract_context_updates()`:
```python
def extract_context_updates(self, text: str, result: str, context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "cot_domain": "mathematical",
        "cot_reasoning_structure": ["step1", "step2", "step3"],
        "cot_detected_complexity": "complex"
    }
```

## Implementing Chain-Aware Techniques

To make a technique chain-aware, implement these optional methods:

### 1. Metadata Provider
```python
def get_application_metadata(self) -> Dict[str, Any]:
    """Return metadata about the technique application"""
    return {
        "domain": self._detected_domain,
        "complexity": self._complexity,
        "custom_data": self._custom_data
    }
```

### 2. Context Extractor
```python
def extract_context_updates(self, text: str, result: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Extract context to pass to subsequent techniques"""
    return {
        "technique_insights": "value",
        "detected_patterns": ["pattern1", "pattern2"]
    }
```

### 3. Chain-Aware Processing
```python
def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
    # Check for chain information
    if context and "chain_info" in context:
        previous_techniques = context["chain_info"]["previous_techniques"]
        if "chain_of_thought" in previous_techniques:
            # Adapt based on previous CoT application
            ...
    
    # Check accumulated context
    if context.get("cot_domain") == "mathematical":
        # Use mathematical examples
        ...
```

## Example: Chain of Thought → Few-Shot → Step-by-Step

### Input
```json
{
    "text": "Create a machine learning pipeline for sentiment analysis",
    "techniques": ["chain_of_thought", "few_shot", "step_by_step"],
    "intent": "code_generation",
    "complexity": "complex"
}
```

### Chain Execution

1. **Chain of Thought**
   - Detects: algorithmic domain, complex task
   - Adds reasoning structure
   - Updates context: `{"cot_domain": "algorithmic", "cot_reasoning_structure": [...]}`

2. **Few-Shot**
   - Sees: algorithmic domain from CoT
   - Selects: ML-specific examples
   - Adds: relevant code examples

3. **Step-by-Step**
   - Sees: complexity and domain from previous techniques
   - Creates: detailed implementation steps
   - Includes: sub-steps for complex parts

### Output Metadata
```json
{
    "chain_summary": {
        "techniques_applied": ["chain_of_thought", "few_shot", "step_by_step"],
        "total_techniques": 3,
        "errors": 0,
        "warnings": 0,
        "total_time_ms": 45.3,
        "technique_timings": {
            "chain_of_thought": 15.2,
            "few_shot": 18.1,
            "step_by_step": 12.0
        },
        "accumulated_context": ["cot_domain", "cot_reasoning_structure", "few_shot_examples"]
    }
}
```

## Benefits of Technique Chaining

1. **Compound Intelligence**: Techniques build on each other's insights
2. **Context Preservation**: Information flows through the entire chain
3. **Error Recovery**: Chain continues even if one technique fails
4. **Performance Tracking**: Detailed metrics for optimization
5. **Debugging Support**: Full transparency of the enhancement process
6. **Flexible Orchestration**: Easy to add/remove/reorder techniques

## Best Practices

### 1. Technique Ordering
- Place analysis techniques (CoT) early in the chain
- Follow with enhancement techniques (Few-Shot)
- End with structural techniques (Step-by-Step)

### 2. Context Design
- Use namespaced keys (e.g., `cot_domain`, `few_shot_examples`)
- Keep context updates focused and relevant
- Don't overwhelm subsequent techniques with data

### 3. Error Handling
- Always handle missing context gracefully
- Provide meaningful fallbacks
- Log warnings but don't fail the chain

### 4. Performance
- Keep context updates lightweight
- Avoid expensive computations in context extraction
- Use caching where appropriate

## Testing Technique Chains

Use the provided test script:
```bash
./scripts/test-technique-chaining.sh
```

This tests:
- Multiple technique combinations
- Context passing between techniques
- Error recovery
- Performance tracking
- Metadata collection

## Future Enhancements

1. **Conditional Chaining**: Techniques that decide which technique runs next
2. **Parallel Chains**: Run independent techniques in parallel
3. **Chain Templates**: Pre-defined chains for common use cases
4. **Learning**: Optimize chain order based on effectiveness
5. **Visualization**: Tools to visualize chain execution