from typing import Dict, Any, Optional
from .base import BaseTechnique


class ZeroShotTechnique(BaseTechnique):
    """
    Zero-shot learning technique
    
    This technique provides clear instructions without examples,
    relying on the model's pre-trained knowledge.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.default_template = """{{ instruction }}

{{ text }}

{{ constraints }}

{{ format_instruction }}"""
        
        if not self.template:
            self.template = self.default_template
            
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply zero-shot technique"""
        text = self.clean_text(text)
        
        # Build instruction based on context
        instruction = self._build_instruction(context)
        constraints = self._build_constraints(context)
        format_instruction = self._build_format_instruction(context)
        
        # If we have very specific context, enhance the instruction
        if context and "task_description" in context:
            instruction = context["task_description"]
        
        result = self.render_template(self.template, {
            "text": text,
            "instruction": instruction,
            "constraints": constraints,
            "format_instruction": format_instruction
        })
        
        # Clean up multiple newlines
        result = "\n".join(line for line in result.split("\n") if line.strip())
        return result
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if zero-shot is appropriate"""
        # Zero-shot works well for straightforward tasks
        # It's less suitable for highly complex or ambiguous tasks
        
        if not text or len(text.strip()) == 0:
            return False
            
        # Check if task is too complex for zero-shot
        complexity_indicators = [
            "step by step",
            "detailed analysis",
            "comprehensive",
            "in-depth",
            "thorough examination"
        ]
        
        text_lower = text.lower()
        is_complex = any(indicator in text_lower for indicator in complexity_indicators)
        
        if is_complex and (not context or "force_zero_shot" not in context):
            self.logger.info("Task may be too complex for pure zero-shot")
            # Still return True as zero-shot can be attempted
            
        return True
    
    def _build_instruction(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build instruction based on context"""
        if not context:
            return "Please provide a clear and helpful response to the following:"
            
        intent = context.get("intent", "general")
        
        instruction_map = {
            "question_answering": "Answer the following question accurately and comprehensively:",
            "summarization": "Summarize the following text concisely while preserving key information:",
            "translation": "Translate the following text accurately:",
            "classification": "Classify the following input into the appropriate category:",
            "generation": "Generate content based on the following prompt:",
            "analysis": "Analyze the following and provide insights:",
            "explanation": "Explain the following clearly and thoroughly:",
            "problem_solving": "Solve the following problem with clear reasoning:",
            "creative_writing": "Create engaging content based on the following:",
            "code_generation": "Generate clean, efficient code for the following requirement:"
        }
        
        return instruction_map.get(intent, "Please provide a clear and helpful response to the following:")
    
    def _build_constraints(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build constraints based on context"""
        if not context:
            return ""
            
        constraints = []
        
        if "max_length" in context:
            constraints.append(f"Keep your response under {context['max_length']} words.")
            
        if "tone" in context:
            constraints.append(f"Use a {context['tone']} tone.")
            
        if "audience" in context:
            constraints.append(f"Tailor your response for {context['audience']}.")
            
        if "requirements" in context:
            for req in context["requirements"]:
                constraints.append(f"Ensure you {req}.")
                
        if constraints:
            return "Requirements:\n" + "\n".join(f"- {c}" for c in constraints)
            
        return ""
    
    def _build_format_instruction(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build format instruction based on context"""
        if not context or "output_format" not in context:
            return ""
            
        format_type = context["output_format"]
        
        format_map = {
            "json": "Provide your response in valid JSON format.",
            "markdown": "Format your response using Markdown.",
            "bullet_points": "Structure your response using bullet points.",
            "numbered_list": "Present your response as a numbered list.",
            "paragraph": "Write your response in paragraph form.",
            "table": "Present the information in a table format.",
            "code": "Format your response as code with appropriate syntax highlighting."
        }
        
        return format_map.get(format_type, "")