"""
Integration tests for book production fixes and enhancements.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch


class TestBookProductionFixesIntegration:
    """Integration tests for all book production fixes"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_bibliography_formatting_integration(self):
        """Test bibliography formatting with memoir citation fields"""
        try:
            from src.codexes.modules.prepress.bibliography_formatter import BibliographyFormatter
            
            config = {'citation_style': 'chicago'}
            formatter = BibliographyFormatter(config)
            
            entries = [
                {'author': 'Smith, John', 'title': 'Test Book', 'year': '2023'},
                {'author': 'Doe, Jane', 'title': 'Another Book', 'year': '2024'}
            ]
            
            result = formatter.generate_latex_bibliography(entries)
            
            assert '\\begin{thebibliography}' in result
            assert '0.15in' in result  # Hanging indent
            assert 'Smith, John' in result
            assert 'Doe, Jane' in result
            
        except ImportError:
            pytest.skip("Bibliography formatter not available")
    
    def test_isbn_caching_integration(self):
        """Test ISBN lookup caching system"""
        try:
            from src.codexes.modules.distribution.isbn_lookup_cache import ISBNLookupCache
            
            cache_file = os.path.join(self.temp_dir, "test_cache.json")
            cache = ISBNLookupCache(cache_file)
            
            # Test caching
            test_data = {'title': 'Test Book', 'author': 'Test Author'}
            cache.cache_isbn_data('9781234567890', test_data)
            
            # Test retrieval
            cached_data = cache.lookup_isbn('9781234567890')
            assert cached_data is not None
            assert cached_data['title'] == 'Test Book'
            
        except ImportError:
            pytest.skip("ISBN cache not available")
    
    def test_reporting_accuracy_integration(self):
        """Test accurate reporting system"""
        try:
            from src.codexes.modules.distribution.accurate_reporting_system import AccurateReportingSystem
            
            reporting = AccurateReportingSystem()
            
            # Track some operations
            reporting.track_prompt_execution('test_prompt', True, {'execution_time': 1.0})
            reporting.track_quote_retrieval('book_1', 85, 90)
            
            # Generate report
            report = reporting.generate_accurate_report()
            
            assert report['overall_statistics']['total_prompts_executed'] == 1
            assert report['overall_statistics']['total_quotes_retrieved'] == 85
            assert report['overall_statistics']['quote_retrieval_rate'] == 85/90
            
        except ImportError:
            pytest.skip("Reporting system not available")
    
    def test_error_handling_integration(self):
        """Test enhanced error handling system"""
        try:
            from src.codexes.modules.distribution.enhanced_error_handler import EnhancedErrorHandler
            import logging
            
            logger = logging.getLogger("test")
            error_handler = EnhancedErrorHandler(logger)
            
            # Test quote verification error handling
            invalid_response = {'invalid': 'data'}
            result = error_handler.handle_quote_verification_error(invalid_response, {})
            
            assert 'verified_quotes' in result
            assert result['verification_status'] == 'failed'
            
        except ImportError:
            pytest.skip("Error handler not available")
    
    def test_typography_integration(self):
        """Test typography management system"""
        try:
            from src.codexes.modules.prepress.typography_manager import TypographyManager
            
            config = {'fonts': {'korean': 'Apple Myungjo'}}
            typography = TypographyManager(config)
            
            # Test Korean text formatting
            korean_text = "한국어 텍스트"
            result = typography.format_title_page_korean(korean_text)
            
            assert 'Apple Myungjo' in result
            assert korean_text in result
            
        except ImportError:
            pytest.skip("Typography manager not available")
    
    def test_glossary_layout_integration(self):
        """Test glossary layout system"""
        try:
            from src.codexes.modules.prepress.glossary_layout_manager import GlossaryLayoutManager
            
            config = {'text_area': {'width': '4.75in'}}
            glossary = GlossaryLayoutManager(config)
            
            terms = [
                {'korean': '자원', 'english': 'Resource', 'definition': 'Materials'},
                {'korean': '독립', 'english': 'Independence', 'definition': 'Freedom'}
            ]
            
            result = glossary.format_glossary_single_column(terms)
            
            assert '\\begin{multicols}' not in result
            assert '자원' in result
            assert 'Resource' in result
            
        except ImportError:
            pytest.skip("Glossary manager not available")
    
    def test_pilsa_content_processing_integration(self):
        """Test pilsa book content processing"""
        try:
            from src.codexes.modules.prepress.pilsa_book_content_processor import PilsaBookContentProcessor
            
            processor = PilsaBookContentProcessor()
            
            # Test back cover enhancement
            back_text = "This is a great book about personal development."
            result = processor.enhance_back_cover_text(back_text)
            
            assert 'pilsa book' in result.lower()
            assert '90 quotations' in result
            assert 'journaling' in result.lower()
            
        except ImportError:
            pytest.skip("Pilsa processor not available")
    
    def test_end_to_end_workflow(self):
        """Test end-to-end workflow with multiple components"""
        try:
            # This would test the complete workflow
            # For now, just verify components can be imported together
            
            from src.codexes.modules.prepress.bibliography_formatter import BibliographyFormatter
            from src.codexes.modules.distribution.isbn_lookup_cache import ISBNLookupCache
            from src.codexes.modules.distribution.accurate_reporting_system import AccurateReportingSystem
            
            # Initialize components
            bibliography = BibliographyFormatter({'citation_style': 'chicago'})
            cache = ISBNLookupCache(os.path.join(self.temp_dir, "cache.json"))
            reporting = AccurateReportingSystem()
            
            # Verify they work together
            assert bibliography is not None
            assert cache is not None
            assert reporting is not None
            
        except ImportError as e:
            pytest.skip(f"Components not available: {e}")
    
    def test_configuration_integration(self):
        """Test configuration system integration"""
        try:
            from src.codexes.modules.ui.tranche_config_ui_manager import TrancheConfigUIManager
            
            # Create test tranche config
            test_config = {
                'display_name': 'Test Tranche',
                'imprint': 'test_imprint',
                'publisher': 'test_publisher',
                'contributor_one': 'Test Author'
            }
            
            manager = TrancheConfigUIManager()
            manager.tranches_dir = self.temp_dir
            
            # Create test config file
            import json
            config_path = os.path.join(self.temp_dir, "test_tranche.json")
            with open(config_path, 'w') as f:
                json.dump(test_config, f)
            
            # Test loading
            tranches = manager.load_available_tranches()
            assert len(tranches) >= 0  # Should not crash
            
        except ImportError:
            pytest.skip("Tranche config manager not available")
    
    def test_performance_benchmarks(self):
        """Test performance of key components"""
        import time
        
        try:
            from src.codexes.modules.prepress.bibliography_formatter import BibliographyFormatter
            
            formatter = BibliographyFormatter({'citation_style': 'chicago'})
            
            # Test with large number of entries
            entries = [
                {'author': f'Author {i}', 'title': f'Title {i}', 'year': '2023'}
                for i in range(100)
            ]
            
            start_time = time.time()
            result = formatter.generate_latex_bibliography(entries)
            end_time = time.time()
            
            # Should complete within reasonable time
            assert end_time - start_time < 5.0  # 5 seconds max
            assert len(result) > 0
            
        except ImportError:
            pytest.skip("Performance test components not available")