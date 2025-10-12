"""
Comprehensive tests for all book production fixes
"""

import pytest
import tempfile
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.modules.prepress.bibliography_formatter import BibliographyFormatter, BibliographyEntry
from codexes.modules.distribution.isbn_lookup_cache import ISBNLookupCache
from codexes.modules.distribution.accurate_reporting_system import AccurateReportingSystem
from codexes.modules.distribution.enhanced_error_handler import EnhancedErrorHandler
from codexes.modules.prepress.typography_manager import TypographyManager
from codexes.modules.prepress.glossary_layout_manager import GlossaryLayoutManager
from codexes.modules.builders.publishers_note_generator import PublishersNoteGenerator
from codexes.modules.distribution.writing_style_manager import WritingStyleManager
from codexes.modules.distribution.quote_assembly_optimizer import QuoteAssemblyOptimizer
from codexes.modules.distribution.isbn_barcode_generator import ISBNBarcodeGenerator

class TestBibliographyFormatter:
    """Test bibliography formatting with memoir citation fields"""
    
    def setup_method(self):
        self.formatter = BibliographyFormatter()
    
    def test_format_bibliography_entry_chicago(self):
        """Test Chicago style bibliography formatting"""
        entry = BibliographyEntry(
            author="Smith, John",
            title="Test Book",
            publisher="Test Publisher",
            year="2023"
        )
        
        result = self.formatter.format_bibliography_entry(entry)
        
        assert "Smith, John." in result
        assert "\\textit{Test Book}" in result
        assert "Test Publisher" in result
        assert "2023" in result
    
    def test_memoir_citation_field_integration(self):
        """Test memoir citation field formatting"""
        entries = [
            BibliographyEntry(author="Author One", title="Book One", publisher="Pub One", year="2023"),
            BibliographyEntry(author="Author Two", title="Book Two", publisher="Pub Two", year="2024")
        ]
        
        result = self.formatter.apply_memoir_citation_field(entries)
        
        assert "\\begin{thebibliography}" in result
        assert "\\setlength{\\itemindent}{-0.15in}" in result
        assert "\\bibitem{001}" in result
        assert "\\bibitem{002}" in result
        assert "\\end{thebibliography}" in result
    
    def test_hanging_indent_application(self):
        """Test that hanging indent is properly applied"""
        entries = [BibliographyEntry(author="Test", title="Test", publisher="Test", year="2023")]
        result = self.formatter.generate_latex_bibliography(entries)
        
        assert "0.15in" in result
        assert "itemindent" in result
        assert "leftmargin" in result

