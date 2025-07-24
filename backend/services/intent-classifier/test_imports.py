#!/usr/bin/env python3
"""Test script to verify module imports work correctly."""

import sys
print(f"Python path: {sys.path}")

try:
    # Test basic imports
    print("\n1. Testing basic app imports...")
    import app
    print("✓ app module imported")
    
    from app.models import classifier
    print("✓ app.models.classifier imported")
    
    # Test enhanced classifier import
    print("\n2. Testing enhanced classifier import...")
    from app.models.enhanced_classifier import EnhancedRuleBasedClassifier, AudienceLevel
    print("✓ EnhancedRuleBasedClassifier imported")
    print("✓ AudienceLevel imported")
    
    # Test zero shot classifier import
    print("\n3. Testing zero shot classifier import...")
    from app.models.zero_shot_classifier import HybridClassifier, ZeroShotModelType
    print("✓ HybridClassifier imported")
    print("✓ ZeroShotModelType imported")
    
    # Test instantiation
    print("\n4. Testing classifier instantiation...")
    enhanced = EnhancedRuleBasedClassifier()
    print("✓ EnhancedRuleBasedClassifier instantiated")
    
    # Test basic classification
    print("\n5. Testing basic classification...")
    test_text = "How do I implement a REST API in Python?"
    result = enhanced.classify(test_text)
    print(f"✓ Classification result: {result.intent} (confidence: {result.confidence:.2f})")
    
    print("\n✅ All imports and basic functionality working correctly!")
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)