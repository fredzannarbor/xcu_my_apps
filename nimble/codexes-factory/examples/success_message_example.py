#!/usr/bin/env python3
"""
Example demonstrating that success messages with ✅ always appear in output.

This script shows how success messages bypass normal logging level restrictions.
"""

import logging
import sys
import os

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.codexes.core.logging_config import setup_application_logging
from src.codexes.core.logging_filters import log_success
from src.codexes.core.statistics_reporter import StatisticsReporter
from unittest.mock import MagicMock


def demonstrate_success_messages():
    """Demonstrate that success messages always appear."""
    print("=== Success Message Demonstration ===")
    print()
    
    # Set up logging with a high level that would normally block INFO messages
    setup_application_logging()
    
    # Get a logger and set it to ERROR level (high level)
    logger = logging.getLogger('codexes.demo')
    logger.setLevel(logging.ERROR)
    
    print("Logger level set to ERROR (high level that blocks INFO messages)")
    print()
    
    print("Testing normal INFO message (should NOT appear):")
    logger.info("This is a normal INFO message that should be blocked")
    print("^ No output above this line (message was blocked)")
    print()
    
    print("Testing success INFO message with ✅ (should ALWAYS appear):")
    log_success(logger, "Task completed successfully ✅", logging.INFO)
    print("^ Success message appeared above despite high logger level")
    print()
    
    print("Testing statistics message with 📊 (should ALWAYS appear):")
    log_success(logger, "📊 Pipeline Statistics Summary", logging.INFO)
    print("^ Statistics message appeared above despite high logger level")
    print()
    
    print("Testing StatisticsReporter with high logger level:")
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
    print("^ Statistics report appeared above despite high logger level")
    print()
    
    print("=== Demonstration Complete ===")
    print()
    print("Key takeaways:")
    print("• Messages with ✅ always appear regardless of logging level")
    print("• Messages with 📊 always appear regardless of logging level")
    print("• Normal messages respect the configured logging levels")
    print("• StatisticsReporter uses log_success to ensure visibility")


if __name__ == '__main__':
    demonstrate_success_messages()