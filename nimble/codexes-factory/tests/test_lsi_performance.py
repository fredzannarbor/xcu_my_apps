#!/usr/bin/env python3
"""
LSI Performance Test Suite

This test suite validates performance characteristics of the LSI CSV generation system,
including processing times, memory usage, and scalability under various load conditions.
"""

import pytest
import time
import psutil
import os
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch
import threading
from concurrent.futures import ThreadPoolExecutor

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.llm_caller import call_model_with_prompt, _parse_json_with_fallbacks
from codexes.modules.distribution.bisac_validator import get_bisac_validator
from codexes.modules.distribution.text_formatter import get_text_formatter
from codexes.modules.distribution.multi_level_config import MultiLevelConfiguration, ConfigurationContext


class PerformanceMonitor:
    """Utility class for monitoring performance metrics."""
    
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.process = psutil.Process(os.getpid())
    
    def start(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def stop(self):
        """Stop monitoring and return metrics."""
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            'duration': end_time - self.start_time,
            'memory_start': self.start_memory,
            'memory_end': end_memory,
            'memory_delta': end_memory - self.start_memory,
            'memory_peak': self.process.memory_info().peak_wss / 1024 / 1024 if hasattr(self.process.memory_info(), 'peak_wss') else end_memory
        }


class TestSingleBookProcessingPerformance:
    """Test performance of single book processing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
        self.bisac_validator = get_bisac_validator()
        self.text_formatter = get_text_formatter()
    
    def test_json_parsing_performance(self):
        """Test JSON parsing performance with various response types."""
        test_cases = [
            '{"title": "Test Book", "author": "Test Author"}',  # Valid JSON
            '{"title": "Test Book", "author": "Test Author"',   # Malformed JSON
            'Here is the response: {"title": "Test Book"}',     # Mixed content
            'Title: Test Book\nAuthor: Test Author',            # Conversational
        ]
        
        self.monitor.start()
        
        for _ in range(100):  # Process 100 responses
            for test_case in test_cases:
                result = _parse_json_with_fallbacks(test_case)
                assert isinstance(result, dict)
        
        metrics = self.monitor.stop()
        
        # Should process 400 responses in under 1 second
        assert metrics['duration'] < 1.0
        # Memory usage should be reasonable
        assert metrics['memory_delta'] < 50  # Less than 50MB increase
    
    def test_bisac_validation_performance(self):
        """Test BISAC validation performance."""
        test_codes = [
            'BUS001000', 'COM002000', 'SCI003000', 'PHI001000', 'SEL001000',
            'INVALID', 'BUS999999', 'ABC123456'  # Mix of valid and invalid
        ]
        
        self.monitor.start()
        
        for _ in range(1000):  # Validate 1000 codes
            for code in test_codes:
                result = self.bisac_validator.validate_bisac_code(code)
                assert hasattr(result, 'is_valid')
        
        metrics = self.monitor.stop()
        
        # Should validate 8000 codes in under 2 seconds
        assert metrics['duration'] < 2.0
        # Memory usage should be stable
        assert metrics['memory_delta'] < 20  # Less than 20MB increase
    
    def test_text_formatting_performance(self):
        """Test text formatting performance."""
        test_texts = [
            'Short text',
            'A' * 100,   # Medium text
            'B' * 1000,  # Long text
            'C' * 5000,  # Very long text requiring truncation
        ]
        
        field_types = ['title', 'short_description', 'long_description', 'keywords']
        
        self.monitor.start()
        
        for _ in range(100):  # Process 100 iterations
            for text in test_texts:
                for field_type in field_types:
                    result = self.text_formatter.validate_field_length(field_type, text)
                    assert hasattr(result, 'is_valid')
        
        metrics = self.monitor.stop()
        
        # Should process 1600 text validations in under 1 second
        assert metrics['duration'] < 1.0
        # Memory usage should be reasonable
        assert metrics['memory_delta'] < 30  # Less than 30MB increase
    
    def test_configuration_loading_performance(self):
        """Test configuration loading performance."""
        # Create temporary configuration files
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir)
        
        # Create multiple config files
        for config_type in ['publishers', 'imprints', 'tranches']:
            type_dir = config_dir / config_type
            type_dir.mkdir()
            
            for i in range(10):  # 10 configs of each type
                config_data = {f'{config_type}_value_{j}': f'value_{i}_{j}' for j in range(20)}
                config_file = type_dir / f'config_{i}.json'
                with open(config_file, 'w') as f:
                    json.dump(config_data, f)
        
        try:
            self.monitor.start()
            
            # Load configuration multiple times
            for _ in range(10):
                config = MultiLevelConfiguration(str(config_dir))
                
                # Access various configuration values
                context = ConfigurationContext(
                    publisher_name='config_0',
                    imprint_name='config_1',
                    tranche_name='config_2'
                )
                
                for i in range(5):
                    value = config.get_value(f'publishers_value_{i}', context)
            
            metrics = self.monitor.stop()
            
            # Should load and access configs in under 2 seconds
            assert metrics['duration'] < 2.0
            # Memory usage should be reasonable
            assert metrics['memory_delta'] < 100  # Less than 100MB increase
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)


class TestBatchProcessingPerformance:
    """Test performance of batch processing operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
    
    def create_mock_metadata(self, count: int) -> List[Mock]:
        """Create mock metadata objects for testing."""
        metadata_list = []
        for i in range(count):
            metadata = Mock()
            metadata.title = f'Test Book {i}'
            metadata.author = f'Test Author {i}'
            metadata.isbn13 = f'978123456{i:04d}'
            metadata.publisher = 'Test Publisher'
            metadata.description = f'This is test book {i} description.'
            metadata_list.append(metadata)
        return metadata_list
    
    def test_small_batch_performance(self):
        """Test performance with small batch (10 books)."""
        metadata_list = self.create_mock_metadata(10)
        
        self.monitor.start()
        
        # Simulate batch processing
        processed_books = []
        for metadata in metadata_list:
            # Simulate field validation
            validator = get_bisac_validator()
            formatter = get_text_formatter()
            
            # Validate some fields
            title_result = formatter.validate_field_length('title', metadata.title)
            bisac_result = validator.validate_bisac_code('BUS001000')
            
            processed_books.append({
                'title': metadata.title,
                'title_valid': title_result.is_valid,
                'bisac_valid': bisac_result.is_valid
            })
        
        metrics = self.monitor.stop()
        
        # Should process 10 books in under 1 second
        assert metrics['duration'] < 1.0
        assert len(processed_books) == 10
        # Memory usage should be reasonable
        assert metrics['memory_delta'] < 50  # Less than 50MB increase
    
    def test_medium_batch_performance(self):
        """Test performance with medium batch (50 books)."""
        metadata_list = self.create_mock_metadata(50)
        
        self.monitor.start()
        
        # Simulate batch processing with error isolation
        processed_books = []
        failed_books = []
        
        for metadata in metadata_list:
            try:
                # Simulate processing that might fail
                if 'Book 25' in metadata.title:  # Simulate failure
                    raise Exception("Simulated processing error")
                
                # Simulate field validation
                validator = get_bisac_validator()
                formatter = get_text_formatter()
                
                title_result = formatter.validate_field_length('title', metadata.title)
                processed_books.append({
                    'title': metadata.title,
                    'title_valid': title_result.is_valid
                })
            except Exception as e:
                failed_books.append({
                    'title': metadata.title,
                    'error': str(e)
                })
        
        metrics = self.monitor.stop()
        
        # Should process 50 books in under 3 seconds
        assert metrics['duration'] < 3.0
        assert len(processed_books) == 49  # One should fail
        assert len(failed_books) == 1
        # Memory usage should be reasonable
        assert metrics['memory_delta'] < 100  # Less than 100MB increase
    
    def test_large_batch_performance(self):
        """Test performance with large batch (100 books)."""
        metadata_list = self.create_mock_metadata(100)
        
        self.monitor.start()
        
        # Simulate batch processing with statistics tracking
        batch_stats = {
            'total_books': len(metadata_list),
            'successful_books': 0,
            'failed_books': 0,
            'processing_errors': []
        }
        
        for i, metadata in enumerate(metadata_list):
            try:
                # Simulate occasional failures
                if i % 20 == 0 and i > 0:  # Fail every 20th book after the first
                    raise Exception(f"Simulated error for book {i}")
                
                # Simulate processing
                validator = get_bisac_validator()
                formatter = get_text_formatter()
                
                title_result = formatter.validate_field_length('title', metadata.title)
                if title_result.is_valid:
                    batch_stats['successful_books'] += 1
                else:
                    batch_stats['failed_books'] += 1
                    
            except Exception as e:
                batch_stats['failed_books'] += 1
                batch_stats['processing_errors'].append(str(e))
        
        metrics = self.monitor.stop()
        
        # Should process 100 books in under 5 seconds
        assert metrics['duration'] < 5.0
        assert batch_stats['successful_books'] > 90  # Most should succeed
        assert batch_stats['failed_books'] < 10     # Few should fail
        # Memory usage should be reasonable for large batch
        assert metrics['memory_delta'] < 200  # Less than 200MB increase
    
    def test_concurrent_processing_performance(self):
        """Test performance of concurrent processing."""
        metadata_list = self.create_mock_metadata(50)
        
        def process_book(metadata):
            """Process a single book."""
            validator = get_bisac_validator()
            formatter = get_text_formatter()
            
            title_result = formatter.validate_field_length('title', metadata.title)
            bisac_result = validator.validate_bisac_code('BUS001000')
            
            return {
                'title': metadata.title,
                'title_valid': title_result.is_valid,
                'bisac_valid': bisac_result.is_valid
            }
        
        self.monitor.start()
        
        # Process books concurrently
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(process_book, metadata_list))
        
        metrics = self.monitor.stop()
        
        # Concurrent processing should be faster than sequential
        assert metrics['duration'] < 2.0  # Should be faster than sequential
        assert len(results) == 50
        # Memory usage might be higher due to threading
        assert metrics['memory_delta'] < 150  # Less than 150MB increase


