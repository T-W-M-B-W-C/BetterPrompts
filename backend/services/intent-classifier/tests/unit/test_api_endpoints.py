"""Unit tests for intent classifier API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
import time

from app.api.v1.intents import (
    classify_intent,
    classify_intents_batch,
    get_intent_types
)
from app.schemas.intent import IntentRequest, IntentBatchRequest
from app.models.torchserve_client import (
    TorchServeError,
    TorchServeConnectionError,
    TorchServeInferenceError
)


class TestClassifyIntentEndpoint:
    """Test suite for the classify intent endpoint."""
    
    @pytest.mark.asyncio
    async def test_classify_intent_success(self, mock_cache_service):
        """Test successful intent classification."""
        # Arrange
        request = IntentRequest(text="Write a Python function to calculate fibonacci")
        mock_classifier = AsyncMock()
        mock_classifier.classify = AsyncMock(return_value={
            "intent": "code_generation",
            "confidence": 0.95,
            "complexity": "moderate",
            "suggested_techniques": ["chain_of_thought", "few_shot"],
            "tokens_used": 15
        })
        
        with patch('app.api.v1.intents.classifier', mock_classifier), \
             patch('app.api.v1.intents.settings.ENABLE_CACHING', True), \
             patch('app.api.v1.intents.settings.MODEL_VERSION', "1.0.0"):
            
            # Act
            response = await classify_intent(request, cache=mock_cache_service)
            
            # Assert
            assert response.intent == "code_generation"
            assert response.confidence == 0.95
            assert response.complexity == "moderate"
            assert response.suggested_techniques == ["chain_of_thought", "few_shot"]
            assert "processing_time" in response.metadata
            assert response.metadata["model_version"] == "1.0.0"
            assert response.metadata["tokens_used"] == 15
            
            # Verify cache was checked and set
            mock_cache_service.get_intent.assert_called_once()
            mock_cache_service.set_intent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_classify_intent_cache_hit(self, mock_cache_service):
        """Test classification with cache hit."""
        # Arrange
        cached_result = {
            "intent": "question_answering",
            "confidence": 0.92,
            "complexity": "simple",
            "suggested_techniques": ["direct_answer"],
            "metadata": {"cached": True}
        }
        mock_cache_service.get_intent.return_value = cached_result
        request = IntentRequest(text="What is the capital of France?")
        
        with patch('app.api.v1.intents.settings.ENABLE_CACHING', True):
            # Act
            response = await classify_intent(request, cache=mock_cache_service)
            
            # Assert
            assert response.intent == "question_answering"
            assert response.confidence == 0.92
            assert response.metadata["cached"] is True
            
            # Verify classifier was not called
            mock_cache_service.set_intent.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_classify_intent_torchserve_connection_error(self, mock_cache_service):
        """Test handling of TorchServe connection errors."""
        # Arrange
        request = IntentRequest(text="Test input")
        mock_classifier = AsyncMock()
        mock_classifier.classify = AsyncMock(
            side_effect=TorchServeConnectionError("Connection refused")
        )
        
        with patch('app.api.v1.intents.classifier', mock_classifier), \
             patch('app.api.v1.intents.settings.ENABLE_CACHING', False):
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await classify_intent(request, cache=mock_cache_service)
            
            assert exc_info.value.status_code == 503
            assert "temporarily unavailable" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_classify_intent_torchserve_inference_error(self, mock_cache_service):
        """Test handling of TorchServe inference errors."""
        # Arrange
        request = IntentRequest(text="Test input")
        mock_classifier = AsyncMock()
        mock_classifier.classify = AsyncMock(
            side_effect=TorchServeInferenceError("Model inference failed")
        )
        
        with patch('app.api.v1.intents.classifier', mock_classifier):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await classify_intent(request, cache=mock_cache_service)
            
            assert exc_info.value.status_code == 500
            assert "inference failed" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_classify_intent_validation_error(self, mock_cache_service):
        """Test handling of validation errors."""
        # Arrange
        request = IntentRequest(text="")  # Empty text
        mock_classifier = AsyncMock()
        mock_classifier.classify = AsyncMock(
            side_effect=ValueError("Input text cannot be empty")
        )
        
        with patch('app.api.v1.intents.classifier', mock_classifier):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await classify_intent(request, cache=mock_cache_service)
            
            assert exc_info.value.status_code == 400
            assert "Input text cannot be empty" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_classify_intent_unexpected_error(self, mock_cache_service):
        """Test handling of unexpected errors."""
        # Arrange
        request = IntentRequest(text="Test input")
        mock_classifier = AsyncMock()
        mock_classifier.classify = AsyncMock(
            side_effect=Exception("Unexpected error occurred")
        )
        
        with patch('app.api.v1.intents.classifier', mock_classifier):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await classify_intent(request, cache=mock_cache_service)
            
            assert exc_info.value.status_code == 500
            assert "unexpected error occurred" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_classify_intent_performance(self, mock_cache_service):
        """Test that classification completes within performance budget."""
        # Arrange
        request = IntentRequest(text="Test performance")
        mock_classifier = AsyncMock()
        
        async def delayed_classify(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms delay
            return {
                "intent": "test",
                "confidence": 0.9,
                "complexity": "simple",
                "suggested_techniques": ["test"],
                "tokens_used": 10
            }
        
        mock_classifier.classify = delayed_classify
        
        with patch('app.api.v1.intents.classifier', mock_classifier), \
             patch('app.api.v1.intents.settings.ENABLE_CACHING', False):
            
            # Act
            start_time = time.time()
            response = await classify_intent(request, cache=mock_cache_service)
            elapsed_time = time.time() - start_time
            
            # Assert
            assert elapsed_time < 0.2  # Should complete within 200ms
            assert response.metadata["processing_time"] < 0.2


class TestBatchClassifyEndpoint:
    """Test suite for the batch classify endpoint."""
    
    @pytest.mark.asyncio
    async def test_batch_classify_success(self, mock_cache_service):
        """Test successful batch classification."""
        # Arrange
        texts = [
            "Write a function to sort an array",
            "What is machine learning?",
            "Translate this to Spanish"
        ]
        request = IntentBatchRequest(texts=texts)
        
        mock_classifier = AsyncMock()
        mock_classifier.classify = AsyncMock(side_effect=[
            {
                "intent": "code_generation",
                "confidence": 0.94,
                "complexity": "moderate",
                "suggested_techniques": ["chain_of_thought"],
                "tokens_used": 12
            },
            {
                "intent": "question_answering",
                "confidence": 0.96,
                "complexity": "simple",
                "suggested_techniques": ["direct_answer"],
                "tokens_used": 8
            },
            {
                "intent": "translation",
                "confidence": 0.98,
                "complexity": "simple",
                "suggested_techniques": ["few_shot"],
                "tokens_used": 10
            }
        ])
        
        with patch('app.api.v1.intents.classifier', mock_classifier), \
             patch('app.api.v1.intents.settings.ENABLE_CACHING', True), \
             patch('app.api.v1.intents.settings.MODEL_VERSION', "1.0.0"):
            
            # Act
            response = await classify_intents_batch(request, cache=mock_cache_service)
            
            # Assert
            assert len(response.results) == 3
            assert response.results[0].intent == "code_generation"
            assert response.results[1].intent == "question_answering"
            assert response.results[2].intent == "translation"
            assert response.total_processing_time > 0
            
            # Verify cache operations
            assert mock_cache_service.get_intent.call_count == 3
            assert mock_cache_service.set_intent.call_count == 3
    
    @pytest.mark.asyncio
    async def test_batch_classify_with_cache_hits(self, mock_cache_service):
        """Test batch classification with some cache hits."""
        # Arrange
        texts = ["Cached query", "New query"]
        request = IntentBatchRequest(texts=texts)
        
        # First text is cached
        mock_cache_service.get_intent.side_effect = [
            {
                "intent": "cached_intent",
                "confidence": 0.85,
                "complexity": "simple",
                "suggested_techniques": ["cached"],
                "metadata": {"cached": True}
            },
            None  # Second text not cached
        ]
        
        mock_classifier = AsyncMock()
        mock_classifier.classify = AsyncMock(return_value={
            "intent": "new_intent",
            "confidence": 0.90,
            "complexity": "moderate",
            "suggested_techniques": ["new"],
            "tokens_used": 15
        })
        
        with patch('app.api.v1.intents.classifier', mock_classifier), \
             patch('app.api.v1.intents.settings.ENABLE_CACHING', True):
            
            # Act
            response = await classify_intents_batch(request, cache=mock_cache_service)
            
            # Assert
            assert len(response.results) == 2
            assert response.results[0].intent == "cached_intent"
            assert response.results[1].intent == "new_intent"
            
            # Verify classifier was called only once (for non-cached item)
            mock_classifier.classify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_classify_max_size_limit(self, mock_cache_service):
        """Test batch classification respects maximum batch size."""
        # Arrange
        texts = ["Text " + str(i) for i in range(150)]  # Exceeds typical max
        request = IntentBatchRequest(texts=texts)
        
        mock_classifier = AsyncMock()
        mock_classifier.classify = AsyncMock(return_value={
            "intent": "test",
            "confidence": 0.9,
            "complexity": "simple",
            "suggested_techniques": ["test"],
            "tokens_used": 5
        })
        
        with patch('app.api.v1.intents.classifier', mock_classifier), \
             patch('app.api.v1.intents.settings.ENABLE_CACHING', False):
            
            # Act
            response = await classify_intents_batch(request, cache=mock_cache_service)
            
            # Assert
            # Batch size is limited by schema validation (max 100)
            assert len(response.results) <= 100
    
    @pytest.mark.asyncio
    async def test_batch_classify_torchserve_error(self, mock_cache_service):
        """Test batch classification handles TorchServe errors."""
        # Arrange
        request = IntentBatchRequest(texts=["Test1", "Test2"])
        mock_classifier = AsyncMock()
        mock_classifier.classify = AsyncMock(
            side_effect=TorchServeConnectionError("Connection failed")
        )
        
        with patch('app.api.v1.intents.classifier', mock_classifier), \
             patch('app.api.v1.intents.settings.ENABLE_CACHING', False):
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await classify_intents_batch(request, cache=mock_cache_service)
            
            assert exc_info.value.status_code == 503


class TestGetIntentTypesEndpoint:
    """Test suite for the get intent types endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_intent_types_success(self):
        """Test getting available intent types."""
        # Act
        response = await get_intent_types()
        
        # Assert
        assert "intent_types" in response
        assert "complexity_levels" in response
        assert "techniques" in response
        
        # Verify expected intent types
        intent_types = response["intent_types"]
        assert "question_answering" in intent_types
        assert "creative_writing" in intent_types
        assert "code_generation" in intent_types
        assert "data_analysis" in intent_types
        assert "reasoning" in intent_types
        assert "summarization" in intent_types
        assert "translation" in intent_types
        assert "conversation" in intent_types
        assert "task_planning" in intent_types
        assert "problem_solving" in intent_types
        
        # Verify complexity levels
        complexity_levels = response["complexity_levels"]
        assert "simple" in complexity_levels
        assert "moderate" in complexity_levels
        assert "complex" in complexity_levels
        
        # Verify techniques
        techniques = response["techniques"]
        assert "chain_of_thought" in techniques
        assert "tree_of_thoughts" in techniques
        assert "few_shot" in techniques
        assert "zero_shot" in techniques
        assert "self_consistency" in techniques
        assert "constitutional_ai" in techniques
        assert "iterative_refinement" in techniques
    
    @pytest.mark.asyncio
    async def test_get_intent_types_structure(self):
        """Test the structure of intent types response."""
        # Act
        response = await get_intent_types()
        
        # Assert
        assert isinstance(response, dict)
        assert isinstance(response["intent_types"], list)
        assert isinstance(response["complexity_levels"], list)
        assert isinstance(response["techniques"], list)
        
        # All lists should have items
        assert len(response["intent_types"]) > 0
        assert len(response["complexity_levels"]) > 0
        assert len(response["techniques"]) > 0


# Import asyncio for performance test
import asyncio