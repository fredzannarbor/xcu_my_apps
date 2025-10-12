"""
Tests for typography management system.
"""

import pytest
from src.codexes.modules.prepress.typography_manager import TypographyManager


class TestTypographyManager:
    
    def setup_method(self):
        """Set up test fixtures"""
        self.imprint_config = {
            'fonts': {
                'body': 'Adobe Caslon Pro',
                'korean': 'Apple Myungjo',
                'quotations': 'Adobe Caslon Pro',
                'mnemonics': 'Adobe Caslon Pro'
            },
            'layout': {
                'page_width': '6in',
                'page_height': '9in',
                'text_area_width': '4.75in'
            }
        }
        self.typography_manager = TypographyManager(self.imprint_config)
    
    def test_font_config_loading(self):
        """Test font configuration loading"""
        fonts = self.typography_manager.fonts
        
        assert fonts['body'] == 'Adobe Caslon Pro'
        assert fonts['korean'] == 'Apple Myungjo'
        assert fonts['quotations'] == 'Adobe Caslon Pro'
        assert fonts['mnemonics'] == 'Adobe Caslon Pro'
    
    def test_layout_config_loading(self):
        """Test layout configuration loading"""
        layout = self.typography_manager.layout_settings
        
        assert layout['page_width'] == '6in'
        assert layout['page_height'] == '9in'
        assert layout['text_area_width'] == '4.75in'
    
    def test_format_mnemonics_page(self):
        """Test mnemonics page formatting with Adobe Caslon and bullet structure"""
        mnemonics = [
            {
                'acronym': 'RISE',
                'expansion': 'Resource Independence Self-Sustenance Economy',
                'explanation': 'This mnemonic highlights the critical goal for Martian settlements.'
            }
        ]
        
        result = self.typography_manager.format_mnemonics_page(mnemonics)
        
        assert '\\chapter{Mnemonics}' in result
        assert '\\fontspec{Adobe Caslon Pro}' in result
        assert '\\textbf{RISE}' in result
        assert '\\begin{itemize}' in result
        assert '\\item \\textbf{R} -- Resource' in result
        assert '\\item \\textbf{I} -- Independence' in result
        assert 'This mnemonic highlights' in result
    
    def test_format_title_page_korean(self):
        """Test Korean character formatting with Apple Myungjo font"""
        korean_text = "한국어 제목"
        
        result = self.typography_manager.format_title_page_korean(korean_text)
        
        assert '\\fontspec{Apple Myungjo}' in result
        assert korean_text in result
        assert result.startswith('{\\fontspec{Apple Myungjo}')
        assert result.endswith('}')
    
    def test_add_instruction_pages(self):
        """Test instruction placement on every 8th recto page"""
        # Create content with multiple pages
        content = "Page 1\\newpagePage 2\\newpagePage 3\\newpagePage 4\\newpagePage 5\\newpagePage 6\\newpagePage 7\\newpagePage 8\\newpagePage 9"
        
        result = self.typography_manager.add_instruction_pages(content)
        
        # Should contain instruction text
        assert 'Use the facing page for your reflections' in result
        # Instructions should be added at appropriate intervals
        assert '\\vfill\\footnotesize\\textit{Use the facing page' in result
    
    def test_adjust_chapter_heading_leading(self):
        """Test chapter heading leading adjustment to 36 points"""
        content = """
        \\chapter{Introduction}
        This is the chapter content.
        
        \\section{Section Title}
        This is section content.
        """
        
        result = self.typography_manager.adjust_chapter_heading_leading(content)
        
        assert '\\vspace{-36pt}' in result
        assert '\\chapter{Introduction}\\n\\\\vspace{-36pt}' in result
        assert '\\section{Section Title}\\n\\\\vspace{-36pt}' in result
    
    def test_escape_latex_commands(self):
        """Test LaTeX command escaping to prevent visibility in PDF"""
        # Test text with visible LaTeX commands
        text_with_commands = "This text has \\textit visible command"
        
        result = self.typography_manager._escape_latex_commands(text_with_commands)
        
        # Should remove or properly escape the command
        assert '\\textit' not in result or '\\\\textit' in result
    
    def test_escape_special_characters(self):
        """Test escaping of special LaTeX characters"""
        text_with_special = "Price: $10 & 50% off #hashtag"
        
        result = self.typography_manager._escape_latex_commands(text_with_special)
        
        assert '\\$' in result
        assert '\\&' in result
        assert '\\%' in result
        assert '\\#' in result
    
    def test_validate_typography_formatting_valid(self):
        """Test typography validation with valid content"""
        valid_content = """
        \\chapter{Title}
        \\vspace{-36pt}
        \\fontspec{Adobe Caslon Pro}
        This is properly formatted content.
        """
        
        result = self.typography_manager.validate_typography_formatting(valid_content)
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_validate_typography_formatting_invalid(self):
        """Test typography validation with invalid content"""
        invalid_content = """
        \\chapter{Title}
        This text has \\textit visible command.
        """
        
        result = self.typography_manager.validate_typography_formatting(invalid_content)
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert any('Visible LaTeX command' in error for error in result['errors'])
    
    def test_apply_consistent_formatting(self):
        """Test application of consistent formatting across content"""
        content = """
        \\documentclass{memoir}
        \\begin{document}
        \\chapter{Test Chapter}
        This is test content with special chars: & % $
        \\end{document}
        """
        
        result = self.typography_manager.apply_consistent_formatting(content)
        
        # Should have font specifications
        assert '\\usepackage{fontspec}' in result
        assert '\\setmainfont{Adobe Caslon Pro}' in result
        
        # Should have adjusted chapter leading
        assert '\\vspace{-36pt}' in result
        
        # Should have escaped special characters
        assert '\\&' in result
        assert '\\%' in result
        assert '\\$' in result
    
    def test_empty_mnemonics_handling(self):
        """Test handling of empty mnemonics list"""
        result = self.typography_manager.format_mnemonics_page([])
        assert result == ""
    
    def test_empty_korean_text_handling(self):
        """Test handling of empty Korean text"""
        result = self.typography_manager.format_title_page_korean("")
        assert result == ""
    
    def test_error_handling_in_formatting(self):
        """Test error handling in various formatting methods"""
        # Test with None values
        result1 = self.typography_manager.format_mnemonics_page(None)
        assert isinstance(result1, str)
        
        result2 = self.typography_manager.format_title_page_korean(None)
        assert isinstance(result2, str)
        
        result3 = self.typography_manager.adjust_chapter_heading_leading(None)
        assert isinstance(result3, str)
    
    def test_font_config_defaults(self):
        """Test default font configuration when imprint config is incomplete"""
        empty_config = {}
        manager = TypographyManager(empty_config)
        
        assert manager.fonts['body'] == 'Adobe Caslon Pro'
        assert manager.fonts['korean'] == 'Apple Myungjo'
        assert manager.fonts['quotations'] == 'Adobe Caslon Pro'
        assert manager.fonts['mnemonics'] == 'Adobe Caslon Pro'
    
    def test_layout_config_defaults(self):
        """Test default layout configuration when imprint config is incomplete"""
        empty_config = {}
        manager = TypographyManager(empty_config)
        
        assert manager.layout_settings['page_width'] == '6in'
        assert manager.layout_settings['page_height'] == '9in'
        assert manager.layout_settings['text_area_width'] == '4.75in'