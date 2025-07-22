"""Mock objects and utilities for prompt-generator tests."""

from typing import Dict, Any, List, Optional, Callable
from unittest.mock import AsyncMock, MagicMock, Mock
from datetime import datetime, timezone
import asyncio
import random
from contextlib import asynccontextmanager

from .constants import MOCK_LLM_RESPONSES, TechniqueType, ModelProvider
from .builders import PromptResponseBuilder, MockDataBuilder
from .factories import PromptFactory, ModelFactory


class MockLLMClient:
    """Base mock LLM client."""
    
    def __init__(
        self,
        provider: ModelProvider,
        default_response: Optional[str] = None,
        failure_rate: float = 0.0,
        latency_ms: int = 200
    ):
        self.provider = provider
        self.default_response = default_response or MOCK_LLM_RESPONSES["generic"]
        self.failure_rate = failure_rate
        self.latency_ms = latency_ms
        self.call_count = 0
        self.call_history = []
        
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Mock generate method."""
        self.call_count += 1
        self.call_history.append({
            "prompt": prompt,
            "kwargs": kwargs,
            "timestamp": datetime.now(timezone.utc)
        })
        
        # Simulate latency
        await asyncio.sleep(self.latency_ms / 1000.0)
        
        # Simulate failures
        if random.random() < self.failure_rate:
            raise Exception(f"{self.provider} API request failed")
        
        # Generate response
        content = self.default_response
        if "technique" in kwargs:
            technique = kwargs["technique"]
            content = MOCK_LLM_RESPONSES.get(technique, self.default_response)
        
        return ModelFactory.create_model_response(
            self.provider,
            content,
            tokens_used=(len(prompt.split()), len(content.split()))
        )
    
    def reset(self) -> None:
        """Reset mock state."""
        self.call_count = 0
        self.call_history = []


class MockOpenAIClient(MockLLMClient):
    """Mock OpenAI client."""
    
    def __init__(self, **kwargs):
        super().__init__(ModelProvider.OPENAI, **kwargs)
        self.chat = Mock()
        self.chat.completions = Mock()
        self.chat.completions.create = AsyncMock(side_effect=self._create_completion)
    
    async def _create_completion(self, **kwargs) -> Dict[str, Any]:
        """Mock completion creation."""
        messages = kwargs.get("messages", [])
        prompt = messages[-1]["content"] if messages else ""
        return await self.generate(prompt, **kwargs)


class MockAnthropicClient(MockLLMClient):
    """Mock Anthropic client."""
    
    def __init__(self, **kwargs):
        super().__init__(ModelProvider.ANTHROPIC, **kwargs)
        self.messages = Mock()
        self.messages.create = AsyncMock(side_effect=self._create_message)
    
    async def _create_message(self, **kwargs) -> Dict[str, Any]:
        """Mock message creation."""
        messages = kwargs.get("messages", [])
        prompt = messages[-1]["content"] if messages else ""
        response = await self.generate(prompt, **kwargs)
        
        # Convert to Anthropic format
        return Mock(
            content=[Mock(text=response["content"][0]["text"])],
            usage=Mock(
                input_tokens=response["usage"]["input_tokens"],
                output_tokens=response["usage"]["output_tokens"]
            )
        )


class MockPromptEngine:
    """Mock prompt engine for testing."""
    
    def __init__(
        self,
        openai_client: Optional[MockOpenAIClient] = None,
        anthropic_client: Optional[MockAnthropicClient] = None
    ):
        self.openai_client = openai_client or MockOpenAIClient()
        self.anthropic_client = anthropic_client or MockAnthropicClient()
        self.technique_applications = {}
        self.generation_count = 0
        
    async def generate_enhanced_prompt(
        self,
        original_prompt: str,
        intent: str,
        techniques: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Mock enhanced prompt generation."""
        self.generation_count += 1
        
        # Track technique applications
        for technique in techniques:
            self.technique_applications[technique] = \
                self.technique_applications.get(technique, 0) + 1
        
        # Create enhanced prompt
        enhanced_prompt = original_prompt
        for technique in techniques:
            try:
                technique_enum = TechniqueType(technique)
                enhanced_prompt = PromptFactory.create_enhanced_prompt(
                    enhanced_prompt,
                    technique_enum,
                    context
                )
            except ValueError:
                pass  # Unknown technique
        
        # Simulate generation time
        await asyncio.sleep(0.1)
        
        return PromptResponseBuilder.generation_response(
            enhanced_prompt=enhanced_prompt,
            techniques_applied=techniques,
            model_used="gpt-4",
            generation_time_ms=100
        )
    
    async def optimize_prompt(
        self,
        original_prompt: str,
        optimization_goals: List[str],
        target_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mock prompt optimization."""
        # Simple optimization simulation
        optimized = original_prompt
        
        if "clarity" in optimization_goals:
            optimized = optimized.replace("thing", "specific item")
            optimized = optimized.replace("stuff", "materials")
        
        if "conciseness" in optimization_goals:
            # Remove filler words
            filler_words = ["basically", "actually", "really", "very"]
            for word in filler_words:
                optimized = optimized.replace(f" {word} ", " ")
        
        if "specificity" in optimization_goals:
            optimized = f"Specifically, {optimized}"
        
        return PromptResponseBuilder.optimization_response(
            optimized_prompt=optimized
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "generation_count": self.generation_count,
            "technique_applications": self.technique_applications,
            "openai_calls": self.openai_client.call_count,
            "anthropic_calls": self.anthropic_client.call_count
        }
    
    def reset(self) -> None:
        """Reset engine state."""
        self.generation_count = 0
        self.technique_applications = {}
        self.openai_client.reset()
        self.anthropic_client.reset()


class MockCacheService:
    """Mock cache service for prompt caching."""
    
    def __init__(self, default_ttl: int = 3600):
        self.cache: Dict[str, Any] = {}
        self.default_ttl = default_ttl
        self.hit_count = 0
        self.miss_count = 0
        
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get from cache."""
        result = self.cache.get(key)
        if result:
            self.hit_count += 1
        else:
            self.miss_count += 1
        return result
    
    async def set(
        self,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> None:
        """Set in cache."""
        self.cache[key] = {
            "value": value,
            "ttl": ttl or self.default_ttl,
            "cached_at": datetime.now(timezone.utc)
        }
    
    async def delete(self, key: str) -> None:
        """Delete from cache."""
        self.cache.pop(key, None)
    
    def get_stats(self) -> Dict[str, float]:
        """Get cache statistics."""
        total = self.hit_count + self.miss_count
        return {
            "hit_rate": self.hit_count / total if total > 0 else 0,
            "size": len(self.cache)
        }


class MockTechniqueManager:
    """Mock technique manager."""
    
    def __init__(self):
        self.techniques = {}
        self._setup_default_techniques()
        
    def _setup_default_techniques(self):
        """Setup default mock techniques."""
        for technique in TechniqueType:
            mock_technique = Mock()
            mock_technique.name = technique.value
            mock_technique.apply = AsyncMock(
                return_value=f"Enhanced with {technique.value}"
            )
            mock_technique.is_compatible = Mock(return_value=True)
            self.techniques[technique.value] = mock_technique
    
    def get_technique(self, name: str) -> Optional[Mock]:
        """Get a technique by name."""
        return self.techniques.get(name)
    
    def get_all_techniques(self) -> Dict[str, Mock]:
        """Get all techniques."""
        return self.techniques.copy()
    
    def add_technique(self, name: str, technique: Mock) -> None:
        """Add a custom technique."""
        self.techniques[name] = technique


class MockMetricsCollector:
    """Mock metrics collector."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.counters: Dict[str, int] = {}
        
    def record_generation_time(self, technique: str, time_ms: float) -> None:
        """Record generation time for a technique."""
        key = f"generation_time_{technique}"
        if key not in self.metrics:
            self.metrics[key] = []
        self.metrics[key].append(time_ms)
    
    def increment_technique_usage(self, technique: str) -> None:
        """Increment technique usage counter."""
        key = f"technique_{technique}"
        self.counters[key] = self.counters.get(key, 0) + 1
    
    def get_technique_stats(self, technique: str) -> Dict[str, float]:
        """Get statistics for a technique."""
        time_key = f"generation_time_{technique}"
        usage_key = f"technique_{technique}"
        
        times = self.metrics.get(time_key, [])
        usage = self.counters.get(usage_key, 0)
        
        if not times:
            return {"usage": usage, "avg_time": 0}
        
        return {
            "usage": usage,
            "avg_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times)
        }


@asynccontextmanager
async def mock_llm_context(
    provider: ModelProvider = ModelProvider.OPENAI,
    responses: Optional[Dict[str, str]] = None
):
    """Context manager for mocking LLM interactions."""
    if provider == ModelProvider.OPENAI:
        client = MockOpenAIClient()
    else:
        client = MockAnthropicClient()
    
    if responses:
        # Configure custom responses
        for technique, response in responses.items():
            # This would configure the mock to return specific responses
            pass
    
    yield client


def create_mock_app_dependencies() -> Dict[str, Any]:
    """Create mock dependencies for the app."""
    return {
        "prompt_engine": MockPromptEngine(),
        "cache_service": MockCacheService(),
        "technique_manager": MockTechniqueManager(),
        "metrics_collector": MockMetricsCollector(),
        "openai_client": MockOpenAIClient(),
        "anthropic_client": MockAnthropicClient()
    }