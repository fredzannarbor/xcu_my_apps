# tests/test_enhanced_metadata_generation.py

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from codexes.modules.metadata.metadata_generator import generate_metadata_from_prompts
from codexes.modules.metadata.metadata_models import CodexMetadata
from codexes.modules.distribution.llm_field_completer import LLMFieldCompleter


class TestEnhancedMetadataGeneration:
    """Test suite for enhanced metadata generation with LSI field completion."""
    
    @pytest.fixture
    def sample_book_content(self):
        """Sample book content for testing."""
        return """
        # The Future of AI
        
        ## Chapter 1: Introduction
        
        Artificial Intelligence represents one of the most significant technological 
        advances of our time. This book explores the implications of AI development
        for society, business, and individual lives.
        
        ## Chapter 2: Current State
        
        Today's AI systems are capable of remarkable feats, from natural language
        processing to computer vision and autonomous decision making.
        
        ## About the Author
        
        Dr. Jane Smith is a professor of Computer Science at MIT and has published
        extensively on artificial intelligence and machine learning.
        """
    
    @pytest.fixture
    def mock_llm_responses(self):
        """Mock LLM responses for testing."""
        return {
            'gpt-3.5-turbo': [
                {
                    'prompt_key': 'gemini_get_basic_info',
                    'content': {
                        'title': 'The Future of AI',
                        'subtitle': 'Implications for Society and Business',
                        'author': 'Dr. Jane Smith',
                        'publisher': 'Nimble Books LLC',
                        'imprint': 'Nimble Books LLC',
                        'publication_date': '2024-01-15',
                        'language': 'English',
                        'illustration_count': '0',
                        'illustration_notes': '',
                        'page_count': 150,
                        'word_count': 45000,
                        'audience': 'Professional',
                        'min_age': '',
                        'max_age': 'Adult',
                        'territorial_rights': 'World',
                        'edition_number': '',
                        'edition_description': ''
                    }
                }
            ]
        }
    
    @pytest.fixture
    def mock_field_completion_responses(self):
        """Mock responses for field completion."""
        return {
            'contributor_one_bio': 'Dr. Jane Smith is a professor of Computer Science at MIT specializing in artificial intelligence and machine learning.',
            'contributor_one_affiliations': 'Massachusetts Institute of Technology',
            'contributor_one_professional_position': 'Professor of Computer Science',
            'contributor_one_location': 'Cambridge, MA',
            'weight_lbs': '0.8',
            'series_name': '',
            'territorial_rights': 'World'
        }
    
    @patch('src.codexes.core.file_handler.load_document')
    @patch('src.codexes.core.llm_caller.get_responses_from_multiple_models')
    @patch('src.codexes.modules.distribution.llm_field_completer.LLMFieldCompleter.complete_missing_fields')
    def test_enhanced_metadata_generation_workflow(self, 
                                                 mock_field_completion,
                                                 mock_llm_responses,
                                                 mock_load_document,
                                                 sample_book_content,
                                                 mock_llm_responses_data):
        """Test the complete enhanced metadata generation workflow."""
        
        # Setup mocks
        mock_load_document.return_value = sample_book_content
        mock_llm_responses.return_value = mock_llm_responses_data
        
        # Create enhanced metadata with completed fields
        enhanced_metadata = CodexMetadata(
            title='The Future of AI',
            author='Dr. Jane Smith',
            contributor_one_bio='Dr. Jane Smith is a professor of Computer Science at MIT.',
            contributor_one_affiliations='Massachusetts Institute of Technology',
            contributor_one_professional_position='Professor of Computer Science',
            contributor_one_location='Cambridge, MA',
            weight_lbs='0.8',
            territorial_rights='World'
        )
        mock_field_completion.return_value = enhanced_metadata
        
        # Create a temporary PDF file for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b'%PDF-1.4\n%Mock PDF content')
            temp_file_path = temp_file.name
        
        try:
            # Test the enhanced metadata generation
            result = generate_metadata_from_prompts(
                file_path=temp_file_path,
                model_name='gpt-3.5-turbo',
                prompt_file_path='prompts/codexes_user_prompts.json',
                prompt_keys=['gemini_get_basic_info']
            )
            
            # Verify the result
            assert result is not None
            assert isinstance(result, CodexMetadata)
            assert result.title == 'The Future of AI'
            assert result.author == 'Dr. Jane Smith'
            
            # Verify that field completion was called
            mock_field_completion.assert_called_once()
            
            # Verify enhanced fields are populated
            assert result.contributor_one_bio != ''
            assert result.contributor_one_affiliations != ''
            assert result.territorial_rights == 'World'
            
        finally:
            # Clean up
            os.unlink(temp_file_path)
    
    def test_llm_field_completer_initialization(self):
        """Test LLMFieldCompleter initialization with new field mappings."""
        completer = LLMFieldCompleter()
        
        # Verify new LSI field mappings are present
        expected_lsi_fields = [
            'contributor_one_affiliations',
            'contributor_one_professional_position',
            'contributor_one_location',
            'contributor_one_prior_work',
            'weight_lbs',
            'territorial_rights',
            'series_name',
            'jacket_path_filename'
        ]
        
        for field in expected_lsi_fields:
            assert field in completer.field_prompt_mapping
    
    @patch('src.codexes.modules.distribution.llm_field_completer.call_model_with_prompt')
    @patch('src.codexes.modules.distribution.llm_field_completer.load_and_prepare_prompts')
    def test_json_completion_prompt_handling(self, mock_load_prompts, mock_call_model):
        """Test handling of JSON completion prompts."""
        
        # Setup mocks
        mock_load_prompts.return_value = [{
            'prompt_config': {
                'messages': [{'role': 'user', 'content': 'test prompt'}],
                'params': {}
            }
        }]
        
        mock_call_model.return_value = {
            'raw_content': '{"contributor_one_bio": "Test bio", "contributor_one_affiliations": "Test University"}'
        }
        
        completer = LLMFieldCompleter()
        
        # Test JSON field completion
        result = completer._call_json_completion_prompt(
            'extract_lsi_contributor_info',
            {'title': 'Test Book', 'author': 'Test Author'},
            'gpt-3.5-turbo',
            'contributor_one_bio'
        )
        
        assert result == 'Test bio'
        mock_call_model.assert_called_once()
    
    def test_field_identification_for_completion(self):
        """Test identification of fields that need completion."""
        
        # Create metadata with some empty LSI fields
        metadata = CodexMetadata(
            title='Test Book',
            author='Test Author',
            contributor_one_bio='',  # Empty - should be completed
            contributor_one_affiliations='',  # Empty - should be completed
            weight_lbs='',  # Empty - should be completed
            isbn13='978-1234567890',  # Not empty - should not be completed
            territorial_rights='World'  # Not empty - should not be completed
        )
        
        completer = LLMFieldCompleter()
        empty_fields = completer._identify_empty_fields(metadata)
        
        # Verify empty fields are identified
        assert 'contributor_one_bio' in empty_fields
        assert 'contributor_one_affiliations' in empty_fields
        assert 'weight_lbs' in empty_fields
        
        # Verify non-empty fields are not included
        assert 'isbn13' not in empty_fields
        assert 'territorial_rights' not in empty_fields
    
    def test_protected_fields_not_completed(self):
        """Test that protected fields are not auto-completed."""
        
        metadata = CodexMetadata(
            title='',  # Empty but protected
            isbn13='',  # Empty but protected
            list_price_usd=0,  # Empty but protected
            contributor_one_bio=''  # Empty and not protected
        )
        
        completer = LLMFieldCompleter()
        
        # Get fields to complete
        fields_to_complete = completer._identify_empty_fields(metadata)
        filtered_fields = [f for f in fields_to_complete if f not in completer.protected_fields]
        
        # Verify protected fields are filtered out
        assert 'title' not in filtered_fields
        assert 'isbn13' not in filtered_fields
        assert 'list_price_usd' not in filtered_fields
        
        # Verify non-protected field is included
        assert 'contributor_one_bio' in filtered_fields
    
    def test_backward_compatibility(self):
        """Test that enhanced metadata generation maintains backward compatibility."""
        
        # Test that existing CodexMetadata objects still work
        metadata = CodexMetadata(
            title='Test Book',
            author='Test Author',
            publisher='Test Publisher'
        )
        
        # Verify all new LSI fields exist with default values
        assert hasattr(metadata, 'contributor_one_bio')
        assert hasattr(metadata, 'contributor_one_affiliations')
        assert hasattr(metadata, 'weight_lbs')
        assert hasattr(metadata, 'territorial_rights')
        assert hasattr(metadata, 'lsi_flexfield1')
        
        # Verify default values
        assert metadata.territorial_rights == 'World'
        assert metadata.cover_submission_method == 'FTP'
        assert metadata.carton_pack_quantity == '1'


if __name__ == '__main__':
    pytest.main([__file__])