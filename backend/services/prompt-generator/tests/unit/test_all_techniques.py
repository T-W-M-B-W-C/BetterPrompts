"""
Comprehensive unit tests for all prompt engineering techniques
"""

import pytest
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from app.techniques.base import BaseTechnique, technique_registry
from app.techniques import (
    ChainOfThoughtTechnique,
    TreeOfThoughtsTechnique,
    FewShotTechnique,
    ZeroShotTechnique,
    RolePlayTechnique,
    StepByStepTechnique,
    StructuredOutputTechnique,
    EmotionalAppealTechnique,
    ConstraintsTechnique,
    AnalogicalTechnique,
    SelfConsistencyTechnique,
    ReactTechnique
)
from app.models import TechniqueType


class TestBaseTechnique:
    """Test the base technique functionality"""
    
    def test_base_technique_initialization(self):
        """Test base technique initialization"""
        config = {
            "name": "test_technique",
            "template": "Test template: {{text}}",
            "parameters": {"param1": "value1"},
            "priority": 5,
            "enabled": True
        }
        
        class TestTechnique(BaseTechnique):
            def apply(self, text, context=None):
                return text
            
            def validate_input(self, text, context=None):
                return True
                
        technique = TestTechnique(config)
        
        assert technique.name == "test_technique"
        assert technique.template == "Test template: {{text}}"
        assert technique.parameters == {"param1": "value1"}
        assert technique.priority == 5
        assert technique.enabled is True
        
    def test_render_template(self):
        """Test template rendering"""
        class TestTechnique(BaseTechnique):
            def apply(self, text, context=None):
                return self.render_template(self.template, {"text": text})
            
            def validate_input(self, text, context=None):
                return True
                
        technique = TestTechnique({
            "name": "test",
            "template": "Enhanced: {{text}} with {{param}}"
        })
        
        result = technique.render_template(
            technique.template,
            {"text": "original", "param": "value"}
        )
        
        assert result == "Enhanced: original with value"
        
    def test_render_template_error(self):
        """Test template rendering error handling"""
        class TestTechnique(BaseTechnique):
            def apply(self, text, context=None):
                return text
            
            def validate_input(self, text, context=None):
                return True
                
        technique = TestTechnique({"name": "test"})
        
        with pytest.raises(Exception):
            # Invalid template syntax
            technique.render_template("{{unclosed", {})
            
    def test_extract_template_variables(self):
        """Test template variable extraction"""
        class TestTechnique(BaseTechnique):
            def apply(self, text, context=None):
                return text
            
            def validate_input(self, text, context=None):
                return True
                
        technique = TestTechnique({"name": "test"})
        
        template = "Hello {{name}}, your score is {{score}} and rank is {{rank}}"
        variables = technique.extract_template_variables(template)
        
        assert set(variables) == {"name", "score", "rank"}
        
    def test_estimate_tokens(self):
        """Test token estimation"""
        class TestTechnique(BaseTechnique):
            def apply(self, text, context=None):
                return text
            
            def validate_input(self, text, context=None):
                return True
                
        technique = TestTechnique({"name": "test"})
        
        # Test various text lengths
        assert technique.estimate_tokens("") == 0
        assert technique.estimate_tokens("Hello world") == 2  # 11 chars / 4
        assert technique.estimate_tokens("A" * 100) == 25  # 100 / 4
        
    def test_clean_text(self):
        """Test text cleaning"""
        class TestTechnique(BaseTechnique):
            def apply(self, text, context=None):
                return text
            
            def validate_input(self, text, context=None):
                return True
                
        technique = TestTechnique({"name": "test"})
        
        # Test whitespace normalization
        assert technique.clean_text("  hello   world  ") == "hello world"
        assert technique.clean_text("line1\n\n\nline2") == "line1 line2"
        assert technique.clean_text("\t\ttabbed\t\t") == "tabbed"
        
    def test_get_metadata(self):
        """Test metadata retrieval"""
        class TestTechnique(BaseTechnique):
            def apply(self, text, context=None):
                return text
            
            def validate_input(self, text, context=None):
                return True
                
        config = {
            "name": "test_meta",
            "priority": 3,
            "enabled": False,
            "parameters": {"key": "value"}
        }
        technique = TestTechnique(config)
        
        metadata = technique.get_metadata()
        
        assert metadata["name"] == "test_meta"
        assert metadata["priority"] == 3
        assert metadata["enabled"] is False
        assert metadata["parameters"] == {"key": "value"}


