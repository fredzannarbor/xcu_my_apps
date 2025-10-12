#!/usr/bin/env python3
"""
Integration test to verify that the success message guarantee works
in a realistic pipeline environment.
"""

import logging
import sys
import os
import io
from contextlib import redirect_stdout, redirect_stderr

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.logging_config import setup_application_logging, get_logging_manager
from codexes.core.logging_filters import log_success
from codexes.core.statistics_reporter import StatisticsReporter
from codexes.core.token_usage_tracker import TokenUsageTracker

# Import the pipeline filters
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from run_book_pipeline import SuccessAwareTerseLogFilter, SuccessAwarePromptLogFilter


def test_pipeline_logging_integration():
    """Test the complete pipeline logging setup with success message guarantee."""
    print("Testing pipeline logging integration...")
    
    # Capture stdout to see what would actually be displayed
    captured_output = io.StringIO()
    
    # Reset logging configuration
    logging_manager = get_logging_manager()
    logging_manager.reset_configuration()
    
    # Set up logging similar to how the pipeline does it
    setup_application_logging(environment='production')
    
    # Get the root logger and console handler
    root_logger = logging.getLogger()
    console_handler = None
    
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            console_handler = handler
            break
    
    if console_handler:
        # Redirect the handler to our captured output
        console_handler.stream = captured_output
        
        # Apply terse filter like the pipeline does
        terse_filter = SuccessAwareTerseLogFilter()
        console_handler.addFilter(terse_filter)
        
        print(f"Console handler type: {type(console_handler).__name__}")
        print(f"Console handler level: {console_handler.level}")
        print("Applied SuccessAwareTerseLogFilter")
    else:
        print("❌ No console handler found")
        return False
    
    # Test various logging scenarios
    app_logger = logging.getLogger('codexes')
    llm_logger = logging.getLogger('codexes.core.llm_caller')
    stats_logger = logging.getLogger('codexes.core.statistics_reporter')
    
    print("\nTesting various logging scenarios...")
    
    # 1. Regular INFO messages (should be filtered out by terse filter)
    app_logger.info("This is a regular INFO message that should be filtered")
    
    # 2. Success messages using log_success (should always appear)
    log_success(app_logger, "✅ Stage 1 complete. Processed JSON saved to test.json")
    log_success(llm_logger, "✅ Successfully received response from test-model [test-prompt].")
    
    # 3. Statistics messages using log_success (should always appear)
    log_success(stats_logger, "📊 Generating statistics report for pipeline: test_pipeline")
    
    # 4. Error messages (should appear)
    app_logger.error("❌ This error message should appear")
    
    # 5. Warning messages with emojis (should appear due to terse filter)
    app_logger.info("⚠️ This warning message should appear")
    
    # 6. Test StatisticsReporter directly
    tracker = TokenUsageTracker()
    
    # Add some mock data
    import types
    mock_response = types.SimpleNamespace()
    mock_response.usage = types.SimpleNamespace()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150
    mock_response.model = "test-model"
    
    tracker.record_usage("test-model", "test-prompt", mock_response, 1.5)
    
    reporter = StatisticsReporter()
    reporter.report_pipeline_statistics(tracker)
    
    # Get the captured output
    output = captured_output.getvalue()
    
    print("\nCaptured output:")
    print("-" * 50)
    print(output)
    print("-" * 50)
    
    # Analyze the output
    lines = output.strip().split('\n')
    success_lines = [line for line in lines if '✅' in line]
    stats_lines = [line for line in lines if '📊' in line]
    error_lines = [line for line in lines if '❌' in line]
    warning_lines = [line for line in lines if '⚠️' in line]
    regular_info_lines = [line for line in lines if 'regular INFO message' in line]
    
    print(f"\nAnalysis:")
    print(f"Success messages (✅): {len(success_lines)}")
    print(f"Statistics messages (📊): {len(stats_lines)}")
    print(f"Error messages (❌): {len(error_lines)}")
    print(f"Warning messages (⚠️): {len(warning_lines)}")
    print(f"Regular INFO messages: {len(regular_info_lines)}")
    
    # Verify expectations
    success = True
    
    if len(success_lines) < 2:
        print("❌ FAILURE: Expected at least 2 success messages")
        success = False
    else:
        print("✅ SUCCESS: Success messages appeared")
    
    if len(stats_lines) < 1:
        print("❌ FAILURE: Expected at least 1 statistics message")
        success = False
    else:
        print("✅ SUCCESS: Statistics messages appeared")
    
    if len(error_lines) < 1:
        print("❌ FAILURE: Expected at least 1 error message")
        success = False
    else:
        print("✅ SUCCESS: Error messages appeared")
    
    if len(warning_lines) < 1:
        print("❌ FAILURE: Expected at least 1 warning message")
        success = False
    else:
        print("✅ SUCCESS: Warning messages appeared")
    
    if len(regular_info_lines) > 0:
        print("❌ FAILURE: Regular INFO messages should be filtered out")
        success = False
    else:
        print("✅ SUCCESS: Regular INFO messages were filtered out")
    
    return success


