"""
Test the log_success function to ensure success messages always appear.
"""

import logging
import tempfile
import unittest
from io import StringIO

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.codexes.core.logging_filters import log_success


class TestLogSuccessFunction(unittest.TestCase):
    """Test the log_success function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.log_stream = StringIO()
        
        # Create a logger with high level
        self.logger = logging.getLogger('test_success_function')
        self.logger.setLevel(logging.ERROR)  # High level that would normally block INFO
        
        # Add handler to capture output
        self.handler = logging.StreamHandler(self.log_stream)
        self.handler.setLevel(logging.ERROR)  # Handler also has high level
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        self.handler.setFormatter(formatter)
        self.logger.addHandler(self.handler)
        
        # Clear any existing handlers
        self.logger.handlers = [self.handler]
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.logger.handlers.clear()
    
    def test_log_success_with_success_icon(self):
        """Test that log_success works with ✅ icon."""
        # This should appear even though logger level is ERROR
        log_success(self.logger, "Task completed successfully ✅", logging.INFO)
        
        output = self.log_stream.getvalue()
        self.assertIn("✅", output)
        self.assertIn("Task completed successfully", output)
    
    def test_log_success_with_statistics_icon(self):
        """Test that log_success works with 📊 icon."""
        # This should appear even though logger level is ERROR
        log_success(self.logger, "📊 Pipeline Statistics Summary", logging.INFO)
        
        output = self.log_stream.getvalue()
        self.assertIn("📊", output)
        self.assertIn("Pipeline Statistics Summary", output)
    
    def test_log_success_without_icons(self):
        """Test that log_success uses normal logging for messages without icons."""
        # This should NOT appear because logger level is ERROR and message level is INFO
        log_success(self.logger, "Normal message without icons", logging.INFO)
        
        output = self.log_stream.getvalue()
        self.assertEqual(output.strip(), "")  # Should be empty
    
    def test_log_success_with_error_level(self):
        """Test that log_success works with ERROR level messages."""
        # This should appear because it's ERROR level
        log_success(self.logger, "Error message ✅", logging.ERROR)
        
        output = self.log_stream.getvalue()
        self.assertIn("✅", output)
        self.assertIn("Error message", output)
    
    def test_log_success_restores_levels(self):
        """Test that log_success restores original logger and handler levels."""
        original_logger_level = self.logger.level
        original_handler_level = self.handler.level
        
        # Call log_success
        log_success(self.logger, "Test message ✅", logging.INFO)
        
        # Verify levels are restored
        self.assertEqual(self.logger.level, original_logger_level)
        self.assertEqual(self.handler.level, original_handler_level)
    
    def test_log_success_with_multiple_handlers(self):
        """Test log_success with multiple handlers."""
        # Add another handler
        stream2 = StringIO()
        handler2 = logging.StreamHandler(stream2)
        handler2.setLevel(logging.WARNING)
        formatter2 = logging.Formatter('HANDLER2: %(message)s')
        handler2.setFormatter(formatter2)
        self.logger.addHandler(handler2)
        
        # Log success message
        log_success(self.logger, "Multi-handler test ✅", logging.INFO)
        
        # Check both outputs
        output1 = self.log_stream.getvalue()
        output2 = stream2.getvalue()
        
        self.assertIn("✅", output1)
        self.assertIn("✅", output2)
        self.assertIn("HANDLER2:", output2)


if __name__ == '__main__':
    unittest.main()