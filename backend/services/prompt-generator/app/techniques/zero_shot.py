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
        complexity = context.get("complexity", "simple")
        
        # Enhanced instruction map with complexity-aware instructions
        instruction_map = {
            "question_answering": {
                "simple": "Answer the following question clearly:",
                "moderate": "Provide a comprehensive answer to the following question, including relevant context:",
                "complex": "Analyze and answer the following question in depth, considering multiple perspectives and implications:"
            },
            "summarization": {
                "simple": "Summarize the following text briefly:",
                "moderate": "Summarize the following text, preserving key details and insights:",
                "complex": "Provide a comprehensive summary with analysis of the following:"
            },
            "explanation": {
                "simple": "Explain the following in simple terms:",
                "moderate": "Explain the following clearly, including relevant details and examples:",
                "complex": "Provide a thorough explanation with multiple perspectives, examples, and implications:"
            },
            "problem_solving": {
                "simple": "Solve the following problem:",
                "moderate": "Solve the following problem, showing your reasoning process:",
                "complex": "Analyze and solve the following problem systematically, considering edge cases and alternatives:"
            },
            "creative_writing": {
                "simple": "Create content based on:",
                "moderate": "Create engaging and well-structured content based on:",
                "complex": "Craft sophisticated, nuanced content with depth and originality based on:"
            },
            "code_generation": {
                "simple": "Generate code for:",
                "moderate": "Generate clean, documented code with error handling for:",
                "complex": "Design and implement a robust, scalable solution with best practices for:"
            },
            "reasoning": {
                "simple": "Consider the following:",
                "moderate": "Analyze and reason through the following:",
                "complex": "Provide deep analytical reasoning with evidence and logical progression for:"
            },
            "data_analysis": {
                "simple": "Analyze the following data:",
                "moderate": "Perform detailed analysis with insights on the following:",
                "complex": "Conduct comprehensive data analysis with patterns, correlations, and recommendations:"
            },
            "task_planning": {
                "simple": "Plan the following task:",
                "moderate": "Create a detailed plan with milestones for:",
                "complex": "Develop a comprehensive strategy with risk assessment and contingencies for:"
            }
        }
        
        # Get the appropriate instruction based on intent and complexity
        if intent in instruction_map:
            if isinstance(instruction_map[intent], dict):
                return instruction_map[intent].get(complexity, instruction_map[intent].get("moderate"))
            return instruction_map[intent]
        
        # Fallback with complexity awareness
        fallback_map = {
            "simple": "Please provide a clear response to the following:",
            "moderate": "Please provide a detailed and well-structured response to the following:",
            "complex": "Please provide a comprehensive, nuanced analysis of the following:"
        }
        
        return fallback_map.get(complexity, "Please provide a clear and helpful response to the following:")
    
    def _build_constraints(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build constraints based on context"""
        if not context:
            return ""
            
        constraints = []
        complexity = context.get("complexity", "simple")
        intent = context.get("intent", "general")
        
        # Add complexity-based structure requirements
        if complexity == "moderate":
            constraints.append("Structure your response with clear sections or paragraphs.")
            constraints.append("Include relevant examples or evidence where appropriate.")
        elif complexity == "complex":
            constraints.append("Organize your response with clear headings or numbered sections.")
            constraints.append("Provide comprehensive coverage with examples and evidence.")
            constraints.append("Consider multiple viewpoints or approaches.")
        
        # Add intent-specific requirements
        intent_requirements = {
            "code_generation": ["Include comments explaining key logic", "Follow best practices and conventions"],
            "explanation": ["Use clear examples", "Define technical terms"],
            "problem_solving": ["Show your work", "Verify your solution"],
            "data_analysis": ["Present findings clearly", "Support conclusions with data"],
            "reasoning": ["Make your logic explicit", "Address potential counterarguments"]
        }
        
        if intent in intent_requirements:
            constraints.extend(intent_requirements[intent])
        
        # Add user-specified constraints
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
            return "Guidelines:\n" + "\n".join(f"• {c}" for c in constraints)
            
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