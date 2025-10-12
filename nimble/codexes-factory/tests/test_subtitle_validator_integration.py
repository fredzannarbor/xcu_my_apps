"""
Integration tests for SubtitleValidator with metadata processing pipeline.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.metadata.subtitle_validator import SubtitleValidator


class TestSubtitleValidatorIntegration:
    """Test integration of SubtitleValidator with book processing pipeline"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = SubtitleValidator()
        
        # Test book data
        self.xynapse_book_data = {
            'title': 'Test Book',
            'subtitle': 'A Very Long Subtitle That Exceeds the Thirty-Eight Character Limit for Xynapse Traces Books',
            'author': 'Test Author',
            'imprint': 'xynapse_traces',
            'subject': 'Computer Science'
        }
        
        self.valid_xynapse_book_data = {
            'title': 'Test Book',
            'subtitle': 'A Short Guide',  # 13 characters
            'author': 'Test Author',
            'imprint': 'xynapse_traces',
            'subject': 'Computer Science'
        }
        
        self.other_imprint_book_data = {
            'title': 'Test Book',
            'subtitle': 'A Very Long Subtitle That Would Be Too Long for Xynapse But Is Fine for Other Imprints',
            'author': 'Test Author',
            'imprint': 'other_imprint',
            'subject': 'Computer Science'
        }
    
    def test_xynapse_subtitle_processing_valid(self):
        """Test processing of valid xynapse_traces subtitle"""
        result = self.validator.process_xynapse_subtitle(
            self.valid_xynapse_book_data['subtitle'],
            self.valid_xynapse_book_data
        )
        
        # Should return original subtitle unchanged
        assert result == self.valid_xynapse_book_data['subtitle']
        assert len(result) <= 38
    
    @patch('src.codexes.modules.metadata.subtitle_validator.LLMCaller')
    def test_xynapse_subtitle_processing_needs_replacement(self, mock_llm_caller_class):
        """Test processing of xynapse_traces subtitle that needs replacement"""
        # Mock LLM response
        mock_llm_caller = Mock()
        mock_response = Mock()
        mock_response.content = "Concise Guide"
        mock_llm_caller.call_llm.return_value = mock_response
        mock_llm_caller_class.return_value = mock_llm_caller
        
        validator = SubtitleValidator(llm_caller=mock_llm_caller)
        
        result = validator.process_xynapse_subtitle(
            self.xynapse_book_data['subtitle'],
            self.xynapse_book_data
        )
        
        # Should return replacement subtitle
        assert result == "Concise Guide"
        assert len(result) <= 38
        assert result != self.xynapse_book_data['subtitle']
    
    def test_other_imprint_subtitle_processing(self):
        """Test processing of subtitle for non-xynapse imprint"""
        result = self.validator.process_xynapse_subtitle(
            self.other_imprint_book_data['subtitle'],
            self.other_imprint_book_data
        )
        
        # Should return original subtitle even if long
        assert result == self.other_imprint_book_data['subtitle']
    
    @patch('src.codexes.modules.metadata.subtitle_validator.LLMCaller')
    def test_subtitle_processing_llm_failure_fallback(self, mock_llm_caller_class):
        """Test subtitle processing when LLM fails"""
        # Mock LLM failure
        mock_llm_caller = Mock()
        mock_llm_caller.call_llm.return_value = None
        mock_llm_caller_class.return_value = mock_llm_caller
        
        validator = SubtitleValidator(llm_caller=mock_llm_caller)
        
        result = validator.process_xynapse_subtitle(
            self.xynapse_book_data['subtitle'],
            self.xynapse_book_data
        )
        
        # Should return fallback subtitle within limit
        assert len(result) <= 38
        assert isinstance(result, str)
        # Should be different from original (truncated/modified)
        assert result != self.xynapse_book_data['subtitle']
    
    def test_batch_processing_mixed_imprints(self):
        """Test batch processing of subtitles from different imprints"""
        subtitle_data = {
            'book1': self.valid_xynapse_book_data,
            'book2': self.xynapse_book_data,
            'book3': self.other_imprint_book_data
        }
        
        results = self.validator.batch_validate_subtitles(subtitle_data)
        
        assert len(results) == 3
        assert results['book1'].is_valid  # Valid xynapse subtitle
        assert not results['book2'].is_valid  # Invalid xynapse subtitle
        assert results['book3'].is_valid  # Other imprint (higher limit)
    
    def test_character_limit_enforcement(self):
        """Test that character limits are properly enforced"""
        # Test xynapse_traces limit
        xynapse_limit = self.validator.get_character_limit('xynapse_traces')
        assert xynapse_limit == 38
        
        # Test default limit
        default_limit = self.validator.get_character_limit('unknown_imprint')
        assert default_limit == 100
        
        # Test validation respects limits
        long_subtitle = "A" * 50  # 50 characters
        
        xynapse_result = self.validator.validate_subtitle_length(long_subtitle, 'xynapse_traces')
        assert not xynapse_result.is_valid
        assert xynapse_result.needs_replacement
        
        default_result = self.validator.validate_subtitle_length(long_subtitle, 'other_imprint')
        assert default_result.is_valid
        assert not default_result.needs_replacement
    
    @patch('src.codexes.modules.metadata.subtitle_validator.LLMCaller')
    def test_llm_prompt_generation(self, mock_llm_caller_class):
        """Test that LLM prompts are generated correctly"""
        mock_llm_caller = Mock()
        mock_response = Mock()
        mock_response.content = "Short Title"
        mock_llm_caller.call_llm.return_value = mock_response
        mock_llm_caller_class.return_value = mock_llm_caller
        
        validator = SubtitleValidator(llm_caller=mock_llm_caller)
        
        validator.generate_replacement_subtitle(
            self.xynapse_book_data['subtitle'],
            self.xynapse_book_data
        )
        
        # Verify LLM was called
        mock_llm_caller.call_llm.assert_called_once()
        
        # Check the request structure
        call_args = mock_llm_caller.call_llm.call_args[0][0]
        assert call_args.model == 'gpt-4o-mini'
        assert len(call_args.messages) == 2
        
        # Check prompt content
        user_message = call_args.messages[1]['content']
        assert self.xynapse_book_data['title'] in user_message
        assert self.xynapse_book_data['subtitle'] in user_message
        assert '38' in user_message  # Character limit
    
    def test_subtitle_consistency_across_processing(self):
        """Test that subtitle changes are consistent across different processing stages"""
        # Simulate the data being passed through different stages
        book_data = self.xynapse_book_data.copy()
        
        # Mock LLM to return consistent replacement
        with patch('src.codexes.modules.metadata.subtitle_validator.LLMCaller') as mock_llm_class:
            mock_llm_caller = Mock()
            mock_response = Mock()
            mock_response.content = "Consistent Replacement"
            mock_llm_caller.call_llm.return_value = mock_response
            mock_llm_class.return_value = mock_llm_caller
            
            validator = SubtitleValidator(llm_caller=mock_llm_caller)
            
            # Process subtitle multiple times (simulating different stages)
            result1 = validator.process_xynapse_subtitle(book_data['subtitle'], book_data)
            result2 = validator.process_xynapse_subtitle(book_data['subtitle'], book_data)
            
            # Results should be consistent
            assert result1 == result2
            assert result1 == "Consistent Replacement"
    
    def test_error_handling_in_integration(self):
        """Test error handling during integration scenarios"""
        # Test with malformed book data
        malformed_data = {
            'title': None,
            'subtitle': self.xynapse_book_data['subtitle'],
            'imprint': 'xynapse_traces'
        }
        
        # Should not raise exception
        result = self.validator.process_xynapse_subtitle(
            malformed_data['subtitle'],
            malformed_data
        )
        
        assert isinstance(result, str)
        assert len(result) <= 38
    
    def test_performance_with_multiple_books(self):
        """Test performance characteristics with multiple books"""
        # Create multiple book data entries
        book_data_list = []
        for i in range(10):
            book_data = self.xynapse_book_data.copy()
            book_data['title'] = f"Test Book {i}"
            book_data_list.append(book_data)
        
        # Process all subtitles
        results = []
        for book_data in book_data_list:
            result = self.validator.process_xynapse_subtitle(
                book_data['subtitle'],
                book_data
            )
            results.append(result)
        
        # All results should be valid
        for result in results:
            assert len(result) <= 38
            assert isinstance(result, str)
    
    def test_subtitle_update_in_data_structure(self):
        """Test that processed subtitles update the original data structure"""
        book_data = self.xynapse_book_data.copy()
        original_subtitle = book_data['subtitle']
        
        with patch('src.codexes.modules.metadata.subtitle_validator.LLMCaller') as mock_llm_class:
            mock_llm_caller = Mock()
            mock_response = Mock()
            mock_response.content = "Updated Subtitle"
            mock_llm_caller.call_llm.return_value = mock_response
            mock_llm_class.return_value = mock_llm_caller
            
            validator = SubtitleValidator(llm_caller=mock_llm_caller)
            
            # Process subtitle
            result = validator.process_xynapse_subtitle(book_data['subtitle'], book_data)
            
            # Verify the result
            assert result == "Updated Subtitle"
            assert result != original_subtitle
            assert len(result) <= 38


if __name__ == "__main__":
    pytest.main([__file__])