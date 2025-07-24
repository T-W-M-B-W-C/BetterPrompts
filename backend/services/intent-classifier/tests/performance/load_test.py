#!/usr/bin/env python3
"""Load testing script for intent classifier with cache monitoring."""

import asyncio
import time
import random
from typing import List, Dict, Any
from datetime import datetime
import statistics

import httpx
import click
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

console = Console()

# Sample prompts for load testing
LOAD_TEST_PROMPTS = [
    "How do I center a div in CSS?",
    "What's the difference between let and const in JavaScript?",
    "Explain Docker containers",
    "Write a Python function to reverse a string",
    "What are microservices?",
    "How does garbage collection work?",
    "Explain REST vs GraphQL",
    "What is a SQL injection attack?",
    "How do neural networks learn?",
    "What's the difference between TCP and UDP?",
    "Explain blockchain technology",
    "How do I optimize database queries?",
    "What is continuous integration?",
    "Explain the CAP theorem",
    "How does OAuth 2.0 work?",
    "What are design patterns?",
    "Explain async/await in JavaScript",
    "What is test-driven development?",
    "How does Git branching work?",
    "What are WebSockets used for?",
]


class LoadTester:
    """Load tester for intent classifier."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "response_times": [],
            "start_time": time.time(),
        }
        
    async def make_request(self, client: httpx.AsyncClient, text: str) -> Dict[str, Any]:
        """Make a single classification request."""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{self.base_url}/api/v1/intents/classify",
                json={"text": text},
                timeout=10.0
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                # Check if this was a cache hit based on response time
                # Cached responses are typically < 10ms
                is_cache_hit = elapsed < 0.01
                
                return {
                    "success": True,
                    "response_time": elapsed,
                    "cache_hit": is_cache_hit,
                    "data": result
                }
            else:
                return {
                    "success": False,
                    "response_time": elapsed,
                    "error": f"Status {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "response_time": time.time() - start_time,
                "error": str(e)
            }
    
    async def worker(self, client: httpx.AsyncClient, rate_limiter: asyncio.Semaphore):
        """Worker coroutine for continuous load generation."""
        while True:
            async with rate_limiter:
                # Pick a random prompt
                text = random.choice(LOAD_TEST_PROMPTS)
                
                # Make request
                result = await self.make_request(client, text)
                
                # Update stats
                self.stats["total_requests"] += 1
                
                if result["success"]:
                    self.stats["successful_requests"] += 1
                    self.stats["response_times"].append(result["response_time"])
                    if result.get("cache_hit"):
                        self.stats["cache_hits"] += 1
                else:
                    self.stats["failed_requests"] += 1
                
                # Keep only last 1000 response times for memory efficiency
                if len(self.stats["response_times"]) > 1000:
                    self.stats["response_times"] = self.stats["response_times"][-1000:]
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        elapsed = time.time() - self.stats["start_time"]
        
        if self.stats["response_times"]:
            response_times = self.stats["response_times"]
            current_stats = {
                "duration": elapsed,
                "total_requests": self.stats["total_requests"],
                "successful_requests": self.stats["successful_requests"],
                "failed_requests": self.stats["failed_requests"],
                "cache_hits": self.stats["cache_hits"],
                "requests_per_second": self.stats["total_requests"] / elapsed if elapsed > 0 else 0,
                "success_rate": self.stats["successful_requests"] / self.stats["total_requests"] * 100 
                    if self.stats["total_requests"] > 0 else 0,
                "cache_hit_rate": self.stats["cache_hits"] / self.stats["successful_requests"] * 100 
                    if self.stats["successful_requests"] > 0 else 0,
                "avg_response_time": statistics.mean(response_times),
                "median_response_time": statistics.median(response_times),
                "p95_response_time": statistics.quantiles(response_times, n=20)[18] 
                    if len(response_times) > 20 else max(response_times),
                "p99_response_time": statistics.quantiles(response_times, n=100)[98] 
                    if len(response_times) > 100 else max(response_times),
            }
        else:
            current_stats = {
                "duration": elapsed,
                "total_requests": self.stats["total_requests"],
                "successful_requests": self.stats["successful_requests"],
                "failed_requests": self.stats["failed_requests"],
                "requests_per_second": 0,
                "success_rate": 0,
                "cache_hit_rate": 0,
            }
        
        return current_stats
    
    def create_stats_table(self) -> Table:
        """Create a table with current statistics."""
        stats = self.get_current_stats()
        
        table = Table(title=f"Load Test Statistics - {datetime.now().strftime('%H:%M:%S')}")
        table.add_column("Metric", style="cyan", width=30)
        table.add_column("Value", style="yellow", width=20)
        
        table.add_row("Duration", f"{stats['duration']:.1f}s")
        table.add_row("Total Requests", f"{stats['total_requests']:,}")
        table.add_row("Successful", f"{stats['successful_requests']:,}")
        table.add_row("Failed", f"{stats['failed_requests']:,}")
        table.add_row("Requests/sec", f"{stats['requests_per_second']:.2f}")
        table.add_row("Success Rate", f"{stats['success_rate']:.1f}%")
        table.add_row("Cache Hit Rate", f"{stats['cache_hit_rate']:.1f}%")
        
        if "avg_response_time" in stats:
            table.add_row("Avg Response Time", f"{stats['avg_response_time']*1000:.2f}ms")
            table.add_row("Median Response Time", f"{stats['median_response_time']*1000:.2f}ms")
            table.add_row("P95 Response Time", f"{stats['p95_response_time']*1000:.2f}ms")
            table.add_row("P99 Response Time", f"{stats['p99_response_time']*1000:.2f}ms")
        
        return table
    
    async def run_load_test(self, duration: int, rps: int):
        """Run load test for specified duration and rate."""
        console.print(f"[bold green]Starting load test: {rps} RPS for {duration} seconds[/bold green]")
        
        # Create rate limiter
        rate_limiter = asyncio.Semaphore(rps)
        
        # Create HTTP client with connection pooling
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        ) as client:
            
            # Check service health
            try:
                health = await client.get(f"{self.base_url}/health")
                if health.status_code != 200:
                    console.print("[red]Service is not healthy![/red]")
                    return
            except Exception as e:
                console.print(f"[red]Cannot connect to service: {e}[/red]")
                return
            
            # Create workers
            workers = []
            for _ in range(min(rps, 100)):  # Cap at 100 concurrent workers
                worker = asyncio.create_task(self.worker(client, rate_limiter))
                workers.append(worker)
            
            # Run with live display
            with Live(self.create_stats_table(), refresh_per_second=1) as live:
                try:
                    # Run for specified duration
                    start_time = time.time()
                    while time.time() - start_time < duration:
                        await asyncio.sleep(1)
                        live.update(self.create_stats_table())
                        
                        # Release permits for rate limiting
                        for _ in range(rps):
                            try:
                                rate_limiter.release()
                            except ValueError:
                                pass  # Semaphore full
                    
                finally:
                    # Cancel all workers
                    for worker in workers:
                        worker.cancel()
                    
                    await asyncio.gather(*workers, return_exceptions=True)
            
            # Print final summary
            console.print("\n[bold green]Load Test Complete![/bold green]")
            final_stats = self.get_current_stats()
            
            summary = Table(title="Final Summary")
            summary.add_column("Metric", style="cyan")
            summary.add_column("Value", style="yellow")
            
            summary.add_row("Total Requests", f"{final_stats['total_requests']:,}")
            summary.add_row("Success Rate", f"{final_stats['success_rate']:.1f}%")
            summary.add_row("Cache Hit Rate", f"{final_stats['cache_hit_rate']:.1f}%")
            summary.add_row("Avg Requests/sec", f"{final_stats['requests_per_second']:.2f}")
            
            if "avg_response_time" in final_stats:
                summary.add_row("Avg Response Time", f"{final_stats['avg_response_time']*1000:.2f}ms")
                summary.add_row("P95 Response Time", f"{final_stats['p95_response_time']*1000:.2f}ms")
                summary.add_row("P99 Response Time", f"{final_stats['p99_response_time']*1000:.2f}ms")
            
            console.print(summary)


@click.command()
@click.option(
    "--base-url",
    default="http://localhost:8001",
    help="Base URL of the intent classifier service"
)
@click.option(
    "--duration",
    "-d",
    default=60,
    help="Duration of the load test in seconds"
)
@click.option(
    "--rps",
    "-r",
    default=10,
    help="Target requests per second"
)
async def main(base_url: str, duration: int, rps: int):
    """Run load test against intent classifier."""
    tester = LoadTester(base_url)
    await tester.run_load_test(duration, rps)


if __name__ == "__main__":
    asyncio.run(main())