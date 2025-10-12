"""
Unit tests for the LiteLLM logging filter.
"""

import logging
import os
import unittest
from unittest.mock import patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.logging_filters import LiteLLMFilter, create_litellm_filter, apply_litellm_filter


class TestLiteLLMFilter(unittest.TestCase):
    """Test cases for the LiteLLMFilter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.filter = LiteLLMFilter(debug_mode=False)
        
        # Create a test handler to capture filtered messages
        self.test_handler = MockHandler()
        self.test_handler.addFilter(self.filter)
        
        # Create test loggers
        self.litellm_logger = logging.getLogger('litellm.test')
        self.litellm_logger.handlers = [self.test_handler]
        self.litellm_logger.propagate = False
        self.litellm_logger.setLevel(logging.DEBUG)
        
        self.app_logger = logging.getLogger('myapp.test')
        self.app_logger.handlers = [self.test_handler]
        self.app_logger.propagate = False
        self.app_logger.setLevel(logging.DEBUG)
    
    def tearDown(self):
        """Clean up after tests."""
        self.test_handler.messages.clear()
    
    def test_filter_litellm_info_messages(self):
        """Test that LiteLLM INFO messages with filtered patterns are blocked."""
        # These should be filtered out
        self.litellm_logger.info("Cost calculation for model gpt-4")
        self.litellm_logger.info("Completion wrapper called")
        self.litellm_logger.info("LiteLLM utils processing request")
        
        # Should have no messages
        self.assertEqual(len(self.test_handler.messages), 0)
    
    def test_allow_litellm_error_messages(self):
        """Test that LiteLLM ERROR messages are always allowed through."""
        self.litellm_logger.error("Authentication failed")
        self.litellm_logger.error("Cost calculation failed")  # Even with filtered pattern
        
        # Should have 2 messages
        self.assertEqual(len(self.test_handler.messages), 2)
        self.assertIn("Authentication failed", self.test_handler.messages[0])
        self.assertIn("Cost calculation failed", self.test_handler.messages[1])
    
    def test_allow_litellm_critical_patterns(self):
        """Test that critical patterns are always allowed through regardless of level."""
        self.litellm_logger.info("Service unavailable - please retry")
        self.litellm_logger.info("Rate limit exceeded")
        self.litellm_logger.info("Authentication error occurred")
        
        # Should have 3 messages
        self.assertEqual(len(self.test_handler.messages), 3)
    
    def test_allow_non_litellm_messages(self):
        """Test that non-LiteLLM logger messages are always allowed through."""
        self.app_logger.info("Cost calculation for my app")  # Same pattern but different logger
        self.app_logger.debug("Debug message from app")
        
        # Should have 2 messages
        self.assertEqual(len(self.test_handler.messages), 2)
    
    def test_debug_mode_allows_all_messages(self):
        """Test that debug mode allows all LiteLLM messages through."""
        self.filter.set_debug_mode(True)
        
        self.litellm_logger.info("Cost calculation for model gpt-4")
        self.litellm_logger.debug("Debug message")
        self.litellm_logger.info("Completion wrapper called")
        
        # Should have 3 messages
        self.assertEqual(len(self.test_handler.messages), 3)
    
    def test_logger_name_matching(self):
        """Test that logger name matching works correctly."""
        # Test exact matches
        self.assertTrue(self.filter._is_litellm_logger('litellm'))
        self.assertTrue(self.filter._is_litellm_logger('litellm.main'))
        self.assertTrue(self.filter._is_litellm_logger('litellm.utils'))
        
        # Test non-matches
        self.assertFalse(self.filter._is_litellm_logger('myapp'))
        self.assertFalse(self.filter._is_litellm_logger('litellm_custom'))  # Doesn't start with exact match
        self.assertFalse(self.filter._is_litellm_logger('app.litellm'))
    
    def test_pattern_matching(self):
        """Test that pattern matching works correctly."""
        # Test filtered patterns
        self.assertTrue(self.filter._contains_filtered_pattern('cost calculation in progress'))
        self.assertTrue(self.filter._contains_filtered_pattern('completion wrapper started'))
        self.assertTrue(self.filter._contains_filtered_pattern('litellm utils loaded'))
        
        # Test critical patterns
        self.assertTrue(self.filter._contains_critical_pattern('authentication failed'))
        self.assertTrue(self.filter._contains_critical_pattern('service unavailable'))
        self.assertTrue(self.filter._contains_critical_pattern('rate limit exceeded'))
        
        # Test non-matching patterns
        self.assertFalse(self.filter._contains_filtered_pattern('normal application message'))
        self.assertFalse(self.filter._contains_critical_pattern('normal application message'))
    
    def test_add_remove_patterns(self):
        """Test adding and removing custom patterns."""
        # Add a custom filtered pattern
        self.filter.add_filtered_pattern('Custom Pattern')
        self.assertTrue(self.filter._contains_filtered_pattern('custom pattern test'))
        
        # Remove the pattern
        self.filter.remove_filtered_pattern('Custom Pattern')
        self.assertFalse(self.filter._contains_filtered_pattern('custom pattern test'))
        
        # Add a custom critical pattern
        self.filter.add_critical_pattern('Critical Custom')
        self.assertTrue(self.filter._contains_critical_pattern('critical custom message'))
    
    def test_environment_variable_debug_mode(self):
        """Test that debug mode can be controlled via environment variable."""
        with patch.dict(os.environ, {'LITELLM_DEBUG': 'true'}):
            filter_with_env = LiteLLMFilter()
            self.assertTrue(filter_with_env.is_debug_mode())
        
        with patch.dict(os.environ, {'LITELLM_DEBUG': 'false'}):
            filter_with_env = LiteLLMFilter()
            self.assertFalse(filter_with_env.is_debug_mode())
    
    def test_convenience_functions(self):
        """Test the convenience functions for creating and applying filters."""
        # Test create_litellm_filter
        filter_instance = create_litellm_filter(debug_mode=True)
        self.assertIsInstance(filter_instance, LiteLLMFilter)
        self.assertTrue(filter_instance.is_debug_mode())
        
        # Test apply_litellm_filter
        test_logger = logging.getLogger('test.logger')
        applied_filter = apply_litellm_filter('test.logger', debug_mode=False)
        self.assertIsInstance(applied_filter, LiteLLMFilter)
        self.assertFalse(applied_filter.is_debug_mode())
        
        # Check that filter was applied to logger
        self.assertIn(applied_filter, test_logger.filters)


class MockHandler(logging.Handler):
    """Mock handler that captures log messages for testing."""
    
    def __init__(self):
        super().__init__()
        self.messages = []
    
    def emit(self, record):
        """Capture the log record."""
        self.messages.append(self.format(record))


if __name__ == '__main__':
    unittest.main()