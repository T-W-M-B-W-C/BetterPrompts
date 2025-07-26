#!/usr/bin/env python3
"""
Wave 8: Failure Mode Testing
Tests system behavior under various failure conditions and recovery scenarios
"""

import json
import time
import subprocess
import signal
from typing import Dict, List, Tuple
from dataclasses import dataclass
import requests
import docker
from datetime import datetime

@dataclass
class FailureTestResult:
    test_name: str
    failure_type: str
    description: str
    pre_failure_state: Dict
    during_failure_state: Dict
    post_recovery_state: Dict
    degradation_handled: bool
    recovery_time: float
    data_loss: bool
    errors_observed: List[str]
    recommendations: List[str]

class FailureModeTester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.docker_client = docker.from_env()
        self.test_results = []
        
        # Define failure scenarios
        self.failure_scenarios = [
            {
                "name": "Redis Cache Failure",
                "type": "dependency_failure",
                "description": "Simulate Redis cache becoming unavailable",
                "setup": self.stop_redis,
                "teardown": self.start_redis,
                "expected_behavior": "Service continues with degraded performance, no caching"
            },
            {
                "name": "Database Connection Loss",
                "type": "dependency_failure", 
                "description": "Simulate PostgreSQL becoming unavailable",
                "setup": self.stop_postgres,
                "teardown": self.start_postgres,
                "expected_behavior": "Read-only mode, feedback endpoints fail gracefully"
            },
            {
                "name": "TorchServe Unavailable",
                "type": "dependency_failure",
                "description": "Simulate TorchServe model server failure",
                "setup": self.stop_torchserve,
                "teardown": self.start_torchserve,
                "expected_behavior": "Fallback to zero-shot and rules-based models"
            },
            {
                "name": "Memory Pressure",
                "type": "resource_exhaustion",
                "description": "Simulate high memory usage scenario",
                "setup": self.simulate_memory_pressure,
                "teardown": self.release_memory_pressure,
                "expected_behavior": "Graceful degradation, possible model unloading"
            },
            {
                "name": "Model File Corruption",
                "type": "data_corruption",
                "description": "Simulate corrupted model file",
                "setup": self.corrupt_model_file,
                "teardown": self.restore_model_file,
                "expected_behavior": "Model fails to load, fallback to other models"
            },
            {
                "name": "Network Partition",
                "type": "network_failure",
                "description": "Simulate network issues between services",
                "setup": self.simulate_network_partition,
                "teardown": self.restore_network,
                "expected_behavior": "Timeout handling, circuit breaker activation"
            },
            {
                "name": "Cascading Service Failure",
                "type": "cascade_failure",
                "description": "Multiple services fail in sequence",
                "setup": self.simulate_cascade_failure,
                "teardown": self.restore_all_services,
                "expected_behavior": "Gradual degradation, core functionality preserved"
            },
            {
                "name": "Rate Limit Exhaustion",
                "type": "resource_exhaustion",
                "description": "Exhaust rate limits on external APIs",
                "setup": self.exhaust_rate_limits,
                "teardown": self.reset_rate_limits,
                "expected_behavior": "Queuing, backpressure, graceful rejection"
            }
        ]
        
        # Test prompts
        self.test_prompts = [
            "What is machine learning?",
            "Help me debug this code",
            "Write a story about AI",
            "Translate hello to Spanish",
            "Explain quantum computing"
        ]
    
    def get_service_state(self) -> Dict:
        """Get current state of the service"""
        state = {
            "health": {},
            "models": {},
            "dependencies": {},
            "metrics": {},
            "feature_flags": {}
        }
        
        try:
            # Health check
            health_response = requests.get(f"{self.base_url}/health/ready", timeout=5)
            state["health"]["ready"] = health_response.status_code == 200
            state["health"]["details"] = health_response.json() if health_response.status_code == 200 else {}
            
            # Model health
            models_response = requests.get(f"{self.base_url}/health/models", timeout=5)
            if models_response.status_code == 200:
                state["models"] = models_response.json()
            
            # Dependencies health
            deps_response = requests.get(f"{self.base_url}/health/dependencies", timeout=5)
            if deps_response.status_code == 200:
                state["dependencies"] = deps_response.json()
            
            # Feature flags
            flags_response = requests.get(f"{self.base_url}/api/v1/feature-flags", timeout=5)
            if flags_response.status_code == 200:
                state["feature_flags"] = flags_response.json()
            
            # Routing stats
            routing_response = requests.get(f"{self.base_url}/api/v1/intents/routing/stats", timeout=5)
            if routing_response.status_code == 200:
                state["metrics"]["routing"] = routing_response.json()
                
        except Exception as e:
            state["health"]["error"] = str(e)
            state["health"]["ready"] = False
        
        return state
    
    def test_classification(self, expected_to_fail: bool = False) -> Tuple[bool, List[str], Dict]:
        """Test classification functionality"""
        errors = []
        results = {"total": len(self.test_prompts), "successful": 0, "models_used": {}}
        
        for prompt in self.test_prompts:
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/intents/classify",
                    json={"text": prompt, "user_id": "failure_test"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results["successful"] += 1
                    model = data.get("model_used", "unknown")
                    results["models_used"][model] = results["models_used"].get(model, 0) + 1
                else:
                    errors.append(f"HTTP {response.status_code} for '{prompt}'")
                    
            except requests.exceptions.Timeout:
                errors.append(f"Timeout for '{prompt}'")
            except Exception as e:
                errors.append(f"Error for '{prompt}': {str(e)}")
        
        success = results["successful"] == results["total"] if not expected_to_fail else results["successful"] > 0
        return success, errors, results
    
    # Failure simulation methods
    def stop_redis(self):
        """Stop Redis container"""
        try:
            redis_container = self.docker_client.containers.get("redis")
            redis_container.stop()
            print("Redis stopped")
            time.sleep(2)
        except Exception as e:
            print(f"Failed to stop Redis: {e}")
    
    def start_redis(self):
        """Start Redis container"""
        try:
            redis_container = self.docker_client.containers.get("redis")
            redis_container.start()
            print("Redis started")
            time.sleep(5)
        except Exception as e:
            print(f"Failed to start Redis: {e}")
    
    def stop_postgres(self):
        """Stop PostgreSQL container"""
        try:
            postgres_container = self.docker_client.containers.get("postgres")
            postgres_container.stop()
            print("PostgreSQL stopped")
            time.sleep(2)
        except Exception as e:
            print(f"Failed to stop PostgreSQL: {e}")
    
    def start_postgres(self):
        """Start PostgreSQL container"""
        try:
            postgres_container = self.docker_client.containers.get("postgres")
            postgres_container.start()
            print("PostgreSQL started")
            time.sleep(10)
        except Exception as e:
            print(f"Failed to start PostgreSQL: {e}")
    
    def stop_torchserve(self):
        """Stop TorchServe container"""
        try:
            torchserve_container = self.docker_client.containers.get("torchserve")
            torchserve_container.stop()
            print("TorchServe stopped")
            time.sleep(2)
        except Exception:
            print("TorchServe not running or not found")
    
    def start_torchserve(self):
        """Start TorchServe container"""
        try:
            torchserve_container = self.docker_client.containers.get("torchserve")
            torchserve_container.start()
            print("TorchServe started")
            time.sleep(10)
        except Exception:
            print("TorchServe not found")
    
    def simulate_memory_pressure(self):
        """Simulate memory pressure"""
        # This is a placeholder - in real testing, you might use stress-ng or similar
        print("Simulating memory pressure (placeholder)")
    
    def release_memory_pressure(self):
        """Release memory pressure"""
        print("Releasing memory pressure (placeholder)")
    
    def corrupt_model_file(self):
        """Temporarily corrupt a model file"""
        # This would backup and corrupt a model file
        print("Simulating model file corruption (placeholder)")
    
    def restore_model_file(self):
        """Restore corrupted model file"""
        print("Restoring model file (placeholder)")
    
    def simulate_network_partition(self):
        """Simulate network partition"""
        # Use iptables or similar to block network traffic
        print("Simulating network partition (placeholder)")
    
    def restore_network(self):
        """Restore network connectivity"""
        print("Restoring network (placeholder)")
    
    def simulate_cascade_failure(self):
        """Simulate cascading failure"""
        self.stop_redis()
        time.sleep(2)
        self.stop_postgres()
        print("Cascading failure simulated")
    
    def restore_all_services(self):
        """Restore all services"""
        self.start_postgres()
        time.sleep(5)
        self.start_redis()
        print("All services restored")
    
    def exhaust_rate_limits(self):
        """Exhaust rate limits"""
        print("Simulating rate limit exhaustion (placeholder)")
    
    def reset_rate_limits(self):
        """Reset rate limits"""
        print("Resetting rate limits (placeholder)")
    
    def run_failure_scenario(self, scenario: Dict) -> FailureTestResult:
        """Run a single failure scenario"""
        print(f"\n{'='*60}")
        print(f"Running Failure Scenario: {scenario['name']}")
        print(f"Type: {scenario['type']}")
        print(f"Description: {scenario['description']}")
        print(f"Expected: {scenario['expected_behavior']}")
        print(f"{'='*60}")
        
        # Get pre-failure state
        print("\n1. Capturing pre-failure state...")
        pre_failure_state = self.get_service_state()
        pre_test_success, pre_errors, pre_results = self.test_classification()
        print(f"   Pre-failure test: {'PASS' if pre_test_success else 'FAIL'}")
        
        # Induce failure
        print(f"\n2. Inducing failure: {scenario['name']}...")
        failure_start_time = time.time()
        scenario["setup"]()
        
        # Test during failure
        print("\n3. Testing during failure...")
        time.sleep(2)  # Allow failure to propagate
        during_failure_state = self.get_service_state()
        during_test_success, during_errors, during_results = self.test_classification(expected_to_fail=True)
        print(f"   During failure test: {during_results['successful']}/{during_results['total']} successful")
        print(f"   Models used: {during_results['models_used']}")
        
        # Check degradation handling
        degradation_handled = during_results["successful"] > 0
        
        # Recover from failure
        print(f"\n4. Recovering from failure...")
        recovery_start_time = time.time()
        scenario["teardown"]()
        
        # Wait for recovery
        print("   Waiting for service recovery...")
        max_recovery_time = 30
        recovered = False
        
        for i in range(max_recovery_time):
            time.sleep(1)
            try:
                health_check = requests.get(f"{self.base_url}/health/ready", timeout=2)
                if health_check.status_code == 200:
                    recovered = True
                    break
            except:
                pass
            
            if i % 5 == 0:
                print(f"   Recovery progress: {i}s elapsed...")
        
        recovery_time = time.time() - recovery_start_time
        
        # Test post-recovery
        print("\n5. Testing post-recovery...")
        post_recovery_state = self.get_service_state()
        post_test_success, post_errors, post_results = self.test_classification()
        print(f"   Post-recovery test: {'PASS' if post_test_success else 'FAIL'}")
        
        # Check for data loss
        data_loss = False
        if "routing" in pre_failure_state["metrics"] and "routing" in post_recovery_state["metrics"]:
            # Simple check - in reality would be more comprehensive
            pre_count = pre_failure_state["metrics"]["routing"].get("total_requests", 0)
            post_count = post_recovery_state["metrics"]["routing"].get("total_requests", 0)
            data_loss = post_count < pre_count
        
        # Generate recommendations
        recommendations = []
        if not degradation_handled:
            recommendations.append("Implement better fallback mechanisms")
        if recovery_time > 10:
            recommendations.append(f"Improve recovery time (current: {recovery_time:.1f}s)")
        if during_errors:
            recommendations.append("Improve error handling and user feedback")
        if data_loss:
            recommendations.append("Implement persistent state management")
        
        # Create result
        result = FailureTestResult(
            test_name=scenario["name"],
            failure_type=scenario["type"],
            description=scenario["description"],
            pre_failure_state=pre_failure_state,
            during_failure_state=during_failure_state,
            post_recovery_state=post_recovery_state,
            degradation_handled=degradation_handled,
            recovery_time=recovery_time,
            data_loss=data_loss,
            errors_observed=during_errors,
            recommendations=recommendations
        )
        
        # Summary
        print(f"\n6. Failure Test Summary:")
        print(f"   Degradation Handled: {'YES' if degradation_handled else 'NO'}")
        print(f"   Recovery Time: {recovery_time:.1f}s")
        print(f"   Data Loss: {'YES' if data_loss else 'NO'}")
        print(f"   Recovered Successfully: {'YES' if recovered else 'NO'}")
        
        return result
    
    def generate_failure_report(self, results: List[FailureTestResult]) -> str:
        """Generate comprehensive failure mode test report"""
        report = []
        report.append("=" * 80)
        report.append("WAVE 8: FAILURE MODE TESTING REPORT")
        report.append("=" * 80)
        report.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary statistics
        total_tests = len(results)
        degradation_handled = sum(1 for r in results if r.degradation_handled)
        avg_recovery_time = sum(r.recovery_time for r in results) / total_tests if total_tests > 0 else 0
        data_losses = sum(1 for r in results if r.data_loss)
        
        report.append("SUMMARY:")
        report.append(f"  Total Failure Scenarios: {total_tests}")
        report.append(f"  Graceful Degradation: {degradation_handled}/{total_tests} ({degradation_handled/total_tests*100:.1f}%)")
        report.append(f"  Average Recovery Time: {avg_recovery_time:.1f}s")
        report.append(f"  Data Loss Incidents: {data_losses}")
        report.append("")
        
        # Detailed results
        report.append("DETAILED RESULTS:")
        for result in results:
            report.append(f"\n{'='*60}")
            report.append(f"Scenario: {result.test_name}")
            report.append(f"Type: {result.failure_type}")
            report.append(f"{'='*60}")
            
            report.append(f"\nDescription: {result.description}")
            report.append(f"Degradation Handled: {'YES' if result.degradation_handled else 'NO'}")
            report.append(f"Recovery Time: {result.recovery_time:.1f}s")
            report.append(f"Data Loss: {'YES' if result.data_loss else 'NO'}")
            
            # Model usage during failure
            if "routing" in result.during_failure_state.get("metrics", {}):
                routing_stats = result.during_failure_state["metrics"]["routing"]
                if "model_selection" in routing_stats:
                    report.append("\nModel Usage During Failure:")
                    for model, stats in routing_stats["model_selection"].items():
                        report.append(f"  {model}: {stats.get('count', 0)} requests")
            
            # Errors observed
            if result.errors_observed:
                report.append("\nErrors Observed:")
                for error in result.errors_observed[:5]:  # Show first 5 errors
                    report.append(f"  - {error}")
                if len(result.errors_observed) > 5:
                    report.append(f"  ... and {len(result.errors_observed)-5} more errors")
            
            # Health status during failure
            if result.during_failure_state.get("health", {}).get("details"):
                health = result.during_failure_state["health"]["details"]
                report.append("\nHealth Status During Failure:")
                report.append(f"  Overall: {health.get('status', 'unknown')}")
                if "checks" in health:
                    for check_name, check_status in health["checks"].items():
                        report.append(f"  {check_name}: {check_status}")
            
            # Recommendations
            if result.recommendations:
                report.append("\nRecommendations:")
                for rec in result.recommendations:
                    report.append(f"  - {rec}")
        
        # Overall recommendations
        report.append("\n" + "="*80)
        report.append("OVERALL RECOMMENDATIONS")
        report.append("="*80)
        
        # Analyze common issues
        all_recommendations = []
        for result in results:
            all_recommendations.extend(result.recommendations)
        
        # Count recommendation frequencies
        rec_counts = {}
        for rec in all_recommendations:
            rec_counts[rec] = rec_counts.get(rec, 0) + 1
        
        # Sort by frequency
        sorted_recs = sorted(rec_counts.items(), key=lambda x: x[1], reverse=True)
        
        report.append("\nMost Common Issues:")
        for rec, count in sorted_recs[:5]:
            report.append(f"  - {rec} (occurred in {count} scenarios)")
        
        # High-level recommendations
        report.append("\nHigh-Level Recommendations:")
        
        if degradation_handled < total_tests * 0.8:
            report.append("  1. Improve fallback mechanisms - only {:.0f}% of scenarios handled gracefully".format(
                degradation_handled/total_tests*100))
        
        if avg_recovery_time > 15:
            report.append(f"  2. Optimize recovery procedures - average recovery time of {avg_recovery_time:.1f}s is too high")
        
        if data_losses > 0:
            report.append(f"  3. Implement better state persistence - {data_losses} scenarios resulted in data loss")
        
        # Success criteria
        report.append("\nSUCCESS CRITERIA:")
        criteria_met = {
            "graceful_degradation": degradation_handled >= total_tests * 0.9,
            "fast_recovery": avg_recovery_time <= 10,
            "no_data_loss": data_losses == 0,
            "error_handling": all(len(r.errors_observed) < 3 for r in results)
        }
        
        for criterion, met in criteria_met.items():
            status = "PASS" if met else "FAIL"
            report.append(f"  {criterion.replace('_', ' ').title()}: {status}")
        
        overall_pass = all(criteria_met.values())
        report.append(f"\nOVERALL RESULT: {'PASS' if overall_pass else 'FAIL'}")
        
        return "\n".join(report)

def main():
    """Run failure mode tests"""
    tester = FailureModeTester()
    
    print("Starting Wave 8 Failure Mode Testing...")
    print("WARNING: This will temporarily disrupt services")
    print("Ensure you have backups and can restore services if needed")
    print("")
    
    # Confirm before proceeding
    response = input("Continue with failure testing? (yes/no): ")
    if response.lower() != "yes":
        print("Failure testing cancelled")
        return
    
    results = []
    
    # Run each failure scenario
    for scenario in tester.failure_scenarios:
        try:
            result = tester.run_failure_scenario(scenario)
            results.append(result)
            
            # Cool down between scenarios
            print("\nCooling down for 15 seconds...")
            time.sleep(15)
            
        except Exception as e:
            print(f"ERROR: Failed to complete scenario {scenario['name']}: {e}")
            # Try to restore services
            try:
                scenario["teardown"]()
            except:
                pass
    
    # Generate report
    report = tester.generate_failure_report(results)
    print("\n" + report)
    
    # Save detailed results
    with open("failure_mode_results.json", "w") as f:
        serializable_results = []
        for result in results:
            serializable_result = {
                "test_name": result.test_name,
                "failure_type": result.failure_type,
                "description": result.description,
                "degradation_handled": result.degradation_handled,
                "recovery_time": result.recovery_time,
                "data_loss": result.data_loss,
                "errors_count": len(result.errors_observed),
                "recommendations": result.recommendations
            }
            serializable_results.append(serializable_result)
        
        json.dump(serializable_results, f, indent=2)
    
    print("\nDetailed results saved to failure_mode_results.json")

if __name__ == "__main__":
    main()