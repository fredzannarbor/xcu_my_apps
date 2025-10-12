"""
Tests for success message filtering functionality.

This module tests that messages containing the success icon ✅ always appear
in log output regardless of logging level configuration.
"""

import logging
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.codexes.core.logging_config import LoggingConfigManager, setup_application_logging
from src.codexes.core.logging_filters import SuccessMessageFilter


class TestSuccessMessageFiltering(unittest.TestCase):
    """Test success message filtering functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_stream = StringIO()
        
        # Reset logging configuration
        for logger_name in logging.Logger.manager.loggerDict:
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
            logger.filters.clear()
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.filters.clear()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Reset global logging manager
        try:
            import src.codexes.core.logging_config as logging_config_module
            logging_config_module._logging_manager = None
        except ImportError:
            pass
    
    def test_success_filter_allows_success_messages(self):
        """Test that SuccessMessageFilter allows messages with ✅."""
        filter_instance = SuccessMessageFilter()
        
        # Create test log records
        success_record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Operation completed successfully ✅',
            args=(),
            exc_info=None
        )
        
        normal_record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Normal message',
            args=(),
            exc_info=None
        )
        
        # Test that success messages are allowed
        self.assertTrue(filter_instance.filter(success_record))
        
        # Test that normal messages are also allowed (filter doesn't block them)
        self.assertTrue(filter_instance.filter(normal_record))
    
    def test_success_messages_appear_with_high_log_level(self):
        """Test that success messages appear even when log level is set high."""
        # Set up a logger with ERROR level (should normally block INFO messages)
        logger = logging.getLogger('test_success')
        logger.setLevel(logging.ERROR)
        
        # Add success filter
        success_filter = SuccessMessageFilter()
        logger.addFilter(success_filter)
        
        # Add handler to capture output
        handler = logging.StreamHandler(self.log_stream)
        handler.setLevel(logging.DEBUG)  # Handler allows all levels
        logger.addHandler(handler)
        
        # Test normal INFO message (should be blocked by logger level)
        logger.info("Normal info message")
        
        # Test success INFO message (should appear due to filter)
        logger.info("Task completed successfully ✅")
        
        # Get the output
        output = self.log_stream.getvalue()
        
        # Success message should appear even though logger level is ERROR
        self.assertIn("✅", output)
        self.assertIn("Task completed successfully", output)
    
    def test_logging_config_applies_success_filter(self):
        """Test that LoggingConfigManager applies success filter to loggers."""
        # Create a minimal configuration that sets high log levels
        config_data = {
            "settings": {
                "litellm_filtering": {"enabled": True},
                "log_levels": {"application": "ERROR"},  # High level
                "handlers": {
                    "console_enabled": True,
                    "file_enabled": False,
                    "error_file_enabled": False,
                    "console_level": "ERROR"
                },
                "output_formats": {
                    "console_format": "simple",
                    "timestamp_format": "%H:%M:%S"
                }
            },
            "format_templates": {
                "simple": "%(levelname)s - %(message)s"
            }
        }
        
        # Create manager and set up logging
        manager = LoggingConfigManager()
        manager._config_data = config_data
        
        # Capture console output
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            manager.setup_logging()
            
            # Get the application logger
            app_logger = logging.getLogger('codexes.test')
            
            # Test normal INFO message (should be blocked)
            app_logger.info("Normal info message")
            
            # Test success INFO message (should appear)
            app_logger.info("Pipeline completed successfully ✅")
            
            # Test ERROR level success message (should definitely appear)
            app_logger.error("Critical task failed ✅ (this shouldn't happen but testing)")
            
            # Get output
            output = fake_stdout.getvalue()
            
            # Success messages should appear
            self.assertIn("✅", output)
            self.assertIn("Pipeline completed successfully", output)
    
    def test_success_filter_with_different_message_formats(self):
        """Test success filter with various message formats containing ✅."""
        filter_instance = SuccessMessageFilter()
        
        test_messages = [
            "✅ Task completed",
            "Task completed ✅",
            "Step 1 ✅ Step 2 ✅ All done",
            "Success ✅: Operation finished",
            "✅✅✅ Multiple success icons",
            "Mixed content ✅ with other text",
        ]
        
        for msg in test_messages:
            record = logging.LogRecord(
                name='test',
                level=logging.INFO,
                pathname='',
                lineno=0,
                msg=msg,
                args=(),
                exc_info=None
            )
            
            # All messages with ✅ should be allowed
            self.assertTrue(filter_instance.filter(record), f"Failed for message: {msg}")
    
    def test_success_filter_with_formatted_messages(self):
        """Test success filter with formatted log messages."""
        filter_instance = SuccessMessageFilter()
        
        # Test with format arguments
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Task %s completed %s',
            args=('processing', '✅'),
            exc_info=None
        )
        
        # Should allow the message because it contains ✅ after formatting
        self.assertTrue(filter_instance.filter(record))
    
    def test_success_filter_exception_handling(self):
        """Test that success filter handles exceptions gracefully."""
        filter_instance = SuccessMessageFilter()
        
        # Create a record that might cause getMessage() to fail
        class BadRecord:
            def getMessage(self):
                raise Exception("Test exception")
        
        bad_record = BadRecord()
        
        # Should return True (allow message) when exception occurs
        self.assertTrue(filter_instance.filter(bad_record))
    
    def test_integration_with_statistics_reporter(self):
        """Test that success messages from StatisticsReporter always appear."""
        from src.codexes.core.statistics_reporter import StatisticsReporter
        from unittest.mock import MagicMock
        
        # Set up logging with high level
        setup_application_logging()
        
        # Create a reporter
        reporter = StatisticsReporter()
        
        # Mock the logger to capture calls
        with patch.object(reporter.logger, 'info') as mock_info:
            # Create mock tracker
            mock_tracker = MagicMock()
            mock_tracker.get_total_statistics.return_value = {
                'total_calls': 0,
                'total_tokens': 0,
                'total_cost': None,
                'duration_seconds': 0
            }
            
            # Call report method
            reporter.report_pipeline_statistics(mock_tracker)
            
            # Verify that info was called (even if with "No LLM calls recorded")
            mock_info.assert_called()
            
            # The actual message should contain the 📊 icon which should always appear
            call_args = mock_info.call_args_list
            self.assertTrue(any('📊' in str(call) for call in call_args))


if __name__ == '__main__':
    unittest.main()