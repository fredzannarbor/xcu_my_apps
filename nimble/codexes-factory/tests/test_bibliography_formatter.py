"""
Tests for bibliography formatting system.
"""

import pytest
try:
    from src.codexes.modules.prepress.bibliography_formatter import BibliographyFormatter
except ImportError:
    from codexes.modules.prepress.bibliography_formatter import BibliographyFormatter


class TestBibliographyFormatter:
    
    def setup_method(self):
        """Set up test fixtures"""
        self.memoir_config = {
            'citation_style': 'chicago',
            'hanging_indent': '0.15in'
        }
        self.formatter = BibliographyFormatter(self.memoir_config)
    
    def test_format_bibliography_entry(self):
        """Test that individual bibliography entries are properly formatted"""
        entry = {
            'author': 'Smith, John',
            'title': 'Test Book Title',
            'publisher': 'Test Publisher',
            'year': '2023',
            'isbn': '978-1234567890'
        }
        
        result = self.formatter.format_bibliography_entry(entry)
        
        assert 'Smith, John.' in result
        assert '\\textit{Test Book Title}' in result
        assert 'Test Publisher, 2023.' in result
        assert 'ISBN: 978-1234567890' in result
    
    def test_hanging_indent_application(self):
        """Test that 0.15 hanging indent is properly applied"""
        entries = [
            {'author': 'Author One', 'title': 'Title One', 'publisher': 'Pub One', 'year': '2023'},
            {'author': 'Author Two', 'title': 'Title Two', 'publisher': 'Pub Two', 'year': '2024'}
        ]
        
        result = self.formatter.generate_latex_bibliography(entries)
        
        assert '0.15in' in result
        assert '\\setlength{\\itemindent}{-0.15in}' in result
        assert '\\setlength{\\leftmargin}{0.15in}' in result
    
    def test_memoir_citation_field_integration(self):
        """Test memoir citation field formatting"""
        entries = [
            {'author': 'Test Author', 'title': 'Test Title', 'publisher': 'Test Pub', 'year': '2023'}
        ]
        
        result = self.formatter.apply_memoir_citation_field(entries)
        
        assert '\\begin{thebibliography}{99}' in result
        assert '\\bibitem{1}' in result
        assert '\\end{thebibliography}' in result
    
    def test_validate_bibliography_format(self):
        """Test bibliography format validation"""
        valid_latex = """\\begin{thebibliography}{99}
\\setlength{\\itemindent}{-0.15in}
\\setlength{\\leftmargin}{0.15in}
\\bibitem{1} Test entry
\\end{thebibliography}"""
        
        assert self.formatter.validate_bibliography_format(valid_latex) is True
        
        invalid_latex = "Just some text"
        assert self.formatter.validate_bibliography_format(invalid_latex) is False
    
    def test_empty_entries_handling(self):
        """Test handling of empty bibliography entries"""
        result = self.formatter.generate_latex_bibliography([])
        assert result == ""
    
    def test_error_handling(self):
        """Test error handling for malformed entries"""
        malformed_entry = {'invalid': 'data'}
        result = self.formatter.format_bibliography_entry(malformed_entry)
        
        # Should handle gracefully and return something
        assert isinstance(result, str)
        assert len(result) > 0