"""
Tests for Thema subject mapping.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.distribution.thema_subject_mapping import (
    ThemaSubjectMappingStrategy,
    expand_thema_code,
    THEMA_CODE_MAPPING
)
from codexes.modules.distribution.field_mapping import MappingContext
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestThemaSubjectMapping(unittest.TestCase):
    """Test cases for Thema subject mapping."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.metadata = CodexMetadata()
        self.metadata.thema_subject_1 = "F"
        self.metadata.thema_subject_2 = "FBA"
        self.metadata.thema_subject_3 = "J Society & Social Sciences"
        
        # Create a mock context
        self.context = MagicMock(spec=MappingContext)
        self.context.field_name = "Thema Subject 1"
        self.context.lsi_headers = ["Thema Subject 1", "Thema Subject 2", "Thema Subject 3"]
        self.context.current_row_data = {}
    
    def test_expand_thema_code(self):
        """Test expanding Thema codes."""
        # Test with single letter code
        self.assertEqual(expand_thema_code("F"), "F Fiction & Related Items")
        
        # Test with multi-letter code
        self.assertEqual(expand_thema_code("FBA"), "FBA Modern & Contemporary Fiction")
        
        # Test with code that already has description
        self.assertEqual(expand_thema_code("J Society & Social Sciences"), "J Society & Social Sciences")
        
        # Test with unknown code
        self.assertEqual(expand_thema_code("ZZZ"), "ZZZ")
        
        # Test with empty string
        self.assertEqual(expand_thema_code(""), "")
        
        # Test with None
        self.assertEqual(expand_thema_code(None), "")
    
    def test_thema_subject_mapping(self):
        """Test Thema subject mapping strategy."""
        # Test with single letter code
        strategy1 = ThemaSubjectMappingStrategy("thema_subject_1")
        result1 = strategy1.map_field(self.metadata, self.context)
        self.assertEqual(result1, "F Fiction & Related Items")
        
        # Test with multi-letter code
        strategy2 = ThemaSubjectMappingStrategy("thema_subject_2")
        result2 = strategy2.map_field(self.metadata, self.context)
        self.assertEqual(result2, "FBA Modern & Contemporary Fiction")
        
        # Test with code that already has description
        strategy3 = ThemaSubjectMappingStrategy("thema_subject_3")
        result3 = strategy3.map_field(self.metadata, self.context)
        self.assertEqual(result3, "J Society & Social Sciences")
        
        # Test with empty field
        self.metadata.thema_subject_1 = ""
        result4 = strategy1.map_field(self.metadata, self.context)
        self.assertEqual(result4, "")
        
        # Test with non-existent field
        strategy5 = ThemaSubjectMappingStrategy("non_existent_field", default_value="DEFAULT")
        result5 = strategy5.map_field(self.metadata, self.context)
        self.assertEqual(result5, "DEFAULT")


if __name__ == '__main__':
    unittest.main()