class TestChainOfThoughtTechnique:
    """Test Chain of Thought technique"""
    
    @pytest.fixture
    def technique(self):
        config = {
            "name": "chain_of_thought",
            "enabled": True,
            "priority": 1
        }
        return ChainOfThoughtTechnique(config)
        
    def test_apply_basic(self, technique):
        """Test basic CoT application"""
        text = "Solve the math problem: 15 + 27"
        result = technique.apply(text)
        
        assert "step" in result.lower() or "think" in result.lower()
        assert text in result
        assert len(result) > len(text)
        
    def test_apply_with_context(self, technique):
        """Test CoT with context"""
        text = "Explain quantum computing"
        context = {
            "complexity": "complex",
            "domain": "physics"
        }
        result = technique.apply(text, context)
        
        assert "step" in result.lower() or "systematic" in result.lower()
        assert text in result
        
    def test_validate_input(self, technique):
        """Test input validation"""
        assert technique.validate_input("Valid text") is True
        assert technique.validate_input("") is False
        assert technique.validate_input("   ") is False
        assert technique.validate_input("a" * 10000) is False  # Too long
        
    def test_edge_cases(self, technique):
        """Test edge cases"""
        # Very short input
        result = technique.apply("Hi")
        assert len(result) > 2
        
        # Input with special characters
        result = technique.apply("What is 2+2=?")
        assert "2+2" in result
        
        # Multi-line input
        result = technique.apply("Line 1\nLine 2\nLine 3")
        assert result is not None


class TestTreeOfThoughtsTechnique:
    """Test Tree of Thoughts technique"""
    
    @pytest.fixture
    def technique(self):
        config = {
            "name": "tree_of_thoughts",
            "enabled": True,
            "priority": 1
        }
        return TreeOfThoughtsTechnique(config)
        
    def test_apply_basic(self, technique):
        """Test basic ToT application"""
        text = "Find the best solution for traffic congestion"
        result = technique.apply(text)
        
        assert "approach" in result.lower() or "option" in result.lower()
        assert text in result
        assert len(result) > len(text)
        
    def test_apply_with_parameters(self, technique):
        """Test ToT with custom parameters"""
        text = "Design a new product"
        context = {
            "parameters": {
                "num_branches": 3,
                "evaluation_criteria": ["feasibility", "cost", "impact"]
            }
        }
        result = technique.apply(text, context)
        
        assert result is not None
        assert len(result) > len(text)
        
    def test_validate_input(self, technique):
        """Test input validation"""
        assert technique.validate_input("Valid problem") is True
        assert technique.validate_input("") is False
        assert technique.validate_input("x" * 5001) is False


class TestFewShotTechnique:
    """Test Few-Shot learning technique"""
    
    @pytest.fixture
    def technique(self):
        config = {
            "name": "few_shot",
            "enabled": True,
            "priority": 1
        }
        return FewShotTechnique(config)
        
    def test_apply_basic(self, technique):
        """Test basic few-shot application"""
        text = "Translate 'hello' to Spanish"
        result = technique.apply(text)
        
        assert "example" in result.lower() or ":" in result
        assert text in result
        assert len(result) > len(text)
        
    def test_apply_with_examples(self, technique):
        """Test few-shot with provided examples"""
        text = "Classify the sentiment"
        context = {
            "examples": [
                {"input": "I love this!", "output": "positive"},
                {"input": "This is terrible", "output": "negative"}
            ]
        }
        result = technique.apply(text, context)
        
        assert "I love this!" in result
        assert "positive" in result
        assert "negative" in result
        
    def test_validate_input(self, technique):
        """Test input validation"""
        assert technique.validate_input("Valid text") is True
        assert technique.validate_input("") is False


