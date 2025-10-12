"""
Performance optimization and validation tests for logging improvements.

This module tests:
- Logging performance impact on LLM operations
- Token tracking overhead optimization
- Filter validation for critical error messages
- High-volume logging scenarios
"""

import pytest
import logging
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor
import statistics
from typing import List, Dict, Any

from src.codexes.core.logging_filters import LiteLLMFilter
from src.codexes.core.token_usage_tracker import TokenUsageTracker
from src.codexes.core.statistics_reporter import StatisticsReporter
from src.codexes.core.logging_config import LoggingConfigManager


class TestLoggingPerformanceOptimization:
    """Test suite for logging performance optimization and validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.filter = LiteLLMFilter(debug_mode=False)
        self.tracker = TokenUsageTracker()
        self.reporter = StatisticsReporter()
        self.logging_manager = LoggingConfigManager()
        
        # Create test logger
        self.test_logger = logging.getLogger('test_performance')
        self.test_logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.test_logger.handlers.clear()
        
        # Add a null handler to prevent output during tests
        null_handler = logging.NullHandler()
        self.test_logger.addHandler(null_handler)
    
    def teardown_method(self):
        """Clean up after tests."""
        self.test_logger.handlers.clear()
        self.tracker.reset()
    
    def test_filter_performance_impact(self):
        """Test that LiteLLM filter has minimal performance impact."""
        # Create test log records
        test_records = []
        for i in range(1000):
            record = logging.LogRecord(
                name='litellm.main',
                level=logging.INFO,
                pathname='test.py',
                lineno=1,
                msg=f'Test message {i} with cost calculation details',
                args=(),
                exc_info=None
            )
            test_records.append(record)
        
        # Measure filtering performance
        start_time = time.perf_counter()
        filtered_count = 0
        for record in test_records:
            if self.filter.filter(record):
                filtered_count += 1
        end_time = time.perf_counter()
        
        filter_time = end_time - start_time
        
        # Performance should be under 1ms for 1000 records
        assert filter_time < 0.001, f"Filter performance too slow: {filter_time:.6f}s for 1000 records"
        
        # Most records should be filtered out (since they contain "cost calculation")
        assert filtered_count < 100, f"Filter not working effectively: {filtered_count} records passed"
    
    def test_filter_performance_with_critical_messages(self):
        """Test filter performance with mix of critical and non-critical messages."""
        # Create mix of critical and non-critical messages
        test_records = []
        
        # Add non-critical messages (should be filtered)
        for i in range(800):
            record = logging.LogRecord(
                name='litellm.main',
                level=logging.INFO,
                pathname='test.py',
                lineno=1,
                msg=f'Cost calculation for request {i}',
                args=(),
                exc_info=None
            )
            test_records.append(record)
        
        # Add critical messages (should pass through)
        critical_messages = [
            'Authentication failed for API key',
            'Rate limit exceeded, retrying',
            'Connection timeout occurred',
            'Internal server error from provider',
            'Quota exceeded for model'
        ]
        
        for i, msg in enumerate(critical_messages * 40):  # 200 critical messages
            record = logging.LogRecord(
                name='litellm.main',
                level=logging.WARNING,
                pathname='test.py',
                lineno=1,
                msg=msg,
                args=(),
                exc_info=None
            )
            test_records.append(record)
        
        # Measure performance
        start_time = time.perf_counter()
        passed_count = 0
        for record in test_records:
            if self.filter.filter(record):
                passed_count += 1
        end_time = time.perf_counter()
        
        filter_time = end_time - start_time
        
        # Performance should still be fast
        assert filter_time < 0.002, f"Filter performance degraded with critical messages: {filter_time:.6f}s"
        
        # All critical messages should pass through
        assert passed_count >= 200, f"Critical messages not passing through: {passed_count} < 200"
    
    def test_token_tracking_overhead(self):
        """Test that token tracking has minimal overhead."""
        # Mock LiteLLM response
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        # Measure tracking overhead
        start_time = time.perf_counter()
        
        for i in range(1000):
            with patch('litellm.completion_cost', return_value=0.001):
                self.tracker.record_usage(
                    model='gpt-3.5-turbo',
                    prompt_name=f'test_prompt_{i % 10}',
                    response=mock_response,
                    response_time=0.5
                )
        
        end_time = time.perf_counter()
        tracking_time = end_time - start_time
        
        # Tracking 1000 calls should be under 100ms
        assert tracking_time < 0.1, f"Token tracking too slow: {tracking_time:.6f}s for 1000 calls"
        
        # Verify data was recorded correctly
        stats = self.tracker.get_total_statistics()
        assert stats['total_calls'] == 1000
        assert stats['total_tokens'] == 150000
    
    def test_statistics_reporting_performance(self):
        """Test that statistics reporting is efficient."""
        # Populate tracker with test data
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        # Add diverse data
        models = ['gpt-3.5-turbo', 'gpt-4', 'claude-3-sonnet']
        prompts = ['completion', 'analysis', 'generation', 'validation']
        
        with patch('litellm.completion_cost', return_value=0.001):
            for i in range(500):
                self.tracker.record_usage(
                    model=models[i % len(models)],
                    prompt_name=prompts[i % len(prompts)],
                    response=mock_response,
                    response_time=0.5 + (i % 10) * 0.1
                )
        
        # Measure reporting performance
        start_time = time.perf_counter()
        
        # Capture log output to prevent console spam
        with patch('logging.Logger.info'):
            self.reporter.report_pipeline_statistics(self.tracker)
        
        end_time = time.perf_counter()
        reporting_time = end_time - start_time
        
        # Reporting should be under 50ms for 500 records
        assert reporting_time < 0.05, f"Statistics reporting too slow: {reporting_time:.6f}s"
    
    def test_concurrent_token_tracking(self):
        """Test token tracking performance under concurrent access."""
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        def track_usage(thread_id: int, iterations: int):
            """Function to run in each thread."""
            with patch('litellm.completion_cost', return_value=0.001):
                for i in range(iterations):
                    self.tracker.record_usage(
                        model=f'model_{thread_id}',
                        prompt_name=f'prompt_{i % 5}',
                        response=mock_response,
                        response_time=0.5
                    )
        
        # Run concurrent tracking
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for thread_id in range(10):
                future = executor.submit(track_usage, thread_id, 100)
                futures.append(future)
            
            # Wait for all threads to complete
            for future in futures:
                future.result()
        
        end_time = time.perf_counter()
        concurrent_time = end_time - start_time
        
        # Concurrent tracking should complete in reasonable time
        assert concurrent_time < 1.0, f"Concurrent tracking too slow: {concurrent_time:.6f}s"
        
        # Verify all data was recorded
        stats = self.tracker.get_total_statistics()
        assert stats['total_calls'] == 1000
        assert stats['total_tokens'] == 150000
    
    def test_filter_critical_message_validation(self):
        """Validate that filter never blocks critical error messages."""
        critical_test_cases = [
            # Error messages
            ('litellm.main', logging.ERROR, 'API authentication failed'),
            ('litellm.completion', logging.ERROR, 'Request failed with 500 error'),
            ('litellm.router', logging.ERROR, 'Connection timeout occurred'),
            
            # Critical warnings
            ('litellm.main', logging.WARNING, 'Rate limit exceeded'),
            ('litellm.main', logging.WARNING, 'Quota exceeded for model'),
            ('litellm.main', logging.WARNING, 'Service unavailable'),
            
            # Critical info messages (should pass due to critical patterns)
            ('litellm.main', logging.INFO, 'Authentication error detected'),
            ('litellm.main', logging.INFO, 'Request failed due to timeout'),
            ('litellm.main', logging.INFO, 'Service returned internal server error'),
        ]
        
        for logger_name, level, message in critical_test_cases:
            record = logging.LogRecord(
                name=logger_name,
                level=level,
                pathname='test.py',
                lineno=1,
                msg=message,
                args=(),
                exc_info=None
            )
            
            # Critical messages should ALWAYS pass through
            assert self.filter.filter(record), f"Critical message blocked: {message}"
    
    def test_filter_non_critical_message_filtering(self):
        """Validate that filter blocks non-critical verbose messages."""
        non_critical_test_cases = [
            ('litellm.main', logging.INFO, 'Cost calculation completed'),
            ('litellm.utils', logging.INFO, 'Token counting in progress'),
            ('litellm.completion', logging.DEBUG, 'Completion wrapper initialized'),
            ('litellm.main', logging.INFO, 'Making request to OpenAI'),
            ('litellm.main', logging.INFO, 'Received response from provider'),
            ('litellm.router', logging.INFO, 'Model mapping configured'),
            ('litellm.main', logging.DEBUG, 'Processing request headers'),
        ]
        
        for logger_name, level, message in non_critical_test_cases:
            record = logging.LogRecord(
                name=logger_name,
                level=level,
                pathname='test.py',
                lineno=1,
                msg=message,
                args=(),
                exc_info=None
            )
            
            # Non-critical messages should be filtered out
            assert not self.filter.filter(record), f"Non-critical message not filtered: {message}"
    
    def test_high_volume_logging_scenario(self):
        """Test logging behavior under high-volume scenarios."""
        # Simulate high-volume logging scenario
        num_messages = 10000
        message_types = [
            ('litellm.main', logging.INFO, 'Cost calculation for request {}'),
            ('litellm.completion', logging.DEBUG, 'Completion wrapper processing {}'),
            ('litellm.utils', logging.INFO, 'Token counting for request {}'),
            ('litellm.main', logging.WARNING, 'Rate limit warning for request {}'),
            ('litellm.main', logging.ERROR, 'Authentication failed for request {}'),
        ]
        
        # Measure performance under high volume
        start_time = time.perf_counter()
        
        filtered_count = 0
        error_count = 0
        
        for i in range(num_messages):
            logger_name, level, msg_template = message_types[i % len(message_types)]
            message = msg_template.format(i)
            
            record = logging.LogRecord(
                name=logger_name,
                level=level,
                pathname='test.py',
                lineno=1,
                msg=message,
                args=(),
                exc_info=None
            )
            
            if self.filter.filter(record):
                filtered_count += 1
                if level >= logging.ERROR:
                    error_count += 1
        
        end_time = time.perf_counter()
        processing_time = end_time - start_time
        
        # High-volume processing should complete in reasonable time
        assert processing_time < 0.5, f"High-volume processing too slow: {processing_time:.6f}s for {num_messages} messages"
        
        # All error messages should pass through
        expected_errors = num_messages // len(message_types)  # One error type per cycle
        assert error_count == expected_errors, f"Not all error messages passed: {error_count} != {expected_errors}"
        
        # Most messages should be filtered (only warnings and errors should pass)
        expected_passed = (num_messages // len(message_types)) * 2  # Warnings and errors
        assert abs(filtered_count - expected_passed) <= 1, f"Unexpected filter behavior: {filtered_count} != {expected_passed}"
    
    def test_memory_usage_optimization(self):
        """Test that logging components don't accumulate excessive memory."""
        import gc
        import sys
        
        # Get initial memory usage
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Create and use many logging components
        filters = []
        trackers = []
        
        for i in range(100):
            # Create filter
            filter_obj = LiteLLMFilter(debug_mode=False)
            filters.append(filter_obj)
            
            # Create tracker and add some data
            tracker = TokenUsageTracker()
            mock_response = Mock()
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5
            mock_response.usage.total_tokens = 15
            
            with patch('litellm.completion_cost', return_value=0.0001):
                for j in range(10):
                    tracker.record_usage(
                        model='test-model',
                        prompt_name=f'prompt_{j}',
                        response=mock_response
                    )
            
            trackers.append(tracker)
        
        # Check memory usage after creation
        gc.collect()
        after_creation_objects = len(gc.get_objects())
        
        # Clean up
        filters.clear()
        for tracker in trackers:
            tracker.reset()
        trackers.clear()
        
        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory should not grow excessively
        memory_growth = after_creation_objects - initial_objects
        memory_cleanup = after_creation_objects - final_objects
        
        # Memory growth should be reasonable (less than 10000 objects for 100 components)
        assert memory_growth < 10000, f"Excessive memory growth: {memory_growth} objects"
        
        # Most memory should be cleaned up (at least 80%)
        cleanup_ratio = memory_cleanup / memory_growth if memory_growth > 0 else 1.0
        assert cleanup_ratio > 0.8, f"Poor memory cleanup: {cleanup_ratio:.2f} ratio"
    
    def test_logging_configuration_performance(self):
        """Test that logging configuration setup is efficient."""
        # Measure configuration setup time
        start_time = time.perf_counter()
        
        # Create and configure multiple logging managers
        managers = []
        for i in range(10):
            manager = LoggingConfigManager()
            manager.setup_logging()
            managers.append(manager)
        
        end_time = time.perf_counter()
        config_time = end_time - start_time
        
        # Configuration should be fast (under 100ms for 10 managers)
        assert config_time < 0.1, f"Logging configuration too slow: {config_time:.6f}s for 10 managers"
        
        # Clean up
        for manager in managers:
            manager.reset_configuration()
    
    def test_filter_pattern_matching_optimization(self):
        """Test that filter pattern matching is optimized."""
        # Test with many patterns
        filter_obj = LiteLLMFilter(debug_mode=False)
        
        # Add many custom patterns
        for i in range(100):
            filter_obj.add_filtered_pattern(f'custom_pattern_{i}')
        
        # Test performance with many patterns
        test_messages = [
            'This is a normal message',
            'Cost calculation in progress',
            'custom_pattern_50 detected',
            'Authentication failed',
            'Token counting completed'
        ]
        
        start_time = time.perf_counter()
        
        for _ in range(1000):
            for msg in test_messages:
                record = logging.LogRecord(
                    name='litellm.main',
                    level=logging.INFO,
                    pathname='test.py',
                    lineno=1,
                    msg=msg,
                    args=(),
                    exc_info=None
                )
                filter_obj.filter(record)
        
        end_time = time.perf_counter()
        pattern_time = end_time - start_time
        
        # Pattern matching should remain fast even with many patterns
        assert pattern_time < 0.1, f"Pattern matching too slow with many patterns: {pattern_time:.6f}s"
    
    def test_statistics_aggregation_efficiency(self):
        """Test that statistics aggregation is efficient with large datasets."""
        # Create tracker with large amount of data
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        models = [f'model_{i}' for i in range(20)]
        prompts = [f'prompt_{i}' for i in range(50)]
        
        # Add large dataset
        start_time = time.perf_counter()
        
        with patch('litellm.completion_cost', return_value=0.001):
            for i in range(5000):
                self.tracker.record_usage(
                    model=models[i % len(models)],
                    prompt_name=prompts[i % len(prompts)],
                    response=mock_response,
                    response_time=0.5
                )
        
        end_time = time.perf_counter()
        aggregation_time = end_time - start_time
        
        # Aggregation should be efficient
        assert aggregation_time < 1.0, f"Statistics aggregation too slow: {aggregation_time:.6f}s for 5000 records"
        
        # Test retrieval performance
        start_time = time.perf_counter()
        
        total_stats = self.tracker.get_total_statistics()
        model_breakdown = self.tracker.get_model_breakdown()
        prompt_breakdown = self.tracker.get_prompt_breakdown()
        
        end_time = time.perf_counter()
        retrieval_time = end_time - start_time
        
        # Retrieval should be fast
        assert retrieval_time < 0.01, f"Statistics retrieval too slow: {retrieval_time:.6f}s"
        
        # Verify data integrity
        assert total_stats['total_calls'] == 5000
        assert len(model_breakdown) == 20
        assert len(prompt_breakdown) == 50


