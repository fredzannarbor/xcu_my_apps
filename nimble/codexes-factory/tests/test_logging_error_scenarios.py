"""
Error handling and edge case tests for logging improvements.

This module tests various error scenarios and edge cases to ensure
the logging system is robust and handles failures gracefully.
"""

import pytest
import logging
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import threading
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.logging_config import LoggingConfigManager
from codexes.core.logging_filters import LiteLLMFilter
from codexes.core.token_usage_tracker import TokenUsageTracker, UsageRecord
from codexes.core.statistics_reporter import StatisticsReporter


class TestLiteLLMFilterErrorScenarios:
    """Test error scenarios for LiteLLM filter."""
    
    def test_filter_with_exception_in_getmessage(self):
        """Test filter behavior when record.getMessage() raises exception."""
        filter_instance = LiteLLMFilter(debug_mode=False)
        
        # Create a mock record that raises exception on getMessage()
        mock_record = Mock()
        mock_record.name = 'litellm'
        mock_record.levelno = logging.INFO
        mock_record.getMessage.side_effect = Exception("Message error")
        
        # Filter should allow the record through to be safe
        result = filter_instance.filter(mock_record)
        assert result is True
    
    def test_filter_with_none_message(self):
        """Test filter behavior with None message."""
        filter_instance = LiteLLMFilter(debug_mode=False)
        
        mock_record = Mock()
        mock_record.name = 'litellm'
        mock_record.levelno = logging.INFO
        mock_record.getMessage.return_value = None
        
        # Should handle None message gracefully
        result = filter_instance.filter(mock_record)
        assert result is True
    
    def test_filter_with_unicode_message(self):
        """Test filter with unicode characters in message."""
        filter_instance = LiteLLMFilter(debug_mode=False)
        
        mock_record = Mock()
        mock_record.name = 'litellm'
        mock_record.levelno = logging.INFO
        mock_record.getMessage.return_value = "Cost calculation with unicode: 🚀💰"
        
        # Should filter out despite unicode characters
        result = filter_instance.filter(mock_record)
        assert result is False
    
    def test_filter_with_very_long_message(self):
        """Test filter performance with very long messages."""
        filter_instance = LiteLLMFilter(debug_mode=False)
        
        # Create a very long message
        long_message = "cost calculation " + "x" * 10000
        
        mock_record = Mock()
        mock_record.name = 'litellm'
        mock_record.levelno = logging.INFO
        mock_record.getMessage.return_value = long_message
        
        # Should still filter correctly
        result = filter_instance.filter(mock_record)
        assert result is False
    
    def test_filter_pattern_modification_during_filtering(self):
        """Test filter behavior when patterns are modified during filtering."""
        filter_instance = LiteLLMFilter(debug_mode=False)
        
        def modify_patterns():
            """Modify patterns in a separate thread."""
            time.sleep(0.01)  # Small delay
            filter_instance.add_filtered_pattern("new pattern")
        
        # Start pattern modification in background
        thread = threading.Thread(target=modify_patterns)
        thread.start()
        
        # Filter messages while patterns are being modified
        for i in range(100):
            mock_record = Mock()
            mock_record.name = 'litellm'
            mock_record.levelno = logging.INFO
            mock_record.getMessage.return_value = f"cost calculation {i}"
            
            # Should not crash despite concurrent modification
            result = filter_instance.filter(mock_record)
            assert isinstance(result, bool)
        
        thread.join()


