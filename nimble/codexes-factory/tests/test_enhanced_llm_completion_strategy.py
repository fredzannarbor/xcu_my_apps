"""
Tests for the enhanced LLM completion strategy.
"""

import unittest
import logging
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.abspath('src'))

from codexes.modules.metadata.metadata_models import CodexMetadata
from codexes.modules.distribution.enhanced_llm_completion_strategy import EnhancedLLMCompletionStrategy
from codexes.modules.distribution.field_mapping import MappingContext


class TestEnhancedLLMCompletionStrategy(unittest.TestCase):
    """Test cases for the EnhancedLLMCompletionStrategy class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock field completer
        self.field_completer = MagicMock()
        self.field_completer.prompt_field_mapping = {
            "generate_contributor_bio": "contributor_one_bio",
            "suggest_bisac_codes": ["bisac_category_2", "bisac_category_3"],
            "generate_keywords": "keywords",
            "create_short_description": "summary_short"
        }
        self.field_completer._complete_field.return_value = "New LLM completion"
        
        # Create a sample metadata object
        self.metadata = CodexMetadata()
        self.metadata.title = "Test Book"
        self.metadata.author = "Test Author"
        self.metadata.isbn13 = "9781234567890"
        
        # Create a mapping context
        self.context = MappingContext(
            field_name="contributor_one_bio",
            lsi_headers=["contributor_one_bio"],
            current_row_data={}
        )
    
    def test_direct_field_value(self):
        """Test that direct field values are used first."""
        # Set up direct field value
        self.metadata.contributor_one_bio = "Direct field value"
        
        # Create strategy
        strategy = EnhancedLLMCompletionStrategy(
            field_completer=self.field_completer,
            metadata_field="contributor_one_bio"
        )
        
        # Test
        result = strategy.map_field(self.metadata, self.context)
        
        # Verify
        self.assertEqual(result, "Direct field value")
        # Verify that _complete_field was not called
        self.field_completer._complete_field.assert_not_called()
    
    def test_llm_completions_value(self):
        """Test that values from llm_completions are used if direct field is empty."""
        # Set up llm_completions
        self.metadata.llm_completions = {
            "generate_contributor_bio": {
                "value": "Bio from llm_completions",
                "_completion_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "model": "test-model",
                    "prompt_key": "generate_contributor_bio"
                }
            }
        }
        
        # Create strategy
        strategy = EnhancedLLMCompletionStrategy(
            field_completer=self.field_completer,
            metadata_field="contributor_one_bio"
        )
        
        # Test
        result = strategy.map_field(self.metadata, self.context)
        
        # Verify
        self.assertEqual(result, "Bio from llm_completions")
        # Verify that _complete_field was not called
        self.field_completer._complete_field.assert_not_called()
    
    def test_llm_completions_dictionary(self):
        """Test extraction from dictionary in llm_completions."""
        # Set up llm_completions with dictionary result
        self.metadata.llm_completions = {
            "extract_lsi_contributor_info": {
                "contributor_one_bio": "Bio from dictionary",
                "contributor_one_affiliations": "Test University",
                "_completion_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "model": "test-model",
                    "prompt_key": "extract_lsi_contributor_info"
                }
            }
        }
        
        # Create strategy
        strategy = EnhancedLLMCompletionStrategy(
            field_completer=self.field_completer,
            metadata_field="contributor_one_bio"
        )
        
        # Test
        result = strategy.map_field(self.metadata, self.context)
        
        # Verify
        self.assertEqual(result, "Bio from dictionary")
        # Verify that _complete_field was not called
        self.field_completer._complete_field.assert_not_called()
    
    def test_explicit_prompt_key(self):
        """Test using an explicit prompt key."""
        # Set up llm_completions
        self.metadata.llm_completions = {
            "custom_prompt": {
                "value": "Bio from custom prompt",
                "_completion_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "model": "test-model",
                    "prompt_key": "custom_prompt"
                }
            }
        }
        
        # Create strategy with explicit prompt key
        strategy = EnhancedLLMCompletionStrategy(
            field_completer=self.field_completer,
            metadata_field="contributor_one_bio",
            prompt_key="custom_prompt"
        )
        
        # Test
        result = strategy.map_field(self.metadata, self.context)
        
        # Verify
        self.assertEqual(result, "Bio from custom prompt")
        # Verify that _complete_field was not called
        self.field_completer._complete_field.assert_not_called()
    
    def test_new_llm_completion(self):
        """Test generating a new LLM completion when no existing value is found."""
        # Create strategy
        strategy = EnhancedLLMCompletionStrategy(
            field_completer=self.field_completer,
            metadata_field="contributor_one_bio"
        )
        
        # Test
        result = strategy.map_field(self.metadata, self.context)
        
        # Verify
        self.assertEqual(result, "New LLM completion")
        # Verify that _complete_field was called
        self.field_completer._complete_field.assert_called_once_with(
            self.metadata, "contributor_one_bio"
        )
    
    def test_fallback_value(self):
        """Test using fallback value when LLM completion fails."""
        # Set up field completer to return None
        self.field_completer._complete_field.return_value = None
        
        # Create strategy with fallback value
        strategy = EnhancedLLMCompletionStrategy(
            field_completer=self.field_completer,
            metadata_field="contributor_one_bio",
            fallback_value="Fallback bio"
        )
        
        # Test
        result = strategy.map_field(self.metadata, self.context)
        
        # Verify
        self.assertEqual(result, "Fallback bio")
        # Verify that _complete_field was called
        self.field_completer._complete_field.assert_called_once_with(
            self.metadata, "contributor_one_bio"
        )
    
    def test_key_matching_in_dictionary(self):
        """Test key matching in dictionary results."""
        # Set up llm_completions with dictionary result and different key names
        self.metadata.llm_completions = {
            "extract_lsi_contributor_info": {
                "bio": "Bio from partial match",
                "affiliations": "Test University",
                "_completion_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "model": "test-model",
                    "prompt_key": "extract_lsi_contributor_info"
                }
            }
        }
        
        # Create strategy
        strategy = EnhancedLLMCompletionStrategy(
            field_completer=self.field_completer,
            metadata_field="contributor_one_bio"
        )
        
        # Test
        result = strategy.map_field(self.metadata, self.context)
        
        # Verify - should match "bio" as a partial match for "contributor_one_bio"
        self.assertEqual(result, "Bio from partial match")
        # Verify that _complete_field was not called
        self.field_completer._complete_field.assert_not_called()
    
    def test_error_handling(self):
        """Test error handling during field mapping."""
        # Set up field completer to raise an exception
        self.field_completer._complete_field.side_effect = Exception("Test error")
        
        # Create strategy with fallback value
        strategy = EnhancedLLMCompletionStrategy(
            field_completer=self.field_completer,
            metadata_field="contributor_one_bio",
            fallback_value="Error fallback"
        )
        
        # Test
        result = strategy.map_field(self.metadata, self.context)
        
        # Verify
        self.assertEqual(result, "Error fallback")
        # Verify that _complete_field was called
        self.field_completer._complete_field.assert_called_once_with(
            self.metadata, "contributor_one_bio"
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()