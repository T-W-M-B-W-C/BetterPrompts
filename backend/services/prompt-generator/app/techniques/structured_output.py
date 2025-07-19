from typing import Dict, Any, Optional, List, Union
from .base import BaseTechnique
import json
import yaml
from xml.etree import ElementTree as ET
import re


class StructuredOutputTechnique(BaseTechnique):
    """
    Enhanced structured output technique with schema validation
    
    This technique requests responses in specific formats like JSON, XML, YAML,
    tables, or custom structures with advanced validation and optimization.
    
    Features:
    - Multiple format support with format-specific templates
    - Schema validation for JSON/XML
    - Grammar-based constraints
    - Hierarchical generation support
    - Error recovery strategies
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Configuration parameters
        self.strict_mode = self.parameters.get("strict_mode", True)
        self.use_prefilling = self.parameters.get("use_prefilling", True)
        self.hierarchical_generation = self.parameters.get("hierarchical_generation", False)
        self.include_schema = self.parameters.get("include_schema", True)
        self.error_handling = self.parameters.get("error_handling", "explicit")  # explicit, implicit, retry
        self.temperature_override = self.parameters.get("temperature_override", 0.0)  # For greedy decoding
        
        # Format-specific templates
        self.templates = {
            "json": self._get_json_template(),
            "xml": self._get_xml_template(),
            "yaml": self._get_yaml_template(),
            "csv": self._get_csv_template(),
            "table": self._get_table_template(),
            "markdown": self._get_markdown_template(),
            "custom": self._get_custom_template()
        }
        
        if not self.template:
            self.template = self.templates.get("json")  # Default to JSON
            
    def _get_json_template(self) -> str:
        """Get JSON-specific template with best practices"""
        return """{{ text }}

{% if temperature_instruction %}
IMPORTANT: Use precise, deterministic generation (temperature=0) for this structured output.
{% endif %}

Please provide your response as valid JSON that can be parsed with `json.loads()`.

{% if include_schema and schema %}
Required JSON Schema:
```json
{{ schema | tojson(indent=2) }}
```
{% endif %}

{{ format_specification }}

{% if use_prefilling %}
Begin your response with: ```json
{% endif %}

{{ format_example }}

{% if error_handling == 'explicit' %}
If the input cannot be structured according to the schema, respond with:
```json
{
  "error": true,
  "reason": "Explanation of why the input cannot be structured",
  "partial_data": {}
}
```
{% endif %}

Ensure your JSON response:
- Is syntactically valid
- Follows the exact schema if provided
- Uses consistent naming conventions
- Includes all required fields
- Properly escapes special characters"""
    
    def _get_xml_template(self) -> str:
        """Get XML-specific template"""
        return """{{ text }}

Please provide your response in valid XML format.

{% if include_schema and schema %}
Required XML Structure:
{{ schema }}
{% endif %}

{{ format_specification }}

{% if use_prefilling %}
Begin your response with: <response>
{% endif %}

{{ format_example }}

Important XML requirements:
- Use proper opening and closing tags
- Escape special characters (&lt; &gt; &amp; &quot; &apos;)
- Include XML declaration if needed: <?xml version="1.0" encoding="UTF-8"?>
- Ensure well-formed structure with proper nesting
{% if hierarchical_generation %}
- Generate top-level structure first, then fill in details
{% endif %}"""
    
    def _get_yaml_template(self) -> str:
        """Get YAML-specific template"""
        return """{{ text }}

Please provide your response in valid YAML format.

{{ format_specification }}

{% if use_prefilling %}
Begin your response with: ```yaml
{% endif %}

{{ format_example }}

YAML formatting requirements:
- Use consistent indentation (2 spaces)
- Properly quote strings when needed
- Use appropriate data types (strings, numbers, booleans, lists, objects)
- Avoid tabs - use spaces only
- Follow YAML 1.2 specification"""
    
    def _get_csv_template(self) -> str:
        """Get CSV-specific template"""
        return """{{ text }}

Please provide your response in CSV format.

