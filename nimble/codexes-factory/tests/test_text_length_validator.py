"""
Tests for text length validator.
"""

import os
import sys
import unittest

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.distribution.text_length_validator import (
    validate_short_description_length,
    truncate_at_word_boundary,
    validate_and_truncate_short_description
)


class TestTextLengthValidator(unittest.TestCase):
    """Test cases for text length validator."""
    
    def test_validate_short_description_length(self):
        """Test validating short description length."""
        # Test with empty string
        is_valid, byte_length = validate_short_description_length("")
        self.assertTrue(is_valid)
        self.assertEqual(byte_length, 0)
        
        # Test with short description
        short_desc = "This is a short description."
        is_valid, byte_length = validate_short_description_length(short_desc)
        self.assertTrue(is_valid)
        self.assertEqual(byte_length, len(short_desc.encode('utf-8')))
        
        # Test with description that exceeds limit
        long_desc = "A" * 400
        is_valid, byte_length = validate_short_description_length(long_desc)
        self.assertFalse(is_valid)
        self.assertEqual(byte_length, 400)
        
        # Test with custom max_bytes
        is_valid, byte_length = validate_short_description_length("A" * 100, max_bytes=50)
        self.assertFalse(is_valid)
        self.assertEqual(byte_length, 100)
    
    def test_truncate_at_word_boundary(self):
        """Test truncating text at word boundary."""
        # Test with empty string
        self.assertEqual(truncate_at_word_boundary(""), "")
        
        # Test with short text
        short_text = "This is a short text."
        self.assertEqual(truncate_at_word_boundary(short_text), short_text)
        
        # Test with long text
        long_text = "This is a very long description that exceeds the maximum byte length. " * 10
        truncated = truncate_at_word_boundary(long_text)
        self.assertLess(len(truncated.encode('utf-8')), 350)
        self.assertTrue(truncated.endswith("..."))
        
        # Test with custom max_bytes
        truncated = truncate_at_word_boundary("This is a test sentence.", max_bytes=10)
        self.assertLessEqual(len(truncated.encode('utf-8')), 10)
        self.assertTrue(truncated.endswith("..."))
    
    def test_validate_and_truncate_short_description(self):
        """Test validating and truncating short description."""
        # Test with empty string
        self.assertEqual(validate_and_truncate_short_description(""), "")
        
        # Test with short description
        short_desc = "This is a short description."
        self.assertEqual(validate_and_truncate_short_description(short_desc), short_desc)
        
        # Test with description that exceeds limit
        long_desc = "This is a very long description that exceeds the maximum byte length. " * 10
        truncated = validate_and_truncate_short_description(long_desc)
        self.assertLess(len(truncated.encode('utf-8')), 350)
        self.assertTrue(truncated.endswith("..."))
        
        # Test with non-ASCII characters
        unicode_desc = "This description contains non-ASCII characters like 你好 and 😊" * 20
        truncated = validate_and_truncate_short_description(unicode_desc)
        self.assertLess(len(truncated.encode('utf-8')), 350)
        self.assertTrue(truncated.endswith("..."))


if __name__ == '__main__':
    unittest.main()