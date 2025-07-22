"""
Unit tests for API endpoints
"""

import pytest
from fastapi import status
from unittest.mock import AsyncMock, MagicMock, patch
import json
import time

from app.models import (
    PromptGenerationRequest,
    PromptGenerationResponse,
    BatchGenerationRequest,
    BatchGenerationResponse,
    TechniqueType
)
from app.engine import PromptGenerationEngine


class TestGenerateEndpoint:
    """Test the /api/v1/generate endpoint"""
    
    @pytest.mark.asyncio
    async def test_generate_success(self, test_client, mock_prompt_engine):
        """Test successful prompt generation"""
        # Prepare request
        request_data = {
            "text": "Explain quantum computing to a beginner",
            "intent": "explain_concept",
            "complexity": "simple",
            "techniques": ["chain_of_thought", "analogical"],
            "target_model": "gpt-4"
        }
        
        # Mock engine response
        mock_response = PromptGenerationResponse(
            text="Let me explain quantum computing step by step...",
            model_version="1.0.0",
            tokens_used=150,
            id="test-id-123",
            original_text=request_data["text"],
            techniques_applied=request_data["techniques"],
            generation_time_ms=123.45,
            confidence_score=0.85
        )
        
        with patch.object(test_client.app.state, 'engine') as mock_engine:
            mock_engine.generate = AsyncMock(return_value=mock_response)
            
            # Make request
            response = test_client.post("/api/v1/generate", json=request_data)
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["enhanced_prompt"] == "Let me explain quantum computing step by step..."
            assert result["model_version"] == "1.0.0"
            assert result["token_count"] == 150
            
            # Verify engine was called correctly
            mock_engine.generate.assert_called_once()
            call_args = mock_engine.generate.call_args[0][0]
            assert call_args.text == request_data["text"]
            assert call_args.techniques == request_data["techniques"]
    
    @pytest.mark.asyncio
    async def test_generate_validation_error(self, test_client):
        """Test generation with invalid request data"""
        # Invalid complexity value
        request_data = {
            "text": "Test prompt",
            "intent": "test",
            "complexity": "invalid_complexity",
            "techniques": ["chain_of_thought"]
        }
        
        response = test_client.post("/api/v1/generate", json=request_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    @pytest.mark.asyncio
    async def test_generate_empty_text(self, test_client):
        """Test generation with empty text"""
        request_data = {
            "text": "",
            "intent": "test",
            "complexity": "simple",
            "techniques": ["chain_of_thought"]
        }
        
        response = test_client.post("/api/v1/generate", json=request_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    @pytest.mark.asyncio
    async def test_generate_invalid_technique(self, test_client):
        """Test generation with invalid technique"""
        request_data = {
            "text": "Test prompt",
            "intent": "test",
            "complexity": "simple",
            "techniques": ["invalid_technique"]
        }
        
        response = test_client.post("/api/v1/generate", json=request_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    @pytest.mark.asyncio
    async def test_generate_engine_error(self, test_client):
        """Test generation when engine raises an error"""
        request_data = {
            "text": "Test prompt",
            "intent": "test",
            "complexity": "simple",
            "techniques": ["chain_of_thought"]
        }
        
        with patch.object(test_client.app.state, 'engine') as mock_engine:
            mock_engine.generate = AsyncMock(side_effect=Exception("Engine error"))
            
            response = test_client.post("/api/v1/generate", json=request_data)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to generate prompt" in response.json()["detail"]
            
    @pytest.mark.asyncio
    async def test_generate_with_all_parameters(self, test_client):
        """Test generation with all optional parameters"""
        request_data = {
            "text": "Complex request with all parameters",
            "intent": "analyze_data",
            "complexity": "complex",
            "techniques": ["tree_of_thoughts", "structured_output"],
            "context": {
                "domain": "data_science",
                "user_level": "expert"
            },
            "parameters": {
                "max_depth": 3,
                "output_format": "json"
            },
            "target_model": "gpt-4",
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        mock_response = PromptGenerationResponse(
            text="Enhanced complex prompt...",
            model_version="1.0.0",
            tokens_used=450,
            confidence_score=0.92
        )
        
        with patch.object(test_client.app.state, 'engine') as mock_engine:
            mock_engine.generate = AsyncMock(return_value=mock_response)
            
            response = test_client.post("/api/v1/generate", json=request_data)
            assert response.status_code == status.HTTP_200_OK
            
            # Verify all parameters were passed to engine
            call_args = mock_engine.generate.call_args[0][0]
            assert call_args.context == request_data["context"]
            assert call_args.parameters == request_data["parameters"]
            assert call_args.temperature == request_data["temperature"]


class TestBatchGenerateEndpoint:
    """Test the /api/v1/generate/batch endpoint"""
    
    @pytest.mark.asyncio
    async def test_batch_generate_success(self, test_client):
        """Test successful batch generation"""
        batch_request = {
            "prompts": [
                {
                    "text": "Prompt 1",
                    "intent": "test",
                    "complexity": "simple",
                    "techniques": ["chain_of_thought"]
                },
                {
                    "text": "Prompt 2",
                    "intent": "test",
                    "complexity": "moderate",
                    "techniques": ["few_shot"]
                }
            ],
            "batch_id": "test-batch-123"
        }
        
        # Mock individual responses
        mock_responses = [
            PromptGenerationResponse(
                text=f"Enhanced prompt {i}",
                model_version="1.0.0",
                tokens_used=100 + i * 50,
                confidence_score=0.8 + i * 0.05
            )
            for i in range(2)
        ]
        
        with patch.object(test_client.app.state, 'engine') as mock_engine:
            mock_engine.generate = AsyncMock(side_effect=mock_responses)
            
            response = test_client.post("/api/v1/generate/batch", json=batch_request)
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["batch_id"] == "test-batch-123"
            assert result["total_prompts"] == 2
            assert result["successful"] == 2
            assert result["failed"] == 0
            assert len(result["results"]) == 2
            assert result["results"][0]["enhanced_prompt"] == "Enhanced prompt 0"
            
    @pytest.mark.asyncio
    async def test_batch_generate_partial_failure(self, test_client):
        """Test batch generation with some failures"""
        batch_request = {
            "prompts": [
                {
                    "text": "Prompt 1",
                    "intent": "test",
                    "complexity": "simple",
                    "techniques": ["chain_of_thought"]
                },
                {
                    "text": "Prompt 2",
                    "intent": "test",
                    "complexity": "moderate",
                    "techniques": ["few_shot"]
                },
                {
                    "text": "Prompt 3",
                    "intent": "test",
                    "complexity": "complex",
                    "techniques": ["tree_of_thoughts"]
                }
            ]
        }
        
        # Mock responses with one failure
        mock_responses = [
            PromptGenerationResponse(text="Enhanced 1", model_version="1.0.0", tokens_used=100),
            Exception("Generation failed"),
            PromptGenerationResponse(text="Enhanced 3", model_version="1.0.0", tokens_used=200)
        ]
        
        with patch.object(test_client.app.state, 'engine') as mock_engine:
            mock_engine.generate = AsyncMock(side_effect=mock_responses)
            
            response = test_client.post("/api/v1/generate/batch", json=batch_request)
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["total_prompts"] == 3
            assert result["successful"] == 2
            assert result["failed"] == 1
            assert len(result["results"]) == 2
            assert len(result["errors"]) == 1
            assert result["errors"][0]["index"] == 1
            assert "Generation failed" in result["errors"][0]["error"]
            
    @pytest.mark.asyncio
    async def test_batch_generate_empty_batch(self, test_client):
        """Test batch generation with empty prompts list"""
        batch_request = {
            "prompts": []
        }
        
        response = test_client.post("/api/v1/generate/batch", json=batch_request)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    @pytest.mark.asyncio
    async def test_batch_generate_with_priority(self, test_client):
        """Test batch generation with priority parameter"""
        batch_request = {
            "prompts": [
                {
                    "text": "High priority prompt",
                    "intent": "urgent",
                    "complexity": "complex",
                    "techniques": ["chain_of_thought"]
                }
            ],
            "priority": 10,
            "callback_url": "https://example.com/callback"
        }
        
        mock_response = PromptGenerationResponse(
            text="Enhanced priority prompt",
            model_version="1.0.0",
            tokens_used=150
        )
        
        with patch.object(test_client.app.state, 'engine') as mock_engine:
            mock_engine.generate = AsyncMock(return_value=mock_response)
            
            response = test_client.post("/api/v1/generate/batch", json=batch_request)
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["successful"] == 1
            # In a real implementation, priority and callback would be handled


class TestTechniquesEndpoint:
    """Test the /api/v1/techniques endpoint"""
    
    def test_list_techniques(self, test_client):
        """Test listing available techniques"""
        response = test_client.get("/api/v1/techniques")
        
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "techniques" in result
        assert len(result["techniques"]) >= 10  # Should have at least 10 techniques
        
        # Check structure of technique info
        technique = result["techniques"][0]
        assert "id" in technique
        assert "name" in technique
        assert "description" in technique
        assert "best_for" in technique
        assert isinstance(technique["best_for"], list)
        
    def test_techniques_contains_all_types(self, test_client):
        """Test that all technique types are included"""
        response = test_client.get("/api/v1/techniques")
        result = response.json()
        
        technique_ids = [t["id"] for t in result["techniques"]]
        
        # Check core techniques
        expected_techniques = [
            "chain_of_thought", "tree_of_thoughts", "few_shot",
            "zero_shot", "role_play", "step_by_step",
            "structured_output", "emotional_appeal", "constraints",
            "analogical"
        ]
        
        for expected in expected_techniques:
            assert expected in technique_ids


class TestHealthEndpoint:
    """Test health check endpoints"""
    
    def test_health_check(self, test_client):
        """Test basic health check"""
        response = test_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "version" in result
        
    def test_health_check_detailed(self, test_client):
        """Test detailed health check"""
        response = test_client.get("/health/detailed")
        
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["status"] == "healthy"
        assert "components" in result
        assert "engine" in result["components"]
        assert "techniques" in result["components"]


class TestMetricsEndpoint:
    """Test metrics endpoint"""
    
    def test_metrics_enabled(self, test_client):
        """Test metrics endpoint when enabled"""
        with patch('app.config.settings.enable_metrics', True):
            response = test_client.get("/metrics")
            
            # Should return prometheus format
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["content-type"] == "text/plain; charset=utf-8"
            assert "prompt_generation_requests_total" in response.text
            
    def test_metrics_disabled(self, test_client):
        """Test metrics endpoint when disabled"""
        with patch('app.config.settings.enable_metrics', False):
            response = test_client.get("/metrics")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Metrics not enabled" in response.json()["detail"]


class TestMiddleware:
    """Test middleware functionality"""
    
    def test_cors_headers(self, test_client):
        """Test CORS headers are properly set"""
        response = test_client.options("/api/v1/generate")
        
        # Check CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        
    def test_process_time_header(self, test_client):
        """Test that process time header is added"""
        request_data = {
            "text": "Test",
            "intent": "test",
            "complexity": "simple",
            "techniques": ["chain_of_thought"]
        }
        
        with patch.object(test_client.app.state, 'engine') as mock_engine:
            mock_engine.generate = AsyncMock(
                return_value=PromptGenerationResponse(
                    text="Enhanced", 
                    model_version="1.0.0", 
                    tokens_used=100
                )
            )
            
            response = test_client.post("/api/v1/generate", json=request_data)
            
            assert "x-process-time" in response.headers
            process_time = float(response.headers["x-process-time"])
            assert process_time > 0
            assert process_time < 10  # Should be reasonably fast


class TestErrorHandlers:
    """Test error handling"""
    
    def test_value_error_handler(self, test_client):
        """Test ValueError handling"""
        with patch.object(test_client.app.state, 'engine') as mock_engine:
            mock_engine.generate = AsyncMock(
                side_effect=ValueError("Invalid input format")
            )
            
            request_data = {
                "text": "Test",
                "intent": "test",
                "complexity": "simple",
                "techniques": ["chain_of_thought"]
            }
            
            response = test_client.post("/api/v1/generate", json=request_data)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid input format" in response.json()["detail"]
            
    def test_general_exception_handler(self, test_client):
        """Test general exception handling"""
        # Force an unexpected error
        with patch.object(test_client.app.state, 'engine') as mock_engine:
            mock_engine.generate = AsyncMock(
                side_effect=RuntimeError("Unexpected error")
            )
            
            request_data = {
                "text": "Test",
                "intent": "test",
                "complexity": "simple",
                "techniques": ["chain_of_thought"]
            }
            
            response = test_client.post("/api/v1/generate", json=request_data)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to generate prompt" in response.json()["detail"]