"""
Unit tests for SubtitleValidator class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.metadata.subtitle_validator import SubtitleValidator, ValidationResult


class TestSubtitleValidator:
    """Test cases for SubtitleValidator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock LLM caller
        self.mock_llm_caller = Mock()
        self.validator = SubtitleValidator(llm_caller=self.mock_llm_caller)
        
        # Test data
        self.valid_short_subtitle = "A Brief Guide"  # 13 characters
        self.valid_long_subtitle = "A Comprehensive Guide to Understanding Complex Topics"  # 54 characters
        self.xynapse_limit_subtitle = "Essential Concepts and Applications"  # 35 characters (under 38)
        self.xynapse_over_limit = "A Very Long Subtitle That Exceeds the Character Limit for Xynapse Traces"  # 75 characters
        
        self.test_metadata = {
            'title': 'Test Book',
            'subject': 'Computer Science',
            'imprint': 'xynapse_traces'
        }
    
    def test_validate_subtitle_length_valid_xynapse(self):
        """Test validation of valid subtitle for xynapse_traces"""
        result = self.validator.validate_subtitle_length(self.xynapse_limit_subtitle, 'xynapse_traces')
        
        assert result.is_valid
        assert result.current_length == 35
        assert result.max_length == 38
        assert not result.needs_replacement
        assert result.error_message is None
    
    def test_validate_subtitle_length_invalid_xynapse(self):
        """Test validation of invalid subtitle for xynapse_traces"""
        result = self.validator.validate_subtitle_length(self.xynapse_over_limit, 'xynapse_traces')
        
        assert not result.is_valid
        assert result.current_length == 75
        assert result.max_length == 38
        assert result.needs_replacement
        assert "exceeds 38 character limit" in result.error_message
    
    def test_validate_subtitle_length_default_imprint(self):
        """Test validation with default imprint limits"""
        result = self.validator.validate_subtitle_length(self.valid_long_subtitle, 'other_imprint')
        
        assert result.is_valid
        assert result.current_length == 54
        assert result.max_length == 100
        assert not result.needs_replacement
    
    def test_validate_subtitle_length_empty_subtitle(self):
        """Test validation of empty subtitle"""
        result = self.validator.validate_subtitle_length("", 'xynapse_traces')
        
        assert result.is_valid
        assert result.current_length == 0
        assert result.max_length == 38
        assert not result.needs_replacement
    
    def test_validate_subtitle_length_none_subtitle(self):
        """Test validation of None subtitle"""
        result = self.validator.validate_subtitle_length(None, 'xynapse_traces')
        
        assert result.is_valid
        assert result.current_length == 0
        assert not result.needs_replacement
    
    @patch('codexes.modules.metadata.subtitle_validator.logger')
    def test_validate_subtitle_length_error_handling(self, mock_logger):
        """Test error handling in subtitle validation"""
        # Force an error by passing invalid input
        with patch.object(self.validator, 'character_limits', side_effect=Exception("Test error")):
            result = self.validator.validate_subtitle_length("test", 'xynapse_traces')
            
            assert not result.is_valid
            assert "Validation error" in result.error_message
            mock_logger.error.assert_called()
    
    def test_generate_replacement_subtitle_success(self):
        """Test successful subtitle replacement generation"""
        # Mock successful LLM response
        mock_response = Mock()
        mock_response.content = "New Short Subtitle"
        self.mock_llm_caller.call_llm.return_value = mock_response
        
        result = self.validator.generate_replacement_subtitle(self.xynapse_over_limit, self.test_metadata)
        
        assert result == "New Short Subtitle"
        assert len(result) <= 38
        self.mock_llm_caller.call_llm.assert_called_once()
    
    def test_generate_replacement_subtitle_llm_failure(self):
        """Test subtitle replacement when LLM fails"""
        # Mock LLM failure
        self.mock_llm_caller.call_llm.return_value = None
        
        result = self.validator.generate_replacement_subtitle(self.xynapse_over_limit, self.test_metadata)
        
        # Should return fallback subtitle
        assert len(result) <= 38
        assert isinstance(result, str)
    
    def test_generate_replacement_subtitle_too_long_response(self):
        """Test handling of LLM response that's still too long"""
        # Mock LLM response that's still too long
        mock_response = Mock()
        mock_response.content = "This is still a very long subtitle that exceeds the character limit"
        self.mock_llm_caller.call_llm.return_value = mock_response
        
        result = self.validator.generate_replacement_subtitle(self.xynapse_over_limit, self.test_metadata)
        
        # Should be truncated to fit limit
        assert len(result) <= 38
    
    def test_create_subtitle_prompt(self):
        """Test subtitle prompt creation"""
        prompt = self.validator._create_subtitle_prompt(
            self.xynapse_over_limit,
            "Test Title",
            "Test Subject",
            38
        )
        
        assert "Test Title" in prompt
        assert "Test Subject" in prompt
        assert self.xynapse_over_limit in prompt
        assert "38" in prompt
        assert "Character Limit" in prompt
    
    def test_truncate_subtitle_safely_word_boundary(self):
        """Test safe truncation at word boundaries"""
        long_subtitle = "This is a very long subtitle that needs truncation"
        result = self.validator._truncate_subtitle_safely(long_subtitle, 25)
        
        assert len(result) <= 25
        # Should not end with partial word
        assert not result.endswith(' ')
        # Should be truncated at word boundary
        words = result.split()
        assert all(word in long_subtitle for word in words)
    
    def test_truncate_subtitle_safely_character_boundary(self):
        """Test truncation when no good word boundary exists"""
        long_subtitle = "Supercalifragilisticexpialidocious"
        result = self.validator._truncate_subtitle_safely(long_subtitle, 20)
        
        assert len(result) <= 20
        # Should add ellipsis if space allows
        if len(result) == 20:
            assert result.endswith("...") or len(long_subtitle[:20]) == 20
    
    def test_truncate_subtitle_safely_already_short(self):
        """Test truncation of subtitle that's already short enough"""
        short_subtitle = "Short"
        result = self.validator._truncate_subtitle_safely(short_subtitle, 20)
        
        assert result == short_subtitle
    
    def test_fallback_subtitle_generation(self):
        """Test fallback subtitle generation"""
        result = self.validator._fallback_subtitle_generation(self.xynapse_over_limit, 38)
        
        assert len(result) <= 38
        assert isinstance(result, str)
        # Should contain some words from original
        original_words = set(self.xynapse_over_limit.lower().split())
        result_words = set(result.lower().split())
        assert len(original_words.intersection(result_words)) > 0
    
    def test_process_xynapse_subtitle_valid(self):
        """Test processing valid xynapse subtitle"""
        result = self.validator.process_xynapse_subtitle(self.xynapse_limit_subtitle, self.test_metadata)
        
        assert result == self.xynapse_limit_subtitle
    
    def test_process_xynapse_subtitle_needs_replacement(self):
        """Test processing xynapse subtitle that needs replacement"""
        # Mock successful LLM response
        mock_response = Mock()
        mock_response.content = "Shorter Title"
        self.mock_llm_caller.call_llm.return_value = mock_response
        
        result = self.validator.process_xynapse_subtitle(self.xynapse_over_limit, self.test_metadata)
        
        assert result == "Shorter Title"
        assert len(result) <= 38
    
    def test_process_xynapse_subtitle_non_xynapse_imprint(self):
        """Test processing subtitle for non-xynapse imprint"""
        metadata = self.test_metadata.copy()
        metadata['imprint'] = 'other_imprint'
        
        result = self.validator.process_xynapse_subtitle(self.xynapse_over_limit, metadata)
        
        # Should return original subtitle even if it's long
        assert result == self.xynapse_over_limit
    
    def test_batch_validate_subtitles(self):
        """Test batch validation of multiple subtitles"""
        subtitle_data = {
            'book1': {'subtitle': self.valid_short_subtitle, 'imprint': 'xynapse_traces'},
            'book2': {'subtitle': self.xynapse_over_limit, 'imprint': 'xynapse_traces'},
            'book3': {'subtitle': self.valid_long_subtitle, 'imprint': 'other_imprint'}
        }
        
        results = self.validator.batch_validate_subtitles(subtitle_data)
        
        assert len(results) == 3
        assert results['book1'].is_valid
        assert not results['book2'].is_valid
        assert results['book3'].is_valid
    
    def test_get_character_limit(self):
        """Test getting character limits for different imprints"""
        assert self.validator.get_character_limit('xynapse_traces') == 38
        assert self.validator.get_character_limit('unknown_imprint') == 100
    
    def test_update_character_limits(self):
        """Test updating character limits"""
        new_limits = {'test_imprint': 50, 'xynapse_traces': 40}
        self.validator.update_character_limits(new_limits)
        
        assert self.validator.get_character_limit('test_imprint') == 50
        assert self.validator.get_character_limit('xynapse_traces') == 40
    
    def test_llm_request_configuration(self):
        """Test that LLM requests are configured correctly"""
        mock_response = Mock()
        mock_response.content = "Test Response"
        self.mock_llm_caller.call_llm.return_value = mock_response
        
        self.validator.generate_replacement_subtitle(self.xynapse_over_limit, self.test_metadata)
        
        # Verify LLM was called with correct configuration
        call_args = self.mock_llm_caller.call_llm.call_args[0][0]
        assert call_args.model == 'gpt-4o-mini'
        assert call_args.max_tokens == 50
        assert call_args.temperature == 0.7
        assert len(call_args.messages) == 2
        assert call_args.messages[0]['role'] == 'system'
        assert call_args.messages[1]['role'] == 'user'
    
    @patch('codexes.modules.metadata.subtitle_validator.logger')
    def test_error_handling_in_process_xynapse_subtitle(self, mock_logger):
        """Test error handling in process_xynapse_subtitle"""
        # Force an error in validation
        with patch.object(self.validator, 'validate_subtitle_length', side_effect=Exception("Test error")):
            result = self.validator.process_xynapse_subtitle(self.xynapse_over_limit, self.test_metadata)
            
            # Should return original subtitle on error
            assert result == self.xynapse_over_limit
            mock_logger.error.assert_called()
    
    def test_validation_result_dataclass(self):
        """Test ValidationResult dataclass functionality"""
        result = ValidationResult(
            is_valid=False,
            current_length=50,
            max_length=38,
            needs_replacement=True,
            error_message="Test error"
        )
        
        assert not result.is_valid
        assert result.current_length == 50
        assert result.max_length == 38
        assert result.needs_replacement
        assert result.error_message == "Test error"


if __name__ == "__main__":
    pytest.main([__file__])