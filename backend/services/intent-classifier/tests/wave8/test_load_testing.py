#!/usr/bin/env python3
"""
Wave 8: Load Testing Infrastructure
Tests system behavior under extreme load with 1000+ concurrent requests
"""

import json
import time
import statistics
import threading
import queue
from typing import Dict, List, Tuple
from dataclasses import dataclass
import requests
import matplotlib.pyplot as plt
from datetime import datetime
import psutil
import numpy as np

@dataclass
class LoadTestResult:
    request_id: int
    start_time: float
    end_time: float
    latency_ms: float
    status_code: int
    success: bool
    error: str
    model_used: str
    thread_id: int

@dataclass
class SystemMetrics:
    timestamp: float
    cpu_percent: float
    memory_percent: float
    active_connections: int

class LoadTester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.results_queue = queue.Queue()
        self.system_metrics = []
        self.monitoring = False
        self.request_counter = 0
        self.request_lock = threading.Lock()
        
        # Test scenarios
        self.load_scenarios = [
            {
                "name": "Gradual Ramp-up",
                "description": "Gradually increase load from 10 to 1000 concurrent users",
                "phases": [
                    {"duration": 30, "concurrent_users": 10},
                    {"duration": 30, "concurrent_users": 50},
                    {"duration": 30, "concurrent_users": 100},
                    {"duration": 30, "concurrent_users": 250},
                    {"duration": 30, "concurrent_users": 500},
                    {"duration": 60, "concurrent_users": 1000},
                ]
            },
            {
                "name": "Spike Test",
                "description": "Sudden spike from 50 to 1000 users",
                "phases": [
                    {"duration": 30, "concurrent_users": 50},
                    {"duration": 60, "concurrent_users": 1000},
                    {"duration": 30, "concurrent_users": 50},
                ]
            },
            {
                "name": "Sustained Load",
                "description": "Sustained 1000 concurrent users for 5 minutes",
                "phases": [
                    {"duration": 300, "concurrent_users": 1000},
                ]
            },
            {
                "name": "Stress Test",
                "description": "Push system to breaking point",
                "phases": [
                    {"duration": 30, "concurrent_users": 500},
                    {"duration": 30, "concurrent_users": 1000},
                    {"duration": 30, "concurrent_users": 1500},
                    {"duration": 30, "concurrent_users": 2000},
                ]
            }
        ]
        
        # Test data
        self.test_prompts = [
            # Simple prompts (should use rules)
            "What is AI?",
            "How does a computer work?",
            "Explain machine learning",
            "What is Python?",
            "How to code?",
            
            # Medium complexity
            "Write a Python function to sort a list",
            "Explain database normalization",
            "How to optimize SQL queries?",
            "What is microservices architecture?",
            "Describe REST API design",
            
            # Complex prompts
            "Explain the implications of quantum computing on cryptography",
            "Design a distributed system for real-time analytics",
            "Compare different consensus algorithms in blockchain",
            "Analyze the computational complexity of neural networks",
            "Discuss the ethics of artificial general intelligence",
            
            # Ambiguous prompts (should trigger zero-shot)
            "Help me with this",
            "I need assistance",
            "Can you explain?",
            "Tell me more",
            "What about it?",
        ]
    
    def get_next_request_id(self) -> int:
        """Get thread-safe request ID"""
        with self.request_lock:
            self.request_counter += 1
            return self.request_counter
    
    def make_request(self, prompt: str, thread_id: int) -> LoadTestResult:
        """Make a single request and record results"""
        request_id = self.get_next_request_id()
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/intents/classify",
                json={"text": prompt, "user_id": f"load_test_{request_id}"},
                timeout=30
            )
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                model_used = data.get("model_used", "unknown")
                success = True
                error = ""
            else:
                model_used = "error"
                success = False
                error = f"HTTP {response.status_code}"
            
            return LoadTestResult(
                request_id=request_id,
                start_time=start_time,
                end_time=end_time,
                latency_ms=latency_ms,
                status_code=response.status_code,
                success=success,
                error=error,
                model_used=model_used,
                thread_id=thread_id
            )
            
        except requests.exceptions.Timeout:
            end_time = time.time()
            return LoadTestResult(
                request_id=request_id,
                start_time=start_time,
                end_time=end_time,
                latency_ms=(end_time - start_time) * 1000,
                status_code=0,
                success=False,
                error="Timeout",
                model_used="timeout",
                thread_id=thread_id
            )
            
        except Exception as e:
            end_time = time.time()
            return LoadTestResult(
                request_id=request_id,
                start_time=start_time,
                end_time=end_time,
                latency_ms=(end_time - start_time) * 1000,
                status_code=0,
                success=False,
                error=str(e),
                model_used="error",
                thread_id=thread_id
            )
    
    def worker_thread(self, thread_id: int, stop_event: threading.Event, request_delay: float):
        """Worker thread that continuously makes requests"""
        prompt_index = thread_id % len(self.test_prompts)
        
        while not stop_event.is_set():
            prompt = self.test_prompts[prompt_index]
            result = self.make_request(prompt, thread_id)
            self.results_queue.put(result)
            
            # Rotate through prompts
            prompt_index = (prompt_index + 1) % len(self.test_prompts)
            
            # Small delay between requests
            time.sleep(request_delay)
    
    def monitor_system_resources(self, stop_event: threading.Event):
        """Monitor system CPU and memory usage"""
        while not stop_event.is_set():
            try:
                # Get active connections count
                response = requests.get(f"{self.base_url}/metrics")
                metrics_text = response.text
                active_connections = 0
                for line in metrics_text.split('\n'):
                    if 'http_requests_active' in line and not line.startswith('#'):
                        active_connections = int(float(line.split()[-1]))
                        break
                
                metric = SystemMetrics(
                    timestamp=time.time(),
                    cpu_percent=psutil.cpu_percent(interval=0.1),
                    memory_percent=psutil.virtual_memory().percent,
                    active_connections=active_connections
                )
                self.system_metrics.append(metric)
                
            except Exception:
                # Continue monitoring even if metrics fail
                pass
            
            time.sleep(1)
    
    def run_load_phase(self, concurrent_users: int, duration: int, phase_name: str) -> List[LoadTestResult]:
        """Run a single load test phase"""
        print(f"\n{'='*60}")
        print(f"Phase: {phase_name}")
        print(f"Concurrent Users: {concurrent_users}")
        print(f"Duration: {duration}s")
        print(f"{'='*60}")
        
        phase_results = []
        stop_event = threading.Event()
        threads = []
        
        # Calculate request delay to achieve target RPS
        # Assuming each user makes ~1 request per second
        request_delay = 1.0
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_system_resources, args=(stop_event,))
        monitor_thread.start()
        
        # Start worker threads
        print(f"Starting {concurrent_users} worker threads...")
        for i in range(concurrent_users):
            thread = threading.Thread(
                target=self.worker_thread,
                args=(i, stop_event, request_delay)
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)
            
            # Stagger thread starts to avoid thundering herd
            if i < 100:
                time.sleep(0.01)
            elif i % 100 == 0:
                time.sleep(0.1)
        
        # Run for specified duration
        start_time = time.time()
        last_report_time = start_time
        
        while time.time() - start_time < duration:
            current_time = time.time()
            
            # Collect results
            while not self.results_queue.empty():
                try:
                    result = self.results_queue.get_nowait()
                    phase_results.append(result)
                except queue.Empty:
                    break
            
            # Report progress every 5 seconds
            if current_time - last_report_time >= 5:
                elapsed = current_time - start_time
                completed = len(phase_results)
                rps = completed / elapsed if elapsed > 0 else 0
                success_count = sum(1 for r in phase_results if r.success)
                success_rate = success_count / completed if completed > 0 else 0
                
                print(f"Progress: {elapsed:.0f}s | Requests: {completed} | "
                      f"RPS: {rps:.1f} | Success: {success_rate:.1%}")
                last_report_time = current_time
            
            time.sleep(0.1)
        
        # Stop threads
        print("Stopping worker threads...")
        stop_event.set()
        
        # Collect remaining results
        time.sleep(2)
        while not self.results_queue.empty():
            try:
                result = self.results_queue.get_nowait()
                phase_results.append(result)
            except queue.Empty:
                break
        
        # Wait for threads to finish
        for thread in threads:
            thread.join(timeout=1)
        
        monitor_thread.join(timeout=1)
        
        # Phase summary
        total_requests = len(phase_results)
        successful_requests = sum(1 for r in phase_results if r.success)
        failed_requests = total_requests - successful_requests
        
        if phase_results:
            latencies = [r.latency_ms for r in phase_results if r.success]
            if latencies:
                avg_latency = statistics.mean(latencies)
                p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
                p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]
            else:
                avg_latency = p95_latency = p99_latency = 0
        else:
            avg_latency = p95_latency = p99_latency = 0
        
        print(f"\nPhase Complete:")
        print(f"  Total Requests: {total_requests}")
        print(f"  Successful: {successful_requests} ({successful_requests/total_requests*100:.1f}%)")
        print(f"  Failed: {failed_requests}")
        print(f"  Avg Latency: {avg_latency:.1f}ms")
        print(f"  P95 Latency: {p95_latency:.1f}ms")
        print(f"  P99 Latency: {p99_latency:.1f}ms")
        
        return phase_results
    
    def run_load_scenario(self, scenario: Dict) -> Dict:
        """Run a complete load test scenario"""
        print(f"\n{'#'*80}")
        print(f"Running Load Scenario: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"{'#'*80}")
        
        scenario_results = {
            "name": scenario["name"],
            "description": scenario["description"],
            "phases": [],
            "overall_metrics": {},
            "system_metrics": []
        }
        
        all_results = []
        
        # Run each phase
        for i, phase in enumerate(scenario["phases"]):
            phase_name = f"Phase {i+1}: {phase['concurrent_users']} users"
            phase_results = self.run_load_phase(
                phase["concurrent_users"],
                phase["duration"],
                phase_name
            )
            
            all_results.extend(phase_results)
            
            # Analyze phase results
            phase_analysis = self.analyze_phase_results(phase_results)
            phase_analysis["concurrent_users"] = phase["concurrent_users"]
            phase_analysis["duration"] = phase["duration"]
            scenario_results["phases"].append(phase_analysis)
            
            # Cool down between phases
            if i < len(scenario["phases"]) - 1:
                print("\nCooling down for 10 seconds...")
                time.sleep(10)
        
        # Overall analysis
        scenario_results["overall_metrics"] = self.analyze_phase_results(all_results)
        scenario_results["system_metrics"] = self.system_metrics.copy()
        self.system_metrics.clear()  # Reset for next scenario
        
        return scenario_results
    
    def analyze_phase_results(self, results: List[LoadTestResult]) -> Dict:
        """Analyze results from a load test phase"""
        if not results:
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "success_rate": 0,
                "error_breakdown": {},
                "latency_stats": {},
                "throughput": 0,
                "model_distribution": {}
            }
        
        # Basic counts
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        
        # Error breakdown
        error_breakdown = {}
        for result in results:
            if not result.success:
                error = result.error or "Unknown"
                error_breakdown[error] = error_breakdown.get(error, 0) + 1
        
        # Latency statistics (only for successful requests)
        success_latencies = [r.latency_ms for r in results if r.success]
        if success_latencies:
            latency_stats = {
                "min": min(success_latencies),
                "max": max(success_latencies),
                "mean": statistics.mean(success_latencies),
                "median": statistics.median(success_latencies),
                "p50": sorted(success_latencies)[int(len(success_latencies) * 0.50)],
                "p90": sorted(success_latencies)[int(len(success_latencies) * 0.90)],
                "p95": sorted(success_latencies)[int(len(success_latencies) * 0.95)],
                "p99": sorted(success_latencies)[int(len(success_latencies) * 0.99)],
            }
        else:
            latency_stats = {
                "min": 0, "max": 0, "mean": 0, "median": 0,
                "p50": 0, "p90": 0, "p95": 0, "p99": 0
            }
        
        # Throughput calculation
        if results:
            duration = max(r.end_time for r in results) - min(r.start_time for r in results)
            throughput = len(results) / duration if duration > 0 else 0
        else:
            throughput = 0
        
        # Model distribution
        model_distribution = {}
        for result in results:
            if result.success:
                model = result.model_used
                model_distribution[model] = model_distribution.get(model, 0) + 1
        
        return {
            "total_requests": total,
            "successful_requests": successful,
            "failed_requests": failed,
            "success_rate": successful / total if total > 0 else 0,
            "error_breakdown": error_breakdown,
            "latency_stats": latency_stats,
            "throughput": throughput,
            "model_distribution": model_distribution
        }
    
    def plot_load_test_results(self, scenario_results: Dict) -> None:
        """Generate plots for load test results"""
        scenario_name = scenario_results["name"].replace(" ", "_").lower()
        
        # 1. Success Rate Over Time
        plt.figure(figsize=(12, 6))
        phases = scenario_results["phases"]
        x = list(range(len(phases)))
        success_rates = [p["success_rate"] * 100 for p in phases]
        concurrent_users = [p["concurrent_users"] for p in phases]
        
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        color = 'tab:green'
        ax1.set_xlabel('Phase')
        ax1.set_ylabel('Success Rate (%)', color=color)
        ax1.plot(x, success_rates, 'o-', color=color, linewidth=2, markersize=8)
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.set_ylim(0, 105)
        ax1.grid(True, alpha=0.3)
        
        ax2 = ax1.twinx()
        color = 'tab:blue'
        ax2.set_ylabel('Concurrent Users', color=color)
        ax2.plot(x, concurrent_users, 's--', color=color, linewidth=2, markersize=8)
        ax2.tick_params(axis='y', labelcolor=color)
        
        plt.title(f'Success Rate vs Load - {scenario_results["name"]}')
        fig.tight_layout()
        plt.savefig(f'{scenario_name}_success_rate.png')
        plt.close()
        
        # 2. Latency Percentiles
        plt.figure(figsize=(12, 6))
        
        p50_latencies = [p["latency_stats"]["p50"] for p in phases]
        p95_latencies = [p["latency_stats"]["p95"] for p in phases]
        p99_latencies = [p["latency_stats"]["p99"] for p in phases]
        
        plt.plot(x, p50_latencies, 'g-', label='P50', linewidth=2)
        plt.plot(x, p95_latencies, 'b-', label='P95', linewidth=2)
        plt.plot(x, p99_latencies, 'r-', label='P99', linewidth=2)
        
        plt.xlabel('Phase')
        plt.ylabel('Latency (ms)')
        plt.title(f'Latency Percentiles - {scenario_results["name"]}')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(f'{scenario_name}_latency_percentiles.png')
        plt.close()
        
        # 3. System Resources
        if scenario_results["system_metrics"]:
            plt.figure(figsize=(12, 6))
            
            metrics = scenario_results["system_metrics"]
            timestamps = [m.timestamp for m in metrics]
            start_time = min(timestamps)
            relative_times = [(t - start_time) for t in timestamps]
            
            cpu_percents = [m.cpu_percent for m in metrics]
            memory_percents = [m.memory_percent for m in metrics]
            
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            color = 'tab:red'
            ax1.set_xlabel('Time (seconds)')
            ax1.set_ylabel('CPU Usage (%)', color=color)
            ax1.plot(relative_times, cpu_percents, color=color, linewidth=2)
            ax1.tick_params(axis='y', labelcolor=color)
            ax1.set_ylim(0, 100)
            
            ax2 = ax1.twinx()
            color = 'tab:blue'
            ax2.set_ylabel('Memory Usage (%)', color=color)
            ax2.plot(relative_times, memory_percents, color=color, linewidth=2)
            ax2.tick_params(axis='y', labelcolor=color)
            ax2.set_ylim(0, 100)
            
            plt.title(f'System Resource Usage - {scenario_results["name"]}')
            fig.tight_layout()
            plt.savefig(f'{scenario_name}_system_resources.png')
            plt.close()
        
        print(f"Saved plots for {scenario_results['name']}")
    
    def generate_load_test_report(self, all_scenarios: List[Dict]) -> str:
        """Generate comprehensive load test report"""
        report = []
        report.append("=" * 80)
        report.append("WAVE 8: LOAD TESTING REPORT")
        report.append("=" * 80)
        report.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Target metrics
        report.append("LOAD TESTING TARGETS:")
        report.append("  - Handle 1000 concurrent requests")
        report.append("  - Maintain >99% success rate under normal load")
        report.append("  - P95 latency <200ms under 1000 concurrent users")
        report.append("  - Graceful degradation under extreme load")
        report.append("")
        
        # Results by scenario
        for scenario in all_scenarios:
            report.append(f"\n{'='*60}")
            report.append(f"SCENARIO: {scenario['name']}")
            report.append(f"Description: {scenario['description']}")
            report.append(f"{'='*60}")
            
            # Overall metrics
            overall = scenario["overall_metrics"]
            report.append(f"\nOverall Results:")
            report.append(f"  Total Requests: {overall['total_requests']:,}")
            report.append(f"  Success Rate: {overall['success_rate']:.2%}")
            report.append(f"  Average Throughput: {overall['throughput']:.1f} req/s")
            report.append(f"  P95 Latency: {overall['latency_stats']['p95']:.1f}ms")
            report.append(f"  P99 Latency: {overall['latency_stats']['p99']:.1f}ms")
            
            # Error breakdown if any
            if overall["error_breakdown"]:
                report.append(f"\n  Error Breakdown:")
                for error, count in sorted(overall["error_breakdown"].items()):
                    percentage = count / overall["failed_requests"] * 100
                    report.append(f"    {error}: {count} ({percentage:.1f}%)")
            
            # Model distribution
            if overall["model_distribution"]:
                report.append(f"\n  Model Distribution:")
                total_successful = overall["successful_requests"]
                for model, count in sorted(overall["model_distribution"].items()):
                    percentage = count / total_successful * 100 if total_successful > 0 else 0
                    report.append(f"    {model}: {count} ({percentage:.1f}%)")
            
            # Phase-by-phase breakdown
            report.append(f"\n  Phase Results:")
            for i, phase in enumerate(scenario["phases"]):
                report.append(f"\n    Phase {i+1} ({phase['concurrent_users']} users, {phase['duration']}s):")
                report.append(f"      Success Rate: {phase['success_rate']:.2%}")
                report.append(f"      Throughput: {phase['throughput']:.1f} req/s")
                report.append(f"      P95 Latency: {phase['latency_stats']['p95']:.1f}ms")
                report.append(f"      Failed Requests: {phase['failed_requests']}")
        
        # Summary and recommendations
        report.append("\n" + "="*80)
        report.append("LOAD TESTING SUMMARY")
        report.append("="*80)
        
        # Check if targets are met
        targets_met = {
            "1000_concurrent": False,
            "99_percent_success": False,
            "p95_under_200ms": False,
            "graceful_degradation": False
        }
        
        for scenario in all_scenarios:
            # Check 1000 concurrent users handling
            for phase in scenario["phases"]:
                if phase["concurrent_users"] >= 1000 and phase["success_rate"] > 0.9:
                    targets_met["1000_concurrent"] = True
                if phase["concurrent_users"] <= 1000 and phase["success_rate"] >= 0.99:
                    targets_met["99_percent_success"] = True
                if phase["concurrent_users"] == 1000 and phase["latency_stats"]["p95"] < 200:
                    targets_met["p95_under_200ms"] = True
            
            # Check graceful degradation (success rate stays >80% even under extreme load)
            if scenario["name"] == "Stress Test":
                min_success_rate = min(p["success_rate"] for p in scenario["phases"])
                if min_success_rate > 0.8:
                    targets_met["graceful_degradation"] = True
        
        report.append("\nTarget Achievement:")
        report.append(f"  ✓ Handle 1000 concurrent users: {'PASS' if targets_met['1000_concurrent'] else 'FAIL'}")
        report.append(f"  ✓ 99% success rate (normal load): {'PASS' if targets_met['99_percent_success'] else 'FAIL'}")
        report.append(f"  ✓ P95 <200ms (1000 users): {'PASS' if targets_met['p95_under_200ms'] else 'FAIL'}")
        report.append(f"  ✓ Graceful degradation: {'PASS' if targets_met['graceful_degradation'] else 'FAIL'}")
        
        # Recommendations
        report.append("\nRECOMMENDATIONS:")
        if not targets_met["1000_concurrent"]:
            report.append("  - Scale up service instances or optimize request handling")
        if not targets_met["99_percent_success"]:
            report.append("  - Investigate timeout settings and connection pooling")
        if not targets_met["p95_under_200ms"]:
            report.append("  - Enable more aggressive caching or optimize model loading")
        if not targets_met["graceful_degradation"]:
            report.append("  - Implement request queuing or rate limiting")
        
        if all(targets_met.values()):
            report.append("  - All load testing targets met! Consider testing at even higher loads")
            report.append("  - Implement auto-scaling based on load patterns observed")
        
        return "\n".join(report)

