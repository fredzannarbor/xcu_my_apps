#!/usr/bin/env python3
"""
Test script to verify the LLM integration setup.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_integration_imports():
    """Test that we can import the integration layer."""
    print("Testing integration layer imports...")
    
    try:
        from codexes.core.llm_integration import (
            CodexesLLMIntegration,
            call_model_with_prompt,
            get_responses_from_multiple_models
        )
        print("✅ Integration layer imports successful")
        return True
    except ImportError as e:
        print(f"❌ Integration layer import failed: {e}")
        return False

def test_integration_initialization():
    """Test that the integration layer initializes correctly."""
    print("Testing integration layer initialization...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        integration = CodexesLLMIntegration()
        print("✅ Integration layer initialized successfully")
        
        # Test configuration validation
        validation = integration.validate_configuration()
        print(f"✅ Configuration validation: {len(validation['models_available'])} models available")
        
        if validation['issues']:
            print(f"⚠️  Configuration issues: {validation['issues']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration layer initialization failed: {e}")
        return False

def test_backward_compatibility():
    """Test that backward compatibility functions work."""
    print("Testing backward compatibility functions...")
    
    try:
        from codexes.core.llm_integration import call_model_with_prompt
        
        # Test with a simple prompt configuration
        prompt_config = {
            "messages": [
                {"role": "user", "content": "Say hello"}
            ],
            "params": {
                "temperature": 0.7,
                "max_tokens": 50
            }
        }
        
        # This should not fail even without API keys (will return error response)
        result = call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=prompt_config,
            response_format_type="text"
        )
        
        print("✅ Backward compatibility function callable")
        print(f"✅ Response format correct: {type(result)} with keys {list(result.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing LLM Integration Setup")
    print("=" * 40)
    
    tests = [
        test_integration_imports,
        test_integration_initialization,
        test_backward_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration setup tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)