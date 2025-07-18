from typing import Dict, Any, Optional, List
from .base import BaseTechnique


class ConstraintsTechnique(BaseTechnique):
    """
    Constraints technique
    
    This technique adds specific constraints or requirements to guide
    the response within defined boundaries.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.default_template = """{{ text }}

Please ensure your response adheres to the following constraints:

{% for constraint in constraints %}
{{ loop.index }}. {{ constraint }}
{% endfor %}

{{ additional_guidance }}"""
        
        if not self.template:
            self.template = self.default_template
            
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply constraints technique"""
        text = self.clean_text(text)
        
        # Gather constraints from various sources
        constraints = self._gather_constraints(context)
        additional_guidance = self._get_additional_guidance(context)
        
        if not constraints:
            # If no specific constraints, add general quality constraints
            constraints = [
                "Be accurate and factual",
                "Provide clear and concise explanations",
                "Use appropriate examples when helpful"
            ]
            
        return self.render_template(self.template, {
            "text": text,
            "constraints": constraints,
            "additional_guidance": additional_guidance
        })
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if constraints technique is appropriate"""
        # Constraints can be applied to most prompts
        # Especially useful when specific requirements exist
        
        if context and ("constraints" in context or "requirements" in context):
            return True
            
        # Check for constraint indicators in text
        constraint_keywords = [
            "must", "should", "ensure", "avoid", "limit",
            "within", "maximum", "minimum", "only", "never"
        ]
        
        text_lower = text.lower()
        has_constraints = any(keyword in text_lower for keyword in constraint_keywords)
        
        if has_constraints:
            self.logger.info("Constraints detected in input")
            
        return True
    
    def _gather_constraints(self, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Gather constraints from context"""
        constraints = []
        
        if not context:
            return constraints
            
        # Direct constraints
        if "constraints" in context:
            constraints.extend(context["constraints"])
            
        # Length constraints
        if "max_length" in context:
            constraints.append(f"Keep the response under {context['max_length']} words")
        if "min_length" in context:
            constraints.append(f"Provide at least {context['min_length']} words")
            
        # Format constraints
        if "format" in context:
            constraints.append(f"Format the response as {context['format']}")
            
        # Tone constraints
        if "tone" in context:
            constraints.append(f"Use a {context['tone']} tone throughout")
            
        # Audience constraints
        if "audience" in context:
            constraints.append(f"Tailor the response for {context['audience']}")
            
        # Technical constraints
        if "technical_level" in context:
            level_map = {
                "beginner": "Explain concepts simply, avoiding jargon",
                "intermediate": "Balance technical accuracy with clarity",
                "expert": "Use precise technical terminology"
            }
            constraints.append(level_map.get(context["technical_level"], ""))
            
        # Content constraints
        if "include" in context:
            for item in context["include"]:
                constraints.append(f"Include information about {item}")
        if "exclude" in context:
            for item in context["exclude"]:
                constraints.append(f"Avoid discussing {item}")
                
        # Style constraints
        if "style" in context:
            style_constraints = self._get_style_constraints(context["style"])
            constraints.extend(style_constraints)
            
        # Remove empty constraints
        return [c for c in constraints if c]
    
    def _get_style_constraints(self, style: str) -> List[str]:
        """Get constraints based on style"""
        style_map = {
            "academic": [
                "Use formal academic language",
                "Include citations or references where appropriate",
                "Maintain objective tone"
            ],
            "conversational": [
                "Use friendly, approachable language",
                "Include relatable examples",
                "Maintain an engaging tone"
            ],
            "professional": [
                "Use clear, professional language",
                "Focus on practical applications",
                "Maintain a businesslike tone"
            ],
            "creative": [
                "Use vivid, descriptive language",
                "Include creative examples or metaphors",
                "Maintain an imaginative approach"
            ],
            "technical": [
                "Use precise technical terminology",
                "Include specific details and specifications",
                "Maintain accuracy over simplicity"
            ]
        }
        
        return style_map.get(style, [])
    
    def _get_additional_guidance(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Get additional guidance text"""
        if not context:
            return ""
            
        guidance_parts = []
        
        if "priority" in context:
            guidance_parts.append(f"Priority: {context['priority']}")
            
        if "time_limit" in context:
            guidance_parts.append(f"Time-sensitive: Provide a response that can be read in {context['time_limit']}")
            
        if "examples_required" in context:
            num_examples = context.get("num_examples", 2)
            guidance_parts.append(f"Include at least {num_examples} concrete examples")
            
        if "avoid_assumptions" in context:
            guidance_parts.append("Make no assumptions beyond what is explicitly stated")
            
        if guidance_parts:
            return "Additional guidance: " + "; ".join(guidance_parts)
            
        return ""