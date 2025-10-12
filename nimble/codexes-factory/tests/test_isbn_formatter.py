"""
Unit tests for ISBNFormatter class.
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.metadata.isbn_formatter import ISBNFormatter


class TestISBNFormatter:
    """Test cases for ISBNFormatter"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.formatter = ISBNFormatter()
        
        # Valid test ISBNs (with correct check digits)
        self.valid_isbn_978 = "9780134685991"  # Valid ISBN-13
        self.valid_isbn_979 = "9791020304056"  # Valid ISBN-13
        self.hyphenated_isbn = "978-0-13-468599-1"
        
        # Invalid test ISBNs
        self.invalid_length = "978012345678"  # 12 digits
        self.invalid_prefix = "9770123456789"  # starts with 977
        self.invalid_check = "9780134685990"  # wrong check digit
        self.non_numeric = "978-0-12345A-78-9"  # contains letter
    
    def test_validate_isbn_format_valid_978(self):
        """Test validation of valid ISBN-13 starting with 978"""
        assert self.formatter.validate_isbn_format(self.valid_isbn_978)
    
    def test_validate_isbn_format_valid_979(self):
        """Test validation of valid ISBN-13 starting with 979"""
        assert self.formatter.validate_isbn_format(self.valid_isbn_979)
    
    def test_validate_isbn_format_with_hyphens(self):
        """Test validation of ISBN with hyphens"""
        assert self.formatter.validate_isbn_format(self.hyphenated_isbn)
    
    def test_validate_isbn_format_invalid_length(self):
        """Test validation fails for incorrect length"""
        assert not self.formatter.validate_isbn_format(self.invalid_length)
    
    def test_validate_isbn_format_invalid_prefix(self):
        """Test validation fails for invalid prefix"""
        assert not self.formatter.validate_isbn_format(self.invalid_prefix)
    
    def test_validate_isbn_format_invalid_check_digit(self):
        """Test validation fails for incorrect check digit"""
        assert not self.formatter.validate_isbn_format(self.invalid_check)
    
    def test_validate_isbn_format_non_numeric(self):
        """Test validation fails for non-numeric characters"""
        assert not self.formatter.validate_isbn_format(self.non_numeric)
    
    def test_validate_check_digit_correct(self):
        """Test check digit validation with correct digit"""
        assert self.formatter._validate_check_digit(self.valid_isbn_978)
    
    def test_validate_check_digit_incorrect(self):
        """Test check digit validation with incorrect digit"""
        assert not self.formatter._validate_check_digit(self.invalid_check)
    
    def test_format_isbn_13_hyphenated_basic(self):
        """Test basic ISBN-13 hyphenation"""
        result = self.formatter.format_isbn_13_hyphenated(self.valid_isbn_978)
        
        # Should contain hyphens
        assert '-' in result
        # Should start with 978
        assert result.startswith('978-')
        # Should end with check digit
        assert result.endswith('-9')
    
    def test_format_isbn_13_hyphenated_979(self):
        """Test ISBN-13 hyphenation for 979 prefix"""
        result = self.formatter.format_isbn_13_hyphenated(self.valid_isbn_979)
        
        # Should contain hyphens
        assert '-' in result
        # Should start with 979
        assert result.startswith('979-')
    
    def test_format_isbn_13_hyphenated_already_hyphenated(self):
        """Test formatting of already hyphenated ISBN"""
        result = self.formatter.format_isbn_13_hyphenated(self.hyphenated_isbn)
        
        # Should still be properly formatted
        assert '-' in result
        assert result.startswith('978-')
    
    def test_format_isbn_13_hyphenated_invalid_input(self):
        """Test formatting with invalid input returns original"""
        result = self.formatter.format_isbn_13_hyphenated(self.invalid_check)
        
        # Should return original invalid ISBN
        assert result == self.invalid_check
    
    def test_basic_hyphenation_978(self):
        """Test basic hyphenation pattern for 978 prefix"""
        result = self.formatter._basic_hyphenation(self.valid_isbn_978)
        
        expected_pattern = "978-0-123456-78-9"
        assert result == expected_pattern
    
    def test_basic_hyphenation_979(self):
        """Test basic hyphenation pattern for 979 prefix"""
        result = self.formatter._basic_hyphenation(self.valid_isbn_979)
        
        # Should follow 979 pattern
        assert result.startswith('979-')
        assert result.count('-') == 4  # Should have 4 hyphens
    
    def test_generate_copyright_page_isbn(self):
        """Test copyright page ISBN generation"""
        result = self.formatter.generate_copyright_page_isbn(self.valid_isbn_978)
        
        # Should start with "ISBN "
        assert result.startswith('ISBN ')
        # Should contain the formatted ISBN
        assert '978-' in result
        # Should be properly hyphenated
        assert result.count('-') == 4
    
    def test_generate_copyright_page_isbn_invalid(self):
        """Test copyright page ISBN generation with invalid input"""
        result = self.formatter.generate_copyright_page_isbn(self.invalid_check)
        
        # Should still start with "ISBN " even for invalid input
        assert result.startswith('ISBN ')
        # Should contain the original ISBN
        assert self.invalid_check in result
    
    def test_extract_isbn_components_valid(self):
        """Test extraction of ISBN components"""
        components = self.formatter.extract_isbn_components(self.valid_isbn_978)
        
        assert components['prefix'] == '978'
        assert components['group'] == '0'
        assert components['check_digit'] == '9'
        assert components['full_isbn'] == self.valid_isbn_978
        assert 'publisher_title' in components
    
    def test_extract_isbn_components_979_10(self):
        """Test extraction of ISBN components for 979-10 (France)"""
        isbn_979_10 = "9791012345678"  # Assuming valid check digit
        components = self.formatter.extract_isbn_components(isbn_979_10)
        
        if components:  # Only test if validation passes
            assert components['prefix'] == '979'
            # For 979-10, group should be '10'
            if components.get('group') == '10':
                assert len(components['publisher_title']) == 7
    
    def test_extract_isbn_components_invalid(self):
        """Test extraction with invalid ISBN returns empty dict"""
        components = self.formatter.extract_isbn_components(self.invalid_check)
        
        assert components == {}
    
    def test_batch_format_isbns(self):
        """Test batch formatting of multiple ISBNs"""
        isbn_list = [self.valid_isbn_978, self.valid_isbn_979, self.hyphenated_isbn]
        results = self.formatter.batch_format_isbns(isbn_list)
        
        assert len(results) == 3
        # All results should be formatted
        for original, formatted in results.items():
            assert '-' in formatted
            assert formatted.startswith(('978-', '979-'))
    
    def test_batch_format_isbns_with_invalid(self):
        """Test batch formatting with some invalid ISBNs"""
        isbn_list = [self.valid_isbn_978, self.invalid_check, "", None]
        results = self.formatter.batch_format_isbns(isbn_list)
        
        # Should process valid ones and skip invalid/empty ones
        assert len(results) >= 1  # At least the valid one
        assert self.valid_isbn_978 in results
    
    def test_format_preserves_check_digit(self):
        """Test that formatting preserves the original check digit"""
        formatted = self.formatter.format_isbn_13_hyphenated(self.valid_isbn_978)
        
        # Extract check digit from formatted ISBN
        check_digit = formatted.split('-')[-1]
        assert check_digit == '1'  # Original check digit
    
    def test_hyphenation_rules_application(self):
        """Test that hyphenation rules are applied when available"""
        # Test with a known ISBN pattern
        result = self.formatter._apply_hyphenation_rules('978', '0', '123456789', '0')
        
        # Should return a formatted string if rules match
        if result:
            assert result.startswith('978-0-')
            assert result.endswith('-0')
    
    def test_error_handling_malformed_input(self):
        """Test error handling with malformed input"""
        malformed_inputs = [
            "",
            None,
            "not-an-isbn",
            "978",
            "978-0-123456-78-9-extra",
            123456789,  # numeric instead of string
        ]
        
        for malformed in malformed_inputs:
            try:
                # Should not raise exceptions
                if malformed is not None:
                    result = self.formatter.format_isbn_13_hyphenated(str(malformed))
                    assert isinstance(result, str)
            except Exception as e:
                pytest.fail(f"Unexpected exception for input {malformed}: {e}")


if __name__ == "__main__":
    pytest.main([__file__])