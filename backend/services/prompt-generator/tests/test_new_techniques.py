"""
Detailed tests for Self-Consistency and ReAct techniques
"""

import pytest
from app.techniques import SelfConsistencyTechnique, ReactTechnique


class TestSelfConsistencyAdvanced:
    """Advanced tests for Self-Consistency technique"""
    
    def test_math_problem_application(self):
        """Test self-consistency on a math problem"""
        config = {"name": "self_consistency", "enabled": True, "priority": 1}
        technique = SelfConsistencyTechnique(config)
        
        text = "If a train travels at 60 mph for 2.5 hours, how far does it travel?"
        context = {
            "num_paths": 3,
            "task_type": "math",
            "show_confidence": True
        }
        result = technique.apply(text, context)
        
        # Check for math-specific reasoning variations
        assert "solve algebraically" in result or "Algebraic Method" in result
        assert "Approach 1" in result
        assert "Approach 3" in result
        assert "Consistency Analysis" in result
        assert "Confidence Level:" in result
    
    def test_logic_problem_application(self):
        """Test self-consistency on a logic problem"""
        config = {"name": "self_consistency", "enabled": True, "priority": 1}
        technique = SelfConsistencyTechnique(config)
        
        text = "If all roses are flowers and some flowers fade quickly, can we conclude that some roses fade quickly?"
        context = {
            "num_paths": 4,
            "task_type": "logic"
        }
        result = technique.apply(text, context)
        
        # Check for logic-specific reasoning
        assert any(phrase in result for phrase in ["formal logic", "truth tables", "Venn diagrams"])
        assert "Approach 4" in result
    
    def test_custom_reasoning_variations(self):
        """Test with custom reasoning variations"""
        config = {"name": "self_consistency", "enabled": True, "priority": 1}
        technique = SelfConsistencyTechnique(config)
        
        text = "What's the best way to optimize this algorithm?"
        context = {
            "num_paths": 3,
            "reasoning_variations": [
                "analyze time complexity",
                "examine space complexity",
                "consider practical constraints"
            ]
        }
        result = technique.apply(text, context)
        
        assert "analyze time complexity" in result
        assert "examine space complexity" in result
        assert "consider practical constraints" in result
    
    def test_edge_cases(self):
        """Test edge cases for self-consistency"""
        config = {"name": "self_consistency", "enabled": True, "priority": 1}
        technique = SelfConsistencyTechnique(config)
        
        # Test with maximum paths
        text = "Complex problem"
        context = {"num_paths": 10}  # Should be capped at 5
        result = technique.apply(text, context)
        
        assert "Approach 5" in result
        assert "Approach 6" not in result  # Should be capped
        
        # Test without context
        result = technique.apply("Solve this problem")
        assert "Approach 1" in result
        assert "Approach 3" in result  # Default is 3 paths


