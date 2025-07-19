"""
Comprehensive tests for all prompt engineering techniques
"""

import pytest
from typing import Dict, Any
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
    ReactTechnique,
    TechniqueRegistry
)
from app.models import TechniqueType


class TestChainOfThought:
    """Test Chain of Thought technique"""
    
    def test_basic_application(self):
        """Test basic CoT application"""
        config = {"name": "chain_of_thought", "enabled": True, "priority": 1}
        technique = ChainOfThoughtTechnique(config)
        
        text = "What is the sum of the first 10 prime numbers?"
        result = technique.apply(text)
        
        assert "Let's think through this step-by-step" in result
        assert text in result
        assert len(result) > len(text)
    
    def test_custom_reasoning_steps(self):
        """Test CoT with custom reasoning steps"""
        config = {"name": "chain_of_thought", "enabled": True, "priority": 1}
        technique = ChainOfThoughtTechnique(config)
        
        text = "Calculate the compound interest"
        context = {
            "reasoning_steps": [
                "Identify the principal amount",
                "Determine the interest rate",
                "Calculate the time period",
                "Apply the compound interest formula"
            ]
        }
        result = technique.apply(text, context)
        
        assert "1. Identify the principal amount" in result
        assert "4. Apply the compound interest formula" in result
    
    def test_validation(self):
        """Test CoT validation logic"""
        config = {"name": "chain_of_thought", "enabled": True, "priority": 1}
        technique = ChainOfThoughtTechnique(config)
        
        # Should validate complex reasoning tasks
        assert technique.validate_input("Solve this complex mathematical problem")
        assert technique.validate_input("Analyze the implications of this decision")
        
        # Should not validate simple queries
        assert not technique.validate_input("Hi")
        assert not technique.validate_input("What time?")


class TestTreeOfThoughts:
    """Test Tree of Thoughts technique"""
    
    def test_basic_application(self):
        """Test basic ToT application"""
        config = {"name": "tree_of_thoughts", "enabled": True, "priority": 1}
        technique = TreeOfThoughtsTechnique(config)
        
        text = "Design a new mobile app for fitness tracking"
        result = technique.apply(text)
        
        assert "explore different approaches" in result
        assert "Approach 1:" in result
        assert "Approach 2:" in result
        assert "Approach 3:" in result
    
    def test_custom_approaches(self):
        """Test ToT with custom approaches"""
        config = {"name": "tree_of_thoughts", "enabled": True, "priority": 1}
        technique = TreeOfThoughtsTechnique(config)
        
        text = "Optimize database performance"
        context = {
            "approaches": [
                "Index optimization",
                "Query rewriting",
                "Hardware scaling",
                "Caching strategy"
            ]
        }
        result = technique.apply(text, context)
        
        assert "Index optimization" in result
        assert "Caching strategy" in result


class TestFewShot:
    """Test Few-shot Learning technique"""
    
    def test_basic_application(self):
        """Test basic few-shot application"""
        config = {"name": "few_shot", "enabled": True, "priority": 1}
        technique = FewShotTechnique(config)
        
        text = "Translate 'Hello' to Spanish"
        result = technique.apply(text)
        
        assert "Example" in result
        assert "Input:" in result
        assert "Output:" in result
    
    def test_custom_examples(self):
        """Test few-shot with custom examples"""
        config = {"name": "few_shot", "enabled": True, "priority": 1}
        technique = FewShotTechnique(config)
        
        text = "Convert temperature from Celsius to Fahrenheit"
        context = {
            "examples": [
                {"input": "0°C", "output": "32°F"},
                {"input": "100°C", "output": "212°F"},
                {"input": "37°C", "output": "98.6°F"}
            ]
        }
        result = technique.apply(text, context)
        
        assert "0°C" in result
        assert "32°F" in result
        assert "100°C" in result


class TestZeroShot:
    """Test Zero-shot technique"""
    
    def test_basic_application(self):
        """Test basic zero-shot application"""
        config = {"name": "zero_shot", "enabled": True, "priority": 1}
        technique = ZeroShotTechnique(config)
        
        text = "Classify this sentiment"
        result = technique.apply(text)
        
        assert "clear instructions" in result.lower() or "task:" in result.lower()
        assert text in result


