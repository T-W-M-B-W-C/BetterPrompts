from typing import Dict, Any, Optional
from .base import BaseTechnique


class EmotionalAppealTechnique(BaseTechnique):
    """
    Emotional appeal technique
    
    This technique adds emotional context or urgency to motivate
    more engaged and thoughtful responses.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.default_template = """{{ emotional_context }}

{{ text }}

{{ appeal }}"""
        
        if not self.template:
            self.template = self.default_template
            
        self.appeal_types = {
            "importance": "This is really important to me and I would greatly appreciate your thoughtful help.",
            "learning": "I'm eager to learn and understand this properly. Your clear explanation would mean a lot.",
            "impact": "Your response could make a significant positive difference in this situation.",
            "curiosity": "I'm genuinely curious about this and excited to hear your insights.",
            "challenge": "This is a challenging problem that I believe you can help solve brilliantly.",
            "collaboration": "Let's work together on this - I value your expertise and perspective.",
            "growth": "This is an opportunity for growth and improvement that I don't want to miss."
        }
        
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply emotional appeal technique"""
        text = self.clean_text(text)
        
        # Determine appeal type and context
        appeal_type = "importance"  # default
        if context and "appeal_type" in context:
            appeal_type = context["appeal_type"]
        elif context and "intent" in context:
            appeal_type = self._determine_appeal_from_intent(context["intent"])
            
        emotional_context = self._get_emotional_context(appeal_type, context)
        appeal = self._get_appeal_text(appeal_type, context)
        
        # For some cases, just append the appeal
        if context and context.get("subtle", False):
            return f"{text}\n\n{appeal}"
            
        return self.render_template(self.template, {
            "text": text,
            "emotional_context": emotional_context,
            "appeal": appeal
        })
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if emotional appeal is appropriate"""
        # Avoid emotional appeal for purely technical/factual queries
        technical_indicators = [
            "calculate", "compute", "formula", "equation",
            "definition", "specification", "syntax", "format"
        ]
        
        text_lower = text.lower()
        is_technical = any(indicator in text_lower for indicator in technical_indicators)
        
        if is_technical:
            self.logger.info("Technical query - emotional appeal may not be appropriate")
            # Still return True but with lower priority
            
        # Check if explicitly disabled
        if context and context.get("no_emotion", False):
            return False
            
        return True
    
    def _determine_appeal_from_intent(self, intent: str) -> str:
        """Determine appropriate appeal type from intent"""
        intent_appeal_map = {
            "learning": "learning",
            "problem_solving": "challenge",
            "creative": "curiosity",
            "analysis": "collaboration",
            "help": "importance",
            "improvement": "growth",
            "explanation": "learning"
        }
        
        for key, appeal in intent_appeal_map.items():
            if key in intent.lower():
                return appeal
                
        return "importance"
    
    def _get_emotional_context(self, appeal_type: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Get emotional context based on appeal type"""
        if context and "custom_context" in context:
            return context["custom_context"]
            
        context_map = {
            "importance": "I've been working on this for a while and could really use your expertise.",
            "learning": "I'm trying to deepen my understanding of this topic.",
            "impact": "This solution could help many people facing similar challenges.",
            "curiosity": "I find this fascinating and would love to explore it with you.",
            "challenge": "This is a complex problem that has me stumped.",
            "collaboration": "I believe we can find a great solution by thinking through this together.",
            "growth": "I see this as a chance to improve and do better."
        }
        
        return context_map.get(appeal_type, "")
    
    def _get_appeal_text(self, appeal_type: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Get appeal text"""
        if context and "custom_appeal" in context:
            return context["custom_appeal"]
            
        base_appeal = self.appeal_types.get(appeal_type, self.appeal_types["importance"])
        
        # Add personal touch if specified
        if context and context.get("personal", False):
            personal_additions = {
                "importance": " This truly matters for my project's success.",
                "learning": " I'm committed to understanding this thoroughly.",
                "impact": " People are counting on getting this right.",
                "curiosity": " I can't wait to see what insights you'll share.",
                "challenge": " I know you enjoy tackling complex problems like this.",
                "collaboration": " Your unique perspective would be invaluable.",
                "growth": " I'm ready to learn from your expertise."
            }
            base_appeal += personal_additions.get(appeal_type, "")
            
        return base_appeal