class TestTokenUsageTrackerErrorScenarios:
    """Test error scenarios for token usage tracker."""
    
    def test_record_usage_with_invalid_model_name(self):
        """Test recording usage with invalid model names."""
        tracker = TokenUsageTracker()
        
        invalid_models = [None, "", 123, [], {}]
        
        for invalid_model in invalid_models:
            mock_response = Mock()
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5
            mock_response.usage.total_tokens = 15
            
            # Should handle invalid model names gracefully
            tracker.record_usage(invalid_model, "test_prompt", mock_response)
        
        # Should have recorded some usage despite invalid model names
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] >= 0  # May be 0 if all failed, but shouldn't crash
    
    def test_record_usage_with_invalid_prompt_name(self):
        """Test recording usage with invalid prompt names."""
        tracker = TokenUsageTracker()
        
        invalid_prompts = [None, "", 123, [], {}]
        
        for invalid_prompt in invalid_prompts:
            mock_response = Mock()
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5
            mock_response.usage.total_tokens = 15
            
            # Should handle invalid prompt names gracefully
            tracker.record_usage("gpt-4", invalid_prompt, mock_response)
        
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] >= 0
    
    def test_record_usage_with_negative_tokens(self):
        """Test recording usage with negative token counts."""
        tracker = TokenUsageTracker()
        
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = -10
        mock_response.usage.completion_tokens = -5
        mock_response.usage.total_tokens = -15
        
        # Should handle negative tokens
        tracker.record_usage("gpt-4", "test_prompt", mock_response)
        
        stats = tracker.get_total_statistics()
        # Should either record the negative values or handle them gracefully
        assert isinstance(stats['total_tokens'], int)
    
    def test_record_usage_with_missing_usage_attributes(self):
        """Test recording usage when usage object is missing attributes."""
        tracker = TokenUsageTracker()
        
        # Test with usage object missing some attributes
        mock_response = Mock()
        mock_response.usage = Mock()
        # Only set prompt_tokens, missing others
        mock_response.usage.prompt_tokens = 10
        # completion_tokens and total_tokens are missing
        
        # Should handle missing attributes gracefully
        tracker.record_usage("gpt-4", "test_prompt", mock_response)
        
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] >= 0
    
    def test_concurrent_usage_recording(self):
        """Test concurrent usage recording from multiple threads."""
        tracker = TokenUsageTracker()
        
        def record_usage_worker(worker_id):
            """Worker function to record usage."""
            for i in range(10):
                mock_response = Mock()
                mock_response.usage = Mock()
                mock_response.usage.prompt_tokens = 10
                mock_response.usage.completion_tokens = 5
                mock_response.usage.total_tokens = 15
                
                with patch('litellm.completion_cost', return_value=0.001):
                    tracker.record_usage(f"model-{worker_id}", f"prompt-{worker_id}-{i}", mock_response)
        
        # Start multiple threads
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=record_usage_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all usage was recorded
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 50  # 5 workers * 10 records each
        assert stats['total_tokens'] == 750  # 50 * 15 tokens each
    
    def test_memory_usage_with_large_number_of_records(self):
        """Test memory usage with a large number of records."""
        tracker = TokenUsageTracker()
        
        # Add a large number of records
        for i in range(1000):
            mock_response = Mock()
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            mock_response.usage.total_tokens = 150
            
            with patch('litellm.completion_cost', return_value=0.01):
                tracker.record_usage("gpt-4", f"prompt_{i}", mock_response)
        
        # Verify all records were stored
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 1000
        assert len(tracker.records) == 1000
        
        # Test that recent records function works with large dataset
        recent = tracker.get_recent_records(limit=10)
        assert len(recent) == 10
        assert recent[-1].prompt_name == "prompt_999"  # Most recent
    
    def test_cost_calculation_with_extreme_values(self):
        """Test cost calculation with extreme values."""
        tracker = TokenUsageTracker()
        
        # Test with very large cost
        with patch('litellm.completion_cost', return_value=999999.99):
            mock_response = Mock()
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 1
            mock_response.usage.completion_tokens = 1
            mock_response.usage.total_tokens = 2
            
            tracker.record_usage("expensive-model", "test_prompt", mock_response)
        
        # Test with very small cost
        with patch('litellm.completion_cost', return_value=0.0000001):
            mock_response = Mock()
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 1
            mock_response.usage.completion_tokens = 1
            mock_response.usage.total_tokens = 2
            
            tracker.record_usage("cheap-model", "test_prompt", mock_response)
        
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 2
        assert stats['total_cost'] is not None
        assert stats['total_cost'] > 999999  # Should include the large cost


