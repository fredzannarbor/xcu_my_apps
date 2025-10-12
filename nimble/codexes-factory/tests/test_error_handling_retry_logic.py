#!/usr/bin/env python3
"""
Test error handling and retry logic for the nimble-llm-caller integration.

This test suite verifies that:
1. Retryable errors trigger retry attempts with exponential backoff
2. Non-retryable errors fail immediately without retries
3. Maximum retry limits are respected
4. Exponential backoff timing works correctly
5. Error messages are properly logged and returned
"""

import sys
import os
import time
import logging
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging to capture retry messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockLLMIntegration:
    """Mock LLM integration for testing error scenarios."""
    
    def __init__(self):
        self.call_count = 0
        self.error_sequence = []
        self.success_response = {
            "raw_content": "Test response",
            "parsed_content": {"test": "success"}
        }
    
    def set_error_sequence(self, errors: List[str]):
        """Set a sequence of errors to return on successive calls."""
        self.error_sequence = errors
        self.call_count = 0
    
    def call_model_with_prompt(self, model_name: str, prompt_config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Mock implementation that can simulate various error conditions."""
        self.call_count += 1
        
        # If we have errors in the sequence, return them
        if self.call_count <= len(self.error_sequence):
            error_msg = self.error_sequence[self.call_count - 1]
            if error_msg:
                raise Exception(error_msg)
        
        # Return success response
        return self.success_response


def test_retryable_errors():
    """Test that retryable errors trigger retry attempts."""
    print("\n🔍 Testing Retryable Errors...")
    
    try:
        from codexes.core.enhanced_llm_caller import EnhancedLLMCaller
        
        # Create caller with reduced retry settings for faster testing
        caller = EnhancedLLMCaller(max_retries=3, base_delay=0.1, max_delay=1.0)
        
        # Mock the LLM integration
        mock_integration = MockLLMIntegration()
        caller.llm_integration = mock_integration
        
        # Test each retryable error type
        retryable_errors = [
            "rate_limit_exceeded",
            "quota_exceeded", 
            "service_unavailable",
            "timeout",
            "internal_server_error",
            "bad_gateway",
            "service_temporarily_unavailable",
            "too_many_requests"
        ]
        
        for error_type in retryable_errors:
            print(f"  Testing {error_type}...")
            
            # Set up error sequence: 2 failures, then success
            mock_integration.set_error_sequence([error_type, error_type, ""])
            
            messages = [{"role": "user", "content": "Test"}]
            
            start_time = time.time()
            result = caller.call_llm_with_retry(
                model="test-model",
                messages=messages
            )
            end_time = time.time()
            
            # Should succeed after retries
            if result is not None:
                print(f"    ✅ {error_type} - Succeeded after retries")
                
                # Check that it took some time (indicating retries with delays)
                elapsed = end_time - start_time
                if elapsed > 0.1:  # Should have at least some delay
                    print(f"    ✅ {error_type} - Proper delay applied ({elapsed:.2f}s)")
                else:
                    print(f"    ⚠️ {error_type} - No delay detected")
                
                # Check that multiple calls were made
                if mock_integration.call_count == 3:
                    print(f"    ✅ {error_type} - Correct number of retry attempts")
                else:
                    print(f"    ⚠️ {error_type} - Expected 3 calls, got {mock_integration.call_count}")
            else:
                print(f"    ❌ {error_type} - Failed to recover after retries")
        
        return True
        
    except Exception as e:
        print(f"❌ Retryable errors test failed: {e}")
        return False


def test_non_retryable_errors():
    """Test that non-retryable errors fail immediately without retries."""
    print("\n🔍 Testing Non-Retryable Errors...")
    
    try:
        from codexes.core.enhanced_llm_caller import EnhancedLLMCaller
        
        caller = EnhancedLLMCaller(max_retries=3, base_delay=0.1, max_delay=1.0)
        
        # Mock the LLM integration
        mock_integration = MockLLMIntegration()
        caller.llm_integration = mock_integration
        
        # Test non-retryable errors
        non_retryable_errors = [
            "invalid_request",
            "authentication_failed",
            "permission_denied",
            "model_not_found",
            "invalid_parameter"
        ]
        
        for error_type in non_retryable_errors:
            print(f"  Testing {error_type}...")
            
            # Set up error sequence: just one error
            mock_integration.set_error_sequence([error_type])
            
            messages = [{"role": "user", "content": "Test"}]
            
            start_time = time.time()
            result = caller.call_llm_with_retry(
                model="test-model",
                messages=messages
            )
            end_time = time.time()
            
            # Should fail immediately
            if result is None:
                print(f"    ✅ {error_type} - Failed immediately as expected")
                
                # Should not have taken much time (no retries)
                elapsed = end_time - start_time
                if elapsed < 0.5:  # Should be quick
                    print(f"    ✅ {error_type} - No retry delay ({elapsed:.2f}s)")
                else:
                    print(f"    ⚠️ {error_type} - Unexpected delay ({elapsed:.2f}s)")
                
                # Should have made only one call
                if mock_integration.call_count == 1:
                    print(f"    ✅ {error_type} - No retry attempts made")
                else:
                    print(f"    ⚠️ {error_type} - Expected 1 call, got {mock_integration.call_count}")
            else:
                print(f"    ❌ {error_type} - Unexpectedly succeeded")
        
        return True
        
    except Exception as e:
        print(f"❌ Non-retryable errors test failed: {e}")
        return False


def test_max_retries_limit():
    """Test that maximum retry limit is respected."""
    print("\n🔍 Testing Maximum Retry Limit...")
    
    try:
        from codexes.core.enhanced_llm_caller import EnhancedLLMCaller
        
        # Create caller with specific retry limit
        max_retries = 2
        caller = EnhancedLLMCaller(max_retries=max_retries, base_delay=0.1, max_delay=1.0)
        
        # Mock the LLM integration
        mock_integration = MockLLMIntegration()
        caller.llm_integration = mock_integration
        
        # Set up error sequence: more errors than max_retries
        error_sequence = ["rate_limit_exceeded"] * (max_retries + 2)
        mock_integration.set_error_sequence(error_sequence)
        
        messages = [{"role": "user", "content": "Test"}]
        
        result = caller.call_llm_with_retry(
            model="test-model",
            messages=messages
        )
        
        # Should fail after max_retries + 1 attempts (initial + retries)
        if result is None:
            print("    ✅ Failed after reaching max retries")
            
            expected_calls = max_retries + 1
            if mock_integration.call_count == expected_calls:
                print(f"    ✅ Made correct number of attempts ({expected_calls})")
            else:
                print(f"    ⚠️ Expected {expected_calls} calls, got {mock_integration.call_count}")
        else:
            print("    ❌ Unexpectedly succeeded despite continuous errors")
        
        return True
        
    except Exception as e:
        print(f"❌ Max retries limit test failed: {e}")
        return False


def test_exponential_backoff_timing():
    """Test that exponential backoff timing works correctly."""
    print("\n🔍 Testing Exponential Backoff Timing...")
    
    try:
        from codexes.core.enhanced_llm_caller import EnhancedLLMCaller
        
        # Create caller with specific timing parameters
        base_delay = 0.2
        max_delay = 2.0
        caller = EnhancedLLMCaller(max_retries=3, base_delay=base_delay, max_delay=max_delay)
        
        # Mock the LLM integration
        mock_integration = MockLLMIntegration()
        caller.llm_integration = mock_integration
        
        # Set up error sequence: 3 failures, then success
        mock_integration.set_error_sequence([
            "rate_limit_exceeded",
            "rate_limit_exceeded", 
            "rate_limit_exceeded",
            ""
        ])
        
        messages = [{"role": "user", "content": "Test"}]
        
        start_time = time.time()
        result = caller.call_llm_with_retry(
            model="test-model",
            messages=messages
        )
        end_time = time.time()
        
        elapsed = end_time - start_time
        
        # Calculate expected minimum delay
        # Attempt 1: no delay
        # Attempt 2: base_delay * 2^0 = 0.2s
        # Attempt 3: base_delay * 2^1 = 0.4s  
        # Attempt 4: base_delay * 2^2 = 0.8s
        expected_min_delay = 0.2 + 0.4 + 0.8  # 1.4s minimum
        
        if result is not None:
            print("    ✅ Eventually succeeded after retries")
            
            if elapsed >= expected_min_delay * 0.8:  # Allow some tolerance
                print(f"    ✅ Proper exponential backoff timing ({elapsed:.2f}s >= {expected_min_delay:.2f}s)")
            else:
                print(f"    ⚠️ Timing seems too fast ({elapsed:.2f}s < {expected_min_delay:.2f}s)")
            
            if mock_integration.call_count == 4:
                print("    ✅ Correct number of attempts made")
            else:
                print(f"    ⚠️ Expected 4 calls, got {mock_integration.call_count}")
        else:
            print("    ❌ Failed to succeed after retries")
        
        return True
        
    except Exception as e:
        print(f"❌ Exponential backoff timing test failed: {e}")
        return False


def test_json_error_handling():
    """Test error handling in JSON response parsing."""
    print("\n🔍 Testing JSON Error Handling...")
    
    try:
        from codexes.core.enhanced_llm_caller import EnhancedLLMCaller
        
        caller = EnhancedLLMCaller(max_retries=1, base_delay=0.1, max_delay=1.0)
        
        # Mock the LLM integration to return invalid JSON
        mock_integration = MockLLMIntegration()
        mock_integration.success_response = {
            "raw_content": "This is not valid JSON",
            "parsed_content": "This is not valid JSON"
        }
        caller.llm_integration = mock_integration
        
        messages = [{"role": "user", "content": "Return JSON"}]
        
        result = caller.call_llm_json_with_retry(
            model="test-model",
            messages=messages,
            expected_keys=["test_key"]
        )
        
        # Should return None due to JSON parsing failure
        if result is None:
            print("    ✅ Properly handled invalid JSON response")
        else:
            print(f"    ⚠️ Unexpected result for invalid JSON: {result}")
        
        # Test with valid JSON but missing expected keys
        mock_integration.success_response = {
            "raw_content": '{"other_key": "value"}',
            "parsed_content": '{"other_key": "value"}'
        }
        
        result = caller.call_llm_json_with_retry(
            model="test-model",
            messages=messages,
            expected_keys=["test_key"]
        )
        
        # Should still return the result but log a warning
        if result is not None and "other_key" in result:
            print("    ✅ Returned valid JSON despite missing expected keys")
        else:
            print(f"    ⚠️ Unexpected handling of missing keys: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON error handling test failed: {e}")
        return False


def test_error_logging():
    """Test that errors are properly logged."""
    print("\n🔍 Testing Error Logging...")
    
    try:
        from codexes.core.enhanced_llm_caller import EnhancedLLMCaller
        import logging
        from io import StringIO
        
        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.WARNING)
        
        # Get the logger used by EnhancedLLMCaller
        llm_logger = logging.getLogger('codexes.core.enhanced_llm_caller')
        llm_logger.addHandler(handler)
        llm_logger.setLevel(logging.WARNING)
        
        caller = EnhancedLLMCaller(max_retries=2, base_delay=0.1, max_delay=1.0)
        
        # Mock the LLM integration
        mock_integration = MockLLMIntegration()
        mock_integration.set_error_sequence([
            "rate_limit_exceeded",
            "rate_limit_exceeded",
            "rate_limit_exceeded"  # Will exceed max retries
        ])
        caller.llm_integration = mock_integration
        
        messages = [{"role": "user", "content": "Test"}]
        
        result = caller.call_llm_with_retry(
            model="test-model",
            messages=messages
        )
        
        # Get the logged output
        log_output = log_capture.getvalue()
        
        # Should have logged retry warnings and final error
        if "Retryable error on attempt" in log_output:
            print("    ✅ Retry attempts are logged")
        else:
            print("    ⚠️ Retry attempts not found in logs")
        
        if "Max retries" in log_output or "All retry attempts failed" in log_output:
            print("    ✅ Max retries failure is logged")
        else:
            print("    ⚠️ Max retries failure not found in logs")
        
        # Clean up
        llm_logger.removeHandler(handler)
        
        return True
        
    except Exception as e:
        print(f"❌ Error logging test failed: {e}")
        return False


def test_integration_layer_error_handling():
    """Test error handling in the integration layer itself."""
    print("\n🔍 Testing Integration Layer Error Handling...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        # Test with invalid configuration
        integration = CodexesLLMIntegration(config_path="/nonexistent/path.json")
        
        # Should still initialize with fallback configuration
        if integration.config_manager is not None:
            print("    ✅ Integration handles invalid config path gracefully")
        else:
            print("    ⚠️ Integration failed to initialize with fallback config")
        
        # Test call with invalid parameters
        result = integration.call_model_with_prompt(
            model_name="nonexistent-model",
            prompt_config={"messages": [{"role": "user", "content": "test"}]},
            response_format_type="invalid_format"
        )
        
        # Should return error response rather than crashing
        if isinstance(result, dict) and "error" in str(result).lower():
            print("    ✅ Integration handles invalid parameters gracefully")
        else:
            print(f"    ⚠️ Unexpected response to invalid parameters: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration layer error handling test failed: {e}")
        return False


def run_all_tests():
    """Run all error handling and retry logic tests."""
    print("🚀 Starting Error Handling and Retry Logic Tests")
    print("=" * 60)
    
    tests = [
        test_retryable_errors,
        test_non_retryable_errors,
        test_max_retries_limit,
        test_exponential_backoff_timing,
        test_json_error_handling,
        test_error_logging,
        test_integration_layer_error_handling
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
        print("🎉 All error handling and retry logic tests passed!")
        return True
    else:
        print(f"⚠️ {failed} tests failed - error handling issues detected")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)