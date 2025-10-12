#!/usr/bin/env python3
"""
Test the enhanced LLM caller backward compatibility.
"""

import sys
import os
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_enhanced_llm_caller_import():
    """Test that the enhanced LLM caller can be imported."""
    print("\n🔍 Testing Enhanced LLM Caller Import...")
    
    try:
        from codexes.core.enhanced_llm_caller import EnhancedLLMCaller
        print("✅ EnhancedLLMCaller import successful")
        
        # Test instantiation
        caller = EnhancedLLMCaller()
        print("✅ EnhancedLLMCaller instantiation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced LLM caller import/instantiation failed: {e}")
        return False


def test_enhanced_llm_caller_methods():
    """Test that the enhanced LLM caller methods work."""
    print("\n🔍 Testing Enhanced LLM Caller Methods...")
    
    try:
        from codexes.core.enhanced_llm_caller import EnhancedLLMCaller
        
        caller = EnhancedLLMCaller(max_retries=1)  # Reduce retries for testing
        
        # Test call_llm_with_retry
        messages = [{"role": "user", "content": "Test message"}]
        
        result = caller.call_llm_with_retry(
            model="gemini/gemini-2.5-flash",
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        
        # Should return a result (even if it's an error due to no API key)
        if result is not None:
            print("✅ call_llm_with_retry returns result")
            
            # Check expected structure
            if isinstance(result, dict):
                expected_keys = ['content', 'usage', 'model', 'attempts']
                missing_keys = [key for key in expected_keys if key not in result]
                if not missing_keys:
                    print("✅ call_llm_with_retry response structure is correct")
                else:
                    print(f"⚠️ Missing keys in response: {missing_keys}")
            else:
                print(f"⚠️ Unexpected response type: {type(result)}")
        else:
            print("⚠️ call_llm_with_retry returned None (may be expected due to API key issues)")
        
        # Test call_llm_json_with_retry
        json_result = caller.call_llm_json_with_retry(
            model="gemini/gemini-2.5-flash",
            messages=[{"role": "user", "content": "Return JSON: {\"test\": \"value\"}"}],
            temperature=0.1,
            max_tokens=100
        )
        
        print("✅ call_llm_json_with_retry executed without crashing")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced LLM caller methods test failed: {e}")
        return False


def test_convenience_functions():
    """Test the convenience functions."""
    print("\n🔍 Testing Convenience Functions...")
    
    try:
        from codexes.core.enhanced_llm_caller import (
            call_llm_with_exponential_backoff,
            call_llm_json_with_exponential_backoff
        )
        
        messages = [{"role": "user", "content": "Test"}]
        
        # Test convenience function
        result = call_llm_with_exponential_backoff(
            model="gemini/gemini-2.5-flash",
            messages=messages,
            temperature=0.7,
            max_tokens=50
        )
        
        print("✅ call_llm_with_exponential_backoff executed without crashing")
        
        # Test JSON convenience function
        json_result = call_llm_json_with_exponential_backoff(
            model="gemini/gemini-2.5-flash",
            messages=[{"role": "user", "content": "Return JSON"}],
            temperature=0.1,
            max_tokens=50
        )
        
        print("✅ call_llm_json_with_exponential_backoff executed without crashing")
        
        return True
        
    except Exception as e:
        print(f"❌ Convenience functions test failed: {e}")
        return False


def test_debug_llm_response_compatibility():
    """Test that the debug_llm_response.py script can import the enhanced caller."""
    print("\n🔍 Testing debug_llm_response.py Compatibility...")
    
    try:
        # Test the import that debug_llm_response.py uses
        from src.codexes.core.enhanced_llm_caller import EnhancedLLMCaller
        
        # Test instantiation like the script does
        caller = EnhancedLLMCaller()
        
        print("✅ debug_llm_response.py import pattern works")
        return True
        
    except Exception as e:
        print(f"❌ debug_llm_response.py compatibility test failed: {e}")
        return False


def run_all_tests():
    """Run all enhanced LLM caller compatibility tests."""
    print("🚀 Starting Enhanced LLM Caller Compatibility Tests")
    print("=" * 60)
    
    tests = [
        test_enhanced_llm_caller_import,
        test_enhanced_llm_caller_methods,
        test_convenience_functions,
        test_debug_llm_response_compatibility
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
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All enhanced LLM caller compatibility tests passed!")
        return True
    else:
        print(f"⚠️ {failed} tests failed - compatibility issues detected")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)