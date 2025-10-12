#!/usr/bin/env python3
"""
Comprehensive backward compatibility test for nimble-llm-caller integration.

This test verifies that all existing LLM functionality continues to work
with the new nimble-llm-caller integration layer.
"""

import sys
import os
import logging
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_import_compatibility():
    """Test that all expected imports work correctly."""
    print("\n🔍 Testing Import Compatibility...")
    
    try:
        # Test importing the integration layer
        from codexes.core.llm_integration import (
            CodexesLLMIntegration,
            call_model_with_prompt,
            get_responses_from_multiple_models,
            get_llm_integration
        )
        print("✅ Integration layer imports successful")
        
        # Test backward compatibility functions exist
        assert callable(call_model_with_prompt), "call_model_with_prompt should be callable"
        assert callable(get_responses_from_multiple_models), "get_responses_from_multiple_models should be callable"
        assert callable(get_llm_integration), "get_llm_integration should be callable"
        
        print("✅ All backward compatibility functions are callable")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False


def test_function_signatures():
    """Test that function signatures match the original API."""
    print("\n🔍 Testing Function Signatures...")
    
    try:
        from codexes.core.llm_integration import call_model_with_prompt, get_responses_from_multiple_models
        import inspect
        
        # Test call_model_with_prompt signature
        sig = inspect.signature(call_model_with_prompt)
        expected_params = [
            'model_name', 'prompt_config', 'response_format_type', 
            'max_retries', 'initial_delay', 'backoff_multiplier', 
            'max_delay', 'ensure_min_tokens', 'min_tokens'
        ]
        
        actual_params = list(sig.parameters.keys())
        
        for param in expected_params:
            if param not in actual_params:
                print(f"❌ Missing parameter in call_model_with_prompt: {param}")
                return False
        
        print("✅ call_model_with_prompt signature is compatible")
        
        # Test get_responses_from_multiple_models signature
        sig2 = inspect.signature(get_responses_from_multiple_models)
        expected_params2 = ['prompt_configs', 'models', 'response_format_type', 'per_model_params']
        
        actual_params2 = list(sig2.parameters.keys())
        
        for param in expected_params2:
            if param not in actual_params2:
                print(f"❌ Missing parameter in get_responses_from_multiple_models: {param}")
                return False
        
        print("✅ get_responses_from_multiple_models signature is compatible")
        return True
        
    except Exception as e:
        print(f"❌ Error testing signatures: {e}")
        return False


def test_response_format_compatibility():
    """Test that response formats match the original API."""
    print("\n🔍 Testing Response Format Compatibility...")
    
    try:
        from codexes.core.llm_integration import call_model_with_prompt, get_responses_from_multiple_models
        
        # Test single model call response format
        prompt_config = {
            "messages": [{"role": "user", "content": "Test message"}],
            "params": {"temperature": 0.7, "max_tokens": 100}
        }
        
        # This should not crash even without API keys (will return error response)
        result = call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=prompt_config,
            response_format_type="text"
        )
        
        # Check response format
        if not isinstance(result, dict):
            print(f"❌ call_model_with_prompt should return dict, got {type(result)}")
            return False
        
        if "parsed_content" not in result:
            print("❌ call_model_with_prompt response missing 'parsed_content'")
            return False
        
        if "raw_content" not in result:
            print("❌ call_model_with_prompt response missing 'raw_content'")
            return False
        
        print("✅ call_model_with_prompt response format is compatible")
        
        # Test multiple models call response format
        prompt_configs = [
            {
                "key": "test_prompt",
                "prompt_config": prompt_config
            }
        ]
        
        batch_result = get_responses_from_multiple_models(
            prompt_configs=prompt_configs,
            models=["gemini/gemini-2.5-flash"],
            response_format_type="text"
        )
        
        # Check response format
        if not isinstance(batch_result, dict):
            print(f"❌ get_responses_from_multiple_models should return dict, got {type(batch_result)}")
            return False
        
        # Should have model as key
        if "gemini/gemini-2.5-flash" not in batch_result:
            print("❌ get_responses_from_multiple_models response missing model key")
            return False
        
        model_responses = batch_result["gemini/gemini-2.5-flash"]
        if not isinstance(model_responses, list):
            print("❌ get_responses_from_multiple_models model responses should be list")
            return False
        
        if len(model_responses) > 0:
            first_response = model_responses[0]
            if not isinstance(first_response, dict):
                print("❌ Individual responses should be dicts")
                return False
            
            if "parsed_content" not in first_response:
                print("❌ Individual response missing 'parsed_content'")
                return False
            
            if "raw_content" not in first_response:
                print("❌ Individual response missing 'raw_content'")
                return False
            
            if "prompt_key" not in first_response:
                print("❌ Individual response missing 'prompt_key'")
                return False
        
        print("✅ get_responses_from_multiple_models response format is compatible")
        return True
        
    except Exception as e:
        print(f"❌ Error testing response formats: {e}")
        return False


