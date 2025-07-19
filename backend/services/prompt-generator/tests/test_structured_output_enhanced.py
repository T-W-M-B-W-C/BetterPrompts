import pytest
import json
import yaml
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree as ET
from app.techniques.structured_output import StructuredOutputTechnique


class TestStructuredOutputTechnique:
    """Comprehensive tests for the enhanced StructuredOutputTechnique"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.base_config = {
            "name": "structured_output",
            "enabled": True,
            "priority": 1,
            "parameters": {}
        }
    
    def test_initialization_default_parameters(self):
        """Test initialization with default parameters"""
        technique = StructuredOutputTechnique(self.base_config)
        
        assert technique.strict_mode is True
        assert technique.use_prefilling is True
        assert technique.hierarchical_generation is False
        assert technique.include_schema is True
        assert technique.error_handling == "explicit"
        assert technique.temperature_override == 0.0
        assert len(technique.templates) == 7  # json, xml, yaml, csv, table, markdown, custom
    
    def test_initialization_custom_parameters(self):
        """Test initialization with custom parameters"""
        config = self.base_config.copy()
        config["parameters"] = {
            "strict_mode": False,
            "use_prefilling": False,
            "hierarchical_generation": True,
            "include_schema": False,
            "error_handling": "implicit",
            "temperature_override": 0.7
        }
        
        technique = StructuredOutputTechnique(config)
        
        assert technique.strict_mode is False
        assert technique.use_prefilling is False
        assert technique.hierarchical_generation is True
        assert technique.include_schema is False
        assert technique.error_handling == "implicit"
        assert technique.temperature_override == 0.7
    
    def test_json_template_generation(self):
        """Test JSON template generation with various options"""
        technique = StructuredOutputTechnique(self.base_config)
        
        context = {
            "output_format": "json",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                },
                "required": ["name"]
            }
        }
        
        result = technique.apply("Generate user data", context)
        
        # Check for key JSON template elements
        assert "valid JSON" in result
        assert "json.loads()" in result
        assert "```json" in result  # Prefilling hint
        assert "Required JSON Schema:" in result
        assert '"name"' in result  # Schema should be included
        
    def test_xml_template_generation(self):
        """Test XML template generation"""
        config = self.base_config.copy()
        config["parameters"] = {"use_prefilling": True}
        technique = StructuredOutputTechnique(config)
        
        context = {"output_format": "xml"}
        result = technique.apply("Generate XML response", context)
        
        assert "valid XML format" in result
        assert "<response>" in result  # Prefilling hint
        assert "<?xml version" in result
        assert "&lt; &gt; &amp;" in result  # Escape characters mentioned
    
    def test_yaml_template_generation(self):
        """Test YAML template generation"""
        technique = StructuredOutputTechnique(self.base_config)
        
        context = {"output_format": "yaml"}
        result = technique.apply("Generate config", context)
        
        assert "valid YAML format" in result
        assert "```yaml" in result  # Prefilling hint
        assert "2 spaces" in result  # Indentation requirement
        assert "YAML 1.2" in result
    
    def test_csv_template_with_config(self):
        """Test CSV template with custom configuration"""
        technique = StructuredOutputTechnique(self.base_config)
        
        context = {
            "output_format": "csv",
            "csv_config": {
                "delimiter": ";",
                "quote_char": "'",
                "include_headers": "yes"
            }
        }
        
        result = technique.apply("Generate CSV data", context)
        
        assert "CSV format" in result
        assert "Delimiter: ;" in result
        assert "Quote character: '" in result
        assert "column headers" in result
    
    def test_table_template_with_style(self):
        """Test table template with style specification"""
        technique = StructuredOutputTechnique(self.base_config)
        
        context = {
            "output_format": "table",
            "table_style": "github-markdown"
        }
        
        result = technique.apply("Generate table", context)
        
        assert "formatted table" in result
        assert "Table style: github-markdown" in result
        assert "consistent column widths" in result
    
    def test_markdown_template_with_features(self):
        """Test markdown template with feature requirements"""
        technique = StructuredOutputTechnique(self.base_config)
        
        context = {
            "output_format": "markdown",
            "markdown_features": ["tables", "code blocks", "links", "headings"]
        }
        
        result = technique.apply("Generate documentation", context)
        
        assert "Markdown format" in result
        assert "- tables" in result
        assert "- code blocks" in result
        assert "# ## ###" in result  # Heading levels
    
    def test_custom_template(self):
        """Test custom template usage"""
        technique = StructuredOutputTechnique(self.base_config)
        
        context = {
            "output_format": "custom",
            "custom_format": "Custom Format Specification",
            "custom_requirements": "Must include timestamps"
        }
        
        result = technique.apply("Generate custom output", context)
        
        assert "custom format" in result
        assert "Custom Format Specification" in result
        assert "Must include timestamps" in result
    
    def test_schema_based_json_example(self):
        """Test JSON example generation from schema"""
        technique = StructuredOutputTechnique(self.base_config)
        
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 123},
                "name": {"type": "string", "default": "John Doe"},
                "active": {"type": "boolean"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "created": {"type": "string"}
                    }
                }
            },
            "required": ["id", "name"]
        }
        
        context = {
            "output_format": "json",
            "schema": schema
        }
        
        result = technique.apply("Generate user", context)
        
        # Schema should be included
        assert "Required JSON Schema:" in result
        assert '"required": ["id", "name"]' in result
        
        # Example should be generated from schema
        assert "123" in result  # example value
        assert "John Doe" in result  # default value
    
    def test_task_aware_examples(self):
        """Test task-specific example generation"""
        technique = StructuredOutputTechnique(self.base_config)
        
        # Test analysis task
        context = {
            "output_format": "json",
            "task_type": "analysis"
        }
        result = technique.apply("Analyze sales data", context)
        assert "response_type\": \"analysis\"" in result
        assert "key_metrics" in result
        
        # Test classification task
        context["task_type"] = "classification"
        result = technique.apply("Classify this text", context)
        assert "response_type\": \"classification\"" in result
        assert "confidence_scores" in result
    
    def test_error_handling_modes(self):
        """Test different error handling modes"""
        # Explicit error handling
        technique = StructuredOutputTechnique(self.base_config)
        context = {"output_format": "json"}
        result = technique.apply("Parse this", context)
        assert '"error": true' in result
        assert "reason" in result
        
        # Implicit error handling
        config = self.base_config.copy()
        config["parameters"] = {"error_handling": "implicit"}
        technique = StructuredOutputTechnique(config)
        result = technique.apply("Parse this", context)
        # Should not include explicit error format
        assert '"error": true' not in result
    
    def test_hierarchical_generation(self):
        """Test hierarchical generation mode"""
        config = self.base_config.copy()
        config["parameters"] = {"hierarchical_generation": True}
        technique = StructuredOutputTechnique(config)
        
        context = {"output_format": "xml"}
        result = technique.apply("Generate complex XML", context)
        
        assert "Generate top-level structure first" in result
    
    def test_temperature_instruction(self):
        """Test temperature override instruction"""
        technique = StructuredOutputTechnique(self.base_config)
        
        context = {"output_format": "json"}
        result = technique.apply("Generate data", context)
        
        assert "temperature=0" in result
        assert "deterministic generation" in result
    
    def test_validate_output_json(self):
        """Test JSON output validation"""
        technique = StructuredOutputTechnique(self.base_config)
        
        # Valid JSON
        valid_json = '{"name": "test", "value": 42}'
        result = technique.validate_output(valid_json, "json")
        assert result["valid"] is True
        assert result["parsed_data"]["name"] == "test"
        
        # Valid JSON in code block
        json_with_block = '```json\n{"status": "ok"}\n```'
        result = technique.validate_output(json_with_block, "json")
        assert result["valid"] is True
        assert result["parsed_data"]["status"] == "ok"
        
        # Invalid JSON
        invalid_json = '{"incomplete": '
        result = technique.validate_output(invalid_json, "json")
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "Invalid JSON" in result["errors"][0]
    
    def test_validate_output_with_schema(self):
        """Test JSON validation against schema"""
        technique = StructuredOutputTechnique(self.base_config)
        
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        
        # Valid according to schema
        valid_data = '{"name": "Alice", "age": 30}'
        result = technique.validate_output(valid_data, "json", schema)
        assert result["valid"] is True
        
        # Missing required field
        missing_field = '{"age": 30}'
        result = technique.validate_output(missing_field, "json", schema)
        assert result["valid"] is False
        assert "Missing required field: name" in result["errors"]
        
        # Wrong type
        wrong_type = '{"name": "Bob", "age": "thirty"}'
        result = technique.validate_output(wrong_type, "json", schema)
        assert result["valid"] is False
        assert "wrong type" in str(result["errors"])
    
    def test_validate_output_xml(self):
        """Test XML output validation"""
        technique = StructuredOutputTechnique(self.base_config)
        
        # Valid XML
        valid_xml = '<?xml version="1.0"?><root><item>test</item></root>'
        result = technique.validate_output(valid_xml, "xml")
        assert result["valid"] is True
        assert result["parsed_data"] is not None
        
        # Valid XML in code block
        xml_with_block = '```xml\n<data>value</data>\n```'
        result = technique.validate_output(xml_with_block, "xml")
        assert result["valid"] is True
        
        # Invalid XML
        invalid_xml = '<unclosed>'
        result = technique.validate_output(invalid_xml, "xml")
        assert result["valid"] is False
        assert "Invalid XML" in result["errors"][0]
    
    def test_validate_output_yaml(self):
        """Test YAML output validation"""
        technique = StructuredOutputTechnique(self.base_config)
        
        # Valid YAML
        valid_yaml = 'name: test\nvalue: 42'
        result = technique.validate_output(valid_yaml, "yaml")
        assert result["valid"] is True
        assert result["parsed_data"]["name"] == "test"
        
        # Valid YAML in code block
        yaml_with_block = '```yaml\nstatus: ok\n```'
        result = technique.validate_output(yaml_with_block, "yaml")
        assert result["valid"] is True
        
        # Invalid YAML
        invalid_yaml = 'invalid:\n  - item\n - bad indent'
        result = technique.validate_output(invalid_yaml, "yaml")
        assert result["valid"] is False
        assert "Invalid YAML" in result["errors"][0]
    
    def test_validate_input(self):
        """Test input validation"""
        technique = StructuredOutputTechnique(self.base_config)
        
        # Should always return True (technique is always applicable)
        assert technique.validate_input("Any text", {}) is True
        assert technique.validate_input("", {}) is True
        
        # Should log when structured output would be beneficial
        with patch.object(technique.logger, 'info') as mock_logger:
            technique.validate_input("Please format this as JSON", {})
            mock_logger.assert_called_with("Structured output would be beneficial")
    
    def test_get_metadata(self):
        """Test metadata generation"""
        config = self.base_config.copy()
        config["parameters"] = {
            "strict_mode": False,
            "hierarchical_generation": True
        }
        technique = StructuredOutputTechnique(config)
        
        metadata = technique.get_metadata()
        
        assert metadata["name"] == "structured_output"
        assert "json" in metadata["supported_formats"]
        assert "xml" in metadata["supported_formats"]
        assert metadata["strict_mode"] is False
        assert metadata["hierarchical_generation"] is True
        assert "schema_validation" in metadata["features"]
        assert "prefilling_hints" in metadata["features"]
    
    def test_complex_schema_generation(self):
        """Test complex schema handling"""
        technique = StructuredOutputTechnique(self.base_config)
        
        complex_schema = {
            "type": "object",
            "properties": {
                "users": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "profile": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "email": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "pending", "disabled"]
                }
            }
        }
        
        context = {
            "output_format": "json",
            "schema": complex_schema
        }
        
        result = technique.apply("Generate user list", context)
        
        # Should include the complex schema
        assert "users" in result
        assert "profile" in result
        assert "enum" in result
    
    @patch('structlog.get_logger')
    def test_logging(self, mock_logger):
        """Test logging functionality"""
        mock_logger_instance = MagicMock()
        mock_logger.return_value.bind.return_value = mock_logger_instance
        
        technique = StructuredOutputTechnique(self.base_config)
        technique.logger = mock_logger_instance
        
        # Test format keyword detection
        technique.validate_input("Please return as JSON", {})
        mock_logger_instance.info.assert_called_with("Structured output would be beneficial")
        
        # Test error logging in schema generation
        technique._generate_json_from_schema({"invalid": "schema"})
        # Logger should not be called for this simple case