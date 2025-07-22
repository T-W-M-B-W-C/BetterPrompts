"""
Edge case tests for individual techniques
"""

import pytest
from typing import Dict, Any
from unittest.mock import patch, MagicMock

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


class TestTechniqueEdgeCases:
    """Test edge cases for all techniques"""
    
    def test_chain_of_thought_edge_cases(self):
        """Test CoT with edge cases"""
        technique = ChainOfThoughtTechnique({"name": "cot", "enabled": True})
        
        # Mathematical expression
        result = technique.apply("2+2=?")
        assert "step" in result.lower() or "think" in result.lower()
        assert "2+2" in result
        
        # Code snippet
        result = technique.apply("def factorial(n): return n * factorial(n-1) if n > 1 else 1")
        assert len(result) > 50
        
        # Question with special characters
        result = technique.apply("What is @#$%^&*() used for?")
        assert "@#$%^&*()" in result
        
        # Multilingual
        result = technique.apply("Explain 人工智能 (AI)")
        assert "人工智能" in result or "AI" in result
        
    def test_tree_of_thoughts_edge_cases(self):
        """Test ToT with edge cases"""
        technique = TreeOfThoughtsTechnique({"name": "tot", "enabled": True})
        
        # Single word input
        result = technique.apply("Democracy")
        assert len(result) > 10
        
        # Numeric optimization problem
        result = technique.apply("Minimize: f(x) = x^2 + 2x + 1")
        assert "approach" in result.lower() or "solution" in result.lower()
        
        # Complex context
        context = {
            "parameters": {
                "num_branches": 5,
                "evaluation_criteria": ["feasibility", "cost", "time", "quality", "risk"]
            }
        }
        result = technique.apply("Design a mobile app", context)
        assert len(result) > 100
        
    def test_few_shot_edge_cases(self):
        """Test few-shot with edge cases"""
        technique = FewShotTechnique({"name": "fs", "enabled": True})
        
        # No examples provided
        result = technique.apply("Classify sentiment")
        assert "example" in result.lower()
        
        # Single example
        context = {
            "examples": [
                {"input": "Great!", "output": "positive"}
            ]
        }
        result = technique.apply("Classify: Amazing!", context)
        assert "Great!" in result
        assert "positive" in result
        
        # Examples with code
        context = {
            "examples": [
                {"input": "reverse('hello')", "output": "'olleh'"},
                {"input": "reverse('world')", "output": "'dlrow'"}
            ]
        }
        result = technique.apply("reverse('python')", context)
        assert "reverse" in result
        assert any(ex["input"] in result for ex in context["examples"])
        
        # Examples with special formatting
        context = {
            "examples": [
                {"input": "Format: JSON", "output": '{"type": "json", "valid": true}'},
                {"input": "Format: XML", "output": '<format>xml</format>'}
            ]
        }
        result = technique.apply("Format: YAML", context)
        assert "JSON" in result or "json" in result
        
    def test_zero_shot_edge_cases(self):
        """Test zero-shot with edge cases"""
        technique = ZeroShotTechnique({"name": "zs", "enabled": True})
        
        # Minimal input
        result = technique.apply("?")
        assert len(result) > 1
        
        # Technical jargon
        result = technique.apply("Explain LSTM backpropagation through time")
        assert "LSTM" in result or "backpropagation" in result
        
        # Multi-line input
        multi_line = """Line 1: Introduction
        Line 2: Main point
        Line 3: Conclusion"""
        result = technique.apply(multi_line)
        assert len(result) >= len(multi_line)
        
    def test_role_play_edge_cases(self):
        """Test role play with edge cases"""
        technique = RolePlayTechnique({"name": "rp", "enabled": True})
        
        # Technical role
        context = {"role": "cybersecurity expert"}
        result = technique.apply("Review this password: abc123", context)
        assert "expert" in result.lower() or "security" in result.lower()
        
        # Creative role
        context = {"role": "poet"}
        result = technique.apply("Describe a sunset", context)
        assert len(result) > 20
        
        # Multiple roles
        context = {"role": "teacher and mentor"}
        result = technique.apply("Explain recursion", context)
        assert "teacher" in result.lower() or "mentor" in result.lower() or "expert" in result.lower()
        
    def test_step_by_step_edge_cases(self):
        """Test step by step with edge cases"""
        technique = StepByStepTechnique({"name": "sbs", "enabled": True})
        
        # Already has steps
        input_with_steps = "Step 1: Do this\nStep 2: Do that"
        result = technique.apply(input_with_steps)
        assert "step" in result.lower()
        
        # Recipe format
        result = technique.apply("Make coffee")
        assert "step" in result.lower() or "first" in result.lower()
        
        # Mathematical proof
        result = technique.apply("Prove that sqrt(2) is irrational")
        assert any(word in result.lower() for word in ["step", "first", "then", "next"])
        
    def test_structured_output_edge_cases(self):
        """Test structured output with edge cases"""
        technique = StructuredOutputTechnique({"name": "so", "enabled": True})
        
        # Request for specific format
        context = {"output_format": "markdown_table"}
        result = technique.apply("Compare Python vs JavaScript", context)
        assert "|" in result or "format" in result.lower()
        
        # JSON output request
        context = {"output_format": "json", "fields": ["name", "age", "email"]}
        result = technique.apply("Generate user data", context)
        assert "json" in result.lower() or "{" in result
        
        # CSV format
        context = {"output_format": "csv"}
        result = technique.apply("List top 5 programming languages", context)
        assert "," in result or "csv" in result.lower()
        
        # Nested structure
        context = {
            "output_format": "nested_list",
            "structure": {
                "level1": ["item1", "item2"],
                "level2": ["subitem1", "subitem2"]
            }
        }
        result = technique.apply("Organize project structure", context)
        assert len(result) > 30
        
    def test_emotional_appeal_edge_cases(self):
        """Test emotional appeal with edge cases"""
        technique = EmotionalAppealTechnique({"name": "ea", "enabled": True})
        
        # Technical request
        result = technique.apply("Debug this code")
        assert any(word in result.lower() for word in ["help", "together", "understand", "support"])
        
        # Urgent request
        context = {"emotion": "urgent", "urgency": "critical"}
        result = technique.apply("Fix the production bug", context)
        assert len(result) > 20
        
        # Learning context
        context = {"emotion": "encouraging"}
        result = technique.apply("I don't understand recursion", context)
        assert any(word in result.lower() for word in ["help", "understand", "together", "can"])
        
    def test_constraints_edge_cases(self):
        """Test constraints with edge cases"""
        technique = ConstraintsTechnique({"name": "con", "enabled": True})
        
        # No explicit constraints
        result = technique.apply("Write a function")
        assert "must" in result.lower() or "should" in result.lower()
        
        # Many constraints
        context = {
            "constraints": [
                "Must be thread-safe",
                "Should handle errors gracefully",
                "Must complete in under 100ms",
                "Should use no more than 10MB memory",
                "Must be compatible with Python 3.8+",
                "Should follow PEP 8",
                "Must include type hints"
            ]
        }
        result = technique.apply("Implement a cache", context)
        assert "thread-safe" in result
        assert "errors" in result
        
        # Conflicting constraints
        context = {
            "constraints": [
                "Must be very fast",
                "Must use minimal memory",
                "Must be highly accurate"
            ]
        }
        result = technique.apply("Design an algorithm", context)
        assert all(c.split("Must")[1].strip() in result for c in context["constraints"])
        
    def test_analogical_edge_cases(self):
        """Test analogical reasoning with edge cases"""
        technique = AnalogicalTechnique({"name": "ana", "enabled": True})
        
        # Abstract concept
        result = technique.apply("Explain consciousness")
        assert any(word in result.lower() for word in ["like", "similar", "think of", "imagine"])
        
        # Technical to simple
        context = {"target_domain": "cooking"}
        result = technique.apply("Explain database transactions", context)
        assert len(result) > 50
        
        # Multiple analogies
        context = {"num_analogies": 3}
        result = technique.apply("Explain machine learning", context)
        assert result.lower().count("like") >= 1 or result.lower().count("similar") >= 1
        
    def test_self_consistency_edge_cases(self):
        """Test self-consistency with edge cases"""
        technique = SelfConsistencyTechnique({"name": "sc", "enabled": True})
        
        # Simple fact checking
        result = technique.apply("Is 17 a prime number?")
        assert any(word in result.lower() for word in ["verify", "check", "confirm", "multiple"])
        
        # Complex reasoning
        context = {"num_paths": 5}
        result = technique.apply("What's the best programming language?", context)
        assert len(result) > 100
        
        # Mathematical problem
        result = technique.apply("Solve: x^2 - 5x + 6 = 0")
        assert "check" in result.lower() or "verify" in result.lower()
        
    def test_react_edge_cases(self):
        """Test ReAct with edge cases"""
        technique = ReactTechnique({"name": "react", "enabled": True})
        
        # No tools specified
        result = technique.apply("Find information about Python")
        assert any(word in result.lower() for word in ["thought", "action", "observation"])
        
        # With specific tools
        context = {
            "available_tools": ["search", "calculate", "read_file", "write_file"],
            "tool_descriptions": {
                "search": "Search the web",
                "calculate": "Perform calculations",
                "read_file": "Read file contents",
                "write_file": "Write to file"
            }
        }
        result = technique.apply("Research and summarize recent AI developments", context)
        assert "search" in result.lower()
        assert any(word in result.lower() for word in ["thought", "action"])
        
        # Multi-step task
        context = {
            "max_iterations": 5,
            "available_tools": ["think", "plan", "execute", "verify"]
        }
        result = technique.apply("Develop a small web application", context)
        assert len(result) > 100
        
    def test_technique_with_html_content(self):
        """Test techniques with HTML content"""
        html_input = "<div>Process this <b>HTML</b> content</div>"
        
        techniques = [
            ChainOfThoughtTechnique({"name": "cot"}),
            StructuredOutputTechnique({"name": "so"}),
            ZeroShotTechnique({"name": "zs"})
        ]
        
        for technique in techniques:
            result = technique.apply(html_input)
            assert result is not None
            assert len(result) > 0
            # Should handle HTML without breaking
            
    def test_technique_with_json_content(self):
        """Test techniques with JSON content"""
        json_input = '{"task": "Process this JSON", "priority": "high", "data": [1, 2, 3]}'
        
        techniques = [
            StructuredOutputTechnique({"name": "so"}),
            FewShotTechnique({"name": "fs"}),
            ConstraintsTechnique({"name": "con"})
        ]
        
        for technique in techniques:
            result = technique.apply(json_input)
            assert result is not None
            assert len(result) > len(json_input) * 0.5
            
    def test_technique_with_code_content(self):
        """Test techniques with code content"""
        code_input = """
def complex_function(x, y):
    '''This function does complex calculations'''
    result = x ** 2 + y ** 2
    if result > 100:
        return math.sqrt(result)
    else:
        return result * 2
"""
        
        techniques = [
            ChainOfThoughtTechnique({"name": "cot"}),
            StepByStepTechnique({"name": "sbs"}),
            AnalogicalTechnique({"name": "ana"})
        ]
        
        for technique in techniques:
            result = technique.apply(code_input)
            assert result is not None
            assert "function" in result.lower() or "code" in result.lower()
            
    def test_technique_context_preservation(self):
        """Test that techniques preserve important context"""
        techniques = [
            ChainOfThoughtTechnique({"name": "cot"}),
            TreeOfThoughtsTechnique({"name": "tot"}),
            FewShotTechnique({"name": "fs"}),
            StepByStepTechnique({"name": "sbs"})
        ]
        
        important_context = {
            "user_id": "12345",
            "session_id": "abc-def",
            "critical_requirement": "Must be HIPAA compliant",
            "target_audience": "medical professionals"
        }
        
        prompt = "Design a patient data system"
        
        for technique in techniques:
            result = technique.apply(prompt, important_context)
            # Should reference the critical requirement
            assert "HIPAA" in result or "compliant" in result.lower() or "medical" in result.lower()
            
    def test_technique_error_messages(self):
        """Test technique behavior with error-like inputs"""
        error_inputs = [
            "Error: Connection timeout",
            "Exception: NullPointerException at line 42",
            "FATAL ERROR: Out of memory",
            "Warning: Deprecated function used"
        ]
        
        technique = ChainOfThoughtTechnique({"name": "cot"})
        
        for error_input in error_inputs:
            result = technique.apply(error_input)
            assert result is not None
            assert len(result) > len(error_input)
            # Should treat as content, not actual error
            
    def test_technique_with_empty_context(self):
        """Test techniques with empty or None context"""
        techniques = [
            ChainOfThoughtTechnique({"name": "cot"}),
            TreeOfThoughtsTechnique({"name": "tot"}),
            RolePlayTechnique({"name": "rp"})
        ]
        
        prompt = "Test with empty context"
        
        for technique in techniques:
            # Test with None context
            result1 = technique.apply(prompt, None)
            assert result1 is not None
            
            # Test with empty dict context
            result2 = technique.apply(prompt, {})
            assert result2 is not None
            
            # Results should be similar
            assert len(result1) > 0 and len(result2) > 0