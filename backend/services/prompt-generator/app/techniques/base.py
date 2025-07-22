from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type
import re
from jinja2 import Template, Environment, meta
import structlog

logger = structlog.get_logger()


class BaseTechnique(ABC):
    """Base class for all prompt engineering techniques"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", self.__class__.__name__)
        self.template = config.get("template", "")
        self.parameters = config.get("parameters", {})
        self.priority = config.get("priority", 0)
        self.enabled = config.get("enabled", True)
        self.logger = logger.bind(technique=self.name)
        
    @abstractmethod
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply the technique to the input text"""
        pass
    
    @abstractmethod
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if the technique can be applied to the input"""
        pass
    
    def render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render a Jinja2 template with given variables"""
        try:
            jinja_template = Template(template)
            return jinja_template.render(**variables)
        except Exception as e:
            self.logger.error(f"Template rendering error: {e}", template=template, variables=variables)
            raise
    
    def extract_template_variables(self, template: str) -> List[str]:
        """Extract variable names from a Jinja2 template"""
        env = Environment()
        ast = env.parse(template)
        return list(meta.find_undeclared_variables(ast))
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for the text"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize input text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get technique metadata"""
        return {
            "name": self.name,
            "priority": self.priority,
            "enabled": self.enabled,
            "parameters": self.parameters,
        }


class TechniqueRegistry:
    """Registry for managing prompt engineering techniques"""
    
    def __init__(self):
        self._techniques: Dict[str, Type[BaseTechnique]] = {}
        self._instances: Dict[str, BaseTechnique] = {}
        self.logger = structlog.get_logger()
        
    def register(self, technique_id: str, technique_class: Type[BaseTechnique]):
        """Register a technique class"""
        if technique_id in self._techniques:
            self.logger.warning(f"Overwriting existing technique: {technique_id}")
        self._techniques[technique_id] = technique_class
        self.logger.info(f"Registered technique: {technique_id}")
        
    def create_instance(self, technique_id: str, config: Dict[str, Any]) -> BaseTechnique:
        """Create an instance of a technique"""
        if technique_id not in self._techniques:
            raise ValueError(f"Unknown technique: {technique_id}")
            
        technique_class = self._techniques[technique_id]
        instance = technique_class(config)
        self._instances[technique_id] = instance
        return instance
        
    def get_instance(self, technique_id: str) -> Optional[BaseTechnique]:
        """Get a technique instance"""
        return self._instances.get(technique_id)
        
    def get_all_instances(self) -> Dict[str, BaseTechnique]:
        """Get all technique instances"""
        return self._instances.copy()
        
    def apply_technique(self, technique_id: str, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply a specific technique"""
        technique = self.get_instance(technique_id)
        if not technique:
            raise ValueError(f"Technique not initialized: {technique_id}")
            
        if not technique.enabled:
            self.logger.warning(f"Technique is disabled: {technique_id}")
            return text
            
        self.logger.info(f"Validating technique {technique_id} with context: {context}")
        validation_result = technique.validate_input(text, context)
        if not validation_result:
            self.logger.warning(f"Input validation failed for technique: {technique_id}")
            return text
        self.logger.info(f"Validation passed for technique: {technique_id}")
            
        try:
            result = technique.apply(text, context)
            self.logger.info(f"Successfully applied technique: {technique_id}")
            return result
        except Exception as e:
            self.logger.error(f"Error applying technique {technique_id}: {e}")
            raise
            
    def apply_multiple(self, technique_ids: List[str], text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply multiple techniques in sequence"""
        result = text
        applied_techniques = []
        
        # Sort by priority
        sorted_ids = sorted(
            technique_ids,
            key=lambda x: self.get_instance(x).priority if self.get_instance(x) else 0,
            reverse=True
        )
        
        for technique_id in sorted_ids:
            try:
                result = self.apply_technique(technique_id, result, context)
                applied_techniques.append(technique_id)
            except Exception as e:
                self.logger.error(f"Failed to apply technique {technique_id}: {e}")
                continue
                
        self.logger.info(f"Applied techniques: {applied_techniques}")
        return result
        
    def list_available(self) -> List[str]:
        """List all available technique IDs"""
        return list(self._techniques.keys())
        
    def list_enabled(self) -> List[str]:
        """List all enabled technique IDs"""
        return [
            tid for tid, technique in self._instances.items()
            if technique.enabled
        ]


# Global registry instance
technique_registry = TechniqueRegistry()