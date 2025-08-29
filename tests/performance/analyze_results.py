#!/usr/bin/env python3
"""
Analyze k6 performance test results and compare against baselines
"""
import json
import sys
import argparse
from typing import Dict, Any, List, Tuple


class PerformanceAnalyzer:
    def __init__(self, baseline_file: str, current_file: str, threshold: float = 10.0):
        self.baseline = self._load_results(baseline_file)
        self.current = self._load_results(current_file)
        self.threshold = threshold
        self.regressions: List[Tuple[str, float, float]] = []
        
    def _load_results(self, filename: str) -> Dict[str, Any]:
        """Load k6 results from JSON file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            sys.exit(1)
    
    def analyze(self) -> bool:
        """Analyze performance and detect regressions"""
        print("🔍 Analyzing Performance Results")
        print("=" * 50)
        
        # Check key metrics
        metrics_to_check = [
            ("http_req_duration", "p(95)", "P95 Response Time"),
            ("http_req_duration", "p(99)", "P99 Response Time"),
            ("http_req_duration", "avg", "Average Response Time"),
            ("enhance_latency", "p(95)", "P95 Enhance Latency"),
            ("classify_latency", "p(95)", "P95 Classify Latency"),
            ("errors", "rate", "Error Rate"),
        ]
        
        all_passed = True
        
        for metric_name, stat, display_name in metrics_to_check:
            baseline_value = self._get_metric_value(self.baseline, metric_name, stat)
            current_value = self._get_metric_value(self.current, metric_name, stat)
            
            if baseline_value is None or current_value is None:
                print(f"⚠️  {display_name}: Unable to compare (missing data)")
                continue
            
            # For error rate, any increase is bad
            if metric_name == "errors":
                if current_value > baseline_value * 1.1:  # 10% tolerance
                    regression_pct = ((current_value - baseline_value) / baseline_value) * 100
                    self.regressions.append((display_name, baseline_value, current_value))
                    print(f"❌ {display_name}: {baseline_value:.2%} → {current_value:.2%} "
                          f"(+{regression_pct:.1f}% regression)")
                    all_passed = False
                else:
                    print(f"✅ {display_name}: {baseline_value:.2%} → {current_value:.2%} (OK)")
            else:
                # For latency metrics, check threshold
                regression_pct = ((current_value - baseline_value) / baseline_value) * 100
                
                if regression_pct > self.threshold:
                    self.regressions.append((display_name, baseline_value, current_value))
                    print(f"❌ {display_name}: {baseline_value:.0f}ms → {current_value:.0f}ms "
                          f"(+{regression_pct:.1f}% regression)")
                    all_passed = False
                elif regression_pct < -5:  # Improvement
                    print(f"🚀 {display_name}: {baseline_value:.0f}ms → {current_value:.0f}ms "
                          f"({regression_pct:.1f}% improvement!)")
                else:
                    print(f"✅ {display_name}: {baseline_value:.0f}ms → {current_value:.0f}ms "
                          f"({regression_pct:+.1f}%)")
        
        print("\n" + "=" * 50)
        
        # Summary
        if all_passed:
            print("✅ All performance metrics within acceptable range!")
        else:
            print(f"❌ Found {len(self.regressions)} performance regressions:")
            for metric, baseline, current in self.regressions:
                print(f"   - {metric}: {baseline:.0f} → {current:.0f}")
        
        # Additional insights
        self._print_insights()
        
        return all_passed
    
    def _get_metric_value(self, data: Dict, metric: str, stat: str) -> float:
        """Extract metric value from k6 results"""
        try:
            metrics = data.get("metrics", {})
            metric_data = metrics.get(metric, {})
            values = metric_data.get("values", {})
            return values.get(stat)
        except:
            return None
    
    def _print_insights(self):
        """Print additional performance insights"""
        print("\n📊 Performance Insights:")
        
        # Request volume
        baseline_reqs = self._get_metric_value(self.baseline, "http_reqs", "count") or 0
        current_reqs = self._get_metric_value(self.current, "http_reqs", "count") or 0
        
        if baseline_reqs > 0 and current_reqs > 0:
            print(f"   Total Requests: {baseline_reqs:.0f} → {current_reqs:.0f}")
        
        # Success rate
        baseline_errors = self._get_metric_value(self.baseline, "errors", "rate") or 0
        current_errors = self._get_metric_value(self.current, "errors", "rate") or 0
        
        baseline_success = (1 - baseline_errors) * 100
        current_success = (1 - current_errors) * 100
        
        print(f"   Success Rate: {baseline_success:.1f}% → {current_success:.1f}%")
        
        # Throughput
        baseline_duration = self.baseline.get("state", {}).get("testRunDurationMs", 1) / 1000
        current_duration = self.current.get("state", {}).get("testRunDurationMs", 1) / 1000
        
        baseline_rps = baseline_reqs / baseline_duration if baseline_duration > 0 else 0
        current_rps = current_reqs / current_duration if current_duration > 0 else 0
        
        if baseline_rps > 0 and current_rps > 0:
            print(f"   Throughput: {baseline_rps:.1f} RPS → {current_rps:.1f} RPS")


def main():
    parser = argparse.ArgumentParser(description="Analyze k6 performance test results")
    parser.add_argument("--baseline", required=True, help="Baseline results JSON file")
    parser.add_argument("--current", required=True, help="Current results JSON file")
    parser.add_argument("--threshold", type=float, default=10.0, 
                       help="Regression threshold percentage (default: 10%)")
    
    args = parser.parse_args()
    
    analyzer = PerformanceAnalyzer(args.baseline, args.current, args.threshold)
    passed = analyzer.analyze()
    
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()