# tests/test_lsi_logging_manager.py

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from codexes.modules.distribution.lsi_logging_manager import (
    LSILoggingManager, FieldMappingLog, ValidationLog, GenerationSession
)
from codexes.modules.metadata.metadata_models import CodexMetadata
from codexes.modules.verifiers.validation_framework import (
    ValidationResult, FieldValidationResult, ValidationSeverity
)


class TestLSILoggingManager:
    """Test suite for LSILoggingManager class"""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary directory for logging tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def logging_manager(self, temp_log_dir):
        """Create LSILoggingManager instance for testing"""
        return LSILoggingManager(temp_log_dir)
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata for testing"""
        return CodexMetadata(
            title="Test Book Title",
            author="Test Author",
            isbn13="9781234567897",
            publisher="Test Publisher",
            imprint="Test Imprint"
        )
    
    def test_initialization(self, logging_manager, temp_log_dir):
        """Test LSILoggingManager initialization"""
        assert logging_manager is not None
        assert logging_manager.log_directory == Path(temp_log_dir)
        assert logging_manager.log_directory.exists()
        assert logging_manager.current_session is None
        assert hasattr(logging_manager, 'logger')
    
    def test_start_generation_session(self, logging_manager, sample_metadata):
        """Test starting a generation session"""
        output_path = "/test/output.csv"
        
        session_id = logging_manager.start_generation_session(sample_metadata, output_path)
        
        assert session_id is not None
        assert session_id.startswith("lsi_gen_")
        assert logging_manager.current_session is not None
        assert logging_manager.current_session.session_id == session_id
        assert logging_manager.current_session.output_file_path == output_path
        
        # Check source metadata summary
        metadata_summary = logging_manager.current_session.source_metadata
        assert metadata_summary["title"] == "Test Book Title"
        assert metadata_summary["author"] == "Test Author"
        assert metadata_summary["isbn13"] == "9781234567897"
        assert metadata_summary["publisher"] == "Test Publisher"
        assert metadata_summary["imprint"] == "Test Imprint"
    
    def test_log_field_mapping_success(self, logging_manager, sample_metadata):
        """Test logging successful field mapping"""
        # Start session first
        logging_manager.start_generation_session(sample_metadata, "/test/output.csv")
        
        # Log field mapping
        logging_manager.log_field_mapping(
            field_name="Title",
            source_value="Test Book Title",
            mapped_value="Test Book Title",
            mapping_strategy="direct",
            processing_time_ms=1.5
        )
        
        # Check session has the mapping log
        assert len(logging_manager.current_session.field_mappings) == 1
        mapping_log = logging_manager.current_session.field_mappings[0]
        
        assert mapping_log.field_name == "Title"
        assert mapping_log.source_value == "Test Book Title"
        assert mapping_log.mapped_value == "Test Book Title"
        assert mapping_log.mapping_strategy == "direct"
        assert mapping_log.processing_time_ms == 1.5
        assert len(mapping_log.errors) == 0
        assert len(mapping_log.warnings) == 0
        
        # Check counters
        assert logging_manager.current_session.total_fields_processed == 1
        assert logging_manager.current_session.successful_mappings == 1
        assert logging_manager.current_session.failed_mappings == 0
    
    def test_log_field_mapping_with_errors(self, logging_manager, sample_metadata):
        """Test logging field mapping with errors"""
        # Start session first
        logging_manager.start_generation_session(sample_metadata, "/test/output.csv")
        
        # Log field mapping with errors
        logging_manager.log_field_mapping(
            field_name="ISBN",
            source_value="invalid_isbn",
            mapped_value="",
            mapping_strategy="direct",
            processing_time_ms=2.0,
            errors=["Invalid ISBN format"]
        )
        
        # Check session has the mapping log
        assert len(logging_manager.current_session.field_mappings) == 1
        mapping_log = logging_manager.current_session.field_mappings[0]
        
        assert mapping_log.field_name == "ISBN"
        assert mapping_log.errors == ["Invalid ISBN format"]
        
        # Check counters
        assert logging_manager.current_session.total_fields_processed == 1
        assert logging_manager.current_session.successful_mappings == 0
        assert logging_manager.current_session.failed_mappings == 1
    
    def test_log_field_mapping_with_warnings(self, logging_manager, sample_metadata):
        """Test logging field mapping with warnings"""
        # Start session first
        logging_manager.start_generation_session(sample_metadata, "/test/output.csv")
        
        # Log field mapping with warnings
        logging_manager.log_field_mapping(
            field_name="Price",
            source_value="19.99",
            mapped_value="$19.99",
            mapping_strategy="computed",
            processing_time_ms=0.8,
            warnings=["Price format adjusted"]
        )
        
        # Check session has the mapping log
        assert len(logging_manager.current_session.field_mappings) == 1
        mapping_log = logging_manager.current_session.field_mappings[0]
        
        assert mapping_log.field_name == "Price"
        assert mapping_log.warnings == ["Price format adjusted"]
        
        # Check counters
        assert logging_manager.current_session.total_fields_processed == 1
        assert logging_manager.current_session.successful_mappings == 1
        assert logging_manager.current_session.failed_mappings == 0
    
    def test_log_field_mapping_no_session(self, logging_manager):
        """Test logging field mapping without active session"""
        # Should not crash, but should log warning
        logging_manager.log_field_mapping(
            field_name="Title",
            source_value="Test",
            mapped_value="Test",
            mapping_strategy="direct"
        )
        
        # No session should be created
        assert logging_manager.current_session is None
    
    def test_log_validation_result(self, logging_manager, sample_metadata):
        """Test logging validation results"""
        # Start session first
        logging_manager.start_generation_session(sample_metadata, "/test/output.csv")
        
        # Create field validation result
        field_result = FieldValidationResult(
            field_name="isbn13",
            is_valid=True,
            severity=ValidationSeverity.INFO,
            error_message="",
            warning_message="",
            suggested_value=None
        )
        
        # Log validation result
        logging_manager.log_validation_result(field_result)
        
        # Check session has the validation log
        assert len(logging_manager.current_session.validation_results) == 1
        validation_log = logging_manager.current_session.validation_results[0]
        
        assert validation_log.field_name == "isbn13"
        assert validation_log.is_valid == True
        assert validation_log.severity == "INFO"
    
    def test_log_validation_result_with_error(self, logging_manager, sample_metadata):
        """Test logging validation result with error"""
        # Start session first
        logging_manager.start_generation_session(sample_metadata, "/test/output.csv")
        
        # Create field validation result with error
        field_result = FieldValidationResult(
            field_name="isbn13",
            is_valid=False,
            severity=ValidationSeverity.ERROR,
            error_message="Invalid ISBN format",
            warning_message="",
            suggested_value="9781234567897"
        )
        
        # Log validation result
        logging_manager.log_validation_result(field_result)
        
        # Check counters
        assert logging_manager.current_session.validation_errors == 1
        assert logging_manager.current_session.validation_warnings == 0
    
    def test_log_validation_summary(self, logging_manager, sample_metadata):
        """Test logging validation summary"""
        # Start session first
        logging_manager.start_generation_session(sample_metadata, "/test/output.csv")
        
        # Create validation result
        field_results = [
            FieldValidationResult(
                field_name="title",
                is_valid=True,
                severity=ValidationSeverity.INFO,
                error_message="",
                warning_message="",
                suggested_value=None
            ),
            FieldValidationResult(
                field_name="isbn13",
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                error_message="Invalid ISBN",
                warning_message="",
                suggested_value=None
            )
        ]
        
        validation_result = ValidationResult(
            is_valid=False,
            field_results=field_results,
            errors=["Invalid ISBN"],
            warnings=["Minor formatting issue"]
        )
        
        # Log validation summary
        logging_manager.log_validation_summary(validation_result)
        
        # Check that field results were logged
        assert len(logging_manager.current_session.validation_results) == 2
        
        # Check that errors and warnings were logged
        assert "Validation: Invalid ISBN" in logging_manager.current_session.error_messages
        assert "Validation: Minor formatting issue" in logging_manager.current_session.warning_messages
    
    def test_log_error_recovery_attempt(self, logging_manager, sample_metadata):
        """Test logging error recovery attempts"""
        # Start session first
        logging_manager.start_generation_session(sample_metadata, "/test/output.csv")
        
        # Log error recovery attempt
        logging_manager.log_error_recovery_attempt(
            field_name="isbn13",
            original_value="9781234567890",
            corrected_value="9781234567897",
            recovery_method="isbn_check_digit_correction"
        )
        
        # Check session has the recovery log
        assert len(logging_manager.current_session.recovery_attempts) == 1
        recovery_log = logging_manager.current_session.recovery_attempts[0]
        
        assert recovery_log["field_name"] == "isbn13"
        assert recovery_log["original_value"] == "9781234567890"
        assert recovery_log["corrected_value"] == "9781234567897"
        assert recovery_log["recovery_method"] == "isbn_check_digit_correction"
        assert "timestamp" in recovery_log
    
    def test_operation_timing(self, logging_manager):
        """Test operation timing functionality"""
        import time
        
        # Start timing
        logging_manager.start_operation_timing("test_operation")
        
        # Simulate some work
        time.sleep(0.01)  # 10ms
        
        # End timing
        duration = logging_manager.end_operation_timing("test_operation")
        
        # Check duration is reasonable (should be around 10ms)
        assert duration >= 8.0  # Allow some variance
        assert duration <= 20.0  # Allow some variance
    
    def test_operation_timing_no_start(self, logging_manager):
        """Test ending timing without starting"""
        duration = logging_manager.end_operation_timing("nonexistent_operation")
        assert duration == 0.0
    
    def test_log_performance_metric(self, logging_manager):
        """Test logging performance metrics"""
        # Should not crash
        logging_manager.log_performance_metric("test_metric", 123.45, "ms")
        logging_manager.log_performance_metric("another_metric", 67.89)
    
    def test_log_messages(self, logging_manager, sample_metadata):
        """Test logging info, warning, and error messages"""
        # Start session first
        logging_manager.start_generation_session(sample_metadata, "/test/output.csv")
        
        # Log different types of messages
        logging_manager.log_info("This is an info message")
        logging_manager.log_warning("This is a warning message")
        logging_manager.log_error("This is an error message")
        
        # Check messages were stored in session
        assert "This is an info message" in logging_manager.current_session.info_messages
        assert "This is a warning message" in logging_manager.current_session.warning_messages
        assert "This is an error message" in logging_manager.current_session.error_messages
    
    def test_complete_generation_session_success(self, logging_manager, sample_metadata, temp_log_dir):
        """Test completing generation session successfully"""
        # Start session
        session_id = logging_manager.start_generation_session(sample_metadata, "/test/output.csv")
        
        # Add some data to session
        logging_manager.log_field_mapping("Title", "Test", "Test", "direct")
        logging_manager.log_info("Generation completed")
        
        # Complete session
        logging_manager.complete_generation_session(success=True, final_file_size=1024)
        
        # Check session was completed
        assert logging_manager.current_session is None
        
        # Check log file was created
        log_files = list(Path(temp_log_dir).glob("*.json"))
        assert len(log_files) == 1
        
        # Check log file content
        with open(log_files[0], 'r') as f:
            session_data = json.load(f)
        
        assert session_data["session_id"] == session_id
        assert session_data["generation_successful"] == True
        assert session_data["final_csv_size_bytes"] == 1024
        assert session_data["end_time"] is not None
        assert session_data["total_duration_ms"] > 0
    
    def test_complete_generation_session_failure(self, logging_manager, sample_metadata):
        """Test completing generation session with failure"""
        # Start session
        logging_manager.start_generation_session(sample_metadata, "/test/output.csv")
        
        # Complete session with failure
        logging_manager.complete_generation_session(success=False)
        
        # Check session was completed
        assert logging_manager.current_session is None
    
    def test_complete_generation_session_no_session(self, logging_manager):
        """Test completing generation session without active session"""
        # Should not crash
        logging_manager.complete_generation_session(success=True)
        assert logging_manager.current_session is None
    
    def test_get_session_summary(self, logging_manager, sample_metadata):
        """Test getting session summary"""
        # No session initially
        summary = logging_manager.get_session_summary()
        assert summary == {}
        
        # Start session
        logging_manager.start_generation_session(sample_metadata, "/test/output.csv")
        
        # Add some data
        logging_manager.log_field_mapping("Title", "Test", "Test", "direct")
        logging_manager.log_error_recovery_attempt("isbn13", "old", "new", "correction")
        
        # Get summary
        summary = logging_manager.get_session_summary()
        
        assert "session_id" in summary
        assert summary["fields_processed"] == 1
        assert summary["successful_mappings"] == 1
        assert summary["failed_mappings"] == 0
        assert summary["recovery_attempts"] == 1
        assert summary["source_metadata"]["title"] == "Test Book Title"
    
    def test_get_field_mapping_statistics(self, logging_manager, sample_metadata):
        """Test getting field mapping statistics"""
        # No session initially
        stats = logging_manager.get_field_mapping_statistics()
        assert stats == {}
        
        # Start session
        logging_manager.start_generation_session(sample_metadata, "/test/output.csv")
        
        # Add field mappings
        logging_manager.log_field_mapping("Title", "Test", "Test", "direct", 1.0)
        logging_manager.log_field_mapping("Price", "19.99", "$19.99", "computed", 2.0)
        logging_manager.log_field_mapping("Default", "", "Default", "default", 0.5)
        
        # Get statistics
        stats = logging_manager.get_field_mapping_statistics()
        
        assert stats["total_mappings"] == 3
        assert stats["total_processing_time_ms"] == 3.5
        assert stats["average_processing_time_ms"] == 3.5 / 3
        assert "strategy_distribution" in stats
        assert stats["strategy_distribution"]["direct"] == 1
        assert stats["strategy_distribution"]["computed"] == 1
        assert stats["strategy_distribution"]["default"] == 1
    
    def test_get_validation_statistics(self, logging_manager, sample_metadata):
        """Test getting validation statistics"""
        # No session initially
        stats = logging_manager.get_validation_statistics()
        assert stats == {}
        
        # Start session
        logging_manager.start_generation_session(sample_metadata, "/test/output.csv")
        
        # Add validation results
        field_results = [
            FieldValidationResult("title", True, ValidationSeverity.INFO, "", "", None),
            FieldValidationResult("isbn13", False, ValidationSeverity.ERROR, "Invalid", "", None),
            FieldValidationResult("price", True, ValidationSeverity.WARNING, "", "Warning", None)
        ]
        
        # Set suggested_value manually since it's not in the constructor
        field_results[1].suggested_value = "suggestion"
        
        for result in field_results:
            logging_manager.log_validation_result(result)
        
        # Get statistics
        stats = logging_manager.get_validation_statistics()
        
        assert stats["total_validations"] == 3
        assert stats["fields_with_suggestions"] == 1
        assert stats["error_rate"] == 1/3
        assert stats["warning_rate"] == 1/3  # One warning out of 3 validations
        assert "severity_distribution" in stats
    
    def test_load_session_log(self, logging_manager, sample_metadata, temp_log_dir):
        """Test loading session log from file"""
        # Start and complete a session to create a log file
        session_id = logging_manager.start_generation_session(sample_metadata, "/test/output.csv")
        logging_manager.log_field_mapping("Title", "Test", "Test", "direct")
        logging_manager.complete_generation_session(success=True, final_file_size=1024)
        
        # Find the log file
        log_files = list(Path(temp_log_dir).glob("*.json"))
        assert len(log_files) == 1
        log_file_path = str(log_files[0])
        
        # Load session log
        loaded_session = LSILoggingManager.load_session_log(log_file_path)
        
        assert loaded_session is not None
        assert loaded_session.session_id == session_id
        assert loaded_session.generation_successful == True
        assert loaded_session.final_csv_size_bytes == 1024
    
    def test_load_session_log_nonexistent_file(self):
        """Test loading session log from nonexistent file"""
        loaded_session = LSILoggingManager.load_session_log("/nonexistent/file.json")
        assert loaded_session is None
    
    def test_load_session_log_invalid_json(self, temp_log_dir):
        """Test loading session log from invalid JSON file"""
        # Create invalid JSON file
        invalid_file = Path(temp_log_dir) / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("invalid json content")
        
        loaded_session = LSILoggingManager.load_session_log(str(invalid_file))
        assert loaded_session is None
    
    def test_structured_logging_setup(self, temp_log_dir):
        """Test that structured logging is properly configured"""
        # Create logging manager
        logging_manager = LSILoggingManager(temp_log_dir)
        
        # Check that log file was created
        log_file = Path(temp_log_dir) / "lsi_generation.log"
        assert log_file.exists()
    
    def test_field_mapping_log_dataclass(self):
        """Test FieldMappingLog dataclass"""
        log = FieldMappingLog(
            field_name="Title",
            source_value="Test Title",
            mapped_value="Test Title",
            mapping_strategy="direct",
            processing_time_ms=1.5,
            warnings=["Warning message"],
            errors=["Error message"]
        )
        
        assert log.field_name == "Title"
        assert log.source_value == "Test Title"
        assert log.mapped_value == "Test Title"
        assert log.mapping_strategy == "direct"
        assert log.processing_time_ms == 1.5
        assert log.warnings == ["Warning message"]
        assert log.errors == ["Error message"]
        assert log.timestamp is not None
    
    def test_validation_log_dataclass(self):
        """Test ValidationLog dataclass"""
        log = ValidationLog(
            field_name="isbn13",
            is_valid=False,
            severity="ERROR",
            message="Invalid ISBN format",
            suggested_value="9781234567897"
        )
        
        assert log.field_name == "isbn13"
        assert log.is_valid == False
        assert log.severity == "ERROR"
        assert log.message == "Invalid ISBN format"
        assert log.suggested_value == "9781234567897"
        assert log.timestamp is not None
    
    def test_generation_session_dataclass(self):
        """Test GenerationSession dataclass"""
        session = GenerationSession(
            session_id="test_session",
            start_time="2024-01-01T00:00:00"
        )
        
        assert session.session_id == "test_session"
        assert session.start_time == "2024-01-01T00:00:00"
        assert session.end_time is None
        assert session.total_duration_ms == 0.0
        assert session.source_metadata == {}
        assert session.field_mappings == []
        assert session.validation_results == []
        assert session.total_fields_processed == 0
        assert session.successful_mappings == 0
        assert session.failed_mappings == 0
        assert session.validation_errors == 0
        assert session.validation_warnings == 0
        assert session.generation_successful == False
        assert session.output_file_path == ""
        assert session.final_csv_size_bytes == 0
        assert session.recovery_attempts == []
        assert session.info_messages == []
        assert session.warning_messages == []
        assert session.error_messages == []