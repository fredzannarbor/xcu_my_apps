# src/codexes/modules/verifiers/validation_framework.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

from ..metadata.metadata_models import CodexMetadata


class ValidationSeverity(Enum):
    """Severity levels for validation results"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class FieldValidationResult:
    """Result of validating a single field"""
    field_name: str
    is_valid: bool
    severity: ValidationSeverity = ValidationSeverity.ERROR
    error_message: str = ""
    warning_message: str = ""
    info_message: str = ""
    suggested_value: str = ""
    
    @property
    def has_error(self) -> bool:
        """Check if this result has an error"""
        return not self.is_valid and self.severity == ValidationSeverity.ERROR
    
    @property
    def has_warning(self) -> bool:
        """Check if this result has a warning"""
        return self.severity == ValidationSeverity.WARNING
    
    @property
    def message(self) -> str:
        """Get the primary message for this result"""
        if self.error_message:
            return self.error_message
        elif self.warning_message:
            return self.warning_message
        elif self.info_message:
            return self.info_message
        return ""


@dataclass
class ValidationResult:
    """Complete validation result for metadata"""
    is_valid: bool
    field_results: List[FieldValidationResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info_messages: List[str] = field(default_factory=list)
    
    def add_field_result(self, result: FieldValidationResult):
        """Add a field validation result"""
        self.field_results.append(result)
        
        if result.has_error:
            self.errors.append(f"{result.field_name}: {result.error_message}")
            self.is_valid = False
        elif result.has_warning:
            self.warnings.append(f"{result.field_name}: {result.warning_message}")
    
    def get_errors_by_field(self, field_name: str) -> List[str]:
        """Get all error messages for a specific field"""
        return [
            result.error_message 
            for result in self.field_results 
            if result.field_name == field_name and result.has_error
        ]
    
    def get_warnings_by_field(self, field_name: str) -> List[str]:
        """Get all warning messages for a specific field"""
        return [
            result.warning_message 
            for result in self.field_results 
            if result.field_name == field_name and result.has_warning
        ]
    
    def has_blocking_errors(self) -> bool:
        """Check if there are any blocking errors that prevent processing"""
        return len(self.errors) > 0
    
    def get_field_result(self, field_name: str) -> Optional[FieldValidationResult]:
        """Get the validation result for a specific field"""
        for result in self.field_results:
            if result.field_name == field_name:
                return result
        return None
    
    def summary(self) -> str:
        """Get a summary of the validation results"""
        total_fields = len(self.field_results)
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        
        return (
            f"Validation Summary: {total_fields} fields checked, "
            f"{error_count} errors, {warning_count} warnings"
        )


class FieldValidator(ABC):
    """Abstract base class for field validators"""
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"validator.{self.name}")
    
    @abstractmethod
    def validate(self, field_name: str, value: Any, metadata: CodexMetadata) -> FieldValidationResult:
        """
        Validate a field value
        
        Args:
            field_name: Name of the field being validated
            value: Value to validate
            metadata: Complete metadata object for context
            
        Returns:
            FieldValidationResult with validation outcome
        """
        pass
    
    def can_validate(self, field_name: str) -> bool:
        """
        Check if this validator can validate the given field
        Default implementation returns True for all fields
        """
        return True
    
    def _create_result(
        self, 
        field_name: str, 
        is_valid: bool, 
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        message: str = "",
        suggested_value: str = ""
    ) -> FieldValidationResult:
        """Helper method to create validation results"""
        result = FieldValidationResult(
            field_name=field_name,
            is_valid=is_valid,
            severity=severity,
            suggested_value=suggested_value
        )
        
        if severity == ValidationSeverity.ERROR:
            result.error_message = message
        elif severity == ValidationSeverity.WARNING:
            result.warning_message = message
        elif severity == ValidationSeverity.INFO:
            result.info_message = message
        
        return result


class LSIValidationPipeline:
    """Pipeline to orchestrate multiple validators for LSI metadata"""
    
    def __init__(self, validators: List[FieldValidator] = None):
        self.validators = validators or []
        self.logger = logging.getLogger("LSIValidationPipeline")
    
    def add_validator(self, validator: FieldValidator):
        """Add a validator to the pipeline"""
        self.validators.append(validator)
        self.logger.debug(f"Added validator: {validator.name}")
    
    def remove_validator(self, validator_name: str):
        """Remove a validator by name"""
        self.validators = [v for v in self.validators if v.name != validator_name]
        self.logger.debug(f"Removed validator: {validator_name}")
    
    def validate(self, metadata: CodexMetadata) -> ValidationResult:
        """
        Run all validators against the metadata
        
        Args:
            metadata: CodexMetadata object to validate
            
        Returns:
            ValidationResult with all validation outcomes
        """
        result = ValidationResult(is_valid=True)
        
        self.logger.info(f"Starting validation with {len(self.validators)} validators")
        
        # Get all field names from metadata
        field_names = [field for field in dir(metadata) if not field.startswith('_')]
        
        for validator in self.validators:
            self.logger.debug(f"Running validator: {validator.name}")
            
            for field_name in field_names:
                if validator.can_validate(field_name):
                    try:
                        field_value = getattr(metadata, field_name)
                        field_result = validator.validate(field_name, field_value, metadata)
                        result.add_field_result(field_result)
                        
                    except Exception as e:
                        self.logger.error(f"Validator {validator.name} failed on field {field_name}: {e}")
                        error_result = FieldValidationResult(
                            field_name=field_name,
                            is_valid=False,
                            severity=ValidationSeverity.ERROR,
                            error_message=f"Validation error: {str(e)}"
                        )
                        result.add_field_result(error_result)
        
        self.logger.info(f"Validation completed: {result.summary()}")
        return result
    
    def validate_field(self, field_name: str, value: Any, metadata: CodexMetadata) -> List[FieldValidationResult]:
        """
        Validate a specific field with all applicable validators
        
        Args:
            field_name: Name of the field to validate
            value: Value to validate
            metadata: Complete metadata object for context
            
        Returns:
            List of FieldValidationResult from all applicable validators
        """
        results = []
        
        for validator in self.validators:
            if validator.can_validate(field_name):
                try:
                    result = validator.validate(field_name, value, metadata)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Validator {validator.name} failed on field {field_name}: {e}")
                    error_result = FieldValidationResult(
                        field_name=field_name,
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        error_message=f"Validation error: {str(e)}"
                    )
                    results.append(error_result)
        
        return results
    
    def get_validator_names(self) -> List[str]:
        """Get names of all registered validators"""
        return [validator.name for validator in self.validators]