class TestMemoryUsagePatterns:
    """Test memory usage patterns and potential leaks."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
    
    def test_memory_stability_over_time(self):
        """Test that memory usage remains stable over extended processing."""
        validator = get_bisac_validator()
        formatter = get_text_formatter()
        
        memory_samples = []
        
        for iteration in range(10):  # 10 iterations
            self.monitor.start()
            
            # Process a batch of operations
            for i in range(100):
                # BISAC validation
                validator.validate_bisac_code('BUS001000')
                
                # Text formatting
                formatter.validate_field_length('title', f'Test Title {i}')
                
                # JSON parsing
                _parse_json_with_fallbacks(f'{{"title": "Test {i}"}}')
            
            metrics = self.monitor.stop()
            memory_samples.append(metrics['memory_end'])
        
        # Memory usage should not continuously increase
        memory_growth = memory_samples[-1] - memory_samples[0]
        assert memory_growth < 100  # Less than 100MB growth over 10 iterations
        
        # Check for memory leaks (no continuous growth)
        if len(memory_samples) >= 5:
            recent_avg = sum(memory_samples[-3:]) / 3
            early_avg = sum(memory_samples[:3]) / 3
            growth_rate = (recent_avg - early_avg) / early_avg
            assert growth_rate < 0.5  # Less than 50% growth
    
    def test_memory_cleanup_after_large_operations(self):
        """Test that memory is cleaned up after large operations."""
        import gc
        
        # Baseline memory
        gc.collect()
        baseline_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        
        # Perform large operation
        large_text = 'A' * 1000000  # 1MB of text
        formatter = get_text_formatter()
        
        for _ in range(100):  # Process large text 100 times
            result = formatter.validate_field_length('long_description', large_text)
            assert result.suggested_text is not None  # Should be truncated
        
        # Force garbage collection
        del large_text
        gc.collect()
        
        # Check memory after cleanup
        final_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        memory_increase = final_memory - baseline_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 200  # Less than 200MB increase after cleanup


class TestScalabilityLimits:
    """Test system behavior at scalability limits."""
    
    def test_maximum_batch_size_handling(self):
        """Test handling of very large batch sizes."""
        # Test with progressively larger batches
        batch_sizes = [100, 500, 1000]
        
        for batch_size in batch_sizes:
            monitor = PerformanceMonitor()
            monitor.start()
            
            # Create large batch
            metadata_list = []
            for i in range(batch_size):
                metadata = Mock()
                metadata.title = f'Book {i}'
                metadata_list.append(metadata)
            
            # Process batch with error isolation
            processed = 0
            failed = 0
            
            for metadata in metadata_list:
                try:
                    formatter = get_text_formatter()
                    result = formatter.validate_field_length('title', metadata.title)
                    if result.is_valid:
                        processed += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1
            
            metrics = monitor.stop()
            
            # Should handle large batches without crashing
            assert processed + failed == batch_size
            # Processing time should scale reasonably
            time_per_book = metrics['duration'] / batch_size
            assert time_per_book < 0.1  # Less than 0.1 seconds per book
    
    def test_resource_constraint_handling(self):
        """Test behavior under resource constraints."""
        # Simulate resource constraints by processing many operations
        validator = get_bisac_validator()
        formatter = get_text_formatter()
        
        operations_count = 10000
        start_time = time.time()
        
        successful_operations = 0
        failed_operations = 0
        
        for i in range(operations_count):
            try:
                # Mix of operations
                if i % 3 == 0:
                    validator.validate_bisac_code('BUS001000')
                elif i % 3 == 1:
                    formatter.validate_field_length('title', f'Title {i}')
                else:
                    _parse_json_with_fallbacks(f'{{"test": "{i}"}}')
                
                successful_operations += 1
            except Exception:
                failed_operations += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle high volume of operations
        assert successful_operations > operations_count * 0.95  # 95% success rate
        # Should maintain reasonable performance
        ops_per_second = operations_count / duration
        assert ops_per_second > 1000  # At least 1000 operations per second


def test_performance_regression_detection():
    """Test for performance regressions."""
    # Baseline performance expectations
    performance_baselines = {
        'json_parsing_per_second': 1000,
        'bisac_validation_per_second': 2000,
        'text_formatting_per_second': 1000,
        'single_book_processing_time': 0.1,  # seconds
        'batch_100_processing_time': 5.0,    # seconds
    }
    
    # Test JSON parsing performance
    start_time = time.time()
    for _ in range(1000):
        _parse_json_with_fallbacks('{"test": "value"}')
    json_time = time.time() - start_time
    json_rate = 1000 / json_time
    
    assert json_rate >= performance_baselines['json_parsing_per_second']
    
    # Test BISAC validation performance
    validator = get_bisac_validator()
    start_time = time.time()
    for _ in range(1000):
        validator.validate_bisac_code('BUS001000')
    bisac_time = time.time() - start_time
    bisac_rate = 1000 / bisac_time
    
    assert bisac_rate >= performance_baselines['bisac_validation_per_second']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])