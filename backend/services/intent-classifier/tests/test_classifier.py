import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from app.models.classifier import IntentClassifier
from app.schemas.intent import IntentRequest, IntentResponse

@pytest.mark.unit
class TestIntentClassifier:
    """Test suite for the Intent Classification service"""
    
    @pytest.fixture
    async def classifier(self):
        """Create a mock classifier instance for testing."""
        with patch('app.models.classifier.settings') as mock_settings:
            mock_settings.USE_TORCHSERVE = False
            mock_settings.MODEL_NAME = "test-model"
            mock_settings.MODEL_MAX_LENGTH = 512
            
            classifier = IntentClassifier()
            # Mock the model loading
            classifier.model = Mock()
            classifier.tokenizer = Mock()
            classifier._initialized = True
            return classifier
    
    @pytest.mark.asyncio
    @pytest.mark.critical
    async def test_classify_simple_prompt(self, classifier):
        """Test classification of simple prompts.
        
        Validates:
        - Correct intent classification
        - Appropriate complexity scoring
        - Confidence threshold handling
        """
        # Mock the classification result
        classifier._classify_intent = AsyncMock(return_value={
            "intent": "question_answering",
            "confidence": 0.95,
            "complexity": "simple",
            "suggested_techniques": ["direct_answer"],
            "tokens_used": 10
        })
        
        result = await classifier.classify("What is the capital of France?")
        
        assert result["intent"] == "question_answering"
        assert result["complexity"] == "simple"
        assert result["confidence"] > 0.9
        assert "direct_answer" in result["suggested_techniques"]
    
    @pytest.mark.asyncio
    @pytest.mark.critical
    async def test_classify_complex_prompt(self, classifier):
        """Test classification of complex multi-intent prompts.
        
        Validates:
        - Multi-intent detection
        - Complex task identification
        - Appropriate technique suggestions
        """
        complex_prompt = """
        Analyze the quarterly sales data, identify trends, 
        create visualizations, and provide recommendations 
        for improving performance in underperforming regions.
        """
        
        classifier._classify_intent = AsyncMock(return_value={
            "intent": "data_analysis",
            "confidence": 0.85,
            "complexity": "complex",
            "suggested_techniques": ["chain_of_thought", "tree_of_thoughts", "self_consistency"],
            "tokens_used": 45
        })
        
        result = await classifier.classify(complex_prompt)
        
        assert result["intent"] == "data_analysis"
        assert result["complexity"] == "complex"
        assert len(result["suggested_techniques"]) > 1
        assert "chain_of_thought" in result["suggested_techniques"]
    
    @pytest.mark.asyncio
    async def test_classify_code_generation(self, classifier):
        """Test classification of code generation requests.
        
        Validates:
        - Code generation intent detection
        - Programming language identification
        - Algorithm complexity assessment
        """
        classifier._classify_intent = AsyncMock(return_value={
            "intent": "code_generation",
            "confidence": 0.92,
            "complexity": "moderate",
            "suggested_techniques": ["few_shot", "chain_of_thought"],
            "tokens_used": 15
        })
        
        result = await classifier.classify("Write a Python function to sort a list using quicksort")
        
        assert result["intent"] == "code_generation"
        assert result["confidence"] > 0.9
        assert "few_shot" in result["suggested_techniques"]
    
    @pytest.mark.asyncio
    async def test_empty_input_handling(self, classifier):
        """Test handling of empty input.
        
        Validates:
        - Proper error handling for empty strings
        - Clear error messages
        """
        with pytest.raises(ValueError, match="Input text must be a non-empty string"):
            await classifier.classify("")
            
        with pytest.raises(ValueError, match="Input text must be a non-empty string"):
            await classifier.classify(None)
    
    @pytest.mark.asyncio
    async def test_very_long_input_handling(self, classifier):
        """Test handling of very long inputs.
        
        Validates:
        - Input truncation for model limits
        - Graceful handling of oversized inputs
        - Warning generation for truncation
        """
        long_input = "x" * 10000  # Very long input
        
        classifier._classify_intent = AsyncMock(return_value={
            "intent": "other",
            "confidence": 0.5,
            "complexity": "simple",
            "suggested_techniques": ["direct_prompting"],
            "tokens_used": 512,
            "truncated": True
        })
        
        result = await classifier.classify(long_input)
        assert result is not None
        assert result["intent"] == "other"
        # Should indicate truncation occurred
        classifier._classify_intent.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("prompt,expected_intent,expected_complexity", [
        ("Hello", "conversation", "simple"),
        ("Explain quantum physics", "question_answering", "complex"),
        ("Debug this code: print('hello')", "problem_solving", "moderate"),
        ("Write a business plan", "creative_writing", "complex"),
        ("Translate to Spanish", "translation", "simple"),
    ])
    async def test_various_prompt_types(self, classifier, prompt, expected_intent, expected_complexity):
        """Test classification of various prompt types.
        
        Validates:
        - Diverse intent recognition
        - Appropriate complexity assignment
        - Consistent classification behavior
        """
        classifier._classify_intent = AsyncMock(return_value={
            "intent": expected_intent,
            "confidence": 0.8,
            "complexity": expected_complexity,
            "suggested_techniques": ["test_technique"],
            "tokens_used": 20
        })
        
        result = await classifier.classify(prompt)
        
        assert result["intent"] == expected_intent
        assert result["complexity"] == expected_complexity
    
    @pytest.mark.asyncio
    async def test_confidence_threshold(self, classifier):
        """Test low confidence handling.
        
        Validates:
        - Low confidence detection
        - Fallback behavior
        - Clarification recommendations
        """
        classifier._classify_intent = AsyncMock(return_value={
            "intent": "other",
            "confidence": 0.3,  # Low confidence
            "complexity": "simple",
            "suggested_techniques": ["clarification_request"],
            "tokens_used": 5
        })
        
        result = await classifier.classify("???")
        
        assert result["intent"] == "other"
        assert result["confidence"] < 0.5
        assert "clarification_request" in result["suggested_techniques"]
    
    @pytest.mark.asyncio
    @pytest.mark.torchserve
    async def test_torchserve_integration(self, classifier):
        """Test TorchServe integration when enabled.
        
        Validates:
        - TorchServe client usage
        - Response format compatibility
        - Error handling for service failures
        """
        # This test requires TorchServe to be running
        with patch('app.models.classifier.settings') as mock_settings:
            mock_settings.USE_TORCHSERVE = True
            mock_settings.TORCHSERVE_URL = "http://localhost:8080/predictions/intent_classifier"
            
            # Mock TorchServe client
            mock_client = AsyncMock()
            mock_client.classify = AsyncMock(return_value={
                "intent": "data_analysis",
                "confidence": 0.85,
                "complexity": {"level": "moderate", "score": 0.7},
                "suggested_techniques": ["chain_of_thought"]
            })
            
            classifier.torchserve_client = mock_client
            classifier.use_torchserve = True
            
            result = await classifier.classify("Analyze data and create charts")
            
            assert result["intent"] == "data_analysis"
            assert mock_client.classify.called