class TestSelfConsistency:
    """Test Self-Consistency technique"""
    
    def test_basic_application(self):
        """Test basic self-consistency application"""
        config = {"name": "self_consistency", "enabled": True, "priority": 1}
        technique = SelfConsistencyTechnique(config)
        
        text = "What is the best algorithm for sorting a large dataset?"
        result = technique.apply(text)
        
        assert "Approach 1" in result
        assert "Approach 2" in result
        assert "Consistency Analysis" in result
        assert "Final Answer" in result
    
    def test_custom_paths(self):
        """Test self-consistency with custom number of paths"""
        config = {"name": "self_consistency", "enabled": True, "priority": 1}
        technique = SelfConsistencyTechnique(config)
        
        text = "Solve this optimization problem"
        context = {
            "num_paths": 4,
            "show_confidence": True
        }
        result = technique.apply(text, context)
        
        assert "Approach 1" in result
        assert "Approach 4" in result
        assert "Confidence Level:" in result
    
    def test_validation(self):
        """Test self-consistency validation logic"""
        config = {"name": "self_consistency", "enabled": True, "priority": 1}
        technique = SelfConsistencyTechnique(config)
        
        # Should validate reasoning problems
        assert technique.validate_input("Solve this complex equation")
        assert technique.validate_input("What is the best way to optimize this?")
        
        # Should not validate simple queries
        assert not technique.validate_input("Hi")
        assert not technique.validate_input("Name?")


class TestReact:
    """Test ReAct technique"""
    
    def test_basic_application(self):
        """Test basic ReAct application"""
        config = {"name": "react", "enabled": True, "priority": 1}
        technique = ReactTechnique(config)
        
        text = "Debug why the application is running slowly"
        result = technique.apply(text)
        
        assert "Thought 1:" in result
        assert "Action 1:" in result
        assert "Observation 1:" in result
        assert "ReAct Process:" in result
    
    def test_custom_steps_and_tools(self):
        """Test ReAct with custom steps and tools"""
        config = {"name": "react", "enabled": True, "priority": 1}
        technique = ReactTechnique(config)
        
        text = "Find and fix the memory leak"
        context = {
            "num_steps": 5,
            "available_tools": ["profiler", "debugger", "heap analyzer"],
            "allow_iterations": True,
            "include_reflection": True
        }
        result = technique.apply(text, context)
        
        assert "Step 5:" in result
        assert "profiler" in result
        assert "Iteration Check:" in result
        assert "Reflection:" in result
    
    def test_validation(self):
        """Test ReAct validation logic"""
        config = {"name": "react", "enabled": True, "priority": 1}
        technique = ReactTechnique(config)
        
        # Should validate multi-step tasks
        assert technique.validate_input("Implement a new feature step by step")
        assert technique.validate_input("Debug and fix this issue")
        assert technique.validate_input("Research and analyze market trends")
        
        # Should not validate simple queries
        assert not technique.validate_input("What color?")
        assert not technique.validate_input("Yes or no?")


class TestRolePlay:
    """Test Role Play technique"""
    
    def test_basic_application(self):
        """Test basic role play application"""
        config = {"name": "role_play", "enabled": True, "priority": 1}
        technique = RolePlayTechnique(config)
        
        text = "Explain quantum computing"
        context = {"role": "physics professor"}
        result = technique.apply(text, context)
        
        assert "physics professor" in result.lower() or "role" in result.lower()


class TestStepByStep:
    """Test Step by Step technique"""
    
    def test_basic_application(self):
        """Test basic step by step application"""
        config = {"name": "step_by_step", "enabled": True, "priority": 1}
        technique = StepByStepTechnique(config)
        
        text = "How to bake a cake"
        result = technique.apply(text)
        
        assert "step" in result.lower()
        assert text in result


