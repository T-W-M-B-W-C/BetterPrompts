from typing import Dict, Any, Optional
from .base import BaseTechnique


class RolePlayTechnique(BaseTechnique):
    """
    Role-playing technique
    
    This technique assigns a specific role or persona to the model
    to influence its responses and expertise.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.default_template = """You are {{ role }}. {{ role_description }}

{{ additional_context }}

With this expertise and perspective in mind, please address the following:

{{ text }}"""
        
        if not self.template:
            self.template = self.default_template
            
        self.default_roles = {
            "expert": {
                "description": "an expert in the relevant field with deep knowledge and years of experience",
                "traits": ["analytical", "precise", "authoritative"]
            },
            "teacher": {
                "description": "an experienced teacher who excels at explaining complex concepts simply",
                "traits": ["patient", "clear", "encouraging"]
            },
            "consultant": {
                "description": "a professional consultant who provides strategic advice and solutions",
                "traits": ["strategic", "practical", "results-oriented"]
            },
            "researcher": {
                "description": "a meticulous researcher who values accuracy and evidence-based approaches",
                "traits": ["thorough", "objective", "data-driven"]
            },
            "creative": {
                "description": "a creative professional who thinks outside the box and generates innovative ideas",
                "traits": ["imaginative", "original", "unconventional"]
            }
        }
        
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply role-playing technique"""
        text = self.clean_text(text)
        
        # Determine role from context
        role = "an expert"
        role_description = "an expert in the relevant field"
        additional_context = ""
        
        if context:
            if "role" in context:
                role = context["role"]
                role_description = context.get("role_description", f"{role} with specialized knowledge")
            elif "intent" in context:
                role, role_description = self._determine_role_from_intent(context["intent"])
            
            if "domain" in context:
                additional_context = f"Your expertise particularly covers {context['domain']}."
            
            if "traits" in context:
                traits_text = ", ".join(context["traits"])
                additional_context += f" You are known for being {traits_text}."
        
        return self.render_template(self.template, {
            "text": text,
            "role": role,
            "role_description": role_description,
            "additional_context": additional_context.strip()
        })
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if role-playing is appropriate"""
        # Role-playing can enhance most prompts
        # But it's particularly useful for certain types
        
        # Check for expertise-requiring keywords
        expertise_keywords = [
            "expert", "professional", "analyze", "advise", "recommend",
            "evaluate", "assess", "review", "critique", "guide"
        ]
        
        text_lower = text.lower()
        benefits_from_role = any(keyword in text_lower for keyword in expertise_keywords)
        
        if benefits_from_role:
            self.logger.info("Input would benefit from role-playing")
            
        return True  # Can be applied to most prompts
    
    def _determine_role_from_intent(self, intent: str) -> tuple[str, str]:
        """Determine appropriate role based on intent"""
        intent_role_mapping = {
            "educational": ("an experienced educator", "a teacher who specializes in making complex topics accessible"),
            "analytical": ("a data analyst", "an analytical expert who excels at breaking down complex problems"),
            "creative": ("a creative director", "a creative professional who generates innovative solutions"),
            "technical": ("a senior engineer", "a technical expert with deep knowledge of software and systems"),
            "business": ("a business strategist", "a business consultant with expertise in strategy and operations"),
            "scientific": ("a research scientist", "a scientist with expertise in research methodology and analysis"),
            "writing": ("a professional writer", "an experienced writer who crafts compelling and clear content"),
            "debugging": ("a senior developer", "a debugging expert who quickly identifies and resolves issues"),
            "design": ("a UX designer", "a design expert who creates intuitive and beautiful experiences")
        }
        
        for key, (role, description) in intent_role_mapping.items():
            if key in intent.lower():
                return role, description
                
        # Default fallback
        return "an expert", "a knowledgeable expert in the relevant field"