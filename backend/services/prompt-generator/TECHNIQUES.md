# Prompt Engineering Techniques

This document describes all implemented prompt engineering techniques in the BetterPrompts system.

## Overview

The prompt-generator service implements 12 advanced prompt engineering techniques, including two newly added techniques: Self-Consistency and ReAct. Each technique is designed to enhance prompts for specific use cases and can be applied individually or in combination.

## Implemented Techniques

### 1. Chain of Thought (CoT) - Enhanced
- **Purpose**: Encourages step-by-step reasoning with adaptive intelligence
- **Best for**: Mathematical problems, logical reasoning, complex analysis, debugging, algorithmic design
- **Example**: "Let's think through this step-by-step..." (adapts to complexity)
- **Key Features**:
  - **Domain-Aware**: Automatically detects and applies domain-specific reasoning (math, algorithms, debugging, analysis, logic)
  - **Adaptive Complexity**: Adjusts reasoning depth based on problem complexity (3-7 steps)
  - **Enhanced Mode**: Dynamic reasoning patterns with quality metrics
  - **Backward Compatible**: Supports custom reasoning steps via context
  - **Quality Metrics**: Built-in evaluation of reasoning quality (coverage, depth, coherence, completeness)

### 2. Tree of Thoughts (ToT)
- **Purpose**: Explores multiple solution paths before selecting the best one
- **Best for**: Creative problems, design decisions, optimization tasks
- **Example**: "Let's explore different approaches..."
- **Key Features**:
  - Evaluates multiple approaches (default: 3)
  - Compares pros and cons of each approach
  - Supports custom approach definitions

### 3. Few-shot Learning
- **Purpose**: Provides examples to demonstrate the desired output format
- **Best for**: Classification, translation, format conversion
- **Example**: Shows input-output pairs before the actual task
- **Key Features**:
  - Default examples for common tasks
  - Supports custom examples via context
  - Automatically formats examples consistently

### 4. Zero-shot Learning
- **Purpose**: Provides clear instructions without examples
- **Best for**: Simple tasks, when examples aren't available
- **Example**: "Task: [clear description]. Instructions: [specific steps]"
- **Key Features**:
  - Structured task definition
  - Clear instruction formatting
  - Constraint specification support

### 5. Role Play
- **Purpose**: Assigns a specific role or persona to guide responses
- **Best for**: Expert advice, creative writing, specialized knowledge
- **Example**: "As a [role], ..."
- **Key Features**:
  - Flexible role assignment
  - Supports expertise and personality traits
  - Context-aware role selection

### 6. Step by Step
- **Purpose**: Breaks down complex tasks into manageable steps
- **Best for**: Tutorials, procedures, complex implementations
- **Example**: "Step 1: ... Step 2: ..."
- **Key Features**:
  - Automatic step extraction from context
  - Supports verification steps
  - Clear numbered formatting

### 7. Structured Output
- **Purpose**: Enforces specific output formats
- **Best for**: Data extraction, API responses, reports
- **Example**: Specifies JSON, Markdown, or custom formats
- **Key Features**:
  - Multiple format support (JSON, XML, Markdown, etc.)
  - Schema definition capability
  - Format validation

### 8. Emotional Appeal
- **Purpose**: Adds emotional context to improve engagement
- **Best for**: Creative writing, persuasion, motivation
- **Example**: Adds enthusiasm or empathy to prompts
- **Key Features**:
  - Tone adjustment (enthusiastic, empathetic, urgent)
  - Context-appropriate emotion selection
  - Maintains professionalism

### 9. Constraints
- **Purpose**: Sets specific limitations or requirements
- **Best for**: Precise outputs, resource limits, specific criteria
- **Example**: "Within 100 words...", "Using only..."
- **Key Features**:
  - Multiple constraint types (length, format, content)
  - Clear constraint specification
  - Validation support

