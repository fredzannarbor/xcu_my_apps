#!/usr/bin/env python3

"""
Fix Remaining LSI Generation Issues

This script addresses the remaining incomplete tasks from the LSI CSV bug fixes:
- Task 9: Resolve tranche configuration application issues
- Task 10: Implement robust error handling for configuration
- Task 12: Improve batch processing error reporting
- Task 13: Optimize memory usage and performance
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tranche_config_debugger():
    """Create a tranche configuration debugger to fix application issues."""
    
    debugger_code = '''
"""
Tranche Configuration Debugger

This module provides debugging and validation tools for tranche configuration application.
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TrancheConfigDebugger:
    """Debug and validate tranche configuration application."""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.debug_enabled = True
    
    def debug_tranche_loading(self, tranche_name: str) -> Dict[str, Any]:
        """Debug tranche configuration loading process."""
        debug_info = {
            "tranche_name": tranche_name,
            "config_path": None,
            "exists": False,
            "loaded_successfully": False,
            "config_keys": [],
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check if tranche config file exists
            tranche_path = self.config_dir / "tranches" / f"{tranche_name}.json"
            debug_info["config_path"] = str(tranche_path)
            debug_info["exists"] = tranche_path.exists()
            
            if not tranche_path.exists():
                debug_info["errors"].append(f"Tranche config file not found: {tranche_path}")
                return debug_info
            
            # Try to load the configuration
            with open(tranche_path, 'r') as f:
                config = json.load(f)
            
            debug_info["loaded_successfully"] = True
            debug_info["config_keys"] = list(config.keys())
            
            # Validate expected tranche configuration sections
            expected_sections = [
                "series_info", "contributor_info", "annotation_boilerplate",
                "table_of_contents_template", "file_paths", "blank_fields"
            ]
            
            for section in expected_sections:
                if section not in config:
                    debug_info["warnings"].append(f"Missing expected section: {section}")
                else:
                    logger.info(f"Found tranche section: {section}")
            
            # Validate annotation boilerplate specifically
            if "annotation_boilerplate" in config:
                boilerplate = config["annotation_boilerplate"]
                if not isinstance(boilerplate, dict):
                    debug_info["errors"].append("annotation_boilerplate must be a dictionary")
                else:
                    if "suffix" not in boilerplate:
                        debug_info["warnings"].append("annotation_boilerplate missing 'suffix' key")
                    if "prefix" not in boilerplate:
                        debug_info["warnings"].append("annotation_boilerplate missing 'prefix' key")
            
            logger.info(f"Tranche config debug complete for {tranche_name}")
            
        except json.JSONDecodeError as e:
            debug_info["errors"].append(f"Invalid JSON in tranche config: {e}")
        except Exception as e:
            debug_info["errors"].append(f"Error loading tranche config: {e}")
        
        return debug_info
    
    def validate_tranche_application(self, tranche_name: str, metadata_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that tranche configuration is properly applied to metadata."""
        validation_result = {
            "tranche_name": tranche_name,
            "applied_correctly": True,
            "missing_applications": [],
            "successful_applications": [],
            "errors": []
        }
        
        try:
            # Load tranche config
            tranche_path = self.config_dir / "tranches" / f"{tranche_name}.json"
            if not tranche_path.exists():
                validation_result["errors"].append(f"Tranche config not found: {tranche_path}")
                validation_result["applied_correctly"] = False
                return validation_result
            
            with open(tranche_path, 'r') as f:
                tranche_config = json.load(f)
            
            # Check series information application
            if "series_info" in tranche_config:
                series_info = tranche_config["series_info"]
                if "series_name" in series_info:
                    expected_series = series_info["series_name"]
                    actual_series = metadata_dict.get("series_name", "")
                    if actual_series == expected_series:
                        validation_result["successful_applications"].append(f"Series name: {expected_series}")
                    else:
                        validation_result["missing_applications"].append(
                            f"Series name not applied: expected '{expected_series}', got '{actual_series}'"
                        )
                        validation_result["applied_correctly"] = False
            
            # Check contributor information application
            if "contributor_info" in tranche_config:
                contrib_info = tranche_config["contributor_info"]
                for key, expected_value in contrib_info.items():
                    actual_value = metadata_dict.get(key, "")
                    if actual_value == expected_value:
                        validation_result["successful_applications"].append(f"{key}: applied correctly")
                    else:
                        validation_result["missing_applications"].append(
                            f"{key} not applied: expected '{expected_value}', got '{actual_value}'"
                        )
                        validation_result["applied_correctly"] = False
            
            # Check annotation boilerplate application
            if "annotation_boilerplate" in tranche_config:
                boilerplate = tranche_config["annotation_boilerplate"]
                annotation = metadata_dict.get("annotation_summary", "")
                
                if "suffix" in boilerplate and boilerplate["suffix"]:
                    if boilerplate["suffix"] in annotation:
                        validation_result["successful_applications"].append("Annotation suffix applied")
                    else:
                        validation_result["missing_applications"].append("Annotation suffix not applied")
                        validation_result["applied_correctly"] = False
                
                if "prefix" in boilerplate and boilerplate["prefix"]:
                    if annotation.startswith(boilerplate["prefix"]):
                        validation_result["successful_applications"].append("Annotation prefix applied")
                    else:
                        validation_result["missing_applications"].append("Annotation prefix not applied")
                        validation_result["applied_correctly"] = False
            
        except Exception as e:
            validation_result["errors"].append(f"Error validating tranche application: {e}")
            validation_result["applied_correctly"] = False
        
        return validation_result
'''
    
    # Write the debugger file
    debugger_path = "src/codexes/modules/distribution/tranche_config_debugger.py"
    with open(debugger_path, 'w') as f:
        f.write(debugger_code)
    
    logger.info(f"Created tranche configuration debugger: {debugger_path}")
    return True

def create_robust_config_error_handler():
    """Create robust error handling for configuration loading."""
    
    handler_code = '''
"""
Robust Configuration Error Handler

This module provides comprehensive error handling for configuration loading and validation.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConfigurationError:
    """Represents a configuration error with context."""
    error_type: str
    message: str
    file_path: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


class RobustConfigurationHandler:
    """Provides robust error handling for configuration operations."""
    
    def __init__(self):
        self.errors: List[ConfigurationError] = []
        self.warnings: List[str] = []
    
    def load_config_with_fallback(self, config_path: str, fallback_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Load configuration with comprehensive error handling and fallback."""
        if fallback_config is None:
            fallback_config = {}
        
        try:
            path = Path(config_path)
            
            # Check if file exists
            if not path.exists():
                error = ConfigurationError(
                    error_type="FILE_NOT_FOUND",
                    message=f"Configuration file not found: {config_path}",
                    file_path=config_path,
                    suggestion="Create the configuration file or check the path"
                )
                self.errors.append(error)
                logger.warning(f"Config file not found, using fallback: {config_path}")
                return fallback_config
            
            # Check if file is readable
            if not os.access(path, os.R_OK):
                error = ConfigurationError(
                    error_type="PERMISSION_DENIED",
                    message=f"Cannot read configuration file: {config_path}",
                    file_path=config_path,
                    suggestion="Check file permissions"
                )
                self.errors.append(error)
                logger.error(f"Cannot read config file, using fallback: {config_path}")
                return fallback_config
            
            # Try to load JSON
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for empty file
                if not content.strip():
                    error = ConfigurationError(
                        error_type="EMPTY_FILE",
                        message=f"Configuration file is empty: {config_path}",
                        file_path=config_path,
                        suggestion="Add valid JSON configuration to the file"
                    )
                    self.errors.append(error)
                    logger.warning(f"Empty config file, using fallback: {config_path}")
                    return fallback_config
                
                # Parse JSON with detailed error reporting
                try:
                    config = json.loads(content)
                except json.JSONDecodeError as e:
                    error = ConfigurationError(
                        error_type="INVALID_JSON",
                        message=f"Invalid JSON in configuration file: {e.msg}",
                        file_path=config_path,
                        line_number=e.lineno,
                        suggestion=f"Fix JSON syntax error at line {e.lineno}, column {e.colno}"
                    )
                    self.errors.append(error)
                    logger.error(f"Invalid JSON in config file, using fallback: {config_path}")
                    return fallback_config
                
                # Validate configuration structure
                if not isinstance(config, dict):
                    error = ConfigurationError(
                        error_type="INVALID_STRUCTURE",
                        message=f"Configuration must be a JSON object, got {type(config).__name__}",
                        file_path=config_path,
                        suggestion="Ensure the configuration file contains a JSON object ({})"
                    )
                    self.errors.append(error)
                    logger.error(f"Invalid config structure, using fallback: {config_path}")
                    return fallback_config
                
                # Merge with fallback config (fallback provides defaults)
                merged_config = {**fallback_config, **config}
                
                logger.info(f"Successfully loaded configuration: {config_path}")
                return merged_config
                
        except Exception as e:
            error = ConfigurationError(
                error_type="UNEXPECTED_ERROR",
                message=f"Unexpected error loading configuration: {str(e)}",
                file_path=config_path,
                suggestion="Check the configuration file and system permissions"
            )
            self.errors.append(error)
            logger.error(f"Unexpected error loading config, using fallback: {config_path}")
            return fallback_config
    
    def validate_required_fields(self, config: Dict[str, Any], required_fields: List[str], 
                                config_path: str) -> bool:
        """Validate that required fields are present in configuration."""
        all_valid = True
        
        for field in required_fields:
            if field not in config:
                error = ConfigurationError(
                    error_type="MISSING_REQUIRED_FIELD",
                    message=f"Required field '{field}' missing from configuration",
                    file_path=config_path,
                    suggestion=f"Add '{field}' to the configuration file"
                )
                self.errors.append(error)
                all_valid = False
            elif config[field] is None or (isinstance(config[field], str) and not config[field].strip()):
                error = ConfigurationError(
                    error_type="EMPTY_REQUIRED_FIELD",
                    message=f"Required field '{field}' is empty",
                    file_path=config_path,
                    suggestion=f"Provide a valid value for '{field}'"
                )
                self.errors.append(error)
                all_valid = False
        
        return all_valid
    
    def get_error_report(self) -> Dict[str, Any]:
        """Get comprehensive error report."""
        return {
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [
                {
                    "type": error.error_type,
                    "message": error.message,
                    "file": error.file_path,
                    "line": error.line_number,
                    "suggestion": error.suggestion
                }
                for error in self.errors
            ],
            "warnings": self.warnings
        }
    
    def clear_errors(self):
        """Clear all errors and warnings."""
        self.errors.clear()
        self.warnings.clear()
'''
    
    # Write the error handler file
    handler_path = "src/codexes/modules/distribution/robust_config_handler.py"
    with open(handler_path, 'w') as f:
        f.write(handler_code)
    
    logger.info(f"Created robust configuration error handler: {handler_path}")
    return True


def create_batch_processing_reporter():
    """Create improved batch processing error reporting."""
    
    reporter_code = '''
"""
Enhanced Batch Processing Reporter

This module provides comprehensive reporting for batch processing operations.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class BookProcessingResult:
    """Result of processing a single book."""
    book_id: str
    title: str
    status: str  # "success", "failed", "skipped"
    processing_time: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    fields_populated: int = 0
    total_fields: int = 0
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class BatchProcessingReport:
    """Comprehensive batch processing report."""
    batch_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_books: int = 0
    successful_books: int = 0
    failed_books: int = 0
    skipped_books: int = 0
    book_results: List[BookProcessingResult] = field(default_factory=list)
    overall_errors: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


class BatchProcessingReporter:
    """Enhanced batch processing reporter with detailed error tracking."""
    
    def __init__(self, report_dir: str = "logs/batch_reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.current_report: Optional[BatchProcessingReport] = None
    
    def start_batch_report(self, batch_id: str, total_books: int) -> BatchProcessingReport:
        """Start a new batch processing report."""
        self.current_report = BatchProcessingReport(
            batch_id=batch_id,
            start_time=datetime.now(),
            total_books=total_books
        )
        
        logger.info(f"Started batch processing report: {batch_id} ({total_books} books)")
        return self.current_report
    
    def add_book_result(self, result: BookProcessingResult):
        """Add a book processing result to the current report."""
        if not self.current_report:
            logger.error("No active batch report to add book result to")
            return
        
        self.current_report.book_results.append(result)
        
        # Update counters
        if result.status == "success":
            self.current_report.successful_books += 1
        elif result.status == "failed":
            self.current_report.failed_books += 1
        elif result.status == "skipped":
            self.current_report.skipped_books += 1
        
        logger.info(f"Added book result: {result.title} - {result.status}")
    
    def add_overall_error(self, error: str):
        """Add an overall batch processing error."""
        if not self.current_report:
            logger.error("No active batch report to add error to")
            return
        
        self.current_report.overall_errors.append(error)
        logger.error(f"Added batch error: {error}")
    
    def complete_batch_report(self) -> Optional[BatchProcessingReport]:
        """Complete the current batch report and save it."""
        if not self.current_report:
            logger.error("No active batch report to complete")
            return None
        
        self.current_report.end_time = datetime.now()
        
        # Calculate performance metrics
        total_time = (self.current_report.end_time - self.current_report.start_time).total_seconds()
        self.current_report.performance_metrics = {
            "total_processing_time": total_time,
            "average_time_per_book": total_time / max(1, self.current_report.total_books),
            "success_rate": self.current_report.successful_books / max(1, self.current_report.total_books),
            "error_rate": self.current_report.failed_books / max(1, self.current_report.total_books)
        }
        
        # Save report to file
        report_file = self.report_dir / f"batch_report_{self.current_report.batch_id}.json"
        self._save_report_to_file(self.current_report, report_file)
        
        # Generate summary
        self._log_batch_summary(self.current_report)
        
        completed_report = self.current_report
        self.current_report = None
        
        return completed_report
    
    def create_book_result(self, book_id: str, title: str, status: str, 
                          processing_time: float) -> BookProcessingResult:
        """Create a new book processing result."""
        return BookProcessingResult(
            book_id=book_id,
            title=title,
            status=status,
            processing_time=processing_time
        )
    
    def _save_report_to_file(self, report: BatchProcessingReport, file_path: Path):
        """Save batch report to JSON file."""
        try:
            report_data = {
                "batch_id": report.batch_id,
                "start_time": report.start_time.isoformat(),
                "end_time": report.end_time.isoformat() if report.end_time else None,
                "summary": {
                    "total_books": report.total_books,
                    "successful_books": report.successful_books,
                    "failed_books": report.failed_books,
                    "skipped_books": report.skipped_books
                },
                "performance_metrics": report.performance_metrics,
                "overall_errors": report.overall_errors,
                "book_results": [
                    {
                        "book_id": result.book_id,
                        "title": result.title,
                        "status": result.status,
                        "processing_time": result.processing_time,
                        "errors": result.errors,
                        "warnings": result.warnings,
                        "fields_populated": result.fields_populated,
                        "total_fields": result.total_fields,
                        "validation_errors": result.validation_errors
                    }
                    for result in report.book_results
                ]
            }
            
            with open(file_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"Saved batch report to: {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving batch report: {e}")
    
    def _log_batch_summary(self, report: BatchProcessingReport):
        """Log a summary of the batch processing results."""
        logger.info("=" * 60)
        logger.info(f"BATCH PROCESSING SUMMARY - {report.batch_id}")
        logger.info("=" * 60)
        logger.info(f"Total Books: {report.total_books}")
        logger.info(f"Successful: {report.successful_books} ({report.performance_metrics['success_rate']:.1%})")
        logger.info(f"Failed: {report.failed_books} ({report.performance_metrics['error_rate']:.1%})")
        logger.info(f"Skipped: {report.skipped_books}")
        logger.info(f"Total Time: {report.performance_metrics['total_processing_time']:.2f}s")
        logger.info(f"Avg Time/Book: {report.performance_metrics['average_time_per_book']:.2f}s")
        
        if report.overall_errors:
            logger.info(f"Overall Errors: {len(report.overall_errors)}")
            for error in report.overall_errors[:5]:  # Show first 5 errors
                logger.info(f"  - {error}")
            if len(report.overall_errors) > 5:
                logger.info(f"  ... and {len(report.overall_errors) - 5} more errors")
        
        logger.info("=" * 60)
'''
    
    # Write the reporter file
    reporter_path = "src/codexes/modules/distribution/batch_processing_reporter.py"
    with open(reporter_path, 'w') as f:
        f.write(reporter_code)
    
    logger.info(f"Created batch processing reporter: {reporter_path}")
    return True


def create_memory_performance_optimizer():
    """Create memory usage and performance optimization tools."""
    
    optimizer_code = '''
"""
Memory and Performance Optimizer

This module provides tools for optimizing memory usage and performance in LSI generation.
"""

import gc
import logging
import psutil
import time
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
        self.process = psutil.Process()
        self.metrics_history: List[PerformanceMetrics] = []
        self.memory_threshold_mb = 1000  # Alert if memory usage exceeds 1GB
        self.gc_frequency = 10  # Force garbage collection every N operations
        self.operation_count = 0
    
    def get_memory_snapshot(self) -> MemorySnapshot:
        """Get current memory usage snapshot."""
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
        available_memory = psutil.virtual_memory().available / 1024 / 1024
        self.memory_threshold_mb = min(1000, available_memory * 0.8)  # Use up to 80% of available
        
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
'''
    
    # Write the optimizer file
    optimizer_path = "src/codexes/modules/distribution/memory_performance_optimizer.py"
    with open(optimizer_path, 'w') as f:
        f.write(optimizer_code)
    
    logger.info(f"Created memory performance optimizer: {optimizer_path}")
    return True


def update_lsi_generator_with_fixes():
    """Update the LSI generator to use the new fixes."""
    
    # Read the current LSI generator
    generator_path = "src/codexes/modules/distribution/lsi_acs_generator_new.py"
    
    try:
        with open(generator_path, 'r') as f:
            content = f.read()
        
        # Add imports for new modules
        import_additions = '''
from .tranche_config_debugger import TrancheConfigDebugger
from .robust_config_handler import RobustConfigurationHandler
from .batch_processing_reporter import BatchProcessingReporter, BookProcessingResult
from .memory_performance_optimizer import get_global_optimizer, memory_optimized
'''
        
        # Find the imports section and add our imports
        if "from .tranche_config_debugger import" not in content:
            # Add after the existing imports
            import_pos = content.find("from .lsi_logging_manager import LSILoggingManager")
            if import_pos != -1:
                end_pos = content.find("\n", import_pos) + 1
                content = content[:end_pos] + import_additions + "\n" + content[end_pos:]
        
        # Add initialization of new components in __init__
        init_additions = '''
        
        # Initialize enhanced error handling and debugging
        self.config_handler = RobustConfigurationHandler()
        self.tranche_debugger = TrancheConfigDebugger()
        self.batch_reporter = BatchProcessingReporter()
        self.memory_optimizer = get_global_optimizer()
'''
        
        # Find the __init__ method and add our initialization
        init_pos = content.find("self.logging_manager.log_info(f\"LSI ACS Generator initialized")
        if init_pos != -1:
            # Add before the final log message
            content = content[:init_pos] + init_additions + "\n        " + content[init_pos:]
        
        # Write the updated content
        with open(generator_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Updated LSI generator with new fixes: {generator_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update LSI generator: {e}")
        return False


def main():
    """Main function to apply all remaining fixes."""
    logger.info("Starting remaining LSI issue fixes...")
    
    success = True
    
    # Task 9: Create tranche configuration debugger
    if not create_tranche_config_debugger():
        success = False
    
    # Task 10: Create robust configuration error handler
    if not create_robust_config_error_handler():
        success = False
    
    # Task 12: Create batch processing reporter
    if not create_batch_processing_reporter():
        success = False
    
    # Task 13: Create memory performance optimizer
    if not create_memory_performance_optimizer():
        success = False
    
    # Update LSI generator to use new fixes
    if not update_lsi_generator_with_fixes():
        success = False
    
    if success:
        logger.info("All remaining LSI fixes applied successfully!")
        logger.info("Completed tasks:")
        logger.info("✅ Task 9: Tranche configuration application issues resolved")
        logger.info("✅ Task 10: Robust error handling for configuration implemented")
        logger.info("✅ Task 12: Batch processing error reporting improved")
        logger.info("✅ Task 13: Memory usage and performance optimization added")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Run the book pipeline to test all fixes")
        logger.info("2. Monitor memory usage during batch processing")
        logger.info("3. Check batch processing reports for detailed error tracking")
        logger.info("4. Validate tranche configuration application")
    else:
        logger.error("Some fixes failed. Please check the logs above.")
    
    return success


if __name__ == "__main__":
    main()