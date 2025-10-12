# tests/test_validation_framework.py

import pytest
from unittest.mock import Mock, patch
from dataclasses import dataclass

from codexes.modules.verifiers.validation_framework import (
    FieldValidator,
    FieldValidationResult,
    ValidationResult,
    ValidationSeverity,
    LSIValidationPipeline
)
from codexes.modules.metadata.metadata_models import CodexMetadata


class MockValidator(FieldValidator):
    """Mock validator for testing"""
    
    def __init__(self, name: str = "MockValidator", should_fail: bool = False):
        super().__init__(name)
        self.should_fail = should_fail
        self.validated_fields = []
    
    def validate(self, field_name: str, value, metadata: CodexMetadata) -> FieldValidationResult:
        self.validated_fields.append(field_name)
        
        if self.should_fail:
            return self._create_result(
                field_name=field_name,
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Mock validation failed for {field_name}"
            )
        else:
            return self._create_result(
                field_name=field_name,
                is_valid=True,
                severity=ValidationSeverity.INFO,
                message=f"Mock validation passed for {field_name}"
            )
    
    def can_validate(self, field_name: str) -> bool:
        # Only validate specific fields for testing
        return field_name in ['title', 'isbn13', 'author']


class TestFieldValidationResult:
    """Test FieldValidationResult class"""
    
    def test_create_valid_result(self):
        result = FieldValidationResult(
            field_name="title",
            is_valid=True,
            severity=ValidationSeverity.INFO,
            info_message="Test info"
        )
        
        assert result.field_name == "title"
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert not result.has_error
        assert not result.has_warning
        assert result.message == "Test info"
    
    def test_create_error_result(self):
        result = FieldValidationResult(
            field_name="isbn13",
            is_valid=False,
            severity=ValidationSeverity.ERROR,
            error_message="Invalid ISBN format"
        )
        
        assert result.field_name == "isbn13"
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert result.has_error
        assert not result.has_warning
        assert result.message == "Invalid ISBN format"
    
    def test_message_priority(self):
        # Error message takes priority over warning
        result = FieldValidationResult(
            field_name="test",
            is_valid=False,
            error_message="Error message",
            warning_message="Warning message"
        )
        
        assert result.message == "Error message"


class TestValidationResult:
    """Test ValidationResult class"""
    
    def test_empty_validation_result(self):
        result = ValidationResult(is_valid=True)
        
        assert result.is_valid is True
        assert len(result.field_results) == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert not result.has_blocking_errors()
    
    def test_add_field_result_error(self):
        result = ValidationResult(is_valid=True)
        
        field_result = FieldValidationResult(
            field_name="isbn13",
            is_valid=False,
            severity=ValidationSeverity.ERROR,
            error_message="Invalid ISBN"
        )
        
        result.add_field_result(field_result)
        
        assert result.is_valid is False
        assert len(result.field_results) == 1
        assert len(result.errors) == 1
        assert "isbn13: Invalid ISBN" in result.errors
        assert result.has_blocking_errors()
    
    def test_add_field_result_warning(self):
        result = ValidationResult(is_valid=True)
        
        field_result = FieldValidationResult(
            field_name="title",
            is_valid=True,
            severity=ValidationSeverity.WARNING,
            warning_message="Title could be improved"
        )
        
        result.add_field_result(field_result)
        
        assert result.is_valid is True  # Warnings don't make result invalid
        assert len(result.field_results) == 1
        assert len(result.warnings) == 1
        assert "title: Title could be improved" in result.warnings
        assert not result.has_blocking_errors()
    
    def test_get_errors_by_field(self):
        result = ValidationResult(is_valid=True)
        
        # Add error for isbn13
        isbn_result = FieldValidationResult(
            field_name="isbn13",
            is_valid=False,
            severity=ValidationSeverity.ERROR,
            error_message="Invalid format"
        )
        result.add_field_result(isbn_result)
        
        # Add error for different field
        title_result = FieldValidationResult(
            field_name="title",
            is_valid=False,
            severity=ValidationSeverity.ERROR,
            error_message="Title required"
        )
        result.add_field_result(title_result)
        
        isbn_errors = result.get_errors_by_field("isbn13")
        assert len(isbn_errors) == 1
        assert "Invalid format" in isbn_errors
        
        title_errors = result.get_errors_by_field("title")
        assert len(title_errors) == 1
        assert "Title required" in title_errors
        
        # Non-existent field
        other_errors = result.get_errors_by_field("author")
        assert len(other_errors) == 0
    
    def test_get_field_result(self):
        result = ValidationResult(is_valid=True)
        
        field_result = FieldValidationResult(
            field_name="isbn13",
            is_valid=True
        )
        result.add_field_result(field_result)
        
        retrieved = result.get_field_result("isbn13")
        assert retrieved is not None
        assert retrieved.field_name == "isbn13"
        
        not_found = result.get_field_result("nonexistent")
        assert not_found is None
    
    def test_summary(self):
        result = ValidationResult(is_valid=True)
        
        # Add some results
        result.add_field_result(FieldValidationResult("field1", True))
        result.add_field_result(FieldValidationResult(
            "field2", False, ValidationSeverity.ERROR, error_message="Error"
        ))
        result.add_field_result(FieldValidationResult(
            "field3", True, ValidationSeverity.WARNING, warning_message="Warning"
        ))
        
        summary = result.summary()
        assert "3 fields checked" in summary
        assert "1 errors" in summary
        assert "1 warnings" in summary


