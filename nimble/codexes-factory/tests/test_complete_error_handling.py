#!/usr/bin/env python3
"""
Complete test suite for error handling and retry logic in the nimble-llm-caller integration.

This comprehensive test suite runs all error handling tests to verify:
1. Error handling and retry logic
2. Configuration validation and model selection
3. Prompt loading and substitution
4. Integration layer robustness
"""

import sys
import os
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_test_suite(test_file: str, description: str) -> bool:
    """Run a test suite and return success status."""
    print(f"\n🚀 Running {description}")
    print("=" * 80)
    
    try:
        # Run the test file using uv run python
        result = subprocess.run(
            ["uv", "run", "python", test_file],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Check if the test passed
        if result.returncode == 0:
            print(f"✅ {description} - ALL TESTS PASSED")
            return True
        else:
            print(f"❌ {description} - TESTS FAILED (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TESTS TIMED OUT")
        return False
    except Exception as e:
        print(f"💥 {description} - TEST EXECUTION FAILED: {e}")
        return False


def main():
    """Run all error handling and retry logic tests."""
    print("🎯 Complete Error Handling and Retry Logic Test Suite")
    print("=" * 80)
    print("This test suite verifies the nimble-llm-caller integration's")
    print("error handling, retry logic, configuration, and prompt handling.")
    print("=" * 80)
    
    # Define test suites to run
    test_suites = [
        {
            "file": "test_error_handling_retry_logic.py",
            "description": "Error Handling and Retry Logic Tests"
        },
        {
            "file": "test_configuration_validation.py", 
            "description": "Configuration Validation Tests"
        },
        {
            "file": "test_prompt_loading_substitution.py",
            "description": "Prompt Loading and Substitution Tests"
        }
    ]
    
    # Track results
    total_suites = len(test_suites)
    passed_suites = 0
    failed_suites = 0
    
    # Run each test suite
    for suite in test_suites:
        if run_test_suite(suite["file"], suite["description"]):
            passed_suites += 1
        else:
            failed_suites += 1
    
    # Print final summary
    print("\n" + "=" * 80)
    print("📊 FINAL TEST RESULTS")
    print("=" * 80)
    print(f"Total Test Suites: {total_suites}")
    print(f"Passed: {passed_suites}")
    print(f"Failed: {failed_suites}")
    
    if failed_suites == 0:
        print("\n🎉 ALL ERROR HANDLING AND RETRY LOGIC TESTS PASSED!")
        print("✅ The nimble-llm-caller integration is working correctly")
        print("✅ Error handling and retry logic are functioning properly")
        print("✅ Configuration validation is working as expected")
        print("✅ Prompt loading and substitution are working correctly")
        print("\n🚀 Ready for production use!")
        return True
    else:
        print(f"\n⚠️ {failed_suites} TEST SUITE(S) FAILED")
        print("❌ Error handling and retry logic need attention")
        print("🔧 Please review the failed tests and fix any issues")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)