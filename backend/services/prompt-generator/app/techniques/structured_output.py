from typing import Dict, Any, Optional
from .base import BaseTechnique
import json


class StructuredOutputTechnique(BaseTechnique):
    """
    Structured output technique
    
    This technique requests responses in specific formats like
    JSON, XML, tables, or custom structures.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.default_template = """{{ text }}

Please provide your response in the following format:

{{ format_specification }}

{{ format_example }}

Ensure your response strictly follows this structure."""
        
        if not self.template:
            self.template = self.default_template
            
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply structured output technique"""
        text = self.clean_text(text)
        
        # Determine output format
        output_format = "json"  # default
        if context and "output_format" in context:
            output_format = context["output_format"]
            
        format_spec = self._get_format_specification(output_format, context)
        format_example = self._get_format_example(output_format, context)
        
        return self.render_template(self.template, {
            "text": text,
            "format_specification": format_spec,
            "format_example": format_example
        })
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if structured output is appropriate"""
        # Structured output is useful when specific format is needed
        if context and "output_format" in context:
            return True
            
        # Check for format indicators in text
        format_keywords = [
            "json", "table", "list", "format", "structure",
            "organize", "categorize", "xml", "csv", "markdown"
        ]
        
        text_lower = text.lower()
        needs_structure = any(keyword in text_lower for keyword in format_keywords)
        
        if needs_structure:
            self.logger.info("Structured output would be beneficial")
            
        return True
    
    def _get_format_specification(self, output_format: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Get format specification based on output type"""
        if context and "custom_format" in context:
            return context["custom_format"]
            
        format_specs = {
            "json": """```json
{
  "summary": "Brief summary of the response",
  "main_points": [
    "Point 1",
    "Point 2"
  ],
  "details": {
    "key": "value"
  },
  "metadata": {
    "confidence": 0.95,
    "sources": []
  }
}
```""",
            "markdown": """# Main Title

## Section 1
- Key point
- Supporting detail

## Section 2
1. Numbered item
2. Another item

### Subsection
Additional details here.""",
            "table": """| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |""",
            "xml": """```xml
<response>
  <summary>Brief summary</summary>
  <sections>
    <section id="1">
      <title>Section Title</title>
      <content>Section content</content>
    </section>
  </sections>
</response>
```""",
            "yaml": """```yaml
summary: Brief summary
main_points:
  - Point 1
  - Point 2
details:
  key1: value1
  key2: value2
metadata:
  confidence: 0.95
```""",
            "csv": """Column1,Column2,Column3
Value1,Value2,Value3
Value4,Value5,Value6""",
            "bullet_points": """• Main Point 1
  ◦ Sub-point 1.1
  ◦ Sub-point 1.2
• Main Point 2
  ◦ Sub-point 2.1
• Main Point 3""",
            "numbered_list": """1. First main point
   1.1. Sub-point
   1.2. Another sub-point
2. Second main point
   2.1. Sub-point
3. Third main point"""
        }
        
        return format_specs.get(output_format, "Structured format as appropriate")
    
    def _get_format_example(self, output_format: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Get format example based on context"""
        if context and "example" in context:
            return f"Example:\n{context['example']}"
            
        if context and "schema" in context and output_format == "json":
            return self._generate_json_example(context["schema"])
            
        examples = {
            "json": """Example for a question about Python features:
```json
{
  "summary": "Python key features overview",
  "main_points": [
    "Dynamic typing",
    "Interpreted language",
    "Extensive standard library"
  ],
  "details": {
    "typing": "Python uses dynamic typing with optional type hints",
    "performance": "Generally slower than compiled languages but highly productive"
  },
  "metadata": {
    "confidence": 0.90,
    "sources": ["official documentation", "community best practices"]
  }
}
```""",
            "table": """Example for comparing options:
| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| A      | Fast | Expensive | For high-performance needs |
| B      | Cheap | Slow | For budget constraints |"""
        }
        
        return examples.get(output_format, "")
    
    def _generate_json_example(self, schema: Dict[str, Any]) -> str:
        """Generate JSON example from schema"""
        try:
            example = {}
            for key, value in schema.items():
                if isinstance(value, dict) and "type" in value:
                    example[key] = self._get_example_value(value["type"])
                else:
                    example[key] = "example_value"
                    
            return f"Example based on schema:\n```json\n{json.dumps(example, indent=2)}\n```"
        except Exception as e:
            self.logger.error(f"Failed to generate JSON example: {e}")
            return ""
    
    def _get_example_value(self, value_type: str) -> Any:
        """Get example value for a type"""
        type_examples = {
            "string": "example text",
            "number": 42,
            "boolean": True,
            "array": ["item1", "item2"],
            "object": {"key": "value"}
        }
        return type_examples.get(value_type, "example")