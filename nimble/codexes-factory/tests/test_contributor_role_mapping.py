"""
Tests for contributor role mapping.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.distribution.contributor_role_mapping import ContributorRoleMappingStrategy
from codexes.modules.distribution.field_mapping import MappingContext
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestContributorRoleMapping(unittest.TestCase):
    """Test cases for contributor role mapping."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.metadata = CodexMetadata()
        self.metadata.contributor_one_role = "A"
        self.metadata.contributor_two_role = "X"  # Invalid code
        
        # Create a mock context
        self.context = MagicMock(spec=MappingContext)
        self.context.field_name = "Contributor One Role"
        self.context.lsi_headers = ["Contributor One Role", "Contributor Two Role"]
        self.context.current_row_data = {}
    
    def test_contributor_role_mapping(self):
        """Test contributor role mapping strategy."""
        # Test with valid code
        strategy = ContributorRoleMappingStrategy("contributor_one_role")
        result = strategy.map_field(self.metadata, self.context)
        self.assertEqual(result, "A")
        
        # Test with empty field
        self.metadata.contributor_one_role = ""
        result = strategy.map_field(self.metadata, self.context)
        self.assertEqual(result, "A")  # Should use default
        
        # Test with non-existent field
        strategy = ContributorRoleMappingStrategy("non_existent_field", default_value="B")
        result = strategy.map_field(self.metadata, self.context)
        self.assertEqual(result, "B")  # Should use specified default


if __name__ == '__main__':
    unittest.main()