"""Request and response builders for prompt-generator tests."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from faker import Faker
import hashlib

from .constants import TechniqueType, IntentType, ModelProvider

fake = Faker()


class PromptRequestBuilder:
    """Builder for creating test requests."""
    
    @staticmethod
    def generation_request(
        original_prompt: Optional[str] = None,
        intent: Optional[str] = None,
        techniques: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build a prompt generation request."""
        request = {
            "original_prompt": original_prompt or fake.sentence(nb_words=15),
            "intent": intent or fake.random_element([e.value for e in IntentType]),
            "techniques": techniques or [
                fake.random_element([e.value for e in TechniqueType])
                for _ in range(fake.random_int(min=1, max=3))
            ],
            "context": context or {
                "user_id": fake.uuid4(),
                "session_id": fake.uuid4(),
                "complexity": fake.random_element(["simple", "intermediate", "complex"]),
                "domain": fake.random_element(["programming", "science", "business", "general"]),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Add any additional fields
        for key, value in kwargs.items():
            request[key] = value
            
        return request
    
    @staticmethod
    def batch_generation_request(
        prompts: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """Build a batch generation request."""
        if prompts is None:
            prompts = [
                PromptRequestBuilder.generation_request()
                for _ in range(batch_size)
            ]
            
        return {
            "requests": prompts,
            "batch_context": {
                "batch_id": fake.uuid4(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **kwargs
            }
        }
    
    @staticmethod
    def optimization_request(
        original_prompt: Optional[str] = None,
        target_model: Optional[str] = None,
        optimization_goals: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build a prompt optimization request."""
        return {
            "original_prompt": original_prompt or fake.sentence(nb_words=20),
            "target_model": target_model or fake.random_element(["gpt-4", "claude-3", "gpt-3.5-turbo"]),
            "optimization_goals": optimization_goals or [
                fake.random_element(["clarity", "conciseness", "specificity", "creativity"])
                for _ in range(fake.random_int(min=1, max=3))
            ],
            "constraints": {
                "max_tokens": kwargs.get("max_tokens", 500),
                "preserve_intent": kwargs.get("preserve_intent", True),
                "maintain_style": kwargs.get("maintain_style", False)
            }
        }
    
    @staticmethod
    def invalid_request(error_type: str = "missing_prompt") -> Dict[str, Any]:
        """Build various invalid requests for error testing."""
        invalid_requests = {
            "missing_prompt": {
                "intent": "explain_concept",
                "techniques": ["chain_of_thought"]
            },
            "empty_prompt": {
                "original_prompt": "",
                "intent": "generate_code",
                "techniques": ["few_shot"]
            },
            "invalid_intent": {
                "original_prompt": "Test prompt",
                "intent": "invalid_intent_type",
                "techniques": ["chain_of_thought"]
            },
            "invalid_technique": {
                "original_prompt": "Test prompt",
                "intent": "explain_concept",
                "techniques": ["invalid_technique"]
            },
            "empty_techniques": {
                "original_prompt": "Test prompt",
                "intent": "explain_concept",
                "techniques": []
            },
            "incompatible_technique": {
                "original_prompt": "Debug this code",
                "intent": "debug_error",
                "techniques": ["emotional_appeal"]  # Not ideal for debugging
            }
        }
        
        return invalid_requests.get(error_type, invalid_requests["missing_prompt"])


class PromptResponseBuilder:
    """Builder for creating test responses."""
    
    @staticmethod
    def generation_response(
        enhanced_prompt: Optional[str] = None,
        techniques_applied: Optional[List[str]] = None,
        model_used: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build a generation response."""
        response = {
            "enhanced_prompt": enhanced_prompt or fake.paragraph(nb_sentences=5),
            "techniques_applied": techniques_applied or [
                fake.random_element([e.value for e in TechniqueType])
                for _ in range(fake.random_int(min=1, max=3))
            ],
            "metadata": {
                "generation_time_ms": kwargs.get("generation_time_ms", fake.random_int(100, 500)),
                "token_count": kwargs.get("token_count", fake.random_int(50, 500)),
                "model_used": model_used or fake.random_element(["gpt-4", "claude-3", "gpt-3.5-turbo"]),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "explanation": kwargs.get(
                "explanation",
                "Applied techniques to enhance the prompt for better results."
            )
        }
        
        # Add any additional fields
        for key, value in kwargs.items():
            if key not in ["generation_time_ms", "token_count", "explanation"]:
                response[key] = value
                
        return response
    
    @staticmethod
    def optimization_response(
        optimized_prompt: Optional[str] = None,
        improvements: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build an optimization response."""
        return {
            "optimized_prompt": optimized_prompt or fake.paragraph(nb_sentences=3),
            "improvements": improvements or [
                {
                    "type": fake.random_element(["clarity", "specificity", "conciseness"]),
                    "description": fake.sentence(),
                    "impact_score": fake.pyfloat(min_value=0.1, max_value=1.0, right_digits=2)
                }
                for _ in range(fake.random_int(min=2, max=4))
            ],
            "metrics": {
                "clarity_score": fake.pyfloat(min_value=0.7, max_value=1.0, right_digits=2),
                "specificity_score": fake.pyfloat(min_value=0.7, max_value=1.0, right_digits=2),
                "token_efficiency": fake.pyfloat(min_value=0.8, max_value=1.2, right_digits=2)
            },
            "metadata": {
                "optimization_time_ms": fake.random_int(200, 800),
                "model_used": kwargs.get("model_used", "gpt-4")
            }
        }
    
    @staticmethod
    def error_response(
        error: str = "Generation failed",
        code: str = "GENERATION_ERROR",
        status_code: int = 500,
        **kwargs
    ) -> Dict[str, Any]:
        """Build an error response."""
        return {
            "error": error,
            "code": code,
            "status_code": status_code,
            "details": kwargs.get("details", {}),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def batch_response(
        batch_size: int = 10,
        include_errors: bool = False
    ) -> List[Dict[str, Any]]:
        """Build a batch generation response."""
        responses = []
        
        for i in range(batch_size):
            if include_errors and i % 5 == 0:  # Include some errors
                responses.append({
                    "index": i,
                    "error": "Generation failed for this item",
                    "code": "ITEM_ERROR"
                })
            else:
                response = PromptResponseBuilder.generation_response()
                response["index"] = i
                responses.append(response)
                
        return responses


class MockDataBuilder:
    """Builder for creating mock data structures."""
    
    @staticmethod
    def llm_response(
        provider: str = "openai",
        success: bool = True,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build a mock LLM response."""
        if not success:
            return {
                "error": {
                    "message": "API request failed",
                    "type": "api_error",
                    "code": "rate_limit_exceeded"
                }
            }
        
        if provider == "openai":
            return {
                "choices": [{
                    "message": {
                        "content": content or fake.paragraph(nb_sentences=5)
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": fake.random_int(50, 200),
                    "completion_tokens": fake.random_int(50, 300),
                    "total_tokens": fake.random_int(100, 500)
                }
            }
        elif provider == "anthropic":
            return {
                "content": [{
                    "text": content or fake.paragraph(nb_sentences=5)
                }],
                "usage": {
                    "input_tokens": fake.random_int(50, 200),
                    "output_tokens": fake.random_int(50, 300)
                }
            }
        
        return {"content": content or fake.paragraph()}
    
    @staticmethod
    def cache_key(
        prompt: str,
        techniques: List[str],
        version: str = "v1"
    ) -> str:
        """Generate a cache key for a prompt."""
        combined = f"{prompt}:{':'.join(sorted(techniques))}"
        prompt_hash = hashlib.sha256(combined.encode()).hexdigest()[:16]
        return f"prompt:{version}:{prompt_hash}"
    
    @staticmethod
    def technique_config(
        technique_name: str,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """Build a technique configuration."""
        return {
            "name": technique_name,
            "enabled": enabled,
            "parameters": {
                "temperature": fake.pyfloat(min_value=0.1, max_value=1.0, right_digits=2),
                "max_examples": fake.random_int(min=2, max=5),
                "detail_level": fake.random_element(["low", "medium", "high"])
            },
            "effectiveness_scores": {
                intent.value: fake.pyfloat(min_value=0.5, max_value=1.0, right_digits=2)
                for intent in IntentType
            }
        }
    
    @staticmethod
    def performance_metrics(
        time_period: str = "1h"
    ) -> Dict[str, Any]:
        """Build performance metrics."""
        return {
            "time_period": time_period,
            "total_requests": fake.random_int(100, 10000),
            "successful_requests": fake.random_int(95, 99),
            "failed_requests": fake.random_int(1, 5),
            "average_generation_time_ms": fake.random_int(100, 500),
            "p95_generation_time_ms": fake.random_int(500, 1000),
            "p99_generation_time_ms": fake.random_int(1000, 2000),
            "technique_usage": {
                technique.value: fake.random_int(10, 1000)
                for technique in TechniqueType
            },
            "model_usage": {
                "gpt-4": fake.random_int(100, 5000),
                "claude-3": fake.random_int(100, 3000),
                "gpt-3.5-turbo": fake.random_int(100, 2000)
            }
        }