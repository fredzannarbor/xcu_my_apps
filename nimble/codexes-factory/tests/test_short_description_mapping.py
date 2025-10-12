"""
Tests for short description mapping.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.distribution.short_description_mapping import ShortDescriptionMappingStrategy
from codexes.modules.distribution.field_mapping import MappingContext
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestShortDescriptionMapping(unittest.TestCase):
    """Test cases for short description mapping."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.metadata = CodexMetadata()
        self.metadata.summary_short = "This is a short description."
        
        # Create a mock context
        self.context = MagicMock(spec=MappingContext)
        self.context.field_name = "Short Description"
        self.context.lsi_headers = ["Short Description"]
        self.context.current_row_data = {}
    
    def test_short_description_mapping(self):
        """Test short description mapping strategy."""
        # Test with valid short description
        strategy = ShortDescriptionMappingStrategy("summary_short")
        result = strategy.map_field(self.metadata, self.context)
        self.assertEqual(result, "This is a short description.")
        
        # Test with long description
        self.metadata.summary_short = "A" * 400
        result = strategy.map_field(self.metadata, self.context)
        self.assertLess(len(result.encode('utf-8')), 350)
        self.assertTrue(result.endswith("..."))
        
        # Test with empty field
        self.metadata.summary_short = ""
        result = strategy.map_field(self.metadata, self.context)
        self.assertEqual(result, "")
        
        # Test with non-existent field
        strategy = ShortDescriptionMappingStrategy("non_existent_field", default_value="DEFAULT")
        result = strategy.map_field(self.metadata, self.context)
        self.assertEqual(result, "DEFAULT")
        
        # Test with custom max_bytes
        self.metadata.summary_short = "This is a test sentence."
        strategy = ShortDescriptionMappingStrategy("summary_short", max_bytes=10)
        result = strategy.map_field(self.metadata, self.context)
        self.assertLessEqual(len(result.encode('utf-8')), 10)
        self.assertTrue(result.endswith("..."))


if __name__ == '__main__':
    unittest.main()