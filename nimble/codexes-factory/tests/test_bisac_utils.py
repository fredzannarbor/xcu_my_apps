"""
Tests for BISAC utilities.
"""

import os
import sys
import unittest

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.distribution.bisac_utils import strip_bisac_code, get_bisac_code


class TestBisacUtils(unittest.TestCase):
    """Test cases for BISAC utilities."""
    
    def test_strip_bisac_code(self):
        """Test stripping codes from BISAC subject fields."""
        # Test with standard BISAC format
        self.assertEqual(
            strip_bisac_code("FIC000000 FICTION / General"),
            "FICTION / General"
        )
        
        # Test with business category
        self.assertEqual(
            strip_bisac_code("BUS000000 BUSINESS & ECONOMICS / General"),
            "BUSINESS & ECONOMICS / General"
        )
        
        # Test with no code to strip
        self.assertEqual(
            strip_bisac_code("FICTION / General"),
            "FICTION / General"
        )
        
        # Test with empty string
        self.assertEqual(strip_bisac_code(""), "")
        
        # Test with None
        self.assertEqual(strip_bisac_code(None), "")
        
        # Test with multiple spaces after code
        self.assertEqual(
            strip_bisac_code("FIC000000    FICTION / General"),
            "FICTION / General"
        )
    
    def test_get_bisac_code(self):
        """Test extracting BISAC codes."""
        # Test with standard BISAC format
        self.assertEqual(
            get_bisac_code("FIC000000 FICTION / General"),
            "FIC000000"
        )
        
        # Test with business category
        self.assertEqual(
            get_bisac_code("BUS000000 BUSINESS & ECONOMICS / General"),
            "BUS000000"
        )
        
        # Test with no code to extract
        self.assertIsNone(get_bisac_code("FICTION / General"))
        
        # Test with empty string
        self.assertIsNone(get_bisac_code(""))
        
        # Test with None
        self.assertIsNone(get_bisac_code(None))


if __name__ == '__main__':
    unittest.main()