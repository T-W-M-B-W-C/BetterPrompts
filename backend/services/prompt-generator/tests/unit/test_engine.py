"""
Unit tests for prompt generation engine
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time
from datetime import datetime
from uuid import uuid4

from app.engine import PromptGenerationEngine
from app.models import (
    PromptGenerationRequest,
    PromptGenerationResponse,
    TechniqueType,
    ValidationResult,
    EnhancementMetrics
)
from app.techniques.base import BaseTechnique, technique_registry
from app.validators import PromptValidator


class MockTechnique(BaseTechnique):
    """Mock technique for testing"""
    
    def apply(self, text, context=None):
        return f"[{self.name}] {text}"
        
    def validate_input(self, text, context=None):
        return True


class TestPromptGenerationEngine:
    """Test the PromptGenerationEngine class"""
    
    @pytest.fixture
    def engine(self):
        """Create an engine instance for testing"""
        with patch.object(PromptGenerationEngine, '_initialize_techniques'):
            engine = PromptGenerationEngine()
            engine.validator = MagicMock(spec=PromptValidator)
            return engine
            
    @pytest.fixture
    def mock_request(self):
        """Create a mock generation request"""
        return PromptGenerationRequest(
            text="Explain machine learning",
            intent="explain_concept",
            complexity="moderate",
            techniques=["chain_of_thought", "analogical"],
            context={"domain": "ai"},
            target_model="gpt-4"
        )
        
    @pytest.mark.asyncio
    async def test_generate_success(self, engine, mock_request):
        """Test successful prompt generation"""
        # Mock validation
        validation_result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Minor warning"],
            suggestions=[],
            token_count=50,
            complexity_score=0.6,
            readability_score=0.8
        )
        engine.validator.validate_prompt = AsyncMock(return_value=validation_result)
        
        # Mock technique application
        with patch.object(engine, '_apply_techniques', return_value="Enhanced prompt text"):
            with patch.object(engine, '_calculate_metrics', return_value=EnhancementMetrics(
                clarity_score=0.8,
                specificity_score=0.7,
                coherence_score=0.9,
                technique_effectiveness={"chain_of_thought": 0.85, "analogical": 0.75},
                overall_quality=0.8,
                improvement_percentage=25.0
            )):
                response = await engine.generate(mock_request)
                
                # Verify response
                assert isinstance(response, PromptGenerationResponse)
                assert response.text == "Enhanced prompt text"
                assert response.original_text == mock_request.text
                assert response.techniques_applied == mock_request.techniques
                assert response.warnings == ["Minor warning"]
                assert response.confidence_score == 0.8
                assert response.generation_time_ms > 0
                
    @pytest.mark.asyncio
    async def test_generate_validation_failure(self, engine, mock_request):
        """Test generation with validation failure"""
        # Mock validation failure
        validation_result = ValidationResult(
            is_valid=False,
            errors=["Invalid prompt format", "Too long"],
            warnings=[],
            suggestions=[],
            token_count=0,
            complexity_score=0,
            readability_score=0
        )
        engine.validator.validate_prompt = AsyncMock(return_value=validation_result)
        
        with pytest.raises(ValueError) as exc_info:
            await engine.generate(mock_request)
            
        assert "Invalid request" in str(exc_info.value)
        assert "Invalid prompt format" in str(exc_info.value)
        
    @pytest.mark.asyncio
    async def test_generate_technique_failure(self, engine, mock_request):
        """Test generation when technique application fails"""
        # Mock successful validation
        validation_result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            suggestions=[],
            token_count=50,
            complexity_score=0.6,
            readability_score=0.8
        )
        engine.validator.validate_prompt = AsyncMock(return_value=validation_result)
        
        # Mock technique failure
        with patch.object(engine, '_apply_techniques', side_effect=Exception("Technique error")):
            with pytest.raises(Exception) as exc_info:
                await engine.generate(mock_request)
                
            assert "Technique error" in str(exc_info.value)
            
    @pytest.mark.asyncio
    async def test_prepare_context(self, engine, mock_request):
        """Test context preparation"""
        context = engine._prepare_context(mock_request)
        
        assert context["intent"] == "explain_concept"
        assert context["complexity"] == "moderate"
        assert context["target_model"] == "gpt-4"
        assert context["domain"] == "ai"  # From request context
        assert "temperature" in context
        
    @pytest.mark.asyncio
    async def test_prepare_context_with_parameters(self, engine):
        """Test context preparation with parameters"""
        request = PromptGenerationRequest(
            text="Test",
            intent="test",
            complexity="simple",
            techniques=["chain_of_thought"],
            parameters={"depth": 3, "format": "json"},
            temperature=0.5
        )
        
        context = engine._prepare_context(request)
        
        assert context["temperature"] == 0.5
        assert context["parameters"]["depth"] == 3
        assert context["parameters"]["format"] == "json"
        
    def test_sort_techniques_by_priority(self, engine):
        """Test technique sorting by priority"""
        # Create mock techniques with different priorities
        mock_techniques = {
            "tech1": MagicMock(priority=1),
            "tech2": MagicMock(priority=5),
            "tech3": MagicMock(priority=3)
        }
        
        with patch.object(technique_registry, 'get_instance', side_effect=lambda x: mock_techniques.get(x)):
            sorted_techs = engine._sort_techniques_by_priority(["tech1", "tech2", "tech3"])
            
            assert sorted_techs == ["tech2", "tech3", "tech1"]  # Sorted by priority desc
            
    def test_post_process(self, engine, mock_request):
        """Test prompt post-processing"""
        # Test whitespace cleanup
        prompt = "  This   has   extra    spaces  "
        result = engine._post_process(prompt, mock_request)
        assert result == "This has extra spaces"
        
        # Test length constraint
        mock_request.max_tokens = 10  # Very short for testing
        long_prompt = "This is a very long prompt that should be truncated"
        result = engine._post_process(long_prompt, mock_request)
        assert result.endswith("...")
        assert len(result) <= 50  # Approximate char limit
        
    def test_estimate_tokens(self, engine):
        """Test token estimation"""
        text = "This is a test prompt with approximately 12 words in it."
        token_count = engine._estimate_tokens(text)
        
        # Should be approximately 1/4 of character count
        assert 10 <= token_count <= 20
        
    def test_calculate_clarity_score(self, engine):
        """Test clarity score calculation"""
        original = "Explain ML"
        
        # Test with structured enhancement
        enhanced1 = "Explain ML\n\n1. First, let's define ML\n2. Then discuss applications"
        score1 = engine._calculate_clarity_score(original, enhanced1)
        assert score1 > 0.7
        
        # Test without structure
        enhanced2 = "Explain ML in detail please"
        score2 = engine._calculate_clarity_score(original, enhanced2)
        assert score2 < score1
        
    def test_calculate_specificity_score(self, engine):
        """Test specificity score calculation"""
        original = "Write code"
        
        # Test with specific instructions
        enhanced1 = "Write code specifically following these steps. Ensure you include error handling and must provide tests."
        score1 = engine._calculate_specificity_score(original, enhanced1)
        assert score1 > 0.7
        
        # Test without specificity
        enhanced2 = "Write some code for me"
        score2 = engine._calculate_specificity_score(original, enhanced2)
        assert score2 < score1
        
    def test_calculate_coherence_score(self, engine):
        """Test coherence score calculation"""
        # Test with transitions
        enhanced1 = "First, understand the problem. Then, design a solution. Next, implement it. Finally, test thoroughly."
        score1 = engine._calculate_coherence_score(enhanced1)
        assert score1 > 0.8
        
        # Test without transitions
        enhanced2 = "Understand problem. Design solution. Implement. Test."
        score2 = engine._calculate_coherence_score(enhanced2)
        assert score2 < score1
        
    def test_calculate_technique_effectiveness(self, engine):
        """Test technique effectiveness calculation"""
        original = "Solve this problem"
        
        # Test chain of thought effectiveness
        enhanced_cot = "Let's think step by step about this problem"
        score_cot = engine._calculate_technique_effectiveness(
            TechniqueType.CHAIN_OF_THOUGHT.value,
            original,
            enhanced_cot
        )
        assert score_cot > 0.8
        
        # Test few shot effectiveness
        enhanced_fs = "Here's an example: Input: X, Output: Y. Now solve this problem"
        score_fs = engine._calculate_technique_effectiveness(
            TechniqueType.FEW_SHOT.value,
            original,
            enhanced_fs
        )
        assert score_fs > 0.8
        
        # Test unknown technique
        score_unknown = engine._calculate_technique_effectiveness(
            "unknown_technique",
            original,
            "Enhanced text"
        )
        assert score_unknown == 0.75  # Default score
        
    @pytest.mark.asyncio
    async def test_calculate_metrics(self, engine):
        """Test overall metrics calculation"""
        original = "Explain AI"
        enhanced = "Let's think step by step about AI. First, AI stands for..."
        techniques = ["chain_of_thought"]
        
        metrics = await engine._calculate_metrics(original, enhanced, techniques)
        
        assert isinstance(metrics, EnhancementMetrics)
        assert 0 <= metrics.clarity_score <= 1
        assert 0 <= metrics.specificity_score <= 1
        assert 0 <= metrics.coherence_score <= 1
        assert 0 <= metrics.overall_quality <= 1
        assert metrics.improvement_percentage != 0
        assert "chain_of_thought" in metrics.technique_effectiveness
        
    @pytest.mark.asyncio
    async def test_calculate_metrics_error_handling(self, engine):
        """Test metrics calculation error handling"""
        with patch.object(engine, '_calculate_clarity_score', side_effect=Exception("Calc error")):
            metrics = await engine._calculate_metrics("test", "enhanced", ["test"])
            
            # Should return None on error
            assert metrics is None
            
    @pytest.mark.asyncio
    async def test_apply_techniques(self, engine):
        """Test technique application"""
        # Set up mock techniques in registry
        mock_technique1 = MockTechnique({"name": "tech1", "priority": 2})
        mock_technique2 = MockTechnique({"name": "tech2", "priority": 1})
        
        with patch.object(technique_registry, 'get_instance') as mock_get:
            with patch.object(technique_registry, 'apply_technique') as mock_apply:
                mock_get.side_effect = lambda x: {"tech1": mock_technique1, "tech2": mock_technique2}.get(x)
                mock_apply.side_effect = lambda t, text, ctx: f"[{t}] {text}"
                
                result = await engine._apply_techniques(
                    "Original text",
                    ["tech1", "tech2"],
                    {"test": "context"}
                )
                
                # Should apply techniques in priority order
                assert mock_apply.call_count == 2
                # tech1 has higher priority (2 > 1), so it should be applied first
                first_call = mock_apply.call_args_list[0]
                assert first_call[0][0] == "tech1"
                
    @pytest.mark.asyncio
    async def test_apply_techniques_error_recovery(self, engine):
        """Test technique application with errors"""
        with patch.object(technique_registry, 'get_instance', return_value=MockTechnique({"name": "test"})):
            with patch.object(technique_registry, 'apply_technique') as mock_apply:
                # First technique fails, second succeeds
                mock_apply.side_effect = [
                    Exception("Technique 1 failed"),
                    "[tech2] Enhanced text"
                ]
                
                result = await engine._apply_techniques(
                    "Original",
                    ["tech1", "tech2"],
                    {}
                )
                
                # Should continue with second technique despite first failure
                assert result == "[tech2] Enhanced text"
                
    def test_load_technique_config(self, engine):
        """Test technique configuration loading"""
        config = engine._load_technique_config("test_technique")
        
        assert config["name"] == "test_technique"
        assert config["enabled"] is True
        assert config["priority"] == 1
        assert isinstance(config["parameters"], dict)
        
    @pytest.mark.asyncio
    async def test_validate_request(self, engine, mock_request):
        """Test request validation"""
        mock_validation = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            suggestions=[],
            token_count=100,
            complexity_score=0.5,
            readability_score=0.8
        )
        
        engine.validator.validate_prompt = AsyncMock(return_value=mock_validation)
        
        result = await engine._validate_request(mock_request)
        
        assert result.is_valid
        assert result.token_count == 100
        
        # Verify validator was called with correct params
        engine.validator.validate_prompt.assert_called_once()
        call_args = engine.validator.validate_prompt.call_args
        assert call_args[0][0] == mock_request.text
        assert call_args[0][1]["techniques"] == mock_request.techniques
        
    @pytest.mark.asyncio
    async def test_generate_with_no_techniques(self, engine):
        """Test generation with empty techniques list"""
        request = PromptGenerationRequest(
            text="Simple prompt",
            intent="test",
            complexity="simple",
            techniques=[]  # No techniques
        )
        
        validation_result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            suggestions=[],
            token_count=10,
            complexity_score=0.2,
            readability_score=0.9
        )
        engine.validator.validate_prompt = AsyncMock(return_value=validation_result)
        
        with patch.object(engine, '_calculate_metrics', return_value=None):
            response = await engine.generate(request)
            
            # Should return original text when no techniques
            assert response.text == "Simple prompt"
            assert response.techniques_applied == []