class TestStructuredOutput:
    """Test Structured Output technique"""
    
    def test_basic_application(self):
        """Test basic structured output application"""
        config = {"name": "structured_output", "enabled": True, "priority": 1}
        technique = StructuredOutputTechnique(config)
        
        text = "List the pros and cons"
        context = {"output_format": "markdown"}
        result = technique.apply(text, context)
        
        assert text in result
        assert "format" in result.lower() or "structure" in result.lower()


class TestTechniqueRegistry:
    """Test the technique registry"""
    
    def test_registration_and_creation(self):
        """Test registering and creating technique instances"""
        registry = TechniqueRegistry()
        
        # Register a technique class
        registry.register("test_technique", ChainOfThoughtTechnique)
        
        # Create an instance
        config = {"name": "test", "enabled": True, "priority": 1}
        instance = registry.create_instance("test_technique", config)
        
        assert instance is not None
        assert isinstance(instance, ChainOfThoughtTechnique)
    
    def test_get_instance(self):
        """Test getting technique instances"""
        registry = TechniqueRegistry()
        
        # Register and create
        registry.register("cot", ChainOfThoughtTechnique)
        config = {"name": "cot", "enabled": True, "priority": 1}
        registry.create_instance("cot", config)
        
        # Get instance
        instance = registry.get_instance("cot")
        assert instance is not None
        assert isinstance(instance, ChainOfThoughtTechnique)
    
    def test_apply_techniques(self):
        """Test applying multiple techniques"""
        registry = TechniqueRegistry()
        
        # Register techniques
        registry.register("cot", ChainOfThoughtTechnique)
        registry.register("few_shot", FewShotTechnique)
        
        # Create instances
        config1 = {"name": "cot", "enabled": True, "priority": 2}
        config2 = {"name": "few_shot", "enabled": True, "priority": 1}
        registry.create_instance("cot", config1)
        registry.create_instance("few_shot", config2)
        
        # Apply techniques
        text = "Solve this problem"
        techniques = ["cot", "few_shot"]
        result = registry.apply_techniques(text, techniques)
        
        # Should apply few_shot first (lower priority number = higher priority)
        assert "Example" in result  # From few_shot
        assert "think through this step-by-step" in result  # From CoT


@pytest.mark.parametrize("technique_class,config", [
    (ChainOfThoughtTechnique, {"name": "cot", "enabled": True, "priority": 1}),
    (TreeOfThoughtsTechnique, {"name": "tot", "enabled": True, "priority": 1}),
    (FewShotTechnique, {"name": "few_shot", "enabled": True, "priority": 1}),
    (ZeroShotTechnique, {"name": "zero_shot", "enabled": True, "priority": 1}),
    (SelfConsistencyTechnique, {"name": "self_consistency", "enabled": True, "priority": 1}),
    (ReactTechnique, {"name": "react", "enabled": True, "priority": 1}),
])
def test_technique_token_estimation(technique_class, config):
    """Test that all techniques can estimate tokens"""
    technique = technique_class(config)
    
    text = "This is a test prompt for token estimation"
    # All techniques should be able to estimate tokens
    tokens = technique.estimate_tokens(text)
    assert tokens > 0
    assert isinstance(tokens, int)


@pytest.mark.parametrize("technique_class,config", [
    (ChainOfThoughtTechnique, {"name": "cot", "enabled": True, "priority": 1}),
    (TreeOfThoughtsTechnique, {"name": "tot", "enabled": True, "priority": 1}),
    (FewShotTechnique, {"name": "few_shot", "enabled": True, "priority": 1}),
    (ZeroShotTechnique, {"name": "zero_shot", "enabled": True, "priority": 1}),
    (SelfConsistencyTechnique, {"name": "self_consistency", "enabled": True, "priority": 1}),
    (ReactTechnique, {"name": "react", "enabled": True, "priority": 1}),
])
def test_technique_error_handling(technique_class, config):
    """Test that techniques handle errors gracefully"""
    technique = technique_class(config)
    
    # Test with None input
    result = technique.apply(None)
    assert result == ""  # Should return empty string on None
    
    # Test with empty string
    result = technique.apply("")
    assert result == ""  # Should return empty string
    
    # Test validation with None
    assert not technique.validate_input(None)
    assert not technique.validate_input("")