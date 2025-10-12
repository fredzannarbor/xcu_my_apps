"""
Field Corrections Validator

This module provides comprehensive validation for the LSI field mapping corrections,
including thema subject codes, age ranges, file paths, and other field-specific validations.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class FieldCorrectionsValidator:
    """Comprehensive validator for LSI field mapping corrections."""
    
    def __init__(self):
        """Initialize the validator."""
        self.errors = []
        self.warnings = []
        
    def validate_thema_subject_codes(self, subjects: List[str]) -> bool:
        """
        Validate thema subject codes against known formats.
        
        Args:
            subjects: List of thema subject codes to validate
            
        Returns:
            True if all codes are valid
        """
        valid = True
        
        for i, subject in enumerate(subjects):
            if not self._validate_single_thema_code(subject):
                self.errors.append(f"Invalid thema subject code {i+1}: '{subject}'")
                valid = False
                
        return valid
        
    def _validate_single_thema_code(self, code: str) -> bool:
        """
        Validate a single thema subject code.
        
        Args:
            code: Thema code to validate
            
        Returns:
            True if code is valid
        """
        if not code or not isinstance(code, str):
            return False
            
        code = code.strip().upper()
        
        # Basic format validation
        if len(code) < 2 or len(code) > 10:
            return False
            
        # Should start with letters
        if not code[0].isalpha():
            return False
            
        # Should contain only letters and numbers
        if not re.match(r'^[A-Z][A-Z0-9]*$', code):
            return False
            
        # Check against known thema code patterns
        known_patterns = [
            r'^[A-Z]{2,4}$',           # Basic codes like "TGBN", "JNFH"
            r'^[A-Z]{2,4}[0-9]{1,3}$', # Codes with numbers like "ABC123"
            r'^[A-Z]{1,2}[A-Z]{2}$',   # Mixed patterns
        ]
        
        return any(re.match(pattern, code) for pattern in known_patterns)
        
    def validate_age_range(self, min_age: Optional[int], max_age: Optional[int]) -> bool:
        """
        Validate age range values.
        
        Args:
            min_age: Minimum age value
            max_age: Maximum age value
            
        Returns:
            True if age range is valid
        """
        valid = True
        
        # Validate individual age values
        if min_age is not None:
            if not self._validate_single_age(min_age, "minimum"):
                valid = False
                
        if max_age is not None:
            if not self._validate_single_age(max_age, "maximum"):
                valid = False
                
        # Validate age range logic
        if min_age is not None and max_age is not None:
            if min_age > max_age:
                self.errors.append(f"Minimum age ({min_age}) cannot be greater than maximum age ({max_age})")
                valid = False
            elif min_age == max_age:
                self.warnings.append(f"Minimum and maximum age are the same ({min_age})")
                
        return valid
        
    def _validate_single_age(self, age: int, age_type: str) -> bool:
        """
        Validate a single age value.
        
        Args:
            age: Age value to validate
            age_type: Type of age ("minimum" or "maximum")
            
        Returns:
            True if age is valid
        """
        if not isinstance(age, int):
            self.errors.append(f"Age value must be an integer, got {type(age).__name__}")
            return False
            
        if age < 0:
            self.errors.append(f"Age cannot be negative: {age}")
            return False
            
        if age > 150:
            self.errors.append(f"Age value seems unrealistic: {age}")
            return False
            
        # Age-specific validations
        if age_type == "minimum" and age > 100:
            self.warnings.append(f"Minimum age is very high: {age}")
        elif age_type == "maximum" and age < 5:
            self.warnings.append(f"Maximum age is very low: {age}")
            
        return True
        
    def validate_file_paths(self, paths: Dict[str, str]) -> bool:
        """
        Validate file paths for LSI naming convention compliance.
        
        Args:
            paths: Dictionary of path type to path string
            
        Returns:
            True if all paths are valid
        """
        valid = True
        
        for path_type, path in paths.items():
            if not self._validate_single_file_path(path, path_type):
                valid = False
                
        return valid
        
    def _validate_single_file_path(self, path: str, path_type: str) -> bool:
        """
        Validate a single file path.
        
        Args:
            path: File path to validate
            path_type: Type of path (interior, cover, etc.)
            
        Returns:
            True if path is valid
        """
        if not path:
            return True  # Empty paths are allowed
            
        # Check for invalid characters
        invalid_chars = r'[<>:"|?*]'
        if re.search(invalid_chars, path):
            self.errors.append(f"File path contains invalid characters: {path}")
            return False
            
        # Check path length
        if len(path) > 255:
            self.errors.append(f"File path too long ({len(path)} chars): {path}")
            return False
            
        # Check for proper file extension
        expected_extensions = {
            'interior': ['.pdf'],
            'cover': ['.pdf'],
            'marketing': ['.png', '.jpg', '.jpeg']
        }
        
        if path_type in expected_extensions:
            path_obj = Path(path)
            if path_obj.suffix.lower() not in expected_extensions[path_type]:
                self.warnings.append(f"Unexpected file extension for {path_type}: {path_obj.suffix}")
                
        # Check for reasonable directory structure
        if path.count('/') > 5:
            self.warnings.append(f"File path has many directory levels: {path}")
            
        return True
        
    def validate_series_description(self, description: str, series_name: Optional[str]) -> bool:
        """
        Validate series-aware description processing.
        
        Args:
            description: Description text
            series_name: Series name (if any)
            
        Returns:
            True if description is properly formatted
        """
        if not description:
            return True
            
        # If series exists, check that it's properly referenced
        if series_name and series_name.strip():
            series_pattern = f'in the {re.escape(series_name.strip())} series'
            if 'this book' in description.lower() and not re.search(series_pattern, description, re.IGNORECASE):
                self.warnings.append(f"Description contains 'this book' but doesn't reference series '{series_name}'")
                return False
                
        # Check for reasonable description length
        if len(description) > 2000:
            self.warnings.append(f"Description is very long ({len(description)} chars)")
        elif len(description) < 50:
            self.warnings.append(f"Description is very short ({len(description)} chars)")
            
        return True
        
    def validate_blank_fields(self, field_values: Dict[str, str], blank_field_names: List[str]) -> bool:
        """
        Validate that specified fields are properly blank.
        
        Args:
            field_values: Dictionary of field names to values
            blank_field_names: List of fields that should be blank
            
        Returns:
            True if all specified fields are blank
        """
        valid = True
        
        for field_name in blank_field_names:
            if field_name in field_values:
                value = field_values[field_name]
                if value and value.strip():
                    self.errors.append(f"Field '{field_name}' should be blank but has value: '{value}'")
                    valid = False
                    
        return valid
        
    def validate_tranche_overrides(self, base_values: Dict[str, str], 
                                 override_values: Dict[str, str],
                                 append_fields: List[str]) -> bool:
        """
        Validate tranche override application.
        
        Args:
            base_values: Original field values
            override_values: Values after override application
            append_fields: List of fields that should append
            
        Returns:
            True if overrides were applied correctly
        """
        valid = True
        
        for field_name, override_value in override_values.items():
            base_value = base_values.get(field_name, "")
            
            if field_name in append_fields:
                # For append fields, check that base value is included
                if base_value and base_value not in override_value:
                    self.warnings.append(f"Append field '{field_name}' doesn't contain base value")
            else:
                # For replace fields, check that value was actually replaced
                if base_value == override_value and field_name in base_values:
                    self.warnings.append(f"Replace field '{field_name}' value unchanged after override")
                    
        return valid
        
    def validate_field_mapping_completeness(self, required_fields: List[str], 
                                          mapped_fields: Dict[str, str]) -> bool:
        """
        Validate that all required fields have been mapped.
        
        Args:
            required_fields: List of required field names
            mapped_fields: Dictionary of mapped field values
            
        Returns:
            True if all required fields are present
        """
        valid = True
        missing_fields = []
        
        for field_name in required_fields:
            if field_name not in mapped_fields:
                missing_fields.append(field_name)
                
        if missing_fields:
            self.errors.append(f"Missing required fields: {', '.join(missing_fields)}")
            valid = False
            
        return valid
        
    def get_validation_results(self) -> Dict[str, List[str]]:
        """
        Get validation results.
        
        Returns:
            Dictionary with errors and warnings
        """
        return {
            "errors": self.errors.copy(),
            "warnings": self.warnings.copy()
        }
        
    def clear_results(self):
        """Clear validation results."""
        self.errors.clear()
        self.warnings.clear()
        
    def has_errors(self) -> bool:
        """Check if there are validation errors."""
        return len(self.errors) > 0
        
    def has_warnings(self) -> bool:
        """Check if there are validation warnings."""
        return len(self.warnings) > 0
        
    def get_error_count(self) -> int:
        """Get number of validation errors."""
        return len(self.errors)
        
    def get_warning_count(self) -> int:
        """Get number of validation warnings."""
        return len(self.warnings)
        
    def validate_all_corrections(self, field_data: Dict[str, Any]) -> bool:
        """
        Validate all field corrections in one call.
        
        Args:
            field_data: Dictionary containing all field data to validate
            
        Returns:
            True if all validations pass
        """
        self.clear_results()
        all_valid = True
        
        # Validate thema subjects
        if 'thema_subjects' in field_data:
            subjects = field_data['thema_subjects']
            if subjects and not self.validate_thema_subject_codes(subjects):
                all_valid = False
                
        # Validate age range
        if 'min_age' in field_data or 'max_age' in field_data:
            min_age = field_data.get('min_age')
            max_age = field_data.get('max_age')
            if not self.validate_age_range(min_age, max_age):
                all_valid = False
                
        # Validate file paths
        if 'file_paths' in field_data:
            paths = field_data['file_paths']
            if paths and not self.validate_file_paths(paths):
                all_valid = False
                
        # Validate series description
        if 'description' in field_data:
            description = field_data['description']
            series_name = field_data.get('series_name')
            if not self.validate_series_description(description, series_name):
                all_valid = False
                
        # Validate blank fields
        if 'field_values' in field_data and 'blank_fields' in field_data:
            field_values = field_data['field_values']
            blank_fields = field_data['blank_fields']
            if not self.validate_blank_fields(field_values, blank_fields):
                all_valid = False
                
        return all_valid