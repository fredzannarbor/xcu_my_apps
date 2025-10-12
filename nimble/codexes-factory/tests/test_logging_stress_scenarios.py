"""
Stress testing for logging improvements under high-volume scenarios.

This module tests logging behavior under extreme conditions to validate
performance and reliability under stress.
"""

import pytest
import logging
import time
import threading
import queue
import random
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
from typing import List, Dict, Any
import gc
import os
import tempfile

from src.codexes.core.logging_filters import LiteLLMFilter
from src.codexes.core.token_usage_tracker import TokenUsageTracker
from src.codexes.core.statistics_reporter import StatisticsReporter
from src.codexes.core.logging_config import LoggingConfigManager


class TestLoggingStressScenarios:
    """Stress tests for logging components under high-volume scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.filter = LiteLLMFilter(debug_mode=False)
        self.tracker = TokenUsageTracker()
        self.reporter = StatisticsReporter()
        
        # Create temporary log file for stress tests
        self.temp_log_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
        self.temp_log_file.close()
        
        # Set up stress test logger
        self.stress_logger = logging.getLogger('stress_test')
        self.stress_logger.setLevel(logging.DEBUG)
        self.stress_logger.handlers.clear()
        
        # Add file handler for stress testing
        file_handler = logging.FileHandler(self.temp_log_file.name)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.stress_logger.addHandler(file_handler)
    
    def teardown_method(self):
        """Clean up after tests."""
        self.stress_logger.handlers.clear()
        self.tracker.reset()
        
        # Clean up temporary file
        try:
            os.unlink(self.temp_log_file.name)
        except OSError:
            pass
    
    def test_extreme_high_volume_filtering(self):
        """Test filter performance with extremely high message volume."""
        num_messages = 100000
        print(f"\n🔥 Stress testing filter with {num_messages:,} messages")
        
        # Generate diverse message patterns
        message_patterns = [
            ('litellm.main', logging.INFO, 'Cost calculation for request {}'),
            ('litellm.completion', logging.DEBUG, 'Completion wrapper processing {}'),
            ('litellm.utils', logging.INFO, 'Token counting for request {}'),
            ('litellm.router', logging.INFO, 'Model mapping configured for {}'),
            ('litellm.main', logging.WARNING, 'Rate limit warning for request {}'),
            ('litellm.main', logging.ERROR, 'Authentication failed for request {}'),
            ('litellm.proxy', logging.INFO, 'Proxy request handling {}'),
            ('other.logger', logging.INFO, 'Non-LiteLLM message {}'),
        ]
        
        # Create test records
        records = []
        for i in range(num_messages):
            pattern = message_patterns[i % len(message_patterns)]
            logger_name, level, msg_template = pattern
            message = msg_template.format(i)
            
            record = logging.LogRecord(
                name=logger_name,
                level=level,
                pathname='stress_test.py',
                lineno=i % 1000 + 1,
                msg=message,
                args=(),
                exc_info=None
            )
            records.append(record)
        
        # Stress test filtering
        start_time = time.perf_counter()
        passed_count = 0
        error_count = 0
        
        for record in records:
            try:
                if self.filter.filter(record):
                    passed_count += 1
                    if record.levelno >= logging.ERROR:
                        error_count += 1
            except Exception as e:
                pytest.fail(f"Filter failed on record {record}: {e}")
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Validate performance
        messages_per_second = num_messages / total_time
        assert messages_per_second > 50000, f"Filter too slow: {messages_per_second:,.0f} msg/sec"
        
        # Validate filtering behavior
        expected_errors = num_messages // len(message_patterns)  # One error pattern per cycle
        assert error_count == expected_errors, f"Error messages not preserved: {error_count} != {expected_errors}"
        
        print(f"✅ Filtered {num_messages:,} messages in {total_time:.3f}s ({messages_per_second:,.0f} msg/sec)")
        print(f"   Passed: {passed_count:,}, Errors preserved: {error_count:,}")
    
    def test_concurrent_high_volume_tracking(self):
        """Test token tracking under concurrent high-volume load."""
        num_threads = 20
        calls_per_thread = 1000
        total_calls = num_threads * calls_per_thread
        
        print(f"\n🔥 Stress testing tracking with {num_threads} threads, {calls_per_thread:,} calls each")
        
        # Mock response with varying token counts
        def create_mock_response(call_id: int):
            mock_response = Mock()
            mock_response.usage = Mock()
            # Vary token counts to simulate real usage
            base_tokens = 50 + (call_id % 200)
            mock_response.usage.prompt_tokens = base_tokens
            mock_response.usage.completion_tokens = base_tokens // 2
            mock_response.usage.total_tokens = base_tokens + base_tokens // 2
            return mock_response
        
        models = [f'model_{i}' for i in range(10)]
        prompts = [f'prompt_{i}' for i in range(25)]
        
        def stress_worker(thread_id: int) -> Dict[str, Any]:
            """Worker function for stress testing."""
            thread_start = time.perf_counter()
            successful_calls = 0
            failed_calls = 0
            
            for call_id in range(calls_per_thread):
                try:
                    mock_response = create_mock_response(call_id)
                    
                    with patch('litellm.completion_cost', return_value=random.uniform(0.0001, 0.01)):
                        self.tracker.record_usage(
                            model=models[(thread_id + call_id) % len(models)],
                            prompt_name=prompts[(thread_id * 2 + call_id) % len(prompts)],
                            response=mock_response,
                            response_time=random.uniform(0.1, 2.0)
                        )
                    successful_calls += 1
                    
                except Exception as e:
                    failed_calls += 1
                    print(f"Thread {thread_id} call {call_id} failed: {e}")
            
            thread_end = time.perf_counter()
            return {
                'thread_id': thread_id,
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'thread_time': thread_end - thread_start
            }
        
        # Run stress test
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(stress_worker, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Analyze results
        total_successful = sum(r['successful_calls'] for r in results)
        total_failed = sum(r['failed_calls'] for r in results)
        max_thread_time = max(r['thread_time'] for r in results)
        min_thread_time = min(r['thread_time'] for r in results)
        
        # Validate performance
        calls_per_second = total_successful / total_time
        assert calls_per_second > 1000, f"Concurrent tracking too slow: {calls_per_second:,.0f} calls/sec"
        
        # Validate data integrity
        stats = self.tracker.get_total_statistics()
        assert stats['total_calls'] == total_successful, f"Call count mismatch: {stats['total_calls']} != {total_successful}"
        assert total_failed == 0, f"Some calls failed: {total_failed}"
        
        # Check for thread contention (variance in thread completion times)
        time_variance = max_thread_time - min_thread_time
        assert time_variance < total_time * 0.5, f"High thread contention detected: {time_variance:.3f}s variance"
        
        print(f"✅ Processed {total_successful:,} calls in {total_time:.3f}s ({calls_per_second:,.0f} calls/sec)")
        print(f"   Thread time variance: {time_variance:.3f}s")
        print(f"   Models tracked: {len(self.tracker.get_model_breakdown())}")
        print(f"   Prompts tracked: {len(self.tracker.get_prompt_breakdown())}")
    
    def test_memory_stress_under_load(self):
        """Test memory behavior under sustained high load."""
        print("\n🔥 Stress testing memory usage under sustained load")
        
        import tracemalloc
        tracemalloc.start()
        
        # Create multiple trackers to simulate real-world usage
        trackers = []
        filters = []
        
        # Phase 1: Create many components
        initial_snapshot = tracemalloc.take_snapshot()
        
        for i in range(50):  # 50 concurrent "pipelines"
            tracker = TokenUsageTracker()
            filter_obj = LiteLLMFilter(debug_mode=False)
            
            trackers.append(tracker)
            filters.append(filter_obj)
        
        creation_snapshot = tracemalloc.take_snapshot()
        
        # Phase 2: Heavy usage
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        models = [f'model_{i}' for i in range(5)]
        prompts = [f'prompt_{i}' for i in range(10)]
        
        # Simulate sustained usage
        for cycle in range(10):  # 10 cycles of heavy usage
            for i, tracker in enumerate(trackers):
                with patch('litellm.completion_cost', return_value=0.001):
                    for j in range(100):  # 100 calls per tracker per cycle
                        tracker.record_usage(
                            model=models[j % len(models)],
                            prompt_name=prompts[j % len(prompts)],
                            response=mock_response,
                            response_time=0.5
                        )
            
            # Periodic cleanup simulation
            if cycle % 3 == 0:
                gc.collect()
        
        usage_snapshot = tracemalloc.take_snapshot()
        
        # Phase 3: Cleanup
        for tracker in trackers:
            tracker.reset()
        
        trackers.clear()
        filters.clear()
        gc.collect()
        
        cleanup_snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        # Analyze memory usage
        initial_memory = sum(stat.size for stat in initial_snapshot.statistics('filename'))
        creation_memory = sum(stat.size for stat in creation_snapshot.statistics('filename'))
        usage_memory = sum(stat.size for stat in usage_snapshot.statistics('filename'))
        cleanup_memory = sum(stat.size for stat in cleanup_snapshot.statistics('filename'))
        
        creation_growth = creation_memory - initial_memory
        usage_growth = usage_memory - creation_memory
        cleanup_ratio = (usage_memory - cleanup_memory) / usage_memory if usage_memory > 0 else 1.0
        
        # Validate memory behavior
        assert cleanup_ratio > 0.7, f"Poor memory cleanup: {cleanup_ratio:.1%}"
        
        # Memory growth should be reasonable
        total_operations = 50 * 10 * 100  # trackers * cycles * calls
        memory_per_operation = usage_growth / total_operations
        assert memory_per_operation < 1000, f"Excessive memory per operation: {memory_per_operation:.1f} bytes"
        
        print(f"✅ Memory stress test completed:")
        print(f"   Initial: {initial_memory / 1024:.1f} KB")
        print(f"   After creation: {creation_memory / 1024:.1f} KB (+{creation_growth / 1024:.1f} KB)")
        print(f"   After usage: {usage_memory / 1024:.1f} KB (+{usage_growth / 1024:.1f} KB)")
        print(f"   After cleanup: {cleanup_memory / 1024:.1f} KB")
        print(f"   Cleanup ratio: {cleanup_ratio:.1%}")
        print(f"   Memory/operation: {memory_per_operation:.1f} bytes")
    
    def test_logging_system_integration_stress(self):
        """Test complete logging system under integrated stress."""
        print("\n🔥 Stress testing complete logging system integration")
        
        # Set up complete logging system
        logging_manager = LoggingConfigManager()
        
        # Create temporary config for stress testing
        stress_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'simple': {'format': '%(levelname)s - %(message)s'}
            },
            'handlers': {
                'file': {
                    'class': 'logging.FileHandler',
                    'level': 'DEBUG',
                    'formatter': 'simple',
                    'filename': self.temp_log_file.name,
                    'mode': 'a'
                }
            },
            'loggers': {
                'stress_test': {
                    'level': 'DEBUG',
                    'handlers': ['file'],
                    'propagate': False
                },
                'litellm': {
                    'level': 'INFO',
                    'handlers': ['file'],
                    'propagate': False
                }
            }
        }
        
        logging_manager.setup_logging(stress_config)
        logging_manager.apply_litellm_filter()
        
        # Stress test parameters
        num_threads = 15
        messages_per_thread = 2000
        total_messages = num_threads * messages_per_thread
        
        # Message templates for stress testing
        message_templates = [
            ('stress_test', logging.INFO, 'Processing request {} in thread {}'),
            ('litellm.main', logging.INFO, 'Cost calculation for request {} thread {}'),
            ('litellm.completion', logging.DEBUG, 'Completion wrapper {} thread {}'),
            ('stress_test', logging.WARNING, 'Warning for request {} thread {}'),
            ('litellm.main', logging.ERROR, 'Error in request {} thread {}'),
            ('stress_test', logging.ERROR, 'Critical error {} thread {}'),
        ]
        
        def stress_logging_worker(thread_id: int) -> Dict[str, Any]:
            """Worker that generates high-volume log messages."""
            thread_start = time.perf_counter()
            messages_logged = 0
            errors_encountered = 0
            
            for msg_id in range(messages_per_thread):
                try:
                    template = message_templates[msg_id % len(message_templates)]
                    logger_name, level, msg_format = template
                    
                    logger = logging.getLogger(logger_name)
                    message = msg_format.format(msg_id, thread_id)
                    logger.log(level, message)
                    
                    messages_logged += 1
                    
                    # Simulate some processing time
                    if msg_id % 100 == 0:
                        time.sleep(0.001)  # 1ms pause every 100 messages
                        
                except Exception as e:
                    errors_encountered += 1
                    print(f"Logging error in thread {thread_id}: {e}")
            
            thread_end = time.perf_counter()
            return {
                'thread_id': thread_id,
                'messages_logged': messages_logged,
                'errors_encountered': errors_encountered,
                'thread_time': thread_end - thread_start
            }
        
        # Run integrated stress test
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(stress_logging_worker, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Analyze results
        total_logged = sum(r['messages_logged'] for r in results)
        total_errors = sum(r['errors_encountered'] for r in results)
        
        # Validate performance
        messages_per_second = total_logged / total_time
        assert messages_per_second > 5000, f"Integrated logging too slow: {messages_per_second:,.0f} msg/sec"
        assert total_errors == 0, f"Logging errors occurred: {total_errors}"
        
        # Validate log file integrity
        with open(self.temp_log_file.name, 'r') as f:
            log_lines = f.readlines()
        
        # Should have some log lines (filtering will reduce the count)
        assert len(log_lines) > 0, "No log messages written to file"
        
        # Check that critical messages are preserved
        error_lines = [line for line in log_lines if 'ERROR' in line]
        expected_errors = total_messages // len(message_templates) * 2  # Two error templates
        
        # Allow some variance due to filtering and threading
        assert len(error_lines) >= expected_errors * 0.8, f"Too many error messages filtered: {len(error_lines)} < {expected_errors * 0.8}"
        
        print(f"✅ Integrated stress test completed:")
        print(f"   Messages logged: {total_logged:,} in {total_time:.3f}s ({messages_per_second:,.0f} msg/sec)")
        print(f"   Log file lines: {len(log_lines):,}")
        print(f"   Error lines preserved: {len(error_lines):,}")
        print(f"   No logging errors: {total_errors == 0}")
    
    def test_burst_load_handling(self):
        """Test handling of sudden burst loads."""
        print("\n🔥 Stress testing burst load handling")
        
        # Simulate burst scenario: quiet period followed by sudden high load
        quiet_period_calls = 100
        burst_period_calls = 10000
        
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        # Phase 1: Quiet period
        quiet_start = time.perf_counter()
        
        with patch('litellm.completion_cost', return_value=0.001):
            for i in range(quiet_period_calls):
                self.tracker.record_usage(
                    model='quiet-model',
                    prompt_name='quiet-prompt',
                    response=mock_response,
                    response_time=0.5
                )
                time.sleep(0.01)  # Simulate normal pacing
        
        quiet_end = time.perf_counter()
        quiet_time = quiet_end - quiet_start
        
        # Phase 2: Sudden burst
        burst_start = time.perf_counter()
        
        with patch('litellm.completion_cost', return_value=0.001):
            for i in range(burst_period_calls):
                self.tracker.record_usage(
                    model=f'burst-model-{i % 5}',
                    prompt_name=f'burst-prompt-{i % 10}',
                    response=mock_response,
                    response_time=0.1  # Faster responses during burst
                )
        
        burst_end = time.perf_counter()
        burst_time = burst_end - burst_start
        
        # Validate burst handling
        quiet_rate = quiet_period_calls / quiet_time
        burst_rate = burst_period_calls / burst_time
        
        # Burst should be handled efficiently
        assert burst_rate > quiet_rate * 10, f"Burst not handled efficiently: {burst_rate:.0f} vs {quiet_rate:.0f}"
        assert burst_rate > 1000, f"Burst rate too low: {burst_rate:.0f} calls/sec"
        
        # Validate data integrity after burst
        stats = self.tracker.get_total_statistics()
        expected_total = quiet_period_calls + burst_period_calls
        assert stats['total_calls'] == expected_total, f"Call count mismatch after burst: {stats['total_calls']} != {expected_total}"
        
        print(f"✅ Burst load test completed:")
        print(f"   Quiet period: {quiet_period_calls} calls in {quiet_time:.3f}s ({quiet_rate:.0f} calls/sec)")
        print(f"   Burst period: {burst_period_calls} calls in {burst_time:.3f}s ({burst_rate:.0f} calls/sec)")
        print(f"   Burst efficiency: {burst_rate / quiet_rate:.1f}x faster")
    
    def test_resource_exhaustion_resilience(self):
        """Test resilience under resource exhaustion conditions."""
        print("\n🔥 Testing resilience under resource exhaustion")
        
        # Simulate resource exhaustion by creating many objects
        trackers = []
        filters = []
        
        try:
            # Create many components to stress memory
            for i in range(1000):
                tracker = TokenUsageTracker()
                filter_obj = LiteLLMFilter(debug_mode=False)
                
                # Add some data to each tracker
                mock_response = Mock()
                mock_response.usage = Mock()
                mock_response.usage.prompt_tokens = 50
                mock_response.usage.completion_tokens = 25
                mock_response.usage.total_tokens = 75
                
                with patch('litellm.completion_cost', return_value=0.0005):
                    for j in range(10):
                        tracker.record_usage(
                            model=f'model_{i % 10}',
                            prompt_name=f'prompt_{j}',
                            response=mock_response
                        )
                
                trackers.append(tracker)
                filters.append(filter_obj)
                
                # Test that components still work under stress
                if i % 100 == 0:
                    # Test filter functionality
                    record = logging.LogRecord(
                        name='litellm.main',
                        level=logging.INFO,
                        pathname='test.py',
                        lineno=1,
                        msg=f'Cost calculation {i}',
                        args=(),
                        exc_info=None
                    )
                    
                    # Should still filter correctly
                    assert not filter_obj.filter(record), f"Filter failed under stress at iteration {i}"
                    
                    # Test tracker functionality
                    stats = tracker.get_total_statistics()
                    assert stats['total_calls'] == 10, f"Tracker failed under stress at iteration {i}"
            
            print(f"✅ Created {len(trackers)} components under resource stress")
            
            # Test that all components are still functional
            functional_trackers = 0
            functional_filters = 0
            
            for i, (tracker, filter_obj) in enumerate(zip(trackers[:100], filters[:100])):  # Test first 100
                try:
                    # Test tracker
                    stats = tracker.get_total_statistics()
                    if stats['total_calls'] == 10:
                        functional_trackers += 1
                    
                    # Test filter
                    record = logging.LogRecord(
                        name='litellm.main',
                        level=logging.INFO,
                        pathname='test.py',
                        lineno=1,
                        msg='Test message',
                        args=(),
                        exc_info=None
                    )
                    if not filter_obj.filter(record):
                        functional_filters += 1
                        
                except Exception as e:
                    print(f"Component {i} failed: {e}")
            
            # Most components should still be functional
            assert functional_trackers >= 95, f"Too many trackers failed: {functional_trackers}/100"
            assert functional_filters >= 95, f"Too many filters failed: {functional_filters}/100"
            
            print(f"✅ Functional components: {functional_trackers}/100 trackers, {functional_filters}/100 filters")
            
        finally:
            # Cleanup
            for tracker in trackers:
                try:
                    tracker.reset()
                except:
                    pass
            trackers.clear()
            filters.clear()
            gc.collect()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])