class TestZeroShotTechnique:
    """Test Zero-Shot technique"""
    
    @pytest.fixture
    def technique(self):
        config = {
            "name": "zero_shot",
            "enabled": True,
            "priority": 1
        }
        return ZeroShotTechnique(config)
        
    def test_apply_basic(self, technique):
        """Test basic zero-shot application"""
        text = "What is artificial intelligence?"
        result = technique.apply(text)
        
        assert text in result
        assert len(result) >= len(text)
        
    def test_apply_with_context(self, technique):
        """Test zero-shot with context"""
        text = "Explain the concept"
        context = {
            "target_audience": "beginners",
            "tone": "friendly"
        }
        result = technique.apply(text, context)
        
        assert text in result
        
    def test_validate_input(self, technique):
        """Test input validation"""
        assert technique.validate_input("Valid question") is True
        assert technique.validate_input("") is False


class TestRolePlayTechnique:
    """Test Role Playing technique"""
    
    @pytest.fixture
    def technique(self):
        config = {
            "name": "role_play",
            "enabled": True,
            "priority": 1
        }
        return RolePlayTechnique(config)
        
    def test_apply_basic(self, technique):
        """Test basic role play application"""
        text = "Explain database design"
        result = technique.apply(text)
        
        assert "expert" in result.lower() or "professional" in result.lower()
        assert text in result
        
    def test_apply_with_role(self, technique):
        """Test role play with specific role"""
        text = "Review this code"
        context = {
            "role": "senior software engineer",
            "expertise": "Python and web development"
        }
        result = technique.apply(text, context)
        
        assert "software engineer" in result.lower() or "expert" in result.lower()
        assert text in result
        
    def test_validate_input(self, technique):
        """Test input validation"""
        assert technique.validate_input("Valid request") is True
        assert technique.validate_input("") is False


class TestStepByStepTechnique:
    """Test Step by Step technique"""
    
    @pytest.fixture
    def technique(self):
        config = {
            "name": "step_by_step",
            "enabled": True,
            "priority": 1
        }
        return StepByStepTechnique(config)
        
    def test_apply_basic(self, technique):
        """Test basic step by step application"""
        text = "How to bake a cake"
        result = technique.apply(text)
        
        assert "step" in result.lower()
        assert text in result
        assert len(result) > len(text)
        
    def test_apply_complex_task(self, technique):
        """Test step by step with complex task"""
        text = "Deploy a web application to production"
        context = {
            "num_steps": 5,
            "detail_level": "detailed"
        }
        result = technique.apply(text, context)
        
        assert "step" in result.lower()
        assert result.count("step") >= 1 or result.count("Step") >= 1
        
    def test_validate_input(self, technique):
        """Test input validation"""
        assert technique.validate_input("Valid procedure") is True
        assert technique.validate_input("") is False


class TestStructuredOutputTechnique:
    """Test Structured Output technique"""
    
    @pytest.fixture
    def technique(self):
        config = {
            "name": "structured_output",
            "enabled": True,
            "priority": 1
        }
        return StructuredOutputTechnique(config)
        
    def test_apply_basic(self, technique):
        """Test basic structured output application"""
        text = "List the pros and cons"
        result = technique.apply(text)
        
        assert any(marker in result for marker in ["-", "•", ":", "|"])
        assert text in result
        
    def test_apply_with_format(self, technique):
        """Test structured output with specific format"""
        text = "Generate user data"
        context = {
            "output_format": "json",
            "fields": ["name", "email", "age"]
        }
        result = technique.apply(text, context)
        
        assert "json" in result.lower() or "format" in result.lower()
        assert text in result
        
    def test_validate_input(self, technique):
        """Test input validation"""
        assert technique.validate_input("Valid request") is True
        assert technique.validate_input("") is False


class TestEmotionalAppealTechnique:
    """Test Emotional Appeal technique"""
    
    @pytest.fixture
    def technique(self):
        config = {
            "name": "emotional_appeal",
            "enabled": True,
            "priority": 1
        }
        return EmotionalAppealTechnique(config)
        
    def test_apply_basic(self, technique):
        """Test basic emotional appeal application"""
        text = "Help me solve this problem"
        result = technique.apply(text)
        
        emotional_markers = ["understand", "important", "together", "help", "care"]
        assert any(marker in result.lower() for marker in emotional_markers)
        assert text in result
        
    def test_apply_with_context(self, technique):
        """Test emotional appeal with context"""
        text = "I'm struggling with this"
        context = {
            "emotion": "supportive",
            "urgency": "high"
        }
        result = technique.apply(text, context)
        
        assert len(result) > len(text)
        assert any(word in result.lower() for word in ["help", "support", "together"])
        
    def test_validate_input(self, technique):
        """Test input validation"""
        assert technique.validate_input("Valid text") is True
        assert technique.validate_input("") is False


