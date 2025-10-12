# tests/test_llm_field_completer.py

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os

from codexes.modules.distribution.llm_field_completer import LLMFieldCompleter
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestLLMFieldCompleter:
    """Test suite for LLMFieldCompleter class."""
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata for testing."""
        return CodexMetadata(
            title="The Future of AI",
            author="Dr. Jane Smith",
            publisher="Tech Books Inc",
            summary_long="A comprehensive exploration of artificial intelligence and its impact on society.",
            summary_short="",  # Empty - should be completed
            keywords="",  # Empty - should be completed
            bisac_codes="",  # Empty - should be completed
            contributor_one_bio="",  # Empty - should be completed
            audience="",  # Empty - should be completed
            min_age="",  # Empty - should be completed
            isbn13="9781234567890"  # Protected field
        )
    
    @pytest.fixture
    def mock_prompts_file(self):
        """Create a temporary prompts file for testing."""
        prompts_data = {
            "generate_contributor_bio": {
                "messages": [
                    {
                        "role": "system",
                        "content": "Generate a professional bio."
                    },
                    {
                        "role": "user",
                        "content": "Generate bio for {author} who wrote {title}."
                    }
                ],
                "params": {
                    "temperature": 0.7,
                    "max_tokens": 200
                }
            },
            "suggest_bisac_codes": {
                "messages": [
                    {
                        "role": "user",
                        "content": "Suggest BISAC codes for {title} by {author}."
                    }
                ],
                "params": {
                    "temperature": 0.3
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(prompts_data, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    @pytest.fixture
    def completer(self, mock_prompts_file):
        """Create LLMFieldCompleter instance with mocked prompts file."""
        return LLMFieldCompleter(
            prompt_file_path=mock_prompts_file,
            default_model="gpt-3.5-turbo"
        )
    
    def test_initialization(self, mock_prompts_file):
        """Test LLMFieldCompleter initialization."""
        completer = LLMFieldCompleter(
            prompt_file_path=mock_prompts_file,
            default_model="gpt-4"
        )
        
        assert completer.prompt_file_path == mock_prompts_file
        assert completer.default_model == "gpt-4"
        assert "contributor_one_bio" in completer.field_prompt_mapping
        assert "isbn13" in completer.protected_fields
    
    def test_identify_empty_fields(self, completer, sample_metadata):
        """Test identification of empty fields."""
        empty_fields = completer._identify_empty_fields(sample_metadata)
        
        expected_empty = [
            'contributor_one_bio', 'bisac_codes', 'keywords', 
            'summary_short', 'audience', 'min_age'
        ]
        
        for field in expected_empty:
            assert field in empty_fields
        
        # Should not include fields with values
        assert 'title' not in empty_fields
        assert 'author' not in empty_fields
    
    def test_prepare_substitutions(self, completer, sample_metadata):
        """Test preparation of substitution variables."""
        substitutions = completer._prepare_substitutions('contributor_one_bio', sample_metadata)
        
        assert substitutions['title'] == "The Future of AI"
        assert substitutions['author'] == "Dr. Jane Smith"
        assert substitutions['publisher'] == "Tech Books Inc"
        assert substitutions['summary_long'] == sample_metadata.summary_long
        assert substitutions['current_value'] == ""
    
    def test_prepare_substitutions_age_fields(self, completer, sample_metadata):
        """Test substitutions for age-related fields."""
        substitutions = completer._prepare_substitutions('min_age', sample_metadata)
        
        assert substitutions['field_name'] == 'min_age'
        assert 'title' in substitutions
        assert 'author' in substitutions
    
    @patch('src.codexes.modules.distribution.llm_field_completer.call_model_with_prompt')
    @patch('src.codexes.modules.distribution.llm_field_completer.load_and_prepare_prompts')
    def test_call_completion_prompt_success(self, mock_load_prompts, mock_call_model, completer):
        """Test successful completion prompt call."""
        # Mock prompt loading
        mock_load_prompts.return_value = [{
            'prompt_config': {
                'messages': [{'role': 'user', 'content': 'test prompt'}],
                'params': {}
            }
        }]
        
        # Mock LLM response
        mock_call_model.return_value = {
            'raw_content': 'Generated bio content',
            'parsed_content': 'Generated bio content'
        }
        
        result = completer._call_completion_prompt(
            'generate_contributor_bio',
            {'author': 'Test Author', 'title': 'Test Title'},
            'gpt-3.5-turbo'
        )
        
        assert result == 'Generated bio content'
        mock_load_prompts.assert_called_once()
        mock_call_model.assert_called_once()
    
    @patch('src.codexes.modules.distribution.llm_field_completer.call_model_with_prompt')
    @patch('src.codexes.modules.distribution.llm_field_completer.load_and_prepare_prompts')
    def test_call_completion_prompt_failure(self, mock_load_prompts, mock_call_model, completer):
        """Test completion prompt call failure."""
        # Mock prompt loading failure
        mock_load_prompts.return_value = None
        
        result = completer._call_completion_prompt(
            'generate_contributor_bio',
            {'author': 'Test Author'},
            'gpt-3.5-turbo'
        )
        
        assert result is None
        mock_call_model.assert_not_called()
    
    @patch('src.codexes.modules.distribution.llm_field_completer.call_model_with_prompt')
    @patch('src.codexes.modules.distribution.llm_field_completer.load_and_prepare_prompts')
    def test_call_completion_prompt_error_response(self, mock_load_prompts, mock_call_model, completer):
        """Test handling of error responses from LLM."""
        mock_load_prompts.return_value = [{
            'prompt_config': {
                'messages': [{'role': 'user', 'content': 'test'}],
                'params': {}
            }
        }]
        
        # Mock error response
        mock_call_model.return_value = {
            'raw_content': 'error: failed to generate',
            'parsed_content': 'error: failed to generate'
        }
        
        result = completer._call_completion_prompt(
            'generate_contributor_bio',
            {'author': 'Test Author'},
            'gpt-3.5-turbo'
        )
        
        assert result is None
    
    def test_complete_field_no_mapping(self, completer, sample_metadata):
        """Test completing field with no prompt mapping."""
        result = completer._complete_field('nonexistent_field', sample_metadata, 'gpt-3.5-turbo')
        assert result is None
    
    @patch.object(LLMFieldCompleter, '_call_completion_prompt')
    def test_complete_field_success(self, mock_call_prompt, completer, sample_metadata):
        """Test successful field completion."""
        mock_call_prompt.return_value = "Generated bio content"
        
        result = completer._complete_field('contributor_one_bio', sample_metadata, 'gpt-3.5-turbo')
        
        assert result == "Generated bio content"
        mock_call_prompt.assert_called_once()
    
    @patch.object(LLMFieldCompleter, '_complete_field')
    def test_complete_missing_fields_all(self, mock_complete_field, completer, sample_metadata):
        """Test completing all missing fields."""
        mock_complete_field.return_value = "completed_value"
        
        result = completer.complete_missing_fields(sample_metadata)
        
        # Should have called _complete_field for each empty field
        assert mock_complete_field.call_count > 0
        
        # Result should be a new CodexMetadata instance
        assert isinstance(result, CodexMetadata)
        assert result.title == sample_metadata.title  # Original values preserved
    
    @patch.object(LLMFieldCompleter, '_complete_field')
    def test_complete_missing_fields_specific(self, mock_complete_field, completer, sample_metadata):
        """Test completing specific fields only."""
        mock_complete_field.return_value = "completed_bio"
        
        result = completer.complete_missing_fields(
            sample_metadata, 
            fields_to_complete=['contributor_one_bio']
        )
        
        # Should only call _complete_field once for the specified field
        mock_complete_field.assert_called_once_with(
            'contributor_one_bio', 
            result, 
            'gpt-3.5-turbo'
        )
    
    def test_complete_missing_fields_protected_fields_filtered(self, completer, sample_metadata):
        """Test that protected fields are not completed."""
        with patch.object(completer, '_complete_field') as mock_complete:
            completer.complete_missing_fields(
                sample_metadata,
                fields_to_complete=['isbn13', 'contributor_one_bio']  # isbn13 is protected
            )
            
            # Should only be called for non-protected field
            mock_complete.assert_called_once()
            args = mock_complete.call_args[0]
            assert args[0] == 'contributor_one_bio'
    
    @patch.object(LLMFieldCompleter, '_call_completion_prompt')
    def test_generate_contributor_bio(self, mock_call_prompt, completer):
        """Test contributor bio generation."""
        mock_call_prompt.return_value = "Dr. Jane Smith is a leading expert in AI research."
        
        result = completer.generate_contributor_bio(
            author="Dr. Jane Smith",
            title="The Future of AI",
            publisher="Tech Books",
            summary="AI exploration"
        )
        
        assert result == "Dr. Jane Smith is a leading expert in AI research."
        mock_call_prompt.assert_called_once_with(
            'generate_contributor_bio',
            {
                'title': 'The Future of AI',
                'author': 'Dr. Jane Smith',
                'publisher': 'Tech Books',
                'summary_short': 'AI exploration'
            },
            'gpt-3.5-turbo'
        )
    
    @patch.object(LLMFieldCompleter, '_call_completion_prompt')
    def test_suggest_bisac_codes(self, mock_call_prompt, completer, sample_metadata):
        """Test BISAC code suggestion."""
        mock_call_prompt.return_value = "COM004000; TEC009000"
        
        result = completer.suggest_bisac_codes(sample_metadata)
        
        assert result == "COM004000; TEC009000"
        mock_call_prompt.assert_called_once()
        
        # Check substitutions
        call_args = mock_call_prompt.call_args[0]
        substitutions = call_args[1]
        assert substitutions['title'] == sample_metadata.title
        assert substitutions['author'] == sample_metadata.author
    
    @patch.object(LLMFieldCompleter, '_call_completion_prompt')
    def test_generate_marketing_copy(self, mock_call_prompt, completer, sample_metadata):
        """Test marketing copy generation."""
        mock_call_prompt.side_effect = [
            "Compelling short description",
            "Great review quotes",
            "AI; technology; future"
        ]
        
        result = completer.generate_marketing_copy(sample_metadata)
        
        assert 'summary_short' in result
        assert 'review_quotes' in result
        assert 'keywords' in result
        assert result['summary_short'] == "Compelling short description"
        assert mock_call_prompt.call_count == 3
    
    @patch.object(LLMFieldCompleter, '_call_completion_prompt')
    def test_generate_marketing_copy_existing_values(self, mock_call_prompt, completer, sample_metadata):
        """Test that marketing copy is not generated for existing values."""
        # Set existing values
        sample_metadata.summary_short = "Existing description"
        sample_metadata.review_quotes = "Existing quotes"
        sample_metadata.keywords = "existing; keywords"
        
        result = completer.generate_marketing_copy(sample_metadata)
        
        # Should return empty dict since all fields have values
        assert result == {}
        mock_call_prompt.assert_not_called()
    
    def test_complete_missing_fields_no_fields_to_complete(self, completer):
        """Test behavior when no fields need completion."""
        # Create metadata with all relevant fields populated
        complete_metadata = CodexMetadata(
            title="Complete Book",
            author="Complete Author",
            contributor_one_bio="Existing bio",
            bisac_codes="COM004000",
            keywords="complete; keywords",
            summary_short="Existing summary",
            audience="General"
        )
        
        result = completer.complete_missing_fields(complete_metadata)
        
        # Should return the same metadata
        assert result.title == complete_metadata.title
        assert result.contributor_one_bio == complete_metadata.contributor_one_bio
    
    @patch.object(LLMFieldCompleter, '_complete_field')
    def test_complete_missing_fields_handles_exceptions(self, mock_complete_field, completer, sample_metadata):
        """Test that exceptions during field completion are handled gracefully."""
        # Mock _complete_field to raise exception for first call, succeed for second
        mock_complete_field.side_effect = [
            Exception("Test exception"),
            "successful_completion"
        ]
        
        # Should not raise exception, should continue with other fields
        result = completer.complete_missing_fields(
            sample_metadata,
            fields_to_complete=['contributor_one_bio', 'bisac_codes']
        )
        
        assert isinstance(result, CodexMetadata)
        assert mock_complete_field.call_count == 2
    
    def test_field_prompt_mapping_completeness(self, completer):
        """Test that field prompt mapping contains expected fields."""
        expected_fields = [
            'contributor_one_bio', 'bisac_codes', 'keywords', 
            'summary_short', 'review_quotes', 'thema_codes',
            'audience', 'min_age', 'max_age'
        ]
        
        for field in expected_fields:
            assert field in completer.field_prompt_mapping
    
    def test_protected_fields_completeness(self, completer):
        """Test that protected fields list contains critical business fields."""
        expected_protected = [
            'isbn13', 'isbn10', 'list_price_usd', 'publisher',
            'lightning_source_account', 'title', 'author'
        ]
        
        for field in expected_protected:
            assert field in completer.protected_fields