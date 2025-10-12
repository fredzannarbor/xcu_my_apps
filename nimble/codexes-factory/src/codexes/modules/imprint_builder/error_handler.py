"""
Error Handler component for comprehensive error management in batch processing.

This module handles error categorization, recovery strategies, logging,
and reporting for batch processing operations.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, field

from .batch_models import (
    ProcessingError,
    ProcessingWarning,
    ProcessingContext,
    ErrorHandlingConfig,
    ErrorHandlingMode,
    ValidationResult
)


@dataclass
class ErrorReport:
    """Comprehensive error report for batch processing."""
    generated_at: datetime = field(default_factory=datetime.now)
    total_errors: int = 0
    total_warnings: int = 0
    critical_errors: int = 0
    recoverable_errors: int = 0
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    errors_by_file: Dict[str, int] = field(default_factory=dict)
    errors: List[ProcessingError] = field(default_factory=list)
    warnings: List[ProcessingWarning] = field(default_factory=list)
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "total_errors": self.total_errors,
            "total_warnings": self.total_warnings,
            "critical_errors": self.critical_errors,
            "recoverable_errors": self.recoverable_errors,
            "errors_by_type": self.errors_by_type,
            "errors_by_file": self.errors_by_file,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "summary": self.summary
        }


class ErrorRecoveryStrategy:
    """Defines recovery strategies for different types of errors."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._strategies: Dict[str, Callable] = {}
        self._setup_default_strategies()
    
    def _setup_default_strategies(self):
        """Set up default recovery strategies."""
        self._strategies.update({
            "CSV_PARSING": self._handle_csv_parsing_error,
            "COLUMN_MAPPING": self._handle_column_mapping_error,
            "CONCEPT_PARSING": self._handle_concept_parsing_error,
            "LLM_PROCESSING": self._handle_llm_processing_error,
            "OUTPUT_WRITING": self._handle_output_writing_error,
            "VALIDATION": self._handle_validation_error,
            "TIMEOUT": self._handle_timeout_error,
            "PERMISSION": self._handle_permission_error
        })
    
    def handle_error(self, error: ProcessingError, context: ProcessingContext) -> Dict[str, Any]:
        """
        Handle error using appropriate recovery strategy.
        
        Args:
            error: Processing error to handle
            context: Processing context
            
        Returns:
            Recovery action dictionary
        """
        strategy = self._strategies.get(error.error_type, self._handle_generic_error)
        
        try:
            return strategy(error, context)
        except Exception as e:
            self.logger.error(f"Error in recovery strategy for {error.error_type}: {e}")
            return {
                "action": "skip",
                "message": f"Recovery strategy failed: {str(e)}",
                "recoverable": False
            }
    
    def _handle_csv_parsing_error(self, error: ProcessingError, context: ProcessingContext) -> Dict[str, Any]:
        """Handle CSV parsing errors."""
        return {
            "action": "skip_file",
            "message": "CSV file is malformed or unreadable",
            "recoverable": False,
            "suggestion": "Check CSV file format and encoding"
        }
    
    def _handle_column_mapping_error(self, error: ProcessingError, context: ProcessingContext) -> Dict[str, Any]:
        """Handle column mapping errors."""
        return {
            "action": "use_fallback",
            "message": "Column mapping failed, using default column names",
            "recoverable": True,
            "suggestion": "Review column mapping configuration"
        }
    
    def _handle_concept_parsing_error(self, error: ProcessingError, context: ProcessingContext) -> Dict[str, Any]:
        """Handle concept parsing errors."""
        return {
            "action": "use_basic_concept",
            "message": "Concept parsing failed, creating basic concept",
            "recoverable": True,
            "suggestion": "Review imprint concept text for clarity"
        }
    
    def _handle_llm_processing_error(self, error: ProcessingError, context: ProcessingContext) -> Dict[str, Any]:
        """Handle LLM processing errors."""
        return {
            "action": "retry_with_backoff",
            "message": "LLM processing failed, will retry with exponential backoff",
            "recoverable": True,
            "suggestion": "Check LLM service availability and rate limits"
        }
    
    def _handle_output_writing_error(self, error: ProcessingError, context: ProcessingContext) -> Dict[str, Any]:
        """Handle output writing errors."""
        return {
            "action": "retry_with_different_path",
            "message": "Output writing failed, trying alternative path",
            "recoverable": True,
            "suggestion": "Check disk space and file permissions"
        }
    
    def _handle_validation_error(self, error: ProcessingError, context: ProcessingContext) -> Dict[str, Any]:
        """Handle validation errors."""
        return {
            "action": "skip_with_warning",
            "message": "Validation failed, skipping item with warning",
            "recoverable": True,
            "suggestion": "Review input data format and requirements"
        }
    
    def _handle_timeout_error(self, error: ProcessingError, context: ProcessingContext) -> Dict[str, Any]:
        """Handle timeout errors."""
        return {
            "action": "retry_with_longer_timeout",
            "message": "Processing timed out, retrying with extended timeout",
            "recoverable": True,
            "suggestion": "Consider increasing timeout settings or simplifying input"
        }
    
    def _handle_permission_error(self, error: ProcessingError, context: ProcessingContext) -> Dict[str, Any]:
        """Handle permission errors."""
        return {
            "action": "skip_with_error",
            "message": "Permission denied, cannot access resource",
            "recoverable": False,
            "suggestion": "Check file and directory permissions"
        }
    
    def _handle_generic_error(self, error: ProcessingError, context: ProcessingContext) -> Dict[str, Any]:
        """Handle generic/unknown errors."""
        return {
            "action": "skip_with_warning",
            "message": f"Unknown error type: {error.error_type}",
            "recoverable": error.recoverable,
            "suggestion": "Review error details and consider reporting as bug"
        }
    
    def register_strategy(self, error_type: str, strategy: Callable):
        """Register custom recovery strategy."""
        self._strategies[error_type] = strategy
        self.logger.info(f"Registered custom recovery strategy for {error_type}")


