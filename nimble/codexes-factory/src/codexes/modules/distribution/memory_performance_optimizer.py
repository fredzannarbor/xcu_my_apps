
"""
Memory and Performance Optimizer

This module provides tools for optimizing memory usage and performance in LSI generation.
"""

import gc
import logging
import time

# Optional psutil import with fallback
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available - memory monitoring will be limited")
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
from dataclasses import dataclass
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class MemorySnapshot:
    """Snapshot of memory usage at a point in time."""
    timestamp: float
    rss_mb: float  # Resident Set Size in MB
    vms_mb: float  # Virtual Memory Size in MB
    percent: float  # Memory percentage
    available_mb: float  # Available memory in MB


@dataclass
class PerformanceMetrics:
    """Performance metrics for an operation."""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    memory_before: MemorySnapshot
    memory_after: MemorySnapshot
    memory_peak: MemorySnapshot
    memory_delta_mb: float


class MemoryPerformanceOptimizer:
    """Provides memory and performance optimization tools."""
    
    def __init__(self):
        self.process = psutil.Process() if PSUTIL_AVAILABLE else None
        self.metrics_history: List[PerformanceMetrics] = []
        self.memory_threshold_mb = 1000  # Alert if memory usage exceeds 1GB
        self.gc_frequency = 10  # Force garbage collection every N operations
        self.operation_count = 0
    
    def get_memory_snapshot(self) -> MemorySnapshot:
        """Get current memory usage snapshot."""
        if not PSUTIL_AVAILABLE or not self.process:
            # Fallback when psutil is not available
            return MemorySnapshot(
                timestamp=time.time(),
                rss_mb=0.0,
                vms_mb=0.0,
                percent=0.0,
                available_mb=1000.0  # Assume 1GB available
            )
        
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()
        virtual_memory = psutil.virtual_memory()
        
        return MemorySnapshot(
            timestamp=time.time(),
            rss_mb=memory_info.rss / 1024 / 1024,
            vms_mb=memory_info.vms / 1024 / 1024,
            percent=memory_percent,
            available_mb=virtual_memory.available / 1024 / 1024
        )
    
    @contextmanager
    def monitor_operation(self, operation_name: str):
        """Context manager to monitor memory and performance of an operation."""
        # Take initial snapshot
        memory_before = self.get_memory_snapshot()
        start_time = time.time()
        peak_memory = memory_before
        
        try:
            yield
        finally:
            # Take final snapshot
            end_time = time.time()
            memory_after = self.get_memory_snapshot()
            
            # Check if we hit a new peak
            if memory_after.rss_mb > peak_memory.rss_mb:
                peak_memory = memory_after
            
            # Create performance metrics
            metrics = PerformanceMetrics(
                operation_name=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=peak_memory,
                memory_delta_mb=memory_after.rss_mb - memory_before.rss_mb
            )
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Log performance info
            logger.info(f"Operation '{operation_name}' completed in {metrics.duration:.3f}s, "
                       f"memory delta: {metrics.memory_delta_mb:+.1f}MB")
            
            # Check for memory issues
            if memory_after.rss_mb > self.memory_threshold_mb:
                logger.warning(f"High memory usage detected: {memory_after.rss_mb:.1f}MB")
            
            # Periodic garbage collection
            self.operation_count += 1
            if self.operation_count % self.gc_frequency == 0:
                self.force_garbage_collection()
    
    def force_garbage_collection(self):
        """Force garbage collection and log memory recovery."""
        memory_before = self.get_memory_snapshot()
        
        # Force garbage collection
        collected = gc.collect()
        
        memory_after = self.get_memory_snapshot()
        memory_freed = memory_before.rss_mb - memory_after.rss_mb
        
        logger.info(f"Garbage collection: freed {memory_freed:.1f}MB, "
                   f"collected {collected} objects")
    
    def optimize_for_batch_processing(self, batch_size: int):
        """Optimize settings for batch processing."""
        # Adjust garbage collection frequency based on batch size
        if batch_size > 100:
            self.gc_frequency = 5  # More frequent GC for large batches
        elif batch_size > 50:
            self.gc_frequency = 8
        else:
            self.gc_frequency = 10
        
        # Adjust memory threshold based on available memory
        if PSUTIL_AVAILABLE:
            available_memory = psutil.virtual_memory().available / 1024 / 1024
            self.memory_threshold_mb = min(1000, available_memory * 0.8)  # Use up to 80% of available
        else:
            self.memory_threshold_mb = 1000  # Default threshold
        
        logger.info(f"Optimized for batch size {batch_size}: "
                   f"GC frequency={self.gc_frequency}, "
                   f"memory threshold={self.memory_threshold_mb:.0f}MB")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics."""
        if not self.metrics_history:
            return {"message": "No performance data available"}
        
        total_operations = len(self.metrics_history)
        total_time = sum(m.duration for m in self.metrics_history)
        avg_time = total_time / total_operations
        
        memory_deltas = [m.memory_delta_mb for m in self.metrics_history]
        avg_memory_delta = sum(memory_deltas) / len(memory_deltas)
        max_memory_delta = max(memory_deltas)
        
        current_memory = self.get_memory_snapshot()
        
        return {
            "total_operations": total_operations,
            "total_time": total_time,
            "average_time_per_operation": avg_time,
            "average_memory_delta_mb": avg_memory_delta,
            "max_memory_delta_mb": max_memory_delta,
            "current_memory_mb": current_memory.rss_mb,
            "current_memory_percent": current_memory.percent,
            "available_memory_mb": current_memory.available_mb
        }
    
    def clear_metrics_history(self):
        """Clear performance metrics history to free memory."""
        cleared_count = len(self.metrics_history)
        self.metrics_history.clear()
        logger.info(f"Cleared {cleared_count} performance metrics from history")


def memory_optimized(operation_name: str = None):
    """Decorator to add memory optimization to functions."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get or create optimizer instance
            if not hasattr(wrapper, '_optimizer'):
                wrapper._optimizer = MemoryPerformanceOptimizer()
            
            op_name = operation_name or func.__name__
            
            with wrapper._optimizer.monitor_operation(op_name):
                result = func(*args, **kwargs)
            
            return result
        
        return wrapper
    return decorator


class LLMResponseCache:
    """Simple cache for LLM responses to avoid repeated calls."""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
        self.access_count: Dict[str, int] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached response."""
        if key in self.cache:
            self.access_count[key] = self.access_count.get(key, 0) + 1
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set cached response."""
        # If cache is full, remove least accessed item
        if len(self.cache) >= self.max_size:
            least_accessed = min(self.access_count.items(), key=lambda x: x[1])
            del self.cache[least_accessed[0]]
            del self.access_count[least_accessed[0]]
        
        self.cache[key] = value
        self.access_count[key] = 1
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()
        self.access_count.clear()
        logger.info("Cleared LLM response cache")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "total_accesses": sum(self.access_count.values()),
            "average_accesses": sum(self.access_count.values()) / max(1, len(self.access_count))
        }


# Global instances
_global_optimizer = MemoryPerformanceOptimizer()
_global_cache = LLMResponseCache()


def get_global_optimizer() -> MemoryPerformanceOptimizer:
    """Get global memory performance optimizer instance."""
    return _global_optimizer


def get_global_cache() -> LLMResponseCache:
    """Get global LLM response cache instance."""
    return _global_cache
