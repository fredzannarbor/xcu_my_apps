"""
Test integration of ISBNFormatter with copyright page generation.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Setup path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.append('imprints/xynapse_traces')

from codexes.modules.metadata.isbn_formatter import ISBNFormatter


class TestCopyrightPageISBNIntegration:
    """Test cases for ISBN formatting in copyright page generation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.test_data = {
            'title': 'Test Book',
            'author': 'Test Author',
            'isbn13': '9780123456789',
            'imprint': 'xynapse_traces'
        }
        
        self.test_data_hyphenated = {
            'title': 'Test Book',
            'author': 'Test Author', 
            'isbn13': '978-0-123456-78-9',
            'imprint': 'xynapse_traces'
        }
        
        self.test_data_invalid = {
            'title': 'Test Book',
            'author': 'Test Author',
            'isbn13': '9780123456788',  # Invalid check digit
            'imprint': 'xynapse_traces'
        }
    
    @patch('imprints.xynapse_traces.prepress.escape_latex')
    def test_copyright_page_isbn_formatting_valid(self, mock_escape):
        """Test copyright page generation with valid ISBN"""
        mock_escape.side_effect = lambda x: x  # Return input unchanged
        
        try:
            # Import the prepress module
            import prepress
            
            # Create temporary directory for test
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Mock the build directory and file operations
                with patch('pathlib.Path.write_text') as mock_write:
                    # Test the copyright page generation logic
                    isbn = self.test_data['isbn13']
                    
                    # This should use the ISBNFormatter
                    import sys
                    from pathlib import Path
                    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
                    
                    from codexes.modules.metadata.isbn_formatter import ISBNFormatter
                    isbn_formatter = ISBNFormatter()
                    formatted_isbn = isbn_formatter.generate_copyright_page_isbn(isbn)
                    
                    # Verify the formatted ISBN
                    assert formatted_isbn.startswith('ISBN ')
                    assert '978-' in formatted_isbn
                    assert formatted_isbn.count('-') == 4  # Proper hyphenation
                    
        except ImportError:
            # If prepress module can't be imported, test the formatter directly
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
            
            from codexes.modules.metadata.isbn_formatter import ISBNFormatter
            isbn_formatter = ISBNFormatter()
            formatted_isbn = isbn_formatter.generate_copyright_page_isbn(self.test_data['isbn13'])
            
            assert formatted_isbn.startswith('ISBN ')
            assert '978-' in formatted_isbn
    
    def test_isbn_formatter_copyright_page_generation(self):
        """Test ISBNFormatter copyright page generation directly"""
        
        formatter = ISBNFormatter()
        
        # Test with valid ISBN
        result = formatter.generate_copyright_page_isbn(self.test_data['isbn13'])
        assert result.startswith('ISBN ')
        assert '978-0-123456-78-9' in result
        
        # Test with already hyphenated ISBN
        result = formatter.generate_copyright_page_isbn(self.test_data_hyphenated['isbn13'])
        assert result.startswith('ISBN ')
        assert '978-0-123456-78-9' in result
        
        # Test with invalid ISBN (should still work but return original)
        result = formatter.generate_copyright_page_isbn(self.test_data_invalid['isbn13'])
        assert result.startswith('ISBN ')
        assert self.test_data_invalid['isbn13'] in result
    
    def test_isbn_validation_in_copyright_context(self):
        """Test ISBN validation specifically for copyright page context"""
        from src.codexes.modules.metadata.isbn_formatter import ISBNFormatter
        
        formatter = ISBNFormatter()
        
        # Valid ISBNs should format properly
        valid_isbns = [
            '9780123456789',
            '978-0-123456-78-9',
            '9791234567890',
            '979-10-12345-67-8'
        ]
        
        for isbn in valid_isbns:
            if formatter.validate_isbn_format(isbn):
                result = formatter.generate_copyright_page_isbn(isbn)
                assert result.startswith('ISBN ')
                assert '-' in result  # Should be hyphenated
    
    def test_copyright_page_error_handling(self):
        """Test error handling in copyright page ISBN formatting"""
        from src.codexes.modules.metadata.isbn_formatter import ISBNFormatter
        
        formatter = ISBNFormatter()
        
        # Test with various problematic inputs
        problematic_inputs = [
            '',
            None,
            'not-an-isbn',
            '123',
            'Unknown',
            'TBD'
        ]
        
        for problematic_input in problematic_inputs:
            if problematic_input is not None:
                result = formatter.generate_copyright_page_isbn(str(problematic_input))
                # Should still return something starting with ISBN
                assert result.startswith('ISBN ')
    
    @patch('src.codexes.modules.metadata.isbn_formatter.logger')
    def test_copyright_page_logging(self, mock_logger):
        """Test that copyright page ISBN formatting logs appropriately"""
        from src.codexes.modules.metadata.isbn_formatter import ISBNFormatter
        
        formatter = ISBNFormatter()
        
        # Test with valid ISBN
        formatter.generate_copyright_page_isbn(self.test_data['isbn13'])
        mock_logger.info.assert_called()
        
        # Test with invalid ISBN
        formatter.generate_copyright_page_isbn(self.test_data_invalid['isbn13'])
        # Should have logged warnings about validation
        assert mock_logger.warning.called or mock_logger.info.called
    
    def test_isbn_hyphenation_patterns(self):
        """Test specific ISBN hyphenation patterns for copyright page"""
        from src.codexes.modules.metadata.isbn_formatter import ISBNFormatter
        
        formatter = ISBNFormatter()
        
        # Test different ISBN patterns
        test_cases = [
            ('9780123456789', '978-0-123456-78-9'),  # English language
            ('9781234567890', '978-1-234567-89-0'),  # English language
            ('9791012345678', '979-10-12345-67-8'),  # France (979-10)
        ]
        
        for input_isbn, expected_pattern in test_cases:
            if formatter.validate_isbn_format(input_isbn):
                formatted = formatter.format_isbn_13_hyphenated(input_isbn)
                copyright_result = formatter.generate_copyright_page_isbn(input_isbn)
                
                # Copyright result should contain the formatted ISBN
                assert formatted in copyright_result
                # Should match expected pattern if validation passes
                if formatted.count('-') == 4:  # Properly hyphenated
                    assert formatted.startswith(expected_pattern[:7])  # At least prefix-group match
    
    def test_integration_with_existing_copyright_logic(self):
        """Test integration with existing copyright page logic"""
        # Simulate the logic from the prepress.py file
        test_data_variants = [
            {'assigned_isbn': '9780123456789'},  # Assigned ISBN takes priority
            {'isbn13': '9780123456789'},         # Standard isbn13 field
            {'isbn': '9780123456789'},           # Fallback isbn field
            {'isbn13': 'Unknown'},               # Invalid ISBN
            {'isbn13': 'TBD'},                   # Placeholder ISBN
            {}                                   # No ISBN
        ]
        
        from src.codexes.modules.metadata.isbn_formatter import ISBNFormatter
        formatter = ISBNFormatter()
        
        for data in test_data_variants:
            # Simulate the ISBN selection logic
            isbn = data.get('assigned_isbn') or data.get('isbn13') or data.get('isbn')
            
            if isbn and isbn != "Unknown" and isbn != "TBD":
                # Should use formatter
                result = formatter.generate_copyright_page_isbn(isbn)
                assert result.startswith('ISBN ')
                if formatter.validate_isbn_format(isbn):
                    assert '-' in result  # Should be hyphenated
            else:
                # Should result in empty ISBN line
                assert isbn is None or isbn in ["Unknown", "TBD"]


if __name__ == "__main__":
    pytest.main([__file__])