#!/usr/bin/env python3
"""Test DistilBERT integration"""

import asyncio
import pytest
from pathlib import Path

from app.models.classifier import IntentClassifier


@pytest.mark.asyncio
async def test_distilbert_loads():
    """Test that DistilBERT model loads successfully"""
    classifier = IntentClassifier()
    await classifier.initialize_model()
    
    # Check if DistilBERT loaded (not just fallback)
    assert classifier._initialized
    
    # If model exists, it should be loaded
    model_path = Path("../../../ml-pipeline/models/distilbert_intent_classifier").resolve()
    if model_path.exists():
        assert classifier.model is not None or classifier.hybrid_classifier is not None
    
    await classifier.cleanup()


@pytest.mark.asyncio
async def test_distilbert_classification():
    """Test DistilBERT classification works"""
    classifier = IntentClassifier()
    await classifier.initialize_model()
    
    test_cases = [
        ("Write a Python function to sort a list", "code_generation"),
        ("What is the capital of France?", "question_answering"),
        ("Translate this to Spanish: Hello world", "translation"),
    ]
    
    for prompt, expected_intent in test_cases:
        result = await classifier.classify(prompt)
        
        assert "intent" in result
        assert "confidence" in result
        assert "complexity" in result
        assert "suggested_techniques" in result
        assert "classification_method" in result
        
        # Check confidence is reasonable
        assert 0.0 <= result["confidence"] <= 1.0
        
        # Check method is distilbert if model loaded
        if classifier.model is not None:
            assert result["classification_method"] == "distilbert"
    
    await classifier.cleanup()


@pytest.mark.asyncio 
async def test_distilbert_fallback():
    """Test fallback works if DistilBERT not available"""
    classifier = IntentClassifier()
    
    # Temporarily set model to None to test fallback
    await classifier.initialize_model()
    original_model = classifier.model
    classifier.model = None
    classifier.tokenizer = None
    
    result = await classifier.classify("What is machine learning?")
    
    # Should still get a valid result from fallback
    assert "intent" in result
    assert "confidence" in result
    assert result["classification_method"] != "distilbert"
    
    # Restore
    classifier.model = original_model
    await classifier.cleanup()


if __name__ == "__main__":
    # Run basic integration test
    async def main():
        classifier = IntentClassifier()
        print("Initializing classifier...")
        await classifier.initialize_model()
        
        test_prompts = [
            "Write a Python function to sort a list",
            "What is the capital of France?",
            "Translate this to Spanish: Hello world",
        ]
        
        for prompt in test_prompts:
            print(f"\nPrompt: {prompt}")
            result = await classifier.classify(prompt)
            print(f"  Intent: {result['intent']}")
            print(f"  Confidence: {result['confidence']:.3f}")
            print(f"  Method: {result.get('classification_method', 'unknown')}")
        
        await classifier.cleanup()
        print("\nTest complete!")
    
    asyncio.run(main())