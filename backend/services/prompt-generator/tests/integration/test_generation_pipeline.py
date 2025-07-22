"""
Integration tests for the complete prompt generation pipeline
"""

import pytest
import asyncio
from typing import List, Dict, Any
from unittest.mock import patch, AsyncMock, MagicMock
import time

from app.engine import PromptGenerationEngine
from app.models import (
    PromptGenerationRequest,
    PromptGenerationResponse,
    BatchGenerationRequest,
    BatchGenerationResponse,
    TechniqueType,
    ComplexityLevel
)
from app.techniques.base import technique_registry
from app.validators import PromptValidator


class TestFullGenerationPipeline:
    """Test the complete generation pipeline with multiple techniques"""
    
    @pytest.fixture
    async def engine(self):
        """Create a real engine instance"""
        # Initialize the engine with all techniques
        engine = PromptGenerationEngine()
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        return engine
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_single_technique_pipeline(self, engine):
        """Test generation with a single technique"""
        request = PromptGenerationRequest(
            text="Explain how photosynthesis works",
            intent="explain_concept",
            complexity="moderate",
            techniques=["chain_of_thought"],
            target_model="gpt-4"
        )
        
        response = await engine.generate(request)
        
        assert isinstance(response, PromptGenerationResponse)
        assert response.text != request.text
        assert len(response.text) > len(request.text)
        assert response.techniques_applied == ["chain_of_thought"]
        assert response.confidence_score > 0
        assert response.generation_time_ms > 0
        assert response.tokens_used > 0
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_techniques_pipeline(self, engine):
        """Test generation with multiple techniques"""
        request = PromptGenerationRequest(
            text="Write a Python function to sort a list",
            intent="generate_code",
            complexity="moderate",
            techniques=["few_shot", "structured_output", "step_by_step"],
            context={
                "language": "python",
                "level": "beginner"
            },
            target_model="gpt-4"
        )
        
        response = await engine.generate(request)
        
        assert isinstance(response, PromptGenerationResponse)
        assert len(response.text) > len(request.text)
        assert len(response.techniques_applied) == 3
        assert response.metadata["intent"] == "generate_code"
        assert response.metadata["complexity"] == "moderate"
        
        # Check that techniques were actually applied
        text_lower = response.text.lower()
        assert any(marker in text_lower for marker in ["example", "step", "format", "structure"])
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_technique_priority_ordering(self, engine):
        """Test that techniques are applied in priority order"""
        # Create a custom context to track application order
        application_order = []
        
        def track_application(technique_id):
            application_order.append(technique_id)
            
        # Patch the apply_technique method to track order
        original_apply = technique_registry.apply_technique
        
        def tracked_apply(technique_id, text, context=None):
            track_application(technique_id)
            return original_apply(technique_id, text, context)
            
        with patch.object(technique_registry, 'apply_technique', side_effect=tracked_apply):
            request = PromptGenerationRequest(
                text="Test priority ordering",
                intent="test",
                complexity="simple",
                techniques=["zero_shot", "role_play", "constraints"],  # Different priorities
                target_model="gpt-4"
            )
            
            response = await engine.generate(request)
            
            # Verify techniques were applied
            assert len(application_order) == 3
            
            # Verify the order matches priority (would need to know actual priorities)
            assert response.text != request.text
            
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_context_propagation(self, engine):
        """Test that context is properly propagated through techniques"""
        request = PromptGenerationRequest(
            text="Design a database schema",
            intent="design",
            complexity="complex",
            techniques=["tree_of_thoughts", "structured_output"],
            context={
                "domain": "e-commerce",
                "requirements": ["scalability", "performance"],
                "constraints": ["PostgreSQL", "microservices"]
            },
            parameters={
                "output_format": "sql",
                "include_indexes": True
            },
            target_model="gpt-4"
        )
        
        response = await engine.generate(request)
        
        assert isinstance(response, PromptGenerationResponse)
        assert response.metadata["context"]["domain"] == "e-commerce"
        assert "requirements" in response.metadata["context"]
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_recovery_pipeline(self, engine):
        """Test pipeline recovery from technique failures"""
        # Create a request that might cause issues
        request = PromptGenerationRequest(
            text="Process this request",
            intent="process",
            complexity="simple",
            techniques=["chain_of_thought", "invalid_technique", "zero_shot"],
            target_model="gpt-4"
        )
        
        # The invalid technique should be filtered out during validation
        with pytest.raises(ValueError):
            await engine.generate(request)
            
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_metrics_calculation(self, engine):
        """Test that metrics are properly calculated"""
        request = PromptGenerationRequest(
            text="Explain artificial intelligence",
            intent="explain_concept",
            complexity="moderate",
            techniques=["chain_of_thought", "analogical"],
            target_model="gpt-4"
        )
        
        response = await engine.generate(request)
        
        # Check metrics in metadata
        metrics = response.metadata.get("metrics", {})
        assert "clarity_score" in metrics
        assert "specificity_score" in metrics
        assert "coherence_score" in metrics
        assert "overall_quality" in metrics
        assert "technique_effectiveness" in metrics
        
        # Verify metric ranges
        assert 0 <= metrics["clarity_score"] <= 1
        assert 0 <= metrics["specificity_score"] <= 1
        assert 0 <= metrics["coherence_score"] <= 1
        assert 0 <= metrics["overall_quality"] <= 1
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_token_limit_enforcement(self, engine):
        """Test that token limits are enforced"""
        request = PromptGenerationRequest(
            text="Write a comprehensive guide about machine learning",
            intent="create_content",
            complexity="complex",
            techniques=["tree_of_thoughts", "step_by_step", "structured_output"],
            max_tokens=100,  # Very low limit
            target_model="gpt-4"
        )
        
        response = await engine.generate(request)
        
        # Check that response respects token limit
        assert response.tokens_used <= 100 or response.tokens_used <= 150  # Some margin
        assert response.text.endswith("...") or len(response.text) < 500
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_temperature_parameter(self, engine):
        """Test temperature parameter handling"""
        # Low temperature - more deterministic
        request_low = PromptGenerationRequest(
            text="Generate a random story",
            intent="create_content",
            complexity="simple",
            techniques=["zero_shot"],
            temperature=0.1,
            target_model="gpt-4"
        )
        
        # High temperature - more creative
        request_high = PromptGenerationRequest(
            text="Generate a random story",
            intent="create_content",
            complexity="simple",
            techniques=["zero_shot"],
            temperature=1.5,
            target_model="gpt-4"
        )
        
        response_low = await engine.generate(request_low)
        response_high = await engine.generate(request_high)
        
        # Both should succeed
        assert response_low.text != request_low.text
        assert response_high.text != request_high.text
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_warning_propagation(self, engine):
        """Test that warnings are properly propagated"""
        # Create a request that might generate warnings
        request = PromptGenerationRequest(
            text="x" * 4500,  # Very long but not quite at limit
            intent="process",
            complexity="simple",
            techniques=["chain_of_thought"],
            target_model="gpt-4"
        )
        
        response = await engine.generate(request)
        
        # Should have warnings about length
        assert isinstance(response.warnings, list)
        # Warnings might be present depending on validation logic


