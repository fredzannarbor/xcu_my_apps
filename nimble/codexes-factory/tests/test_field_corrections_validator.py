"""
Tests for FieldCorrectionsValidator
"""

import pytest
from codexes.modules.distribution.field_corrections_validator import FieldCorrectionsValidator


class TestFieldCorrectionsValidator:
    """Test cases for FieldCorrectionsValidator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = FieldCorrectionsValidator()
        
    def test_validate_thema_subject_codes_valid(self):
        """Test validating valid thema subject codes."""
        valid_codes = ['TGBN', 'JNFH', 'JFFG', 'ABC123', 'XY']
        
        result = self.validator.validate_thema_subject_codes(valid_codes)
        
        assert result is True
        assert self.validator.get_error_count() == 0
        
    def test_validate_thema_subject_codes_invalid(self):
        """Test validating invalid thema subject codes."""
        invalid_codes = ['1ABC', 'A', 'TOOLONGCODE123', 'AB-CD', '']
        
        result = self.validator.validate_thema_subject_codes(invalid_codes)
        
        assert result is False
        assert self.validator.get_error_count() > 0
        
    def test_validate_single_thema_code_valid(self):
        """Test validating single valid thema codes."""
        valid_codes = ['TGBN', 'ABC123', 'XYZ', 'AB12']
        
        for code in valid_codes:
            assert self.validator._validate_single_thema_code(code) is True
            
    def test_validate_single_thema_code_invalid(self):
        """Test validating single invalid thema codes."""
        invalid_codes = ['1ABC', 'A', 'TOOLONGCODE123', 'AB-CD', '', None]
        
        for code in invalid_codes:
            assert self.validator._validate_single_thema_code(code) is False
            
    def test_validate_age_range_valid(self):
        """Test validating valid age ranges."""
        test_cases = [
            (18, 65),    # Normal range
            (0, 100),    # Wide range
            (25, 25),    # Same age (warning but valid)
            (None, 65),  # Only max age
            (18, None),  # Only min age
            (None, None) # No ages
        ]
        
        for min_age, max_age in test_cases:
            self.validator.clear_results()
            result = self.validator.validate_age_range(min_age, max_age)
            assert result is True
            
    def test_validate_age_range_invalid(self):
        """Test validating invalid age ranges."""
        test_cases = [
            (65, 18),    # Min > Max
            (-5, 25),    # Negative min
            (25, -5),    # Negative max
            (200, 250),  # Unrealistic ages
        ]
        
        for min_age, max_age in test_cases:
            self.validator.clear_results()
            result = self.validator.validate_age_range(min_age, max_age)
            assert result is False
            assert self.validator.get_error_count() > 0
            
    def test_validate_single_age_valid(self):
        """Test validating single valid ages."""
        valid_ages = [0, 18, 25, 65, 100, 150]
        
        for age in valid_ages:
            self.validator.clear_results()
            result = self.validator._validate_single_age(age, "minimum")
            assert result is True
            
    def test_validate_single_age_invalid(self):
        """Test validating single invalid ages."""
        invalid_ages = [-1, -10, 200, 300]
        
        for age in invalid_ages:
            self.validator.clear_results()
            result = self.validator._validate_single_age(age, "minimum")
            assert result is False
            assert self.validator.get_error_count() > 0
            
    def test_validate_single_age_warnings(self):
        """Test age validation warnings."""
        # High minimum age should generate warning
        self.validator.clear_results()
        result = self.validator._validate_single_age(120, "minimum")
        assert result is True
        assert self.validator.get_warning_count() > 0
        
        # Low maximum age should generate warning
        self.validator.clear_results()
        result = self.validator._validate_single_age(3, "maximum")
        assert result is True
        assert self.validator.get_warning_count() > 0
        
    def test_validate_file_paths_valid(self):
        """Test validating valid file paths."""
        valid_paths = {
            'interior': 'interior/test_book_interior.pdf',
            'cover': 'covers/test_book_cover.pdf',
            'marketing': 'images/test_book_thumb.png'
        }
        
        result = self.validator.validate_file_paths(valid_paths)
        
        assert result is True
        assert self.validator.get_error_count() == 0
        
    def test_validate_file_paths_invalid(self):
        """Test validating invalid file paths."""
        invalid_paths = {
            'interior': 'interior/test<book>interior.pdf',  # Invalid characters
            'cover': 'a' * 300 + '.pdf',  # Too long
        }
        
        result = self.validator.validate_file_paths(invalid_paths)
        
        assert result is False
        assert self.validator.get_error_count() > 0
        
    def test_validate_single_file_path_valid(self):
        """Test validating single valid file paths."""
        valid_paths = [
            'interior/book_interior.pdf',
            'covers/book_cover.pdf',
            '',  # Empty path is valid
            'simple.pdf'
        ]
        
        for path in valid_paths:
            self.validator.clear_results()
            result = self.validator._validate_single_file_path(path, 'interior')
            assert result is True
            
    def test_validate_single_file_path_invalid(self):
        """Test validating single invalid file paths."""
        invalid_paths = [
            'path/with<invalid>chars.pdf',
            'path/with|pipe.pdf',
            'a' * 300 + '.pdf'  # Too long
        ]
        
        for path in invalid_paths:
            self.validator.clear_results()
            result = self.validator._validate_single_file_path(path, 'interior')
            assert result is False
            assert self.validator.get_error_count() > 0
            
    def test_validate_series_description_valid(self):
        """Test validating valid series descriptions."""
        test_cases = [
            ("This book in the Test Series series offers insights.", "Test Series"),
            ("A comprehensive guide to advanced topics.", "Test Series"),  # No "this book"
            ("This book offers insights.", None),  # No series
            ("", "Test Series"),  # Empty description
        ]
        
        for description, series_name in test_cases:
            self.validator.clear_results()
            result = self.validator.validate_series_description(description, series_name)
            assert result is True
            
    def test_validate_series_description_invalid(self):
        """Test validating invalid series descriptions."""
        # Description with "this book" but no series reference
        self.validator.clear_results()
        result = self.validator.validate_series_description(
            "This book offers great insights.", "Test Series"
        )
        assert result is False
        assert self.validator.get_warning_count() > 0
        
    def test_validate_series_description_warnings(self):
        """Test series description validation warnings."""
        # Very long description
        long_description = "a" * 2500
        self.validator.clear_results()
        result = self.validator.validate_series_description(long_description, None)
        assert result is True
        assert self.validator.get_warning_count() > 0
        
        # Very short description
        short_description = "Short"
        self.validator.clear_results()
        result = self.validator.validate_series_description(short_description, None)
        assert result is True
        assert self.validator.get_warning_count() > 0
        
    def test_validate_blank_fields_valid(self):
        """Test validating blank fields correctly."""
        field_values = {
            'Field1': 'value1',
            'Field2': '',
            'Field3': '   ',  # Whitespace only
            'Field4': 'value4'
        }
        blank_field_names = ['Field2', 'Field3', 'Field5']  # Field5 not in values
        
        result = self.validator.validate_blank_fields(field_values, blank_field_names)
        
        assert result is True
        assert self.validator.get_error_count() == 0
        
    def test_validate_blank_fields_invalid(self):
        """Test validating blank fields with non-blank values."""
        field_values = {
            'Field1': 'value1',
            'Field2': 'should_be_blank',
            'Field3': '   not blank   '
        }
        blank_field_names = ['Field2', 'Field3']
        
        result = self.validator.validate_blank_fields(field_values, blank_field_names)
        
        assert result is False
        assert self.validator.get_error_count() > 0
        
    def test_validate_tranche_overrides(self):
        """Test validating tranche override application."""
        base_values = {
            'Field1': 'base_value1',
            'Field2': 'base_value2',
            'Field3': 'base_value3'
        }
        override_values = {
            'Field1': 'override_value1',  # Replaced
            'Field2': 'base_value2 appended_text',  # Appended
            'Field3': 'base_value3'  # Unchanged
        }
        append_fields = ['Field2']
        
        result = self.validator.validate_tranche_overrides(
            base_values, override_values, append_fields
        )
        
        assert result is True
        # Should have warnings for unchanged replace field
        assert self.validator.get_warning_count() > 0
        
    def test_validate_field_mapping_completeness_valid(self):
        """Test validating complete field mapping."""
        required_fields = ['Field1', 'Field2', 'Field3']
        mapped_fields = {
            'Field1': 'value1',
            'Field2': 'value2',
            'Field3': 'value3',
            'Field4': 'extra_value'  # Extra field is OK
        }
        
        result = self.validator.validate_field_mapping_completeness(
            required_fields, mapped_fields
        )
        
        assert result is True
        assert self.validator.get_error_count() == 0
        
    def test_validate_field_mapping_completeness_invalid(self):
        """Test validating incomplete field mapping."""
        required_fields = ['Field1', 'Field2', 'Field3']
        mapped_fields = {
            'Field1': 'value1',
            'Field3': 'value3'
            # Field2 is missing
        }
        
        result = self.validator.validate_field_mapping_completeness(
            required_fields, mapped_fields
        )
        
        assert result is False
        assert self.validator.get_error_count() > 0
        
    def test_validate_all_corrections(self):
        """Test validating all corrections together."""
        field_data = {
            'thema_subjects': ['TGBN', 'JNFH'],
            'min_age': 18,
            'max_age': 65,
            'file_paths': {
                'interior': 'interior/book_interior.pdf',
                'cover': 'covers/book_cover.pdf'
            },
            'description': 'This book in the Test Series series offers insights.',
            'series_name': 'Test Series',
            'field_values': {
                'Field1': 'value1',
                'Field2': ''
            },
            'blank_fields': ['Field2']
        }
        
        result = self.validator.validate_all_corrections(field_data)
        
        assert result is True
        assert self.validator.get_error_count() == 0
        
    def test_get_validation_results(self):
        """Test getting validation results."""
        # Generate some errors and warnings
        self.validator.errors.append("Test error")
        self.validator.warnings.append("Test warning")
        
        results = self.validator.get_validation_results()
        
        assert results['errors'] == ["Test error"]
        assert results['warnings'] == ["Test warning"]
        
    def test_clear_results(self):
        """Test clearing validation results."""
        self.validator.errors.append("Test error")
        self.validator.warnings.append("Test warning")
        
        self.validator.clear_results()
        
        assert len(self.validator.errors) == 0
        assert len(self.validator.warnings) == 0
        
    def test_has_errors_and_warnings(self):
        """Test checking for errors and warnings."""
        assert not self.validator.has_errors()
        assert not self.validator.has_warnings()
        
        self.validator.errors.append("Test error")
        self.validator.warnings.append("Test warning")
        
        assert self.validator.has_errors()
        assert self.validator.has_warnings()
        
    def test_get_counts(self):
        """Test getting error and warning counts."""
        assert self.validator.get_error_count() == 0
        assert self.validator.get_warning_count() == 0
        
        self.validator.errors.extend(["Error 1", "Error 2"])
        self.validator.warnings.append("Warning 1")
        
        assert self.validator.get_error_count() == 2
        assert self.validator.get_warning_count() == 1