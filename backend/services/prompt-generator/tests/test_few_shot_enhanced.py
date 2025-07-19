import pytest
from unittest.mock import MagicMock, patch
from app.techniques.few_shot import FewShotTechnique


class TestFewShotTechnique:
    """Comprehensive tests for the enhanced FewShotTechnique"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.base_config = {
            "name": "few_shot",
            "enabled": True,
            "priority": 1,
            "parameters": {}
        }
    
    def test_initialization_default_parameters(self):
        """Test initialization with default parameters"""
        technique = FewShotTechnique(self.base_config)
        
        assert technique.min_examples == 2
        assert technique.max_examples == 5
        assert technique.optimal_examples == 3
        assert technique.format_style == "input_output"
        assert technique.delimiter == "###"
        assert technique.include_explanations is True
        assert technique.randomize_order is False
        assert technique.use_chain_of_thought is False
    
    def test_initialization_custom_parameters(self):
        """Test initialization with custom parameters"""
        config = self.base_config.copy()
        config["parameters"] = {
            "min_examples": 1,
            "max_examples": 10,
            "optimal_examples": 5,
            "format_style": "xml",
            "delimiter": "---",
            "include_explanations": False,
            "randomize_order": True,
            "use_chain_of_thought": True
        }
        
        technique = FewShotTechnique(config)
        
        assert technique.min_examples == 1
        assert technique.max_examples == 10
        assert technique.optimal_examples == 5
        assert technique.format_style == "xml"
        assert technique.delimiter == "---"
        assert technique.include_explanations is False
        assert technique.randomize_order is True
        assert technique.use_chain_of_thought is True
    
    def test_format_templates(self):
        """Test different format templates"""
        # Test INPUT/OUTPUT format
        config = self.base_config.copy()
        config["parameters"] = {"format_style": "input_output"}
        technique = FewShotTechnique(config)
        assert "INPUT:" in technique.template
        assert "OUTPUT:" in technique.template
        
        # Test XML format
        config["parameters"] = {"format_style": "xml"}
        technique = FewShotTechnique(config)
        assert "<example" in technique.template
        assert "<input>" in technique.template
        assert "<output>" in technique.template
        
        # Test delimiter format
        config["parameters"] = {"format_style": "delimiter", "delimiter": "###"}
        technique = FewShotTechnique(config)
        assert "###" in technique.template
    
    def test_apply_with_custom_examples(self):
        """Test apply method with custom examples"""
        technique = FewShotTechnique(self.base_config)
        
        context = {
            "examples": [
                {"input": "2+2", "output": "4", "explanation": "Basic addition"},
                {"input": "5*3", "output": "15", "explanation": "Basic multiplication"},
                {"input": "10/2", "output": "5", "explanation": "Basic division"}
            ]
        }
        
        result = technique.apply("7+3", context)
        
        assert "2+2" in result
        assert "4" in result
        assert "5*3" in result
        assert "15" in result
        assert "7+3" in result
        assert "Basic addition" in result
    
    def test_apply_with_task_type(self):
        """Test apply method with task type"""
        technique = FewShotTechnique(self.base_config)
        
        context = {"task_type": "classification"}
        result = technique.apply("This product is amazing!", context)
        
        # Should contain classification examples
        assert "Positive" in result
        assert "Negative" in result
        assert "This product is amazing!" in result
    
    def test_apply_without_examples(self):
        """Test apply method without examples"""
        technique = FewShotTechnique(self.base_config)
        
        result = technique.apply("Test input", {})
        
        # Should fallback to instruction-based prompt
        assert "Test input" in result
        assert "Please" in result  # Fallback contains polite instruction
    
    def test_example_selection_by_similarity(self):
        """Test similarity-based example selection"""
        technique = FewShotTechnique(self.base_config)
        technique.max_examples = 2
        
        context = {
            "examples": [
                {"input": "Python programming", "output": "High-level language"},
                {"input": "Machine learning", "output": "AI subset"},
                {"input": "Coffee brewing", "output": "Hot beverage preparation"},
                {"input": "Python syntax", "output": "Code structure"},
                {"input": "Data science", "output": "Analytics field"}
            ]
        }
        
        result = technique.apply("Python coding tips", context)
        
        # Should prefer Python-related examples
        assert "Python programming" in result or "Python syntax" in result
        # Coffee brewing should be less likely to appear
        assert result.count("Coffee brewing") <= result.count("Python")
    
    def test_chain_of_thought_enhancement(self):
        """Test chain-of-thought enhancement"""
        config = self.base_config.copy()
        config["parameters"] = {"use_chain_of_thought": True}
        technique = FewShotTechnique(config)
        
        context = {
            "examples": [
                {"input": "2+2", "output": "4"},  # No explanation
                {"input": "5*3", "output": "15", "explanation": "Existing explanation"}
            ]
        }
        
        result = technique.apply("7+3", context)
        
        # All examples should have explanations now
        assert result.count("REASONING:") >= 1 or result.count("explanation") >= 1
    
    def test_smart_randomization(self):
        """Test smart randomization of examples"""
        config = self.base_config.copy()
        config["parameters"] = {"randomize_order": True}
        technique = FewShotTechnique(config)
        
        context = {
            "examples": [
                {"input": "Best example", "output": "A"},
                {"input": "Good example", "output": "B"},
                {"input": "OK example", "output": "C"},
                {"input": "Another example", "output": "D"}
            ]
        }
        
        # Run multiple times to check randomization
        results = []
        for _ in range(5):
            result = technique.apply("Test", context)
            results.append(result)
        
        # First example should always be first (best example)
        for result in results:
            assert result.index("Best example") < result.index("Good example")
        
        # Other examples should vary in order
        # This is probabilistic, so we just check that we get some variation
        assert len(set(results)) > 1
    
    def test_validate_input_success(self):
        """Test input validation success cases"""
        technique = FewShotTechnique(self.base_config)
        
        # Valid with custom examples
        context = {
            "examples": [
                {"input": "A", "output": "1"},
                {"input": "B", "output": "2"}
            ]
        }
        assert technique.validate_input("Test input", context) is True
        
        # Valid with task type
        assert technique.validate_input("Test input", {"task_type": "classification"}) is True
    
    def test_validate_input_failure(self):
        """Test input validation failure cases"""
        technique = FewShotTechnique(self.base_config)
        
        # Too short input
        assert technique.validate_input("", {}) is False
        assert technique.validate_input("  ", {}) is False
        
        # Too few examples
        context = {"examples": [{"input": "A", "output": "1"}]}
        assert technique.validate_input("Test", context) is False
        
        # Invalid example structure
        context = {"examples": ["Not a dict"]}
        assert technique.validate_input("Test", context) is False
        
        # Missing required fields
        context = {"examples": [{"input": "A"}, {"output": "B"}]}
        assert technique.validate_input("Test", context) is False
        
        # No examples or task type
        assert technique.validate_input("Test", {}) is False
    
    def test_get_default_examples(self):
        """Test default example retrieval"""
        technique = FewShotTechnique(self.base_config)
        
        # Test known task types
        for task_type in ["classification", "summarization", "translation", 
                         "code_generation", "question_answering", "analysis", 
                         "generation", "reasoning"]:
            examples = technique._get_default_examples(task_type)
            assert len(examples) > 0
            assert all(isinstance(ex, dict) for ex in examples)
            assert all("input" in ex and "output" in ex for ex in examples)
        
        # Test unknown task type (should return generic examples)
        examples = technique._get_default_examples("unknown_task")
        assert len(examples) > 0
        assert all(isinstance(ex, dict) for ex in examples)
    
    def test_get_metadata(self):
        """Test metadata retrieval"""
        config = self.base_config.copy()
        config["parameters"] = {
            "min_examples": 3,
            "max_examples": 7,
            "format_style": "xml"
        }
        technique = FewShotTechnique(config)
        
        metadata = technique.get_metadata()
        
        assert metadata["name"] == "few_shot"
        assert metadata["min_examples"] == 3
        assert metadata["max_examples"] == 7
        assert metadata["format_style"] == "xml"
        assert "supported_task_types" in metadata
        assert len(metadata["supported_task_types"]) > 0
    
    def test_fallback_prompt_generation(self):
        """Test fallback prompt generation"""
        technique = FewShotTechnique(self.base_config)
        
        # Test with task type
        prompt = technique._create_fallback_prompt("Analyze this data", {"task_type": "analysis"})
        assert "analyze" in prompt.lower()
        assert "Analyze this data" in prompt
        
        # Test without task type
        prompt = technique._create_fallback_prompt("Do something", {})
        assert "Do something" in prompt
        assert "Please" in prompt
    
    def test_xml_format_rendering(self):
        """Test XML format rendering"""
        config = self.base_config.copy()
        config["parameters"] = {"format_style": "xml"}
        technique = FewShotTechnique(config)
        
        context = {
            "examples": [
                {"input": "Test input", "output": "Test output", "explanation": "Test explanation"}
            ]
        }
        
        result = technique.apply("New input", context)
        
        assert '<example number="1">' in result
        assert '<input>Test input</input>' in result
        assert '<output>Test output</output>' in result
        assert '<reasoning>Test explanation</reasoning>' in result
        assert '<input>New input</input>' in result
    
    def test_delimiter_format_rendering(self):
        """Test delimiter format rendering"""
        config = self.base_config.copy()
        config["parameters"] = {"format_style": "delimiter", "delimiter": "***"}
        technique = FewShotTechnique(config)
        
        context = {
            "examples": [
                {"input": "Question", "output": "Answer", "explanation": "Because..."}
            ]
        }
        
        result = technique.apply("My question", context)
        
        assert "*** Example 1 ***" in result
        assert "Query: Question" in result
        assert "Response: Answer" in result
        assert "Rationale: Because..." in result
        assert "*** Your Task ***" in result
        assert "Query: My question" in result
    
    @patch('structlog.get_logger')
    def test_logging(self, mock_logger):
        """Test logging functionality"""
        mock_logger_instance = MagicMock()
        mock_logger.return_value.bind.return_value = mock_logger_instance
        
        technique = FewShotTechnique(self.base_config)
        technique.logger = mock_logger_instance
        
        # Test warning for no examples
        technique.apply("Test", {})
        mock_logger_instance.warning.assert_called()
        
        # Test info for using custom examples
        technique.apply("Test", {"examples": [{"input": "A", "output": "1"}, {"input": "B", "output": "2"}]})
        mock_logger_instance.info.assert_called()