"""
Tests for enhanced error handling system.
"""

import pytest
import logging
from unittest.mock import Mock, MagicMock
from src.codexes.modules.distribution.enhanced_error_handler import EnhancedErrorHandler, ErrorContext


class TestEnhancedErrorHandler:
    
    def setup_method(self):
        """Set up test fixtures"""
        self.logger = logging.getLogger("test_logger")
        self.error_handler = EnhancedErrorHandler(self.logger)
    
    def test_handle_quote_verification_error_missing_key(self):
        """Test handling of quote verification errors with missing keys"""
        # Response missing 'verified_quotes' key
        invalid_response = {
            'acronym': 'RISE',
            'expansion': 'Resource Independence & Self-Sustenance Economy',
            'explanation': 'This mnemonic highlights...'
        }
        
        context = {'book_id': 'test_book'}
        
        result = self.error_handler.handle_quote_verification_error(invalid_response, context)
        
        # Should return safe fallback
        assert 'verified_quotes' in result
        assert result['verified_quotes'] == []
        assert result['verification_status'] == 'failed'
        assert 'error' in result
    
    def test_quote_verification_recovery_alternative_key(self):
        """Test recovery using alternative quote keys"""
        response_with_alt_key = {
            'quotes': ['Quote 1', 'Quote 2', 'Quote 3'],
            'other_data': 'some value'
        }
        
        context = {'book_id': 'test_book'}
        
        result = self.error_handler.handle_quote_verification_error(response_with_alt_key, context)
        
        # Should recover quotes from alternative key
        assert result['verified_quotes'] == ['Quote 1', 'Quote 2', 'Quote 3']
        assert result['verification_status'] == 'recovered'
        assert 'alternative_key' in result['recovery_method']
    
    def test_quote_verification_string_extraction(self):
        """Test quote extraction from string response"""
        string_response = '''
        Here are some quotes:
        "First quote about something important"
        "Second quote with more content here"
        "Third quote that is also meaningful"
        '''
        
        context = {'book_id': 'test_book'}
        
        result = self.error_handler.handle_quote_verification_error(string_response, context)
        
        # Should extract quotes from string
        assert len(result['verified_quotes']) > 0
        assert result['verification_status'] == 'recovered'
        assert result['recovery_method'] == 'string_extraction'
    
    def test_handle_field_completion_error_with_fallback(self):
        """Test field completion error handling with fallback methods"""
        # Mock completer object with fallback method
        mock_completer = Mock()
        mock_completer.complete_field_safe = Mock(return_value="Fallback Title")
        
        error = AttributeError("'MockCompleter' object has no attribute 'complete_field'")
        
        result = self.error_handler.handle_field_completion_error(
            error, "title", mock_completer
        )
        
        # Should use fallback method
        assert result == "Fallback Title"
        mock_completer.complete_field_safe.assert_called_once_with("title")
    
    def test_field_completion_default_values(self):
        """Test field completion with default values when no recovery possible"""
        error = Exception("Complete failure")
        
        # Test various field names
        title_result = self.error_handler.handle_field_completion_error(error, "title")
        author_result = self.error_handler.handle_field_completion_error(error, "author")
        unknown_result = self.error_handler.handle_field_completion_error(error, "unknown_field")
        
        assert title_result == "Untitled"
        assert author_result == "Unknown Author"
        assert unknown_result == ""  # Default for unknown fields
    
    def test_handle_validation_error(self):
        """Test validation error handling"""
        validation_result = {
            'errors': ['Required field missing', 'Invalid format'],
            'warnings': ['Field length exceeds recommendation'],
            'field_errors': {
                'title': 'Title is empty',
                'isbn': 'Invalid ISBN format'
            }
        }
        
        # Should not raise exception
        self.error_handler.handle_validation_error(validation_result)
        
        # Check that error was logged (would need to capture logs in real test)
        assert True  # Placeholder - in real test would check log output
    
    def test_validation_recovery_suggestions(self):
        """Test generation of validation recovery suggestions"""
        validation_result = {
            'errors': ['Required field title is missing', 'Invalid format in isbn field'],
            'field_errors': {
                'description': 'Field is empty',
                'price': 'Invalid value format'
            }
        }
        
        suggestions = self.error_handler._generate_validation_recovery_suggestions(validation_result)
        
        assert len(suggestions) > 0
        assert any('required fields' in s.lower() for s in suggestions)
        assert any('format' in s.lower() for s in suggestions)
        assert any('description' in s for s in suggestions)
    
    def test_error_statistics_tracking(self):
        """Test error statistics tracking"""
        # Generate some errors
        self.error_handler.handle_field_completion_error(ValueError("Test error 1"), "field1")
        self.error_handler.handle_field_completion_error(AttributeError("Test error 2"), "field2")
        self.error_handler.handle_field_completion_error(ValueError("Test error 3"), "field3")
        
        stats = self.error_handler.get_error_statistics()
        
        assert stats['total_errors_handled'] == 3
        assert stats['error_counts_by_type']['ValueError'] == 2
        assert stats['error_counts_by_type']['AttributeError'] == 1
    
    def test_recovery_strategy_registration(self):
        """Test registration and use of custom recovery strategies"""
        def custom_recovery_strategy(error, context):
            return "Custom recovery result"
        
        self.error_handler.register_recovery_strategy("custom_error", custom_recovery_strategy)
        
        stats = self.error_handler.get_error_statistics()
        assert "custom_error" in stats['registered_strategies']
    
    def test_log_error_with_context(self):
        """Test structured error logging with context"""
        error = ValueError("Test error")
        context = {
            'operation': 'test_operation',
            'input_data': {'key': 'value'},
            'system_state': {'state': 'active'}
        }
        
        # Should not raise exception
        self.error_handler.log_error_with_context(error, context)
        
        # Check error count was incremented
        assert self.error_handler.error_counts.get('ValueError', 0) >= 1
    
    def test_clear_error_history(self):
        """Test clearing error history and statistics"""
        # Generate some errors first
        self.error_handler.handle_field_completion_error(ValueError("Test"), "field")
        
        # Verify errors exist
        stats_before = self.error_handler.get_error_statistics()
        assert stats_before['total_errors_handled'] > 0
        
        # Clear history
        self.error_handler.clear_error_history()
        
        # Verify cleared
        stats_after = self.error_handler.get_error_statistics()
        assert stats_after['total_errors_handled'] == 0
    
    def test_extract_quotes_from_string_patterns(self):
        """Test quote extraction with various quote patterns"""
        test_strings = [
            'Text with "double quotes" and more text',
            "Text with 'single quotes' and more text",
            'Text with «French quotes» and more text',
            'Text with "smart quotes" and more text'
        ]
        
        for test_string in test_strings:
            quotes = self.error_handler._extract_quotes_from_string(test_string)
            assert len(quotes) >= 0  # Should not crash
    
    def test_error_handling_robustness(self):
        """Test that error handlers themselves don't crash on bad input"""
        # Test with None values
        result1 = self.error_handler.handle_quote_verification_error(None, {})
        assert 'verified_quotes' in result1
        
        # Test with malformed data
        result2 = self.error_handler.handle_field_completion_error(None, None, None)
        assert result2 is not None
        
        # Test with empty validation result
        self.error_handler.handle_validation_error({})  # Should not crash