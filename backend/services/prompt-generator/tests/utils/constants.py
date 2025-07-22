"""Test constants for prompt-generator tests."""

from enum import Enum
from typing import Dict, List, Any


class TechniqueType(str, Enum):
    """Prompt engineering techniques."""
    CHAIN_OF_THOUGHT = "chain_of_thought"
    FEW_SHOT = "few_shot"
    ZERO_SHOT = "zero_shot"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    SELF_CONSISTENCY = "self_consistency"
    STEP_BY_STEP = "step_by_step"
    ROLE_PLAY = "role_play"
    EMOTIONAL_APPEAL = "emotional_appeal"
    STRUCTURED_OUTPUT = "structured_output"
    ANALOGICAL = "analogical"
    REACT = "react"


class ModelProvider(str, Enum):
    """LLM model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class IntentType(str, Enum):
    """Intent types that influence prompt generation."""
    EXPLAIN_CONCEPT = "explain_concept"
    GENERATE_CODE = "generate_code"
    DEBUG_ERROR = "debug_error"
    ANALYZE_DATA = "analyze_data"
    CREATE_CONTENT = "create_content"
    ANSWER_QUESTION = "answer_question"
    SUMMARIZE_TEXT = "summarize_text"
    TRANSLATE_TEXT = "translate_text"


# Technique compatibility matrix
TECHNIQUE_COMPATIBILITY: Dict[str, List[str]] = {
    IntentType.EXPLAIN_CONCEPT: [
        TechniqueType.ANALOGICAL,
        TechniqueType.STEP_BY_STEP,
        TechniqueType.CHAIN_OF_THOUGHT,
        TechniqueType.FEW_SHOT
    ],
    IntentType.GENERATE_CODE: [
        TechniqueType.FEW_SHOT,
        TechniqueType.STEP_BY_STEP,
        TechniqueType.STRUCTURED_OUTPUT,
        TechniqueType.CHAIN_OF_THOUGHT
    ],
    IntentType.DEBUG_ERROR: [
        TechniqueType.CHAIN_OF_THOUGHT,
        TechniqueType.STEP_BY_STEP,
        TechniqueType.TREE_OF_THOUGHTS,
        TechniqueType.REACT
    ],
    IntentType.ANALYZE_DATA: [
        TechniqueType.CHAIN_OF_THOUGHT,
        TechniqueType.TREE_OF_THOUGHTS,
        TechniqueType.STRUCTURED_OUTPUT,
        TechniqueType.STEP_BY_STEP
    ],
    IntentType.CREATE_CONTENT: [
        TechniqueType.ROLE_PLAY,
        TechniqueType.EMOTIONAL_APPEAL,
        TechniqueType.FEW_SHOT,
        TechniqueType.ANALOGICAL
    ],
    IntentType.ANSWER_QUESTION: [
        TechniqueType.ZERO_SHOT,
        TechniqueType.CHAIN_OF_THOUGHT,
        TechniqueType.SELF_CONSISTENCY,
        TechniqueType.FEW_SHOT
    ]
}


# Technique templates
TECHNIQUE_TEMPLATES: Dict[str, str] = {
    TechniqueType.CHAIN_OF_THOUGHT: """Let me think through this step by step:

1. First, I need to understand {problem_aspect}
2. Next, I'll consider {key_factors}
3. Then, I'll analyze {relationships}
4. Finally, I'll {conclusion_action}

{original_prompt}""",
    
    TechniqueType.FEW_SHOT: """Here are some examples to guide the response:

Example 1:
Input: {example1_input}
Output: {example1_output}

Example 2:
Input: {example2_input}
Output: {example2_output}

Now, for your request:
{original_prompt}""",
    
    TechniqueType.TREE_OF_THOUGHTS: """I'll explore multiple approaches to this problem:

Approach 1: {approach1_description}
- Pros: {approach1_pros}
- Cons: {approach1_cons}

Approach 2: {approach2_description}
- Pros: {approach2_pros}
- Cons: {approach2_cons}

Approach 3: {approach3_description}
- Pros: {approach3_pros}
- Cons: {approach3_cons}

Evaluating these approaches for: {original_prompt}""",
    
    TechniqueType.STEP_BY_STEP: """I'll break this down into clear steps:

Step 1: {step1_description}
Step 2: {step2_description}
Step 3: {step3_description}
Step 4: {step4_description}

Let's apply these steps to: {original_prompt}""",
    
    TechniqueType.ROLE_PLAY: """As {role_description} with expertise in {domain}, I'll address your request:

{original_prompt}

From my professional perspective, here's my response:""",
    
    TechniqueType.STRUCTURED_OUTPUT: """I'll provide a structured response in the following format:

### Overview
{overview_section}

### Key Points
1. {point1}
2. {point2}
3. {point3}

### Details
{details_section}

### Summary
{summary_section}

Addressing: {original_prompt}"""
}


# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "generation_time_ms": 500,
    "enhancement_time_ms": 300,
    "batch_generation_time_ms": 3000,
    "min_token_efficiency": 0.7,  # Enhanced prompt shouldn't be >1.3x original
    "max_token_expansion": 2.0,   # Enhanced prompt shouldn't be >2x original
    "cache_hit_time_ms": 20
}


# Error messages
ERROR_MESSAGES = {
    "missing_prompt": "Original prompt is required",
    "empty_prompt": "Prompt cannot be empty",
    "invalid_intent": "Invalid intent type provided",
    "invalid_technique": "Invalid technique specified",
    "incompatible_technique": "Technique not compatible with intent",
    "generation_failed": "Failed to generate enhanced prompt",
    "llm_error": "LLM API error occurred",
    "token_limit_exceeded": "Token limit exceeded",
    "invalid_context": "Invalid context format"
}


# Mock LLM responses
MOCK_LLM_RESPONSES = {
    "chain_of_thought": """Let me think through this step by step:

1. First, I need to understand the core requirement
2. Next, I'll consider the key factors involved
3. Then, I'll analyze the relationships between components
4. Finally, I'll provide a comprehensive solution

Based on this analysis, here's my response to your request...""",
    
    "few_shot": """Here are some examples to guide the response:

Example 1:
Input: Calculate 2+2
Output: 4

Example 2:
Input: Calculate 5*3
Output: 15

Now, applying this pattern to your request...""",
    
    "generic": "This is a generic enhanced response incorporating the requested techniques."
}


# Test prompts by intent
TEST_PROMPTS_BY_INTENT = {
    IntentType.GENERATE_CODE: [
        "Write a Python function to sort a list",
        "Create a React component for a button",
        "Implement a binary search algorithm"
    ],
    IntentType.EXPLAIN_CONCEPT: [
        "Explain how neural networks work",
        "What is recursion in programming?",
        "Describe the concept of blockchain"
    ],
    IntentType.DEBUG_ERROR: [
        "Fix this TypeError in my Python code",
        "Why is my React component re-rendering infinitely?",
        "Debug this null pointer exception"
    ],
    IntentType.ANALYZE_DATA: [
        "Analyze this sales data for trends",
        "What patterns do you see in this dataset?",
        "Perform statistical analysis on these numbers"
    ],
    IntentType.CREATE_CONTENT: [
        "Write a blog post about AI",
        "Create a story about a robot",
        "Generate marketing copy for a product"
    ],
    IntentType.ANSWER_QUESTION: [
        "What is the capital of France?",
        "How does photosynthesis work?",
        "When was the internet invented?"
    ]
}


# Technique effectiveness scores (for testing)
TECHNIQUE_EFFECTIVENESS = {
    TechniqueType.CHAIN_OF_THOUGHT: {
        IntentType.EXPLAIN_CONCEPT: 0.9,
        IntentType.DEBUG_ERROR: 0.95,
        IntentType.ANALYZE_DATA: 0.9,
        IntentType.ANSWER_QUESTION: 0.8
    },
    TechniqueType.FEW_SHOT: {
        IntentType.GENERATE_CODE: 0.95,
        IntentType.CREATE_CONTENT: 0.85,
        IntentType.ANSWER_QUESTION: 0.8
    },
    TechniqueType.TREE_OF_THOUGHTS: {
        IntentType.DEBUG_ERROR: 0.9,
        IntentType.ANALYZE_DATA: 0.95
    },
    TechniqueType.STEP_BY_STEP: {
        IntentType.EXPLAIN_CONCEPT: 0.85,
        IntentType.GENERATE_CODE: 0.9,
        IntentType.DEBUG_ERROR: 0.85
    },
    TechniqueType.ROLE_PLAY: {
        IntentType.CREATE_CONTENT: 0.9,
        IntentType.EXPLAIN_CONCEPT: 0.8
    },
    TechniqueType.STRUCTURED_OUTPUT: {
        IntentType.GENERATE_CODE: 0.85,
        IntentType.ANALYZE_DATA: 0.9
    }
}


# Model configuration
MODEL_CONFIGS = {
    ModelProvider.OPENAI: {
        "models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
        "max_tokens": 4096,
        "temperature_range": (0.0, 2.0),
        "default_temperature": 0.7
    },
    ModelProvider.ANTHROPIC: {
        "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "max_tokens": 4096,
        "temperature_range": (0.0, 1.0),
        "default_temperature": 0.7
    }
}


# Cache configuration
CACHE_CONFIG = {
    "ttl_seconds": 3600,
    "max_entries": 10000,
    "key_prefix": "prompt:v1:",
    "compression_enabled": True
}


# Batch processing limits
BATCH_LIMITS = {
    "max_batch_size": 50,
    "max_tokens_per_batch": 10000,
    "timeout_seconds": 60
}