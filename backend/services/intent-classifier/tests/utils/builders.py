"""Request and response builders for intent-classifier tests."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from faker import Faker
import hashlib
import json

from .constants import IntentType, ComplexityLevel, Domain, TechniqueType

fake = Faker()


class RequestBuilder:
    """Builder for creating test requests."""
    
    @staticmethod
    def classification_request(
        prompt: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build a classification request."""
        request = {
            "prompt": prompt or fake.sentence(nb_words=10),
            "context": context or {}
        }
        
        if user_id:
            request["context"]["user_id"] = user_id
        if session_id:
            request["context"]["session_id"] = session_id
            
        request["context"]["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Add any additional fields
        for key, value in kwargs.items():
            request[key] = value
            
        return request
    
    @staticmethod
    def batch_classification_request(
        prompts: Optional[List[str]] = None,
        batch_size: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """Build a batch classification request."""
        if prompts is None:
            prompts = [fake.sentence(nb_words=fake.random_int(5, 20)) for _ in range(batch_size)]
            
        return {
            "prompts": prompts,
            "context": {
                "batch_id": fake.uuid4(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **kwargs
            }
        }
    
    @staticmethod
    def invalid_request(error_type: str = "missing_prompt") -> Dict[str, Any]:
        """Build various invalid requests for error testing."""
        invalid_requests = {
            "missing_prompt": {"context": {}},
            "empty_prompt": {"prompt": "", "context": {}},
            "null_prompt": {"prompt": None, "context": {}},
            "too_long_prompt": {"prompt": "x" * 10001, "context": {}},
            "invalid_type": {"prompt": 123, "context": {}},
            "missing_context": {"prompt": "test"},
            "invalid_context": {"prompt": "test", "context": "not a dict"}
        }
        
        return invalid_requests.get(error_type, invalid_requests["missing_prompt"])


class ResponseBuilder:
    """Builder for creating test responses."""
    
    @staticmethod
    def classification_response(
        intent: Optional[str] = None,
        confidence: Optional[float] = None,
        complexity: Optional[str] = None,
        domain: Optional[str] = None,
        techniques: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build a classification response."""
        response = {
            "intent": intent or fake.random_element([e.value for e in IntentType]),
            "confidence": confidence if confidence is not None else fake.pyfloat(min_value=0.7, max_value=1.0, right_digits=2),
            "complexity": complexity or fake.random_element([e.value for e in ComplexityLevel]),
            "domain": domain or fake.random_element([e.value for e in Domain]),
            "suggested_techniques": techniques or [
                fake.random_element([e.value for e in TechniqueType])
                for _ in range(fake.random_int(1, 3))
            ],
            "metadata": {
                "model_version": kwargs.get("model_version", "1.0.0"),
                "inference_time_ms": kwargs.get("inference_time_ms", fake.random_int(20, 100)),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Add any additional fields
        for key, value in kwargs.items():
            if key not in ["model_version", "inference_time_ms"]:
                response[key] = value
                
        return response
    
    @staticmethod
    def error_response(
        error: str = "Classification failed",
        code: str = "CLASSIFICATION_ERROR",
        status_code: int = 500,
        **kwargs
    ) -> Dict[str, Any]:
        """Build an error response."""
        return {
            "error": error,
            "code": code,
            "status_code": status_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs
        }
    
    @staticmethod
    def batch_response(
        batch_size: int = 10,
        include_errors: bool = False
    ) -> List[Dict[str, Any]]:
        """Build a batch classification response."""
        responses = []
        
        for i in range(batch_size):
            if include_errors and i % 5 == 0:  # Include some errors
                responses.append({
                    "index": i,
                    "error": "Classification failed for this item",
                    "code": "ITEM_ERROR"
                })
            else:
                response = ResponseBuilder.classification_response()
                response["index"] = i
                responses.append(response)
                
        return responses


class MockDataBuilder:
    """Builder for creating mock data structures."""
    
    @staticmethod
    def torchserve_response(
        success: bool = True,
        intent: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """Build a mock TorchServe response."""
        if not success:
            return {
                "code": 503,
                "type": "ServiceUnavailableException",
                "message": "Model is not ready"
            }
            
        return {
            "predictions": [{
                "intent": intent or fake.random_element([e.value for e in IntentType]),
                "confidence": confidence or fake.pyfloat(min_value=0.7, max_value=1.0, right_digits=2),
                "sub_intent": fake.random_element(["technical", "creative", "analytical"]),
                "complexity": {
                    "level": fake.random_element([e.value for e in ComplexityLevel]),
                    "score": fake.pyfloat(min_value=0.1, max_value=1.0, right_digits=2)
                },
                "domain": fake.random_element([e.value for e in Domain]),
                "suggested_techniques": [
                    fake.random_element([e.value for e in TechniqueType])
                    for _ in range(fake.random_int(1, 3))
                ]
            }]
        }
    
    @staticmethod
    def cache_key(prompt: str, version: str = "v1") -> str:
        """Generate a cache key for a prompt."""
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        return f"intent:{version}:{prompt_hash}"
    
    @staticmethod
    def cached_response(
        prompt: str,
        response: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build a cached response structure."""
        if response is None:
            response = ResponseBuilder.classification_response()
            
        return {
            "prompt": prompt,
            "response": response,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "ttl": 3600
        }
    
    @staticmethod
    def user_history(
        user_id: str,
        num_entries: int = 10
    ) -> List[Dict[str, Any]]:
        """Build user history entries."""
        history = []
        
        for _ in range(num_entries):
            entry = {
                "prompt": fake.sentence(nb_words=fake.random_int(5, 20)),
                "intent": fake.random_element([e.value for e in IntentType]),
                "timestamp": fake.date_time_between(start_date="-30d", end_date="now", tzinfo=timezone.utc).isoformat(),
                "session_id": fake.uuid4()
            }
            history.append(entry)
            
        return sorted(history, key=lambda x: x["timestamp"], reverse=True)
    
    @staticmethod
    def database_record(
        prompt: str,
        response: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build a database record structure."""
        if response is None:
            response = ResponseBuilder.classification_response()
            
        return {
            "id": fake.uuid4(),
            "prompt": prompt,
            "intent": response["intent"],
            "confidence": response["confidence"],
            "complexity": response["complexity"],
            "domain": response["domain"],
            "techniques": json.dumps(response["suggested_techniques"]),
            "user_id": user_id or fake.uuid4(),
            "session_id": fake.uuid4(),
            "created_at": datetime.now(timezone.utc),
            "metadata": json.dumps(response.get("metadata", {}))
        }