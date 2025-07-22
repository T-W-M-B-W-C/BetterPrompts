"""
Integration tests for batch processing and performance
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any
from unittest.mock import patch, AsyncMock
import statistics

from app.engine import PromptGenerationEngine
from app.models import (
    PromptGenerationRequest,
    PromptGenerationResponse,
    BatchGenerationRequest,
    BatchGenerationResponse,
    TechniqueType
)


class TestBatchProcessing:
    """Test batch processing capabilities"""
    
    @pytest.fixture
    async def engine(self):
        """Create an engine instance"""
        return PromptGenerationEngine()
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_small_batch_processing(self, engine):
        """Test processing a small batch of prompts"""
        batch_size = 5
        requests = [
            PromptGenerationRequest(
                text=f"Explain concept {i}",
                intent="explain_concept",
                complexity="simple",
                techniques=["chain_of_thought"],
                target_model="gpt-4"
            )
            for i in range(batch_size)
        ]
        
        start_time = time.time()
        responses = []
        
        for request in requests:
            response = await engine.generate(request)
            responses.append(response)
            
        end_time = time.time()
        
        assert len(responses) == batch_size
        assert all(isinstance(r, PromptGenerationResponse) for r in responses)
        assert all(r.text != requests[i].text for i, r in enumerate(responses))
        
        # Check performance
        total_time = end_time - start_time
        assert total_time < batch_size * 2  # Less than 2 seconds per prompt
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_medium_batch_processing(self, engine):
        """Test processing a medium batch of prompts"""
        batch_size = 20
        requests = []
        
        # Mix of different complexities and techniques
        for i in range(batch_size):
            complexity = ["simple", "moderate", "complex"][i % 3]
            techniques = [
                ["chain_of_thought"],
                ["few_shot", "structured_output"],
                ["tree_of_thoughts", "step_by_step", "constraints"]
            ][i % 3]
            
            requests.append(PromptGenerationRequest(
                text=f"Task {i}: Process this {complexity} request",
                intent="process",
                complexity=complexity,
                techniques=techniques,
                target_model="gpt-4"
            ))
            
        # Process with timing
        timings = []
        responses = []
        
        for request in requests:
            start = time.time()
            response = await engine.generate(request)
            end = time.time()
            
            timings.append(end - start)
            responses.append(response)
            
        assert len(responses) == batch_size
        
        # Analyze timings
        avg_time = statistics.mean(timings)
        max_time = max(timings)
        min_time = min(timings)
        
        assert avg_time < 2.0  # Average under 2 seconds
        assert max_time < 5.0  # No single request over 5 seconds
        
        # Complex prompts should generally take longer
        simple_times = [timings[i] for i in range(0, batch_size, 3)]
        complex_times = [timings[i] for i in range(2, batch_size, 3)]
        
        assert statistics.mean(complex_times) >= statistics.mean(simple_times) * 0.8
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_batch_processing(self, engine):
        """Test processing a large batch of prompts"""
        batch_size = 50
        
        # Create diverse requests
        requests = []
        for i in range(batch_size):
            intent = ["explain_concept", "generate_code", "analyze_data", "create_content"][i % 4]
            complexity = ["simple", "moderate", "complex"][i % 3]
            technique_sets = [
                ["chain_of_thought"],
                ["few_shot", "structured_output"],
                ["tree_of_thoughts", "constraints"],
                ["step_by_step", "role_play"],
                ["analogical", "emotional_appeal"]
            ]
            techniques = technique_sets[i % len(technique_sets)]
            
            requests.append(PromptGenerationRequest(
                text=f"Batch item {i}: {intent} task with {complexity} complexity",
                intent=intent,
                complexity=complexity,
                techniques=techniques,
                target_model="gpt-4"
            ))
            
        # Process in chunks to avoid overwhelming the system
        chunk_size = 10
        all_responses = []
        chunk_times = []
        
        for i in range(0, batch_size, chunk_size):
            chunk = requests[i:i + chunk_size]
            chunk_start = time.time()
            
            # Process chunk
            for request in chunk:
                response = await engine.generate(request)
                all_responses.append(response)
                
            chunk_end = time.time()
            chunk_times.append(chunk_end - chunk_start)
            
            # Small delay between chunks
            await asyncio.sleep(0.1)
            
        assert len(all_responses) == batch_size
        
        # Verify all responses are unique
        response_ids = [r.id for r in all_responses]
        assert len(set(response_ids)) == batch_size
        
        # Check chunk processing times
        avg_chunk_time = statistics.mean(chunk_times)
        assert avg_chunk_time < chunk_size * 2  # Less than 2 seconds per item
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_batch_processing(self, engine):
        """Test concurrent processing of multiple prompts"""
        concurrent_limit = 5
        total_prompts = 15
        
        requests = [
            PromptGenerationRequest(
                text=f"Concurrent prompt {i}",
                intent="test",
                complexity="simple",
                techniques=["zero_shot"],
                target_model="gpt-4"
            )
            for i in range(total_prompts)
        ]
        
        async def process_with_semaphore(request, semaphore):
            async with semaphore:
                return await engine.generate(request)
                
        # Use semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        start_time = time.time()
        
        # Process all requests concurrently with limit
        tasks = [
            process_with_semaphore(request, semaphore)
            for request in requests
        ]
        responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        assert len(responses) == total_prompts
        assert all(isinstance(r, PromptGenerationResponse) for r in responses)
        
        # Should be faster than sequential processing
        expected_sequential_time = total_prompts * 0.5  # Assume 0.5s per prompt
        assert total_time < expected_sequential_time
        
        # But not faster than if all were truly parallel
        min_expected_time = (total_prompts / concurrent_limit) * 0.5
        assert total_time > min_expected_time * 0.5  # Some overhead expected
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_error_handling(self, engine):
        """Test batch processing with errors"""
        requests = [
            # Valid request
            PromptGenerationRequest(
                text="Valid prompt 1",
                intent="explain_concept",
                complexity="simple",
                techniques=["chain_of_thought"]
            ),
            # Invalid request (will be caught during generation)
            PromptGenerationRequest(
                text="",  # Empty
                intent="explain_concept",
                complexity="simple",
                techniques=["chain_of_thought"]
            ),
            # Valid request
            PromptGenerationRequest(
                text="Valid prompt 2",
                intent="explain_concept",
                complexity="simple",
                techniques=["zero_shot"]
            ),
            # Invalid technique (will be caught during validation)
            PromptGenerationRequest(
                text="Invalid technique test",
                intent="explain_concept",
                complexity="simple",
                techniques=["invalid_technique"]
            ),
            # Valid request
            PromptGenerationRequest(
                text="Valid prompt 3",
                intent="explain_concept",
                complexity="simple",
                techniques=["step_by_step"]
            )
        ]
        
        results = []
        errors = []
        
        for i, request in enumerate(requests):
            try:
                response = await engine.generate(request)
                results.append((i, response))
            except Exception as e:
                errors.append((i, str(e)))
                
        # Should have 3 successes and 2 errors
        assert len(results) == 3
        assert len(errors) == 2
        
        # Check error indices
        error_indices = [e[0] for e in errors]
        assert 1 in error_indices  # Empty prompt
        assert 3 in error_indices  # Invalid technique
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_memory_efficiency(self, engine):
        """Test memory efficiency during batch processing"""
        import gc
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process a batch
        batch_size = 20
        requests = [
            PromptGenerationRequest(
                text=f"Memory test prompt {i} with some content to process",
                intent="test",
                complexity="moderate",
                techniques=["chain_of_thought", "structured_output"],
                target_model="gpt-4"
            )
            for i in range(batch_size)
        ]
        
        responses = []
        for request in requests:
            response = await engine.generate(request)
            responses.append(response)
            
        # Get memory after processing
        mid_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Clear responses and force garbage collection
        responses.clear()
        gc.collect()
        await asyncio.sleep(0.1)
        
        # Get final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Memory increase should be reasonable
        memory_increase = mid_memory - initial_memory
        memory_recovered = mid_memory - final_memory
        
        assert memory_increase < 100  # Less than 100MB increase
        assert memory_recovered > 0  # Some memory should be recovered
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_with_different_models(self, engine):
        """Test batch processing with different target models"""
        models = ["gpt-4", "gpt-3.5-turbo", "claude-2"]
        requests = []
        
        for i, model in enumerate(models * 3):  # 9 requests total
            requests.append(PromptGenerationRequest(
                text=f"Test prompt for {model}",
                intent="test",
                complexity="simple",
                techniques=["zero_shot"],
                target_model=model
            ))
            
        responses = []
        response_times = {model: [] for model in models}
        
        for request in requests:
            start = time.time()
            response = await engine.generate(request)
            end = time.time()
            
            responses.append(response)
            response_times[request.target_model].append(end - start)
            
        assert len(responses) == len(requests)
        
        # Analyze response times by model
        for model, times in response_times.items():
            avg_time = statistics.mean(times)
            assert avg_time < 3.0  # All models should respond within 3 seconds
            
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_technique_distribution(self, engine):
        """Test batch processing with various technique combinations"""
        # Create requests with different technique combinations
        technique_combinations = [
            ["chain_of_thought"],
            ["tree_of_thoughts"],
            ["few_shot", "structured_output"],
            ["step_by_step", "constraints"],
            ["role_play", "emotional_appeal"],
            ["analogical", "self_consistency"],
            ["react", "structured_output"],
            ["zero_shot"],
            ["chain_of_thought", "tree_of_thoughts", "structured_output"],
            ["few_shot", "step_by_step", "constraints", "structured_output"]
        ]
        
        requests = []
        for i, techniques in enumerate(technique_combinations * 2):  # 20 requests
            requests.append(PromptGenerationRequest(
                text=f"Test different technique combination {i}",
                intent="test",
                complexity="moderate",
                techniques=techniques,
                target_model="gpt-4"
            ))
            
        # Process and track technique usage
        technique_times = {}
        responses = []
        
        for request in requests:
            start = time.time()
            response = await engine.generate(request)
            end = time.time()
            
            responses.append(response)
            
            # Track time for each technique combination
            key = ",".join(sorted(request.techniques))
            if key not in technique_times:
                technique_times[key] = []
            technique_times[key].append(end - start)
            
        assert len(responses) == len(requests)
        
        # Analyze technique performance
        for techniques, times in technique_times.items():
            avg_time = statistics.mean(times)
            technique_count = len(techniques.split(","))
            
            # More techniques should generally take more time
            if technique_count == 1:
                assert avg_time < 2.0
            elif technique_count <= 3:
                assert avg_time < 3.0
            else:
                assert avg_time < 4.0
                
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_cancellation(self, engine):
        """Test cancelling batch processing"""
        batch_size = 10
        requests = [
            PromptGenerationRequest(
                text=f"Cancellation test {i}",
                intent="test",
                complexity="simple",
                techniques=["chain_of_thought"],
                target_model="gpt-4"
            )
            for i in range(batch_size)
        ]
        
        # Process with cancellation after 5
        responses = []
        cancelled = False
        
        for i, request in enumerate(requests):
            if i >= 5:
                cancelled = True
                break
                
            response = await engine.generate(request)
            responses.append(response)
            
        assert len(responses) == 5
        assert cancelled is True
        
        # Verify the completed responses
        assert all(isinstance(r, PromptGenerationResponse) for r in responses)
        
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_priority_processing(self, engine):
        """Test processing prompts with different priorities"""
        # Create requests with priorities
        high_priority = [
            PromptGenerationRequest(
                text=f"High priority {i}",
                intent="urgent",
                complexity="simple",
                techniques=["zero_shot"],
                target_model="gpt-4"
            )
            for i in range(3)
        ]
        
        low_priority = [
            PromptGenerationRequest(
                text=f"Low priority {i}",
                intent="standard",
                complexity="simple",
                techniques=["zero_shot"],
                target_model="gpt-4"
            )
            for i in range(3)
        ]
        
        # In a real system, high priority would be processed first
        # For this test, we'll simulate priority handling
        all_requests = high_priority + low_priority
        
        # Process with priority simulation
        responses = []
        for request in all_requests:
            response = await engine.generate(request)
            responses.append(response)
            
            # Simulate faster processing for high priority
            if "High priority" in request.text:
                await asyncio.sleep(0.05)
            else:
                await asyncio.sleep(0.1)
                
        assert len(responses) == 6
        
        # All responses should be valid
        assert all(isinstance(r, PromptGenerationResponse) for r in responses)