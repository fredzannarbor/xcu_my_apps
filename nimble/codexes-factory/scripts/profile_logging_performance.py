#!/usr/bin/env python3
"""
Performance profiling script for logging improvements.

This script profiles the performance impact of logging components
and provides detailed performance metrics and optimization recommendations.
"""

import time
import logging
import cProfile
import pstats
import io
import statistics
from typing import List, Dict, Any, Tuple
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor
import threading
import gc
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.logging_filters import LiteLLMFilter
from codexes.core.token_usage_tracker import TokenUsageTracker
from codexes.core.statistics_reporter import StatisticsReporter
from codexes.core.logging_config import LoggingConfigManager


class LoggingPerformanceProfiler:
    """Profiles logging performance and provides optimization recommendations."""
    
    def __init__(self):
        """Initialize the profiler."""
        self.results = {}
        self.recommendations = []
    
    def profile_filter_performance(self, num_messages: int = 10000) -> Dict[str, Any]:
        """Profile LiteLLM filter performance."""
        print(f"\n🔍 Profiling LiteLLM Filter Performance ({num_messages:,} messages)")
        print("=" * 60)
        
        filter_obj = LiteLLMFilter(debug_mode=False)
        
        # Create test messages
        test_messages = [
            ('litellm.main', logging.INFO, 'Cost calculation for request {}'),
            ('litellm.completion', logging.DEBUG, 'Completion wrapper processing {}'),
            ('litellm.utils', logging.INFO, 'Token counting for request {}'),
            ('litellm.main', logging.WARNING, 'Rate limit warning for request {}'),
            ('litellm.main', logging.ERROR, 'Authentication failed for request {}'),
            ('other.logger', logging.INFO, 'Non-LiteLLM message {}'),
        ]
        
        # Generate test records
        records = []
        for i in range(num_messages):
            logger_name, level, msg_template = test_messages[i % len(test_messages)]
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
            records.append(record)
        
        # Profile filtering
        start_time = time.perf_counter()
        filtered_count = 0
        
        for record in records:
            if filter_obj.filter(record):
                filtered_count += 1
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Calculate metrics
        messages_per_second = num_messages / total_time if total_time > 0 else 0
        microseconds_per_message = (total_time * 1_000_000) / num_messages
        filter_efficiency = (num_messages - filtered_count) / num_messages * 100
        
        results = {
            'total_messages': num_messages,
            'total_time_seconds': total_time,
            'messages_per_second': messages_per_second,
            'microseconds_per_message': microseconds_per_message,
            'filtered_count': filtered_count,
            'passed_count': num_messages - filtered_count,
            'filter_efficiency_percent': filter_efficiency
        }
        
        print(f"📊 Filter Performance Results:")
        print(f"   • Total Time: {total_time:.6f} seconds")
        print(f"   • Messages/Second: {messages_per_second:,.0f}")
        print(f"   • μs/Message: {microseconds_per_message:.2f}")
        print(f"   • Messages Filtered: {num_messages - filtered_count:,} ({filter_efficiency:.1f}%)")
        print(f"   • Messages Passed: {filtered_count:,}")
        
        # Performance recommendations
        if microseconds_per_message > 10:
            self.recommendations.append(
                f"⚠️  Filter performance: {microseconds_per_message:.2f}μs/message is high. "
                "Consider optimizing pattern matching."
            )
        elif microseconds_per_message < 1:
            print(f"✅ Excellent filter performance: {microseconds_per_message:.2f}μs/message")
        
        self.results['filter_performance'] = results
        return results
    
    def profile_token_tracking_performance(self, num_calls: int = 5000) -> Dict[str, Any]:
        """Profile token tracking performance."""
        print(f"\n📈 Profiling Token Tracking Performance ({num_calls:,} calls)")
        print("=" * 60)
        
        tracker = TokenUsageTracker()
        
        # Create mock response
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        models = ['gpt-3.5-turbo', 'gpt-4', 'claude-3-sonnet', 'llama-2-70b']
        prompts = ['completion', 'analysis', 'generation', 'validation', 'summarization']
        
        # Profile tracking
        start_time = time.perf_counter()
        
        with patch('litellm.completion_cost', return_value=0.001):
            for i in range(num_calls):
                tracker.record_usage(
                    model=models[i % len(models)],
                    prompt_name=prompts[i % len(prompts)],
                    response=mock_response,
                    response_time=0.5 + (i % 10) * 0.1
                )
        
        end_time = time.perf_counter()
        tracking_time = end_time - start_time
        
        # Profile statistics retrieval
        stats_start = time.perf_counter()
        total_stats = tracker.get_total_statistics()
        model_breakdown = tracker.get_model_breakdown()
        prompt_breakdown = tracker.get_prompt_breakdown()
        stats_end = time.perf_counter()
        stats_time = stats_end - stats_start
        
        # Calculate metrics
        calls_per_second = num_calls / tracking_time if tracking_time > 0 else 0
        microseconds_per_call = (tracking_time * 1_000_000) / num_calls
        
        results = {
            'total_calls': num_calls,
            'tracking_time_seconds': tracking_time,
            'stats_retrieval_time_seconds': stats_time,
            'calls_per_second': calls_per_second,
            'microseconds_per_call': microseconds_per_call,
            'total_tokens_tracked': total_stats['total_tokens'],
            'models_tracked': len(model_breakdown),
            'prompts_tracked': len(prompt_breakdown)
        }
        
        print(f"📊 Token Tracking Results:")
        print(f"   • Tracking Time: {tracking_time:.6f} seconds")
        print(f"   • Calls/Second: {calls_per_second:,.0f}")
        print(f"   • μs/Call: {microseconds_per_call:.2f}")
        print(f"   • Stats Retrieval: {stats_time:.6f} seconds")
        print(f"   • Total Tokens: {total_stats['total_tokens']:,}")
        print(f"   • Models Tracked: {len(model_breakdown)}")
        print(f"   • Prompts Tracked: {len(prompt_breakdown)}")
        
        # Performance recommendations
        if microseconds_per_call > 100:
            self.recommendations.append(
                f"⚠️  Token tracking: {microseconds_per_call:.2f}μs/call is high. "
                "Consider optimizing data structures."
            )
        elif microseconds_per_call < 20:
            print(f"✅ Excellent tracking performance: {microseconds_per_call:.2f}μs/call")
        
        self.results['token_tracking'] = results
        return results
    
    def profile_statistics_reporting_performance(self, num_records: int = 2000) -> Dict[str, Any]:
        """Profile statistics reporting performance."""
        print(f"\n📋 Profiling Statistics Reporting Performance ({num_records:,} records)")
        print("=" * 60)
        
        # Set up tracker with data
        tracker = TokenUsageTracker()
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        models = [f'model_{i}' for i in range(10)]
        prompts = [f'prompt_{i}' for i in range(20)]
        
        # Populate with test data
        with patch('litellm.completion_cost', return_value=0.001):
            for i in range(num_records):
                tracker.record_usage(
                    model=models[i % len(models)],
                    prompt_name=prompts[i % len(prompts)],
                    response=mock_response,
                    response_time=0.5
                )
        
        # Profile different reporting levels
        reporter = StatisticsReporter()
        reporting_times = {}
        
        detail_levels = ['minimal', 'summary', 'standard', 'detailed']
        
        for level in detail_levels:
            reporter.config['detail_level'] = level
            
            start_time = time.perf_counter()
            
            # Capture output to prevent console spam
            with patch('logging.Logger.info'):
                reporter.report_pipeline_statistics(tracker)
            
            end_time = time.perf_counter()
            reporting_times[level] = end_time - start_time
        
        # Calculate metrics
        avg_reporting_time = statistics.mean(reporting_times.values())
        
        results = {
            'num_records': num_records,
            'reporting_times': reporting_times,
            'average_reporting_time': avg_reporting_time,
            'models_in_data': len(models),
            'prompts_in_data': len(prompts)
        }
        
        print(f"📊 Statistics Reporting Results:")
        for level, time_taken in reporting_times.items():
            print(f"   • {level.capitalize()} Report: {time_taken:.6f} seconds")
        print(f"   • Average Time: {avg_reporting_time:.6f} seconds")
        
        # Performance recommendations
        if avg_reporting_time > 0.1:
            self.recommendations.append(
                f"⚠️  Statistics reporting: {avg_reporting_time:.6f}s average is high. "
                "Consider reducing detail level for large datasets."
            )
        elif avg_reporting_time < 0.01:
            print(f"✅ Excellent reporting performance: {avg_reporting_time:.6f}s average")
        
        self.results['statistics_reporting'] = results
        return results
    
    def profile_concurrent_performance(self, num_threads: int = 10, calls_per_thread: int = 100) -> Dict[str, Any]:
        """Profile performance under concurrent load."""
        print(f"\n🔄 Profiling Concurrent Performance ({num_threads} threads, {calls_per_thread} calls each)")
        print("=" * 60)
        
        tracker = TokenUsageTracker()
        filter_obj = LiteLLMFilter(debug_mode=False)
        
        # Mock response
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        def worker_function(thread_id: int) -> Dict[str, Any]:
            """Worker function for each thread."""
            thread_results = {
                'thread_id': thread_id,
                'tracking_time': 0,
                'filtering_time': 0,
                'calls_completed': 0
            }
            
            # Token tracking
            tracking_start = time.perf_counter()
            with patch('litellm.completion_cost', return_value=0.001):
                for i in range(calls_per_thread):
                    tracker.record_usage(
                        model=f'model_{thread_id}',
                        prompt_name=f'prompt_{i % 5}',
                        response=mock_response,
                        response_time=0.5
                    )
            tracking_end = time.perf_counter()
            thread_results['tracking_time'] = tracking_end - tracking_start
            
            # Filter testing
            filtering_start = time.perf_counter()
            for i in range(calls_per_thread):
                record = logging.LogRecord(
                    name='litellm.main',
                    level=logging.INFO,
                    pathname='test.py',
                    lineno=1,
                    msg=f'Cost calculation for thread {thread_id} call {i}',
                    args=(),
                    exc_info=None
                )
                filter_obj.filter(record)
            filtering_end = time.perf_counter()
            thread_results['filtering_time'] = filtering_end - filtering_start
            thread_results['calls_completed'] = calls_per_thread
            
            return thread_results
        
        # Run concurrent test
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for thread_id in range(num_threads):
                future = executor.submit(worker_function, thread_id)
                futures.append(future)
            
            thread_results = []
            for future in futures:
                thread_results.append(future.result())
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Calculate metrics
        total_calls = num_threads * calls_per_thread
        calls_per_second = total_calls / total_time if total_time > 0 else 0
        
        tracking_times = [r['tracking_time'] for r in thread_results]
        filtering_times = [r['filtering_time'] for r in thread_results]
        
        results = {
            'num_threads': num_threads,
            'calls_per_thread': calls_per_thread,
            'total_calls': total_calls,
            'total_time_seconds': total_time,
            'calls_per_second': calls_per_second,
            'avg_tracking_time_per_thread': statistics.mean(tracking_times),
            'avg_filtering_time_per_thread': statistics.mean(filtering_times),
            'max_tracking_time': max(tracking_times),
            'max_filtering_time': max(filtering_times),
            'thread_results': thread_results
        }
        
        print(f"📊 Concurrent Performance Results:")
        print(f"   • Total Time: {total_time:.6f} seconds")
        print(f"   • Total Calls: {total_calls:,}")
        print(f"   • Calls/Second: {calls_per_second:,.0f}")
        print(f"   • Avg Tracking Time/Thread: {statistics.mean(tracking_times):.6f}s")
        print(f"   • Avg Filtering Time/Thread: {statistics.mean(filtering_times):.6f}s")
        print(f"   • Max Tracking Time: {max(tracking_times):.6f}s")
        print(f"   • Max Filtering Time: {max(filtering_times):.6f}s")
        
        # Check for thread contention
        tracking_variance = statistics.variance(tracking_times) if len(tracking_times) > 1 else 0
        if tracking_variance > 0.001:  # High variance indicates contention
            self.recommendations.append(
                f"⚠️  High variance in thread performance ({tracking_variance:.6f}). "
                "Consider thread-local optimizations."
            )
        
        self.results['concurrent_performance'] = results
        return results
    
    def profile_memory_usage(self, num_operations: int = 1000) -> Dict[str, Any]:
        """Profile memory usage of logging components."""
        print(f"\n💾 Profiling Memory Usage ({num_operations:,} operations)")
        print("=" * 60)
        
        import tracemalloc
        
        # Start memory tracing
        tracemalloc.start()
        
        # Get initial memory snapshot
        initial_snapshot = tracemalloc.take_snapshot()
        
        # Create components and perform operations
        components = []
        
        for i in range(num_operations // 100):  # Create 10 components for 1000 operations
            # Create filter
            filter_obj = LiteLLMFilter(debug_mode=False)
            
            # Create tracker
            tracker = TokenUsageTracker()
            
            # Add some data to tracker
            mock_response = Mock()
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            mock_response.usage.total_tokens = 150
            
            with patch('litellm.completion_cost', return_value=0.001):
                for j in range(100):  # 100 operations per component
                    tracker.record_usage(
                        model=f'model_{i}',
                        prompt_name=f'prompt_{j % 10}',
                        response=mock_response
                    )
            
            components.append((filter_obj, tracker))
        
        # Take snapshot after operations
        after_operations_snapshot = tracemalloc.take_snapshot()
        
        # Clean up components
        for filter_obj, tracker in components:
            tracker.reset()
        components.clear()
        
        # Force garbage collection
        gc.collect()
        
        # Take final snapshot
        final_snapshot = tracemalloc.take_snapshot()
        
        # Calculate memory usage
        initial_memory = sum(stat.size for stat in initial_snapshot.statistics('filename'))
        after_operations_memory = sum(stat.size for stat in after_operations_snapshot.statistics('filename'))
        final_memory = sum(stat.size for stat in final_snapshot.statistics('filename'))
        
        memory_growth = after_operations_memory - initial_memory
        memory_cleanup = after_operations_memory - final_memory
        cleanup_ratio = memory_cleanup / memory_growth if memory_growth > 0 else 1.0
        
        # Stop tracing
        tracemalloc.stop()
        
        results = {
            'num_operations': num_operations,
            'initial_memory_bytes': initial_memory,
            'after_operations_memory_bytes': after_operations_memory,
            'final_memory_bytes': final_memory,
            'memory_growth_bytes': memory_growth,
            'memory_cleanup_bytes': memory_cleanup,
            'cleanup_ratio': cleanup_ratio,
            'memory_per_operation_bytes': memory_growth / num_operations if num_operations > 0 else 0
        }
        
        print(f"📊 Memory Usage Results:")
        print(f"   • Initial Memory: {initial_memory / 1024:.1f} KB")
        print(f"   • After Operations: {after_operations_memory / 1024:.1f} KB")
        print(f"   • Final Memory: {final_memory / 1024:.1f} KB")
        print(f"   • Memory Growth: {memory_growth / 1024:.1f} KB")
        print(f"   • Memory Cleanup: {memory_cleanup / 1024:.1f} KB ({cleanup_ratio:.1%})")
        print(f"   • Memory/Operation: {memory_growth / num_operations:.1f} bytes")
        
        # Memory recommendations
        if cleanup_ratio < 0.8:
            self.recommendations.append(
                f"⚠️  Memory cleanup ratio is low ({cleanup_ratio:.1%}). "
                "Check for memory leaks in logging components."
            )
        elif cleanup_ratio > 0.95:
            print(f"✅ Excellent memory cleanup: {cleanup_ratio:.1%}")
        
        self.results['memory_usage'] = results
        return results
    
    def profile_with_cprofile(self, test_function, *args, **kwargs) -> pstats.Stats:
        """Profile a function using cProfile."""
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = test_function(*args, **kwargs)
        
        profiler.disable()
        
        # Create stats object
        stats_stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stats_stream)
        stats.sort_stats('cumulative')
        
        return stats, result
    
    def run_comprehensive_profile(self) -> Dict[str, Any]:
        """Run comprehensive performance profiling."""
        print("🚀 Starting Comprehensive Logging Performance Profile")
        print("=" * 80)
        
        # Profile each component
        self.profile_filter_performance(10000)
        self.profile_token_tracking_performance(5000)
        self.profile_statistics_reporting_performance(2000)
        self.profile_concurrent_performance(10, 100)
        self.profile_memory_usage(1000)
        
        # Generate summary
        self.generate_performance_summary()
        
        return self.results
    
    def generate_performance_summary(self):
        """Generate performance summary and recommendations."""
        print("\n📋 Performance Summary")
        print("=" * 80)
        
        # Overall performance assessment
        filter_perf = self.results.get('filter_performance', {})
        tracking_perf = self.results.get('token_tracking', {})
        reporting_perf = self.results.get('statistics_reporting', {})
        concurrent_perf = self.results.get('concurrent_performance', {})
        memory_perf = self.results.get('memory_usage', {})
        
        print("🎯 Key Performance Metrics:")
        if filter_perf:
            print(f"   • Filter: {filter_perf.get('messages_per_second', 0):,.0f} messages/sec")
        if tracking_perf:
            print(f"   • Tracking: {tracking_perf.get('calls_per_second', 0):,.0f} calls/sec")
        if reporting_perf:
            print(f"   • Reporting: {reporting_perf.get('average_reporting_time', 0):.6f} sec avg")
        if concurrent_perf:
            print(f"   • Concurrent: {concurrent_perf.get('calls_per_second', 0):,.0f} calls/sec")
        if memory_perf:
            print(f"   • Memory: {memory_perf.get('cleanup_ratio', 0):.1%} cleanup ratio")
        
        # Performance recommendations
        print("\n💡 Performance Recommendations:")
        if self.recommendations:
            for i, rec in enumerate(self.recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print("   ✅ All performance metrics are within acceptable ranges!")
        
        # Optimization suggestions
        print("\n🔧 Optimization Suggestions:")
        
        # Filter optimizations
        if filter_perf.get('microseconds_per_message', 0) > 5:
            print("   • Consider using compiled regex patterns for filter matching")
            print("   • Implement pattern caching for frequently used filters")
        
        # Tracking optimizations
        if tracking_perf.get('microseconds_per_call', 0) > 50:
            print("   • Consider using more efficient data structures for statistics")
            print("   • Implement lazy evaluation for expensive calculations")
        
        # Memory optimizations
        if memory_perf.get('cleanup_ratio', 1.0) < 0.9:
            print("   • Review object lifecycle management")
            print("   • Consider implementing object pooling for frequently created objects")
        
        # Concurrent optimizations
        if concurrent_perf.get('calls_per_second', 0) < 1000:
            print("   • Consider thread-local storage for performance-critical data")
            print("   • Review locking mechanisms for potential contention")
        
        print("\n✅ Performance profiling complete!")


def main():
    """Main function to run performance profiling."""
    profiler = LoggingPerformanceProfiler()
    
    try:
        results = profiler.run_comprehensive_profile()
        
        # Save results to file
        import json
        with open('logs/performance_profile_results.json', 'w') as f:
            # Convert any non-serializable objects to strings
            serializable_results = {}
            for key, value in results.items():
                if isinstance(value, dict):
                    serializable_results[key] = {
                        k: str(v) if not isinstance(v, (int, float, str, bool, list, dict, type(None))) else v
                        for k, v in value.items()
                    }
                else:
                    serializable_results[key] = str(value)
            
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n📁 Results saved to: logs/performance_profile_results.json")
        
    except Exception as e:
        print(f"❌ Error during profiling: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())