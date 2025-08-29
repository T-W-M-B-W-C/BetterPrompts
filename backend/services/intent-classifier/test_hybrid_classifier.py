#!/usr/bin/env python3
"""
Test script for hybrid classifier with ambiguous examples
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.enhanced_classifier import EnhancedRuleBasedClassifier
from app.models.zero_shot_classifier import HybridClassifier, ZeroShotModelType


async def test_hybrid_classifier():
    """Test hybrid classifier with various examples"""
    
    # Initialize classifiers
    rule_classifier = EnhancedRuleBasedClassifier()
    hybrid_classifier = HybridClassifier(
        rule_classifier=rule_classifier,
        zero_shot_model=ZeroShotModelType.DEBERTA_V3_MNLI,
        rule_confidence_threshold=0.85
    )
    
    await hybrid_classifier.initialize()
    
    # Test cases with varying ambiguity
    test_cases = [
        # High confidence rule-based (should use rules)
        ("Write a Python function to calculate the factorial of a number", "code_generation", "rule_based"),
        ("Translate 'Hello World' to Spanish", "translation", "rule_based"),
        ("Explain photosynthesis to a 5 year old", "question_answering", "rule_based"),
        
        # Ambiguous cases (should use zero-shot)
        ("Help me with this", "conversation", "zero_shot"),
        ("Can you do something for me?", "conversation", "zero_shot"),
        ("I need assistance", "conversation", "zero_shot"),
        ("Process this information", "data_analysis", "zero_shot"),
        
        # Edge cases
        ("Tell me a story about explaining code", None, "any"),  # Mixed signals
        ("Create a plan to analyze the data", None, "any"),  # Multiple intents
        ("What's the best way to solve problems?", None, "any"),  # Meta question
    ]
    
    print("Testing Hybrid Classifier")
    print("=" * 80)
    print(f"Rule confidence threshold: 0.85")
    print("=" * 80)
    
    for text, expected_intent, expected_method in test_cases:
        result = await hybrid_classifier.classify(text)
        
        # Check if expectations are met
        intent_match = expected_intent is None or result["intent"] == expected_intent
        method_match = expected_method == "any" or result["method"] == expected_method
        
        status = "✅" if intent_match and method_match else "⚠️"
        
        print(f"\n{status} Text: {text[:60]}...")
        print(f"   Intent: {result['intent']}")
        print(f"   Method: {result['method']}")
        print(f"   Confidence: {result['confidence']:.3f}")
        
        if result["method"] == "zero_shot":
            print(f"   Rule confidence: {result.get('rule_confidence', 0):.3f} (below threshold)")
            print(f"   Zero-shot model: {result.get('zero_shot_model', 'unknown')}")
            print(f"   Inference time: {result.get('inference_time_ms', 0):.1f}ms")
            
            # Show top 3 intents from zero-shot
            if result.get("all_scores"):
                print("   Top zero-shot scores:")
                sorted_scores = sorted(result["all_scores"].items(), key=lambda x: x[1], reverse=True)
                for intent, score in sorted_scores[:3]:
                    print(f"     - {intent}: {score:.3f}")
        else:
            print(f"   Rule patterns: {result.get('matched_patterns', [])[:3]}")
    
    # Test explanation generation
    print("\n" + "=" * 80)
    print("Example Classification Explanation:")
    print("=" * 80)
    
    ambiguous_text = "Help me understand how to approach this task"
    result = await hybrid_classifier.classify(ambiguous_text)
    explanation = hybrid_classifier.explain_classification(result)
    
    print(f"\nText: {ambiguous_text}")
    print("\n" + explanation)


async def test_confidence_thresholds():
    """Test different confidence thresholds"""
    rule_classifier = EnhancedRuleBasedClassifier()
    
    print("\n" + "=" * 80)
    print("Testing Confidence Threshold Impact")
    print("=" * 80)
    
    test_text = "I want to understand something"
    
    for threshold in [0.7, 0.8, 0.85, 0.9]:
        hybrid = HybridClassifier(
            rule_classifier=rule_classifier,
            rule_confidence_threshold=threshold
        )
        await hybrid.initialize()
        
        result = await hybrid.classify(test_text)
        print(f"\nThreshold: {threshold}")
        print(f"  Method used: {result['method']}")
        print(f"  Rule confidence: {result.get('rule_confidence', 0):.3f}")
        print(f"  Final confidence: {result['confidence']:.3f}")


if __name__ == "__main__":
    print("Running Hybrid Classifier Tests\n")
    
    # Run async tests
    asyncio.run(test_hybrid_classifier())
    asyncio.run(test_confidence_thresholds())