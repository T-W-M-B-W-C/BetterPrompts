"""OpenAI client with rate limiting and retry logic for data generation."""

import asyncio
import os
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
import json

from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_retry,
    after_retry
)
from ratelimit import limits, sleep_and_retry
from loguru import logger
from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    """Model for generation requests."""
    prompt: str
    temperature: float = Field(default=0.8, ge=0.0, le=2.0)
    max_tokens: int = Field(default=150, ge=1, le=4000)
    model: str = Field(default="gpt-3.5-turbo")
    n: int = Field(default=1, ge=1, le=10)


class GenerationResponse(BaseModel):
    """Model for generation responses."""
    text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    timestamp: datetime


class RateLimitedOpenAIClient:
    """OpenAI client with rate limiting and retry logic."""
    
    # Rate limits for different models (requests per minute)
    RATE_LIMITS = {
        "gpt-3.5-turbo": 3500,  # Tier 2 limits
        "gpt-4": 500,           # Tier 2 limits
    }
    
    # Token limits per minute
    TOKEN_LIMITS = {
        "gpt-3.5-turbo": 90000,  # Tier 2 limits
        "gpt-4": 10000,          # Tier 2 limits
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenAI client with rate limiting."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided or found in environment")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.token_usage = {}
        self.request_counts = {}
        self._reset_counters()
        
        logger.info("Initialized RateLimitedOpenAIClient")
    
    def _reset_counters(self):
        """Reset usage counters."""
        now = datetime.now()
        self.token_usage = {
            "gpt-3.5-turbo": {"tokens": 0, "reset_at": now + timedelta(minutes=1)},
            "gpt-4": {"tokens": 0, "reset_at": now + timedelta(minutes=1)},
        }
        self.request_counts = {
            "gpt-3.5-turbo": {"count": 0, "reset_at": now + timedelta(minutes=1)},
            "gpt-4": {"count": 0, "reset_at": now + timedelta(minutes=1)},
        }
    
    def _check_and_update_limits(self, model: str, estimated_tokens: int):
        """Check if we're within rate limits and update counters."""
        now = datetime.now()
        
        # Reset counters if needed
        if now >= self.token_usage[model]["reset_at"]:
            self.token_usage[model] = {"tokens": 0, "reset_at": now + timedelta(minutes=1)}
        if now >= self.request_counts[model]["reset_at"]:
            self.request_counts[model] = {"count": 0, "reset_at": now + timedelta(minutes=1)}
        
        # Check limits
        if self.request_counts[model]["count"] >= self.RATE_LIMITS[model]:
            wait_time = (self.request_counts[model]["reset_at"] - now).total_seconds()
            raise Exception(f"Rate limit reached. Wait {wait_time:.1f} seconds")
        
        if self.token_usage[model]["tokens"] + estimated_tokens > self.TOKEN_LIMITS[model]:
            wait_time = (self.token_usage[model]["reset_at"] - now).total_seconds()
            raise Exception(f"Token limit reached. Wait {wait_time:.1f} seconds")
        
        # Update counters
        self.request_counts[model]["count"] += 1
        self.token_usage[model]["tokens"] += estimated_tokens
    
    @staticmethod
    def _log_retry(retry_state):
        """Log retry attempts."""
        logger.warning(
            f"Retrying OpenAI API call. Attempt {retry_state.attempt_number}, "
            f"wait time: {retry_state.next_action.sleep} seconds"
        )
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((Exception,)),
        before=lambda retry_state: logger.debug(f"Calling OpenAI API..."),
        after=_log_retry.__func__
    )
    async def generate_single(self, request: GenerationRequest) -> GenerationResponse:
        """Generate a single completion with retry logic."""
        try:
            # Estimate tokens (rough approximation)
            estimated_tokens = len(request.prompt.split()) * 1.5 + request.max_tokens
            
            # Check rate limits
            self._check_and_update_limits(request.model, int(estimated_tokens))
            
            # Make the API call
            response = await self.client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates diverse examples of user prompts for different AI tasks."},
                    {"role": "user", "content": request.prompt}
                ],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                n=request.n
            )
            
            # Extract the generated text
            generated_text = response.choices[0].message.content.strip()
            
            # Create response
            return GenerationResponse(
                text=generated_text,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                model=response.model,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise
    
    async def generate_batch(
        self, 
        requests: List[GenerationRequest], 
        batch_size: int = 10,
        delay_between_batches: float = 1.0
    ) -> AsyncGenerator[GenerationResponse, None]:
        """Generate multiple completions in batches."""
        logger.info(f"Starting batch generation for {len(requests)} requests")
        
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [self.generate_single(req) for req in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Yield successful results
            for result in results:
                if isinstance(result, GenerationResponse):
                    yield result
                else:
                    logger.error(f"Failed generation: {result}")
            
            # Delay between batches to avoid rate limits
            if i + batch_size < len(requests):
                await asyncio.sleep(delay_between_batches)
    
    async def generate_with_validation(
        self, 
        request: GenerationRequest,
        validator: Optional[callable] = None,
        max_retries: int = 3
    ) -> Optional[GenerationResponse]:
        """Generate with validation and retry if validation fails."""
        for attempt in range(max_retries):
            try:
                response = await self.generate_single(request)
                
                # Validate if validator provided
                if validator and not validator(response.text):
                    logger.warning(f"Validation failed for attempt {attempt + 1}")
                    continue
                
                return response
                
            except Exception as e:
                logger.error(f"Generation failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise
        
        return None
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return {
            "token_usage": self.token_usage,
            "request_counts": self.request_counts,
            "timestamp": datetime.now().isoformat()
        }


# Convenience function for creating the client
def create_openai_client(api_key: Optional[str] = None) -> RateLimitedOpenAIClient:
    """Create and return a rate-limited OpenAI client."""
    return RateLimitedOpenAIClient(api_key=api_key)


# Example usage
if __name__ == "__main__":
    async def main():
        # Create client
        client = create_openai_client()
        
        # Test single generation
        request = GenerationRequest(
            prompt="Generate a question about machine learning for a beginner",
            temperature=0.8,
            max_tokens=50
        )
        
        response = await client.generate_single(request)
        print(f"Generated: {response.text}")
        print(f"Tokens used: {response.total_tokens}")
        
        # Test batch generation
        requests = [
            GenerationRequest(prompt=f"Generate a {intent} example")
            for intent in ["question", "command", "analysis request"]
        ]
        
        async for response in client.generate_batch(requests, batch_size=2):
            print(f"Batch result: {response.text[:50]}...")
    
    # Run example
    asyncio.run(main())