"""Unit tests for the intent classifier model."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import torch
import numpy as np

from app.models.classifier import IntentClassifier
from app.models.torchserve_client import (
    TorchServeClient,
    TorchServeError,
    TorchServeConnectionError,
    TorchServeInferenceError
)


class TestIntentClassifier:
    """Test suite for IntentClassifier class."""
    
    @pytest.fixture
    def classifier(self):
        """Create an IntentClassifier instance."""
        return IntentClassifier()
    
    @pytest.mark.asyncio
    async def test_initialize_model_torchserve_mode(self, classifier):
        """Test model initialization in TorchServe mode."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.health_check = AsyncMock(return_value=True)
        
        with patch('app.models.classifier.settings.USE_TORCHSERVE', True), \
             patch('app.models.classifier.TorchServeClient', return_value=mock_client):
            
            # Act
            await classifier.initialize_model()
            
            # Assert
            assert classifier._initialized is True
            assert classifier.torchserve_client is not None
            mock_client.connect.assert_called_once()
            mock_client.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_model_torchserve_unhealthy(self, classifier):
        """Test model initialization when TorchServe is unhealthy."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.health_check = AsyncMock(return_value=False)
        
        with patch('app.models.classifier.settings.USE_TORCHSERVE', True), \
             patch('app.models.classifier.TorchServeClient', return_value=mock_client):
            
            # Act & Assert
            with pytest.raises(TorchServeConnectionError):
                await classifier.initialize_model()
            
            assert classifier._initialized is False
    
    @pytest.mark.asyncio
    async def test_initialize_model_local_mode(self, classifier):
        """Test model initialization in local mode."""
        # Arrange
        mock_tokenizer = MagicMock()
        mock_model = MagicMock()
        
        with patch('app.models.classifier.settings.USE_TORCHSERVE', False), \
             patch('app.models.classifier.settings.MODEL_NAME', 'test-model'), \
             patch('app.models.classifier.AutoTokenizer.from_pretrained', return_value=mock_tokenizer), \
             patch('app.models.classifier.AutoModelForSequenceClassification.from_pretrained', return_value=mock_model):
            
            # Act
            await classifier.initialize_model()
            
            # Assert
            assert classifier._initialized is True
            assert classifier.tokenizer is not None
            assert classifier.model is not None
    
    @pytest.mark.asyncio
    async def test_classify_not_initialized(self, classifier):
        """Test classification when model is not initialized."""
        # Act & Assert
        with pytest.raises(RuntimeError, match="Model not initialized"):
            await classifier.classify("Test text")
    
    @pytest.mark.asyncio
    async def test_classify_torchserve_mode(self, classifier):
        """Test classification using TorchServe."""
        # Arrange
        classifier._initialized = True
        classifier.use_torchserve = True
        
        mock_torchserve_response = {
            "intent": "code_generation",
            "confidence": 0.95,
            "complexity": {"level": "moderate", "score": 0.6},
            "techniques": [
                {"name": "chain_of_thought", "score": 0.8},
                {"name": "few_shot", "score": 0.7}
            ],
            "all_intents": {
                "code_generation": 0.95,
                "question_answering": 0.03,
                "creative_writing": 0.02
            },
            "metadata": {
                "tokens_used": 25,
                "inference_time_ms": 150
            }
        }
        
        mock_client = AsyncMock()
        mock_client.classify = AsyncMock(return_value=mock_torchserve_response)
        classifier.torchserve_client = mock_client
        
        # Act
        result = await classifier.classify("Write a Python function")
        
        # Assert
        assert result["intent"] == "code_generation"
        assert result["confidence"] == 0.95
        assert result["complexity"] == "moderate"
        assert result["suggested_techniques"] == ["chain_of_thought", "few_shot"]
        assert result["tokens_used"] == 25
        assert "all_probabilities" in result
        assert "torchserve_metadata" in result
        
        mock_client.classify.assert_called_once_with("Write a Python function")
    
    @pytest.mark.asyncio
    async def test_classify_local_mode(self, classifier):
        """Test classification using local model."""
        # Arrange
        classifier._initialized = True
        classifier.use_torchserve = False
        
        # Mock tokenizer
        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {
            "input_ids": torch.tensor([[101, 2023, 2003, 102]]),
            "attention_mask": torch.tensor([[1, 1, 1, 1]])
        }
        classifier.tokenizer = mock_tokenizer
        
        # Mock model
        mock_model = MagicMock()
        mock_outputs = MagicMock()
        mock_outputs.logits = torch.tensor([[2.0, 3.5, 1.0, 0.5, -1.0, -2.0, -3.0, -4.0, -5.0, -6.0]])
        mock_model.return_value = mock_outputs
        classifier.model = mock_model
        
        with patch('app.models.classifier.settings.MODEL_MAX_LENGTH', 512):
            # Act
            result = await classifier.classify("Write a Python function")
            
            # Assert
            assert result["intent"] in classifier.intent_labels
            assert 0 <= result["confidence"] <= 1
            assert result["complexity"] in ["simple", "moderate", "complex"]
            assert isinstance(result["suggested_techniques"], list)
            assert result["tokens_used"] > 0
            assert "all_probabilities" in result
    
    @pytest.mark.asyncio
    async def test_classify_torchserve_error_handling(self, classifier):
        """Test error handling for TorchServe errors."""
        # Arrange
        classifier._initialized = True
        classifier.use_torchserve = True
        
        mock_client = AsyncMock()
        mock_client.classify = AsyncMock(side_effect=TorchServeInferenceError("Inference failed"))
        classifier.torchserve_client = mock_client
        
        # Act & Assert
        with pytest.raises(TorchServeInferenceError):
            await classifier.classify("Test text")
    
    def test_determine_complexity_simple(self, classifier):
        """Test complexity determination for simple tasks."""
        # Test cases for simple complexity
        simple_cases = [
            ("What is 2+2?", 0.95),
            ("Hello world", 0.98),
            ("Define Python", 0.90),
        ]
        
        for text, confidence in simple_cases:
            complexity = classifier._determine_complexity(text, confidence)
            assert complexity == "simple"
    
    def test_determine_complexity_moderate(self, classifier):
        """Test complexity determination for moderate tasks."""
        # Test cases for moderate complexity
        moderate_cases = [
            ("Write a function to sort an array and handle edge cases", 0.85),
            ("Explain machine learning concepts. Also provide examples.", 0.80),
            ("Compare Python and Java for web development", 0.75),
        ]
        
        for text, confidence in moderate_cases:
            complexity = classifier._determine_complexity(text, confidence)
            assert complexity == "moderate"
    
    def test_determine_complexity_complex(self, classifier):
        """Test complexity determination for complex tasks."""
        # Test case for complex task
        complex_text = """
        Design a distributed system for processing real-time data streams.
        The system should handle millions of events per second, provide fault tolerance,
        and support horizontal scaling. Include considerations for data consistency,
        latency requirements, and monitoring. Also compare different architectural patterns
        and provide implementation details.
        """
        
        complexity = classifier._determine_complexity(complex_text, 0.70)
        assert complexity == "complex"
    
    @pytest.mark.asyncio
    async def test_cleanup_torchserve_mode(self, classifier):
        """Test cleanup in TorchServe mode."""
        # Arrange
        classifier._initialized = True
        classifier.use_torchserve = True
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        classifier.torchserve_client = mock_client
        
        # Act
        await classifier.cleanup()
        
        # Assert
        assert classifier._initialized is False
        assert classifier.torchserve_client is None
        mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_local_mode(self, classifier):
        """Test cleanup in local mode."""
        # Arrange
        classifier._initialized = True
        classifier.use_torchserve = False
        classifier.model = MagicMock()
        classifier.tokenizer = MagicMock()
        classifier.device = torch.device("cpu")
        
        # Act
        await classifier.cleanup()
        
        # Assert
        assert classifier._initialized is False
        assert classifier.model is None
        assert classifier.tokenizer is None
    
    @pytest.mark.asyncio
    async def test_cleanup_cuda_cache(self, classifier):
        """Test CUDA cache cleanup when using GPU."""
        # Arrange
        classifier._initialized = True
        classifier.use_torchserve = False
        classifier.model = MagicMock()
        classifier.tokenizer = MagicMock()
        
        # Mock CUDA device
        mock_device = MagicMock()
        mock_device.type = "cuda"
        classifier.device = mock_device
        
        with patch('torch.cuda.empty_cache') as mock_empty_cache:
            # Act
            await classifier.cleanup()
            
            # Assert
            mock_empty_cache.assert_called_once()
    
    def test_is_initialized(self, classifier):
        """Test is_initialized method."""
        # Initially not initialized
        assert classifier.is_initialized() is False
        
        # After setting initialized flag
        classifier._initialized = True
        assert classifier.is_initialized() is True
    
    def test_intent_labels(self, classifier):
        """Test that all expected intent labels are present."""
        expected_labels = [
            "question_answering",
            "creative_writing",
            "code_generation",
            "data_analysis",
            "reasoning",
            "summarization",
            "translation",
            "conversation",
            "task_planning",
            "problem_solving",
        ]
        
        assert classifier.intent_labels == expected_labels
    
    def test_technique_mapping(self, classifier):
        """Test that technique mapping covers all intents."""
        # Verify all intents have technique mappings
        for intent in classifier.intent_labels:
            assert intent in classifier.technique_mapping
            assert isinstance(classifier.technique_mapping[intent], list)
            assert len(classifier.technique_mapping[intent]) > 0
    
    def test_complexity_thresholds(self, classifier):
        """Test complexity threshold values."""
        thresholds = classifier.complexity_thresholds
        
        # Verify threshold ordering
        assert thresholds["simple"] > thresholds["moderate"]
        assert thresholds["moderate"] > thresholds["complex"]
        assert thresholds["complex"] == 0.0
        
        # Verify threshold ranges
        assert 0.0 <= thresholds["complex"] < thresholds["moderate"]
        assert thresholds["moderate"] < thresholds["simple"] <= 1.0