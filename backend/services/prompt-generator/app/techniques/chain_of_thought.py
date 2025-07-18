from typing import Dict, Any, Optional
from .base import BaseTechnique


class ChainOfThoughtTechnique(BaseTechnique):
    """
    Chain of Thought (CoT) prompting technique
    
    This technique encourages step-by-step reasoning by explicitly
    asking the model to show its thinking process.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.default_template = """{{ text }}

Let's approach this step-by-step:

1. First, let me understand what is being asked...
2. Next, I'll identify the key components...
3. Then, I'll analyze each part...
4. Finally, I'll synthesize the solution...

Please show your reasoning at each step."""
        
        if not self.template:
            self.template = self.default_template
            
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply Chain of Thought technique to the input"""
        text = self.clean_text(text)
        
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
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if CoT is appropriate for the input"""
        # CoT is best for complex reasoning tasks
        if len(text.split()) < 10:  # Very short prompts might not benefit
            self.logger.warning("Input too short for Chain of Thought")
            return False
            
        # Check for certain keywords that indicate reasoning tasks
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