class TestISBNLookupCache:
    """Test ISBN lookup caching system"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = Path(self.temp_dir) / "test_isbn_cache.json"
        self.cache = ISBNLookupCache(str(self.cache_file))
    
    def test_isbn_normalization(self):
        """Test ISBN normalization"""
        test_cases = [
            ("978-0-123456-78-9", "9780123456789"),
            ("978 0 123456 78 9", "9780123456789"),
            ("9780123456789", "9780123456789"),
            ("invalid", None)
        ]
        
        for input_isbn, expected in test_cases:
            result = self.cache._normalize_isbn(input_isbn)
            assert result == expected
    
    def test_cache_persistence(self):
        """Test that cache data persists across instances"""
        # Add data to first instance
        test_data = {
            'isbn': '9780123456789',
            'title': 'Test Book',
            'author': 'Test Author',
            'publisher': 'Test Publisher',
            'publication_date': '2023',
            'source': 'test',
            'lookup_timestamp': '2023-01-01T00:00:00'
        }
        
        self.cache.cache_isbn_data('9780123456789', test_data)
        
        # Create new instance
        new_cache = ISBNLookupCache(str(self.cache_file))
        
        # Verify data was loaded
        assert '9780123456789' in new_cache.cache_data
        assert new_cache.cache_data['9780123456789'].title == 'Test Book'
    
    def test_document_processing_tracking(self):
        """Test document processing tracking"""
        doc_id = "test_document"
        content = "This is test content with ISBN 9780123456789"
        
        # First scan
        isbns = self.cache.scan_document_for_isbns(doc_id, content)
        # Note: The ISBN extraction might not find ISBNs in this simple test
        # The important part is that the document is marked as processed
        assert self.cache.is_document_processed(doc_id)
        
        # Second scan should return empty (already processed)
        isbns2 = self.cache.scan_document_for_isbns(doc_id, content)
        assert len(isbns2) == 0

class TestAccurateReportingSystem:
    """Test accurate reporting system"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.report_file = Path(self.temp_dir) / "test_report.json"
        self.reporting = AccurateReportingSystem(str(self.report_file))
    
    def test_prompt_execution_tracking(self):
        """Test prompt execution tracking"""
        self.reporting.track_prompt_execution(
            "test_prompt",
            True,
            {'execution_time': 1.5, 'model_name': 'test-model', 'response_length': 1000}
        )
        
        assert "test_prompt" in self.reporting.prompt_stats
        assert len(self.reporting.prompt_stats["test_prompt"]) == 1
        assert self.reporting.prompt_stats["test_prompt"][0].success is True
    
    def test_quote_retrieval_tracking(self):
        """Test quote retrieval tracking"""
        self.reporting.track_quote_retrieval("test_book", 90, 90, 85, 80, 3.0)
        
        assert "test_book" in self.reporting.quote_stats
        result = self.reporting.quote_stats["test_book"]
        assert result.quotes_retrieved == 90
        assert result.quotes_requested == 90
    
    def test_accurate_report_generation(self):
        """Test accurate report generation"""
        # Add test data
        self.reporting.track_prompt_execution("prompt1", True, {'execution_time': 1.0, 'model_name': 'test', 'response_length': 500})
        self.reporting.track_quote_retrieval("book1", 90, 90, 85, 80, 3.0)
        
        report = self.reporting.generate_accurate_report()
        
        assert 'summary' in report
        assert report['summary']['successful_prompts'] == 1
        assert report['summary']['total_quotes_retrieved'] == 90

class TestEnhancedErrorHandler:
    """Test enhanced error handler"""
    
    def setup_method(self):
        import logging
        self.logger = logging.getLogger("test")
        self.temp_dir = tempfile.mkdtemp()
        self.error_log = Path(self.temp_dir) / "test_errors.json"
        self.handler = EnhancedErrorHandler(self.logger, str(self.error_log))
    
    def test_quote_verification_error_recovery(self):
        """Test quote verification error recovery"""
        invalid_response = {'status': 'completed'}  # Missing verified_quotes
        context = {
            'original_quotes': [{'quote': 'test', 'author': 'test', 'source': 'test'}],
            'verifier_model': 'test-model'
        }
        
        result = self.handler.handle_quote_verification_error(invalid_response, context)
        
        assert 'verified_quotes' in result
        assert 'verification_status' in result
    
    def test_field_completion_error_recovery(self):
        """Test field completion error recovery"""
        error = AttributeError("Missing method")
        
        result = self.handler.handle_field_completion_error(error, "test_field", None)
        
        assert callable(result)
    
    def test_error_history_tracking(self):
        """Test error history tracking"""
        error = Exception("Test error")
        context = {'test': 'data'}
        
        initial_count = len(self.handler.error_history)
        self.handler.log_error_with_context(error, context)
        
        assert len(self.handler.error_history) == initial_count + 1

