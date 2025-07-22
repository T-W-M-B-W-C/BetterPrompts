"""
Chain of Thought (CoT) Prompt Engineering Technique.

This implementation provides both basic and enhanced CoT capabilities:
- Basic mode: Simple step-by-step reasoning (backward compatible)
- Enhanced mode: Dynamic reasoning patterns, domain awareness, adaptive complexity
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from .base import BaseTechnique
from ..utils import complexity_string_to_float, complexity_float_to_string


class ChainOfThoughtTechnique(BaseTechnique):
    """
    Chain of Thought (CoT) prompting technique with enhanced capabilities.
    
    This technique encourages step-by-step reasoning by explicitly
    asking the model to show its thinking process. Supports both
    basic and advanced modes.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Basic template for backward compatibility
        self.default_template = """{{ text }}

Let's approach this step-by-step:

1. First, let me understand what is being asked...
2. Next, I'll identify the key components...
3. Then, I'll analyze each part...
4. Finally, I'll synthesize the solution...

Please show your reasoning at each step."""
        
        if not self.template:
            self.template = self.default_template
        
        # Enhanced mode configurations
        self.enhanced_mode = config.get('enhanced_mode', True)
        
        # Domain-specific reasoning patterns for enhanced mode
        self.reasoning_patterns = {
            "mathematical": {
                "steps": [
                    "Identify given information and unknowns",
                    "Determine applicable formulas or theorems",
                    "Set up the problem structure",
                    "Perform calculations step by step",
                    "Verify the solution"
                ],
                "depth_multiplier": 1.5
            },
            "algorithmic": {
                "steps": [
                    "Understand the problem requirements",
                    "Identify input/output specifications",
                    "Consider edge cases and constraints",
                    "Design the algorithm approach",
                    "Analyze time and space complexity"
                ],
                "depth_multiplier": 2.0
            },
            "analytical": {
                "steps": [
                    "Define the scope and objectives",
                    "Gather relevant information",
                    "Identify patterns and relationships",
                    "Evaluate different perspectives",
                    "Draw conclusions based on evidence"
                ],
                "depth_multiplier": 1.3
            },
            "debugging": {
                "steps": [
                    "Reproduce and understand the issue",
                    "Identify potential causes",
                    "Isolate the problematic component",
                    "Test hypotheses systematically",
                    "Implement and verify the fix"
                ],
                "depth_multiplier": 1.8
            },
            "logical": {
                "steps": [
                    "Identify premises and assumptions",
                    "Examine logical relationships",
                    "Check for contradictions",
                    "Apply deductive reasoning",
                    "Validate conclusions"
                ],
                "depth_multiplier": 1.4
            }
        }
        
        # Complexity thresholds
        self.complexity_thresholds = {
            "simple": 0.3,
            "moderate": 0.6,
            "complex": 0.8
        }
            
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Apply Chain of Thought technique to the input.
        
        Args:
            text: The original prompt
            context: Additional context including:
                - reasoning_steps: Custom reasoning steps (basic mode)
                - enhanced: Force enhanced mode (default: True if available)
                - domain: Problem domain for enhanced mode
                - complexity: Complexity score (0-1) for enhanced mode
                - show_substeps: Show detailed sub-steps in enhanced mode
        
        Returns:
            Enhanced prompt with CoT structure
        """
        text = self.clean_text(text)
        context = context or {}
        
        # Check if enhanced mode should be used
        use_enhanced = (
            self.enhanced_mode and 
            context.get('enhanced', False) and  # Only use enhanced if explicitly requested
            not context.get('reasoning_steps')  # Custom steps use basic mode
        )
        
        self.logger.info(
            f"CoT apply: enhanced_mode={self.enhanced_mode}, "
            f"context_enhanced={context.get('enhanced', False)}, "
            f"has_reasoning_steps={bool(context.get('reasoning_steps'))}, "
            f"use_enhanced={use_enhanced}"
        )
        
        if use_enhanced:
            return self._apply_enhanced(text, context)
        else:
            return self._apply_basic(text, context)
    
    def _apply_basic(self, text: str, context: Dict[str, Any]) -> str:
        """Apply basic Chain of Thought (backward compatible)."""
        # Check if custom steps are provided in context
        if context and "reasoning_steps" in context:
            steps = context["reasoning_steps"]
            step_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
            custom_template = """{{ text }}

Let's think through this systematically:

{{ steps }}

