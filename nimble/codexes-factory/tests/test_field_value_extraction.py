"""
Tests for the field value extraction logic in the enhanced LLM completion strategy.
"""

import unittest
import logging
from unittest.mock import MagicMock
import sys
import os
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.abspath('src'))

from codexes.modules.distribution.enhanced_llm_completion_strategy import EnhancedLLMCompletionStrategy


class TestFieldValueExtraction(unittest.TestCase):
    """Test cases for the field value extraction logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock field completer
        self.field_completer = MagicMock()
        
        # Create a strategy for testing
        self.strategy = EnhancedLLMCompletionStrategy(
            field_completer=self.field_completer,
            metadata_field="contributor_one_bio"
        )
    
    def test_extract_from_dict_direct_match(self):
        """Test extracting a value with a direct key match."""
        result_dict = {
            "contributor_one_bio": "Direct match bio",
            "contributor_one_affiliations": "Test University"
        }
        
        value = self.strategy._extract_from_dict(result_dict, "contributor_one_bio")
        self.assertEqual(value, "Direct match bio")
    
    def test_extract_from_dict_case_insensitive_match(self):
        """Test extracting a value with a case-insensitive key match."""
        result_dict = {
            "Contributor_One_Bio": "Case insensitive match bio",
            "contributor_one_affiliations": "Test University"
        }
        
        value = self.strategy._extract_from_dict(result_dict, "contributor_one_bio")
        self.assertEqual(value, "Case insensitive match bio")
    
    def test_extract_from_dict_partial_match(self):
        """Test extracting a value with a partial key match."""
        result_dict = {
            "bio": "Partial match bio",
            "affiliations": "Test University"
        }
        
        value = self.strategy._extract_from_dict(result_dict, "contributor_one_bio")
        self.assertEqual(value, "Partial match bio")
    
    def test_extract_from_dict_word_based_match(self):
        """Test extracting a value with a word-based key match."""
        result_dict = {
            "author_bio": "Word-based match bio",
            "affiliations": "Test University"
        }
        
        value = self.strategy._extract_from_dict(result_dict, "contributor_one_bio")
        self.assertEqual(value, "Word-based match bio")
    
    def test_extract_from_dict_single_value(self):
        """Test extracting a value from a dictionary with a single value."""
        result_dict = {
            "value": "Single value bio"
        }
        
        value = self.strategy._extract_from_dict(result_dict, "contributor_one_bio")
        self.assertEqual(value, "Single value bio")
    
    def test_extract_from_dict_no_match(self):
        """Test extracting a value with no matching key."""
        result_dict = {
            "unrelated_key": "Unrelated value",
            "another_key": "Another value"
        }
        
        value = self.strategy._extract_from_dict(result_dict, "contributor_one_bio")
        self.assertIsNone(value)
    
    def test_extract_from_dict_empty_dict(self):
        """Test extracting a value from an empty dictionary."""
        result_dict = {}
        
        value = self.strategy._extract_from_dict(result_dict, "contributor_one_bio")
        self.assertIsNone(value)
    
    def test_extract_from_dict_none_value(self):
        """Test extracting a None value."""
        result_dict = {
            "contributor_one_bio": None
        }
        
        value = self.strategy._extract_from_dict(result_dict, "contributor_one_bio")
        self.assertIsNone(value)
    
    def test_extract_from_dict_invalid_input(self):
        """Test extracting a value from an invalid input."""
        # Test with None
        value = self.strategy._extract_from_dict(None, "contributor_one_bio")
        self.assertIsNone(value)
        
        # Test with non-dictionary
        value = self.strategy._extract_from_dict("not a dict", "contributor_one_bio")
        self.assertIsNone(value)
    
    def test_extract_completion_value_with_metadata(self):
        """Test extracting a completion value with metadata structure."""
        llm_completions = {
            "generate_contributor_bio": {
                "value": "Bio with metadata",
                "_completion_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "model": "test-model",
                    "prompt_key": "generate_contributor_bio"
                }
            }
        }
        
        value = self.strategy._extract_completion_value(
            llm_completions, "generate_contributor_bio", "contributor_one_bio"
        )
        self.assertEqual(value, "Bio with metadata")
    
    def test_extract_completion_value_with_field_dict(self):
        """Test extracting a completion value from a dictionary with field keys."""
        llm_completions = {
            "extract_lsi_contributor_info": {
                "contributor_one_bio": "Bio from field dict",
                "contributor_one_affiliations": "Test University",
                "_completion_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "model": "test-model",
                    "prompt_key": "extract_lsi_contributor_info"
                }
            }
        }
        
        value = self.strategy._extract_completion_value(
            llm_completions, "extract_lsi_contributor_info", "contributor_one_bio"
        )
        self.assertEqual(value, "Bio from field dict")
    
    def test_extract_completion_value_string_result(self):
        """Test extracting a completion value that is a string."""
        llm_completions = {
            "generate_contributor_bio": "Direct string bio"
        }
        
        value = self.strategy._extract_completion_value(
            llm_completions, "generate_contributor_bio", "contributor_one_bio"
        )
        self.assertEqual(value, "Direct string bio")
    
    def test_extract_completion_value_other_type(self):
        """Test extracting a completion value of another type."""
        llm_completions = {
            "generate_contributor_bio": 12345
        }
        
        value = self.strategy._extract_completion_value(
            llm_completions, "generate_contributor_bio", "contributor_one_bio"
        )
        self.assertEqual(value, "12345")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()