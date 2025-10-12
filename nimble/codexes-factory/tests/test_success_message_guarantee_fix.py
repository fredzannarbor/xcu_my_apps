#!/usr/bin/env python3
"""
Test to verify that the success message guarantee is working correctly
in the actual pipeline execution environment.
"""

import logging
import sys
import os
import io
from contextlib import redirect_stdout, redirect_stderr

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.logging_config import setup_application_logging, get_logging_manager
from codexes.core.logging_filters import log_success, SuccessMessageFilter
from codexes.core.statistics_reporter import StatisticsReporter
from codexes.core.token_usage_tracker import TokenUsageTracker

# Import the pipeline filters
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from run_book_pipeline import SuccessAwareTerseLogFilter, SuccessAwarePromptLogFilter


def test_success_message_guarantee_with_pipeline_filters():
    """Test that success messages appear even with pipeline filters applied."""
    print("Testing success message guarantee with pipeline filters...")
    
    # Capture log output
    log_stream = io.StringIO()
    
    # Set up logging with our configuration
    logging_manager = get_logging_manager()
    logging_manager.reset_configuration()
    
    # Import the new success-aware handler
    from codexes.core.logging_filters import SuccessAwareHandler
    
    # Create a custom handler that writes to our stream
    handler = SuccessAwareHandler(log_stream)
    handler.setLevel(logging.WARNING)  # Set high level to test guarantee
    handler._debug_mode = True  # Enable debug output
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Set up logger
    logger = logging.getLogger('test_logger')
    logger.setLevel(logging.INFO)  # Set to INFO so messages can reach handler
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False
    
    # Apply pipeline filters (these were causing the issue)
    terse_filter = SuccessAwareTerseLogFilter()
    success_filter = SuccessMessageFilter()
    
    handler.addFilter(terse_filter)
    handler.addFilter(success_filter)
    
    print(f"Logger level: {logger.level} ({logging.getLevelName(logger.level)})")
    print(f"Handler level: {handler.level} ({logging.getLevelName(handler.level)})")
    print("Applied filters: SuccessAwareTerseLogFilter, SuccessMessageFilter")
    print("This simulates a scenario where handler level is higher than message level")
    print()
    
    # Debug: Check handler level after adding filters
    print(f"Handler level after adding filters: {handler.level}")
    
    # Test regular INFO message (should be filtered out)
    logger.info("This is a regular INFO message that should be filtered")
    
    # Test success messages using log_success function
    log_success(logger, "✅ This success message should always appear")
    log_success(logger, "📊 This statistics message should always appear")
    
    # Test success messages using regular logging 
    # These should be filtered out because they don't use log_success
    # and the handler level is higher than INFO
    print("Testing direct logger.info calls with success emojis...")
    print("(These should be filtered out because handler level > INFO level)")
    print(f"Logger effective level: {logger.getEffectiveLevel()}")
    print(f"Handler level: {handler.level}")
    print(f"INFO level: {logging.INFO}")
    
    logger.info("✅ Direct success message through logger.info")
    logger.info("📊 Direct statistics message through logger.info")
    print("Direct logger.info calls completed")
    
    # Test other emoji messages that should be filtered
    logger.info("❌ Error message should appear")
    logger.info("⚠️ Warning message should appear")
    
    # Get the captured output
    log_output = log_stream.getvalue()
    print("Captured log output:")
    print("-" * 40)
    print(log_output)
    print("-" * 40)
    
    # Verify results
    lines = log_output.strip().split('\n')
    success_lines = [line for line in lines if '✅' in line or '📊' in line]
    
    print(f"Found {len(success_lines)} success/statistics messages:")
    for line in success_lines:
        print(f"  - {line}")
    
    # Should have 2 success/statistics messages (only the log_success ones)
    # The direct logger.info calls should be filtered out by handler level
    expected_count = 2
    if len(success_lines) == expected_count:
        print(f"✅ SUCCESS: Found all {expected_count} expected success/statistics messages")
        print("✅ Direct logger.info calls were correctly filtered out (as expected)")
        return True
    else:
        print(f"❌ FAILURE: Expected {expected_count} success/statistics messages, found {len(success_lines)}")
        return False


