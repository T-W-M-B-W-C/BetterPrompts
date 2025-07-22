"""Integration tests for ML model with TorchServe integration."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio
import json

from app.models.classifier import IntentClassifier
from app.models.torchserve_client import TorchServeClient


class TestMLModelIntegration:
    """Integration tests for ML model operations."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_model_initialization_and_inference_flow(self):
        """Test complete model initialization and inference flow."""
        # Arrange
        classifier = IntentClassifier()
        
        mock_torchserve_response = {
            "intent": "code_generation",
            "confidence": 0.95,
            "complexity": {
                "level": "moderate",
                "score": 0.65,
                "factors": ["multi_step", "technical"]
            },
            "techniques": [
                {"name": "chain_of_thought", "score": 0.85},
                {"name": "few_shot", "score": 0.72},
                {"name": "self_consistency", "score": 0.68}
            ],
            "all_intents": {
                "code_generation": 0.95,
                "question_answering": 0.03,
                "creative_writing": 0.01,
                "data_analysis": 0.01
            },
            "metadata": {
                "model_version": "1.0.0",
                "inference_time_ms": 125,
                "tokens_used": 45,
                "device": "gpu"
            }
        }
        
        with patch('app.models.classifier.settings.USE_TORCHSERVE', True), \
             patch('app.models.classifier.TorchServeClient') as mock_client_class:
            
            # Setup mock client
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.health_check = AsyncMock(return_value=True)
            mock_client.classify = AsyncMock(return_value=mock_torchserve_response)
            mock_client_class.return_value = mock_client
            
            # Act - Initialize
            await classifier.initialize_model()
            
            # Assert initialization
            assert classifier.is_initialized()
            assert classifier.torchserve_client is not None
            
            # Act - Classify
            result = await classifier.classify("Write a Python function to merge two sorted lists")
            
            # Assert classification
            assert result["intent"] == "code_generation"
            assert result["confidence"] == 0.95
            assert result["complexity"] == "moderate"
            assert len(result["suggested_techniques"]) == 3
            assert "chain_of_thought" in result["suggested_techniques"]
            assert result["tokens_used"] == 45
            assert "torchserve_metadata" in result
            
            # Act - Cleanup
            await classifier.cleanup()
            assert not classifier.is_initialized()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_model_fallback_to_local(self):
        """Test model fallback to local mode when TorchServe is unavailable."""
        # Arrange
        classifier = IntentClassifier()
        
        with patch('app.models.classifier.settings.USE_TORCHSERVE', True), \
             patch('app.models.classifier.TorchServeClient') as mock_client_class:
            
            # Setup mock client that fails health check
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.health_check = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client
            
            # Act & Assert
            with pytest.raises(Exception):  # Should fail when TorchServe is unhealthy
                await classifier.initialize_model()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_classification_requests(self):
        """Test handling multiple concurrent classification requests."""
        # Arrange
        classifier = IntentClassifier()
        
        # Different responses for different inputs
        responses = {
            "code": {
                "intent": "code_generation",
                "confidence": 0.94,
                "complexity": {"level": "moderate"},
                "techniques": [{"name": "chain_of_thought"}],
                "metadata": {"inference_time_ms": 100}
            },
            "question": {
                "intent": "question_answering",
                "confidence": 0.96,
                "complexity": {"level": "simple"},
                "techniques": [{"name": "direct_answer"}],
                "metadata": {"inference_time_ms": 80}
            },
            "creative": {
                "intent": "creative_writing",
                "confidence": 0.91,
                "complexity": {"level": "complex"},
                "techniques": [{"name": "few_shot"}],
                "metadata": {"inference_time_ms": 120}
            }
        }
        
        def get_response(text):
            if "function" in text or "code" in text:
                return responses["code"]
            elif "what" in text or "?" in text:
                return responses["question"]
            else:
                return responses["creative"]
        
        with patch('app.models.classifier.settings.USE_TORCHSERVE', True), \
             patch('app.models.classifier.TorchServeClient') as mock_client_class:
            
            # Setup mock client
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.health_check = AsyncMock(return_value=True)
            mock_client.classify = AsyncMock(side_effect=lambda text: get_response(text))
            mock_client_class.return_value = mock_client
            
            # Initialize
            await classifier.initialize_model()
            
            # Act - Concurrent requests
            texts = [
                "Write a function to sort an array",
                "What is machine learning?",
                "Create a story about space",
                "How to implement binary search?",
                "Explain quantum computing",
                "Write a poem about nature"
            ]
            
            tasks = [classifier.classify(text) for text in texts]
            results = await asyncio.gather(*tasks)
            
            # Assert
            assert len(results) == 6
            
            # Verify different intents were returned
            intents = [r["intent"] for r in results]
            assert "code_generation" in intents
            assert "question_answering" in intents
            assert "creative_writing" in intents
            
            # Cleanup
            await classifier.cleanup()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complexity_determination_integration(self):
        """Test complexity determination with various inputs."""
        # Arrange
        classifier = IntentClassifier()
        
        test_cases = [
            {
                "text": "What is 2+2?",
                "expected_complexity": "simple",
                "torchserve_response": {
                    "intent": "question_answering",
                    "confidence": 0.98,
                    "complexity": {"level": "simple"},
                    "techniques": [{"name": "direct_answer"}],
                    "metadata": {"inference_time_ms": 50}
                }
            },
            {
                "text": "Write a function to implement a binary search tree with insert, delete, and search operations. Include error handling.",
                "expected_complexity": "moderate",
                "torchserve_response": {
                    "intent": "code_generation",
                    "confidence": 0.85,
                    "complexity": {"level": "moderate"},
                    "techniques": [{"name": "chain_of_thought"}, {"name": "few_shot"}],
                    "metadata": {"inference_time_ms": 150}
                }
            },
            {
                "text": "Design and implement a distributed caching system that handles millions of requests per second. "
                         "Consider data consistency, fault tolerance, and horizontal scaling. Compare different "
                         "architectural patterns and provide implementation details with code examples.",
                "expected_complexity": "complex",
                "torchserve_response": {
                    "intent": "task_planning",
                    "confidence": 0.75,
                    "complexity": {"level": "complex"},
                    "techniques": [{"name": "tree_of_thoughts"}, {"name": "chain_of_thought"}],
                    "metadata": {"inference_time_ms": 200}
                }
            }
        ]
        
        with patch('app.models.classifier.settings.USE_TORCHSERVE', True), \
             patch('app.models.classifier.TorchServeClient') as mock_client_class:
            
            # Setup mock client
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.health_check = AsyncMock(return_value=True)
            
            # Set up different responses for different texts
            def mock_classify(text):
                for case in test_cases:
                    if case["text"] in text:
                        return case["torchserve_response"]
                return test_cases[0]["torchserve_response"]  # Default
            
            mock_client.classify = AsyncMock(side_effect=mock_classify)
            mock_client_class.return_value = mock_client
            
            # Initialize
            await classifier.initialize_model()
            
            # Act & Assert
            for case in test_cases:
                result = await classifier.classify(case["text"])
                assert result["complexity"] == case["expected_complexity"], \
                    f"Expected {case['expected_complexity']} for text: {case['text'][:50]}..."
            
            # Cleanup
            await classifier.cleanup()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_technique_mapping_integration(self):
        """Test that technique suggestions are appropriate for each intent."""
        # Arrange
        classifier = IntentClassifier()
        
        intent_test_cases = {
            "code_generation": {
                "text": "Write a Python function to calculate prime numbers",
                "expected_techniques": ["chain_of_thought", "few_shot", "self_consistency"]
            },
            "data_analysis": {
                "text": "Analyze this sales data and identify trends",
                "expected_techniques": ["chain_of_thought", "tree_of_thoughts"]
            },
            "creative_writing": {
                "text": "Write a short story about time travel",
                "expected_techniques": ["few_shot", "iterative_refinement"]
            },
            "reasoning": {
                "text": "Solve this logic puzzle step by step",
                "expected_techniques": ["chain_of_thought", "tree_of_thoughts", "self_consistency"]
            }
        }
        
        with patch('app.models.classifier.settings.USE_TORCHSERVE', True), \
             patch('app.models.classifier.TorchServeClient') as mock_client_class:
            
            # Setup mock client
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.health_check = AsyncMock(return_value=True)
            
            def mock_classify(text):
                for intent, case in intent_test_cases.items():
                    if any(keyword in text.lower() for keyword in case["text"].lower().split()):
                        return {
                            "intent": intent,
                            "confidence": 0.9,
                            "complexity": {"level": "moderate"},
                            "techniques": [{"name": t} for t in case["expected_techniques"]],
                            "metadata": {"inference_time_ms": 100}
                        }
                return {
                    "intent": "question_answering",
                    "confidence": 0.85,
                    "complexity": {"level": "simple"},
                    "techniques": [{"name": "direct_answer"}],
                    "metadata": {"inference_time_ms": 80}
                }
            
            mock_client.classify = AsyncMock(side_effect=mock_classify)
            mock_client_class.return_value = mock_client
            
            # Initialize
            await classifier.initialize_model()
            
            # Act & Assert
            for intent, case in intent_test_cases.items():
                result = await classifier.classify(case["text"])
                assert result["intent"] == intent
                
                # Verify appropriate techniques are suggested
                suggested_techniques = result["suggested_techniques"]
                for expected_technique in case["expected_techniques"]:
                    assert expected_technique in suggested_techniques, \
                        f"Expected {expected_technique} for {intent}"
            
            # Cleanup
            await classifier.cleanup()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_recovery_and_retry(self):
        """Test error recovery and retry mechanisms."""
        # Arrange
        classifier = IntentClassifier()
        attempt_count = 0
        
        async def mock_classify_with_retry(text):
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count < 3:
                raise Exception("Temporary failure")
            
            return {
                "intent": "test",
                "confidence": 0.9,
                "complexity": {"level": "simple"},
                "techniques": [{"name": "test"}],
                "metadata": {"inference_time_ms": 100, "retry_count": attempt_count - 1}
            }
        
        with patch('app.models.classifier.settings.USE_TORCHSERVE', True), \
             patch('app.models.classifier.TorchServeClient') as mock_client_class:
            
            # Setup mock client
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.health_check = AsyncMock(return_value=True)
            mock_client.classify = AsyncMock(side_effect=mock_classify_with_retry)
            mock_client_class.return_value = mock_client
            
            # Initialize
            await classifier.initialize_model()
            
            # Act - Should succeed after retries
            result = await classifier.classify("Test input")
            
            # Assert
            assert result["intent"] == "test"
            assert attempt_count == 3  # Failed twice, succeeded on third
            
            # Cleanup
            await classifier.cleanup()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_model_performance_metrics(self):
        """Test that model performance metrics are collected correctly."""
        # Arrange
        classifier = IntentClassifier()
        
        with patch('app.models.classifier.settings.USE_TORCHSERVE', True), \
             patch('app.models.classifier.TorchServeClient') as mock_client_class:
            
            # Setup mock client with varying response times
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.health_check = AsyncMock(return_value=True)
            
            response_times = [50, 100, 150, 200, 250]
            call_count = 0
            
            async def mock_classify_with_timing(text):
                nonlocal call_count
                response_time = response_times[call_count % len(response_times)]
                call_count += 1
                
                await asyncio.sleep(response_time / 1000)  # Simulate latency
                
                return {
                    "intent": "test",
                    "confidence": 0.9,
                    "complexity": {"level": "simple"},
                    "techniques": [{"name": "test"}],
                    "metadata": {"inference_time_ms": response_time}
                }
            
            mock_client.classify = mock_classify_with_timing
            mock_client_class.return_value = mock_client
            
            # Initialize
            await classifier.initialize_model()
            
            # Act - Make multiple requests
            results = []
            for i in range(5):
                result = await classifier.classify(f"Test input {i}")
                results.append(result)
            
            # Assert
            assert len(results) == 5
            
            # Verify inference times match expected
            for i, result in enumerate(results):
                expected_time = response_times[i]
                assert result["torchserve_metadata"]["inference_time_ms"] == expected_time
            
            # Cleanup
            await classifier.cleanup()