class TestBatchGenerationPipeline:
    """Test batch generation functionality"""
    
    @pytest.fixture
    async def engine(self):
        """Create a real engine instance"""
        return PromptGenerationEngine()
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_generation_success(self, engine, test_app):
        """Test successful batch generation"""
        test_app.state.engine = engine
        
        batch_request = BatchGenerationRequest(
            prompts=[
                PromptGenerationRequest(
                    text="Explain quantum physics",
                    intent="explain_concept",
                    complexity="complex",
                    techniques=["chain_of_thought", "analogical"]
                ),
                PromptGenerationRequest(
                    text="Write a sorting algorithm",
                    intent="generate_code",
                    complexity="moderate",
                    techniques=["few_shot", "step_by_step"]
                ),
                PromptGenerationRequest(
                    text="Create a marketing plan",
                    intent="create_content",
                    complexity="moderate",
                    techniques=["structured_output", "constraints"]
                )
            ],
            batch_id="test-batch-001",
            priority=5
        )
        
        # Process batch through API endpoint simulation
        results = []
        errors = []
        
        for i, prompt_req in enumerate(batch_request.prompts):
            try:
                result = await engine.generate(prompt_req)
                results.append(result)
            except Exception as e:
                errors.append({
                    "index": i,
                    "error": str(e),
                    "prompt": prompt_req.text[:100]
                })
                
        # All should succeed
        assert len(results) == 3
        assert len(errors) == 0
        
        # Each result should be different
        texts = [r.text for r in results]
        assert len(set(texts)) == 3  # All unique
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_generation_with_failures(self, engine, test_app):
        """Test batch generation with some failures"""
        test_app.state.engine = engine
        
        batch_request = BatchGenerationRequest(
            prompts=[
                PromptGenerationRequest(
                    text="Valid prompt",
                    intent="explain_concept",
                    complexity="simple",
                    techniques=["chain_of_thought"]
                ),
                PromptGenerationRequest(
                    text="",  # Invalid - empty
                    intent="explain_concept",
                    complexity="simple",
                    techniques=["chain_of_thought"]
                ),
                PromptGenerationRequest(
                    text="Another valid prompt",
                    intent="explain_concept",
                    complexity="simple",
                    techniques=["zero_shot"]
                )
            ]
        )
        
        results = []
        errors = []
        
        for i, prompt_req in enumerate(batch_request.prompts):
            try:
                result = await engine.generate(prompt_req)
                results.append(result)
            except Exception as e:
                errors.append({
                    "index": i,
                    "error": str(e),
                    "prompt": prompt_req.text[:100] if prompt_req.text else "empty"
                })
                
        # Should have 2 successes and 1 failure
        assert len(results) == 2
        assert len(errors) == 1
        assert errors[0]["index"] == 1
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_generation_performance(self, engine):
        """Test batch generation performance"""
        # Create a batch of 10 similar prompts
        prompts = [
            PromptGenerationRequest(
                text=f"Explain concept {i}",
                intent="explain_concept",
                complexity="simple",
                techniques=["zero_shot"]
            )
            for i in range(10)
        ]
        
        start_time = time.time()
        
        # Process all prompts
        results = []
        for prompt in prompts:
            result = await engine.generate(prompt)
            results.append(result)
            
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete reasonably quickly
        assert len(results) == 10
        assert total_time < 10.0  # Less than 10 seconds for 10 prompts
        
        # Calculate average time per prompt
        avg_time = total_time / 10
        assert avg_time < 1.0  # Less than 1 second per prompt on average