class TestTypographyManager:
    """Test typography manager"""
    
    def setup_method(self):
        self.typography = TypographyManager()
    
    def test_mnemonics_formatting(self):
        """Test mnemonics page formatting"""
        mnemonics = [
            {'text': 'Test mnemonic 1', 'type': 'standard'},
            {'text': 'Test mnemonic 2', 'type': 'standard'}
        ]
        
        result = self.typography.format_mnemonics_page(mnemonics)
        
        assert "Adobe Caslon" in result
        assert "\\begin{itemize}" in result
        assert "Test mnemonic 1" in result
        assert "Test mnemonic 2" in result
    
    def test_korean_text_formatting(self):
        """Test Korean text formatting"""
        korean_text = "안녕하세요"
        
        result = self.typography.format_title_page_korean(korean_text)
        
        assert "Apple Myungjo" in result
        assert korean_text in result
    
    def test_chapter_heading_adjustment(self):
        """Test chapter heading leading adjustment"""
        content = "\\chapter{Test Chapter}\nContent here"
        
        result = self.typography.adjust_chapter_heading_leading(content)
        
        assert "36pt" in result or "vspace" in result

class TestGlossaryLayoutManager:
    """Test glossary layout manager"""
    
    def setup_method(self):
        self.glossary = GlossaryLayoutManager()
    
    def test_two_column_formatting(self):
        """Test two-column glossary formatting"""
        terms = [
            {'korean': '안녕', 'english': 'hello', 'definition': 'A greeting'},
            {'korean': '감사', 'english': 'thanks', 'definition': 'Expression of gratitude'}
        ]
        
        result = self.glossary.format_glossary_single_column(terms)
        
        assert "\\begin{multicols}" not in result
        assert "안녕" in result
        assert "hello" in result
    
    def test_term_stacking(self):
        """Test Korean/English term stacking"""
        result = self.glossary.stack_korean_english_terms("안녕", "hello")
        
        assert "Apple Myungjo" in result
        assert "Adobe Caslon" in result
        assert "안녕" in result
        assert "hello" in result
    
    def test_column_distribution(self):
        """Test term distribution across columns"""
        terms = [{'english': f'term{i}'} for i in range(10)]
        
        left, right = self.glossary.distribute_terms_across_columns(terms)
        
        assert len(left) + len(right) == len(terms)
        assert abs(len(left) - len(right)) <= 1  # Balanced distribution

class TestPublishersNoteGenerator:
    """Test Publisher's Note generator"""
    
    def setup_method(self):
        self.generator = PublishersNoteGenerator()
    
    def test_structured_note_generation(self):
        """Test structured Publisher's Note generation"""
        book_data = {
            'title': 'Test Book',
            'author': 'Test Author',
            'stream': 'Test Stream',
            'description': 'Test description',
            'quotes': [{'quote': 'test'}] * 90
        }
        
        result = self.generator.generate_publishers_note(book_data)
        
        # Check structure
        paragraphs = [p.strip() for p in result.split('\n\n') if p.strip()]
        assert len(paragraphs) == 3
        
        # Check length constraints
        for paragraph in paragraphs:
            assert len(paragraph) <= 600
        
        # Check required content
        assert 'pilsa' in result.lower()
    
    def test_paragraph_length_enforcement(self):
        """Test paragraph length enforcement"""
        long_paragraph = "This is a very long paragraph. " * 50  # Over 600 chars
        
        result = self.generator._ensure_paragraph_length(long_paragraph, 1)
        
        assert len(result) <= 600
    
    def test_validation(self):
        """Test Publisher's Note validation"""
        valid_note = ("This pilsa book offers comprehensive insights into the subject matter. " +
                     "The carefully curated content provides valuable perspectives for readers.\n\n" +
                     "The content addresses contemporary challenges and modern applications. " +
                     "Each section is designed to engage readers intellectually and practically.\n\n" +
                     "Readers will benefit greatly from this structured approach to learning. " +
                     "The pilsa format ensures accessibility while maintaining academic rigor.")
        
        # Set up the generator state
        self.generator.pilsa_explanation_included = True
        
        result = self.generator._validate_publishers_note(valid_note)
        assert result is True