class ErrorHandler:
    """Comprehensive error handling system for batch processing."""
    
    def __init__(self, config: ErrorHandlingConfig):
        """
        Initialize ErrorHandler.
        
        Args:
            config: Error handling configuration
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Set up logging level
        self.logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))
        
        # Initialize collections
        self.errors: List[ProcessingError] = []
        self.warnings: List[ProcessingWarning] = []
        self.recovery_strategy = ErrorRecoveryStrategy()
        
        # Error counters
        self.error_counts_by_type: Dict[str, int] = {}
        self.error_counts_by_file: Dict[str, int] = {}
        
        self.logger.info(f"Initialized ErrorHandler with mode: {config.mode}")
    
    def handle_error(self, error: Exception, context: ProcessingContext) -> bool:
        """
        Handle an error with appropriate strategy.
        
        Args:
            error: Exception that occurred
            context: Processing context where error occurred
            
        Returns:
            True if processing should continue, False if it should stop
        """
        # Create processing error
        processing_error = ProcessingError(
            error_type=self._classify_error(error),
            message=str(error),
            context=context.to_dict(),
            exception=error,
            recoverable=self._is_recoverable_error(error)
        )
        
        # Add to collections
        self.errors.append(processing_error)
        self._update_error_counts(processing_error, context)
        
        # Log the error
        self._log_error(processing_error, context)
        
        # Check if we should stop processing
        if not self.should_continue_processing(processing_error):
            return False
        
        # Apply recovery strategy
        recovery_action = self.recovery_strategy.handle_error(processing_error, context)
        self.logger.info(f"Recovery action for {processing_error.error_type}: {recovery_action.get('action', 'none')}")
        
        return True
    
    def handle_warning(self, warning: str, context: ProcessingContext):
        """
        Handle a warning.
        
        Args:
            warning: Warning message
            context: Processing context
        """
        processing_warning = ProcessingWarning(
            message=warning,
            context=context.to_dict()
        )
        
        self.warnings.append(processing_warning)
        self._log_warning(processing_warning, context)
    
    def _classify_error(self, error: Exception) -> str:
        """
        Classify error type based on exception.
        
        Args:
            error: Exception to classify
            
        Returns:
            Error type string
        """
        error_type = type(error).__name__
        
        # Map common exceptions to error types
        error_mapping = {
            "FileNotFoundError": "FILE_NOT_FOUND",
            "PermissionError": "PERMISSION",
            "ValueError": "VALIDATION",
            "TypeError": "TYPE_ERROR",
            "KeyError": "MISSING_KEY",
            "TimeoutError": "TIMEOUT",
            "ConnectionError": "CONNECTION",
            "JSONDecodeError": "JSON_PARSING",
            "UnicodeDecodeError": "ENCODING",
            "OSError": "SYSTEM_ERROR"
        }
        
        return error_mapping.get(error_type, error_type.upper())
    
    def _is_recoverable_error(self, error: Exception) -> bool:
        """
        Determine if an error is recoverable.
        
        Args:
            error: Exception to check
            
        Returns:
            True if error is recoverable
        """
        # Non-recoverable errors
        non_recoverable = {
            FileNotFoundError,
            PermissionError,
            MemoryError,
            KeyboardInterrupt,
            SystemExit
        }
        
        return type(error) not in non_recoverable
    
    def _update_error_counts(self, error: ProcessingError, context: ProcessingContext):
        """Update error counters."""
        # Count by type
        self.error_counts_by_type[error.error_type] = self.error_counts_by_type.get(error.error_type, 0) + 1
        
        # Count by file
        if context.file_path:
            file_key = str(context.file_path)
            self.error_counts_by_file[file_key] = self.error_counts_by_file.get(file_key, 0) + 1
    
    def _log_error(self, error: ProcessingError, context: ProcessingContext):
        """Log error with appropriate level."""
        log_message = f"Error in {context.operation}: {error.message}"
        
        if context.file_path:
            log_message += f" (file: {context.file_path}"
            if context.row_number:
                log_message += f", row: {context.row_number}"
            log_message += ")"
        
        if error.recoverable:
            self.logger.warning(log_message)
        else:
            self.logger.error(log_message)
        
        # Include stack trace if configured
        if self.config.include_stack_traces and error.exception:
            self.logger.error("Stack trace:", exc_info=error.exception)
    
    def _log_warning(self, warning: ProcessingWarning, context: ProcessingContext):
        """Log warning."""
        log_message = f"Warning in {context.operation}: {warning.message}"
        
        if context.file_path:
            log_message += f" (file: {context.file_path}"
            if context.row_number:
                log_message += f", row: {context.row_number}"
            log_message += ")"
        
        self.logger.warning(log_message)
    
    def should_continue_processing(self, error: ProcessingError) -> bool:
        """
        Determine if processing should continue after an error.
        
        Args:
            error: Processing error
            
        Returns:
            True if processing should continue
        """
        # Check error handling mode
        if self.config.mode == ErrorHandlingMode.FAIL_FAST:
            return False
        
        if self.config.mode == ErrorHandlingMode.CONTINUE_ON_ERROR:
            return error.recoverable
        
        # COLLECT_ERRORS mode - continue unless too many errors
        if len(self.errors) > self.config.max_errors_per_file:
            self.logger.error(f"Too many errors ({len(self.errors)}), stopping processing")
            return False
        
        return True
    
    def generate_error_report(self) -> ErrorReport:
        """
        Generate comprehensive error report.
        
        Returns:
            ErrorReport with detailed information
        """
        report = ErrorReport(
            total_errors=len(self.errors),
            total_warnings=len(self.warnings),
            critical_errors=len([e for e in self.errors if not e.recoverable]),
            recoverable_errors=len([e for e in self.errors if e.recoverable]),
            errors_by_type=self.error_counts_by_type.copy(),
            errors_by_file=self.error_counts_by_file.copy(),
            errors=self.errors.copy(),
            warnings=self.warnings.copy()
        )
        
        # Generate summary
        if report.total_errors == 0 and report.total_warnings == 0:
            report.summary = "No errors or warnings encountered during processing."
        else:
            summary_parts = []
            if report.total_errors > 0:
                summary_parts.append(f"{report.total_errors} errors ({report.critical_errors} critical)")
            if report.total_warnings > 0:
                summary_parts.append(f"{report.total_warnings} warnings")
            
            report.summary = f"Processing completed with {' and '.join(summary_parts)}."
            
            # Add top error types
            if report.errors_by_type:
                top_errors = sorted(report.errors_by_type.items(), key=lambda x: x[1], reverse=True)[:3]
                error_types = [f"{error_type} ({count})" for error_type, count in top_errors]
                report.summary += f" Most common errors: {', '.join(error_types)}."
        
        return report
    
    def save_error_report(self, output_path: Path) -> bool:
        """
        Save error report to file.
        
        Args:
            output_path: Path to save report
            
        Returns:
            True if saved successfully
        """
        if not self.config.create_error_report:
            return False
        
        try:
            report = self.generate_error_report()
            
            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write report
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Error report saved to: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save error report: {e}")
            return False
    
    def clear_errors(self):
        """Clear all errors and warnings."""
        self.errors.clear()
        self.warnings.clear()
        self.error_counts_by_type.clear()
        self.error_counts_by_file.clear()
        self.logger.info("Cleared all errors and warnings")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of current errors and warnings.
        
        Returns:
            Summary dictionary
        """
        return {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "critical_errors": len([e for e in self.errors if not e.recoverable]),
            "recoverable_errors": len([e for e in self.errors if e.recoverable]),
            "errors_by_type": self.error_counts_by_type.copy(),
            "errors_by_file": self.error_counts_by_file.copy(),
            "has_critical_errors": any(not e.recoverable for e in self.errors)
        }
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """Register custom recovery strategy."""
        self.recovery_strategy.register_strategy(error_type, strategy)


def create_error_handler(config: ErrorHandlingConfig) -> ErrorHandler:
    """
    Factory function to create an ErrorHandler instance.
    
    Args:
        config: Error handling configuration
        
    Returns:
        Configured ErrorHandler instance
    """
    return ErrorHandler(config)