def test_high_log_level_scenario():
    """Test success message guarantee when log levels are set very high."""
    print("\n" + "="*60)
    print("Testing high log level scenario...")
    
    # Capture output
    captured_output = io.StringIO()
    
    # Reset and configure logging
    logging_manager = get_logging_manager()
    logging_manager.reset_configuration()
    
    # Set up with very high log levels
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {'format': '%(levelname)s - %(message)s'}
        },
        'handlers': {
            'console': {
                'class': 'codexes.core.logging_filters.SuccessAwareHandler',
                'level': 'ERROR',  # Very high level
                'formatter': 'simple',
                'stream': captured_output
            }
        },
        'loggers': {
            'codexes': {
                'level': 'ERROR',  # Very high level
                'handlers': ['console'],
                'propagate': False
            }
        }
    }
    
    logging.config.dictConfig(config)
    
    # Apply filters
    console_handler = logging.getLogger('codexes').handlers[0]
    terse_filter = SuccessAwareTerseLogFilter()
    console_handler.addFilter(terse_filter)
    
    logger = logging.getLogger('codexes')
    
    print(f"Logger level: {logger.level} (ERROR)")
    print(f"Handler level: {console_handler.level} (ERROR)")
    
    # Test messages
    logger.info("This INFO message should be filtered out")
    logger.warning("This WARNING message should be filtered out")
    log_success(logger, "✅ This success message should appear despite high levels")
    log_success(logger, "📊 This statistics message should appear despite high levels")
    logger.error("❌ This error message should appear")
    
    # Get output
    output = captured_output.getvalue()
    
    print("\nCaptured output:")
    print("-" * 40)
    print(output)
    print("-" * 40)
    
    # Check results
    lines = output.strip().split('\n')
    success_lines = [line for line in lines if '✅' in line or '📊' in line]
    error_lines = [line for line in lines if '❌' in line]
    other_lines = [line for line in lines if line and '✅' not in line and '📊' not in line and '❌' not in line]
    
    print(f"Success/Statistics messages: {len(success_lines)}")
    print(f"Error messages: {len(error_lines)}")
    print(f"Other messages: {len(other_lines)}")
    
    if len(success_lines) >= 2 and len(error_lines) >= 1 and len(other_lines) == 0:
        print("✅ SUCCESS: High log level scenario passed")
        return True
    else:
        print("❌ FAILURE: High log level scenario failed")
        return False


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("PIPELINE SUCCESS MESSAGE GUARANTEE INTEGRATION TEST")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(test_pipeline_logging_integration())
    results.append(test_high_log_level_scenario())
    
    # Summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ Success message guarantee is working in pipeline environment")
        return 0
    else:
        print("❌ SOME INTEGRATION TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())