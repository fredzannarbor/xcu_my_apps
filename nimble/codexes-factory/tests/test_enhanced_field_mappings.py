"""
Tests for enhanced field mappings.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.distribution.enhanced_field_mappings import create_enhanced_field_mapping_registry
from codexes.modules.distribution.field_mapping import MappingContext
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestEnhancedFieldMappings(unittest.TestCase):
    """Test cases for enhanced field mappings."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.metadata = CodexMetadata()
        self.metadata.bisac_codes = "FIC000000 FICTION / General"
        self.metadata.bisac_category_2 = "BUS000000 BUSINESS & ECONOMICS / General"
        self.metadata.bisac_category_3 = "SCI000000 SCIENCE / General"
        
        # Create a mock context
        self.context = MagicMock(spec=MappingContext)
        self.context.field_name = "BISAC Category 1"
        self.context.lsi_headers = ["BISAC Category 1", "BISAC Category 2", "BISAC Category 3"]
        self.context.current_row_data = {}
    
    def test_bisac_field_mappings(self):
        """Test that BISAC fields are properly mapped with codes stripped."""
        registry = create_enhanced_field_mapping_registry()
        
        # Set up context with empty config
        self.context.config = {}
        
        # Test BISAC Category 1
        strategy1 = registry.get_strategy("BISAC Category 1")
        result1 = strategy1.map_field(self.metadata, self.context)
        self.assertEqual(result1, "FICTION / General")
        
        # Test BISAC Category 2
        strategy2 = registry.get_strategy("BISAC Category 2")
        result2 = strategy2.map_field(self.metadata, self.context)
        self.assertEqual(result2, "BUSINESS & ECONOMICS / General")
        
        # Test BISAC Category 3
        strategy3 = registry.get_strategy("BISAC Category 3")
        result3 = strategy3.map_field(self.metadata, self.context)
        self.assertEqual(result3, "SCIENCE / General")


if __name__ == '__main__':
    unittest.main()