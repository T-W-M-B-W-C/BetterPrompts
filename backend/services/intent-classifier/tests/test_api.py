import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app
from app.models.schemas import IntentResponse

client = TestClient(app)

class TestIntentClassifierAPI:
    """Test suite for Intent Classifier API endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "intent-classifier"}
    
    def test_classify_endpoint_success(self):
        """Test successful classification"""
        with patch('app.api.routes.classifier') as mock_classifier:
            mock_classifier.classify.return_value = IntentResponse(
                category="analysis",
                confidence=0.95,
                complexity=0.7,
                sub_intents=["data_analysis", "visualization"],
                requires_clarification=False
            )
            
            response = client.post(
                "/classify",
                json={"input": "Analyze sales data and create charts"}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["category"] == "analysis"
            assert result["confidence"] == 0.95
            assert result["complexity"] == 0.7
            assert len(result["sub_intents"]) == 2
    
    def test_classify_endpoint_empty_input(self):
        """Test classification with empty input"""
        response = client.post("/classify", json={"input": ""})
        
        assert response.status_code == 400
        assert "Input cannot be empty" in response.json()["detail"]
    
    def test_classify_endpoint_missing_input(self):
        """Test classification with missing input field"""
        response = client.post("/classify", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_classify_endpoint_very_long_input(self):
        """Test classification with very long input"""
        long_input = "x" * 5001  # Exceeds max length
        response = client.post("/classify", json={"input": long_input})
        
        assert response.status_code == 400
        assert "too long" in response.json()["detail"].lower()
    
    def test_classify_endpoint_with_options(self):
        """Test classification with additional options"""
        with patch('app.api.routes.classifier') as mock_classifier:
            mock_classifier.classify.return_value = IntentResponse(
                category="code_generation",
                confidence=0.88,
                complexity=0.5,
                sub_intents=["python", "algorithm"],
                requires_clarification=False
            )
            
            response = client.post(
                "/classify",
                json={
                    "input": "Write a Python sorting algorithm",
                    "options": {
                        "include_examples": True,
                        "language": "en"
                    }
                }
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["category"] == "code_generation"
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import concurrent.futures
        
        def make_request(i):
            return client.post(
                "/classify",
                json={"input": f"Test prompt {i}"}
            )
        
        with patch('app.api.routes.classifier') as mock_classifier:
            mock_classifier.classify.return_value = IntentResponse(
                category="test",
                confidence=0.9,
                complexity=0.3,
                sub_intents=[],
                requires_clarification=False
            )
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request, i) for i in range(10)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
            assert all(r.status_code == 200 for r in results)
    
    def test_classification_timeout(self):
        """Test handling of classification timeout"""
        with patch('app.api.routes.classifier') as mock_classifier:
            # Simulate a timeout
            mock_classifier.classify.side_effect = TimeoutError("Classification timed out")
            
            response = client.post(
                "/classify",
                json={"input": "Complex prompt requiring long processing"}
            )
            
            assert response.status_code == 504
            assert "timeout" in response.json()["detail"].lower()
    
    def test_model_not_loaded_error(self):
        """Test handling when model is not loaded"""
        with patch('app.api.routes.classifier') as mock_classifier:
            mock_classifier.classify.side_effect = RuntimeError("Model not loaded")
            
            response = client.post(
                "/classify",
                json={"input": "Test prompt"}
            )
            
            assert response.status_code == 503
            assert "service unavailable" in response.json()["detail"].lower()