def main():
    """Run load tests"""
    tester = LoadTester()
    
    print("Starting Wave 8 Load Testing...")
    print("WARNING: This will generate significant load on the service")
    print("Ensure the service is running and properly configured")
    print("")
    
    all_scenario_results = []
    
    # Run each scenario
    for scenario in tester.load_scenarios:
        scenario_results = tester.run_load_scenario(scenario)
        all_scenario_results.append(scenario_results)
        
        # Generate plots
        tester.plot_load_test_results(scenario_results)
        
        # Cool down between scenarios
        print("\nCooling down for 30 seconds before next scenario...")
        time.sleep(30)
    
    # Generate report
    report = tester.generate_load_test_report(all_scenario_results)
    print("\n" + report)
    
    # Save detailed results
    with open("load_test_results.json", "w") as f:
        # Convert to serializable format
        serializable_results = []
        for scenario in all_scenario_results:
            serializable_scenario = {
                "name": scenario["name"],
                "description": scenario["description"],
                "phases": scenario["phases"],
                "overall_metrics": scenario["overall_metrics"],
                "system_metrics_count": len(scenario["system_metrics"])
            }
            serializable_results.append(serializable_scenario)
        
        json.dump(serializable_results, f, indent=2)
    
    print("\nDetailed results saved to load_test_results.json")
    print("Load test plots saved as PNG files")

if __name__ == "__main__":
    main()