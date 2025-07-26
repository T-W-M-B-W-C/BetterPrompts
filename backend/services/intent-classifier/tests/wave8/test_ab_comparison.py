#!/usr/bin/env python3
"""
Wave 8: A/B Model Comparison Framework
Compares effectiveness of different models and routing strategies
"""

import json
import time
import statistics
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from scipy import stats

@dataclass
class ABTestResult:
    variant: str
    text: str
    intent: str
    confidence: float
    latency_ms: float
    model_used: str
    correct: bool
    user_satisfaction: float  # Simulated user satisfaction score

@dataclass
class ABVariant:
    name: str
    description: str
    config: Dict
    results: List[ABTestResult]

class ABModelComparison:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        
        # Define A/B test variants
        self.variants = [
            ABVariant(
                name="baseline_adaptive",
                description="Default adaptive routing with standard thresholds",
                config={
                    "adaptive_routing": True,
                    "performance_mode": False,
                    "quality_mode": False,
                    "confidence_thresholds": {"rules": 0.85, "zero_shot": 0.70}
                },
                results=[]
            ),
            ABVariant(
                name="performance_first",
                description="Prioritize speed with rules-based model",
                config={
                    "adaptive_routing": False,
                    "performance_mode": True,
                    "quality_mode": False
                },
                results=[]
            ),
            ABVariant(
                name="quality_first",
                description="Prioritize accuracy with DistilBERT model",
                config={
                    "adaptive_routing": False,
                    "performance_mode": False,
                    "quality_mode": True
                },
                results=[]
            ),
            ABVariant(
                name="aggressive_routing",
                description="More aggressive confidence thresholds",
                config={
                    "adaptive_routing": True,
                    "performance_mode": False,
                    "quality_mode": False,
                    "confidence_thresholds": {"rules": 0.90, "zero_shot": 0.80}
                },
                results=[]
            ),
            ABVariant(
                name="conservative_routing",
                description="More conservative confidence thresholds",
                config={
                    "adaptive_routing": True,
                    "performance_mode": False,
                    "quality_mode": False,
                    "confidence_thresholds": {"rules": 0.75, "zero_shot": 0.60}
                },
                results=[]
            ),
        ]
        
        # Test dataset with ground truth
        self.test_dataset = [
            # Clear intent examples
            {"text": "What is machine learning?", "intent": "question_answering", "difficulty": "easy"},
            {"text": "How can I fix my broken computer?", "intent": "problem_solving", "difficulty": "easy"},
            {"text": "Write a poem about spring", "intent": "creative_writing", "difficulty": "easy"},
            {"text": "Create a Python function to reverse a string", "intent": "code_generation", "difficulty": "easy"},
            {"text": "Summarize this article about climate change", "intent": "summarization", "difficulty": "easy"},
            
            # Medium difficulty examples
            {"text": "Explain quantum computing to a beginner", "intent": "explanation", "difficulty": "medium"},
            {"text": "Design a distributed caching system", "intent": "task_planning", "difficulty": "medium"},
            {"text": "Debug this multithreading issue", "intent": "problem_solving", "difficulty": "medium"},
            {"text": "Translate this technical document to Spanish", "intent": "translation", "difficulty": "medium"},
            {"text": "Let's discuss AI ethics", "intent": "conversation", "difficulty": "medium"},
            
            # Ambiguous examples
            {"text": "Help me with this", "intent": "general_assistance", "difficulty": "hard"},
            {"text": "I need some advice", "intent": "general_assistance", "difficulty": "hard"},
            {"text": "Can you explain and write code for this?", "intent": "code_generation", "difficulty": "hard"},
            {"text": "Tell me about it and how to implement", "intent": "explanation", "difficulty": "hard"},
            {"text": "What do you think about this problem?", "intent": "conversation", "difficulty": "hard"},
            
            # Edge cases
            {"text": "Solve and explain this algorithm", "intent": "problem_solving", "difficulty": "hard"},
            {"text": "Write a story explaining photosynthesis", "intent": "creative_writing", "difficulty": "hard"},
            {"text": "Plan how to learn programming", "intent": "task_planning", "difficulty": "hard"},
            {"text": "Translate and summarize this", "intent": "translation", "difficulty": "hard"},
            {"text": "Debug this: print('Hello')", "intent": "problem_solving", "difficulty": "hard"},
        ]
        
        # Extend dataset with variations
        extended_dataset = []
        for item in self.test_dataset:
            # Add original
            extended_dataset.append(item)
            
            # Add variations
            if item["difficulty"] == "easy":
                # Add child-friendly version
                child_version = item.copy()
                child_version["text"] = item["text"].lower().replace("?", " please?")
                child_version["audience"] = "child"
                extended_dataset.append(child_version)
                
                # Add expert version
                expert_version = item.copy()
                expert_version["text"] = f"Provide a comprehensive analysis of: {item['text']}"
                expert_version["audience"] = "expert"
                extended_dataset.append(expert_version)
        
        self.test_dataset = extended_dataset
    
    def configure_variant(self, variant: ABVariant) -> None:
        """Configure the service for a specific A/B variant"""
        print(f"Configuring variant: {variant.name}")
        
        # Set feature flags
        if "adaptive_routing" in variant.config:
            requests.put(
                f"{self.base_url}/api/v1/feature-flags/adaptive_routing",
                json={"enabled": variant.config["adaptive_routing"], "rollout_percentage": 100}
            )
        
        if "performance_mode" in variant.config:
            requests.put(
                f"{self.base_url}/api/v1/feature-flags/performance_mode",
                json={"enabled": variant.config["performance_mode"], "rollout_percentage": 100}
            )
        
        if "quality_mode" in variant.config:
            requests.put(
                f"{self.base_url}/api/v1/feature-flags/quality_mode",
                json={"enabled": variant.config["quality_mode"], "rollout_percentage": 100}
            )
        
        # Update routing config if needed
        if "confidence_thresholds" in variant.config:
            requests.post(
                f"{self.base_url}/api/v1/intents/routing/config",
                json={"confidence_thresholds": variant.config["confidence_thresholds"]}
            )
        
        # Wait for configuration to take effect
        time.sleep(2)
    
    def run_classification(self, text: str, user_id: str) -> Tuple[Dict, float]:
        """Run a single classification and measure latency"""
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/intents/classify",
                json={"text": text, "user_id": user_id},
                timeout=10
            )
            response.raise_for_status()
            
            latency_ms = (time.time() - start_time) * 1000
            return response.json(), latency_ms
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return {"error": str(e), "intent": "error", "confidence": 0.0}, latency_ms
    
    def calculate_user_satisfaction(self, correct: bool, latency_ms: float, confidence: float) -> float:
        """Calculate simulated user satisfaction score"""
        # Base score from correctness
        base_score = 1.0 if correct else 0.0
        
        # Latency penalty (users prefer fast responses)
        if latency_ms < 50:
            latency_score = 1.0
        elif latency_ms < 100:
            latency_score = 0.9
        elif latency_ms < 200:
            latency_score = 0.7
        elif latency_ms < 500:
            latency_score = 0.5
        else:
            latency_score = 0.3
        
        # Confidence bonus (users trust confident responses)
        confidence_score = confidence
        
        # Weighted combination
        if correct:
            satisfaction = 0.6 * base_score + 0.3 * latency_score + 0.1 * confidence_score
        else:
            # If wrong, latency doesn't matter as much
            satisfaction = 0.8 * base_score + 0.1 * latency_score + 0.1 * confidence_score
        
        return satisfaction
    
    def run_variant_test(self, variant: ABVariant, num_iterations: int = 5) -> None:
        """Run tests for a specific variant"""
        print(f"\nTesting variant: {variant.name}")
        print(f"Description: {variant.description}")
        
        # Configure variant
        self.configure_variant(variant)
        
        # Run multiple iterations to account for variability
        for iteration in range(num_iterations):
            print(f"  Iteration {iteration + 1}/{num_iterations}")
            
            for i, test_case in enumerate(self.test_dataset):
                # Create unique user ID for this test
                user_id = f"ab_test_{variant.name}_{iteration}_{i}"
                
                # Run classification
                result, latency_ms = self.run_classification(test_case["text"], user_id)
                
                # Check correctness
                correct = result.get("intent") == test_case["intent"]
                
                # Calculate user satisfaction
                satisfaction = self.calculate_user_satisfaction(
                    correct,
                    latency_ms,
                    result.get("confidence", 0.0)
                )
                
                # Store result
                ab_result = ABTestResult(
                    variant=variant.name,
                    text=test_case["text"],
                    intent=result.get("intent", "error"),
                    confidence=result.get("confidence", 0.0),
                    latency_ms=latency_ms,
                    model_used=result.get("model_used", "unknown"),
                    correct=correct,
                    user_satisfaction=satisfaction
                )
                
                variant.results.append(ab_result)
                
                # Small delay between requests
                time.sleep(0.05)
        
        print(f"  Completed {len(variant.results)} classifications")
    
    def run_all_variants(self) -> None:
        """Run tests for all variants"""
        print("Starting A/B Model Comparison Tests")
        print(f"Testing {len(self.variants)} variants with {len(self.test_dataset)} test cases")
        print(f"Total classifications per variant: {len(self.test_dataset) * 5}")
        
        for variant in self.variants:
            self.run_variant_test(variant)
            
            # Cool down between variants
            print("  Cooling down for 5 seconds...")
            time.sleep(5)
        
        print("\nAll variant tests completed")
    
    def analyze_variant_results(self, variant: ABVariant) -> Dict:
        """Analyze results for a single variant"""
        results = variant.results
        
        if not results:
            return {}
        
        # Basic metrics
        total = len(results)
        correct = sum(1 for r in results if r.correct)
        accuracy = correct / total if total > 0 else 0
        
        # Latency statistics
        latencies = [r.latency_ms for r in results]
        latency_stats = {
            "mean": statistics.mean(latencies),
            "median": statistics.median(latencies),
            "p95": sorted(latencies)[int(len(latencies) * 0.95)],
            "p99": sorted(latencies)[int(len(latencies) * 0.99)],
        }
        
        # User satisfaction
        satisfactions = [r.user_satisfaction for r in results]
        satisfaction_stats = {
            "mean": statistics.mean(satisfactions),
            "median": statistics.median(satisfactions),
            "std": statistics.stdev(satisfactions) if len(satisfactions) > 1 else 0
        }
        
        # Model distribution
        model_counts = {}
        for result in results:
            model = result.model_used
            model_counts[model] = model_counts.get(model, 0) + 1
        
        # Accuracy by difficulty
        accuracy_by_difficulty = {}
        for difficulty in ["easy", "medium", "hard"]:
            difficulty_results = [r for r in results 
                               for tc in self.test_dataset 
                               if tc["text"] == r.text and tc.get("difficulty") == difficulty]
            if difficulty_results:
                difficulty_correct = sum(1 for r in difficulty_results if r.correct)
                accuracy_by_difficulty[difficulty] = difficulty_correct / len(difficulty_results)
        
        return {
            "total_tests": total,
            "accuracy": accuracy,
            "latency_stats": latency_stats,
            "satisfaction_stats": satisfaction_stats,
            "model_distribution": model_counts,
            "accuracy_by_difficulty": accuracy_by_difficulty
        }
    
    def statistical_comparison(self, variant1: ABVariant, variant2: ABVariant) -> Dict:
        """Perform statistical comparison between two variants"""
        # Extract metrics
        v1_satisfactions = [r.user_satisfaction for r in variant1.results]
        v2_satisfactions = [r.user_satisfaction for r in variant2.results]
        
        v1_latencies = [r.latency_ms for r in variant1.results]
        v2_latencies = [r.latency_ms for r in variant2.results]
        
        v1_accuracy = sum(1 for r in variant1.results if r.correct) / len(variant1.results)
        v2_accuracy = sum(1 for r in variant2.results if r.correct) / len(variant2.results)
        
        # T-tests
        satisfaction_ttest = stats.ttest_ind(v1_satisfactions, v2_satisfactions)
        latency_ttest = stats.ttest_ind(v1_latencies, v2_latencies)
        
        # Effect sizes (Cohen's d)
        def cohens_d(x, y):
            nx = len(x)
            ny = len(y)
            dof = nx + ny - 2
            return (statistics.mean(x) - statistics.mean(y)) / np.sqrt(
                ((nx-1)*statistics.stdev(x)**2 + (ny-1)*statistics.stdev(y)**2) / dof
            )
        
        satisfaction_effect_size = cohens_d(v1_satisfactions, v2_satisfactions)
        latency_effect_size = cohens_d(v1_latencies, v2_latencies)
        
        return {
            "satisfaction_p_value": satisfaction_ttest.pvalue,
            "satisfaction_effect_size": satisfaction_effect_size,
            "latency_p_value": latency_ttest.pvalue,
            "latency_effect_size": latency_effect_size,
            "v1_accuracy": v1_accuracy,
            "v2_accuracy": v2_accuracy,
            "accuracy_diff": v2_accuracy - v1_accuracy
        }
    
    def plot_variant_comparison(self) -> None:
        """Generate comparison plots for all variants"""
        # Prepare data
        variant_names = [v.name for v in self.variants]
        accuracies = []
        mean_latencies = []
        mean_satisfactions = []
        
        for variant in self.variants:
            analysis = self.analyze_variant_results(variant)
            accuracies.append(analysis["accuracy"] * 100)
            mean_latencies.append(analysis["latency_stats"]["mean"])
            mean_satisfactions.append(analysis["satisfaction_stats"]["mean"])
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Accuracy comparison
        ax1 = axes[0, 0]
        bars1 = ax1.bar(variant_names, accuracies, color='skyblue')
        ax1.set_ylabel('Accuracy (%)')
        ax1.set_title('Model Accuracy Comparison')
        ax1.set_ylim(0, 100)
        for bar, acc in zip(bars1, accuracies):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{acc:.1f}%', ha='center', va='bottom')
        
        # 2. Latency comparison
        ax2 = axes[0, 1]
        bars2 = ax2.bar(variant_names, mean_latencies, color='lightcoral')
        ax2.set_ylabel('Mean Latency (ms)')
        ax2.set_title('Average Latency Comparison')
        for bar, lat in zip(bars2, mean_latencies):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{lat:.1f}ms', ha='center', va='bottom')
        
        # 3. User satisfaction
        ax3 = axes[1, 0]
        bars3 = ax3.bar(variant_names, mean_satisfactions, color='lightgreen')
        ax3.set_ylabel('Mean User Satisfaction')
        ax3.set_title('User Satisfaction Score')
        ax3.set_ylim(0, 1)
        for bar, sat in zip(bars3, mean_satisfactions):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{sat:.3f}', ha='center', va='bottom')
        
        # 4. Model distribution (for baseline variant)
        ax4 = axes[1, 1]
        baseline_variant = self.variants[0]
        baseline_analysis = self.analyze_variant_results(baseline_variant)
        model_dist = baseline_analysis["model_distribution"]
        
        if model_dist:
            models = list(model_dist.keys())
            counts = list(model_dist.values())
            ax4.pie(counts, labels=models, autopct='%1.1f%%', startangle=90)
            ax4.set_title('Model Usage Distribution (Baseline)')
        
        # Adjust layout
        plt.tight_layout()
        plt.savefig('ab_comparison_overview.png')
        plt.close()
        
        # Create accuracy by difficulty plot
        plt.figure(figsize=(12, 6))
        difficulties = ["easy", "medium", "hard"]
        x = np.arange(len(difficulties))
        width = 0.15
        
        for i, variant in enumerate(self.variants):
            analysis = self.analyze_variant_results(variant)
            acc_by_diff = analysis["accuracy_by_difficulty"]
            values = [acc_by_diff.get(d, 0) * 100 for d in difficulties]
            plt.bar(x + i*width, values, width, label=variant.name)
        
        plt.xlabel('Difficulty')
        plt.ylabel('Accuracy (%)')
        plt.title('Accuracy by Difficulty Level')
        plt.xticks(x + width * 2, difficulties)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('ab_accuracy_by_difficulty.png')
        plt.close()
        
        print("Saved comparison plots")
    
    def generate_ab_report(self) -> str:
        """Generate comprehensive A/B test report"""
        report = []
        report.append("=" * 80)
        report.append("WAVE 8: A/B MODEL COMPARISON REPORT")
        report.append("=" * 80)
        report.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Test overview
        report.append("TEST OVERVIEW:")
        report.append(f"  Variants Tested: {len(self.variants)}")
        report.append(f"  Test Cases: {len(self.test_dataset)}")
        report.append(f"  Iterations per Variant: 5")
        report.append(f"  Total Classifications: {sum(len(v.results) for v in self.variants)}")
        report.append("")
        
        # Variant results
        report.append("VARIANT RESULTS:")
        for variant in self.variants:
            analysis = self.analyze_variant_results(variant)
            
            report.append(f"\n{'='*60}")
            report.append(f"Variant: {variant.name}")
            report.append(f"Description: {variant.description}")
            report.append(f"{'='*60}")
            
            report.append(f"\nPerformance Metrics:")
            report.append(f"  Accuracy: {analysis['accuracy']:.2%}")
            report.append(f"  Mean Latency: {analysis['latency_stats']['mean']:.1f}ms")
            report.append(f"  P95 Latency: {analysis['latency_stats']['p95']:.1f}ms")
            report.append(f"  User Satisfaction: {analysis['satisfaction_stats']['mean']:.3f} ± {analysis['satisfaction_stats']['std']:.3f}")
            
            report.append(f"\nAccuracy by Difficulty:")
            for difficulty, acc in analysis['accuracy_by_difficulty'].items():
                report.append(f"  {difficulty}: {acc:.2%}")
            
            report.append(f"\nModel Usage:")
            total_requests = sum(analysis['model_distribution'].values())
            for model, count in sorted(analysis['model_distribution'].items()):
                percentage = count / total_requests * 100 if total_requests > 0 else 0
                report.append(f"  {model}: {count} ({percentage:.1f}%)")
        
        # Statistical comparisons
        report.append("\n" + "="*80)
        report.append("STATISTICAL COMPARISONS (vs Baseline)")
        report.append("="*80)
        
        baseline = self.variants[0]
        for variant in self.variants[1:]:
            comparison = self.statistical_comparison(baseline, variant)
            
            report.append(f"\n{baseline.name} vs {variant.name}:")
            report.append(f"  Accuracy Difference: {comparison['accuracy_diff']:+.2%}")
            report.append(f"  Satisfaction p-value: {comparison['satisfaction_p_value']:.4f}")
            report.append(f"  Satisfaction Effect Size: {comparison['satisfaction_effect_size']:.3f}")
            report.append(f"  Latency p-value: {comparison['latency_p_value']:.4f}")
            report.append(f"  Latency Effect Size: {comparison['latency_effect_size']:.3f}")
            
            # Interpret results
            if comparison['satisfaction_p_value'] < 0.05:
                if comparison['satisfaction_effect_size'] > 0:
                    report.append(f"  → {variant.name} has SIGNIFICANTLY HIGHER user satisfaction")
                else:
                    report.append(f"  → {variant.name} has SIGNIFICANTLY LOWER user satisfaction")
            else:
                report.append(f"  → No significant difference in user satisfaction")
        
        # Winner determination
        report.append("\n" + "="*80)
        report.append("WINNER DETERMINATION")
        report.append("="*80)
        
        # Find best variant for each metric
        best_accuracy = max(self.variants, key=lambda v: self.analyze_variant_results(v)["accuracy"])
        best_latency = min(self.variants, key=lambda v: self.analyze_variant_results(v)["latency_stats"]["mean"])
        best_satisfaction = max(self.variants, key=lambda v: self.analyze_variant_results(v)["satisfaction_stats"]["mean"])
        
        report.append(f"\nBest Accuracy: {best_accuracy.name} ({self.analyze_variant_results(best_accuracy)['accuracy']:.2%})")
        report.append(f"Best Latency: {best_latency.name} ({self.analyze_variant_results(best_latency)['latency_stats']['mean']:.1f}ms)")
        report.append(f"Best User Satisfaction: {best_satisfaction.name} ({self.analyze_variant_results(best_satisfaction)['satisfaction_stats']['mean']:.3f})")
        
        # Overall recommendation
        report.append("\nRECOMMENDATION:")
        
        # Simple scoring system
        scores = {}
        for variant in self.variants:
            analysis = self.analyze_variant_results(variant)
            # Weighted score: 40% accuracy, 30% satisfaction, 30% latency
            score = (
                0.4 * analysis["accuracy"] +
                0.3 * analysis["satisfaction_stats"]["mean"] +
                0.3 * (1 - min(analysis["latency_stats"]["mean"] / 500, 1))  # Normalize latency
            )
            scores[variant.name] = score
        
        best_overall = max(scores.items(), key=lambda x: x[1])
        report.append(f"  Recommended Variant: {best_overall[0]} (composite score: {best_overall[1]:.3f})")
        
        # Specific recommendations
        report.append("\nSPECIFIC USE CASE RECOMMENDATIONS:")
        report.append(f"  For Speed-Critical Applications: {best_latency.name}")
        report.append(f"  For Accuracy-Critical Applications: {best_accuracy.name}")
        report.append(f"  For Best User Experience: {best_satisfaction.name}")
        report.append(f"  For Balanced Performance: {best_overall[0]}")
        
        return "\n".join(report)

def main():
    """Run A/B model comparison tests"""
    tester = ABModelComparison()
    
    print("Starting Wave 8 A/B Model Comparison Tests...")
    print("This will test different model configurations and routing strategies")
    print("")
    
    # Run all variant tests
    tester.run_all_variants()
    
    # Generate plots
    print("\nGenerating comparison plots...")
    tester.plot_variant_comparison()
    
    # Generate report
    report = tester.generate_ab_report()
    print("\n" + report)
    
    # Save detailed results
    with open("ab_comparison_results.json", "w") as f:
        results = {}
        for variant in tester.variants:
            analysis = tester.analyze_variant_results(variant)
            results[variant.name] = {
                "description": variant.description,
                "config": variant.config,
                "analysis": analysis,
                "total_tests": len(variant.results)
            }
        
        json.dump(results, f, indent=2)
    
    print("\nDetailed results saved to ab_comparison_results.json")
    print("Comparison plots saved as PNG files")

if __name__ == "__main__":
    main()