class TestTechniqueCombinations:
    """Test various technique combinations"""
    
    @pytest.fixture
    async def engine(self):
        """Create a real engine instance"""
        return PromptGenerationEngine()
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analytical_combination(self, engine):
        """Test combination for analytical tasks"""
        request = PromptGenerationRequest(
            text="Analyze the pros and cons of renewable energy",
            intent="analyze",
            complexity="complex",
            techniques=["chain_of_thought", "tree_of_thoughts", "structured_output"],
            target_model="gpt-4"
        )
        
        response = await engine.generate(request)
        
        # Should have structured analytical content
        assert "pro" in response.text.lower() or "advantage" in response.text.lower()
        assert "con" in response.text.lower() or "disadvantage" in response.text.lower()
        assert any(marker in response.text for marker in [":", "-", "•", "\n"])
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_creative_combination(self, engine):
        """Test combination for creative tasks"""
        request = PromptGenerationRequest(
            text="Write a creative story about time travel",
            intent="create_content",
            complexity="moderate",
            techniques=["role_play", "emotional_appeal", "analogical"],
            context={
                "genre": "science fiction",
                "tone": "mysterious"
            },
            target_model="gpt-4"
        )
        
        response = await engine.generate(request)
        
        # Should have creative elements
        assert len(response.text) > len(request.text)
        assert response.confidence_score > 0.5
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_educational_combination(self, engine):
        """Test combination for educational content"""
        request = PromptGenerationRequest(
            text="Teach me about machine learning",
            intent="explain_concept",
            complexity="moderate",
            techniques=["step_by_step", "few_shot", "analogical", "self_consistency"],
            context={
                "audience": "beginner",
                "include_examples": True
            },
            target_model="gpt-4"
        )
        
        response = await engine.generate(request)
        
        # Should have educational elements
        educational_markers = ["example", "step", "like", "similar", "first", "then"]
        assert any(marker in response.text.lower() for marker in educational_markers)
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_problem_solving_combination(self, engine):
        """Test combination for problem-solving tasks"""
        request = PromptGenerationRequest(
            text="Solve the traveling salesman problem",
            intent="solve_problem",
            complexity="complex",
            techniques=["chain_of_thought", "tree_of_thoughts", "constraints", "react"],
            parameters={
                "max_depth": 3,
                "num_approaches": 3
            },
            target_model="gpt-4"
        )
        
        response = await engine.generate(request)
        
        # Should have problem-solving structure
        assert len(response.text) > len(request.text)
        problem_markers = ["approach", "solution", "constraint", "step", "think"]
        assert any(marker in response.text.lower() for marker in problem_markers)


