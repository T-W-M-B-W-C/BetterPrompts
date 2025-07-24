#!/usr/bin/env python3
"""Performance testing script for cache impact analysis."""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import random
import json
from datetime import datetime

import httpx
import click
from rich import print
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()

# Test data - diverse prompts for classification
TEST_PROMPTS = [
    "How do I implement a binary search algorithm in Python?",
    "Write a creative story about a robot learning to paint",
    "Analyze this sales data and identify trends",
    "Translate this paragraph from English to Spanish",
    "What's the capital of France?",
    "Help me debug this JavaScript function",
    "Create a marketing plan for a new mobile app",
    "Explain quantum computing like I'm five",
    "Design a REST API for a social media platform",
    "Calculate the compound interest on a $10,000 investment",
    "Write a haiku about artificial intelligence",
    "How can I optimize my PostgreSQL queries?",
    "Summarize this 10-page research paper",
    "Plan a 7-day trip to Japan",
    "Solve this differential equation",
    "Generate test cases for a login system",
    "What are the best practices for React hooks?",
    "Create a meal plan for a vegetarian athlete",
    "Explain the theory of relativity",
    "Debug this memory leak in my C++ application",
]


class CachePerformanceTester:
    """Performance tester for intent classifier cache."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        """Initialize the tester."""
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def __aenter__(self):
        """Enter async context."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        await self.client.aclose()
    
    async def clear_cache(self) -> bool:
        """Clear all cached results."""
        # This would typically be done through a management endpoint
        # For now, we'll assume cache entries expire naturally
        return True
    
    async def classify_intent(self, text: str) -> Dict[str, Any]:
        """Classify a single intent."""
        start_time = time.time()
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/intents/classify",
            json={"text": text}
        )
        
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            result["response_time"] = end_time - start_time
            return result
        else:
            raise Exception(f"Classification failed: {response.status_code}")
    
    async def run_classification_batch(
        self,
        prompts: List[str],
        name: str = "Batch"
    ) -> Dict[str, Any]:
        """Run a batch of classifications and collect metrics."""
        console.print(f"\n[bold blue]Running {name}...[/bold blue]")
        
        response_times = []
        results = []
        errors = 0
        
        for prompt in track(prompts, description=f"Processing {name}"):
            try:
                result = await self.classify_intent(prompt)
                response_times.append(result["response_time"])
                results.append(result)
            except Exception as e:
                errors += 1
                console.print(f"[red]Error: {e}[/red]")
        
        # Calculate statistics
        if response_times:
            stats = {
                "name": name,
                "total_requests": len(prompts),
                "successful_requests": len(response_times),
                "errors": errors,
                "avg_response_time": statistics.mean(response_times),
                "median_response_time": statistics.median(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "p95_response_time": statistics.quantiles(response_times, n=20)[18],
                "p99_response_time": statistics.quantiles(response_times, n=100)[98],
                "std_dev": statistics.stdev(response_times) if len(response_times) > 1 else 0,
            }
        else:
            stats = {
                "name": name,
                "total_requests": len(prompts),
                "successful_requests": 0,
                "errors": errors,
            }
        
        return stats
    
    async def run_cache_impact_test(self) -> Dict[str, Any]:
        """Run comprehensive cache impact test."""
        console.print("[bold green]Starting Cache Impact Performance Test[/bold green]")
        
        results = {}
        
        # Test 1: Cold cache (first run)
        console.print("\n[yellow]Test 1: Cold Cache Performance[/yellow]")
        cold_stats = await self.run_classification_batch(
            TEST_PROMPTS,
            "Cold Cache"
        )
        results["cold_cache"] = cold_stats
        
        # Test 2: Warm cache (second run with same prompts)
        console.print("\n[yellow]Test 2: Warm Cache Performance[/yellow]")
        warm_stats = await self.run_classification_batch(
            TEST_PROMPTS,
            "Warm Cache"
        )
        results["warm_cache"] = warm_stats
        
        # Test 3: Mixed cache (50% cached, 50% new)
        console.print("\n[yellow]Test 3: Mixed Cache Performance[/yellow]")
        mixed_prompts = TEST_PROMPTS[:10] + [
            f"{prompt} - variation {i}" 
            for i, prompt in enumerate(TEST_PROMPTS[10:])
        ]
        mixed_stats = await self.run_classification_batch(
            mixed_prompts,
            "Mixed Cache"
        )
        results["mixed_cache"] = mixed_stats
        
        # Test 4: Concurrent requests
        console.print("\n[yellow]Test 4: Concurrent Request Performance[/yellow]")
        concurrent_stats = await self.run_concurrent_test()
        results["concurrent"] = concurrent_stats
        
        # Calculate cache impact
        if cold_stats["successful_requests"] > 0 and warm_stats["successful_requests"] > 0:
            cache_speedup = cold_stats["avg_response_time"] / warm_stats["avg_response_time"]
            cache_impact_pct = ((cold_stats["avg_response_time"] - warm_stats["avg_response_time"]) 
                              / cold_stats["avg_response_time"] * 100)
            
            results["cache_impact"] = {
                "speedup_factor": round(cache_speedup, 2),
                "performance_improvement_pct": round(cache_impact_pct, 2),
                "avg_cold_response_ms": round(cold_stats["avg_response_time"] * 1000, 2),
                "avg_warm_response_ms": round(warm_stats["avg_response_time"] * 1000, 2),
            }
        
        return results
    
    async def run_concurrent_test(self, num_concurrent: int = 10) -> Dict[str, Any]:
        """Run concurrent request test."""
        # Create tasks for concurrent execution
        tasks = []
        prompts = random.choices(TEST_PROMPTS, k=num_concurrent)
        
        start_time = time.time()
        
        for prompt in prompts:
            task = asyncio.create_task(self.classify_intent(prompt))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Count successes and failures
        successes = sum(1 for r in results if not isinstance(r, Exception))
        failures = len(results) - successes
        
        return {
            "name": "Concurrent Requests",
            "total_requests": num_concurrent,
            "successful_requests": successes,
            "errors": failures,
            "total_time": total_time,
            "avg_response_time": total_time / num_concurrent,
            "requests_per_second": num_concurrent / total_time if total_time > 0 else 0,
        }
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted results."""
        console.print("\n[bold green]Performance Test Results[/bold green]")
        
        # Create results table
        table = Table(title="Response Time Comparison")
        table.add_column("Test", style="cyan")
        table.add_column("Avg Response (ms)", justify="right", style="yellow")
        table.add_column("P95 (ms)", justify="right", style="yellow")
        table.add_column("P99 (ms)", justify="right", style="yellow")
        table.add_column("Success Rate", justify="right", style="green")
        
        for test_name in ["cold_cache", "warm_cache", "mixed_cache"]:
            if test_name in results:
                stats = results[test_name]
                if stats["successful_requests"] > 0:
                    success_rate = f"{(stats['successful_requests'] / stats['total_requests'] * 100):.1f}%"
                    table.add_row(
                        stats["name"],
                        f"{stats['avg_response_time'] * 1000:.2f}",
                        f"{stats['p95_response_time'] * 1000:.2f}",
                        f"{stats['p99_response_time'] * 1000:.2f}",
                        success_rate
                    )
        
        console.print(table)
        
        # Print cache impact
        if "cache_impact" in results:
            impact = results["cache_impact"]
            console.print("\n[bold yellow]Cache Impact Analysis[/bold yellow]")
            console.print(f"🚀 Speedup Factor: [green]{impact['speedup_factor']}x[/green]")
            console.print(f"📈 Performance Improvement: [green]{impact['performance_improvement_pct']}%[/green]")
            console.print(f"❄️  Cold Cache Avg: [yellow]{impact['avg_cold_response_ms']}ms[/yellow]")
            console.print(f"🔥 Warm Cache Avg: [green]{impact['avg_warm_response_ms']}ms[/green]")
        
        # Print concurrent test results
        if "concurrent" in results:
            concurrent = results["concurrent"]
            console.print("\n[bold yellow]Concurrent Request Performance[/bold yellow]")
            console.print(f"⚡ Requests per Second: [green]{concurrent['requests_per_second']:.2f}[/green]")
            console.print(f"⏱️  Avg Response Time: [yellow]{concurrent['avg_response_time'] * 1000:.2f}ms[/yellow]")
        
        # Save detailed results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cache_performance_results_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        console.print(f"\n💾 Detailed results saved to: [blue]{filename}[/blue]")


@click.command()
@click.option(
    "--base-url",
    default="http://localhost:8001",
    help="Base URL of the intent classifier service"
)
@click.option(
    "--full-test",
    is_flag=True,
    help="Run extended test with more iterations"
)
async def main(base_url: str, full_test: bool):
    """Run cache performance tests."""
    async with CachePerformanceTester(base_url) as tester:
        try:
            # Check service health first
            health_response = await tester.client.get(f"{base_url}/health")
            if health_response.status_code != 200:
                console.print("[red]Service is not healthy![/red]")
                return
            
            # Run the tests
            results = await tester.run_cache_impact_test()
            
            # Print formatted results
            tester.print_results(results)
            
            # Run extended tests if requested
            if full_test:
                console.print("\n[bold blue]Running Extended Tests...[/bold blue]")
                # Add more comprehensive tests here
                
        except Exception as e:
            console.print(f"[red]Test failed: {e}[/red]")
            raise


if __name__ == "__main__":
    asyncio.run(main())