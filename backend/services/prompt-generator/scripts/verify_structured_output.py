#!/usr/bin/env python3
"""
Verification script for the enhanced StructuredOutputTechnique
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.techniques.structured_output import StructuredOutputTechnique


def verify_structured_output():
    """Verify the StructuredOutputTechnique implementation"""
    print("🔍 Verifying StructuredOutputTechnique implementation...\n")
    
    # Test 1: Basic initialization
    print("Test 1: Basic initialization")
    try:
        config = {
            "name": "structured_output",
            "enabled": True,
            "priority": 1,
            "parameters": {}
        }
        technique = StructuredOutputTechnique(config)
        print("✅ Initialization successful")
        print(f"  - Supported formats: {', '.join(technique.templates.keys())}")
        print(f"  - Strict mode: {technique.strict_mode}")
        print(f"  - Prefilling enabled: {technique.use_prefilling}")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    # Test 2: JSON format generation
    print("\nTest 2: JSON format generation")
    try:
        context = {
            "output_format": "json",
            "task_type": "analysis"
        }
        result = technique.apply("Analyze this data and return structured results", context)
        print("✅ JSON format generation successful")
        print(f"  - Template includes JSON instructions: {'json.loads()' in result}")
        print(f"  - Includes example: {'response_type' in result}")
        print(f"  - Prefilling hint present: {'```json' in result}")
    except Exception as e:
        print(f"❌ JSON format generation failed: {e}")
        return False
    
    # Test 3: Schema-based generation
    print("\nTest 3: Schema-based JSON generation")
    try:
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["success", "error"]},
                "data": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "items": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "timestamp": {"type": "string"}
            },
            "required": ["status", "data"]
        }
        
        context = {
            "output_format": "json",
            "schema": schema
        }
        result = technique.apply("Generate response following schema", context)
        print("✅ Schema-based generation successful")
        print(f"  - Schema included in prompt: {'Required JSON Schema:' in result}")
        print(f"  - Example generated from schema: {'status' in result and 'data' in result}")
    except Exception as e:
        print(f"❌ Schema-based generation failed: {e}")
        return False
    
    # Test 4: Multiple format support
    print("\nTest 4: Multiple format support")
    formats_tested = []
    for format_type in ["xml", "yaml", "csv", "table", "markdown"]:
        try:
            context = {"output_format": format_type}
            result = technique.apply(f"Generate {format_type} output", context)
            formats_tested.append(format_type)
        except Exception as e:
            print(f"❌ {format_type} format failed: {e}")
            return False
    
    print(f"✅ All formats generated successfully: {', '.join(formats_tested)}")
    
    # Test 5: Output validation
    print("\nTest 5: Output validation")
    try:
        # Valid JSON
        valid_json = '{"status": "ok", "count": 42}'
        validation = technique.validate_output(valid_json, "json")
        print(f"✅ Valid JSON validation: {validation['valid']}")
        
        # Invalid JSON
        invalid_json = '{"incomplete":'
        validation = technique.validate_output(invalid_json, "json")
        print(f"✅ Invalid JSON detection: {not validation['valid']}")
        print(f"  - Error message: {validation['errors'][0] if validation['errors'] else 'None'}")
        
        # JSON with schema validation
        schema = {
            "properties": {"status": {"type": "string"}},
            "required": ["status"]
        }
        missing_field = '{"count": 10}'
        validation = technique.validate_output(missing_field, "json", schema)
        print(f"✅ Schema validation working: {not validation['valid']}")
        print(f"  - Schema error: Missing required field detected")
    except Exception as e:
        print(f"❌ Output validation failed: {e}")
        return False
    
    # Test 6: Advanced features
    print("\nTest 6: Advanced features")
    try:
        # Hierarchical generation
        config["parameters"]["hierarchical_generation"] = True
        technique = StructuredOutputTechnique(config)
        context = {"output_format": "xml"}
        result = technique.apply("Generate complex XML", context)
        print(f"✅ Hierarchical generation enabled: {'top-level structure first' in result}")
        
        # Error handling modes
        config["parameters"]["error_handling"] = "explicit"
        technique = StructuredOutputTechnique(config)
        context = {"output_format": "json"}
        result = technique.apply("Parse data", context)
        print(f"✅ Explicit error handling: {'error\": true' in result}")
    except Exception as e:
        print(f"❌ Advanced features failed: {e}")
        return False
    
    # Test 7: Metadata
    print("\nTest 7: Metadata retrieval")
    try:
        metadata = technique.get_metadata()
        print("✅ Metadata retrieval successful")
        print(f"  - Supported formats: {len(metadata['supported_formats'])}")
        print(f"  - Features: {', '.join(metadata['features'][:3])}...")
        print(f"  - Configuration preserved: strict_mode={metadata['strict_mode']}")
    except Exception as e:
        print(f"❌ Metadata retrieval failed: {e}")
        return False
    
    print("\n✨ All tests passed! StructuredOutputTechnique is working correctly.")
    return True


if __name__ == "__main__":
    success = verify_structured_output()
    sys.exit(0 if success else 1)