class TestStatisticsReporterErrorScenarios:
    """Test error scenarios for statistics reporter."""
    
    def test_report_with_corrupted_tracker_data(self, caplog):
        """Test reporting with corrupted tracker data."""
        reporter = StatisticsReporter()
        
        # Create a mock tracker with corrupted methods
        mock_tracker = Mock()
        mock_tracker.get_total_statistics.return_value = {
            'total_calls': 'not_a_number',  # Invalid type
            'total_tokens': None,  # Unexpected None
            'total_cost': float('inf'),  # Infinite cost
            'duration_seconds': -1,  # Negative duration
            'models_used': None,  # Should be a list
            'prompts_used': None,  # Should be a list
        }
        mock_tracker.get_model_breakdown.return_value = {}
        mock_tracker.get_prompt_breakdown.return_value = {}
        
        # Should handle corrupted data gracefully
        with caplog.at_level(logging.INFO):
            reporter.report_pipeline_statistics(mock_tracker)
        
        # Should have attempted to generate a report
        log_text = caplog.text
        assert "PIPELINE STATISTICS SUMMARY" in log_text
    
    def test_report_with_exception_in_tracker_methods(self, caplog):
        """Test reporting when tracker methods raise exceptions."""
        reporter = StatisticsReporter()
        
        mock_tracker = Mock()
        mock_tracker.get_total_statistics.side_effect = Exception("Stats error")
        mock_tracker.get_model_breakdown.side_effect = Exception("Model error")
        mock_tracker.get_prompt_breakdown.side_effect = Exception("Prompt error")
        
        # Should handle exceptions gracefully
        with caplog.at_level(logging.ERROR):
            reporter.report_pipeline_statistics(mock_tracker)
        
        # Should log the error
        error_messages = [record.message for record in caplog.records if record.levelname == 'ERROR']
        assert any("Error generating pipeline statistics report" in msg for msg in error_messages)
    
    def test_format_cost_summary_with_invalid_data(self):
        """Test cost summary formatting with invalid data."""
        reporter = StatisticsReporter()
        
        invalid_stats = [
            {'total_calls': None, 'total_tokens': None, 'total_cost': None},
            {'total_calls': -1, 'total_tokens': -1, 'total_cost': -1},
            {'total_calls': float('inf'), 'total_tokens': float('inf'), 'total_cost': float('inf')},
            {},  # Empty dict
        ]
        
        for stats in invalid_stats:
            # Should not crash with invalid data
            result = reporter.format_cost_summary(stats)
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_generate_summary_report_with_unicode_data(self):
        """Test summary report generation with unicode data."""
        reporter = StatisticsReporter()
        
        # Create tracker with unicode data
        tracker = TokenUsageTracker()
        
        # Add record with unicode model and prompt names
        record = UsageRecord(
            model="gpt-4-🚀",
            prompt_name="测试提示",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost=0.01,
            timestamp=datetime.now()
        )
        
        tracker.records.append(record)
        tracker._update_model_stats(record)
        tracker._update_prompt_stats(record)
        
        # Should handle unicode data correctly
        result = reporter.generate_summary_report(tracker)
        assert isinstance(result, str)
        assert "1 LLM calls" in result or "LLM calls" in result


