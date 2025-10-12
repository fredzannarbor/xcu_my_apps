#!/usr/bin/env python3

"""
Enhanced Logging and Debugging System

This module provides comprehensive logging and debugging capabilities for LSI CSV generation,
including structured logging, performance monitoring, and debug mode functionality.
"""

import json
import logging
import logging.handlers
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps
import threading
from contextlib import contextmanager

# Performance monitoring
import psutil
import os


class LogLevel(Enum):
    """Enhanced log levels."""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LogCategory(Enum):
    """Log categories for better organization."""
    SYSTEM = "system"
    VALIDATION = "validation"
    FIELD_COMPLETION = "field_completion"
    CONFIGURATION = "configuration"
    BATCH_PROCESSING = "batch_processing"
    PERFORMANCE = "performance"
    LLM_INTERACTION = "llm_interaction"
    DATA_TRANSFORMATION = "data_transformation"


@dataclass
class LogContext:
    """Context information for structured logging."""
    operation: str
    book_id: Optional[str] = None
    field_name: Optional[str] = None
    batch_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceMetric:
    """Performance metric data."""
    operation: str
    duration: float
    memory_usage_mb: float
    cpu_percent: float
    timestamp: datetime
    context: Optional[LogContext] = None


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record):
        """Format log record as structured JSON."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add context information if available
        if hasattr(record, 'context') and record.context:
            log_entry['context'] = asdict(record.context)
        
        # Add category if available
        if hasattr(record, 'category'):
            log_entry['category'] = record.category.value if isinstance(record.category, LogCategory) else record.category
        
        # Add performance metrics if available
        if hasattr(record, 'performance'):
            log_entry['performance'] = asdict(record.performance)
        
        # Add exception information
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add stack trace for errors
        if record.levelno >= logging.ERROR and not record.exc_info:
            log_entry['stack_trace'] = traceback.format_stack()
        
        return json.dumps(log_entry, default=str)


class EnhancedLogger:
    """Enhanced logger with structured logging and debugging capabilities."""
    
    def __init__(self, name: str, log_dir: str = "logs", debug_mode: bool = False):
        """Initialize enhanced logger."""
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.debug_mode = debug_mode
        self.performance_metrics: List[PerformanceMetric] = []
        self._setup_loggers()
        self._context_stack = []
        self._lock = threading.RLock()
    
    def _setup_loggers(self):
        """Set up different loggers for different purposes."""
        # Main application logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(LogLevel.TRACE.value if self.debug_mode else LogLevel.INFO.value)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LogLevel.DEBUG.value if self.debug_mode else LogLevel.INFO.value)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for all logs
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(LogLevel.TRACE.value)
        file_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(file_handler)
        
        # Error-only file handler
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}_errors.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(LogLevel.ERROR.value)
        error_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(error_handler)
        
        # Performance metrics logger
        self.perf_logger = logging.getLogger(f"{self.name}.performance")
        self.perf_logger.setLevel(LogLevel.INFO.value)
        perf_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}_performance.log",
            maxBytes=5*1024*1024,
            backupCount=3
        )
        perf_handler.setFormatter(StructuredFormatter())
        self.perf_logger.addHandler(perf_handler)
        
        # Debug logger (only active in debug mode)
        if self.debug_mode:
            self.debug_logger = logging.getLogger(f"{self.name}.debug")
            self.debug_logger.setLevel(LogLevel.TRACE.value)
            debug_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / f"{self.name}_debug.log",
                maxBytes=20*1024*1024,  # 20MB for debug logs
                backupCount=2
            )
            debug_handler.setFormatter(StructuredFormatter())
            self.debug_logger.addHandler(debug_handler)\n    \n    def trace(self, message: str, context: LogContext = None, category: LogCategory = None, **kwargs):\n        \"\"\"Log trace level message.\"\"\"\n        self._log(LogLevel.TRACE.value, message, context, category, **kwargs)\n    \n    def debug(self, message: str, context: LogContext = None, category: LogCategory = None, **kwargs):\n        \"\"\"Log debug level message.\"\"\"\n        self._log(LogLevel.DEBUG.value, message, context, category, **kwargs)\n    \n    def info(self, message: str, context: LogContext = None, category: LogCategory = None, **kwargs):\n        \"\"\"Log info level message.\"\"\"\n        self._log(LogLevel.INFO.value, message, context, category, **kwargs)\n    \n    def warning(self, message: str, context: LogContext = None, category: LogCategory = None, **kwargs):\n        \"\"\"Log warning level message.\"\"\"\n        self._log(LogLevel.WARNING.value, message, context, category, **kwargs)\n    \n    def error(self, message: str, context: LogContext = None, category: LogCategory = None, \n             exc_info: bool = True, **kwargs):\n        \"\"\"Log error level message.\"\"\"\n        self._log(LogLevel.ERROR.value, message, context, category, exc_info=exc_info, **kwargs)\n    \n    def critical(self, message: str, context: LogContext = None, category: LogCategory = None, \n                exc_info: bool = True, **kwargs):\n        \"\"\"Log critical level message.\"\"\"\n        self._log(LogLevel.CRITICAL.value, message, context, category, exc_info=exc_info, **kwargs)\n    \n    def _log(self, level: int, message: str, context: LogContext = None, \n            category: LogCategory = None, exc_info: bool = False, **kwargs):\n        \"\"\"Internal logging method.\"\"\"\n        # Get current context if none provided\n        if context is None and self._context_stack:\n            context = self._context_stack[-1]\n        \n        # Create log record\n        record = self.logger.makeRecord(\n            self.logger.name, level, \"\", 0, message, (), \n            exc_info if exc_info else None\n        )\n        \n        # Add context and category\n        if context:\n            record.context = context\n        if category:\n            record.category = category\n        \n        # Add additional data\n        for key, value in kwargs.items():\n            setattr(record, key, value)\n        \n        # Log to appropriate logger\n        if level >= LogLevel.ERROR.value:\n            self.logger.handle(record)\n        elif self.debug_mode and hasattr(self, 'debug_logger'):\n            self.debug_logger.handle(record)\n        else:\n            self.logger.handle(record)\n    \n    @contextmanager\n    def context(self, context: LogContext):\n        \"\"\"Context manager for logging context.\"\"\"\n        with self._lock:\n            self._context_stack.append(context)\n        try:\n            yield\n        finally:\n            with self._lock:\n                if self._context_stack:\n                    self._context_stack.pop()\n    \n    def log_performance(self, operation: str, duration: float, \n                       context: LogContext = None, **metrics):\n        \"\"\"Log performance metrics.\"\"\"\n        # Get system metrics\n        process = psutil.Process()\n        memory_info = process.memory_info()\n        cpu_percent = process.cpu_percent()\n        \n        perf_metric = PerformanceMetric(\n            operation=operation,\n            duration=duration,\n            memory_usage_mb=memory_info.rss / 1024 / 1024,\n            cpu_percent=cpu_percent,\n            timestamp=datetime.now(),\n            context=context\n        )\n        \n        self.performance_metrics.append(perf_metric)\n        \n        # Log performance data\n        perf_record = self.perf_logger.makeRecord(\n            self.perf_logger.name, LogLevel.INFO.value, \"\", 0,\n            f\"Performance: {operation}\", (), None\n        )\n        perf_record.performance = perf_metric\n        if context:\n            perf_record.context = context\n        \n        # Add custom metrics\n        for key, value in metrics.items():\n            setattr(perf_record, key, value)\n        \n        self.perf_logger.handle(perf_record)\n    \n    def log_llm_interaction(self, prompt: str, response: str, model: str, \n                           duration: float, context: LogContext = None):\n        \"\"\"Log LLM interaction details.\"\"\"\n        llm_context = LogContext(\n            operation=\"llm_interaction\",\n            additional_data={\n                \"model\": model,\n                \"prompt_length\": len(prompt),\n                \"response_length\": len(response),\n                \"duration\": duration\n            }\n        )\n        \n        if context:\n            llm_context.book_id = context.book_id\n            llm_context.field_name = context.field_name\n            llm_context.batch_id = context.batch_id\n        \n        self.info(\n            f\"LLM interaction completed: {model}\",\n            context=llm_context,\n            category=LogCategory.LLM_INTERACTION,\n            prompt_preview=prompt[:200] + \"...\" if len(prompt) > 200 else prompt,\n            response_preview=response[:200] + \"...\" if len(response) > 200 else response\n        )\n        \n        # Log full interaction in debug mode\n        if self.debug_mode:\n            self.debug(\n                f\"Full LLM interaction: {model}\",\n                context=llm_context,\n                category=LogCategory.LLM_INTERACTION,\n                full_prompt=prompt,\n                full_response=response\n            )\n    \n    def log_validation_result(self, field_name: str, is_valid: bool, \n                            issues: List[str], context: LogContext = None):\n        \"\"\"Log field validation results.\"\"\"\n        validation_context = LogContext(\n            operation=\"field_validation\",\n            field_name=field_name,\n            additional_data={\n                \"is_valid\": is_valid,\n                \"issue_count\": len(issues)\n            }\n        )\n        \n        if context:\n            validation_context.book_id = context.book_id\n            validation_context.batch_id = context.batch_id\n        \n        if is_valid:\n            self.debug(\n                f\"Field validation passed: {field_name}\",\n                context=validation_context,\n                category=LogCategory.VALIDATION\n            )\n        else:\n            self.warning(\n                f\"Field validation failed: {field_name}\",\n                context=validation_context,\n                category=LogCategory.VALIDATION,\n                validation_issues=issues\n            )\n    \n    def log_batch_progress(self, batch_id: str, processed: int, total: int, \n                          success_count: int, error_count: int):\n        \"\"\"Log batch processing progress.\"\"\"\n        progress_percent = (processed / total * 100) if total > 0 else 0\n        success_rate = (success_count / processed * 100) if processed > 0 else 0\n        \n        batch_context = LogContext(\n            operation=\"batch_processing\",\n            batch_id=batch_id,\n            additional_data={\n                \"processed\": processed,\n                \"total\": total,\n                \"success_count\": success_count,\n                \"error_count\": error_count,\n                \"progress_percent\": progress_percent,\n                \"success_rate\": success_rate\n            }\n        )\n        \n        self.info(\n            f\"Batch progress: {processed}/{total} ({progress_percent:.1f}%) - \"\n            f\"Success rate: {success_rate:.1f}%\",\n            context=batch_context,\n            category=LogCategory.BATCH_PROCESSING\n        )\n    \n    def get_performance_summary(self, operation_filter: str = None) -> Dict[str, Any]:\n        \"\"\"Get performance metrics summary.\"\"\"\n        metrics = self.performance_metrics\n        if operation_filter:\n            metrics = [m for m in metrics if operation_filter in m.operation]\n        \n        if not metrics:\n            return {}\n        \n        durations = [m.duration for m in metrics]\n        memory_usage = [m.memory_usage_mb for m in metrics]\n        \n        return {\n            \"total_operations\": len(metrics),\n            \"average_duration\": sum(durations) / len(durations),\n            \"min_duration\": min(durations),\n            \"max_duration\": max(durations),\n            \"average_memory_mb\": sum(memory_usage) / len(memory_usage),\n            \"max_memory_mb\": max(memory_usage),\n            \"operations_by_type\": self._group_operations_by_type(metrics)\n        }\n    \n    def _group_operations_by_type(self, metrics: List[PerformanceMetric]) -> Dict[str, Dict[str, float]]:\n        \"\"\"Group performance metrics by operation type.\"\"\"\n        grouped = {}\n        for metric in metrics:\n            if metric.operation not in grouped:\n                grouped[metric.operation] = {\n                    \"count\": 0,\n                    \"total_duration\": 0,\n                    \"total_memory\": 0\n                }\n            \n            grouped[metric.operation][\"count\"] += 1\n            grouped[metric.operation][\"total_duration\"] += metric.duration\n            grouped[metric.operation][\"total_memory\"] += metric.memory_usage_mb\n        \n        # Calculate averages\n        for operation, data in grouped.items():\n            count = data[\"count\"]\n            data[\"average_duration\"] = data[\"total_duration\"] / count\n            data[\"average_memory\"] = data[\"total_memory\"] / count\n        \n        return grouped\n    \n    def export_logs(self, start_time: datetime = None, end_time: datetime = None, \n                   categories: List[LogCategory] = None) -> str:\n        \"\"\"Export logs for analysis.\"\"\"\n        # This would implement log export functionality\n        # For now, return a placeholder\n        return f\"Log export functionality - would export logs from {start_time} to {end_time}\"\n\n\ndef performance_monitor(operation_name: str, logger: EnhancedLogger = None):\n    \"\"\"Decorator to monitor function performance.\"\"\"\n    def decorator(func: Callable) -> Callable:\n        @wraps(func)\n        def wrapper(*args, **kwargs):\n            start_time = time.time()\n            \n            try:\n                result = func(*args, **kwargs)\n                duration = time.time() - start_time\n                \n                if logger:\n                    logger.log_performance(operation_name, duration)\n                \n                return result\n            except Exception as e:\n                duration = time.time() - start_time\n                \n                if logger:\n                    logger.log_performance(operation_name, duration, error=str(e))\n                    logger.error(f\"Error in {operation_name}: {e}\")\n                \n                raise\n        \n        return wrapper\n    return decorator\n\n\nclass DebugManager:\n    \"\"\"Manager for debug mode functionality.\"\"\"\n    \n    def __init__(self, logger: EnhancedLogger):\n        self.logger = logger\n        self.debug_data = {}\n        self.breakpoints = set()\n    \n    def set_breakpoint(self, operation: str):\n        \"\"\"Set a debug breakpoint.\"\"\"\n        self.breakpoints.add(operation)\n        self.logger.debug(f\"Debug breakpoint set: {operation}\")\n    \n    def check_breakpoint(self, operation: str) -> bool:\n        \"\"\"Check if operation has a breakpoint.\"\"\"\n        return operation in self.breakpoints\n    \n    def capture_debug_data(self, operation: str, data: Dict[str, Any]):\n        \"\"\"Capture debug data for analysis.\"\"\"\n        if operation not in self.debug_data:\n            self.debug_data[operation] = []\n        \n        self.debug_data[operation].append({\n            \"timestamp\": datetime.now(),\n            \"data\": data\n        })\n        \n        self.logger.trace(f\"Debug data captured for {operation}\", \n                         additional_data=data)\n    \n    def get_debug_data(self, operation: str = None) -> Dict[str, Any]:\n        \"\"\"Get captured debug data.\"\"\"\n        if operation:\n            return self.debug_data.get(operation, [])\n        return self.debug_data\n    \n    def clear_debug_data(self, operation: str = None):\n        \"\"\"Clear debug data.\"\"\"\n        if operation:\n            self.debug_data.pop(operation, None)\n        else:\n            self.debug_data.clear()\n        \n        self.logger.debug(f\"Debug data cleared: {operation or 'all'}\")\n\n\n# Global logger instances\n_loggers = {}\n_lock = threading.Lock()\n\n\ndef get_enhanced_logger(name: str, debug_mode: bool = False) -> EnhancedLogger:\n    \"\"\"Get or create an enhanced logger instance.\"\"\"\n    with _lock:\n        if name not in _loggers:\n            _loggers[name] = EnhancedLogger(name, debug_mode=debug_mode)\n        return _loggers[name]\n\n\ndef setup_logging(debug_mode: bool = False, log_dir: str = \"logs\"):\n    \"\"\"Set up enhanced logging for the application.\"\"\"\n    # Create main application logger\n    app_logger = get_enhanced_logger(\"lsi_csv_generator\", debug_mode)\n    \n    # Set up category-specific loggers\n    validation_logger = get_enhanced_logger(\"validation\", debug_mode)\n    field_completion_logger = get_enhanced_logger(\"field_completion\", debug_mode)\n    batch_processing_logger = get_enhanced_logger(\"batch_processing\", debug_mode)\n    \n    return {\n        \"app\": app_logger,\n        \"validation\": validation_logger,\n        \"field_completion\": field_completion_logger,\n        \"batch_processing\": batch_processing_logger\n    }\n\n\n# Context managers for common logging scenarios\n@contextmanager\ndef log_operation(logger: EnhancedLogger, operation: str, \n                 context: LogContext = None, **kwargs):\n    \"\"\"Context manager for logging operations with timing.\"\"\"\n    start_time = time.time()\n    \n    op_context = context or LogContext(operation=operation)\n    \n    logger.info(f\"Starting operation: {operation}\", context=op_context, **kwargs)\n    \n    try:\n        yield\n        duration = time.time() - start_time\n        logger.info(f\"Completed operation: {operation} ({duration:.2f}s)\", \n                   context=op_context)\n        logger.log_performance(operation, duration, context=op_context)\n    except Exception as e:\n        duration = time.time() - start_time\n        logger.error(f\"Failed operation: {operation} ({duration:.2f}s) - {e}\", \n                    context=op_context)\n        logger.log_performance(operation, duration, context=op_context, error=str(e))\n        raise\n\n\n@contextmanager\ndef log_batch_operation(logger: EnhancedLogger, batch_id: str, total_items: int):\n    \"\"\"Context manager for batch operations.\"\"\"\n    batch_context = LogContext(operation=\"batch_processing\", batch_id=batch_id)\n    \n    logger.info(f\"Starting batch: {batch_id} ({total_items} items)\", \n               context=batch_context, category=LogCategory.BATCH_PROCESSING)\n    \n    start_time = time.time()\n    \n    try:\n        yield\n        duration = time.time() - start_time\n        logger.info(f\"Completed batch: {batch_id} ({duration:.2f}s)\", \n                   context=batch_context, category=LogCategory.BATCH_PROCESSING)\n    except Exception as e:\n        duration = time.time() - start_time\n        logger.error(f\"Failed batch: {batch_id} ({duration:.2f}s) - {e}\", \n                    context=batch_context, category=LogCategory.BATCH_PROCESSING)\n        raise