class TestConstraintsTechnique:
    """Test Constraints technique"""
    
    @pytest.fixture
    def technique(self):
        config = {
            "name": "constraints",
            "enabled": True,
            "priority": 1
        }
        return ConstraintsTechnique(config)
        
    def test_apply_basic(self, technique):
        """Test basic constraints application"""
        text = "Write a story"
        result = technique.apply(text)
        
        constraint_markers = ["must", "should", "constraint", "requirement", "limit"]
        assert any(marker in result.lower() for marker in constraint_markers)
        assert text in result
        
    def test_apply_with_constraints(self, technique):
        """Test constraints with specific requirements"""
        text = "Create a function"
        context = {
            "constraints": [
                "Must be under 50 lines",
                "Should handle errors",
                "Must be documented"
            ]
        }
        result = technique.apply(text, context)
        
        assert "50 lines" in result
        assert "errors" in result
        assert "documented" in result
        
    def test_validate_input(self, technique):
        """Test input validation"""
        assert technique.validate_input("Valid task") is True
        assert technique.validate_input("") is False


class TestAnalogicalTechnique:
    """Test Analogical Reasoning technique"""
    
    @pytest.fixture
    def technique(self):
        config = {
            "name": "analogical",
            "enabled": True,
            "priority": 1
        }
        return AnalogicalTechnique(config)
        
    def test_apply_basic(self, technique):
        """Test basic analogical application"""
        text = "Explain how neural networks work"
        result = technique.apply(text)
        
        analogy_markers = ["like", "similar", "analogy", "think of", "imagine"]
        assert any(marker in result.lower() for marker in analogy_markers)
        assert text in result
        
    def test_apply_with_domain(self, technique):
        """Test analogical with specific domain"""
        text = "Explain quantum computing"
        context = {
            "target_domain": "everyday life",
            "complexity": "simple"
        }
        result = technique.apply(text, context)
        
        assert len(result) > len(text)
        assert any(word in result.lower() for word in ["like", "similar", "think"])
        
    def test_validate_input(self, technique):
        """Test input validation"""
        assert technique.validate_input("Valid concept") is True
        assert technique.validate_input("") is False


class TestSelfConsistencyTechnique:
    """Test Self-Consistency technique"""
    
    @pytest.fixture
    def technique(self):
        config = {
            "name": "self_consistency",
            "enabled": True,
            "priority": 1
        }
        return SelfConsistencyTechnique(config)
        
    def test_apply_basic(self, technique):
        """Test basic self-consistency application"""
        text = "What is the capital of France?"
        result = technique.apply(text)
        
        consistency_markers = ["verify", "check", "multiple", "angle", "approach"]
        assert any(marker in result.lower() for marker in consistency_markers)
        assert text in result
        
    def test_apply_with_paths(self, technique):
        """Test self-consistency with multiple paths"""
        text = "Calculate the result"
        context = {
            "num_paths": 3,
            "verification_method": "cross-check"
        }
        result = technique.apply(text, context)
        
        assert len(result) > len(text)
        
    def test_validate_input(self, technique):
        """Test input validation"""
        assert technique.validate_input("Valid question") is True
        assert technique.validate_input("") is False


class TestReactTechnique:
    """Test ReAct (Reasoning and Acting) technique"""
    
    @pytest.fixture
    def technique(self):
        config = {
            "name": "react",
            "enabled": True,
            "priority": 1
        }
        return ReactTechnique(config)
        
    def test_apply_basic(self, technique):
        """Test basic ReAct application"""
        text = "Find information about climate change"
        result = technique.apply(text)
        
        react_markers = ["thought", "action", "observation", "reasoning"]
        assert any(marker in result.lower() for marker in react_markers)
        assert text in result
        
    def test_apply_with_tools(self, technique):
        """Test ReAct with tool definitions"""
        text = "Research and summarize AI trends"
        context = {
            "available_tools": ["search", "calculate", "analyze"],
            "max_iterations": 3
        }
        result = technique.apply(text, context)
        
        assert len(result) > len(text)
        assert any(word in result.lower() for word in ["thought", "action", "reason"])
        
    def test_validate_input(self, technique):
        """Test input validation"""
        assert technique.validate_input("Valid task") is True
        assert technique.validate_input("") is False


