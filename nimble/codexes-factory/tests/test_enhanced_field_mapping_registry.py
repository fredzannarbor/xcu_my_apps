"""
Tests for the enhanced field mapping registry.
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
from codexes.modules.distribution.field_mapping_registry import create_enhanced_lsi_registry
from codexes.modules.distribution.field_mapping import MappingContext
from codexes.modules.distribution.enhanced_llm_completion_strategy import EnhancedLLMCompletionStrategy


class TestEnhancedFieldMappingRegistry(unittest.TestCase):
    """Test cases for the enhanced field mapping registry."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock field completer
        self.field_completer = MagicMock()
        self.field_completer.prompt_field_mapping = {
            "generate_contributor_bio": "contributor_one_bio",
            "suggest_bisac_codes": ["bisac_category_2", "bisac_category_3"],
            "generate_keywords": "keywords",
            "create_short_description": "summary_short",
            "suggest_thema_subjects": ["thema_subject_1", "thema_subject_2", "thema_subject_3"],
            "determine_audience": "audience",
            "determine_age_range": ["min_age", "max_age"],
            "extract_lsi_contributor_info": [
                "contributor_one_bio", 
                "contributor_one_affiliations",
                "contributor_one_professional_position",
                "contributor_one_location",
                "contributor_one_prior_work"
            ],
            "suggest_series_info": ["series_name", "series_number"]
        }
        self.field_completer._complete_field.return_value = "New LLM completion"
        
        # Create a sample metadata object
        self.metadata = CodexMetadata()
        self.metadata.title = "Test Book"
        self.metadata.author = "Test Author"
        self.metadata.isbn13 = "9781234567890"
        self.metadata.llm_completions = {
            "generate_contributor_bio": {
                "value": "Test Author is a renowned expert in testing.",
                "_completion_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "model": "test-model",
                    "prompt_key": "generate_contributor_bio"
                }
            },
            "suggest_bisac_codes": {
                "bisac_category_2": "COM051010",
                "bisac_category_3": "COM051020",
                "_completion_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "model": "test-model",
                    "prompt_key": "suggest_bisac_codes"
                }
            }
        }
        
        # Mock the create_comprehensive_lsi_registry function
        self.mock_create_comprehensive = MagicMock()
        self.mock_create_comprehensive.return_value = MagicMock()
    
    def test_create_enhanced_registry(self):
        """Test creating an enhanced registry."""
        # Set up mock
        with patch('src.codexes.modules.distribution.enhanced_field_mappings.create_comprehensive_lsi_registry') as mock_create_comprehensive:
            registry = MagicMock()
            mock_create_comprehensive.return_value = registry
            
            # Create enhanced registry
            with patch('src.codexes.modules.distribution.field_mapping_registry.create_comprehensive_lsi_registry', mock_create_comprehensive):
                enhanced_registry = create_enhanced_lsi_registry(
                    config=None,
                    llm_field_completer=self.field_completer
                )
            
            # Verify that create_comprehensive_lsi_registry was called
            mock_create_comprehensive.assert_called_once_with(None, self.field_completer)
            
            # Verify that register_strategy was called for enhanced fields
            self.assertTrue(registry.register_strategy.called)
            
            # Check that at least one call was for an EnhancedLLMCompletionStrategy
            enhanced_strategy_calls = 0
            for call in registry.register_strategy.call_args_list:
                args, kwargs = call
                if len(args) >= 2 and isinstance(args[1], EnhancedLLMCompletionStrategy):
                    enhanced_strategy_calls += 1
            
            self.assertGreater(enhanced_strategy_calls, 0)
    
    def test_no_llm_field_completer(self):
        """Test creating an enhanced registry without an LLM field completer."""
        # Set up mock
        with patch('src.codexes.modules.distribution.enhanced_field_mappings.create_comprehensive_lsi_registry') as mock_create_comprehensive:
            registry = MagicMock()
            mock_create_comprehensive.return_value = registry
            
            # Create enhanced registry without field completer
            with patch('src.codexes.modules.distribution.field_mapping_registry.create_comprehensive_lsi_registry', mock_create_comprehensive):
                enhanced_registry = create_enhanced_lsi_registry(config=None, llm_field_completer=None)
            
            # Verify that create_comprehensive_lsi_registry was called
            mock_create_comprehensive.assert_called_once_with(None, None)
            
            # Verify that the base registry was returned without enhancement
            self.assertEqual(enhanced_registry, registry)
    
    def test_contributor_fields_enhancement(self):
        """Test enhancement of contributor fields."""
        # Set up mock
        with patch('src.codexes.modules.distribution.enhanced_field_mappings.create_comprehensive_lsi_registry') as mock_create_comprehensive:
            registry = MagicMock()
            mock_create_comprehensive.return_value = registry
            
            # Create enhanced registry
            with patch('src.codexes.modules.distribution.field_mapping_registry.create_comprehensive_lsi_registry', mock_create_comprehensive):
                enhanced_registry = create_enhanced_lsi_registry(
                    config=None,
                    llm_field_completer=self.field_completer
                )
            
            # Verify that register_strategy was called for contributor fields
            contributor_fields = [
                "Contributor One BIO",
                "Contributor One Affiliations",
                "Contributor One Professional Position",
                "Contributor One Location",
                "Contributor One Prior Work"
            ]
            
            for field in contributor_fields:
                found = False
                for call in registry.register_strategy.call_args_list:
                    args, kwargs = call
                    if len(args) >= 1 and args[0] == field:
                        found = True
                        break
                self.assertTrue(found, f"Field {field} was not registered")
    
    def test_classification_fields_enhancement(self):
        """Test enhancement of classification fields."""
        # Set up mock
        with patch('src.codexes.modules.distribution.enhanced_field_mappings.create_comprehensive_lsi_registry') as mock_create_comprehensive:
            registry = MagicMock()
            mock_create_comprehensive.return_value = registry
            
            # Create enhanced registry
            with patch('src.codexes.modules.distribution.field_mapping_registry.create_comprehensive_lsi_registry', mock_create_comprehensive):
                enhanced_registry = create_enhanced_lsi_registry(
                    config=None,
                    llm_field_completer=self.field_completer
                )
            
            # Verify that register_strategy was called for classification fields
            classification_fields = [
                "BISAC Category 2",
                "BISAC Category 3",
                "Thema Subject 1",
                "Thema Subject 2",
                "Thema Subject 3",
                "Keywords"
            ]
            
            for field in classification_fields:
                found = False
                for call in registry.register_strategy.call_args_list:
                    args, kwargs = call
                    if len(args) >= 1 and args[0] == field:
                        found = True
                        break
                self.assertTrue(found, f"Field {field} was not registered")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()