class TestReactAdvanced:
    """Advanced tests for ReAct technique"""
    
    def test_implementation_task(self):
        """Test ReAct on an implementation task"""
        config = {"name": "react", "enabled": True, "priority": 1}
        technique = ReactTechnique(config)
        
        text = "Implement a REST API endpoint for user authentication"
        context = {
            "num_steps": 4,
            "task_type": "implementation",
            "include_reflection": True
        }
        result = technique.apply(text, context)
        
        # Check for implementation-specific actions
        assert "Analyze the requirements" in result
        assert "Implement the core functionality" in result
        assert "Test the implementation works correctly" in result
        assert "Reflection:" in result
    
    def test_debugging_task(self):
        """Test ReAct on a debugging task"""
        config = {"name": "react", "enabled": True, "priority": 1}
        technique = ReactTechnique(config)
        
        text = "Debug why the database queries are running slowly"
        context = {
            "num_steps": 5,
            "task_type": "debugging",
            "available_tools": ["query analyzer", "profiler", "explain plan"],
            "allow_iterations": True
        }
        result = technique.apply(text, context)
        
        # Check for debugging-specific approach
        assert "Analyze the error or issue" in result
        assert "query analyzer" in result
        assert "profiler" in result
        assert "Iteration Check:" in result
    
    def test_research_task(self):
        """Test ReAct on a research task"""
        config = {"name": "react", "enabled": True, "priority": 1}
        technique = ReactTechnique(config)
        
        text = "Research the best practices for microservices architecture"
        context = {
            "num_steps": 4,
            "task_type": "research",
            "initial_analysis": "This requires gathering information from multiple sources and synthesizing best practices."
        }
        result = technique.apply(text, context)
        
        # Check for research-specific actions
        assert "Search for relevant information" in result
        assert "Compare different sources and perspectives" in result
        assert "Initial Analysis:" in result
        assert context["initial_analysis"] in result
    
    def test_tool_integration(self):
        """Test ReAct with specific tools"""
        config = {"name": "react", "enabled": True, "priority": 1}
        technique = ReactTechnique(config)
        
        text = "Analyze website performance issues"
        context = {
            "num_steps": 6,
            "available_tools": [
                "Chrome DevTools",
                "Lighthouse",
                "WebPageTest",
                "GTmetrix"
            ]
        }
        result = technique.apply(text, context)
        
        # All tools should be mentioned
        assert "Chrome DevTools" in result
        assert "Lighthouse" in result
        assert "WebPageTest" in result
        assert "GTmetrix" in result
        
        # Tools should cycle if more steps than tools
        assert result.count("Use") >= 6  # Each step should use a tool
    
    def test_edge_cases(self):
        """Test edge cases for ReAct"""
        config = {"name": "react", "enabled": True, "priority": 1}
        technique = ReactTechnique(config)
        
        # Test with maximum steps
        text = "Complex task"
        context = {"num_steps": 10}  # Should be capped at 6
        result = technique.apply(text, context)
        
        assert "Step 6:" in result
        assert "Step 7:" not in result  # Should be capped
        
        # Test without context
        result = technique.apply("Debug this issue")
        assert "Step 1:" in result
        assert "Step 3:" in result  # Default is 3 steps


class TestTechniqueInteraction:
    """Test how techniques work together"""
    
    def test_validation_mutual_exclusivity(self):
        """Test that techniques validate appropriately for different inputs"""
        sc_config = {"name": "self_consistency", "enabled": True, "priority": 1}
        react_config = {"name": "react", "enabled": True, "priority": 1}
        
        sc_technique = SelfConsistencyTechnique(sc_config)
        react_technique = ReactTechnique(react_config)
        
        # Self-consistency should be better for pure reasoning
        reasoning_prompt = "What is the optimal solution to the traveling salesman problem?"
        assert sc_technique.validate_input(reasoning_prompt)
        assert not react_technique.validate_input(reasoning_prompt)
        
        # ReAct should be better for procedural tasks
        procedural_prompt = "How to set up a CI/CD pipeline step by step"
        assert react_technique.validate_input(procedural_prompt)
        assert not sc_technique.validate_input(procedural_prompt)
        
        # Both might work for complex analytical tasks
        complex_prompt = "Analyze and solve the performance issues in our distributed system"
        # This could go either way depending on the specific keywords


@pytest.mark.parametrize("text,expected_validation", [
    ("Solve 2+2", False),  # Too simple
    ("What color is the sky?", False),  # Too simple
    ("Analyze the time complexity of quicksort", True),  # Good for self-consistency
    ("Determine the best investment strategy given market conditions", True),  # Good for self-consistency
    ("Figure out why the server is crashing", True),  # Could use self-consistency
])
def test_self_consistency_validation_cases(text, expected_validation):
    """Test various validation cases for self-consistency"""
    config = {"name": "self_consistency", "enabled": True, "priority": 1}
    technique = SelfConsistencyTechnique(config)
    
    assert technique.validate_input(text) == expected_validation


@pytest.mark.parametrize("text,expected_validation", [
    ("Hello", False),  # Too simple
    ("What's your name?", False),  # Too simple
    ("Build a web scraper that extracts data from multiple sites", True),  # Good for ReAct
    ("Debug why the application crashes on startup", True),  # Good for ReAct
    ("Research and implement a recommendation system", True),  # Good for ReAct
])
def test_react_validation_cases(text, expected_validation):
    """Test various validation cases for ReAct"""
    config = {"name": "react", "enabled": True, "priority": 1}
    technique = ReactTechnique(config)
    
    assert technique.validate_input(text) == expected_validation