### 10. Analogical Reasoning
- **Purpose**: Uses analogies to explain complex concepts
- **Best for**: Education, explanation, concept clarification
- **Example**: "Think of it like..."
- **Key Features**:
  - Domain-appropriate analogy selection
  - Custom analogy support
  - Complexity-based analogy matching

### 11. Self-Consistency (NEW)
- **Purpose**: Generates multiple reasoning paths and selects the most consistent answer
- **Best for**: Complex reasoning, mathematical problems, decision-making
- **Example**: "Approach 1: ... Approach 2: ... Consistency Analysis: ..."
- **Key Features**:
  - Multiple reasoning paths (3-5)
  - Task-specific reasoning variations
  - Confidence level assessment
  - Consistency analysis across approaches
  - Supports math, logic, coding, and analysis tasks

### 12. ReAct - Reasoning + Acting (NEW)
- **Purpose**: Interleaves thinking and action for complex multi-step tasks
- **Best for**: Implementation tasks, debugging, research, problem-solving
- **Example**: "Thought 1: ... Action 1: ... Observation 1: ..."
- **Key Features**:
  - Structured thought-action-observation cycles
  - Support for external tool integration
  - Task-specific action sequences
  - Iterative refinement capability
  - Reflection and learning components

## Technique Selection Guidelines

### By Task Type

**Mathematical/Logical Problems**:
- Primary: Self-Consistency, Chain of Thought
- Secondary: Tree of Thoughts, Step by Step

**Implementation/Development**:
- Primary: ReAct, Step by Step
- Secondary: Structured Output, Constraints

**Creative Tasks**:
- Primary: Tree of Thoughts, Role Play
- Secondary: Emotional Appeal, Analogical

**Analysis/Research**:
- Primary: ReAct, Chain of Thought
- Secondary: Self-Consistency, Tree of Thoughts

**Learning/Explanation**:
- Primary: Few-shot, Analogical
- Secondary: Step by Step, Chain of Thought

## Technique Combinations

Techniques can be combined for enhanced effectiveness:

1. **Chain of Thought + Self-Consistency**: For complex reasoning with high reliability
2. **ReAct + Structured Output**: For systematic tasks with specific output requirements
3. **Few-shot + Constraints**: For format learning with specific limitations
4. **Role Play + Emotional Appeal**: For engaging, persona-driven responses

## Configuration

Each technique supports configuration through:
- **Priority**: Determines application order when multiple techniques are used
- **Enabled**: Toggle technique availability
- **Parameters**: Technique-specific settings
- **Template**: Custom prompt templates

## Usage Example

```python
# Single technique
request = PromptGenerationRequest(
    text="Solve this optimization problem",
    intent="problem_solving",
    complexity=0.8,
    techniques=["self_consistency"],
    context={
        "num_paths": 4,
        "task_type": "math",
        "show_confidence": True
    }
)

# Multiple techniques
request = PromptGenerationRequest(
    text="Build a REST API",
    intent="implementation",
    complexity=0.7,
    techniques=["react", "structured_output"],
    context={
        "available_tools": ["IDE", "debugger", "docs"],
        "output_format": "markdown"
    }
)
```

## Best Practices

1. **Match technique to task type**: Use the selection guidelines above
2. **Consider complexity**: More complex tasks benefit from advanced techniques
3. **Combine thoughtfully**: Not all techniques work well together
4. **Test effectiveness**: Monitor which techniques work best for your use cases
5. **Customize parameters**: Adjust technique parameters based on results

## Recent Enhancements

The Chain of Thought technique has been significantly enhanced with:
- Automatic domain detection (mathematical, algorithmic, debugging, analytical, logical)
- Adaptive complexity handling with dynamic step generation
- Built-in quality metrics for reasoning evaluation
- Backward compatibility with basic mode

## Future Enhancements

Additional improvements planned for the system:
- Dynamic technique selection based on ML analysis
- Technique effectiveness learning and adaptation
- Enhanced versions of other techniques (similar to CoT enhancement)
- Cross-technique optimization and intelligent combination
- Custom technique creation framework
- Real-time effectiveness monitoring and adjustment