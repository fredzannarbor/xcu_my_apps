#!/usr/bin/env python3
"""
Test suite for performance optimization and caching system.
Tests cache management, query optimization, and performance monitoring.
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.codexes.modules.ideation.performance.cache_manager import (
    CacheManager, CacheEntry, CacheStrategy, PerformanceMonitor
)


class TestCacheManager:
    """Test cases for CacheManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache_manager = CacheManager()
    
    def test_cache_manager_initialization(self):
        """Test cache manager initialization."""
        manager = CacheManager()
        assert manager.cache_storage == {}
        assert manager.cache_stats["hits"] == 0
        assert manager.cache_stats["misses"] == 0
        assert manager.max_cache_size == 1000
        assert manager.default_ttl == 3600
    
    def test_cache_entry_creation(self):
        """Test cache entry creation and validation."""
        data = {"test": "data"}
        entry = CacheEntry(
            key="test_key",
            data=data,
            ttl=300,
            strategy=CacheStrategy.LRU
        )
        
        assert entry.key == "test_key"
        assert entry.data == data
        assert entry.ttl == 300
        assert entry.strategy == CacheStrategy.LRU
        assert entry.created_at is not None
        assert entry.last_accessed is not None
        assert entry.access_count == 0
        assert not entry.is_expired()
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration logic."""
        entry = CacheEntry(
            key="test_key",
            data={"test": "data"},
            ttl=1  # 1 second TTL
        )
        
        assert not entry.is_expired()
        
        # Simulate time passing
        entry.created_at = datetime.now() - timedelta(seconds=2)
        assert entry.is_expired()
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        key = "test_key"
        data = {"message": "test data"}
        
        # Set cache entry
        self.cache_manager.set(key, data, ttl=300)
        
        # Get cache entry
        result = self.cache_manager.get(key)
        
        assert result == data
        assert self.cache_manager.cache_stats["hits"] == 1
        assert self.cache_manager.cache_stats["misses"] == 0
    
    def test_cache_miss(self):
        """Test cache miss behavior."""
        result = self.cache_manager.get("non_existent_key")
        
        assert result is None
        assert self.cache_manager.cache_stats["hits"] == 0
        assert self.cache_manager.cache_stats["misses"] == 1
    
    def test_cache_expiration_cleanup(self):
        """Test automatic cleanup of expired entries."""
        # Set entry with short TTL
        self.cache_manager.set("short_ttl", {"data": "test"}, ttl=1)
        
        # Verify it exists
        assert self.cache_manager.get("short_ttl") is not None
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should return None and trigger cleanup
        result = self.cache_manager.get("short_ttl")
        assert result is None
        assert "short_ttl" not in self.cache_manager.cache_storage
    
    def test_cache_size_limit_enforcement(self):
        """Test cache size limit enforcement with LRU eviction."""
        # Set small cache size for testing
        self.cache_manager.max_cache_size = 3
        
        # Fill cache to capacity
        for i in range(3):
            self.cache_manager.set(f"key_{i}", {"data": i})
        
        assert len(self.cache_manager.cache_storage) == 3
        
        # Add one more entry (should evict least recently used)
        self.cache_manager.set("key_3", {"data": 3})
        
        assert len(self.cache_manager.cache_storage) == 3
        assert "key_0" not in self.cache_manager.cache_storage  # Should be evicted
        assert "key_3" in self.cache_manager.cache_storage
    
    def test_cache_invalidation(self):
        """Test cache invalidation functionality."""
        key = "test_key"
        self.cache_manager.set(key, {"data": "test"})
        
        # Verify entry exists
        assert self.cache_manager.get(key) is not None
        
        # Invalidate entry
        self.cache_manager.invalidate(key)
        
        # Should return None after invalidation
        assert self.cache_manager.get(key) is None
        assert key not in self.cache_manager.cache_storage
    
    def test_cache_clear(self):
        """Test clearing entire cache."""
        # Add multiple entries
        for i in range(5):
            self.cache_manager.set(f"key_{i}", {"data": i})
        
        assert len(self.cache_manager.cache_storage) == 5
        
        # Clear cache
        self.cache_manager.clear()
        
        assert len(self.cache_manager.cache_storage) == 0
        assert self.cache_manager.cache_stats["hits"] == 0
        assert self.cache_manager.cache_stats["misses"] == 0
    
    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        # Generate some cache activity
        self.cache_manager.set("key1", {"data": 1})
        self.cache_manager.set("key2", {"data": 2})
        
        # Generate hits and misses
        self.cache_manager.get("key1")  # Hit
        self.cache_manager.get("key1")  # Hit
        self.cache_manager.get("key3")  # Miss
        
        stats = self.cache_manager.get_statistics()
        
        assert stats["total_entries"] == 2
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 2/3
        assert stats["memory_usage"] > 0
    
    def test_cache_key_generation(self):
        """Test cache key generation for complex objects."""
        # Test with different data types
        key1 = self.cache_manager.generate_cache_key("llm_response", {"prompt": "test"})
        key2 = self.cache_manager.generate_cache_key("llm_response", {"prompt": "test"})
        key3 = self.cache_manager.generate_cache_key("llm_response", {"prompt": "different"})
        
        assert key1 == key2  # Same input should generate same key
        assert key1 != key3  # Different input should generate different key
        assert isinstance(key1, str)
        assert len(key1) > 0
    
    def test_cache_strategies(self):
        """Test different cache strategies."""
        # Test LRU strategy
        self.cache_manager.max_cache_size = 2
        
        self.cache_manager.set("key1", {"data": 1}, strategy=CacheStrategy.LRU)
        self.cache_manager.set("key2", {"data": 2}, strategy=CacheStrategy.LRU)
        
        # Access key1 to make it more recently used
        self.cache_manager.get("key1")
        
        # Add key3 (should evict key2, not key1)
        self.cache_manager.set("key3", {"data": 3}, strategy=CacheStrategy.LRU)
        
        assert "key1" in self.cache_manager.cache_storage
        assert "key2" not in self.cache_manager.cache_storage
        assert "key3" in self.cache_manager.cache_storage


class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
    
    def test_monitor_initialization(self):
        """Test performance monitor initialization."""
        monitor = PerformanceMonitor()
        assert monitor.metrics == {}
        assert monitor.active_operations == {}
    
    def test_operation_timing(self):
        """Test operation timing functionality."""
        operation_id = "test_operation"
        
        # Start timing
        self.monitor.start_operation(operation_id)
        assert operation_id in self.monitor.active_operations
        
        # Simulate some work
        time.sleep(0.1)
        
        # End timing
        duration = self.monitor.end_operation(operation_id)
        
        assert duration >= 0.1
        assert operation_id not in self.monitor.active_operations
        assert operation_id in self.monitor.metrics
    
    def test_context_manager_timing(self):
        """Test timing using context manager."""
        with self.monitor.time_operation("context_test") as timer:
            time.sleep(0.05)
            # Can access timer.operation_id if needed
            assert timer.operation_id == "context_test"
        
        # Operation should be recorded
        assert "context_test" in self.monitor.metrics
        assert self.monitor.metrics["context_test"]["duration"] >= 0.05
    
    def test_memory_usage_tracking(self):
        """Test memory usage tracking."""
        # Record memory usage
        self.monitor.record_memory_usage("test_operation")
        
        assert "test_operation" in self.monitor.metrics
        assert "memory_usage" in self.monitor.metrics["test_operation"]
        assert self.monitor.metrics["test_operation"]["memory_usage"] > 0
    
    def test_database_query_metrics(self):
        """Test database query performance tracking."""
        query = "SELECT * FROM codex_objects WHERE genre = ?"
        params = ("fantasy",)
        
        # Simulate query execution
        with self.monitor.time_operation("db_query") as timer:
            time.sleep(0.02)  # Simulate query time
        
        # Record query-specific metrics
        self.monitor.record_database_query(query, params, 0.02, 150)
        
        stats = self.monitor.get_database_statistics()
        assert stats["total_queries"] == 1
        assert stats["average_query_time"] == 0.02
        assert stats["total_rows_processed"] == 150
    
    def test_llm_call_metrics(self):
        """Test LLM call performance tracking."""
        prompt = "Generate a fantasy book concept"
        model = "gpt-4"
        
        # Record LLM call metrics
        self.monitor.record_llm_call(
            prompt=prompt,
            model=model,
            response_time=1.5,
            tokens_used=250,
            cost=0.05
        )
        
        stats = self.monitor.get_llm_statistics()
        assert stats["total_calls"] == 1
        assert stats["average_response_time"] == 1.5
        assert stats["total_tokens"] == 250
        assert stats["total_cost"] == 0.05
    
    def test_performance_report_generation(self):
        """Test comprehensive performance report generation."""
        # Generate some test metrics
        with self.monitor.time_operation("operation1"):
            time.sleep(0.01)
        
        with self.monitor.time_operation("operation2"):
            time.sleep(0.02)
        
        self.monitor.record_memory_usage("memory_test")
        self.monitor.record_llm_call("test prompt", "gpt-4", 1.0, 100, 0.02)
        
        report = self.monitor.generate_performance_report()
        
        assert "summary" in report
        assert "operations" in report
        assert "database" in report
        assert "llm_calls" in report
        assert "memory" in report
        assert report["summary"]["total_operations"] == 2
    
    def test_performance_optimization_suggestions(self):
        """Test performance optimization suggestions."""
        # Create scenarios that should trigger suggestions
        
        # Slow operation
        self.monitor.metrics["slow_operation"] = {
            "duration": 5.0,
            "timestamp": datetime.now()
        }
        
        # High memory usage
        self.monitor.metrics["memory_heavy"] = {
            "memory_usage": 500 * 1024 * 1024,  # 500MB
            "timestamp": datetime.now()
        }
        
        # Expensive LLM calls
        self.monitor.record_llm_call("expensive", "gpt-4", 3.0, 1000, 0.50)
        
        suggestions = self.monitor.get_optimization_suggestions()
        
        assert len(suggestions) > 0
        assert any("slow" in suggestion.lower() for suggestion in suggestions)
        assert any("memory" in suggestion.lower() for suggestion in suggestions)
        assert any("cost" in suggestion.lower() for suggestion in suggestions)
    
    def test_metrics_export(self):
        """Test metrics export functionality."""
        # Generate test data
        with self.monitor.time_operation("export_test"):
            time.sleep(0.01)
        
        # Export to JSON
        json_export = self.monitor.export_metrics("json")
        assert isinstance(json_export, str)
        
        # Verify JSON is valid
        parsed_json = json.loads(json_export)
        assert "export_test" in parsed_json
        
        # Export to CSV format
        csv_export = self.monitor.export_metrics("csv")
        assert isinstance(csv_export, str)
        assert "operation_id" in csv_export
        assert "duration" in csv_export


class TestCacheIntegration:
    """Integration tests for cache and performance systems."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache_manager = CacheManager()
        self.performance_monitor = PerformanceMonitor()
    
    def test_cached_llm_response_simulation(self):
        """Test caching of LLM responses with performance monitoring."""
        prompt = "Generate a fantasy book concept"
        
        # Simulate first call (cache miss)
        with self.performance_monitor.time_operation("llm_call_1") as timer:
            cache_key = self.cache_manager.generate_cache_key("llm_response", {"prompt": prompt})
            cached_response = self.cache_manager.get(cache_key)
            
            if cached_response is None:
                # Simulate LLM call
                time.sleep(0.1)  # Simulate network delay
                response = {"title": "The Crystal Sword", "genre": "fantasy"}
                self.cache_manager.set(cache_key, response, ttl=3600)
                result = response
            else:
                result = cached_response
        
        # Simulate second call (cache hit)
        with self.performance_monitor.time_operation("llm_call_2") as timer:
            cache_key = self.cache_manager.generate_cache_key("llm_response", {"prompt": prompt})
            cached_response = self.cache_manager.get(cache_key)
            
            if cached_response is None:
                time.sleep(0.1)  # This shouldn't happen
                response = {"title": "The Crystal Sword", "genre": "fantasy"}
                self.cache_manager.set(cache_key, response, ttl=3600)
                result = response
            else:
                result = cached_response
        
        # Verify cache hit improved performance
        metrics = self.performance_monitor.metrics
        call1_duration = metrics["llm_call_1"]["duration"]
        call2_duration = metrics["llm_call_2"]["duration"]
        
        assert call2_duration < call1_duration  # Cache hit should be faster
        assert self.cache_manager.cache_stats["hits"] == 1
        assert self.cache_manager.cache_stats["misses"] == 1
    
    def test_database_query_caching(self):
        """Test database query result caching."""
        query = "SELECT * FROM codex_objects WHERE genre = ?"
        params = ("fantasy",)
        
        # Simulate first query (cache miss)
        with self.performance_monitor.time_operation("db_query_1"):
            cache_key = self.cache_manager.generate_cache_key("db_query", {
                "query": query,
                "params": params
            })
            
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is None:
                # Simulate database query
                time.sleep(0.05)
                result = [{"id": 1, "title": "Fantasy Book", "genre": "fantasy"}]
                self.cache_manager.set(cache_key, result, ttl=1800)
            else:
                result = cached_result
        
        # Simulate second query (cache hit)
        with self.performance_monitor.time_operation("db_query_2"):
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is None:
                time.sleep(0.05)  # This shouldn't happen
                result = [{"id": 1, "title": "Fantasy Book", "genre": "fantasy"}]
                self.cache_manager.set(cache_key, result, ttl=1800)
            else:
                result = cached_result
        
        # Verify performance improvement
        metrics = self.performance_monitor.metrics
        query1_duration = metrics["db_query_1"]["duration"]
        query2_duration = metrics["db_query_2"]["duration"]
        
        assert query2_duration < query1_duration
        assert len(result) == 1
        assert result[0]["genre"] == "fantasy"
    
    def test_performance_monitoring_with_caching(self):
        """Test comprehensive performance monitoring with caching enabled."""
        operations = ["operation_1", "operation_2", "operation_3"]
        
        for i, op in enumerate(operations):
            with self.performance_monitor.time_operation(op):
                # Simulate work with caching
                cache_key = f"work_result_{i}"
                cached_result = self.cache_manager.get(cache_key)
                
                if cached_result is None:
                    time.sleep(0.02)  # Simulate work
                    result = {"work": f"result_{i}"}
                    self.cache_manager.set(cache_key, result)
                else:
                    result = cached_result
        
        # Generate performance report
        report = self.performance_monitor.generate_performance_report()
        cache_stats = self.cache_manager.get_statistics()
        
        assert report["summary"]["total_operations"] == 3
        assert cache_stats["total_entries"] == 3
        assert cache_stats["misses"] == 3  # All first-time operations
    
    def test_cache_warming_strategy(self):
        """Test cache warming for frequently accessed data."""
        # Simulate cache warming for common queries
        common_queries = [
            ("fantasy", 100),
            ("mystery", 75),
            ("romance", 150)
        ]
        
        # Warm cache with common query results
        for genre, count in common_queries:
            cache_key = self.cache_manager.generate_cache_key("genre_count", {"genre": genre})
            self.cache_manager.set(cache_key, {"genre": genre, "count": count}, ttl=7200)
        
        # Verify cache is warmed
        assert len(self.cache_manager.cache_storage) == 3
        
        # Test retrieval performance
        with self.performance_monitor.time_operation("warmed_cache_access"):
            for genre, expected_count in common_queries:
                cache_key = self.cache_manager.generate_cache_key("genre_count", {"genre": genre})
                result = self.cache_manager.get(cache_key)
                assert result is not None
                assert result["count"] == expected_count
        
        # Should be very fast due to cache hits
        access_duration = self.performance_monitor.metrics["warmed_cache_access"]["duration"]
        assert access_duration < 0.01  # Should be very fast


if __name__ == "__main__":
    pytest.main([__file__])