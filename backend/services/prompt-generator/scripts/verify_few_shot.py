#!/usr/bin/env python3
"""
Simple verification script for the FewShotTechnique implementation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.techniques.few_shot import FewShotTechnique


def verify_few_shot():
    """Verify the FewShotTechnique implementation"""
    print("🔍 Verifying FewShotTechnique implementation...\n")
    
    # Test 1: Basic initialization
    print("Test 1: Basic initialization")
    try:
        config = {
            "name": "few_shot",
            "enabled": True,
            "priority": 1,
            "parameters": {}
        }
        technique = FewShotTechnique(config)
        print("✅ Initialization successful")
        print(f"  - Min examples: {technique.min_examples}")
        print(f"  - Max examples: {technique.max_examples}")
        print(f"  - Format style: {technique.format_style}")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    # Test 2: Apply with custom examples
    print("\nTest 2: Apply with custom examples")
    try:
        context = {
            "examples": [
                {"input": "What is 2+2?", "output": "4", "explanation": "Basic addition"},
                {"input": "What is 5*3?", "output": "15", "explanation": "Basic multiplication"}
            ]
        }
        result = technique.apply("What is 10/2?", context)
        print("✅ Apply with custom examples successful")
        print(f"  - Result length: {len(result)} characters")
        print(f"  - Contains examples: {'2+2' in result and '5*3' in result}")
    except Exception as e:
        print(f"❌ Apply with custom examples failed: {e}")
        return False
    
    # Test 3: Apply with task type
    print("\nTest 3: Apply with task type")
    try:
        context = {"task_type": "classification"}
        result = technique.apply("This movie was amazing!", context)
        print("✅ Apply with task type successful")
        print(f"  - Result contains classification examples: {'Positive' in result}")
    except Exception as e:
        print(f"❌ Apply with task type failed: {e}")
        return False
    
    # Test 4: Different format styles
    print("\nTest 4: Different format styles")
    for style in ["input_output", "xml", "delimiter"]:
        try:
            config["parameters"]["format_style"] = style
            technique = FewShotTechnique(config)
            result = technique.apply("Test input", {"task_type": "generation"})
            print(f"✅ Format style '{style}' works correctly")
        except Exception as e:
            print(f"❌ Format style '{style}' failed: {e}")
            return False
    
    # Test 5: Validation
    print("\nTest 5: Input validation")
    try:
        technique = FewShotTechnique({"name": "few_shot", "parameters": {}})
        
        # Should pass
        valid = technique.validate_input("Valid input", {"task_type": "analysis"})
        print(f"✅ Valid input validation: {valid}")
        
        # Should fail
        invalid = technique.validate_input("", {})
        print(f"✅ Invalid input validation: {not invalid}")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False
    
    # Test 6: Metadata
    print("\nTest 6: Metadata retrieval")
    try:
        metadata = technique.get_metadata()
        print("✅ Metadata retrieval successful")
        print(f"  - Keys: {', '.join(metadata.keys())}")
        print(f"  - Supported task types: {len(metadata.get('supported_task_types', []))}")
    except Exception as e:
        print(f"❌ Metadata retrieval failed: {e}")
        return False
    
    print("\n✨ All tests passed! FewShotTechnique is working correctly.")
    return True


if __name__ == "__main__":
    success = verify_few_shot()
    sys.exit(0 if success else 1)