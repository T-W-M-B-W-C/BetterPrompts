"""
Self-Consistency Prompt Engineering Technique.

This technique generates multiple reasoning paths for the same problem
and selects the most consistent answer through majority voting.
It improves reliability by leveraging the wisdom of crowds principle.
"""

import re
from typing import Dict, Any, Optional, List
from .base import BaseTechnique


class SelfConsistencyTechnique(BaseTechnique):
    """
    Self-Consistency technique implementation.
    
    Generates multiple diverse reasoning paths and selects the most
    consistent answer through aggregation, improving reliability and
    reducing errors in complex reasoning tasks.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Self-Consistency technique."""
        super().__init__(config)
        
        # Default template for self-consistency prompting
        self.default_template = """{{ original_prompt }}

To ensure accuracy and reliability, I'll approach this problem from {{ num_paths }} different perspectives:

{% for i in range(num_paths) %}
**Approach {{ i + 1 }}{{ approach_descriptions[i] }}:**
Let me {{ reasoning_variations[i] }} to solve this problem.
[Provide detailed reasoning and arrive at an answer]

{% endfor %}

**Consistency Analysis:**
Now I'll analyze all {{ num_paths }} approaches to identify the most consistent and reliable answer:
- Compare the conclusions from each approach
- Identify common patterns and agreements
- Note any discrepancies and evaluate their significance
- Select the answer that appears most frequently or has the strongest support

**Final Answer:**
Based on the consistency analysis across all approaches, the most reliable answer is:
[Provide the final answer with confidence level]

{% if show_confidence %}
**Confidence Level:** [High/Medium/Low] based on the agreement between approaches
{% endif %}"""
        
        # Use provided template or default
        if not self.template:
            self.template = self.default_template
            
        # Default reasoning variations for diversity
        self.reasoning_variations = [
            "think step-by-step",
            "work backwards from the goal",
            "use analogical reasoning",
            "apply first principles",
            "consider edge cases first"
        ]
        
        # Approach descriptions for clarity
        self.approach_descriptions = [
            " (Systematic Analysis)",
            " (Reverse Engineering)",
            " (Pattern Matching)",
            " (Fundamental Principles)",
            " (Boundary Testing)"
        ]
    
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Apply the Self-Consistency technique to the input text.
        
        Args:
            text: The original prompt or question
            context: Additional context including:
                - num_paths: Number of reasoning paths (default: 3)
                - reasoning_variations: Custom reasoning approaches
                - show_confidence: Whether to show confidence level
                - task_type: Type of task for optimization
        
        Returns:
            Enhanced prompt with self-consistency structure
        """
        try:
            # Clean the input text
            clean_text = self.clean_text(text)
            
            # Extract parameters from context
            context = context or {}
            num_paths = min(context.get('num_paths', 3), 5)  # Cap at 5 for token efficiency
            show_confidence = context.get('show_confidence', True)
            task_type = context.get('task_type', 'general')
            
            # Use custom reasoning variations if provided
            custom_variations = context.get('reasoning_variations')
            if custom_variations and isinstance(custom_variations, list):
                reasoning_variations = custom_variations[:num_paths]
            else:
                reasoning_variations = self._get_reasoning_variations(task_type, num_paths)
            
            # Get approach descriptions
            approach_descriptions = self._get_approach_descriptions(reasoning_variations)
            
            # Prepare template variables
            template_vars = {
                'original_prompt': clean_text,
                'num_paths': num_paths,
                'reasoning_variations': reasoning_variations,
                'approach_descriptions': approach_descriptions,
                'show_confidence': show_confidence
            }
            
            # Render the template
            enhanced_prompt = self.render_template(self.template, template_vars)
            
            self.logger.debug(
                f"Applied Self-Consistency with {num_paths} paths for task type: {task_type}"
            )
            
            return enhanced_prompt
            
        except Exception as e:
            self.logger.error(f"Error applying Self-Consistency technique: {str(e)}")
            return text
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate if the input is suitable for Self-Consistency technique.
        
        Best suited for:
        - Complex reasoning problems
        - Mathematical problems
        - Logic puzzles
        - Decision-making scenarios
        - Problems with multiple valid approaches
        
        Args:
            text: The input text to validate
            context: Additional context
        
        Returns:
            True if suitable for self-consistency, False otherwise
        """
        if not text or len(text.strip()) < 20:
            self.logger.debug("Text too short for Self-Consistency technique")
            return False
        
        # Keywords indicating suitability for self-consistency
        reasoning_keywords = [
            'solve', 'calculate', 'determine', 'analyze', 'evaluate',
            'decide', 'figure out', 'work out', 'find', 'prove',
            'deduce', 'infer', 'conclude', 'reason', 'think'
        ]
        
        uncertainty_keywords = [
            'best', 'optimal', 'correct', 'right', 'accurate',
            'reliable', 'certain', 'sure', 'confident'
        ]
        
        complexity_indicators = [
            'complex', 'difficult', 'challenging', 'tricky',
            'multiple', 'various', 'different ways'
        ]
        
        text_lower = text.lower()
        
        # Check for reasoning-related keywords
        has_reasoning = any(keyword in text_lower for keyword in reasoning_keywords)
        has_uncertainty = any(keyword in text_lower for keyword in uncertainty_keywords)
        has_complexity = any(keyword in text_lower for keyword in complexity_indicators)
        
        # Self-consistency is valuable when there's reasoning involved
        # and either uncertainty or complexity
        if has_reasoning and (has_uncertainty or has_complexity):
            self.logger.debug("Input suitable for Self-Consistency: reasoning with uncertainty/complexity")
            return True
        
        # Check context for explicit task types
        if context:
            task_type = context.get('task_type', '').lower()
            suitable_types = ['math', 'logic', 'reasoning', 'analysis', 'problem-solving']
            if any(t in task_type for t in suitable_types):
                self.logger.debug(f"Input suitable for Self-Consistency: task type {task_type}")
                return True
        
        # For questions that benefit from multiple perspectives
        if text.strip().endswith('?') and len(text.split()) > 10:
            self.logger.debug("Input suitable for Self-Consistency: complex question")
            return True
        
        self.logger.debug("Input not ideal for Self-Consistency technique")
        return False
    
    def _get_reasoning_variations(self, task_type: str, num_paths: int) -> List[str]:
        """Get task-specific reasoning variations."""
        task_variations = {
            'math': [
                "solve algebraically",
                "use geometric interpretation",
                "apply numerical methods",
                "work with specific examples",
                "use mathematical induction"
            ],
            'logic': [
                "use formal logic",
                "apply truth tables",
                "work through contradictions",
                "use Venn diagrams",
                "apply syllogistic reasoning"
            ],
            'coding': [
                "trace through the algorithm",
                "analyze time complexity",
                "consider edge cases",
                "use debugging techniques",
                "apply design patterns"
            ],
            'analysis': [
                "examine from multiple stakeholder perspectives",
                "use SWOT analysis",
                "apply root cause analysis",
                "consider historical precedents",
                "use systems thinking"
            ],
            'general': self.reasoning_variations
        }
        
        variations = task_variations.get(task_type, task_variations['general'])
        return variations[:num_paths]
    
    def _get_approach_descriptions(self, reasoning_variations: List[str]) -> List[str]:
        """Generate descriptions for each reasoning approach."""
        description_map = {
            "think step-by-step": " (Systematic Analysis)",
            "work backwards from the goal": " (Reverse Engineering)",
            "use analogical reasoning": " (Pattern Matching)",
            "apply first principles": " (Fundamental Principles)",
            "consider edge cases first": " (Boundary Testing)",
            "solve algebraically": " (Algebraic Method)",
            "use geometric interpretation": " (Geometric Approach)",
            "apply numerical methods": " (Numerical Analysis)",
            "use formal logic": " (Formal Logic)",
            "apply truth tables": " (Truth Table Method)",
            "trace through the algorithm": " (Algorithm Tracing)",
            "analyze time complexity": " (Complexity Analysis)",
            "examine from multiple stakeholder perspectives": " (Stakeholder Analysis)",
            "use SWOT analysis": " (SWOT Framework)",
            "apply root cause analysis": " (Root Cause Analysis)"
        }
        
        descriptions = []
        for variation in reasoning_variations:
            desc = description_map.get(variation, " (Alternative Method)")
            descriptions.append(desc)
        
        return descriptions