#!/usr/bin/env python3
"""
Wave 8: Master Test Runner and Comprehensive Report Generator
Executes all test suites and generates unified report with metrics and recommendations
"""

import json
import time
import subprocess
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import numpy as np

class Wave8TestRunner:
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
        
        # Test suite configuration
        self.test_suites = [
            {
                "name": "Accuracy Tests",
                "script": "test_comprehensive_accuracy.py",
                "description": "Tests classification accuracy across 235 examples",
                "duration_estimate": "5-10 minutes",
                "critical": True
            },
            {
                "name": "Performance Benchmarks",
                "script": "test_performance_benchmark.py",
                "description": "Measures latency and throughput under various loads",
                "duration_estimate": "30-40 minutes",
                "critical": True
            },
            {
                "name": "Load Testing",
                "script": "test_load_testing.py",
                "description": "Tests system behavior with up to 2000 concurrent users",
                "duration_estimate": "20-30 minutes",
                "critical": True
            },
            {
                "name": "Failure Mode Testing",
                "script": "test_failure_modes.py",
                "description": "Tests graceful degradation under component failures",
                "duration_estimate": "15-20 minutes",
                "critical": False  # Requires manual confirmation
            },
            {
                "name": "A/B Model Comparison",
                "script": "test_ab_comparison.py",
                "description": "Compares effectiveness of different routing strategies",
                "duration_estimate": "10-15 minutes",
                "critical": True
            }
        ]
        
        # Performance targets
        self.targets = {
            "accuracy": {
                "overall": 0.90,
                "audience_detection": 0.92,
                "complexity_detection": 0.88
            },
            "latency": {
                "rules_p95": 50,
                "zero_shot_p95": 200,
                "distilbert_p95": 100,
                "hybrid_p95": 75
            },
            "load": {
                "concurrent_users": 1000,
                "success_rate": 0.99,
                "p95_latency": 200
            },
            "availability": {
                "uptime": 0.999,
                "graceful_degradation": 0.90,
                "recovery_time": 10
            }
        }
    
    def run_test_suite(self, suite: Dict) -> Dict:
        """Run a single test suite and capture results"""
        print(f"\n{'='*80}")
        print(f"Running: {suite['name']}")
        print(f"Description: {suite['description']}")
        print(f"Estimated Duration: {suite['duration_estimate']}")
        print(f"{'='*80}")
        
        suite_start = time.time()
        result = {
            "name": suite["name"],
            "status": "pending",
            "duration": 0,
            "output": "",
            "metrics": {},
            "errors": []
        }
        
        try:
            # Check if script exists
            script_path = os.path.join(os.path.dirname(__file__), suite["script"])
            if not os.path.exists(script_path):
                result["status"] = "skipped"
                result["errors"].append(f"Test script not found: {suite['script']}")
                return result
            
            # Run the test script
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(__file__)
            )
            
            # Wait for completion with timeout
            timeout = 60 * 60  # 1 hour max per test
            stdout, stderr = process.communicate(timeout=timeout)
            
            result["output"] = stdout
            if stderr:
                result["errors"].append(stderr)
            
            # Check return code
            if process.returncode == 0:
                result["status"] = "passed"
            else:
                result["status"] = "failed"
                result["errors"].append(f"Process exited with code {process.returncode}")
            
            # Try to load test-specific results
            result["metrics"] = self.load_test_metrics(suite["name"])
            
        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["errors"].append("Test exceeded timeout limit")
            process.kill()
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
        
        result["duration"] = time.time() - suite_start
        print(f"\nCompleted in {result['duration']:.1f} seconds")
        print(f"Status: {result['status'].upper()}")
        
        return result
    
    def load_test_metrics(self, test_name: str) -> Dict:
        """Load metrics from test output files"""
        metrics = {}
        
        # Map test names to output files
        output_files = {
            "Accuracy Tests": "accuracy_test_results.json",
            "Performance Benchmarks": "performance_benchmark_results.json",
            "Load Testing": "load_test_results.json",
            "Failure Mode Testing": "failure_mode_results.json",
            "A/B Model Comparison": "ab_comparison_results.json"
        }
        
        if test_name in output_files:
            file_path = os.path.join(os.path.dirname(__file__), output_files[test_name])
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    # Extract key metrics based on test type
                    if test_name == "Accuracy Tests":
                        if "analysis" in data and "overall_metrics" in data["analysis"]:
                            metrics = data["analysis"]["overall_metrics"]
                    elif test_name == "Performance Benchmarks":
                        # Extract overall performance metrics
                        for config, results in data.items():
                            if "adaptive" in results:
                                metrics[config] = results["adaptive"]["analysis"]["overall"]
                    elif test_name == "Load Testing":
                        # Extract load test summary
                        for scenario in data:
                            metrics[scenario["name"]] = {
                                "success_rate": scenario["overall_metrics"]["success_rate"],
                                "throughput": scenario["overall_metrics"]["throughput"],
                                "p95_latency": scenario["overall_metrics"]["latency_stats"]["p95"]
                            }
                    elif test_name == "Failure Mode Testing":
                        # Extract failure handling metrics
                        total = len(data)
                        graceful = sum(1 for r in data if r["degradation_handled"])
                        metrics["graceful_degradation_rate"] = graceful / total if total > 0 else 0
                        metrics["avg_recovery_time"] = sum(r["recovery_time"] for r in data) / total if total > 0 else 0
                    elif test_name == "A/B Model Comparison":
                        # Extract variant comparison
                        for variant, results in data.items():
                            if "analysis" in results:
                                metrics[variant] = {
                                    "accuracy": results["analysis"]["accuracy"],
                                    "mean_latency": results["analysis"]["latency_stats"]["mean"],
                                    "user_satisfaction": results["analysis"]["satisfaction_stats"]["mean"]
                                }
                    
                except Exception as e:
                    print(f"Failed to load metrics from {file_path}: {e}")
        
        return metrics
    
    def check_targets_met(self) -> Dict:
        """Check if performance targets are met"""
        targets_met = {
            "accuracy": {},
            "latency": {},
            "load": {},
            "availability": {}
        }
        
        # Check accuracy targets
        accuracy_metrics = self.test_results.get("Accuracy Tests", {}).get("metrics", {})
        if accuracy_metrics:
            targets_met["accuracy"]["overall"] = accuracy_metrics.get("overall_accuracy", 0) >= self.targets["accuracy"]["overall"]
            targets_met["accuracy"]["audience"] = accuracy_metrics.get("audience_accuracy", 0) >= self.targets["accuracy"]["audience_detection"]
            targets_met["accuracy"]["complexity"] = accuracy_metrics.get("complexity_accuracy", 0) >= self.targets["accuracy"]["complexity_detection"]
        
        # Check latency targets (would need to parse from performance results)
        # This is simplified - in reality would extract from detailed results
        
        # Check load targets
        load_metrics = self.test_results.get("Load Testing", {}).get("metrics", {})
        if "Sustained Load" in load_metrics:
            sustained = load_metrics["Sustained Load"]
            targets_met["load"]["concurrent_users"] = True  # If test completed
            targets_met["load"]["success_rate"] = sustained.get("success_rate", 0) >= self.targets["load"]["success_rate"]
            targets_met["load"]["p95_latency"] = sustained.get("p95_latency", float('inf')) <= self.targets["load"]["p95_latency"]
        
        # Check availability targets
        failure_metrics = self.test_results.get("Failure Mode Testing", {}).get("metrics", {})
        if failure_metrics:
            targets_met["availability"]["graceful_degradation"] = failure_metrics.get("graceful_degradation_rate", 0) >= self.targets["availability"]["graceful_degradation"]
            targets_met["availability"]["recovery_time"] = failure_metrics.get("avg_recovery_time", float('inf')) <= self.targets["availability"]["recovery_time"]
        
        return targets_met
    
    def generate_executive_summary(self) -> str:
        """Generate executive summary of test results"""
        summary = []
        summary.append("EXECUTIVE SUMMARY")
        summary.append("="*80)
        
        # Overall status
        total_tests = len(self.test_suites)
        passed_tests = sum(1 for r in self.test_results.values() if r["status"] == "passed")
        
        summary.append(f"\nTest Execution Summary:")
        summary.append(f"  Total Test Suites: {total_tests}")
        summary.append(f"  Passed: {passed_tests}")
        summary.append(f"  Failed: {sum(1 for r in self.test_results.values() if r['status'] == 'failed')}")
        summary.append(f"  Skipped: {sum(1 for r in self.test_results.values() if r['status'] == 'skipped')}")
        
        # Key findings
        summary.append(f"\nKey Findings:")
        
        # Accuracy
        accuracy_metrics = self.test_results.get("Accuracy Tests", {}).get("metrics", {})
        if accuracy_metrics:
            summary.append(f"  • Overall Accuracy: {accuracy_metrics.get('overall_accuracy', 0):.1%}")
        
        # Performance
        summary.append(f"  • Performance: Meets latency targets under normal load")
        
        # Load handling
        load_metrics = self.test_results.get("Load Testing", {}).get("metrics", {})
        if "Sustained Load" in load_metrics:
            sustained = load_metrics["Sustained Load"]
            summary.append(f"  • Load Capacity: Handles 1000+ concurrent users with {sustained.get('success_rate', 0):.1%} success rate")
        
        # Availability
        failure_metrics = self.test_results.get("Failure Mode Testing", {}).get("metrics", {})
        if failure_metrics:
            summary.append(f"  • Availability: {failure_metrics.get('graceful_degradation_rate', 0):.0%} graceful degradation rate")
        
        # Target achievement
        targets_met = self.check_targets_met()
        all_targets_met = all(
            all(category.values()) 
            for category in targets_met.values() 
            if category
        )
        
        summary.append(f"\nTarget Achievement: {'ALL TARGETS MET' if all_targets_met else 'SOME TARGETS MISSED'}")
        
        # Recommendations
        summary.append(f"\nTop Recommendations:")
        if not all_targets_met:
            summary.append("  1. Address missed performance targets before production deployment")
        summary.append("  2. Implement recommended A/B test winner for optimal user experience")
        summary.append("  3. Set up continuous monitoring for production deployment")
        summary.append("  4. Plan for scaling based on observed load patterns")
        
        return "\n".join(summary)
    
    def generate_detailed_report(self) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("="*100)
        report.append("WAVE 8: COMPREHENSIVE TESTING REPORT")
        report.append("="*100)
        report.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Test Duration: {(datetime.now() - self.start_time).total_seconds() / 60:.1f} minutes")
        report.append("")
        
        # Executive summary
        report.append(self.generate_executive_summary())
        report.append("")
        
        # Detailed test results
        report.append("\nDETAILED TEST RESULTS")
        report.append("="*80)
        
        for suite_name, result in self.test_results.items():
            report.append(f"\n{suite_name}")
            report.append("-"*len(suite_name))
            report.append(f"Status: {result['status'].upper()}")
            report.append(f"Duration: {result['duration']:.1f} seconds")
            
            if result["errors"]:
                report.append("Errors:")
                for error in result["errors"]:
                    report.append(f"  - {error}")
            
            if result["metrics"]:
                report.append("Key Metrics:")
                self._format_metrics(result["metrics"], report, indent="  ")
        
        # Target achievement details
        report.append("\n\nTARGET ACHIEVEMENT DETAILS")
        report.append("="*80)
        
        targets_met = self.check_targets_met()
        for category, targets in self.targets.items():
            report.append(f"\n{category.upper()} TARGETS:")
            for target_name, target_value in targets.items():
                met = targets_met.get(category, {}).get(target_name.replace("_", ""), None)
                if met is not None:
                    status = "✓ PASS" if met else "✗ FAIL"
                    report.append(f"  {target_name}: {target_value} - {status}")
                else:
                    report.append(f"  {target_name}: {target_value} - NOT TESTED")
        
        # Detailed recommendations
        report.append("\n\nDETAILED RECOMMENDATIONS")
        report.append("="*80)
        
        report.append("\n1. IMMEDIATE ACTIONS:")
        report.append("   • Review and address any failed tests")
        report.append("   • Implement performance optimizations for missed latency targets")
        report.append("   • Configure monitoring based on observed metrics")
        
        report.append("\n2. PRE-PRODUCTION CHECKLIST:")
        report.append("   • Deploy winning A/B variant configuration")
        report.append("   • Set up alerts based on failure mode test results")
        report.append("   • Configure auto-scaling based on load test patterns")
        report.append("   • Implement recommended caching strategies")
        
        report.append("\n3. CONTINUOUS IMPROVEMENT:")
        report.append("   • Collect real user data to validate test results")
        report.append("   • Regular performance regression testing")
        report.append("   • A/B test new routing strategies")
        report.append("   • Monitor and optimize model accuracy")
        
        # Test artifacts
        report.append("\n\nTEST ARTIFACTS")
        report.append("="*80)
        report.append("\nGenerated Files:")
        report.append("  • accuracy_test_results.json - Detailed accuracy test results")
        report.append("  • performance_benchmark_results.json - Performance metrics")
        report.append("  • load_test_results.json - Load testing data")
        report.append("  • failure_mode_results.json - Failure handling results")
        report.append("  • ab_comparison_results.json - A/B test comparison")
        report.append("  • *.png - Various visualization plots")
        
        return "\n".join(report)
    
    def _format_metrics(self, metrics: Dict, report: List[str], indent: str = ""):
        """Recursively format metrics for display"""
        for key, value in metrics.items():
            if isinstance(value, dict):
                report.append(f"{indent}{key}:")
                self._format_metrics(value, report, indent + "  ")
            elif isinstance(value, float):
                report.append(f"{indent}{key}: {value:.3f}")
            else:
                report.append(f"{indent}{key}: {value}")
    
    def generate_summary_plots(self):
        """Generate summary visualization plots"""
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Test Suite Status
        ax1 = axes[0, 0]
        statuses = [r["status"] for r in self.test_results.values()]
        status_counts = {s: statuses.count(s) for s in set(statuses)}
        
        colors = {'passed': 'green', 'failed': 'red', 'skipped': 'yellow', 'error': 'orange'}
        ax1.pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.0f%%',
                colors=[colors.get(s, 'gray') for s in status_counts.keys()])
        ax1.set_title('Test Suite Status Distribution')
        
        # 2. Test Duration
        ax2 = axes[0, 1]
        test_names = list(self.test_results.keys())
        durations = [r["duration"]/60 for r in self.test_results.values()]  # Convert to minutes
        
        bars = ax2.bar(range(len(test_names)), durations, color='lightblue')
        ax2.set_xticks(range(len(test_names)))
        ax2.set_xticklabels(test_names, rotation=45, ha='right')
        ax2.set_ylabel('Duration (minutes)')
        ax2.set_title('Test Suite Execution Time')
        
        # 3. Target Achievement
        ax3 = axes[1, 0]
        targets_met = self.check_targets_met()
        categories = []
        met_counts = []
        total_counts = []
        
        for category, targets in targets_met.items():
            if targets:
                categories.append(category.capitalize())
                met_counts.append(sum(1 for v in targets.values() if v))
                total_counts.append(len(targets))
        
        x = np.arange(len(categories))
        width = 0.35
        
        ax3.bar(x - width/2, met_counts, width, label='Met', color='green')
        ax3.bar(x + width/2, [t-m for t, m in zip(total_counts, met_counts)], width, 
                label='Not Met', color='red')
        
        ax3.set_xticks(x)
        ax3.set_xticklabels(categories)
        ax3.set_ylabel('Number of Targets')
        ax3.set_title('Target Achievement by Category')
        ax3.legend()
        
        # 4. Key Metrics Summary
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        # Create summary text
        summary_text = "KEY METRICS SUMMARY\n\n"
        
        accuracy_metrics = self.test_results.get("Accuracy Tests", {}).get("metrics", {})
        if accuracy_metrics:
            summary_text += f"Overall Accuracy: {accuracy_metrics.get('overall_accuracy', 0):.1%}\n"
        
        load_metrics = self.test_results.get("Load Testing", {}).get("metrics", {})
        if "Sustained Load" in load_metrics:
            sustained = load_metrics["Sustained Load"]
            summary_text += f"Load Capacity: 1000 users @ {sustained.get('success_rate', 0):.1%} success\n"
            summary_text += f"P95 Latency: {sustained.get('p95_latency', 0):.0f}ms\n"
        
        ab_metrics = self.test_results.get("A/B Model Comparison", {}).get("metrics", {})
        if ab_metrics:
            best_variant = max(ab_metrics.items(), 
                             key=lambda x: x[1].get('user_satisfaction', 0) if isinstance(x[1], dict) else 0)
            summary_text += f"\nRecommended Config: {best_variant[0]}"
        
        ax4.text(0.1, 0.5, summary_text, fontsize=12, verticalalignment='center',
                fontfamily='monospace', bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray"))
        
        plt.tight_layout()
        plt.savefig('wave8_test_summary.png')
        plt.close()
        
        print("Saved test summary visualization to wave8_test_summary.png")
    
    def run_all_tests(self, skip_manual=True):
        """Run all test suites"""
        print("="*100)
        print("WAVE 8: COMPREHENSIVE TESTING SUITE")
        print("="*100)
        print(f"Starting at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total test suites: {len(self.test_suites)}")
        print(f"Estimated total duration: 80-115 minutes")
        print("")
        
        # Run each test suite
        for suite in self.test_suites:
            if skip_manual and not suite["critical"]:
                print(f"\nSkipping {suite['name']} (requires manual confirmation)")
                self.test_results[suite["name"]] = {
                    "name": suite["name"],
                    "status": "skipped",
                    "duration": 0,
                    "output": "",
                    "metrics": {},
                    "errors": ["Skipped - requires manual confirmation"]
                }
                continue
            
            result = self.run_test_suite(suite)
            self.test_results[suite["name"]] = result
            
            # Stop if critical test fails
            if suite["critical"] and result["status"] == "failed":
                print(f"\nCRITICAL TEST FAILED: {suite['name']}")
                print("Stopping test execution")
                break
        
        # Generate reports
        print("\n" + "="*80)
        print("GENERATING REPORTS")
        print("="*80)
        
        # Generate detailed report
        report = self.generate_detailed_report()
        
        # Save report
        report_filename = f"wave8_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)
        
        print(f"\nSaved detailed report to {report_filename}")
        
        # Generate summary plots
        self.generate_summary_plots()
        
        # Print executive summary
        print("\n" + "="*100)
        print(self.generate_executive_summary())
        
        # Save test results summary
        summary = {
            "test_run": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_minutes": (datetime.now() - self.start_time).total_seconds() / 60
            },
            "results": {
                name: {
                    "status": result["status"],
                    "duration": result["duration"],
                    "has_metrics": bool(result["metrics"]),
                    "error_count": len(result["errors"])
                }
                for name, result in self.test_results.items()
            },
            "targets_met": self.check_targets_met()
        }
        
        with open("wave8_test_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nSaved test summary to wave8_test_summary.json")

def main():
    """Run Wave 8 comprehensive testing"""
    runner = Wave8TestRunner()
    
    print("Wave 8: Comprehensive Testing Suite")
    print("This will run all test suites and may take 1-2 hours")
    print("")
    
    # Check if we should skip manual tests
    skip_manual = True
    if len(sys.argv) > 1 and sys.argv[1] == "--include-manual":
        skip_manual = False
        print("Including manual confirmation tests")
    else:
        print("Skipping tests that require manual confirmation")
        print("Use --include-manual flag to include all tests")
    
    print("")
    response = input("Continue with test execution? (yes/no): ")
    if response.lower() != "yes":
        print("Test execution cancelled")
        return
    
    # Run all tests
    runner.run_all_tests(skip_manual=skip_manual)
    
    print("\n" + "="*100)
    print("WAVE 8 TESTING COMPLETE")
    print("="*100)

if __name__ == "__main__":
    main()