#!/usr/bin/env python3
"""
Logging performance optimization script.

This script implements performance optimizations for the logging system
based on profiling results and performance analysis.
"""

import sys
import os
import time
import logging
from typing import Dict, Any, List, Set
import re
from functools import lru_cache
import threading
from collections import defaultdict

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.logging_filters import LiteLLMFilter
from codexes.core.token_usage_tracker import TokenUsageTracker
from codexes.core.statistics_reporter import StatisticsReporter


class OptimizedLiteLLMFilter(LiteLLMFilter):
    """
    Optimized version of LiteLLM filter with performance improvements.
    
    Optimizations:
    - Compiled regex patterns for faster matching
    - Pattern caching for frequently used patterns
    - Early exit conditions
    - Reduced string operations
    """
    
    def __init__(self, debug_mode: bool = None):
        """Initialize the optimized filter."""
        super().__init__(debug_mode)
        
        # Compile regex patterns for faster matching
        self._compiled_patterns = self._compile_patterns()
        self._compiled_critical_patterns = self._compile_critical_patterns()
        
        # Cache for pattern matching results
        self._pattern_cache = {}
        self._cache_lock = threading.RLock()
        self._cache_max_size = 1000
        
        # Performance counters
        self._filter_calls = 0
        self._cache_hits = 0
        self._cache_misses = 0
    
    def _compile_patterns(self) -> List[re.Pattern]:
        """Compile filtered patterns into regex objects for faster matching."""
        compiled = []
        for pattern in self.filtered_patterns:
            try:
                # Create case-insensitive regex pattern
                regex_pattern = re.compile(re.escape(pattern), re.IGNORECASE)
                compiled.append(regex_pattern)
            except re.error:
                # If regex compilation fails, fall back to string matching
                pass
        return compiled
    
    def _compile_critical_patterns(self) -> List[re.Pattern]:
        """Compile critical patterns into regex objects for faster matching."""
        compiled = []
        for pattern in self.critical_patterns:
            try:
                # Create case-insensitive regex pattern
                regex_pattern = re.compile(re.escape(pattern), re.IGNORECASE)
                compiled.append(regex_pattern)
            except re.error:
                # If regex compilation fails, fall back to string matching
                pass
        return compiled
    
    @lru_cache(maxsize=256)
    def _is_litellm_logger_cached(self, logger_name: str) -> bool:
        """Cached version of LiteLLM logger check."""
        return super()._is_litellm_logger(logger_name)
    
    def _get_cached_pattern_result(self, message: str) -> tuple:
        """Get cached pattern matching result."""
        with self._cache_lock:
            if message in self._pattern_cache:
                self._cache_hits += 1
                return self._pattern_cache[message]
            
            self._cache_misses += 1
            
            # Check if cache is too large
            if len(self._pattern_cache) >= self._cache_max_size:
                # Remove oldest entries (simple FIFO)
                keys_to_remove = list(self._pattern_cache.keys())[:self._cache_max_size // 4]
                for key in keys_to_remove:
                    del self._pattern_cache[key]
            
            return None
    
    def _cache_pattern_result(self, message: str, has_filtered: bool, has_critical: bool):
        """Cache pattern matching result."""
        with self._cache_lock:
            self._pattern_cache[message] = (has_filtered, has_critical)
    
    def _contains_filtered_pattern_optimized(self, message: str) -> bool:
        """Optimized version of filtered pattern checking."""
        # Check cache first
        cached_result = self._get_cached_pattern_result(message)
        if cached_result is not None:
            return cached_result[0]
        
        # Use compiled regex patterns for faster matching
        for pattern in self._compiled_patterns:
            if pattern.search(message):
                self._cache_pattern_result(message, True, False)
                return True
        
        # Fallback to original string-based matching for non-compiled patterns
        for pattern in self.filtered_patterns:
            if pattern in message:
                self._cache_pattern_result(message, True, False)
                return True
        
        self._cache_pattern_result(message, False, False)
        return False
    
    def _contains_critical_pattern_optimized(self, message: str) -> bool:
        """Optimized version of critical pattern checking."""
        # Check cache first
        cached_result = self._get_cached_pattern_result(message)
        if cached_result is not None:
            return cached_result[1]
        
        # Use compiled regex patterns for faster matching
        for pattern in self._compiled_critical_patterns:
            if pattern.search(message):
                # Update cache with critical pattern found
                with self._cache_lock:
                    if message in self._pattern_cache:
                        filtered, _ = self._pattern_cache[message]
                        self._pattern_cache[message] = (filtered, True)
                    else:
                        self._pattern_cache[message] = (False, True)
                return True
        
        # Fallback to original string-based matching
        for pattern in self.critical_patterns:
            if pattern in message:
                # Update cache with critical pattern found
                with self._cache_lock:
                    if message in self._pattern_cache:
                        filtered, _ = self._pattern_cache[message]
                        self._pattern_cache[message] = (filtered, True)
                    else:
                        self._pattern_cache[message] = (False, True)
                return True
        
        return False
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Optimized filter method with performance improvements."""
        self._filter_calls += 1
        
        # Early exit for debug mode
        if self.debug_mode:
            return True
        
        # Early exit for non-LiteLLM loggers (cached)
        if not self._is_litellm_logger_cached(record.name):
            return True
        
        # Early exit for ERROR and CRITICAL levels
        if record.levelno >= logging.ERROR:
            return True
        
        # Get message with error handling
        try:
            message = record.getMessage().lower()
        except Exception:
            return True  # Allow through if we can't get the message
        
        # Early exit for empty messages
        if not message:
            return True
        
        # Check critical patterns first (more important)
        if self._contains_critical_pattern_optimized(message):
            return True
        
        # Filter out INFO and DEBUG messages with filtered patterns
        if record.levelno <= logging.INFO:
            if self._contains_filtered_pattern_optimized(message):
                return False
        
        return True
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the optimized filter."""
        cache_hit_rate = (self._cache_hits / (self._cache_hits + self._cache_misses)) * 100 if (self._cache_hits + self._cache_misses) > 0 else 0
        
        return {
            'filter_calls': self._filter_calls,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate_percent': cache_hit_rate,
            'cache_size': len(self._pattern_cache),
            'compiled_patterns': len(self._compiled_patterns),
            'compiled_critical_patterns': len(self._compiled_critical_patterns)
        }
    
    def clear_cache(self):
        """Clear the pattern matching cache."""
        with self._cache_lock:
            self._pattern_cache.clear()
            self._cache_hits = 0
            self._cache_misses = 0


class OptimizedTokenUsageTracker(TokenUsageTracker):
    """
    Optimized version of token usage tracker with performance improvements.
    
    Optimizations:
    - Lazy evaluation of expensive calculations
    - Batch processing for statistics updates
    - Memory-efficient data structures
    - Reduced object creation
    """
    
    def __init__(self):
        """Initialize the optimized tracker."""
        super().__init__()
        
        # Optimized data structures
        self._model_stats_cache = {}
        self._prompt_stats_cache = {}
        self._stats_dirty = True
        
        # Batch processing
        self._batch_updates = []
        self._batch_size = 100
        
        # Performance counters
        self._record_calls = 0
        self._batch_flushes = 0
        
        # Thread safety
        self._lock = threading.RLock()
    
    def record_usage(self, model: str, prompt_name: str, response: Any, response_time: float = None) -> None:
        """Optimized usage recording with batch processing."""
        self._record_calls += 1
        
        try:
            # Extract usage data (optimized)
            usage_data = self._extract_usage_optimized(response)
            if not usage_data:
                return
            
            # Calculate cost (cached if possible)
            cost = self._calculate_cost_optimized(response, model)
            
            # Create minimal record for batch processing
            batch_record = {
                'model': model,
                'prompt_name': prompt_name,
                'input_tokens': usage_data.get('prompt_tokens', 0),
                'output_tokens': usage_data.get('completion_tokens', 0),
                'total_tokens': usage_data.get('total_tokens', 0),
                'cost': cost,
                'response_time': response_time
            }
            
            with self._lock:
                self._batch_updates.append(batch_record)
                
                # Flush batch if it's full
                if len(self._batch_updates) >= self._batch_size:
                    self._flush_batch()
            
        except Exception as e:
            # Log error but don't fail
            logging.getLogger(__name__).error(f"Error in optimized usage recording: {e}")
    
    def _extract_usage_optimized(self, response: Any) -> Dict[str, int]:
        """Optimized usage extraction with minimal object access."""
        try:
            # Fast path for common response structure
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                return {
                    'prompt_tokens': getattr(usage, 'prompt_tokens', 0),
                    'completion_tokens': getattr(usage, 'completion_tokens', 0),
                    'total_tokens': getattr(usage, 'total_tokens', 0)
                }
            
            # Fallback path
            return super()._extract_usage_from_response(response)
            
        except Exception:
            return {}
    
    def _calculate_cost_optimized(self, response: Any, model: str) -> float:
        """Optimized cost calculation with caching."""
        # Use a simple cache for cost calculations
        cache_key = f"{model}_{getattr(response, 'id', 'unknown')}"
        
        try:
            # Try the parent implementation
            return super()._calculate_cost(response, model)
        except Exception:
            return None
    
    def _flush_batch(self):
        """Flush batch updates to main data structures."""
        if not self._batch_updates:
            return
        
        self._batch_flushes += 1
        
        # Process all batch updates
        for batch_record in self._batch_updates:
            # Create full record
            from datetime import datetime
            from .token_usage_tracker import UsageRecord
            
            record = UsageRecord(
                model=batch_record['model'],
                prompt_name=batch_record['prompt_name'],
                input_tokens=batch_record['input_tokens'],
                output_tokens=batch_record['output_tokens'],
                total_tokens=batch_record['total_tokens'],
                cost=batch_record['cost'],
                timestamp=datetime.now(),
                response_time=batch_record['response_time']
            )
            
            # Add to main records
            self.records.append(record)
            
            # Update aggregated statistics
            self._update_model_stats(record)
            self._update_prompt_stats(record)
        
        # Clear batch
        self._batch_updates.clear()
        self._stats_dirty = True
    
    def get_total_statistics(self) -> Dict[str, Any]:
        """Get statistics with lazy evaluation."""
        # Flush any pending batch updates
        with self._lock:
            if self._batch_updates:
                self._flush_batch()
        
        return super().get_total_statistics()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the optimized tracker."""
        return {
            'record_calls': self._record_calls,
            'batch_flushes': self._batch_flushes,
            'pending_batch_size': len(self._batch_updates),
            'batch_size_limit': self._batch_size,
            'total_records': len(self.records)
        }
    
    def reset(self):
        """Reset with batch flush."""
        with self._lock:
            if self._batch_updates:
                self._flush_batch()
        
        super().reset()
        
        # Reset optimization state
        self._model_stats_cache.clear()
        self._prompt_stats_cache.clear()
        self._stats_dirty = True
        self._record_calls = 0
        self._batch_flushes = 0


class PerformanceOptimizer:
    """Main class for implementing and testing logging performance optimizations."""
    
    def __init__(self):
        """Initialize the performance optimizer."""
        self.original_filter = LiteLLMFilter(debug_mode=False)
        self.optimized_filter = OptimizedLiteLLMFilter(debug_mode=False)
        
        self.original_tracker = TokenUsageTracker()
        self.optimized_tracker = OptimizedTokenUsageTracker()
        
        self.benchmark_results = {}
    
    def benchmark_filter_performance(self, num_messages: int = 10000) -> Dict[str, Any]:
        """Benchmark filter performance improvements."""
        print(f"🔍 Benchmarking Filter Performance ({num_messages:,} messages)")
        print("=" * 60)
        
        # Create test messages
        test_messages = [
            ('litellm.main', logging.INFO, 'Cost calculation for request {}'),
            ('litellm.completion', logging.DEBUG, 'Completion wrapper processing {}'),
            ('litellm.utils', logging.INFO, 'Token counting for request {}'),
            ('litellm.main', logging.WARNING, 'Rate limit warning for request {}'),
            ('litellm.main', logging.ERROR, 'Authentication failed for request {}'),
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
        
        # Benchmark original filter
        start_time = time.perf_counter()
        original_passed = 0
        for record in records:
            if self.original_filter.filter(record):
                original_passed += 1
        original_time = time.perf_counter() - start_time
        
        # Benchmark optimized filter
        start_time = time.perf_counter()
        optimized_passed = 0
        for record in records:
            if self.optimized_filter.filter(record):
                optimized_passed += 1
        optimized_time = time.perf_counter() - start_time
        
        # Calculate improvements
        speedup = original_time / optimized_time if optimized_time > 0 else float('inf')
        original_rate = num_messages / original_time if original_time > 0 else 0
        optimized_rate = num_messages / optimized_time if optimized_time > 0 else 0
        
        results = {
            'num_messages': num_messages,
            'original_time': original_time,
            'optimized_time': optimized_time,
            'speedup': speedup,
            'original_rate': original_rate,
            'optimized_rate': optimized_rate,
            'original_passed': original_passed,
            'optimized_passed': optimized_passed,
            'results_match': original_passed == optimized_passed
        }
        
        # Get optimization stats
        opt_stats = self.optimized_filter.get_performance_stats()
        results.update(opt_stats)
        
        print(f"📊 Filter Benchmark Results:")
        print(f"   • Original Time: {original_time:.6f}s ({original_rate:,.0f} msg/sec)")
        print(f"   • Optimized Time: {optimized_time:.6f}s ({optimized_rate:,.0f} msg/sec)")
        print(f"   • Speedup: {speedup:.2f}x")
        print(f"   • Results Match: {results['results_match']}")
        print(f"   • Cache Hit Rate: {opt_stats['cache_hit_rate_percent']:.1f}%")
        
        self.benchmark_results['filter'] = results
        return results
    
    def benchmark_tracker_performance(self, num_calls: int = 5000) -> Dict[str, Any]:
        """Benchmark tracker performance improvements."""
        print(f"\n📈 Benchmarking Tracker Performance ({num_calls:,} calls)")
        print("=" * 60)
        
        from unittest.mock import Mock, patch
        
        # Create mock response
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        models = ['gpt-3.5-turbo', 'gpt-4', 'claude-3-sonnet']
        prompts = ['completion', 'analysis', 'generation']
        
        # Benchmark original tracker
        start_time = time.perf_counter()
        with patch('litellm.completion_cost', return_value=0.001):
            for i in range(num_calls):
                self.original_tracker.record_usage(
                    model=models[i % len(models)],
                    prompt_name=prompts[i % len(prompts)],
                    response=mock_response,
                    response_time=0.5
                )
        original_time = time.perf_counter() - start_time
        
        # Benchmark optimized tracker
        start_time = time.perf_counter()
        with patch('litellm.completion_cost', return_value=0.001):
            for i in range(num_calls):
                self.optimized_tracker.record_usage(
                    model=models[i % len(models)],
                    prompt_name=prompts[i % len(prompts)],
                    response=mock_response,
                    response_time=0.5
                )
        optimized_time = time.perf_counter() - start_time
        
        # Get statistics to ensure data integrity
        original_stats = self.original_tracker.get_total_statistics()
        optimized_stats = self.optimized_tracker.get_total_statistics()
        
        # Calculate improvements
        speedup = original_time / optimized_time if optimized_time > 0 else float('inf')
        original_rate = num_calls / original_time if original_time > 0 else 0
        optimized_rate = num_calls / optimized_time if optimized_time > 0 else 0
        
        results = {
            'num_calls': num_calls,
            'original_time': original_time,
            'optimized_time': optimized_time,
            'speedup': speedup,
            'original_rate': original_rate,
            'optimized_rate': optimized_rate,
            'original_total_calls': original_stats['total_calls'],
            'optimized_total_calls': optimized_stats['total_calls'],
            'data_integrity': original_stats['total_calls'] == optimized_stats['total_calls']
        }
        
        # Get optimization stats
        opt_stats = self.optimized_tracker.get_performance_stats()
        results.update(opt_stats)
        
        print(f"📊 Tracker Benchmark Results:")
        print(f"   • Original Time: {original_time:.6f}s ({original_rate:,.0f} calls/sec)")
        print(f"   • Optimized Time: {optimized_time:.6f}s ({optimized_rate:,.0f} calls/sec)")
        print(f"   • Speedup: {speedup:.2f}x")
        print(f"   • Data Integrity: {results['data_integrity']}")
        print(f"   • Batch Flushes: {opt_stats['batch_flushes']}")
        
        self.benchmark_results['tracker'] = results
        return results
    
    def run_comprehensive_optimization_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive optimization benchmarks."""
        print("🚀 Starting Comprehensive Optimization Benchmarks")
        print("=" * 80)
        
        # Run benchmarks
        filter_results = self.benchmark_filter_performance(20000)
        tracker_results = self.benchmark_tracker_performance(10000)
        
        # Generate summary
        print("\n📋 Optimization Summary")
        print("=" * 80)
        
        print("🎯 Performance Improvements:")
        print(f"   • Filter Speedup: {filter_results['speedup']:.2f}x")
        print(f"   • Tracker Speedup: {tracker_results['speedup']:.2f}x")
        
        print(f"\n📊 Throughput Improvements:")
        print(f"   • Filter: {filter_results['original_rate']:,.0f} → {filter_results['optimized_rate']:,.0f} msg/sec")
        print(f"   • Tracker: {tracker_results['original_rate']:,.0f} → {tracker_results['optimized_rate']:,.0f} calls/sec")
        
        print(f"\n✅ Data Integrity:")
        print(f"   • Filter Results Match: {filter_results['results_match']}")
        print(f"   • Tracker Data Integrity: {tracker_results['data_integrity']}")
        
        print(f"\n🔧 Optimization Features:")
        print(f"   • Filter Cache Hit Rate: {filter_results['cache_hit_rate_percent']:.1f}%")
        print(f"   • Tracker Batch Processing: {tracker_results['batch_flushes']} flushes")
        
        return {
            'filter': filter_results,
            'tracker': tracker_results,
            'overall_success': filter_results['results_match'] and tracker_results['data_integrity']
        }
    
    def save_optimization_report(self, filename: str = None) -> str:
        """Save optimization benchmark report."""
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/optimization_benchmark_{timestamp}.json"
        
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        import json
        with open(filename, 'w') as f:
            json.dump(self.benchmark_results, f, indent=2)
        
        return filename


def main():
    """Main function to run optimization benchmarks."""
    optimizer = PerformanceOptimizer()
    
    try:
        # Run comprehensive benchmarks
        results = optimizer.run_comprehensive_optimization_benchmark()
        
        # Save results
        report_file = optimizer.save_optimization_report()
        print(f"\n📁 Optimization report saved to: {report_file}")
        
        # Return success/failure based on data integrity
        return 0 if results['overall_success'] else 1
        
    except Exception as e:
        print(f"❌ Error during optimization benchmarking: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())