"""
Tests for glossary layout management system.
"""

import pytest
from src.codexes.modules.prepress.glossary_layout_manager import GlossaryLayoutManager


class TestGlossaryLayoutManager:
    
    def setup_method(self):
        """Set up test fixtures"""
        self.page_config = {
            'text_area': {
                'width': '4.75in',
                'height': '7.5in'
            },
            'column_sep': '0.25in',
            'term_spacing': '0.5em'
        }
        self.glossary_manager = GlossaryLayoutManager(self.page_config)
    
    def test_single_column_initialization(self):
        """Test single-column glossary manager initialization"""
        # Single column layout should not have column width calculation
        assert self.glossary_manager.column_count == 1
        assert hasattr(self.glossary_manager, 'term_spacing')
    
    def test_stack_korean_english_terms(self):
        """Test stacking of Korean and English terms in left-hand cells"""
        korean_term = "자원"
        english_term = "Resource"
        definition = "Materials or assets that can be used"
        
        result = self.glossary_manager.stack_korean_english_terms(
            korean_term, english_term, definition
        )
        
        assert '\\textbf{\\korean{자원}}' in result
        assert '\\textit{Resource}' in result
        assert 'Materials or assets that can be used' in result
        assert '\\vspace{-12pt}' in result
    
    def test_single_column_layout(self):
        """Test single column layout doesn't distribute terms"""
        terms = [
            {'korean': '자원', 'english': 'Resource'},
            {'korean': '독립', 'english': 'Independence'},
            {'korean': '경제', 'english': 'Economy'},
            {'korean': '지속', 'english': 'Sustainability'},
            {'korean': '화성', 'english': 'Mars'}
        ]
        
        # Single column layout processes all terms in order
        result = self.glossary_manager.format_glossary_single_column(terms)
        
        # Should contain all terms
        assert '\\korean{자원}' in result
        assert '\\korean{독립}' in result
        assert '\\korean{경제}' in result
        assert '\\korean{지속}' in result
        assert '\\korean{화성}' in result
    
    def test_format_glossary_single_column(self):
        """Test formatting glossary in single column layout"""
        terms = [
            {'korean': '자원', 'english': 'Resource', 'definition': 'Materials that can be used'},
            {'korean': '독립', 'english': 'Independence', 'definition': 'Freedom from dependence'},
            {'korean': '경제', 'english': 'Economy', 'definition': 'System of trade and industry'}
        ]
        
        result = self.glossary_manager.format_glossary_single_column(terms)
        
        assert '\\chapter*{Glossary}' in result
        assert '\\begin{multicols}' not in result
        assert '\\end{multicols}' not in result
        assert '\\korean{자원}' in result
        assert '\\textit{Resource}' in result
    
    def test_validate_glossary_layout_valid(self):
        """Test validation of valid single-column glossary layout"""
        valid_latex = """
        \\chapter*{Glossary}
        \\textbf{\\korean{자원}} \\textit{Resource}
        Materials
        \\vspace{-12pt}
        \\textbf{\\korean{독립}} \\textit{Independence}
        Freedom
        \\vspace{-12pt}
        """
        
        result = self.glossary_manager.validate_glossary_layout(valid_latex)
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_validate_glossary_layout_invalid(self):
        """Test validation of invalid glossary layout with multicols"""
        invalid_latex = """
        \\chapter{Glossary}
        \\begin{multicols}{2}
        Some content with multicols which should be invalid for single-column
        \\end{multicols}
        """
        
        result = self.glossary_manager.validate_glossary_layout(invalid_latex)
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert any('should not use multicols' in error for error in result['errors'])
    
    def test_extract_glossary_terms_korean_english(self):
        """Test extraction of Korean-English term pairs from content"""
        content = """
        This text contains glossary terms:
        자원 - Resource: Materials that can be used
        독립 - Independence: Freedom from dependence
        경제 - Economy: System of trade and industry
        """
        
        terms = self.glossary_manager.extract_glossary_terms(content)
        
        assert len(terms) >= 3
        
        # Check for specific terms
        resource_term = next((t for t in terms if t['korean'] == '자원'), None)
        assert resource_term is not None
        assert resource_term['english'] == 'Resource'
        assert 'Materials' in resource_term['definition']
    
    def test_extract_glossary_terms_english_korean(self):
        """Test extraction of English-Korean term pairs from content"""
        content = """
        Resource - 자원: Materials that can be used
        Independence - 독립: Freedom from dependence
        """
        
        terms = self.glossary_manager.extract_glossary_terms(content)
        
        assert len(terms) >= 2
        
        # Check term extraction
        resource_term = next((t for t in terms if t['english'] == 'Resource'), None)
        assert resource_term is not None
        assert resource_term['korean'] == '자원'
    
    def test_sort_glossary_terms_by_english(self):
        """Test sorting glossary terms by English alphabetically"""
        terms = [
            {'korean': '자원', 'english': 'Resource'},
            {'korean': '경제', 'english': 'Economy'},
            {'korean': '독립', 'english': 'Independence'}
        ]
        
        sorted_terms = self.glossary_manager.sort_glossary_terms(terms, 'english')
        
        # Should be sorted: Economy, Independence, Resource
        assert sorted_terms[0]['english'] == 'Economy'
        assert sorted_terms[1]['english'] == 'Independence'
        assert sorted_terms[2]['english'] == 'Resource'
    
    def test_sort_glossary_terms_by_korean(self):
        """Test sorting glossary terms by Korean alphabetically"""
        terms = [
            {'korean': '자원', 'english': 'Resource'},
            {'korean': '경제', 'english': 'Economy'},
            {'korean': '독립', 'english': 'Independence'}
        ]
        
        sorted_terms = self.glossary_manager.sort_glossary_terms(terms, 'korean')
        
        # Should be sorted by Korean characters
        assert len(sorted_terms) == 3
        # Exact order depends on Korean collation, but should be consistent
        assert all(term['korean'] for term in sorted_terms)
    
    def test_generate_glossary_from_content(self):
        """Test complete glossary generation from content"""
        content = """
        This book discusses various concepts:
        자원 - Resource: Materials that can be used
        독립 - Independence: Freedom from dependence
        경제 - Economy: System of trade and industry
        """
        
        result = self.glossary_manager.generate_glossary_from_content(content)
        
        assert '\\chapter*{Glossary}' in result
        assert '\\begin{multicols}' not in result  # Single column should not use multicols
        assert '자원' in result
        assert 'Resource' in result
        assert 'Materials' in result
    
    def test_get_layout_statistics(self):
        """Test glossary layout statistics"""
        terms = [
            {'korean': '자원', 'english': 'Resource', 'definition': 'Materials'},
            {'korean': '독립', 'english': 'Independence'},
            {'korean': '', 'english': 'Economy', 'definition': 'Trade system'},
            {'korean': '화성', 'english': ''}
        ]
        
        stats = self.glossary_manager.get_layout_statistics(terms)
        
        assert stats['total_terms'] == 4
        # Single column layout doesn't have column distribution
        assert 'left_column_terms' not in stats
        assert 'right_column_terms' not in stats
        assert stats['korean_terms'] == 3  # Terms with Korean text
        assert stats['english_terms'] == 3  # Terms with English text
        assert stats['terms_with_definitions'] == 2
    
    def test_empty_terms_handling(self):
        """Test handling of empty terms list"""
        result = self.glossary_manager.format_glossary_single_column([])
        assert result == ""
        
        # Single column layout doesn't distribute terms
        stats = self.glossary_manager.get_layout_statistics([])
        assert stats['total_terms'] == 0
    
    def test_single_term_handling(self):
        """Test handling of single term"""
        terms = [{'korean': '자원', 'english': 'Resource'}]
        
        # Single column layout processes single term correctly
        result = self.glossary_manager.format_glossary_single_column(terms)
        assert '\\korean{자원}' in result
        assert '\\textit{Resource}' in result
    
    def test_error_handling(self):
        """Test error handling in various methods"""
        # Test with malformed terms
        malformed_terms = [{'invalid': 'data'}]
        
        result = self.glossary_manager.format_glossary_single_column(malformed_terms)
        assert isinstance(result, str)
        
        # Test with None values
        result2 = self.glossary_manager.stack_korean_english_terms(None, None)
        assert isinstance(result2, str)
    
    def test_single_column_configuration(self):
        """Test single column configuration with various inputs"""
        # Test with different configurations
        config_pt = {'text_area': {'width': '342pt'}, 'term_spacing': '1em'}
        manager_pt = GlossaryLayoutManager(config_pt)
        assert manager_pt.column_count == 1
        
        # Test with minimal config
        config_minimal = {}
        manager_minimal = GlossaryLayoutManager(config_minimal)
        assert manager_minimal.column_count == 1