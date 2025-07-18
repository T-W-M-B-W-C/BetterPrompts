from typing import Dict, Any, Optional, List
from .base import BaseTechnique


class AnalogicalTechnique(BaseTechnique):
    """
    Analogical reasoning technique
    
    This technique uses analogies and comparisons to explain complex
    concepts or solve problems by relating them to familiar situations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.default_template = """{{ text }}

To better understand this, let's use an analogy:

{{ analogy }}

{{ connection }}

Now, applying this analogy to our specific case:
{{ application }}"""
        
        if not self.template:
            self.template = self.default_template
            
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply analogical reasoning technique"""
        text = self.clean_text(text)
        
        # Get or generate analogy
        analogy = ""
        connection = ""
        application = ""
        
        if context and "analogy" in context:
            analogy = context["analogy"]
            connection = context.get("connection", "This relates to our problem because:")
            application = context.get("application", "[Apply the analogy to solve the problem]")
        else:
            # Generate based on domain
            domain = context.get("domain", "general") if context else "general"
            analogy_data = self._generate_analogy(text, domain)
            analogy = analogy_data["analogy"]
            connection = analogy_data["connection"]
            application = analogy_data["application"]
            
        # For simple analogical prompts
        if context and context.get("simple", False):
            return f"{text}\n\nThink of it like this: {analogy}"
            
        return self.render_template(self.template, {
            "text": text,
            "analogy": analogy,
            "connection": connection,
            "application": application
        })
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if analogical reasoning is appropriate"""
        # Check for complexity that benefits from analogies
        complexity_indicators = [
            "complex", "difficult", "understand", "explain",
            "how", "why", "similar", "like", "compare"
        ]
        
        text_lower = text.lower()
        benefits_from_analogy = any(indicator in text_lower for indicator in complexity_indicators)
        
        # Also good for teaching/learning contexts
        if context and context.get("educational", False):
            return True
            
        if benefits_from_analogy:
            self.logger.info("Analogical reasoning would be helpful")
            
        return True
    
    def _generate_analogy(self, text: str, domain: str) -> Dict[str, str]:
        """Generate appropriate analogy based on domain"""
        # Analyze text to determine concept type
        concept_type = self._identify_concept_type(text)
        
        # Get domain-specific analogies
        analogies = self._get_domain_analogies(domain, concept_type)
        
        if analogies:
            return analogies[0]  # Use first matching analogy
            
        # Fallback to general analogies
        return self._get_general_analogy(concept_type)
    
    def _identify_concept_type(self, text: str) -> str:
        """Identify the type of concept being discussed"""
        text_lower = text.lower()
        
        concept_types = {
            "system": ["system", "architecture", "structure", "framework"],
            "process": ["process", "flow", "sequence", "procedure", "method"],
            "relationship": ["relationship", "connection", "interaction", "communication"],
            "growth": ["growth", "development", "improvement", "evolution"],
            "problem": ["problem", "issue", "challenge", "obstacle"],
            "organization": ["organize", "arrange", "sort", "categorize"],
            "balance": ["balance", "trade-off", "equilibrium", "optimization"]
        }
        
        for concept, keywords in concept_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return concept
                
        return "general"
    
    def _get_domain_analogies(self, domain: str, concept_type: str) -> List[Dict[str, str]]:
        """Get domain-specific analogies"""
        domain_analogies = {
            "software": {
                "system": [{
                    "analogy": "A software system is like a city. Just as a city has districts (modules), roads (interfaces), and utilities (services), a software system has components that must work together harmoniously.",
                    "connection": "This helps us understand how different parts interact and depend on each other.",
                    "application": "We can design our system with clear 'districts' (modules) connected by well-defined 'roads' (APIs)."
                }],
                "process": [{
                    "analogy": "A software development process is like cooking a complex meal. You need the right ingredients (requirements), a good recipe (design), proper timing (scheduling), and quality checks (testing).",
                    "connection": "Both require careful planning and execution in the right order.",
                    "application": "We should approach our development with the same care a chef uses in the kitchen."
                }]
            },
            "business": {
                "system": [{
                    "analogy": "A business organization is like a sports team. Each player (employee) has a specific position (role) and must coordinate with teammates to score goals (achieve objectives).",
                    "connection": "Success requires both individual excellence and team coordination.",
                    "application": "We need to ensure each team member knows their role and how it contributes to our goals."
                }],
                "growth": [{
                    "analogy": "Business growth is like tending a garden. You need good soil (market), seeds (ideas), water and sunlight (resources), and patience for the plants (initiatives) to grow.",
                    "connection": "Both require consistent nurturing and the right conditions.",
                    "application": "We should focus on creating the right environment for our initiatives to flourish."
                }]
            }
        }
        
        domain_specific = domain_analogies.get(domain, {})
        return domain_specific.get(concept_type, [])
    
    def _get_general_analogy(self, concept_type: str) -> Dict[str, str]:
        """Get general analogies by concept type"""
        general_analogies = {
            "system": {
                "analogy": "Think of this like an orchestra. Each instrument (component) plays its part, and the conductor (controller) ensures they work in harmony to create beautiful music (desired outcome).",
                "connection": "This shows how individual parts must coordinate to achieve something greater.",
                "application": "We need to ensure each component knows its role and timing."
            },
            "process": {
                "analogy": "This is like following a recipe. You need ingredients (inputs), steps to follow (process), and the right conditions (environment) to get the desired dish (output).",
                "connection": "Both require following steps in order with the right resources.",
                "application": "Let's identify our 'ingredients' and 'recipe steps' clearly."
            },
            "problem": {
                "analogy": "Solving this is like untangling a knot. You need to find the right thread to pull (key issue), work patiently, and sometimes loosen other parts before you can resolve it.",
                "connection": "Complex problems often require patience and systematic approach.",
                "application": "Let's identify which 'thread' to pull first."
            },
            "general": {
                "analogy": "Consider this like building with LEGO blocks. You start with basic pieces (fundamentals) and combine them in specific ways to create something complex and functional.",
                "connection": "Complex things are built from simple, well-understood components.",
                "application": "Let's identify our basic 'blocks' and how they fit together."
            }
        }
        
        return general_analogies.get(concept_type, general_analogies["general"])