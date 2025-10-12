"""
Unit tests for ErrorHandler component.
"""

import pytest
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.imprint_builder.error_handler import (
    ErrorHandler, 
    ErrorRecoveryStrategy, 
    ErrorReport,
    create_error_handler
)
from codexes.modules.imprint_builder.batch_models import (
    ErrorHandlingConfig,
    ErrorHandlingMode,
    ProcessingError,
    ProcessingWarning,
    ProcessingContext
)


class TestErrorRecoveryStrategy:
    """Test ErrorRecoveryStrategy functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = ErrorRecoveryStrategy()
    
    def test_initialization(self):
        """Test ErrorRecoveryStrategy initialization."""
        assert len(self.strategy._strategies) > 0
        assert "CSV_PARSING" in self.strategy._strategies
        assert "LLM_PROCESSING" in self.strategy._strategies
    
    def test_handle_csv_parsing_error(self):
        """Test CSV parsing error handling."""
        error = ProcessingError(
            error_type="CSV_PARSING",
            message="Invalid CSV format",
            context={}
        )
        context = ProcessingContext(operation="csv_reading")
        
        result = self.strategy.handle_error(error, context)
        
        assert result["action"] == "skip_file"
        assert result["recoverable"] is False
        assert "suggestion" in result
    
    def test_handle_llm_processing_error(self):
        """Test LLM processing error handling."""
        error = ProcessingError(
            error_type="LLM_PROCESSING",
            message="LLM service unavailable",
            context={}
        )
        context = ProcessingContext(operation="llm_expansion")
        
        result = self.strategy.handle_error(error, context)
        
        assert result["action"] == "retry_with_backoff"
        assert result["recoverable"] is True
    
    def test_handle_unknown_error(self):
        """Test handling of unknown error types."""
        error = ProcessingError(
            error_type="UNKNOWN_ERROR",
            message="Something went wrong",
            context={}
        )
        context = ProcessingContext(operation="unknown")
        
        result = self.strategy.handle_error(error, context)
        
        assert result["action"] == "skip_with_warning"
        assert "Unknown error type" in result["message"]
    
    def test_register_custom_strategy(self):
        """Test registering custom recovery strategy."""
        def custom_strategy(error, context):
            return {"action": "custom_action", "recoverable": True}
        
        self.strategy.register_strategy("CUSTOM_ERROR", custom_strategy)
        
        error = ProcessingError(
            error_type="CUSTOM_ERROR",
            message="Custom error",
            context={}
        )
        context = ProcessingContext(operation="custom")
        
        result = self.strategy.handle_error(error, context)
        assert result["action"] == "custom_action"
    
    def test_strategy_exception_handling(self):
        """Test handling of exceptions in recovery strategies."""
        def failing_strategy(error, context):
            raise Exception("Strategy failed")
        
        self.strategy.register_strategy("FAILING_ERROR", failing_strategy)
        
        error = ProcessingError(
            error_type="FAILING_ERROR",
            message="This will fail",
            context={}
        )
        context = ProcessingContext(operation="failing")
        
        result = self.strategy.handle_error(error, context)
        
        assert result["action"] == "skip"
        assert result["recoverable"] is False
        assert "Recovery strategy failed" in result["message"]


class TestErrorHandler:
    """Test ErrorHandler functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ErrorHandlingConfig(
            mode=ErrorHandlingMode.CONTINUE_ON_ERROR,
            log_level="INFO",
            create_error_report=True,
            include_stack_traces=False,
            max_errors_per_file=10
        )
        self.error_handler = ErrorHandler(self.config)
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            for item in self.temp_dir.iterdir():
                if item.is_file():
                    item.unlink()
            self.temp_dir.rmdir()
    
    def test_initialization(self):
        """Test ErrorHandler initialization."""
        assert self.error_handler.config == self.config
        assert len(self.error_handler.errors) == 0
        assert len(self.error_handler.warnings) == 0
        assert isinstance(self.error_handler.recovery_strategy, ErrorRecoveryStrategy)
    
    def test_classify_error(self):
        """Test error classification."""
        # Test common exceptions
        assert self.error_handler._classify_error(FileNotFoundError()) == "FILE_NOT_FOUND"
        assert self.error_handler._classify_error(PermissionError()) == "PERMISSION"
        assert self.error_handler._classify_error(ValueError()) == "VALIDATION"
        assert self.error_handler._classify_error(TimeoutError()) == "TIMEOUT"
        
        # Test unknown exception
        class CustomError(Exception):
            pass
        
        assert self.error_handler._classify_error(CustomError()) == "CUSTOMERROR"
    
    def test_is_recoverable_error(self):
        """Test recoverable error detection."""
        # Recoverable errors
        assert self.error_handler._is_recoverable_error(ValueError()) is True
        assert self.error_handler._is_recoverable_error(TypeError()) is True
        
        # Non-recoverable errors
        assert self.error_handler._is_recoverable_error(FileNotFoundError()) is False
        assert self.error_handler._is_recoverable_error(PermissionError()) is False
        assert self.error_handler._is_recoverable_error(MemoryError()) is False
    
    def test_handle_error(self):
        """Test error handling."""
        context = ProcessingContext(
            operation="test_operation",
            file_path=Path("test.csv"),
            row_number=5
        )
        
        error = ValueError("Test error")
        
        # Handle error
        should_continue = self.error_handler.handle_error(error, context)
        
        # Verify error was recorded
        assert len(self.error_handler.errors) == 1
        assert self.error_handler.errors[0].error_type == "VALIDATION"
        assert self.error_handler.errors[0].message == "Test error"
        assert should_continue is True
        
        # Verify counters were updated
        assert self.error_handler.error_counts_by_type["VALIDATION"] == 1
        assert self.error_handler.error_counts_by_file["test.csv"] == 1
    
    def test_handle_warning(self):
        """Test warning handling."""
        context = ProcessingContext(
            operation="test_operation",
            file_path=Path("test.csv")
        )
        
        self.error_handler.handle_warning("Test warning", context)
        
        # Verify warning was recorded
        assert len(self.error_handler.warnings) == 1
        assert self.error_handler.warnings[0].message == "Test warning"
    
    def test_should_continue_processing_fail_fast(self):
        """Test fail fast mode."""
        config = ErrorHandlingConfig(mode=ErrorHandlingMode.FAIL_FAST)
        handler = ErrorHandler(config)
        
        error = ProcessingError(
            error_type="TEST",
            message="Test error",
            context={},
            recoverable=True
        )
        
        # Should not continue in fail fast mode
        assert handler.should_continue_processing(error) is False
    
    def test_should_continue_processing_continue_on_error(self):
        """Test continue on error mode."""
        config = ErrorHandlingConfig(mode=ErrorHandlingMode.CONTINUE_ON_ERROR)
        handler = ErrorHandler(config)
        
        # Recoverable error - should continue
        recoverable_error = ProcessingError(
            error_type="TEST",
            message="Recoverable error",
            context={},
            recoverable=True
        )
        assert handler.should_continue_processing(recoverable_error) is True
        
        # Non-recoverable error - should not continue
        non_recoverable_error = ProcessingError(
            error_type="TEST",
            message="Non-recoverable error",
            context={},
            recoverable=False
        )
        assert handler.should_continue_processing(non_recoverable_error) is False
    
    def test_should_continue_processing_collect_errors(self):
        """Test collect errors mode with max limit."""
        config = ErrorHandlingConfig(
            mode=ErrorHandlingMode.COLLECT_ERRORS,
            max_errors_per_file=2
        )
        handler = ErrorHandler(config)
        
        # Add errors up to limit
        for i in range(2):
            handler.errors.append(ProcessingError(
                error_type="TEST",
                message=f"Error {i}",
                context={}
            ))
        
        # Should continue at limit
        error = ProcessingError(
            error_type="TEST",
            message="At limit",
            context={}
        )
        assert handler.should_continue_processing(error) is True
        
        # Add one more to exceed limit
        handler.errors.append(error)
        
        # Should not continue when over limit
        another_error = ProcessingError(
            error_type="TEST",
            message="Over limit",
            context={}
        )
        assert handler.should_continue_processing(another_error) is False
    
    def test_generate_error_report_empty(self):
        """Test error report generation with no errors."""
        report = self.error_handler.generate_error_report()
        
        assert isinstance(report, ErrorReport)
        assert report.total_errors == 0
        assert report.total_warnings == 0
        assert "No errors or warnings" in report.summary
    
    def test_generate_error_report_with_errors(self):
        """Test error report generation with errors and warnings."""
        # Add some errors
        context = ProcessingContext(operation="test")
        
        self.error_handler.handle_error(ValueError("Error 1"), context)
        self.error_handler.handle_error(TypeError("Error 2"), context)
        self.error_handler.handle_warning("Warning 1", context)
        
        report = self.error_handler.generate_error_report()
        
        assert report.total_errors == 2
        assert report.total_warnings == 1
        assert report.recoverable_errors == 2  # ValueError and TypeError are recoverable
        assert report.critical_errors == 0
        assert len(report.errors) == 2
        assert len(report.warnings) == 1
        assert "2 errors" in report.summary
        assert "1 warnings" in report.summary
    
    def test_save_error_report(self):
        """Test saving error report to file."""
        # Add some errors
        context = ProcessingContext(operation="test")
        self.error_handler.handle_error(ValueError("Test error"), context)
        
        # Save report
        report_path = self.temp_dir / "error_report.json"
        success = self.error_handler.save_error_report(report_path)
        
        assert success is True
        assert report_path.exists()
        
        # Verify content
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        assert data["total_errors"] == 1
        assert data["total_warnings"] == 0
        assert len(data["errors"]) == 1
    
    def test_save_error_report_disabled(self):
        """Test saving error report when disabled."""
        config = ErrorHandlingConfig(create_error_report=False)
        handler = ErrorHandler(config)
        
        report_path = self.temp_dir / "error_report.json"
        success = handler.save_error_report(report_path)
        
        assert success is False
        assert not report_path.exists()
    
    def test_clear_errors(self):
        """Test clearing errors and warnings."""
        # Add some errors and warnings
        context = ProcessingContext(operation="test")
        self.error_handler.handle_error(ValueError("Error"), context)
        self.error_handler.handle_warning("Warning", context)
        
        # Verify they exist
        assert len(self.error_handler.errors) == 1
        assert len(self.error_handler.warnings) == 1
        assert len(self.error_handler.error_counts_by_type) == 1
        
        # Clear them
        self.error_handler.clear_errors()
        
        # Verify they're gone
        assert len(self.error_handler.errors) == 0
        assert len(self.error_handler.warnings) == 0
        assert len(self.error_handler.error_counts_by_type) == 0
        assert len(self.error_handler.error_counts_by_file) == 0
    
    def test_get_error_summary(self):
        """Test getting error summary."""
        # Add mixed errors
        context = ProcessingContext(operation="test", file_path=Path("test.csv"))
        
        self.error_handler.handle_error(ValueError("Recoverable"), context)
        self.error_handler.handle_error(FileNotFoundError("Non-recoverable"), context)
        self.error_handler.handle_warning("Warning", context)
        
        summary = self.error_handler.get_error_summary()
        
        assert summary["total_errors"] == 2
        assert summary["total_warnings"] == 1
        assert summary["critical_errors"] == 1  # FileNotFoundError is non-recoverable
        assert summary["recoverable_errors"] == 1  # ValueError is recoverable
        assert summary["has_critical_errors"] is True
        assert "VALIDATION" in summary["errors_by_type"]
        assert "FILE_NOT_FOUND" in summary["errors_by_type"]
        assert "test.csv" in summary["errors_by_file"]
    
    def test_register_recovery_strategy(self):
        """Test registering custom recovery strategy."""
        def custom_strategy(error, context):
            return {"action": "custom", "recoverable": True}
        
        self.error_handler.register_recovery_strategy("CUSTOM", custom_strategy)
        
        # Verify it was registered
        assert "CUSTOM" in self.error_handler.recovery_strategy._strategies


class TestErrorReport:
    """Test ErrorReport functionality."""
    
    def test_error_report_to_dict(self):
        """Test ErrorReport serialization."""
        error = ProcessingError(
            error_type="TEST",
            message="Test error",
            context={}
        )
        warning = ProcessingWarning(
            message="Test warning",
            context={}
        )
        
        report = ErrorReport(
            total_errors=1,
            total_warnings=1,
            critical_errors=0,
            recoverable_errors=1,
            errors=[error],
            warnings=[warning],
            summary="Test summary"
        )
        
        data = report.to_dict()
        
        assert data["total_errors"] == 1
        assert data["total_warnings"] == 1
        assert data["critical_errors"] == 0
        assert data["recoverable_errors"] == 1
        assert len(data["errors"]) == 1
        assert len(data["warnings"]) == 1
        assert data["summary"] == "Test summary"
        assert "generated_at" in data


class TestFactoryFunction:
    """Test factory function."""
    
    def test_create_error_handler(self):
        """Test creating ErrorHandler with factory function."""
        config = ErrorHandlingConfig()
        handler = create_error_handler(config)
        
        assert isinstance(handler, ErrorHandler)
        assert handler.config == config


if __name__ == "__main__":
    pytest.main([__file__])