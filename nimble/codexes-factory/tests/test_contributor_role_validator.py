"""
Tests for contributor role validator.
"""

import os
import sys
import unittest
from unittest.mock import patch, mock_open

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.distribution.contributor_role_validator import ContributorRoleValidator


class TestContributorRoleValidator(unittest.TestCase):
    """Test cases for contributor role validator."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock CSV data for testing
        self.mock_csv_data = "Code,Description\nA,Author\nB,Editor\nC,Compiler\nD,Translator\n"
    
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    def test_load_valid_codes(self, mock_file, mock_exists):
        """Test loading valid contributor codes."""
        mock_file.return_value.read.return_value = self.mock_csv_data
        mock_file.return_value.__iter__.return_value = self.mock_csv_data.splitlines(True)
        
        # Create a validator with a custom codes file
        validator = ContributorRoleValidator("custom_codes.csv")
        
        # Check that default codes are available
        self.assertGreaterEqual(len(validator.valid_codes), 4)
        self.assertEqual(validator.valid_codes["A"], "Author")
        self.assertEqual(validator.valid_codes["B"], "Editor")
        self.assertEqual(validator.valid_codes["C"], "Compiler")
        self.assertEqual(validator.valid_codes["D"], "Translator")
    
    def test_is_valid_code(self):
        """Test validating contributor codes."""
        validator = ContributorRoleValidator()
        
        # Test valid codes
        self.assertTrue(validator.is_valid_code("A"))
        self.assertTrue(validator.is_valid_code("B"))
        self.assertTrue(validator.is_valid_code("C"))
        self.assertTrue(validator.is_valid_code("D"))
        
        # Test invalid codes
        self.assertFalse(validator.is_valid_code(""))
        self.assertFalse(validator.is_valid_code(None))
        
        # Test case insensitivity
        self.assertTrue(validator.is_valid_code("a"))
        self.assertTrue(validator.is_valid_code("b"))
    
    def test_get_code_description(self):
        """Test getting code descriptions."""
        validator = ContributorRoleValidator()
        
        # Test valid codes
        self.assertEqual(validator.get_code_description("A"), "Author")
        self.assertEqual(validator.get_code_description("B"), "Editor")
        
        # Test invalid codes
        self.assertIsNone(validator.get_code_description(""))
        self.assertIsNone(validator.get_code_description(None))
        
        # Test case insensitivity
        self.assertEqual(validator.get_code_description("a"), "Author")
        self.assertEqual(validator.get_code_description("b"), "Editor")
    
    def test_validate_and_correct(self):
        """Test validating and correcting contributor codes."""
        validator = ContributorRoleValidator()
        
        # Test valid codes
        is_valid, code, error = validator.validate_and_correct("A")
        self.assertTrue(is_valid)
        self.assertEqual(code, "A")
        self.assertIsNone(error)
        
        # Test empty code
        is_valid, code, error = validator.validate_and_correct("")
        self.assertFalse(is_valid)
        self.assertEqual(code, "A")  # Default to Author
        self.assertIsNotNone(error)
        
        # Test case insensitivity
        is_valid, code, error = validator.validate_and_correct("a")
        self.assertTrue(is_valid)
        self.assertEqual(code, "A")
        self.assertIsNone(error)


if __name__ == '__main__':
    unittest.main()