class TestLoggingValidation:
    """Additional validation tests for logging behavior."""
    
    def test_debug_mode_override_validation(self):
        """Test that debug mode override works correctly."""
        # Test with debug mode disabled
        filter_normal = LiteLLMFilter(debug_mode=False)
        
        record = logging.LogRecord(
            name='litellm.main',
            level=logging.DEBUG,
            pathname='test.py',
            lineno=1,
            msg='Cost calculation debug info',
            args=(),
            exc_info=None
        )
        
        # Should be filtered in normal mode
        assert not filter_normal.filter(record)
        
        # Test with debug mode enabled
        filter_debug = LiteLLMFilter(debug_mode=True)
        
        # Should pass through in debug mode
        assert filter_debug.filter(record)
    
    def test_environment_variable_debug_mode(self):
        """Test that debug mode respects environment variables."""
        import os
        
        # Test with environment variable set
        with patch.dict(os.environ, {'LITELLM_DEBUG': 'true'}):
            filter_obj = LiteLLMFilter()
            assert filter_obj.debug_mode
        
        # Test with environment variable unset
        with patch.dict(os.environ, {}, clear=True):
            filter_obj = LiteLLMFilter()
            assert not filter_obj.debug_mode
    
    def test_cost_calculation_error_handling(self):
        """Test that cost calculation errors are handled gracefully."""
        tracker = TokenUsageTracker()
        
        # Mock response with usage data
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        # Test with cost calculation error
        with patch('litellm.completion_cost', side_effect=Exception('Cost calculation failed')):
            # Should not raise exception
            tracker.record_usage(
                model='test-model',
                prompt_name='test-prompt',
                response=mock_response
            )
        
        # Verify data was still recorded
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 1
        assert stats['total_tokens'] == 150
        assert stats['total_cost'] is None  # Cost should be None due to error
    
    def test_malformed_response_handling(self):
        """Test handling of malformed LLM responses."""
        tracker = TokenUsageTracker()
        
        # Test with response missing usage data
        mock_response_no_usage = Mock()
        mock_response_no_usage.usage = None
        
        tracker.record_usage(
            model='test-model',
            prompt_name='test-prompt',
            response=mock_response_no_usage
        )
        
        # Should handle gracefully
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 0  # No valid data recorded
        
        # Test with completely invalid response
        invalid_response = "not a response object"
        
        tracker.record_usage(
            model='test-model',
            prompt_name='test-prompt',
            response=invalid_response
        )
        
        # Should still handle gracefully
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])