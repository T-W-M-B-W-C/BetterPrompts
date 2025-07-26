#!/usr/bin/env python3
"""
Wave 8: Performance Benchmarking Framework
Tests latency and throughput for all models against performance targets
"""

import json
import time
import statistics
import concurrent.futures
from typing import Dict, List, Tuple
from dataclasses import dataclass
import requests
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

@dataclass
class PerformanceMetric:
    model: str
    operation: str
    latency_ms: float
    success: bool
    timestamp: float

@dataclass 
class BenchmarkConfig:
    name: str
    description: str
    requests_per_test: int
    concurrent_workers: int
    test_duration_seconds: int
    warmup_requests: int

class PerformanceBenchmark:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.metrics: List[PerformanceMetric] = []
        
        # Performance targets
        self.latency_targets = {
            "rules": 50,  # <50ms p95
            "zero_shot": 200,  # <200ms p95
            "distilbert": 100,  # <100ms p95 (with ONNX)
            "hybrid": 75,  # <75ms p95 average
        }
        
        # Test configurations
        self.benchmark_configs = [
            BenchmarkConfig(
                name="single_thread_latency",
                description="Single-threaded latency test",
                requests_per_test=100,
                concurrent_workers=1,
                test_duration_seconds=30,
                warmup_requests=10
            ),
            BenchmarkConfig(
                name="moderate_load",
                description="Moderate concurrent load",
                requests_per_test=500,
                concurrent_workers=10,
                test_duration_seconds=60,
                warmup_requests=50
            ),
            BenchmarkConfig(
                name="high_load",
                description="High concurrent load",
                requests_per_test=1000,
                concurrent_workers=50,
                test_duration_seconds=120,
                warmup_requests=100
            ),
            BenchmarkConfig(
                name="stress_test",
                description="Stress test with maximum load",
                requests_per_test=2000,
                concurrent_workers=100,
                test_duration_seconds=180,
                warmup_requests=200
            ),
        ]
        
        # Test prompts for different models
        self.test_prompts = {
            "rules_friendly": [
                "What is photosynthesis?",
                "How can I fix my computer?",
                "Write a story about a cat",
                "Translate hello to Spanish",
                "Explain gravity",
            ],
            "ambiguous": [
                "Tell me about it",
                "Help me with this",
                "What should I do?",
                "Can you assist?",
                "I need guidance",
            ],
            "complex": [
                "Explain quantum entanglement and its implications for computing",
                "Design a distributed caching strategy for microservices",
                "Write a technical analysis of Byzantine fault tolerance",
                "Create a comprehensive disaster recovery plan",
                "Analyze the socioeconomic impacts of automation",
            ]
        }
    
    def force_model_selection(self, model: str) -> None:
        """Force the classifier to use a specific model via feature flags"""
        if model == "rules":
            # Enable performance mode (rules first)
            requests.put(
                f"{self.base_url}/api/v1/feature-flags/performance_mode",
                json={"enabled": True, "rollout_percentage": 100}
            )
            requests.put(
                f"{self.base_url}/api/v1/feature-flags/quality_mode",
                json={"enabled": False}
            )
        elif model == "distilbert":
            # Enable quality mode (DistilBERT first)
            requests.put(
                f"{self.base_url}/api/v1/feature-flags/quality_mode",
                json={"enabled": True, "rollout_percentage": 100}
            )
            requests.put(
                f"{self.base_url}/api/v1/feature-flags/performance_mode",
                json={"enabled": False}
            )
        else:
            # Default adaptive mode
            requests.put(
                f"{self.base_url}/api/v1/feature-flags/performance_mode",
                json={"enabled": False}
            )
            requests.put(
                f"{self.base_url}/api/v1/feature-flags/quality_mode",
                json={"enabled": False}
            )
    
    def make_request(self, text: str, user_id: str = "bench_user") -> Tuple[float, str, bool]:
        """Make a single classification request and measure latency"""
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/intents/classify",
                json={"text": text, "user_id": user_id},
                timeout=10
            )
            response.raise_for_status()
            
            latency_ms = (time.time() - start_time) * 1000
            data = response.json()
            model_used = data.get("model_used", "unknown")
            
            return latency_ms, model_used, True
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return latency_ms, "error", False
    
    def warmup(self, num_requests: int) -> None:
        """Warm up the service before benchmarking"""
        print(f"Warming up with {num_requests} requests...")
        
        prompts = []
        for prompt_list in self.test_prompts.values():
            prompts.extend(prompt_list)
        
        for i in range(num_requests):
            prompt = prompts[i % len(prompts)]
            self.make_request(prompt, f"warmup_{i}")
            
        print("Warmup complete")
        time.sleep(2)  # Let the system stabilize
    
    def run_concurrent_benchmark(self, config: BenchmarkConfig, model_mode: str = None) -> List[PerformanceMetric]:
        """Run concurrent benchmark with specified configuration"""
        print(f"\nRunning benchmark: {config.name}")
        if model_mode:
            print(f"Forcing model mode: {model_mode}")
            self.force_model_selection(model_mode)
        
        # Select appropriate prompts
        if model_mode == "rules":
            prompts = self.test_prompts["rules_friendly"]
        elif model_mode == "zero_shot":
            prompts = self.test_prompts["ambiguous"]
        else:
            # Mix all prompts
            prompts = []
            for prompt_list in self.test_prompts.values():
                prompts.extend(prompt_list)
        
        metrics = []
        start_time = time.time()
        request_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=config.concurrent_workers) as executor:
            futures = []
            
            while time.time() - start_time < config.test_duration_seconds:
                # Submit batch of requests
                for i in range(config.concurrent_workers):
                    prompt = prompts[request_count % len(prompts)]
                    future = executor.submit(
                        self.make_request, 
                        prompt, 
                        f"bench_{request_count}"
                    )
                    futures.append((future, time.time()))
                    request_count += 1
                
                # Collect completed results
                while futures and futures[0][0].done():
                    future, submit_time = futures.pop(0)
                    latency_ms, model_used, success = future.result()
                    
                    metric = PerformanceMetric(
                        model=model_used,
                        operation="classify",
                        latency_ms=latency_ms,
                        success=success,
                        timestamp=submit_time
                    )
                    metrics.append(metric)
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.01)
        
        # Wait for remaining futures
        for future, submit_time in futures:
            latency_ms, model_used, success = future.result()
            metric = PerformanceMetric(
                model=model_used,
                operation="classify",
                latency_ms=latency_ms,
                success=success,
                timestamp=submit_time
            )
            metrics.append(metric)
        
        duration = time.time() - start_time
        print(f"Completed {len(metrics)} requests in {duration:.1f} seconds")
        print(f"Throughput: {len(metrics)/duration:.1f} requests/second")
        
        return metrics
    
    def calculate_percentiles(self, latencies: List[float]) -> Dict[str, float]:
        """Calculate latency percentiles"""
        if not latencies:
            return {"p50": 0, "p75": 0, "p90": 0, "p95": 0, "p99": 0}
        
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        
        return {
            "p50": sorted_latencies[int(n * 0.50)],
            "p75": sorted_latencies[int(n * 0.75)],
            "p90": sorted_latencies[int(n * 0.90)],
            "p95": sorted_latencies[int(n * 0.95)],
            "p99": sorted_latencies[int(n * 0.99)],
        }
    
    def analyze_metrics(self, metrics: List[PerformanceMetric], config_name: str) -> Dict:
        """Analyze performance metrics"""
        # Group by model
        model_metrics = {}
        for metric in metrics:
            if metric.model not in model_metrics:
                model_metrics[metric.model] = {
                    "latencies": [],
                    "success_count": 0,
                    "total_count": 0
                }
            
            model_metrics[metric.model]["latencies"].append(metric.latency_ms)
            model_metrics[metric.model]["total_count"] += 1
            if metric.success:
                model_metrics[metric.model]["success_count"] += 1
        
        # Calculate statistics for each model
        analysis = {
            "config": config_name,
            "total_requests": len(metrics),
            "duration": max(m.timestamp for m in metrics) - min(m.timestamp for m in metrics),
            "models": {}
        }
        
        for model, data in model_metrics.items():
            latencies = data["latencies"]
            percentiles = self.calculate_percentiles(latencies)
            
            analysis["models"][model] = {
                "request_count": data["total_count"],
                "success_rate": data["success_count"] / data["total_count"] if data["total_count"] > 0 else 0,
                "min_latency": min(latencies) if latencies else 0,
                "max_latency": max(latencies) if latencies else 0,
                "avg_latency": statistics.mean(latencies) if latencies else 0,
                "std_latency": statistics.stdev(latencies) if len(latencies) > 1 else 0,
                "percentiles": percentiles,
                "meets_target": self.check_latency_target(model, percentiles["p95"])
            }
        
        # Overall metrics
        all_latencies = [m.latency_ms for m in metrics]
        overall_percentiles = self.calculate_percentiles(all_latencies)
        
        analysis["overall"] = {
            "throughput": len(metrics) / analysis["duration"] if analysis["duration"] > 0 else 0,
            "success_rate": sum(1 for m in metrics if m.success) / len(metrics) if metrics else 0,
            "avg_latency": statistics.mean(all_latencies) if all_latencies else 0,
            "percentiles": overall_percentiles,
            "meets_hybrid_target": overall_percentiles["p95"] <= self.latency_targets["hybrid"]
        }
        
        return analysis
    
    def check_latency_target(self, model: str, p95_latency: float) -> bool:
        """Check if model meets its latency target"""
        # Map model names to target keys
        model_map = {
            "rules": "rules",
            "zero-shot": "zero_shot",
            "distilbert": "distilbert",
            "hybrid": "hybrid",
        }
        
        target_key = model_map.get(model.lower(), "hybrid")
        target = self.latency_targets.get(target_key, 100)
        
        return p95_latency <= target
    
    def plot_latency_distribution(self, metrics: List[PerformanceMetric], title: str) -> None:
        """Plot latency distribution histogram"""
        plt.figure(figsize=(12, 6))
        
        # Group by model
        model_latencies = {}
        for metric in metrics:
            if metric.model not in model_latencies:
                model_latencies[metric.model] = []
            model_latencies[metric.model].append(metric.latency_ms)
        
        # Plot histogram for each model
        for model, latencies in model_latencies.items():
            plt.hist(latencies, bins=50, alpha=0.5, label=model)
        
        plt.xlabel('Latency (ms)')
        plt.ylabel('Frequency')
        plt.title(title)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Save plot
        filename = f"latency_distribution_{title.replace(' ', '_').lower()}.png"
        plt.savefig(filename)
        print(f"Saved latency distribution plot to {filename}")
        plt.close()
    
    def plot_throughput_timeline(self, metrics: List[PerformanceMetric], title: str) -> None:
        """Plot throughput over time"""
        plt.figure(figsize=(12, 6))
        
        # Group requests by second
        start_time = min(m.timestamp for m in metrics)
        time_buckets = {}
        
        for metric in metrics:
            bucket = int(metric.timestamp - start_time)
            if bucket not in time_buckets:
                time_buckets[bucket] = 0
            time_buckets[bucket] += 1
        
        # Plot throughput
        times = sorted(time_buckets.keys())
        throughputs = [time_buckets[t] for t in times]
        
        plt.plot(times, throughputs, 'b-', linewidth=2)
        plt.xlabel('Time (seconds)')
        plt.ylabel('Requests per second')
        plt.title(title)
        plt.grid(True, alpha=0.3)
        
        # Add average line
        avg_throughput = statistics.mean(throughputs)
        plt.axhline(y=avg_throughput, color='r', linestyle='--', label=f'Average: {avg_throughput:.1f} req/s')
        plt.legend()
        
        # Save plot
        filename = f"throughput_timeline_{title.replace(' ', '_').lower()}.png"
        plt.savefig(filename)
        print(f"Saved throughput timeline plot to {filename}")
        plt.close()
    
    def run_all_benchmarks(self) -> Dict:
        """Run all benchmark configurations"""
        all_results = {}
        
        # Test each model mode separately
        model_modes = ["rules", "zero_shot", None]  # None = adaptive mode
        
        for config in self.benchmark_configs:
            config_results = {}
            
            for model_mode in model_modes:
                mode_name = model_mode or "adaptive"
                print(f"\n{'='*60}")
                print(f"Running {config.name} with {mode_name} mode")
                print(f"{'='*60}")
                
                # Warmup
                self.warmup(config.warmup_requests)
                
                # Run benchmark
                metrics = self.run_concurrent_benchmark(config, model_mode)
                
                # Analyze results
                analysis = self.analyze_metrics(metrics, f"{config.name}_{mode_name}")
                config_results[mode_name] = {
                    "metrics": metrics,
                    "analysis": analysis
                }
                
                # Generate plots
                self.plot_latency_distribution(metrics, f"{config.name} - {mode_name} mode")
                self.plot_throughput_timeline(metrics, f"{config.name} - {mode_name} mode")
                
                # Cool down between tests
                time.sleep(5)
            
            all_results[config.name] = config_results
        
        return all_results
    
    def generate_performance_report(self, results: Dict) -> str:
        """Generate comprehensive performance report"""
        report = []
        report.append("=" * 80)
        report.append("WAVE 8: PERFORMANCE BENCHMARK REPORT")
        report.append("=" * 80)
        report.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Performance targets reminder
        report.append("PERFORMANCE TARGETS:")
        report.append("  Rules-based: <50ms p95")
        report.append("  Zero-shot: <200ms p95")
        report.append("  DistilBERT: <100ms p95")
        report.append("  Hybrid (average): <75ms p95")
        report.append("")
        
        # Results by configuration
        for config_name, config_results in results.items():
            report.append(f"\n{'='*60}")
            report.append(f"CONFIGURATION: {config_name}")
            report.append(f"{'='*60}")
            
            for mode_name, mode_data in config_results.items():
                analysis = mode_data["analysis"]
                report.append(f"\nMode: {mode_name}")
                report.append(f"Total Requests: {analysis['total_requests']}")
                report.append(f"Duration: {analysis['duration']:.1f}s")
                report.append(f"Overall Throughput: {analysis['overall']['throughput']:.1f} req/s")
                report.append(f"Overall Success Rate: {analysis['overall']['success_rate']:.2%}")
                report.append(f"Overall P95 Latency: {analysis['overall']['percentiles']['p95']:.1f}ms")
                report.append(f"Meets Hybrid Target: {'✓' if analysis['overall']['meets_hybrid_target'] else '✗'}")
                
                # Per-model results
                if analysis["models"]:
                    report.append("\n  Model Performance:")
                    for model, model_stats in sorted(analysis["models"].items()):
                        report.append(f"    {model}:")
                        report.append(f"      Requests: {model_stats['request_count']}")
                        report.append(f"      Success Rate: {model_stats['success_rate']:.2%}")
                        report.append(f"      Avg Latency: {model_stats['avg_latency']:.1f}ms")
                        report.append(f"      P95 Latency: {model_stats['percentiles']['p95']:.1f}ms")
                        report.append(f"      P99 Latency: {model_stats['percentiles']['p99']:.1f}ms")
                        report.append(f"      Meets Target: {'✓' if model_stats['meets_target'] else '✗'}")
        
        # Summary
        report.append("\n" + "="*80)
        report.append("PERFORMANCE SUMMARY")
        report.append("="*80)
        
        # Check if targets are met across all configurations
        targets_met = {
            "rules": True,
            "zero_shot": True,
            "distilbert": True,
            "hybrid": True
        }
        
        for config_results in results.values():
            for mode_data in config_results.values():
                analysis = mode_data["analysis"]
                for model, stats in analysis["models"].items():
                    if not stats["meets_target"]:
                        model_key = model.lower().replace("-", "_")
                        if model_key in targets_met:
                            targets_met[model_key] = False
                
                if not analysis["overall"]["meets_hybrid_target"]:
                    targets_met["hybrid"] = False
        
        report.append("Target Achievement:")
        for target, met in targets_met.items():
            status = "PASS" if met else "FAIL"
            report.append(f"  {target}: {status}")
        
        # Recommendations
        report.append("\nRECOMMENDATIONS:")
        if not targets_met["rules"]:
            report.append("  - Rules-based classifier needs optimization for <50ms p95")
        if not targets_met["zero_shot"]:
            report.append("  - Zero-shot model may need caching or optimization")
        if not targets_met["distilbert"]:
            report.append("  - Consider ONNX optimization for DistilBERT model")
        if not targets_met["hybrid"]:
            report.append("  - Adaptive routing thresholds may need adjustment")
        
        if all(targets_met.values()):
            report.append("  - All performance targets met! Consider stress testing at higher loads")
        
        return "\n".join(report)

def main():
    """Run performance benchmarks"""
    benchmark = PerformanceBenchmark()
    
    print("Starting Wave 8 Performance Benchmarks...")
    print("This will take approximately 30-40 minutes to complete all tests")
    
    # Run all benchmarks
    results = benchmark.run_all_benchmarks()
    
    # Generate report
    report = benchmark.generate_performance_report(results)
    print("\n" + report)
    
    # Save detailed results
    with open("performance_benchmark_results.json", "w") as f:
        # Convert metrics to serializable format
        serializable_results = {}
        for config_name, config_results in results.items():
            serializable_results[config_name] = {}
            for mode_name, mode_data in config_results.items():
                serializable_results[config_name][mode_name] = {
                    "analysis": mode_data["analysis"],
                    "metrics_count": len(mode_data["metrics"])
                }
        
        json.dump(serializable_results, f, indent=2)
    
    print("\nDetailed results saved to performance_benchmark_results.json")
    print("Latency distribution plots saved as PNG files")
    print("Throughput timeline plots saved as PNG files")

if __name__ == "__main__":
    main()