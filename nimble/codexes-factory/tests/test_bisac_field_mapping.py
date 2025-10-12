"""
Tests for BISAC field mapping.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.distribution.bisac_field_mapping import BisacCategoryMappingStrategy
from codexes.modules.distribution.field_mapping import MappingContext
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestBisacFieldMapping(unittest.TestCase):
    """Test cases for BISAC field mapping."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.metadata = CodexMetadata()
        self.metadata.bisac_codes = "FIC000000 FICTION / General"
        self.metadata.bisac_category_2 = "BUS000000 BUSINESS & ECONOMICS / General"
        self.metadata.bisac_category_3 = "SCIENCE / General"  # No code
    
    def test_bisac_category_mapping(self):
        """Test BISAC category mapping strategy."""
        # Create a mock context
        context = MagicMock()
        
        # Test mapping for primary BISAC code
        strategy1 = BisacCategoryMappingStrategy("bisac_codes")
        result1 = strategy1.map_field(self.metadata, context)
        self.assertEqual(result1, "FICTION / General")
        
        # Test mapping for secondary BISAC code
        strategy2 = BisacCategoryMappingStrategy("bisac_category_2")
        result2 = strategy2.map_field(self.metadata, context)
        self.assertEqual(result2, "BUSINESS & ECONOMICS / General")
        
        # Test mapping for tertiary BISAC code (no code to strip)
        strategy3 = BisacCategoryMappingStrategy("bisac_category_3")
        result3 = strategy3.map_field(self.metadata, context)
        self.assertEqual(result3, "SCIENCE / General")
        
        # Test mapping for non-existent field
        strategy4 = BisacCategoryMappingStrategy("non_existent_field", "DEFAULT")
        result4 = strategy4.map_field(self.metadata, context)
        self.assertEqual(result4, "DEFAULT")
        
        # Test mapping for empty field
        self.metadata.bisac_codes = ""
        result5 = strategy1.map_field(self.metadata, context)
        self.assertEqual(result5, "")


if __name__ == '__main__':
    unittest.main()