#!/usr/bin/env python3
"""Demo script for Wave 6 Adaptive Multi-Model Classifier.

This script demonstrates the intelligent routing between:
1. Rule-based classifier (fastest, ~10-30ms)
2. Zero-shot classifier (medium, ~100-200ms)
3. DistilBERT via TorchServe (slowest, ~300-500ms)
"""

import asyncio
import time
from typing import List, Dict, Any
import json
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

# Import the necessary components
from app.models.enhanced_classifier import EnhancedRuleBasedClassifier
from app.models.zero_shot_classifier import HybridClassifier, ZeroShotModelType
from app.models.adaptive_router import AdaptiveModelRouter
from app.models.torchserve_client import TorchServeClient
from app.core.config import settings


# Test queries with different characteristics
TEST_QUERIES = [
    # Simple queries that should use rules
    {
        "text": "What is the capital of France?",
        "latency": "critical",
        "expected_model": "rules",
        "description": "Simple factual question"
    },
    {
        "text": "How do I print hello world in Python?",
        "latency": "critical",
        "expected_model": "rules",
        "description": "Simple code question"
    },
    
    # Medium complexity that might use zero-shot
    {
        "text": "Explain the difference between supervised and unsupervised learning in machine learning",
        "latency": "standard",
        "expected_model": "zero_shot",
        "description": "Explanation requiring moderate analysis"
    },
    {
        "text": "Write a function to reverse a linked list and explain the algorithm",
        "latency": "standard",
        "expected_model": "zero_shot",
        "description": "Code generation with explanation"
    },
    
    # Complex queries that should use DistilBERT
    {
        "text": "Analyze the following dataset and provide insights about customer behavior patterns, identify anomalies, and suggest predictive models that could be applied",
        "latency": "relaxed",
        "expected_model": "distilbert",
        "description": "Complex data analysis task"
    },
    {
        "text": "Design a scalable microservices architecture for an e-commerce platform that handles millions of users, includes real-time inventory management, payment processing, and recommendation engine",
        "latency": "relaxed",
        "expected_model": "distilbert",
        "description": "Complex system design"
    },
]


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{text:^80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")


def print_result(query_info: Dict[str, Any], result: Dict[str, Any], routing_decision: Any):
    """Print classification result with routing information."""
    print(f"{Fore.YELLOW}Query:{Style.RESET_ALL} {query_info['text'][:80]}...")
    print(f"{Fore.YELLOW}Description:{Style.RESET_ALL} {query_info['description']}")
    print(f"{Fore.YELLOW}Latency Requirement:{Style.RESET_ALL} {query_info['latency']}")
    
    print(f"\n{Fore.GREEN}Classification Result:{Style.RESET_ALL}")
    print(f"  Intent: {result['intent']}")
    print(f"  Confidence: {result['confidence']:.3f}")
    print(f"  Complexity: {result['complexity']}")
    print(f"  Techniques: {', '.join(result.get('suggested_techniques', []))}")
    
    print(f"\n{Fore.MAGENTA}Routing Decision:{Style.RESET_ALL}")
    print(f"  Selected Model: {routing_decision.selected_model.value}")
    print(f"  Expected Latency: {routing_decision.expected_latency:.1f}ms")
    print(f"  Actual Latency: {result['routing_metadata']['latency_ms']:.1f}ms")
    print(f"  A/B Test Group: {routing_decision.ab_test_group or 'None'}")
    
    print(f"\n{Fore.BLUE}Routing Reasons:{Style.RESET_ALL}")
    for reason in routing_decision.reasons:
        print(f"  - {reason}")
    
    # Check if expected model matches
    if routing_decision.selected_model.value == query_info['expected_model']:
        print(f"\n{Fore.GREEN}✓ Model selection matched expectation{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}✗ Expected {query_info['expected_model']}, got {routing_decision.selected_model.value}{Style.RESET_ALL}")
    
    print(f"\n{'-' * 80}\n")


async def run_demo():
    """Run the Wave 6 adaptive routing demo."""
    print_header("Wave 6: Adaptive Multi-Model Classifier Demo")
    
    print("Initializing classifiers...")
    
    # Initialize rule-based classifier
    rule_classifier = EnhancedRuleBasedClassifier()
    
    # Initialize hybrid classifier
    hybrid_classifier = HybridClassifier(
        rule_classifier=rule_classifier,
        zero_shot_model=ZeroShotModelType.DEBERTA_V3_MNLI,
        rule_confidence_threshold=0.85
    )
    await hybrid_classifier.initialize()
    
    # Initialize TorchServe client (optional)
    torchserve_client = None
    if settings.USE_TORCHSERVE:
        try:
            torchserve_client = TorchServeClient()
            await torchserve_client.connect()
            if await torchserve_client.health_check():
                print(f"{Fore.GREEN}✓ TorchServe connected successfully{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠ TorchServe not healthy, will use fallback{Style.RESET_ALL}")
                torchserve_client = None
        except Exception as e:
            print(f"{Fore.YELLOW}⚠ TorchServe not available: {e}{Style.RESET_ALL}")
            torchserve_client = None
    
    # Initialize adaptive router
    router = AdaptiveModelRouter(
        rule_classifier=rule_classifier,
        hybrid_classifier=hybrid_classifier,
        torchserve_client=torchserve_client,
        enable_ab_testing=True,
        ab_test_percentage=0.3  # 30% for demo
    )
    
    print(f"\n{Fore.GREEN}✓ All classifiers initialized{Style.RESET_ALL}")
    
    # Test each query
    print_header("Running Classification Tests")
    
    for i, query_info in enumerate(TEST_QUERIES, 1):
        print(f"{Fore.CYAN}Test {i}/{len(TEST_QUERIES)}{Style.RESET_ALL}")
        
        try:
            # Run classification with routing
            result, routing_decision = await router.route_and_classify(
                text=query_info["text"],
                latency_requirement=query_info["latency"],
                min_confidence=0.7
            )
            
            # Print results
            print_result(query_info, result, routing_decision)
            
            # Small delay between tests
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
            continue
    
    # Print routing statistics
    print_header("Routing Statistics")
    
    stats = router.get_routing_stats()
    print(f"Total Requests: {stats['total_requests']}")
    
    print(f"\n{Fore.YELLOW}Model Distribution:{Style.RESET_ALL}")
    for model, data in stats['model_distribution'].items():
        print(f"  {model}: {data['count']} requests ({data['percentage']:.1f}%)")
    
    print(f"\n{Fore.YELLOW}Average Latencies:{Style.RESET_ALL}")
    for model, latencies in stats['average_latencies'].items():
        print(f"  {model}:")
        print(f"    P50: {latencies['p50']:.1f}ms")
        print(f"    P95: {latencies['p95']:.1f}ms")
        print(f"    P99: {latencies['p99']:.1f}ms")
    
    if stats['ab_test_groups']:
        print(f"\n{Fore.YELLOW}A/B Test Groups:{Style.RESET_ALL}")
        for group, data in stats['ab_test_groups'].items():
            print(f"  {group}:")
            print(f"    Requests: {data['count']}")
            print(f"    Avg Latency: {data['avg_latency']:.1f}ms")
            print(f"    Avg Confidence: {data['avg_confidence']:.3f}")
    
    # Cleanup
    if torchserve_client:
        await torchserve_client.close()
    
    print(f"\n{Fore.GREEN}✓ Demo completed successfully{Style.RESET_ALL}")


async def test_latency_scenarios():
    """Test different latency scenarios."""
    print_header("Latency Scenario Testing")
    
    # Initialize components
    rule_classifier = EnhancedRuleBasedClassifier()
    hybrid_classifier = HybridClassifier(
        rule_classifier=rule_classifier,
        zero_shot_model=ZeroShotModelType.DEBERTA_V3_MNLI,
        rule_confidence_threshold=0.85
    )
    await hybrid_classifier.initialize()
    
    router = AdaptiveModelRouter(
        rule_classifier=rule_classifier,
        hybrid_classifier=hybrid_classifier,
        torchserve_client=None,  # No TorchServe for this test
        enable_ab_testing=False   # Disable A/B testing for predictable results
    )
    
    test_text = "Explain quantum computing in simple terms"
    
    scenarios = ["critical", "standard", "relaxed"]
    
    for scenario in scenarios:
        print(f"\n{Fore.YELLOW}Testing with {scenario} latency requirement:{Style.RESET_ALL}")
        
        result, decision = await router.route_and_classify(
            text=test_text,
            latency_requirement=scenario,
            min_confidence=0.7
        )
        
        print(f"  Selected Model: {decision.selected_model.value}")
        print(f"  Latency: {result['routing_metadata']['latency_ms']:.1f}ms")
        print(f"  Confidence: {result['confidence']:.3f}")


async def test_confidence_thresholds():
    """Test how confidence thresholds affect routing."""
    print_header("Confidence Threshold Testing")
    
    # Initialize components
    rule_classifier = EnhancedRuleBasedClassifier()
    hybrid_classifier = HybridClassifier(
        rule_classifier=rule_classifier,
        zero_shot_model=ZeroShotModelType.DEBERTA_V3_MNLI,
        rule_confidence_threshold=0.85
    )
    await hybrid_classifier.initialize()
    
    router = AdaptiveModelRouter(
        rule_classifier=rule_classifier,
        hybrid_classifier=hybrid_classifier,
        torchserve_client=None,
        enable_ab_testing=False
    )
    
    # Test with different confidence thresholds
    thresholds = [0.7, 0.8, 0.85, 0.9]
    test_text = "What are the best practices for API design?"
    
    for threshold in thresholds:
        print(f"\n{Fore.YELLOW}Testing with rules confidence threshold: {threshold}{Style.RESET_ALL}")
        
        # Update threshold
        router.update_confidence_threshold(router.metrics[AdaptiveModelRouter.ModelType.RULES].model_type, threshold)
        
        result, decision = await router.route_and_classify(
            text=test_text,
            latency_requirement="standard",
            min_confidence=0.7
        )
        
        print(f"  Selected Model: {decision.selected_model.value}")
        print(f"  Confidence: {result['confidence']:.3f}")


if __name__ == "__main__":
    # Run the main demo
    asyncio.run(run_demo())
    
    # Run additional tests
    print("\n" * 2)
    asyncio.run(test_latency_scenarios())
    
    print("\n" * 2)
    asyncio.run(test_confidence_thresholds())