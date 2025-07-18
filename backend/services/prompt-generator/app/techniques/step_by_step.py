from typing import Dict, Any, Optional, List
from .base import BaseTechnique


class StepByStepTechnique(BaseTechnique):
    """
    Step-by-step instruction technique
    
    This technique breaks down complex tasks into clear, sequential steps
    to ensure thorough and organized completion.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.default_template = """{{ text }}

Please complete this task by following these steps:

{% for step in steps %}
Step {{ loop.index }}: {{ step }}
{% endfor %}

{{ additional_instructions }}

Begin with Step 1 and work through each step sequentially."""
        
        if not self.template:
            self.template = self.default_template
            
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply step-by-step technique"""
        text = self.clean_text(text)
        
        # Generate or use provided steps
        steps = []
        additional_instructions = ""
        
        if context and "steps" in context:
            steps = context["steps"]
        else:
            steps = self._generate_steps(text, context)
            
        if context and "verification_steps" in context:
            additional_instructions = "\nAfter completing all steps, verify your work by:\n"
            for i, vstep in enumerate(context["verification_steps"], 1):
                additional_instructions += f"{i}. {vstep}\n"
                
        if not steps:
            # Fallback to generic instruction
            return f"{text}\n\nPlease approach this task systematically, breaking it down into clear steps."
            
        return self.render_template(self.template, {
            "text": text,
            "steps": steps,
            "additional_instructions": additional_instructions.strip()
        })
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if step-by-step is appropriate"""
        # Check if task is complex enough to benefit from steps
        complexity_indicators = [
            "multiple", "several", "various", "steps", "process",
            "procedure", "workflow", "sequence", "stages", "phases"
        ]
        
        text_lower = text.lower()
        is_multi_step = any(indicator in text_lower for indicator in complexity_indicators)
        
        # Also check text length as an indicator
        word_count = len(text.split())
        if word_count < 10 and not is_multi_step:
            self.logger.info("Task appears too simple for step-by-step breakdown")
            
        return True
    
    def _generate_steps(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Generate steps based on the task type"""
        if context and "task_type" in context:
            return self._get_steps_by_type(context["task_type"], text)
            
        # Try to infer task type from text
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["analyze", "analysis", "examine"]):
            return self._get_steps_by_type("analysis", text)
        elif any(word in text_lower for word in ["create", "build", "develop", "design"]):
            return self._get_steps_by_type("creation", text)
        elif any(word in text_lower for word in ["solve", "fix", "debug", "troubleshoot"]):
            return self._get_steps_by_type("problem_solving", text)
        elif any(word in text_lower for word in ["explain", "describe", "teach"]):
            return self._get_steps_by_type("explanation", text)
        else:
            return self._get_generic_steps()
    
    def _get_steps_by_type(self, task_type: str, text: str) -> List[str]:
        """Get task-specific steps"""
        steps_map = {
            "analysis": [
                "Identify the key components or elements to analyze",
                "Gather relevant data and context",
                "Examine relationships and patterns",
                "Evaluate findings against criteria",
                "Draw conclusions and insights",
                "Provide recommendations if applicable"
            ],
            "creation": [
                "Define requirements and constraints",
                "Research and gather necessary resources",
                "Create initial design or outline",
                "Implement the core functionality",
                "Refine and optimize the solution",
                "Test and validate the result"
            ],
            "problem_solving": [
                "Clearly define the problem",
                "Identify root causes or contributing factors",
                "Generate potential solutions",
                "Evaluate each solution's feasibility",
                "Implement the chosen solution",
                "Verify the problem is resolved"
            ],
            "explanation": [
                "Introduce the topic with context",
                "Break down complex concepts into simple parts",
                "Provide examples or analogies",
                "Address common questions or misconceptions",
                "Summarize key points",
                "Suggest next steps or applications"
            ],
            "implementation": [
                "Review requirements and specifications",
                "Plan the implementation approach",
                "Set up necessary environment or dependencies",
                "Implement core functionality",
                "Add error handling and edge cases",
                "Test and document the implementation"
            ]
        }
        
        return steps_map.get(task_type, self._get_generic_steps())
    
    def _get_generic_steps(self) -> List[str]:
        """Get generic steps for unknown task types"""
        return [
            "Understand the requirements and objectives",
            "Plan your approach",
            "Execute the main task",
            "Review and refine the output",
            "Ensure all requirements are met"
        ]