def test_statistics_reporter_with_filters():
    """Test that StatisticsReporter messages appear with filters applied."""
    print("\nTesting StatisticsReporter with filters...")
    
    # Capture log output
    log_stream = io.StringIO()
    
    # Set up logging
    logging_manager = get_logging_manager()
    logging_manager.reset_configuration()
    
    # Import the success-aware handler
    from codexes.core.logging_filters import SuccessAwareHandler
    
    # Create success-aware handler
    handler = SuccessAwareHandler(log_stream)
    handler.setLevel(logging.ERROR)  # Set very high level to test guarantee
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Apply filters
    terse_filter = SuccessAwareTerseLogFilter()
    success_filter = SuccessMessageFilter()
    handler.addFilter(terse_filter)
    handler.addFilter(success_filter)
    
    # Set up the statistics reporter logger specifically
    stats_logger = logging.getLogger('codexes.core.statistics_reporter')
    stats_logger.setLevel(logging.INFO)  # Allow INFO messages to reach handler
    stats_logger.handlers.clear()
    stats_logger.addHandler(handler)
    stats_logger.propagate = False
    
    print(f"Statistics logger level: {stats_logger.level} ({logging.getLevelName(stats_logger.level)})")
    print(f"Handler level: {handler.level} ({logging.getLevelName(handler.level)})")
    
    # Create a mock token tracker with some data
    tracker = TokenUsageTracker()
    
    # Simulate some usage data using the actual LiteLLM response format
    import types
    
    # Create a mock response that matches LiteLLM's structure
    mock_response = types.SimpleNamespace()
    mock_response.usage = types.SimpleNamespace()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150
    mock_response.model = "test-model"
    
    # Record some mock usage
    tracker.record_usage("test-model", "test-prompt", mock_response, 1.5)
    
    # Create statistics reporter and generate report
    reporter = StatisticsReporter()
    
    print("Generating statistics report...")
    reporter.report_pipeline_statistics(tracker)
    
    # Get the captured output
    log_output = log_stream.getvalue()
    print("Captured log output:")
    print("-" * 40)
    print(log_output)
    print("-" * 40)
    
    # Check for statistics messages
    statistics_lines = [line for line in log_output.split('\n') if '📊' in line]
    
    print(f"Found {len(statistics_lines)} statistics messages:")
    for line in statistics_lines:
        print(f"  - {line}")
    
    if len(statistics_lines) > 0:
        print("✅ SUCCESS: Statistics messages appeared despite high handler level")
        return True
    else:
        print("❌ FAILURE: No statistics messages found")
        return False


def test_llm_caller_success_messages():
    """Test that LLM caller success messages work with filters."""
    print("\nTesting LLM caller success messages...")
    
    # This would require mocking LiteLLM, so we'll just test the logging part
    log_stream = io.StringIO()
    
    # Set up logging
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Set up logger with high level
    logger = logging.getLogger('codexes.core.llm_caller')
    logger.setLevel(logging.ERROR)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False
    
    # Apply filters
    terse_filter = SuccessAwareTerseLogFilter()
    success_filter = SuccessMessageFilter()
    handler.addFilter(terse_filter)
    handler.addFilter(success_filter)
    
    # Test the log_success function directly
    log_success(logger, "✅ Successfully received response from test-model [test-prompt].")
    log_success(logger, "✅ [test-prompt] Success from test-model.")
    
    # Get output
    log_output = log_stream.getvalue()
    print("Captured log output:")
    print("-" * 40)
    print(log_output)
    print("-" * 40)
    
    success_lines = [line for line in log_output.split('\n') if '✅' in line]
    
    if len(success_lines) >= 2:
        print("✅ SUCCESS: LLM caller success messages appeared")
        return True
    else:
        print("❌ FAILURE: LLM caller success messages missing")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("SUCCESS MESSAGE GUARANTEE FIX VALIDATION")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(test_success_message_guarantee_with_pipeline_filters())
    results.append(test_statistics_reporter_with_filters())
    results.append(test_llm_caller_success_messages())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Success message guarantee is working!")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Success message guarantee needs more work")
        return 1


if __name__ == "__main__":
    sys.exit(main())