class TestFieldValidator:
    """Test FieldValidator abstract base class"""
    
    def test_mock_validator_creation(self):
        validator = MockValidator("TestValidator")
        assert validator.name == "TestValidator"
    
    def test_validator_can_validate(self):
        validator = MockValidator()
        
        assert validator.can_validate("title") is True
        assert validator.can_validate("isbn13") is True
        assert validator.can_validate("unknown_field") is False
    
    def test_validator_validate_success(self):
        validator = MockValidator(should_fail=False)
        metadata = CodexMetadata(title="Test Book")
        
        result = validator.validate("title", "Test Book", metadata)
        
        assert result.field_name == "title"
        assert result.is_valid is True
        assert "title" in validator.validated_fields
    
    def test_validator_validate_failure(self):
        validator = MockValidator(should_fail=True)
        metadata = CodexMetadata(title="Test Book")
        
        result = validator.validate("title", "Test Book", metadata)
        
        assert result.field_name == "title"
        assert result.is_valid is False
        assert result.has_error
        assert "Mock validation failed" in result.error_message
    
    def test_create_result_helper(self):
        validator = MockValidator()
        
        result = validator._create_result(
            field_name="test",
            is_valid=False,
            severity=ValidationSeverity.WARNING,
            message="Test warning",
            suggested_value="suggested"
        )
        
        assert result.field_name == "test"
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.WARNING
        assert result.warning_message == "Test warning"
        assert result.suggested_value == "suggested"


class TestLSIValidationPipeline:
    """Test LSIValidationPipeline class"""
    
    def test_empty_pipeline(self):
        pipeline = LSIValidationPipeline()
        assert len(pipeline.validators) == 0
        assert len(pipeline.get_validator_names()) == 0
    
    def test_add_validator(self):
        pipeline = LSIValidationPipeline()
        validator = MockValidator("TestValidator")
        
        pipeline.add_validator(validator)
        
        assert len(pipeline.validators) == 1
        assert "TestValidator" in pipeline.get_validator_names()
    
    def test_remove_validator(self):
        pipeline = LSIValidationPipeline()
        validator1 = MockValidator("Validator1")
        validator2 = MockValidator("Validator2")
        
        pipeline.add_validator(validator1)
        pipeline.add_validator(validator2)
        
        assert len(pipeline.validators) == 2
        
        pipeline.remove_validator("Validator1")
        
        assert len(pipeline.validators) == 1
        assert "Validator2" in pipeline.get_validator_names()
        assert "Validator1" not in pipeline.get_validator_names()
    
    def test_validate_with_single_validator(self):
        pipeline = LSIValidationPipeline()
        validator = MockValidator("TestValidator", should_fail=False)
        pipeline.add_validator(validator)
        
        metadata = CodexMetadata(title="Test Book", isbn13="1234567890123", author="Test Author")
        
        result = pipeline.validate(metadata)
        
        assert result.is_valid is True
        assert len(result.field_results) == 3  # title, isbn13, author
        assert not result.has_blocking_errors()
        
        # Check that validator was called for expected fields
        assert "title" in validator.validated_fields
        assert "isbn13" in validator.validated_fields
        assert "author" in validator.validated_fields
    
    def test_validate_with_failing_validator(self):
        pipeline = LSIValidationPipeline()
        validator = MockValidator("FailingValidator", should_fail=True)
        pipeline.add_validator(validator)
        
        metadata = CodexMetadata(title="Test Book")
        
        result = pipeline.validate(metadata)
        
        assert result.is_valid is False
        assert len(result.errors) == 3  # title, isbn13, author all fail
        assert result.has_blocking_errors()
    
    def test_validate_with_multiple_validators(self):
        pipeline = LSIValidationPipeline()
        
        good_validator = MockValidator("GoodValidator", should_fail=False)
        bad_validator = MockValidator("BadValidator", should_fail=True)
        
        pipeline.add_validator(good_validator)
        pipeline.add_validator(bad_validator)
        
        metadata = CodexMetadata(title="Test Book")
        
        result = pipeline.validate(metadata)
        
        # Should have results from both validators
        assert len(result.field_results) == 6  # 3 fields × 2 validators
        assert result.is_valid is False  # Bad validator causes failure
        assert result.has_blocking_errors()
    
    def test_validate_field_single(self):
        pipeline = LSIValidationPipeline()
        validator = MockValidator("TestValidator", should_fail=False)
        pipeline.add_validator(validator)
        
        metadata = CodexMetadata(title="Test Book")
        
        results = pipeline.validate_field("title", "Test Book", metadata)
        
        assert len(results) == 1
        assert results[0].field_name == "title"
        assert results[0].is_valid is True
    
    def test_validate_field_no_applicable_validators(self):
        pipeline = LSIValidationPipeline()
        validator = MockValidator("TestValidator")  # Only validates title, isbn13, author
        pipeline.add_validator(validator)
        
        metadata = CodexMetadata()
        
        results = pipeline.validate_field("unknown_field", "value", metadata)
        
        assert len(results) == 0
    
    @patch('src.codexes.modules.verifiers.validation_framework.logging')
    def test_validator_exception_handling(self, mock_logging):
        """Test that validator exceptions are handled gracefully"""
        
        class ExceptionValidator(FieldValidator):
            def validate(self, field_name: str, value, metadata: CodexMetadata) -> FieldValidationResult:
                raise ValueError("Test exception")
            
            def can_validate(self, field_name: str) -> bool:
                return field_name == "title"
        
        pipeline = LSIValidationPipeline()
        pipeline.add_validator(ExceptionValidator("ExceptionValidator"))
        
        metadata = CodexMetadata(title="Test Book")
        
        result = pipeline.validate(metadata)
        
        # Should have error result for the exception
        assert result.is_valid is False
        assert len(result.field_results) == 1
        assert "Validation error: Test exception" in result.field_results[0].error_message


if __name__ == "__main__":
    pytest.main([__file__])