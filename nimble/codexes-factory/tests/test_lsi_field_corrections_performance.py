"""
Performance tests for LSI field mapping corrections
"""

import pytest
import time
import tempfile
import json
import csv
from pathlib import Path
from unittest.mock import Mock, patch
from codexes.modules.distribution.enhanced_field_mappings import (
    ThemaSubjectStrategy, AgeRangeStrategy, SeriesAwareDescriptionStrategy,
    BlankIngramPricingStrategy, TrancheFilePathStrategy
)
from codexes.modules.distribution.field_mapping import MappingContext
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestLSIFieldCorrectionsPerformance:
    """Performance tests for LSI field mapping corrections."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_metadata = self.create_test_metadata()
        self.test_context = self.create_test_context()
        
    def create_test_metadata(self):
        """Create test metadata."""
        metadata = Mock(spec=CodexMetadata)
        metadata.title = "Performance Test Book"
        metadata.short_description = "This book offers comprehensive performance testing insights."
        metadata.series_name = "Performance Series"
        return metadata
        
    def create_test_context(self):
        """Create test mapping context."""
        context = Mock(spec=MappingContext)
        context.field_name = "Test Field"
        context.raw_metadata = {
            'thema': ['TGBN', 'JNFH', 'JFFG'],
            'min_age': 18,
            'max_age': 65,
            'series_name': 'Performance Series'
        }
        context.config = {
            'tranche_config': {
                'file_path_templates': {
                    'interior': 'interior/{title_slug}_interior.pdf',
                    'cover': 'covers/{title_slug}_cover.pdf'
                }
            }
        }
        return context
        
    def test_thema_subject_extraction_performance(self):
        """Test performance of thema subject extraction."""
        strategy = ThemaSubjectStrategy(1)
        
        # Warm up
        for _ in range(10):
            strategy.map_field(self.test_metadata, self.test_context)
        
        # Performance test
        start_time = time.time()
        iterations = 1000
        
        for _ in range(iterations):
            result = strategy.map_field(self.test_metadata, self.test_context)
            assert result == "TGBN"
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_ms = (total_time / iterations) * 1000
        
        # Should complete each extraction in less than 1ms
        assert avg_time_ms < 1.0, f"Thema extraction too slow: {avg_time_ms:.3f}ms per extraction"
        print(f"Thema subject extraction: {avg_time_ms:.3f}ms per extraction")
        
    def test_age_range_extraction_performance(self):
        """Test performance of age range extraction."""
        min_strategy = AgeRangeStrategy("min")
        max_strategy = AgeRangeStrategy("max")
        
        # Warm up
        for _ in range(10):
            min_strategy.map_field(self.test_metadata, self.test_context)
            max_strategy.map_field(self.test_metadata, self.test_context)
        
        # Performance test
        start_time = time.time()
        iterations = 1000
        
        for _ in range(iterations):
            min_result = min_strategy.map_field(self.test_metadata, self.test_context)
            max_result = max_strategy.map_field(self.test_metadata, self.test_context)
            assert min_result == "18"
            assert max_result == "65"
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_ms = (total_time / iterations) * 1000
        
        # Should complete each extraction in less than 1ms
        assert avg_time_ms < 1.0, f"Age range extraction too slow: {avg_time_ms:.3f}ms per extraction"
        print(f"Age range extraction: {avg_time_ms:.3f}ms per extraction")
        
    def test_series_description_processing_performance(self):
        """Test performance of series-aware description processing."""
        strategy = SeriesAwareDescriptionStrategy()
        
        # Warm up
        for _ in range(10):
            strategy.map_field(self.test_metadata, self.test_context)
        
        # Performance test
        start_time = time.time()
        iterations = 1000
        
        for _ in range(iterations):
            result = strategy.map_field(self.test_metadata, self.test_context)
            assert "Performance Series series" in result
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_ms = (total_time / iterations) * 1000
        
        # Should complete each processing in less than 2ms
        assert avg_time_ms < 2.0, f"Series description processing too slow: {avg_time_ms:.3f}ms per processing"
        print(f"Series description processing: {avg_time_ms:.3f}ms per processing")
        
    def test_file_path_generation_performance(self):
        """Test performance of file path generation."""
        interior_strategy = TrancheFilePathStrategy("interior")
        cover_strategy = TrancheFilePathStrategy("cover")
        
        # Warm up
        for _ in range(10):
            interior_strategy.map_field(self.test_metadata, self.test_context)
            cover_strategy.map_field(self.test_metadata, self.test_context)
        
        # Performance test
        start_time = time.time()
        iterations = 1000
        
        for _ in range(iterations):
            interior_result = interior_strategy.map_field(self.test_metadata, self.test_context)
            cover_result = cover_strategy.map_field(self.test_metadata, self.test_context)
            assert "interior/" in interior_result
            assert "covers/" in cover_result
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_ms = (total_time / iterations) * 1000
        
        # Should complete each generation in less than 1ms
        assert avg_time_ms < 1.0, f"File path generation too slow: {avg_time_ms:.3f}ms per generation"
        print(f"File path generation: {avg_time_ms:.3f}ms per generation")
        
    def test_blank_ingram_pricing_performance(self):
        """Test performance of blank Ingram pricing strategy."""
        strategy = BlankIngramPricingStrategy()
        
        # Performance test (no warm up needed for simple strategy)
        start_time = time.time()
        iterations = 10000
        
        for _ in range(iterations):
            result = strategy.map_field(self.test_metadata, self.test_context)
            assert result == ""
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_ms = (total_time / iterations) * 1000
        
        # Should complete each call in less than 0.1ms
        assert avg_time_ms < 0.1, f"Blank pricing strategy too slow: {avg_time_ms:.3f}ms per call"
        print(f"Blank Ingram pricing: {avg_time_ms:.3f}ms per call")
        
    def test_combined_strategies_performance(self):
        """Test performance of all strategies combined."""
        strategies = [
            ("Thema Subject 1", ThemaSubjectStrategy(1)),
            ("Thema Subject 2", ThemaSubjectStrategy(2)),
            ("Thema Subject 3", ThemaSubjectStrategy(3)),
            ("Min Age", AgeRangeStrategy("min")),
            ("Max Age", AgeRangeStrategy("max")),
            ("Short Description", SeriesAwareDescriptionStrategy()),
            ("Interior Path", TrancheFilePathStrategy("interior")),
            ("Cover Path", TrancheFilePathStrategy("cover")),
            ("Blank Pricing", BlankIngramPricingStrategy()),
        ]
        
        # Warm up
        for _ in range(10):
            for name, strategy in strategies:
                strategy.map_field(self.test_metadata, self.test_context)
        
        # Performance test
        start_time = time.time()
        iterations = 100
        
        for _ in range(iterations):
            results = {}
            for name, strategy in strategies:
                results[name] = strategy.map_field(self.test_metadata, self.test_context)
            
            # Verify results
            assert results["Thema Subject 1"] == "TGBN"
            assert results["Min Age"] == "18"
            assert "Performance Series series" in results["Short Description"]
            assert results["Blank Pricing"] == ""
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_ms = (total_time / iterations) * 1000
        
        # Should complete all strategies in less than 10ms
        assert avg_time_ms < 10.0, f"Combined strategies too slow: {avg_time_ms:.3f}ms per iteration"
        print(f"Combined strategies: {avg_time_ms:.3f}ms per iteration ({len(strategies)} strategies)")
        
    def test_memory_usage_stability(self):
        """Test that strategies don't leak memory over many iterations."""
        import gc
        import sys
        
        strategy = ThemaSubjectStrategy(1)
        
        # Get initial memory usage
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Run many iterations
        iterations = 10000
        for _ in range(iterations):
            result = strategy.map_field(self.test_metadata, self.test_context)
            assert result == "TGBN"
        
        # Check memory usage after
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory usage should not grow significantly
        object_growth = final_objects - initial_objects
        growth_percentage = (object_growth / initial_objects) * 100
        
        # Allow up to 5% growth in object count
        assert growth_percentage < 5.0, f"Memory usage grew too much: {growth_percentage:.1f}%"
        print(f"Memory stability: {growth_percentage:.1f}% object growth over {iterations} iterations")
        
    def test_concurrent_strategy_usage(self):
        """Test performance with concurrent strategy usage."""
        import threading
        import queue
        
        def worker(strategy, metadata, context, result_queue, iterations):
            """Worker function for threading test."""
            start_time = time.time()
            for _ in range(iterations):
                result = strategy.map_field(metadata, context)
                # Don't store all results to avoid memory issues
            end_time = time.time()
            result_queue.put(end_time - start_time)
        
        strategy = ThemaSubjectStrategy(1)
        result_queue = queue.Queue()
        threads = []
        num_threads = 4
        iterations_per_thread = 250
        
        # Start threads
        for _ in range(num_threads):
            thread = threading.Thread(
                target=worker,
                args=(strategy, self.test_metadata, self.test_context, result_queue, iterations_per_thread)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Collect results
        times = []
        while not result_queue.empty():
            times.append(result_queue.get())
        
        # Verify all threads completed
        assert len(times) == num_threads
        
        # Check performance
        max_time = max(times)
        avg_time = sum(times) / len(times)
        
        # Should complete in reasonable time even with concurrency
        assert max_time < 2.0, f"Concurrent execution too slow: {max_time:.3f}s max time"
        print(f"Concurrent execution: {avg_time:.3f}s average, {max_time:.3f}s max ({num_threads} threads)")
        
    def test_large_data_handling_performance(self):
        """Test performance with large data sets."""
        # Create metadata with large data
        large_metadata = Mock(spec=CodexMetadata)
        large_metadata.title = "A" * 1000  # Very long title
        large_metadata.short_description = "This book " + "offers insights " * 100  # Long description
        large_metadata.series_name = "Large Series Name " * 10
        
        large_context = Mock(spec=MappingContext)
        large_context.field_name = "Test Field"
        large_context.raw_metadata = {
            'thema': ['TGBN'] * 100,  # Many thema subjects (will be limited to 3)
            'min_age': 18,
            'max_age': 65,
            'series_name': large_metadata.series_name
        }
        large_context.config = {
            'tranche_config': {
                'file_path_templates': {
                    'interior': 'interior/{title_slug}_interior.pdf',
                    'cover': 'covers/{title_slug}_cover.pdf'
                }
            }
        }
        
        strategies = [
            ThemaSubjectStrategy(1),
            SeriesAwareDescriptionStrategy(),
            TrancheFilePathStrategy("interior")
        ]
        
        # Performance test with large data
        start_time = time.time()
        iterations = 100
        
        for _ in range(iterations):
            for strategy in strategies:
                result = strategy.map_field(large_metadata, large_context)
                # Verify results are reasonable
                assert len(result) < 10000  # Shouldn't be excessively long
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_ms = (total_time / iterations) * 1000
        
        # Should handle large data efficiently
        assert avg_time_ms < 50.0, f"Large data handling too slow: {avg_time_ms:.3f}ms per iteration"
        print(f"Large data handling: {avg_time_ms:.3f}ms per iteration")
        
    def test_error_handling_performance(self):
        """Test that error handling doesn't significantly impact performance."""
        # Create context that will cause errors
        error_context = Mock(spec=MappingContext)
        error_context.field_name = "Test Field"
        error_context.raw_metadata = None  # Will cause errors
        error_context.config = None
        
        strategy = ThemaSubjectStrategy(1)
        
        # Performance test with errors
        start_time = time.time()
        iterations = 1000
        
        for _ in range(iterations):
            try:
                result = strategy.map_field(self.test_metadata, error_context)
                # Should return empty string on error
                assert result == ""
            except Exception:
                # Errors are acceptable in this test
                pass
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_ms = (total_time / iterations) * 1000
        
        # Error handling should not be excessively slow
        assert avg_time_ms < 5.0, f"Error handling too slow: {avg_time_ms:.3f}ms per iteration"
        print(f"Error handling: {avg_time_ms:.3f}ms per iteration")