#!/usr/bin/env python3
"""
Test script to verify that success messages appear in the pipeline with terse logging.
"""

import logging
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from codexes.core.logging_config import setup_application_logging, get_logging_manager
from codexes.core.statistics_reporter import StatisticsReporter
from codexes.core.logging_filters import log_success
from unittest.mock import MagicMock

# Import the filters from the pipeline
sys.path.insert(0, os.path.dirname(__file__))
from run_book_pipeline import SuccessAwareTerseLogFilter, SuccessAwarePromptLogFilter


def test_success_messages_with_terse_filter():
    """Test that success messages appear even with terse logging enabled."""
    print("=== Testing Success Messages with Terse Filter ===")
    print()
    
    # Set up logging
    setup_application_logging()
    
    # Get logger
    logger = logging.getLogger('codexes.test')
    
    # Apply terse filter to console handler (simulating -tl flag)
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            handler.addFilter(SuccessAwareTerseLogFilter())
            break
    
    print("Applied SuccessAwareTerseLogFilter to console handler")
    print()
    
    print("Testing normal INFO message (should be filtered out):")
    logger.info("This is a normal INFO message without emojis")
    print("^ No output above (message was filtered)")
    print()
    
    print("Testing success message with ✅ (should ALWAYS appear):")
    logger.info("Task completed successfully ✅")
    print("^ Success message should appear above")
    print()
    
    print("Testing statistics message with 📊 (should ALWAYS appear):")
    logger.info("📊 Pipeline Statistics Summary")
    print("^ Statistics message should appear above")
    print()
    
    print("Testing StatisticsReporter (should ALWAYS appear):")
    # Create a mock tracker for demonstration
    mock_tracker = MagicMock()
    mock_tracker.get_total_statistics.return_value = {
        'total_calls': 0,
        'total_tokens': 0,
        'total_cost': None,
        'duration_seconds': 0
    }
    
    # Create reporter and generate report
    reporter = StatisticsReporter()
    reporter.report_pipeline_statistics(mock_tracker)
    print("^ Statistics report should appear above")
    print()
    
    print("Testing error message with ❌ (should appear in terse mode):")
    logger.info("Operation failed ❌")
    print("^ Error message should appear above")
    print()
    
    print("Testing warning message with ⚠️ (should appear in terse mode):")
    logger.info("Warning: Something needs attention ⚠️")
    print("^ Warning message should appear above")
    print()
    
    print("=== Test Complete ===")


if __name__ == '__main__':
    test_success_messages_with_terse_filter()