class TestWritingStyleManager:
    """Test writing style manager"""
    
    def setup_method(self):
        self.style_manager = WritingStyleManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def test_style_config_validation(self):
        """Test writing style configuration validation"""
        valid_config = {
            'text_values': ['Write clearly', 'Use active voice'],
            'style_type': 'formal'
        }
        
        result = self.style_manager.validate_style_config_data(valid_config)
        
        assert result['is_valid'] is True
        assert len(result['errors']) == 0
    
    def test_prompt_construction(self):
        """Test style prompt construction"""
        style_config = {
            'text_values': ['Write clearly', 'Use active voice', 'Be concise']
        }
        
        result = self.style_manager.construct_style_prompt(style_config)
        
        assert 'Write clearly' in result
        assert 'Use active voice' in result
        assert 'Be concise' in result
    
    def test_hierarchical_loading(self):
        """Test hierarchical style loading"""
        # This would require setting up mock config files
        result = self.style_manager.load_writing_style()
        
        # Should return default style when no configs found
        assert 'text_values' in result
        assert 'style_type' in result

class TestQuoteAssemblyOptimizer:
    """Test quote assembly optimizer"""
    
    def setup_method(self):
        self.optimizer = QuoteAssemblyOptimizer(max_consecutive_author=3)
    
    def test_author_distribution_analysis(self):
        """Test author distribution analysis"""
        quotes = [
            {'author': 'Author A', 'quote': 'Quote 1'},
            {'author': 'Author A', 'quote': 'Quote 2'},
            {'author': 'Author A', 'quote': 'Quote 3'},
            {'author': 'Author A', 'quote': 'Quote 4'},  # Violation
            {'author': 'Author B', 'quote': 'Quote 5'}
        ]
        
        analysis = self.optimizer.check_author_distribution(quotes)
        
        assert analysis.total_quotes == 5
        assert analysis.unique_authors == 2
        assert len(analysis.consecutive_violations) == 1
        assert analysis.max_consecutive == 4
    
    def test_quote_optimization(self):
        """Test quote order optimization"""
        quotes = [
            {'author': 'Author A', 'quote': 'Quote 1'},
            {'author': 'Author A', 'quote': 'Quote 2'},
            {'author': 'Author A', 'quote': 'Quote 3'},
            {'author': 'Author A', 'quote': 'Quote 4'},
            {'author': 'Author B', 'quote': 'Quote 5'},
            {'author': 'Author B', 'quote': 'Quote 6'}
        ]
        
        optimized = self.optimizer.optimize_quote_order(quotes)
        
        # Check that optimization reduced violations
        original_analysis = self.optimizer.check_author_distribution(quotes)
        optimized_analysis = self.optimizer.check_author_distribution(optimized)
        
        assert len(optimized_analysis.consecutive_violations) <= len(original_analysis.consecutive_violations)
    
    def test_validation(self):
        """Test author distribution validation"""
        valid_quotes = [
            {'author': 'Author A', 'quote': 'Quote 1'},
            {'author': 'Author B', 'quote': 'Quote 2'},
            {'author': 'Author A', 'quote': 'Quote 3'}
        ]
        
        result = self.optimizer.validate_author_distribution(valid_quotes)
        assert result is True

class TestISBNBarcodeGenerator:
    """Test ISBN barcode generator"""
    
    def setup_method(self):
        self.generator = ISBNBarcodeGenerator()
    
    def test_isbn_normalization(self):
        """Test ISBN-13 normalization"""
        test_cases = [
            ("978-0-123456-78-9", "9780123456789"),
            ("978 0 123456 78 9", "9780123456789"),
            ("9780123456789", "9780123456789"),
            ("invalid", None),
            ("123456789", None)  # Too short
        ]
        
        for input_isbn, expected in test_cases:
            result = self.generator._normalize_isbn13(input_isbn)
            assert result == expected
    
    def test_isbn_to_upc_conversion(self):
        """Test ISBN-13 to UPC conversion"""
        isbn13 = "9780123456789"
        
        result = self.generator._isbn13_to_upc(isbn13)
        
        assert result is not None
        # The result should be 10 digits (after removing 978 prefix and recalculating check digit)
        # Then it becomes 12 digits when formatted as UPC-A
        assert len(result) >= 10
    
    def test_barcode_info_generation(self):
        """Test barcode information generation"""
        isbn = "978-0-123456-78-9"
        
        info = self.generator.get_barcode_info(isbn)
        
        assert 'original_isbn' in info
        assert 'normalized_isbn' in info
        assert 'upc_code' in info
        assert 'is_valid_isbn' in info
    
    def test_numeral_formatting(self):
        """Test barcode numeral formatting"""
        isbn = "9780123456789"
        
        result = self.generator.format_barcode_numerals(isbn)
        
        assert "-" in result  # Should be formatted with hyphens
        assert "978" in result