{% if csv_config %}
CSV Configuration:
- Delimiter: {{ csv_config.delimiter | default(',') }}
- Quote character: {{ csv_config.quote_char | default('"') }}
- Include headers: {{ csv_config.include_headers | default('yes') }}
{% endif %}

{{ format_specification }}

{{ format_example }}

CSV requirements:
- First row should contain column headers
- Properly quote fields containing delimiters or newlines
- Escape quotes within quoted fields
- Maintain consistent number of columns per row"""
    
    def _get_table_template(self) -> str:
        """Get table-specific template"""
        return """{{ text }}

Please provide your response as a formatted table.

{% if table_style %}
Table style: {{ table_style }}
{% endif %}

{{ format_specification }}

{{ format_example }}

Table formatting requirements:
- Use consistent column widths
- Align numeric data to the right
- Include clear headers
- Use appropriate separators (|, -, +)
- Ensure readability with proper spacing"""
    
    def _get_markdown_template(self) -> str:
        """Get Markdown-specific template"""
        return """{{ text }}

Please provide your response in Markdown format.

{% if markdown_features %}
Required Markdown features:
{% for feature in markdown_features %}
- {{ feature }}
{% endfor %}
{% endif %}

{{ format_specification }}

{{ format_example }}

Markdown requirements:
- Use appropriate heading levels (# ## ###)
- Format lists consistently (- or 1. 2. 3.)
- Use code blocks with language specification
- Include links in proper format [text](url)
- Bold **important** text and italicize *emphasis*"""
    
    def _get_custom_template(self) -> str:
        """Get custom format template"""
        return """{{ text }}

Please provide your response in the following custom format:

{{ format_specification }}

{{ format_example }}

{% if custom_requirements %}
Additional requirements:
{{ custom_requirements }}
{% endif %}"""
    
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply structured output technique with enhanced features"""
        text = self.clean_text(text)
        
        # Determine output format
        output_format = context.get("output_format", "json") if context else "json"
        
        # Select appropriate template
        template = self.templates.get(output_format, self.templates["custom"])
        if context and "custom_template" in context:
            template = context["custom_template"]
        
        # Get format specification and example
        format_spec = self._get_format_specification(output_format, context)
        format_example = self._get_format_example(output_format, context)
        
        # Prepare template variables
        template_vars = {
            "text": text,
            "format_specification": format_spec,
            "format_example": format_example,
            "include_schema": self.include_schema,
            "use_prefilling": self.use_prefilling,
            "error_handling": self.error_handling,
            "temperature_instruction": self.temperature_override == 0.0,
            "hierarchical_generation": self.hierarchical_generation
        }
        
        # Add format-specific variables
        if context:
            if "schema" in context:
                template_vars["schema"] = context["schema"]
            if "csv_config" in context:
                template_vars["csv_config"] = context["csv_config"]
            if "table_style" in context:
                template_vars["table_style"] = context["table_style"]
            if "markdown_features" in context:
                template_vars["markdown_features"] = context["markdown_features"]
            if "custom_requirements" in context:
                template_vars["custom_requirements"] = context["custom_requirements"]
        
        return self.render_template(template, template_vars)
    
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
        """Get enhanced format specification based on output type and context"""
        if context and "custom_format" in context:
            return context["custom_format"]
        
        # Check for schema-based specification
        if context and "schema" in context and output_format in ["json", "xml"]:
            return self._generate_schema_specification(output_format, context["schema"])
        
        # Enhanced format specifications with better structure
        format_specs = {
            "json": """```json
{
  "response_type": "string (analysis|summary|classification|generation|etc)",
  "content": {
    "main_message": "Primary response content",
    "supporting_details": [
      "Detail 1 with evidence",
      "Detail 2 with explanation"
    ],
    "structured_data": {
      "key_metrics": {},
      "relationships": [],
      "categories": []
    }
  },
  "metadata": {
    "confidence_score": 0.0-1.0,
    "reasoning_steps": ["step1", "step2"],
    "assumptions": [],
    "limitations": []
  },
  "next_steps": ["Optional actionable items"]
}
```""",
            "xml": """```xml
<?xml version="1.0" encoding="UTF-8"?>
<response type="analysis">
  <summary>
    <main_point>Primary message</main_point>
    <confidence>0.95</confidence>
  </summary>
  <details>
    <detail id="1" priority="high">
      <description>First key detail</description>
      <evidence>Supporting evidence</evidence>
    </detail>
    <detail id="2" priority="medium">
      <description>Second detail</description>
      <evidence>Supporting data</evidence>
    </detail>
  </details>
  <metadata>
    <timestamp>ISO-8601 timestamp</timestamp>
    <version>1.0</version>
  </metadata>
</response>
```""",
            "yaml": """```yaml
response_type: analysis
content:
  main_message: Primary response content
  supporting_details:
    - point: First key point
      evidence: Supporting evidence
      confidence: high
    - point: Second point
      evidence: Data or reasoning
      confidence: medium
  structured_data:
    metrics:
      accuracy: 0.95
      coverage: 0.88
    categories:
      - name: Category 1
        items: []
metadata:
  confidence_score: 0.92
  reasoning_steps:
    - Analyzed input data
    - Applied domain knowledge
    - Generated structured output
  assumptions:
    - Input data is representative
  limitations:
    - Limited to available context
```""",
            "csv": """Type,Category,Description,Value,Confidence,Notes
summary,main,Primary finding,<value>,0.95,Based on analysis
detail,supporting,First detail,<value>,0.90,Evidence included
detail,supporting,Second detail,<value>,0.85,Additional context
metric,performance,Accuracy,0.92,0.99,Validated
metric,performance,Speed,<value>,0.95,Optimized""",
            "table": """| Category    | Item              | Description                    | Status    | Priority |
|-------------|-------------------|--------------------------------|-----------|----------|
| Analysis    | Main Finding      | Primary insight from data      | Confirmed | High     |
| Supporting  | Evidence 1        | First supporting evidence      | Verified  | High     |
| Supporting  | Evidence 2        | Additional supporting data     | Probable  | Medium   |
| Action      | Recommendation 1  | Primary recommended action     | Pending   | High     |
| Metadata    | Confidence        | Overall confidence level: 0.92 | -         | -        |""",
            "markdown": """# Response Title

## Executive Summary
Brief overview of the main findings or response content.

## Detailed Analysis

### Main Points
1. **First Key Point**
   - Supporting detail with evidence
   - Additional context or explanation
   
2. **Second Key Point**
   - Evidence-based observation
   - Implications or connections

### Supporting Data
| Metric | Value | Confidence |
|--------|-------|------------|
| Metric1| Value1| High       |
| Metric2| Value2| Medium     |

## Conclusions
- Primary conclusion based on analysis
- Secondary insights

## Recommendations
1. First actionable recommendation
2. Second recommendation with rationale

---
*Confidence Level: 0.92 | Generated: [timestamp]*"""
        }
        
        return format_specs.get(output_format, self._get_generic_structure())
    
    def _get_format_example(self, output_format: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Get enhanced format example based on context"""
        if context and "example" in context:
            return f"Example:\n{context['example']}"
            
        if context and "schema" in context and output_format in ["json", "xml"]:
            return self._generate_schema_example(output_format, context["schema"])
        
        # Task-aware examples
        task_type = context.get("task_type", "general") if context else "general"
        
        examples = {
            "json": self._get_json_example(task_type),
            "xml": self._get_xml_example(task_type),
            "yaml": self._get_yaml_example(task_type),
            "csv": """Example for data analysis:
Type,Category,Description,Value,Confidence,Notes
summary,analysis,Market share increased,15%,0.95,Q4 2023 data
detail,trend,Mobile usage growing,+23%,0.92,Year-over-year
detail,risk,Desktop declining,-8%,0.88,Gradual shift
metric,kpi,User retention,87%,0.97,Above target
action,recommendation,Prioritize mobile,High,0.90,Strategic focus""",
            "table": """Example for decision matrix:
| Factor          | Option A         | Option B         | Option C         | Weight |
|-----------------|------------------|------------------|------------------|--------|
| Cost            | $10,000 (Low)    | $25,000 (Medium) | $50,000 (High)   | 30%    |
| Time to Market  | 2 months (Fast)  | 4 months (Avg)   | 6 months (Slow)  | 25%    |
| Scalability     | High             | Medium           | Very High        | 25%    |
| Risk Level      | Low              | Medium           | High             | 20%    |
| Recommendation  | ✓ Best overall   | Good compromise  | Future option    | -      |""",
            "markdown": """Example for technical analysis:
# API Performance Analysis

## Executive Summary
API response times have improved by 35% following optimization efforts, with p95 latency now under 200ms.

## Detailed Findings

### Performance Metrics
1. **Response Time Improvements**
   - Average: 145ms → 94ms (-35%)
   - P95: 312ms → 198ms (-37%)
   - P99: 520ms → 340ms (-35%)

2. **Throughput Gains**
   - Requests/second: 1,200 → 1,850 (+54%)
   - Concurrent connections: 500 → 750 (+50%)

### Key Optimizations
| Optimization | Impact | Implementation Effort |
|--------------|--------|----------------------|
| Caching layer | -40ms | Medium |
| Query optimization | -25ms | Low |
| Connection pooling | -20ms | Low |

## Recommendations
1. Implement Redis caching for frequently accessed data
2. Add database read replicas for further scaling
3. Monitor cache hit rates and adjust TTL values

---
*Analysis Date: 2024-01-15 | Confidence: High (0.93)*"""
        }
        
        return examples.get(output_format, self._get_generic_example())
    
    def _get_json_example(self, task_type: str) -> str:
        """Get task-specific JSON example"""
        examples = {
            "analysis": """Example for data analysis:
```json
{
  "response_type": "analysis",
  "content": {
    "main_message": "Sales increased 23% year-over-year, driven primarily by new product launches",
    "supporting_details": [
      "Q4 revenue reached $12.5M, exceeding targets by 15%",
      "New product line contributed 40% of growth"
    ],
    "structured_data": {
      "key_metrics": {
        "revenue_growth": 0.23,
        "market_share": 0.18,
        "customer_retention": 0.87
      },
      "trends": [
        {"period": "Q4", "growth": 0.15, "driver": "holiday sales"},
        {"period": "Q3", "growth": 0.08, "driver": "back-to-school"}
      ]
    }
  },
  "metadata": {
    "confidence_score": 0.92,
    "data_quality": "high",
    "analysis_date": "2024-01-15"
  }
}
```""",
            "classification": """Example for classification task:
```json
{
  "response_type": "classification",
  "content": {
    "primary_category": "Technical Issue",
    "subcategories": ["Software", "Performance"],
    "confidence_scores": {
      "Technical Issue": 0.89,
      "User Error": 0.08,
      "Feature Request": 0.03
    },
    "key_indicators": [
      "Error message mentioned",
      "Performance degradation described",
      "Technical terms used"
    ]
  },
  "metadata": {
    "model_version": "2.1.0",
    "classification_timestamp": "2024-01-15T10:30:00Z"
  }
}
```""",
            "general": """Example response:
```json
{
  "response_type": "structured_response",
  "content": {
    "main_message": "Your primary response here",
    "supporting_details": [
      "First supporting point with evidence",
      "Second supporting point with context"
    ],
    "structured_data": {
      "relevant_info": "Organized data as needed"
    }
  },
  "metadata": {
    "confidence_score": 0.88,
    "processing_time": "1.2s"
  }
}
```"""
        }
        return examples.get(task_type, examples["general"])
    
    def _get_xml_example(self, task_type: str) -> str:
        """Get task-specific XML example"""
        return """Example for analysis response:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<response type="analysis" version="1.0">
  <summary>
    <main_point>System performance improved by 40% after optimization</main_point>
    <confidence>0.94</confidence>
    <timestamp>2024-01-15T10:30:00Z</timestamp>
  </summary>
  <details>
    <detail id="1" priority="high">
      <description>Database query optimization</description>
      <evidence>Query time reduced from 500ms to 50ms</evidence>
      <impact>Major performance gain</impact>
    </detail>
    <detail id="2" priority="medium">
      <description>Caching implementation</description>
      <evidence>Cache hit rate at 85%</evidence>
      <impact>Reduced database load</impact>
    </detail>
  </details>
  <recommendations>
    <recommendation priority="1">
      <action>Implement connection pooling</action>
      <expected_benefit>Additional 20% improvement</expected_benefit>
    </recommendation>
  </recommendations>
</response>
```"""
    
    def _get_yaml_example(self, task_type: str) -> str:
        """Get task-specific YAML example"""
        return """Example for configuration analysis:
```yaml
response_type: configuration_analysis
content:
  main_message: Security configuration requires attention
  issues_found:
    - issue: Weak password policy
      severity: high
      recommendation: Enforce minimum 12 characters with complexity
    - issue: Outdated TLS version
      severity: medium
      recommendation: Update to TLS 1.3
  current_status:
    security_score: 0.72
    compliant_settings: 18
    total_settings: 25
    last_audit: 2024-01-10
metadata:
  scan_date: 2024-01-15
  scanner_version: 3.2.1
  confidence: 0.91
next_steps:
  - Update password policy immediately
  - Schedule TLS upgrade within 30 days
  - Re-run security scan after changes
```"""
    
    def _generate_schema_specification(self, output_format: str, schema: Dict[str, Any]) -> str:
        """Generate format specification from schema"""
        if output_format == "json":
            return f"Required JSON Schema:\n```json\n{json.dumps(schema, indent=2)}\n```"
        elif output_format == "xml":
            # Convert JSON schema to XML structure description
            return self._json_schema_to_xml_description(schema)
        return ""
    
    def _generate_schema_example(self, output_format: str, schema: Dict[str, Any]) -> str:
        """Generate example from schema"""
        if output_format == "json":
            example = self._generate_json_from_schema(schema)
            return f"Example based on schema:\n```json\n{json.dumps(example, indent=2)}\n```"
        elif output_format == "xml":
            example = self._generate_xml_from_schema(schema)
            return f"Example based on schema:\n```xml\n{example}\n```"
        return ""
    
    def _generate_json_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON example from JSON Schema"""
        if "properties" in schema:
            example = {}
            for key, prop in schema["properties"].items():
                example[key] = self._get_schema_example_value(prop)
            return example
        elif "type" in schema:
            return self._get_schema_example_value(schema)
        return {}
    
    def _get_schema_example_value(self, prop: Dict[str, Any]) -> Any:
        """Get example value from schema property"""
        prop_type = prop.get("type", "string")
        
        if "example" in prop:
            return prop["example"]
        elif "default" in prop:
            return prop["default"]
        elif "enum" in prop:
            return prop["enum"][0]
        elif prop_type == "string":
            return prop.get("description", "example string")
        elif prop_type == "number" or prop_type == "integer":
            return prop.get("minimum", 42)
        elif prop_type == "boolean":
            return True
        elif prop_type == "array":
            item_schema = prop.get("items", {"type": "string"})
            return [self._get_schema_example_value(item_schema)]
        elif prop_type == "object":
            return self._generate_json_from_schema(prop)
        
        return "example"
    
    def _json_schema_to_xml_description(self, schema: Dict[str, Any]) -> str:
        """Convert JSON schema to XML structure description"""
        xml_desc = ["XML Structure based on schema:"]
        xml_desc.append("```xml")
        xml_desc.append('<?xml version="1.0" encoding="UTF-8"?>')
        xml_desc.append("<root>")
        
        if "properties" in schema:
            for key, prop in schema["properties"].items():
                xml_desc.append(f"  <{key}>{self._get_xml_type_desc(prop)}</{key}>")
        
        xml_desc.append("</root>")
        xml_desc.append("```")
        return "\n".join(xml_desc)
    
    def _get_xml_type_desc(self, prop: Dict[str, Any]) -> str:
        """Get XML type description from property"""
        prop_type = prop.get("type", "string")
        desc = prop.get("description", "")
        
        if prop_type == "array":
            return f"<item>...</item> <!-- {desc} -->"
        elif prop_type == "object":
            return f"<!-- nested structure: {desc} -->"
        else:
            return f"{prop_type} value <!-- {desc} -->"
    
    def _generate_xml_from_schema(self, schema: Dict[str, Any]) -> str:
        """Generate XML example from schema"""
        # Simple XML generation - could be enhanced
        return """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <!-- Generated from schema -->
  <data>Example based on provided schema</data>
</response>"""
    
    def _get_generic_structure(self) -> str:
        """Get generic structure specification"""
        return """Organize your response with:
1. A clear main message or summary
2. Supporting details with evidence
3. Any relevant metadata or confidence indicators
4. Structured data in a logical format"""
    
    def _get_generic_example(self) -> str:
        """Get generic example"""
        return """Example of well-structured output:

Main Finding: [Your primary insight or response]

Supporting Evidence:
- Point 1: [Evidence or detail]
- Point 2: [Additional support]

Additional Context:
[Any relevant metadata, confidence levels, or limitations]"""
    
    def validate_output(self, output: str, output_format: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate structured output against format and schema"""
        validation_result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "parsed_data": None
        }
        
        try:
            if output_format == "json":
                # Extract JSON from code blocks if present
                json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = output
                
                parsed = json.loads(json_str)
                validation_result["parsed_data"] = parsed
                
                # Validate against schema if provided
                if schema:
                    schema_errors = self._validate_json_schema(parsed, schema)
                    validation_result["errors"].extend(schema_errors)
                
                validation_result["valid"] = len(validation_result["errors"]) == 0
                
            elif output_format == "xml":
                # Extract XML from code blocks if present
                xml_match = re.search(r'```xml\s*(.*?)\s*```', output, re.DOTALL)
                if xml_match:
                    xml_str = xml_match.group(1)
                else:
                    xml_str = output
                
                root = ET.fromstring(xml_str)
                validation_result["valid"] = True
                validation_result["parsed_data"] = root
                
            elif output_format == "yaml":
                # Extract YAML from code blocks if present
                yaml_match = re.search(r'```yaml\s*(.*?)\s*```', output, re.DOTALL)
                if yaml_match:
                    yaml_str = yaml_match.group(1)
                else:
                    yaml_str = output
                
                parsed = yaml.safe_load(yaml_str)
                validation_result["parsed_data"] = parsed
                validation_result["valid"] = True
                
        except json.JSONDecodeError as e:
            validation_result["errors"].append(f"Invalid JSON: {str(e)}")
        except ET.ParseError as e:
            validation_result["errors"].append(f"Invalid XML: {str(e)}")
        except yaml.YAMLError as e:
            validation_result["errors"].append(f"Invalid YAML: {str(e)}")
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _validate_json_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate JSON data against schema (simplified version)"""
        errors = []
        
        if "required" in schema:
            for required_field in schema["required"]:
                if required_field not in data:
                    errors.append(f"Missing required field: {required_field}")
        
        if "properties" in schema:
            for key, prop in schema["properties"].items():
                if key in data:
                    value = data[key]
                    expected_type = prop.get("type")
                    
                    if expected_type and not self._check_type(value, expected_type):
                        errors.append(f"Field '{key}' has wrong type. Expected: {expected_type}")
        
        return errors
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected = type_map.get(expected_type)
        if expected:
            return isinstance(value, expected)
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get enhanced metadata including configuration details"""
        metadata = super().get_metadata()
        metadata.update({
            "supported_formats": list(self.templates.keys()),
            "strict_mode": self.strict_mode,
            "use_prefilling": self.use_prefilling,
            "hierarchical_generation": self.hierarchical_generation,
            "error_handling": self.error_handling,
            "features": [
                "schema_validation",
                "format_templates", 
                "task_aware_examples",
                "error_recovery",
                "prefilling_hints"
            ]
        })
        return metadata