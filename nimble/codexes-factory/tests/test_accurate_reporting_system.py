"""
Tests for accurate reporting system.
"""

import pytest
import tempfile
import os
from datetime import datetime
try:
    from src.codexes.modules.distribution.accurate_reporting_system import (
        AccurateReportingSystem, ProcessingStatistics, PromptExecution, QuoteRetrievalRecord
    )
except ImportError:
    from codexes.modules.distribution.accurate_reporting_system import (
        AccurateReportingSystem, ProcessingStatistics, PromptExecution, QuoteRetrievalRecord
    )


class TestAccurateReportingSystem:
    
    def setup_method(self):
        """Set up test fixtures"""
        self.reporting_system = AccurateReportingSystem()
    
    def test_track_prompt_execution(self):
        """Test prompt execution tracking"""
        # Track successful prompt
        self.reporting_system.track_prompt_execution(
            "test_prompt", 
            True, 
            {"execution_time": 1.5, "model": "gpt-4"}
        )
        
        # Track failed prompt
        self.reporting_system.track_prompt_execution(
            "test_prompt", 
            False, 
            {"execution_time": 0.8, "error_message": "API timeout"}
        )
        
        # Check statistics
        assert self.reporting_system.processing_stats.total_prompts == 2
        assert self.reporting_system.processing_stats.successful_prompts == 1
        assert self.reporting_system.processing_stats.failed_prompts == 1
        assert self.reporting_system.processing_stats.processing_time == 2.3
    
    def test_track_quote_retrieval(self):
        """Test quote retrieval tracking"""
        # Track quote retrieval
        self.reporting_system.track_quote_retrieval(
            book_id="book_123",
            quotes_retrieved=85,
            quotes_requested=90,
            source="llm_generation",
            retrieval_time=2.5
        )
        
        # Check statistics
        assert self.reporting_system.processing_stats.total_quotes_requested == 90
        assert self.reporting_system.processing_stats.total_quotes_retrieved == 85
        
        # Check book-specific stats
        book_stats = self.reporting_system.quote_stats["book_123"]
        assert len(book_stats) == 1
        assert book_stats[0].quotes_retrieved == 85
        assert book_stats[0].success_rate == 85/90
        assert book_stats[0].retrieval_time == 2.5
    
    def test_quote_count_accuracy(self):
        """Test that reported quote counts match actual retrieval"""
        # Track multiple quote retrievals
        self.reporting_system.track_quote_retrieval("book_1", 45, 50)
        self.reporting_system.track_quote_retrieval("book_2", 38, 40)
        self.reporting_system.track_quote_retrieval("book_3", 42, 45)
        
        report = self.reporting_system.generate_accurate_report()
        overall_stats = report['overall_statistics']
        
        # Should show actual counts, not 0
        assert overall_stats['total_quotes_retrieved'] == 125  # 45 + 38 + 42
        assert overall_stats['total_quotes_requested'] == 135  # 50 + 40 + 45
        assert overall_stats['quote_retrieval_rate'] == 125/135
        assert overall_stats['books_processed'] == 3
    
    def test_prompt_success_rate_calculation(self):
        """Test accurate prompt success rate calculation"""
        # Track multiple prompts with different success rates
        prompts = [
            ("generate_quotes", True, {}),
            ("generate_quotes", True, {}),
            ("generate_quotes", False, {"error_message": "timeout"}),
            ("verify_quotes", True, {}),
            ("verify_quotes", False, {"error_message": "invalid response"})
        ]
        
        for prompt_name, success, details in prompts:
            self.reporting_system.track_prompt_execution(prompt_name, success, details)
        
        report = self.reporting_system.generate_accurate_report()
        
        # Overall success rate should be 3/5 = 0.6
        assert report['overall_statistics']['prompt_success_rate'] == 0.6
        
        # Check individual prompt stats
        generate_quotes_stats = report['prompt_details']['generate_quotes']
        assert generate_quotes_stats['success_rate'] == 2/3  # 2 success out of 3
        
        verify_quotes_stats = report['prompt_details']['verify_quotes']
        assert verify_quotes_stats['success_rate'] == 0.5  # 1 success out of 2
    
    def test_validate_reporting_accuracy(self):
        """Test reporting accuracy validation"""
        # Set up test data
        self.reporting_system.track_quote_retrieval("book_1", 90, 90)
        self.reporting_system.track_prompt_execution("test_prompt", True, {})
        self.reporting_system.track_prompt_execution("test_prompt", True, {})
        
        # Test validation with correct expectations
        expected_results = {
            'expected_quotes_retrieved': 90,
            'expected_prompt_success_rate': 1.0,
            'expected_books_processed': 1
        }
        
        assert self.reporting_system.validate_reporting_accuracy(expected_results) is True
        
        # Test validation with incorrect expectations
        wrong_expectations = {
            'expected_quotes_retrieved': 100,  # Wrong count
            'expected_prompt_success_rate': 0.5  # Wrong rate
        }
        
        assert self.reporting_system.validate_reporting_accuracy(wrong_expectations) is False
    
    def test_get_prompt_statistics(self):
        """Test detailed prompt statistics retrieval"""
        # Track some executions for a specific prompt
        self.reporting_system.track_prompt_execution(
            "test_prompt", True, {"execution_time": 1.0}
        )
        self.reporting_system.track_prompt_execution(
            "test_prompt", False, {"execution_time": 0.5, "error_message": "failed"}
        )
        
        stats = self.reporting_system.get_prompt_statistics("test_prompt")
        
        assert stats['prompt_name'] == "test_prompt"
        assert stats['total_executions'] == 2
        assert stats['successful'] == 1
        assert stats['failed'] == 1
        assert stats['success_rate'] == 0.5
        assert stats['average_execution_time'] == 0.75
        assert len(stats['recent_executions']) == 2
    
    def test_error_handling(self):
        """Test error handling in reporting system"""
        # Test with invalid data
        self.reporting_system.track_prompt_execution(None, True, {})
        self.reporting_system.track_quote_retrieval("", 0, 0)
        
        # Should not crash and should generate report
        report = self.reporting_system.generate_accurate_report()
        assert 'overall_statistics' in report
    
    def test_export_statistics(self):
        """Test statistics export functionality"""
        # Add some test data
        self.reporting_system.track_prompt_execution("test", True, {})
        self.reporting_system.track_quote_retrieval("book_1", 50, 50)
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            success = self.reporting_system.export_statistics(temp_path)
            assert success is True
            assert os.path.exists(temp_path)
            
            # Verify file content
            import json
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert 'overall_statistics' in data
            assert data['overall_statistics']['total_quotes_retrieved'] == 50
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_session_statistics(self):
        """Test session statistics retrieval"""
        # Add some data
        self.reporting_system.track_prompt_execution("test", True, {})
        self.reporting_system.track_quote_retrieval("book_1", 50, 50, retrieval_time=1.5)
        
        # Get session stats
        stats = self.reporting_system.get_session_statistics()
        
        assert stats['total_prompts_executed'] == 1
        assert stats['total_quotes_retrieved'] == 50
        assert stats['books_processed'] == 1
    
    def test_reset_statistics(self):
        """Test statistics reset functionality"""
        # Add some data
        self.reporting_system.track_prompt_execution("test", True, {})
        self.reporting_system.track_quote_retrieval("book_1", 50, 50)
        
        # Reset
        self.reporting_system.reset_statistics()
        
        # Should be empty
        report = self.reporting_system.generate_accurate_report()
        overall_stats = report['overall_statistics']
        
        assert overall_stats['total_prompts_executed'] == 0
        assert overall_stats['total_quotes_retrieved'] == 0
        assert overall_stats['books_processed'] == 0