Please provide detailed reasoning for each step before reaching your conclusion."""
            return self.render_template(custom_template, {"text": text, "steps": step_text})
        
        # Use default template
        return self.render_template(self.template, {"text": text})
    
    def _apply_enhanced(self, text: str, context: Dict[str, Any]) -> str:
        """Apply enhanced Chain of Thought with adaptive reasoning."""
        try:
            # Extract parameters
            domain = context.get('domain') or self._detect_domain(text)
            complexity_str = context.get('complexity', 'moderate')
            # Convert string complexity to float for calculations if needed
            if isinstance(complexity_str, str):
                complexity = complexity_string_to_float(complexity_str)
            else:
                complexity = complexity_str
                complexity_str = complexity_float_to_string(complexity)
            show_substeps = context.get('show_substeps', complexity_str in ['moderate', 'complex'])
            
            # Generate adaptive reasoning steps
            reasoning_steps = self._generate_reasoning_steps(domain, complexity_str, text)
            
            # Build enhanced prompt
            enhanced_prompt = self._build_enhanced_prompt(
                text, reasoning_steps, domain, complexity_str, show_substeps
            )
            
            self.logger.info(
                f"Applied enhanced CoT: domain={domain}, "
                f"complexity={complexity:.2f}, steps={len(reasoning_steps)}, "
                f"enhanced_mode={self.enhanced_mode}"
            )
            
            return enhanced_prompt
            
        except Exception as e:
            self.logger.error(f"Error in enhanced CoT, falling back to basic: {str(e)}")
            return self._apply_basic(text, context)
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if CoT is appropriate for the input."""
        if not text or len(text.strip()) < 10:
            self.logger.debug("Input too short for Chain of Thought")
            return False
        
        self.logger.info(f"CoT validation: text_len={len(text)}, enhanced_mode={self.enhanced_mode}, context={context}")
        
        # Enhanced validation if in enhanced mode
        # Only use enhanced validation if explicitly requested via context
        if self.enhanced_mode and context and context.get('enhanced', False):
            result = self._validate_enhanced(text, context)
            self.logger.info(f"Enhanced validation result: {result}")
            return result
        
        # Basic validation
        reasoning_keywords = [
            "analyze", "explain", "solve", "calculate", "determine",
            "evaluate", "compare", "reason", "think", "consider",
            "deduce", "infer", "conclude", "prove", "derive"
        ]
        
        text_lower = text.lower()
        has_reasoning_task = any(keyword in text_lower for keyword in reasoning_keywords)
        
        if not has_reasoning_task:
            self.logger.info("No clear reasoning task detected")
            
        return True  # CoT can generally be applied to most tasks
    
    def _validate_enhanced(self, text: str, context: Dict[str, Any]) -> bool:
        """Enhanced validation with scoring system."""
        validation_score = 0.0
        
        # Check for reasoning indicators
        reasoning_patterns = [
            (r'\b(how|why|what if|explain|analyze)\b', 0.3),
            (r'\b(solve|calculate|determine|derive|prove)\b', 0.3),
            (r'\b(compare|evaluate|assess|consider)\b', 0.2),
            (r'\?', 0.1),
            (r'\b(step|process|method|approach)\b', 0.1)
        ]
        
        text_lower = text.lower()
        for pattern, weight in reasoning_patterns:
            if re.search(pattern, text_lower):
                validation_score += weight
        
        # Complexity check
        complexity = self._estimate_complexity(text)
        if complexity > 0.3:
            validation_score += 0.3
        
        # Domain check
        domain = self._detect_domain(text)
        if domain != "general":
            validation_score += 0.3
        
        # Length bonus
        if len(text) > 50:
            validation_score += 0.1
        
        is_valid = validation_score >= 0.4  # Lower threshold
        self.logger.debug(f"Enhanced validation score: {validation_score:.2f}, domain: {domain}, is_valid: {is_valid}")
        
        return is_valid
    
    def _detect_domain(self, text: str) -> str:
        """Detect the problem domain from the text."""
        text_lower = text.lower()
        
        # Quick domain detection based on keywords
        if any(word in text_lower for word in ['equation', 'calculate', 'solve for', 'formula']):
            return "mathematical"
        elif any(word in text_lower for word in ['algorithm', 'implement', 'code', 'function']):
            return "algorithmic"
        elif any(word in text_lower for word in ['bug', 'error', 'fix', 'debug', 'issue']):
            return "debugging"
        elif any(word in text_lower for word in ['analyze', 'examine', 'investigate', 'data']):
            return "analytical"
        elif any(word in text_lower for word in ['if', 'then', 'implies', 'therefore']):
            return "logical"
        
        return "general"
    
    def _estimate_complexity(self, text: str) -> float:
        """Estimate problem complexity (0-1 scale)."""
        complexity_score = 0.0
        
        # Length factor
        word_count = len(text.split())
        complexity_score += min(word_count / 100, 1.0) * 0.3
        
        # Multiple requirements
        if text.count(',') > 3 or text.count('and') > 2:
            complexity_score += 0.2
        
        # Technical terms (simple check)
        technical_indicators = len(re.findall(r'\b[A-Z]{2,}\b', text))  # Acronyms
        complexity_score += min(technical_indicators * 0.1, 0.2)
        
        # Conditional logic
        if 'if' in text.lower() and 'then' in text.lower():
            complexity_score += 0.15
        
        # Multiple steps
        step_words = ['first', 'second', 'then', 'next', 'finally']
        step_count = sum(word in text.lower() for word in step_words)
        complexity_score += min(step_count * 0.1, 0.2)
        
        return min(complexity_score, 1.0)
    
    def _generate_reasoning_steps(self, domain: str, complexity: str, text: str) -> List[str]:
        """Generate adaptive reasoning steps based on domain and complexity."""
        # Convert string complexity to float for comparison
        if isinstance(complexity, str):
            complexity_value = complexity_string_to_float(complexity)
        else:
            complexity_value = complexity
            
        # Get domain-specific steps or use general ones
        if domain in self.reasoning_patterns:
            base_steps = self.reasoning_patterns[domain]["steps"]
        else:
            base_steps = [
                "Understand the problem and identify key information",
                "Break down the problem into components",
                "Analyze each component systematically",
                "Consider relationships and dependencies",
                "Synthesize findings into a solution"
            ]
        
        # Adjust based on complexity
        if complexity_value < self.complexity_thresholds["simple"]:
            return base_steps[:3]
        elif complexity_value < self.complexity_thresholds["moderate"]:
            return base_steps
        else:
            # Complex problems get additional detail
            steps = base_steps.copy()
            if "verify" not in steps[-1].lower():
                steps.append("Verify the solution and check edge cases")
            return steps
    
    def _build_enhanced_prompt(
        self,
        text: str,
        steps: List[str],
        domain: str,
        complexity: str,
        show_substeps: bool
    ) -> str:
        """Build the enhanced CoT prompt."""
        # Complexity-based intro
        # Convert string complexity to float for comparison
        if isinstance(complexity, str):
            complexity_value = complexity_string_to_float(complexity)
        else:
            complexity_value = complexity
            
        if complexity_value > self.complexity_thresholds["complex"]:
            intro = "This is a complex problem that requires careful analysis. Let's think through it systematically:"
        elif complexity_value > self.complexity_thresholds["moderate"]:
            intro = "Let's approach this methodically:"
        else:
            intro = "Let's think through this step by step:"
        
        # Format steps
        formatted_steps = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
        
        # Domain-specific guidance
        domain_guidance = {
            "mathematical": "\nPlease show all mathematical work and justify each step.",
            "algorithmic": "\nPlease explain the algorithm design choices and complexity analysis.",
            "debugging": "\nPlease document your debugging process and reasoning.",
            "analytical": "\nPlease provide evidence and support for your analysis.",
            "logical": "\nPlease make your logical reasoning explicit at each step."
        }
        
        guidance = domain_guidance.get(domain, "\nPlease provide detailed reasoning at each step.")
        
        # Build final prompt
        enhanced_prompt = f"""{text}

{intro}

{formatted_steps}
{guidance}"""
        
        return enhanced_prompt
    
    def get_metrics(self, generated_text: str) -> Dict[str, float]:
        """Calculate quality metrics for generated CoT reasoning."""
        metrics = {
            "step_coverage": 0.0,
            "reasoning_depth": 0.0,
            "coherence": 0.0,
            "completeness": 0.0
        }
        
        if not generated_text:
            return metrics
        
        # Check step coverage
        steps_found = len(re.findall(r'\d+\.', generated_text))
        expected_steps = 5
        metrics["step_coverage"] = min(steps_found / expected_steps, 1.0)
        
        # Check reasoning depth
        reasoning_words = ['because', 'therefore', 'thus', 'since', 'as a result']
        reasoning_count = sum(word in generated_text.lower() for word in reasoning_words)
        metrics["reasoning_depth"] = min(reasoning_count / 5, 1.0)
        
        # Check coherence
        transition_words = ['first', 'next', 'then', 'finally', 'moreover']
        transition_count = sum(word in generated_text.lower() for word in transition_words)
        metrics["coherence"] = min(transition_count / 4, 1.0)
        
        # Check completeness
        has_conclusion = any(word in generated_text.lower() 
                           for word in ['therefore', 'conclusion', 'answer', 'solution'])
        metrics["completeness"] = 1.0 if has_conclusion else 0.5
        
        return metrics