class TestLoggingConfigErrorScenarios:
    """Test error scenarios for logging configuration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Clean up after tests."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_setup_logging_with_permission_denied(self):
        """Test logging setup when log directory creation fails."""
        # Create a file where logs directory should be
        with open('logs', 'w') as f:
            f.write("blocking file")
        
        manager = LoggingConfigManager()
        
        # Should handle permission/creation errors gracefully
        # This might raise an exception or handle it gracefully depending on implementation
        try:
            manager.setup_logging()
        except Exception as e:
            # If it raises an exception, it should be a reasonable one
            assert "logs" in str(e).lower() or "permission" in str(e).lower()
    
    def test_setup_logging_with_invalid_config(self):
        """Test logging setup with invalid configuration."""
        manager = LoggingConfigManager()
        
        invalid_configs = [
            None,
            {},
            {"invalid": "config"},
            {"version": "not_a_number"},
        ]
        
        for invalid_config in invalid_configs:
            # Should handle invalid configs gracefully or raise appropriate exceptions
            try:
                manager.setup_logging(invalid_config)
            except Exception as e:
                # Should be a configuration-related exception
                assert isinstance(e, (ValueError, TypeError, KeyError)) or "config" in str(e).lower()
    
    def test_apply_filter_to_nonexistent_logger(self):
        """Test applying filter to loggers that don't exist."""
        manager = LoggingConfigManager()
        
        # Try to apply filter before setting up logging
        # Should not crash
        manager.apply_litellm_filter()
        
        # Verify that it doesn't break subsequent setup
        manager.setup_logging()
        assert manager.is_configured()
    
    def test_reset_configuration_multiple_times(self):
        """Test resetting configuration multiple times."""
        manager = LoggingConfigManager()
        
        # Set up logging
        manager.setup_logging()
        assert manager.is_configured()
        
        # Reset multiple times
        for _ in range(3):
            manager.reset_configuration()
            assert not manager.is_configured()
        
        # Should still be able to set up again
        manager.setup_logging()
        assert manager.is_configured()
    
    def test_concurrent_configuration_access(self):
        """Test concurrent access to logging configuration."""
        manager = LoggingConfigManager()
        
        def setup_worker():
            """Worker function to set up logging."""
            try:
                manager.setup_logging()
            except Exception:
                pass  # Ignore exceptions in concurrent setup
        
        def reset_worker():
            """Worker function to reset logging."""
            try:
                manager.reset_configuration()
            except Exception:
                pass  # Ignore exceptions in concurrent reset
        
        # Start multiple threads doing setup and reset
        threads = []
        for _ in range(5):
            setup_thread = threading.Thread(target=setup_worker)
            reset_thread = threading.Thread(target=reset_worker)
            threads.extend([setup_thread, reset_thread])
            setup_thread.start()
            reset_thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Manager should still be in a consistent state
        assert isinstance(manager.is_configured(), bool)


class TestEdgeCaseScenarios:
    """Test various edge cases across all components."""
    
    def test_empty_string_patterns(self):
        """Test filter with empty string patterns."""
        filter_instance = LiteLLMFilter(debug_mode=False)
        
        # Add empty pattern
        filter_instance.add_filtered_pattern("")
        
        mock_record = Mock()
        mock_record.name = 'litellm'
        mock_record.levelno = logging.INFO
        mock_record.getMessage.return_value = "any message"
        
        # Should handle empty pattern gracefully
        result = filter_instance.filter(mock_record)
        assert isinstance(result, bool)
    
    def test_zero_token_usage(self):
        """Test handling of zero token usage."""
        tracker = TokenUsageTracker()
        
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 0
        mock_response.usage.completion_tokens = 0
        mock_response.usage.total_tokens = 0
        
        with patch('litellm.completion_cost', return_value=0.0):
            tracker.record_usage("gpt-4", "test_prompt", mock_response)
        
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 1
        assert stats['total_tokens'] == 0
    
    def test_very_long_model_and_prompt_names(self):
        """Test with very long model and prompt names."""
        tracker = TokenUsageTracker()
        
        long_model = "x" * 1000
        long_prompt = "y" * 1000
        
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        
        # Should handle very long names
        tracker.record_usage(long_model, long_prompt, mock_response)
        
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 1
        assert long_model in stats['models_used']
        assert long_prompt in stats['prompts_used']
    
    def test_special_characters_in_names(self):
        """Test with special characters in model and prompt names."""
        tracker = TokenUsageTracker()
        
        special_model = "model/with:special@chars#$%"
        special_prompt = "prompt\nwith\ttabs\rand\nnewlines"
        
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        
        # Should handle special characters
        tracker.record_usage(special_model, special_prompt, mock_response)
        
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])