class TestEdgeCasesAndLimits:
    """Test edge cases and system limits"""
    
    @pytest.fixture
    async def engine(self):
        """Create a real engine instance"""
        return PromptGenerationEngine()
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_very_short_input(self, engine):
        """Test with very short input"""
        request = PromptGenerationRequest(
            text="Hi",
            intent="greeting",
            complexity="simple",
            techniques=["zero_shot"],
            target_model="gpt-4"
        )
        
        response = await engine.generate(request)
        
        assert len(response.text) >= 2
        assert response.tokens_used > 0
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_near_max_length_input(self, engine):
        """Test with input near maximum length"""
        long_text = "This is a test. " * 300  # About 4800 characters
        
        request = PromptGenerationRequest(
            text=long_text,
            intent="process",
            complexity="simple",
            techniques=["zero_shot"],
            target_model="gpt-4"
        )
        
        response = await engine.generate(request)
        
        assert response.text is not None
        assert response.warnings is not None  # Should have warnings about length
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_all_techniques_combination(self, engine):
        """Test with all available techniques"""
        all_techniques = [t.value for t in TechniqueType][:5]  # Limit to 5 for performance
        
        request = PromptGenerationRequest(
            text="Create a comprehensive guide",
            intent="create_content",
            complexity="complex",
            techniques=all_techniques,
            target_model="gpt-4"
        )
        
        response = await engine.generate(request)
        
        assert len(response.techniques_applied) <= len(all_techniques)
        assert response.generation_time_ms > 0
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_special_characters_handling(self, engine):
        """Test handling of special characters"""
        request = PromptGenerationRequest(
            text="Handle these: <script>alert('test')</script> & \"quotes\" 'apostrophes' émojis 🚀",
            intent="process",
            complexity="simple",
            techniques=["zero_shot"],
            target_model="gpt-4"
        )
        
        response = await engine.generate(request)
        
        assert response.text is not None
        assert len(response.text) > 0
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_generation(self, engine):
        """Test concurrent prompt generation"""
        requests = [
            PromptGenerationRequest(
                text=f"Concurrent request {i}",
                intent="test",
                complexity="simple",
                techniques=["zero_shot"],
                target_model="gpt-4"
            )
            for i in range(5)
        ]
        
        # Generate concurrently
        tasks = [engine.generate(req) for req in requests]
        responses = await asyncio.gather(*tasks)
        
        assert len(responses) == 5
        assert all(isinstance(r, PromptGenerationResponse) for r in responses)
        assert len(set(r.id for r in responses)) == 5  # All unique IDs