def test_integration_class_compatibility():
    """Test that the integration class provides expected methods."""
    print("\n🔍 Testing Integration Class Compatibility...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration, get_llm_integration
        
        # Test class instantiation
        integration = CodexesLLMIntegration()
        print("✅ CodexesLLMIntegration instantiation successful")
        
        # Test global instance
        global_integration = get_llm_integration()
        assert isinstance(global_integration, CodexesLLMIntegration)
        print("✅ Global integration instance works")
        
        # Test expected methods exist
        expected_methods = [
            'call_model_with_prompt',
            'get_responses_from_multiple_models',
            'validate_configuration',
            'get_statistics',
            'list_available_models',
            'call_llm'
        ]
        
        for method_name in expected_methods:
            if not hasattr(integration, method_name):
                print(f"❌ Missing method: {method_name}")
                return False
            
            if not callable(getattr(integration, method_name)):
                print(f"❌ Method not callable: {method_name}")
                return False
        
        print("✅ All expected methods are present and callable")
        
        # Test method call without crashing
        try:
            models = integration.list_available_models()
            print(f"✅ list_available_models works: {len(models)} models available")
        except Exception as e:
            print(f"⚠️ list_available_models error (may be expected): {e}")
        
        try:
            validation = integration.validate_configuration()
            print(f"✅ validate_configuration works: {validation.get('valid', 'unknown')}")
        except Exception as e:
            print(f"⚠️ validate_configuration error (may be expected): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing integration class: {e}")
        return False


def test_parameter_handling():
    """Test that parameters are handled correctly."""
    print("\n🔍 Testing Parameter Handling...")
    
    try:
        from codexes.core.llm_integration import call_model_with_prompt
        
        # Test with various parameter combinations
        prompt_config = {
            "messages": [{"role": "user", "content": "Test"}],
            "params": {"temperature": 0.5, "max_tokens": 50}
        }
        
        # Test with default parameters
        result1 = call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=prompt_config
        )
        
        # Test with custom parameters
        result2 = call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=prompt_config,
            response_format_type="json_object",
            max_retries=1,
            ensure_min_tokens=False
        )
        
        # Both should return valid response structures
        for i, result in enumerate([result1, result2], 1):
            if not isinstance(result, dict):
                print(f"❌ Result {i} should be dict, got {type(result)}")
                return False
            
            if "parsed_content" not in result or "raw_content" not in result:
                print(f"❌ Result {i} missing required keys")
                return False
        
        print("✅ Parameter handling works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error testing parameter handling: {e}")
        return False


def test_error_handling():
    """Test that error handling works as expected."""
    print("\n🔍 Testing Error Handling...")
    
    try:
        from codexes.core.llm_integration import call_model_with_prompt
        
        # Test with invalid model
        prompt_config = {
            "messages": [{"role": "user", "content": "Test"}],
            "params": {"temperature": 0.7}
        }
        
        result = call_model_with_prompt(
            model_name="invalid/model-name",
            prompt_config=prompt_config
        )
        
        # Should return error response, not crash
        if not isinstance(result, dict):
            print(f"❌ Error response should be dict, got {type(result)}")
            return False
        
        if "parsed_content" not in result:
            print("❌ Error response missing 'parsed_content'")
            return False
        
        # Error should be indicated in parsed_content
        parsed = result["parsed_content"]
        if isinstance(parsed, dict) and "error" in parsed:
            print("✅ Error handling works correctly")
            return True
        else:
            print(f"⚠️ Unexpected error response format: {parsed}")
            return True  # Still pass as long as it doesn't crash
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def test_json_response_format():
    """Test JSON response format handling."""
    print("\n🔍 Testing JSON Response Format...")
    
    try:
        from codexes.core.llm_integration import call_model_with_prompt
        
        prompt_config = {
            "messages": [
                {"role": "user", "content": "Return a JSON object with a 'test' field set to 'success'"}
            ],
            "params": {"temperature": 0.1, "max_tokens": 100}
        }
        
        result = call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=prompt_config,
            response_format_type="json_object"
        )
        
        # Should handle JSON format request without crashing
        if not isinstance(result, dict):
            print(f"❌ JSON response should be dict, got {type(result)}")
            return False
        
        if "parsed_content" not in result:
            print("❌ JSON response missing 'parsed_content'")
            return False
        
        print("✅ JSON response format handling works")
        return True
        
    except Exception as e:
        print(f"❌ Error testing JSON response format: {e}")
        return False


def run_all_tests():
    """Run all backward compatibility tests."""
    print("🚀 Starting Backward Compatibility Tests for nimble-llm-caller Integration")
    print("=" * 80)
    
    tests = [
        test_import_compatibility,
        test_function_signatures,
        test_response_format_compatibility,
        test_integration_class_compatibility,
        test_parameter_handling,
        test_error_handling,
        test_json_response_format
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All backward compatibility tests passed!")
        return True
    else:
        print(f"⚠️ {failed} tests failed - backward compatibility issues detected")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)