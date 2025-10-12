# tests/test_llm_integration.py

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import os

from codexes.modules.distribution.llm_field_completer import LLMFieldCompleter
from codexes.modules.distribution.field_mapping import (
    FieldMappingRegistry, 
    LLMCompletionStrategy,
    DirectMappingStrategy,
    MappingContext
)
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestLLMFieldCompleterIntegration:
    """Integration tests for LLM field completion with field mapping system."""
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata with some empty fields."""
        return CodexMetadata(
            title="Advanced Machine Learning Techniques",
            author="Dr. Sarah Johnson",
            publisher="Tech Publications",
            summary_long="A comprehensive guide to advanced machine learning algorithms and their applications in modern data science.",
            # These fields are empty and should be completed by LLM
            contributor_one_bio="",
            keywords="",
            summary_short="",
            bisac_codes="",
            audience=""
        )
    
    @pytest.fixture
    def mock_prompt_file(self, tmp_path):
        """Create a temporary prompt file for testing."""
        prompt_data = {
            "generate_contributor_bio": {
                "messages": [
                    {"role": "system", "content": "Generate professional bio"},
                    {"role": "user", "content": "Generate bio for {author} who wrote {title}"}
                ],
                "params": {"temperature": 0.7}
            },
            "suggest_bisac_codes": {
                "messages": [
                    {"role": "system", "content": "Suggest BISAC codes"},
                    {"role": "user", "content": "BISAC for {title}: {summary_long}"}
                ],
                "params": {"temperature": 0.3}
            },
            "generate_keywords": {
                "messages": [
                    {"role": "system", "content": "Generate keywords"},
                    {"role": "user", "content": "Keywords for {title}: {summary_long}"}
                ],
                "params": {"temperature": 0.6}
            }
        }
        
        prompt_file = tmp_path / "integration_prompts.json"
        with open(prompt_file, 'w') as f:
            json.dump(prompt_data, f)
        
        return str(prompt_file)
    
    @pytest.fixture
    def field_completer(self, mock_prompt_file):
        """Create LLMFieldCompleter instance."""
        return LLMFieldCompleter(
            prompt_file_path=mock_prompt_file,
            default_model="gpt-3.5-turbo"
        )
    
    @pytest.fixture
    def registry_with_llm(self, field_completer):
        """Create field mapping registry with LLM completion strategies."""
        registry = FieldMappingRegistry()
        
        # Register direct mappings for basic fields
        registry.register_strategy("Title", DirectMappingStrategy("title"))
        registry.register_strategy("Author", DirectMappingStrategy("author"))
        registry.register_strategy("Publisher", DirectMappingStrategy("publisher"))
        
        # Register LLM completion strategies for fields that can be enhanced
        registry.register_strategy("Contributor Bio", 
                                 LLMCompletionStrategy(field_completer, "contributor_one_bio", "No bio available"))
        registry.register_strategy("Keywords", 
                                 LLMCompletionStrategy(field_completer, "keywords", ""))
        registry.register_strategy("BISAC Codes", 
                                 LLMCompletionStrategy(field_completer, "bisac_codes", ""))
        
        return registry
    
    @patch('src.codexes.modules.distribution.llm_field_completer.call_model_with_prompt')
    @patch('src.codexes.modules.distribution.llm_field_completer.load_and_prepare_prompts')
    def test_llm_completion_strategy_integration(self, mock_load_prompts, mock_call_model, 
                                               registry_with_llm, sample_metadata):
        """Test LLM completion strategy working within field mapping registry."""
        # Mock successful prompt loading
        mock_load_prompts.return_value = [{
            'key': 'generate_contributor_bio',
            'prompt_config': {
                'messages': [{'role': 'user', 'content': 'Generate bio'}],
                'params': {'temperature': 0.7}
            }
        }]
        
        # Mock LLM response
        mock_call_model.return_value = {
            'raw_content': 'Dr. Sarah Johnson is a leading expert in machine learning and data science.',
            'parsed_content': 'Dr. Sarah Johnson is a leading expert in machine learning and data science.'
        }
        
        # Test field mapping with LLM completion
        lsi_headers = ["Title", "Author", "Publisher", "Contributor Bio"]
        results = registry_with_llm.apply_mappings(sample_metadata, lsi_headers)
        
        # Verify direct mappings work
        assert results["Title"] == "Advanced Machine Learning Techniques"
        assert results["Author"] == "Dr. Sarah Johnson"
        assert results["Publisher"] == "Tech Publications"
        
        # Verify LLM completion was called and result used
        assert results["Contributor Bio"] == "Dr. Sarah Johnson is a leading expert in machine learning and data science."
        mock_call_model.assert_called_once()
    
    @patch('src.codexes.modules.distribution.llm_field_completer.call_model_with_prompt')
    @patch('src.codexes.modules.distribution.llm_field_completer.load_and_prepare_prompts')
    def test_llm_completion_fallback_on_failure(self, mock_load_prompts, mock_call_model, 
                                               registry_with_llm, sample_metadata):
        """Test LLM completion strategy falls back to default when LLM fails."""
        # Mock prompt loading failure
        mock_load_prompts.return_value = None
        
        # Test field mapping with LLM completion failure
        lsi_headers = ["Contributor Bio"]
        results = registry_with_llm.apply_mappings(sample_metadata, lsi_headers)
        
        # Should use fallback value
        assert results["Contributor Bio"] == "No bio available"
        mock_call_model.assert_not_called()
    
    @patch('src.codexes.modules.distribution.llm_field_completer.call_model_with_prompt')
    @patch('src.codexes.modules.distribution.llm_field_completer.load_and_prepare_prompts')
    def test_llm_completion_with_existing_value(self, mock_load_prompts, mock_call_model, 
                                              registry_with_llm, sample_metadata):
        """Test LLM completion strategy uses existing value when present."""
        # Set existing bio
        sample_metadata.contributor_one_bio = "Existing bio content"
        
        # Test field mapping
        lsi_headers = ["Contributor Bio"]
        results = registry_with_llm.apply_mappings(sample_metadata, lsi_headers)
        
        # Should use existing value, not call LLM
        assert results["Contributor Bio"] == "Existing bio content"
        mock_call_model.assert_not_called()
        mock_load_prompts.assert_not_called()
    
    @patch('src.codexes.modules.distribution.llm_field_completer.call_model_with_prompt')
    @patch('src.codexes.modules.distribution.llm_field_completer.load_and_prepare_prompts')
    def test_multiple_llm_completions(self, mock_load_prompts, mock_call_model, 
                                    registry_with_llm, sample_metadata):
        """Test multiple LLM completions in single mapping operation."""
        # Mock successful prompt loading for different prompts
        def mock_load_side_effect(prompt_file, prompt_keys, substitutions):
            if 'generate_contributor_bio' in prompt_keys:
                return [{
                    'key': 'generate_contributor_bio',
                    'prompt_config': {'messages': [{'role': 'user', 'content': 'bio prompt'}]}
                }]
            elif 'generate_keywords' in prompt_keys:
                return [{
                    'key': 'generate_keywords', 
                    'prompt_config': {'messages': [{'role': 'user', 'content': 'keywords prompt'}]}
                }]
            return None
        
        mock_load_prompts.side_effect = mock_load_side_effect
        
        # Mock different LLM responses
        def mock_call_side_effect(model_name, prompt_config, **kwargs):
            if 'bio prompt' in str(prompt_config):
                return {
                    'raw_content': 'Generated bio content',
                    'parsed_content': 'Generated bio content'
                }
            elif 'keywords prompt' in str(prompt_config):
                return {
                    'raw_content': 'machine learning; data science; algorithms',
                    'parsed_content': 'machine learning; data science; algorithms'
                }
            return {'raw_content': '', 'parsed_content': {'error': 'Unknown prompt'}}
        
        mock_call_model.side_effect = mock_call_side_effect
        
        # Test multiple LLM completions
        lsi_headers = ["Title", "Contributor Bio", "Keywords"]
        results = registry_with_llm.apply_mappings(sample_metadata, lsi_headers)
        
        # Verify all fields completed correctly
        assert results["Title"] == "Advanced Machine Learning Techniques"
        assert results["Contributor Bio"] == "Generated bio content"
        assert results["Keywords"] == "machine learning; data science; algorithms"
        
        # Verify LLM was called twice (once for bio, once for keywords)
        assert mock_call_model.call_count == 2
    
    def test_llm_completion_strategy_initialization(self, field_completer):
        """Test LLM completion strategy initialization."""
        strategy = LLMCompletionStrategy(
            field_completer=field_completer,
            metadata_field="contributor_one_bio",
            fallback_value="Default bio"
        )
        
        assert strategy.field_completer == field_completer
        assert strategy.metadata_field == "contributor_one_bio"
        assert strategy.fallback_value == "Default bio"
    
    @patch('src.codexes.modules.distribution.llm_field_completer.call_model_with_prompt')
    @patch('src.codexes.modules.distribution.llm_field_completer.load_and_prepare_prompts')
    def test_end_to_end_metadata_enhancement(self, mock_load_prompts, mock_call_model, 
                                           field_completer, sample_metadata):
        """Test end-to-end metadata enhancement using LLM field completer."""
        # Mock successful LLM responses for different fields
        def mock_load_side_effect(prompt_file, prompt_keys, substitutions):
            return [{
                'key': prompt_keys[0],
                'prompt_config': {'messages': [{'role': 'user', 'content': f'prompt for {prompt_keys[0]}'}]}
            }]
        
        def mock_call_side_effect(model_name, prompt_config, **kwargs):
            prompt_content = str(prompt_config)
            if 'generate_contributor_bio' in prompt_content:
                return {
                    'raw_content': 'Dr. Sarah Johnson is a renowned expert in machine learning.',
                    'parsed_content': 'Dr. Sarah Johnson is a renowned expert in machine learning.'
                }
            elif 'generate_keywords' in prompt_content:
                return {
                    'raw_content': 'machine learning; artificial intelligence; data science; algorithms',
                    'parsed_content': 'machine learning; artificial intelligence; data science; algorithms'
                }
            elif 'suggest_bisac_codes' in prompt_content:
                return {
                    'raw_content': 'COM004000; COM021030',
                    'parsed_content': 'COM004000; COM021030'
                }
            return {'raw_content': '', 'parsed_content': {'error': 'Unknown'}}
        
        mock_load_prompts.side_effect = mock_load_side_effect
        mock_call_model.side_effect = mock_call_side_effect
        
        # Enhance metadata using field completer
        enhanced_metadata = field_completer.complete_missing_fields(
            sample_metadata,
            fields_to_complete=['contributor_one_bio', 'keywords', 'bisac_codes']
        )
        
        # Verify enhancements
        assert enhanced_metadata.contributor_one_bio == 'Dr. Sarah Johnson is a renowned expert in machine learning.'
        assert enhanced_metadata.keywords == 'machine learning; artificial intelligence; data science; algorithms'
        assert enhanced_metadata.bisac_codes == 'COM004000; COM021030'
        
        # Original fields should remain unchanged
        assert enhanced_metadata.title == sample_metadata.title
        assert enhanced_metadata.author == sample_metadata.author
        assert enhanced_metadata.summary_long == sample_metadata.summary_long
    
    def test_registry_stats_with_llm_strategies(self, registry_with_llm):
        """Test registry statistics include LLM completion strategies."""
        stats = registry_with_llm.get_registry_stats()
        
        assert stats["total_strategies"] > 0
        assert "LLMCompletionStrategy" in stats["strategy_types"]
        assert "DirectMappingStrategy" in stats["strategy_types"]
        
        # Should have multiple LLM completion strategies
        assert stats["strategy_types"]["LLMCompletionStrategy"] >= 3
    
    @patch('src.codexes.modules.distribution.llm_field_completer.call_model_with_prompt')
    @patch('src.codexes.modules.distribution.llm_field_completer.load_and_prepare_prompts')
    def test_error_handling_in_llm_strategy(self, mock_load_prompts, mock_call_model, 
                                          registry_with_llm, sample_metadata):
        """Test error handling in LLM completion strategy."""
        # Mock prompt loading success but LLM call failure
        mock_load_prompts.return_value = [{
            'key': 'generate_contributor_bio',
            'prompt_config': {'messages': [{'role': 'user', 'content': 'test'}]}
        }]
        
        # Mock LLM call raising exception
        mock_call_model.side_effect = Exception("API Error")
        
        # Test field mapping with error
        lsi_headers = ["Contributor Bio"]
        results = registry_with_llm.apply_mappings(sample_metadata, lsi_headers)
        
        # Should use fallback value on error
        assert results["Contributor Bio"] == "No bio available"
    
    def test_mapping_context_with_llm_strategy(self, field_completer, sample_metadata):
        """Test that mapping context is properly passed to LLM strategy."""
        strategy = LLMCompletionStrategy(
            field_completer=field_completer,
            metadata_field="contributor_one_bio",
            fallback_value="Default"
        )
        
        context = MappingContext(
            field_name="Contributor Bio",
            lsi_headers=["Title", "Contributor Bio"],
            current_row_data={"Title": "Test Book"},
            metadata=sample_metadata
        )
        
        # Test that strategy can access context (even if LLM call fails)
        with patch.object(field_completer, '_complete_field', return_value=None):
            result = strategy.map_field(sample_metadata, context)
            assert result == "Default"  # Should use fallback


# Performance and stress tests
class TestLLMIntegrationPerformance:
    """Performance tests for LLM integration."""
    
    @pytest.fixture
    def large_metadata_list(self):
        """Create a list of metadata objects for batch testing."""
        metadata_list = []
        for i in range(5):  # Small number for testing
            metadata = CodexMetadata(
                title=f"Book Title {i}",
                author=f"Author {i}",
                summary_long=f"Summary for book {i}",
                contributor_one_bio="",  # Empty field to complete
                keywords=""  # Empty field to complete
            )
            metadata_list.append(metadata)
        return metadata_list
    
    @patch('src.codexes.modules.distribution.llm_field_completer.call_model_with_prompt')
    @patch('src.codexes.modules.distribution.llm_field_completer.load_and_prepare_prompts')
    def test_batch_completion_performance(self, mock_load_prompts, mock_call_model, 
                                        large_metadata_list):
        """Test batch completion performance."""
        # Mock successful responses
        mock_load_prompts.return_value = [{
            'key': 'test_prompt',
            'prompt_config': {'messages': [{'role': 'user', 'content': 'test'}]}
        }]
        
        mock_call_model.return_value = {
            'raw_content': 'Generated content',
            'parsed_content': 'Generated content'
        }
        
        # Create field completer
        completer = LLMFieldCompleter()
        
        # Test batch completion
        enhanced_list = completer.batch_complete_fields(
            large_metadata_list,
            fields_to_complete=['contributor_one_bio']
        )
        
        # Verify all items processed
        assert len(enhanced_list) == len(large_metadata_list)
        
        # Verify LLM was called for each item
        assert mock_call_model.call_count == len(large_metadata_list)