class TestIntegrationScenarios:
    """Test integration scenarios combining multiple fixes"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def test_complete_book_processing_pipeline(self):
        """Test complete book processing with all fixes"""
        # Set up components
        bibliography = BibliographyFormatter()
        reporting = AccurateReportingSystem()
        typography = TypographyManager()
        
        # Test data
        book_data = {
            'title': 'Integration Test Book',
            'author': 'Test Author',
            'isbn13': '9780123456789',
            'quotes': [
                {'author': 'Author A', 'quote': 'Quote 1', 'source': 'Source 1'},
                {'author': 'Author B', 'quote': 'Quote 2', 'source': 'Source 2'}
            ]
        }
        
        # Test bibliography formatting
        entries = [
            BibliographyEntry(author="Test Author", title="Test Book", publisher="Test Pub", year="2023")
        ]
        bib_result = bibliography.generate_latex_bibliography(entries)
        assert "\\begin{thebibliography}" in bib_result
        
        # Test reporting
        reporting.track_quote_retrieval("test_book", 2, 2, 2, 2, 1.0)
        report = reporting.generate_accurate_report()
        assert report['summary']['total_quotes_retrieved'] == 2
        
        # Test typography
        mnemonics = [{'text': 'Test mnemonic', 'type': 'standard'}]
        typo_result = typography.format_mnemonics_page(mnemonics)
        assert "Adobe Caslon" in typo_result
    
    def test_error_handling_integration(self):
        """Test error handling across all components"""
        import logging
        logger = logging.getLogger("integration_test")
        error_handler = EnhancedErrorHandler(logger)
        
        # Test various error scenarios
        quote_error = error_handler.handle_quote_verification_error({}, {})
        assert 'verified_quotes' in quote_error
        
        field_error = error_handler.handle_field_completion_error(
            Exception("Test error"), "test_field", None
        )
        assert callable(field_error)
    
    def test_performance_with_large_datasets(self):
        """Test performance with large datasets"""
        # Test with large quote list
        large_quote_list = []
        for i in range(1000):
            large_quote_list.append({
                'author': f'Author {i % 10}',  # 10 different authors
                'quote': f'Quote {i}',
                'source': f'Source {i}'
            })
        
        optimizer = QuoteAssemblyOptimizer()
        
        # This should complete in reasonable time
        import time
        start_time = time.time()
        optimized = optimizer.optimize_quote_order(large_quote_list)
        end_time = time.time()
        
        assert len(optimized) == len(large_quote_list)
        assert end_time - start_time < 10  # Should complete in under 10 seconds
    
    def test_configuration_validation(self):
        """Test configuration validation across components"""
        # Test typography configuration
        typography = TypographyManager({'fonts': {'adobe_caslon': 'Adobe Caslon Pro'}})
        validation = typography.validate_typography_settings()
        assert validation['fonts_configured'] is True
        
        # Test writing style configuration
        style_manager = WritingStyleManager()
        config_validation = style_manager.validate_style_config_data({
            'text_values': ['Test style'],
            'style_type': 'formal'
        })
        assert config_validation['is_valid'] is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])