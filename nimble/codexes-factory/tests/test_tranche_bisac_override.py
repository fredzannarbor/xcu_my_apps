"""
Tests for tranche BISAC subject override functionality.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.distribution.bisac_field_mapping import BisacCategoryMappingStrategy
from codexes.modules.distribution.field_mapping import MappingContext
from codexes.modules.distribution.enhanced_field_mappings import create_comprehensive_lsi_registry
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestTrancheBisacOverride(unittest.TestCase):
    """Test cases for tranche BISAC subject override functionality."""
    
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
        self.context.config = {}
    
    def test_bisac_override_in_strategy(self):
        """Test that tranche BISAC override works in the mapping strategy."""
        # Test with no override
        strategy = BisacCategoryMappingStrategy("bisac_codes", is_primary=True)
        result = strategy.map_field(self.metadata, self.context)
        self.assertEqual(result, "FICTION / General")
        
        # Test with override
        self.context.config['tranche_bisac_subject'] = "SOC052000 SELF-HELP / Journaling"
        result = strategy.map_field(self.metadata, self.context)
        self.assertEqual(result, "SELF-HELP / Journaling")
        
        # Test that non-primary BISAC categories are not affected
        strategy2 = BisacCategoryMappingStrategy("bisac_category_2")
        result2 = strategy2.map_field(self.metadata, self.context)
        self.assertEqual(result2, "BUSINESS & ECONOMICS / General")
    
    @patch('src.codexes.modules.distribution.tranche_config_loader.TrancheConfigLoader.get_tranche_bisac_subject')
    def test_registry_with_tranche_override(self, mock_get_bisac):
        """Test that registry correctly applies tranche BISAC override."""
        # Mock the tranche config loader to return a specific BISAC subject
        mock_get_bisac.return_value = "SOC052000 SELF-HELP / Journaling"
        
        # Create registry with tranche name
        registry = create_comprehensive_lsi_registry(tranche_name="xynapse_tranche_1")
        
        # Get the BISAC Category 1 strategy
        strategy = registry.get_strategy("BISAC Category 1")
        
        # Create a context with the config from the registry
        context = MagicMock(spec=MappingContext)
        context.config = {'tranche_bisac_subject': "SOC052000 SELF-HELP / Journaling"}
        
        # Test that the strategy uses the override
        result = strategy.map_field(self.metadata, context)
        self.assertEqual(result, "SELF-HELP / Journaling")
        
        # Verify that the tranche config loader was called
        mock_get_bisac.assert_called_once_with("xynapse_tranche_1")


if __name__ == '__main__':
    unittest.main()