class TestTechniqueRegistry:
    """Test the technique registry functionality"""
    
    def test_register_technique(self):
        """Test registering a new technique"""
        registry = technique_registry
        
        class CustomTechnique(BaseTechnique):
            def apply(self, text, context=None):
                return f"Custom: {text}"
                
            def validate_input(self, text, context=None):
                return True
                
        # Clear any existing registration
        if "custom_test" in registry._techniques:
            del registry._techniques["custom_test"]
            
        registry.register("custom_test", CustomTechnique)
        
        assert "custom_test" in registry._techniques
        assert registry._techniques["custom_test"] == CustomTechnique
        
    def test_create_instance(self):
        """Test creating technique instance"""
        registry = technique_registry
        
        class CustomTechnique(BaseTechnique):
            def apply(self, text, context=None):
                return f"Custom: {text}"
                
            def validate_input(self, text, context=None):
                return True
                
        registry.register("custom_test2", CustomTechnique)
        
        config = {"name": "custom_test2", "priority": 5}
        instance = registry.create_instance("custom_test2", config)
        
        assert isinstance(instance, CustomTechnique)
        assert instance.priority == 5
        
    def test_apply_technique(self):
        """Test applying a technique through registry"""
        registry = technique_registry
        
        class TestTechnique(BaseTechnique):
            def apply(self, text, context=None):
                return f"Test: {text}"
                
            def validate_input(self, text, context=None):
                return len(text) > 0
                
        registry.register("test_apply", TestTechnique)
        registry.create_instance("test_apply", {"name": "test_apply"})
        
        result = registry.apply_technique("test_apply", "input text")
        assert result == "Test: input text"
        
    def test_apply_technique_disabled(self):
        """Test applying a disabled technique"""
        registry = technique_registry
        
        class DisabledTechnique(BaseTechnique):
            def apply(self, text, context=None):
                return f"Should not see this: {text}"
                
            def validate_input(self, text, context=None):
                return True
                
        registry.register("disabled_test", DisabledTechnique)
        registry.create_instance("disabled_test", {
            "name": "disabled_test",
            "enabled": False
        })
        
        # Should return original text when disabled
        result = registry.apply_technique("disabled_test", "input")
        assert result == "input"
        
    def test_apply_multiple_techniques(self):
        """Test applying multiple techniques in sequence"""
        registry = technique_registry
        
        class Tech1(BaseTechnique):
            def apply(self, text, context=None):
                return f"[Tech1] {text}"
                
            def validate_input(self, text, context=None):
                return True
                
        class Tech2(BaseTechnique):
            def apply(self, text, context=None):
                return f"[Tech2] {text}"
                
            def validate_input(self, text, context=None):
                return True
                
        registry.register("multi_test1", Tech1)
        registry.register("multi_test2", Tech2)
        registry.create_instance("multi_test1", {"name": "multi_test1", "priority": 2})
        registry.create_instance("multi_test2", {"name": "multi_test2", "priority": 1})
        
        result = registry.apply_multiple(
            ["multi_test1", "multi_test2"],
            "input"
        )
        
        # Should apply in priority order (multi_test1 first due to higher priority)
        assert result == "[Tech2] [Tech1] input"
        
    def test_list_available_techniques(self):
        """Test listing available techniques"""
        registry = technique_registry
        
        available = registry.list_available()
        assert isinstance(available, list)
        assert len(available) > 0
        
        # Check that standard techniques are registered
        expected = [
            "chain_of_thought", "tree_of_thoughts", "few_shot",
            "zero_shot", "role_play", "step_by_step"
        ]
        for tech in expected:
            assert tech in available
            
    def test_list_enabled_techniques(self):
        """Test listing only enabled techniques"""
        registry = technique_registry
        
        enabled = registry.list_enabled()
        assert isinstance(enabled, list)
        
        # All enabled techniques should have enabled=True
        for tech_id in enabled:
            instance = registry.get_instance(tech_id)
            if instance:
                assert instance.enabled is True