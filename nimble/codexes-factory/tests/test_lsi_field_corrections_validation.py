"""
Validation tests for LSI field mapping corrections
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock
from codexes.modules.distribution.field_corrections_validator import FieldCorrectionsValidator
from codexes.modules.distribution.tranche_config_loader import TrancheConfigLoader


class TestLSIFieldCorrectionsValidation:
    """Validation tests for LSI field mapping corrections."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = FieldCorrectionsValidator()
        
    def test_comprehensive_validation_success(self):
        """Test comprehensive validation with all valid data."""
        field_data = {
            'thema_subjects': ['TGBN', 'JNFH', 'JFFG'],
            'min_age': 18,
            'max_age': 65,
            'file_paths': {
                'interior': 'interior/test_book_interior.pdf',
                'cover': 'covers/test_book_cover.pdf'
            },
            'description': 'This book in the Test Series series offers comprehensive insights.',
            'series_name': 'Test Series',
            'field_values': {
                'Field1': 'value1',
                'Field2': '',
                'US-Ingram-Only* Suggested List Price (mode 2)': ''
            },
            'blank_fields': ['Field2', 'US-Ingram-Only* Suggested List Price (mode 2)']
        }
        
        result = self.validator.validate_all_corrections(field_data)
        
        assert result is True
        assert self.validator.get_error_count() == 0
        
    def test_comprehensive_validation_with_errors(self):
        """Test comprehensive validation with various errors."""
        field_data = {
            'thema_subjects': ['TGBN', '123INVALID', 'TOOLONGCODE123'],
            'min_age': -5,
            'max_age': 200,
            'file_paths': {
                'interior': 'interior/test<invalid>chars.pdf',
                'cover': 'a' * 300 + '.pdf'
            },
            'description': 'This book offers insights.',  # Missing series reference
            'series_name': 'Test Series',
            'field_values': {
                'Field1': 'value1',
                'Field2': 'should_be_blank'
            },
            'blank_fields': ['Field2']
        }
        
        result = self.validator.validate_all_corrections(field_data)
        
        assert result is False
        assert self.validator.get_error_count() > 0
        
        results = self.validator.get_validation_results()
        
        # Check for specific error types
        error_messages = ' '.join(results['errors'])
        assert 'Invalid thema subject code' in error_messages
        assert 'negative' in error_messages.lower()
        assert 'invalid characters' in error_messages.lower()
        assert 'should be blank' in error_messages
        
    def test_thema_subject_validation_comprehensive(self):
        """Test comprehensive thema subject validation."""
        test_cases = [
            # Valid cases
            (['TGBN', 'JNFH'], True, 0),
            (['ABC123', 'XY'], True, 0),
            ([], True, 0),  # Empty is valid
            
            # Invalid cases
            (['1ABC'], False, 1),  # Starts with number
            (['A'], False, 1),     # Too short
            (['TOOLONGCODE123'], False, 1),  # Too long
            (['AB-CD'], False, 1), # Invalid characters
            (['TGBN', '123', 'VALID'], False, 1),  # Mixed valid/invalid
        ]
        
        for subjects, expected_valid, expected_errors in test_cases:
            self.validator.clear_results()
            result = self.validator.validate_thema_subject_codes(subjects)
            
            assert result == expected_valid, f"Subjects {subjects}: expected {expected_valid}, got {result}"
            assert self.validator.get_error_count() == expected_errors, f"Subjects {subjects}: expected {expected_errors} errors, got {self.validator.get_error_count()}"
            
    def test_age_range_validation_comprehensive(self):
        """Test comprehensive age range validation."""
        test_cases = [
            # Valid cases
            (18, 65, True, 0),
            (0, 150, True, 0),
            (None, 65, True, 0),
            (18, None, True, 0),
            (None, None, True, 0),
            
            # Invalid cases
            (-5, 25, False, 1),    # Negative min
            (25, -5, False, 1),    # Negative max
            (200, 250, False, 2),  # Both unrealistic
            (65, 18, False, 1),    # Min > Max
        ]
        
        for min_age, max_age, expected_valid, expected_errors in test_cases:
            self.validator.clear_results()
            result = self.validator.validate_age_range(min_age, max_age)
            
            assert result == expected_valid, f"Ages {min_age}-{max_age}: expected {expected_valid}, got {result}"
            assert self.validator.get_error_count() == expected_errors, f"Ages {min_age}-{max_age}: expected {expected_errors} errors, got {self.validator.get_error_count()}"
            
    def test_file_path_validation_comprehensive(self):
        """Test comprehensive file path validation."""
        test_cases = [
            # Valid cases
            ({'interior': 'interior/book.pdf'}, True, 0),
            ({'cover': 'covers/book.pdf'}, True, 0),
            ({'interior': ''}, True, 0),  # Empty is valid
            
            # Invalid cases
            ({'interior': 'path/with<invalid>chars.pdf'}, False, 1),
            ({'cover': 'a' * 300 + '.pdf'}, False, 1),  # Too long
            ({'interior': 'path/with|pipe.pdf'}, False, 1),
        ]
        
        for paths, expected_valid, expected_errors in test_cases:
            self.validator.clear_results()
            result = self.validator.validate_file_paths(paths)
            
            assert result == expected_valid, f"Paths {paths}: expected {expected_valid}, got {result}"
            assert self.validator.get_error_count() == expected_errors, f"Paths {paths}: expected {expected_errors} errors, got {self.validator.get_error_count()}"
            
    def test_series_description_validation_comprehensive(self):
        """Test comprehensive series description validation."""
        test_cases = [
            # Valid cases
            ("This book in the Test Series series offers insights.", "Test Series", True),
            ("A comprehensive guide.", "Test Series", True),  # No "this book"
            ("This book offers insights.", None, True),  # No series
            ("", "Test Series", True),  # Empty description
            
            # Invalid cases (warnings, not errors)
            ("This book offers insights.", "Test Series", False),  # Missing series reference
        ]
        
        for description, series_name, expected_valid in test_cases:
            self.validator.clear_results()
            result = self.validator.validate_series_description(description, series_name)
            
            assert result == expected_valid, f"Description '{description}' with series '{series_name}': expected {expected_valid}, got {result}"
            
    def test_blank_fields_validation_comprehensive(self):
        """Test comprehensive blank fields validation."""
        test_cases = [
            # Valid cases
            ({'Field1': 'value', 'Field2': ''}, ['Field2'], True, 0),
            ({'Field1': 'value', 'Field2': '   '}, ['Field2'], True, 0),  # Whitespace only
            ({'Field1': 'value'}, ['Field2'], True, 0),  # Missing field is OK
            
            # Invalid cases
            ({'Field1': 'value', 'Field2': 'not_blank'}, ['Field2'], False, 1),
            ({'Field1': 'value', 'Field2': '  text  '}, ['Field2'], False, 1),  # Non-blank with whitespace
        ]
        
        for field_values, blank_fields, expected_valid, expected_errors in test_cases:
            self.validator.clear_results()
            result = self.validator.validate_blank_fields(field_values, blank_fields)
            
            assert result == expected_valid, f"Fields {field_values} with blank {blank_fields}: expected {expected_valid}, got {result}"
            assert self.validator.get_error_count() == expected_errors, f"Fields {field_values}: expected {expected_errors} errors, got {self.validator.get_error_count()}"
            
    def test_tranche_override_validation(self):
        """Test tranche override validation."""
        base_values = {
            'Field1': 'base_value1',
            'Field2': 'base_value2',
            'Field3': 'base_value3'
        }
        override_values = {
            'Field1': 'override_value1',  # Properly replaced
            'Field2': 'base_value2 appended',  # Properly appended
            'Field3': 'base_value3'  # Unchanged (should warn)
        }
        append_fields = ['Field2']
        
        result = self.validator.validate_tranche_overrides(
            base_values, override_values, append_fields
        )
        
        assert result is True  # No errors, but may have warnings
        assert self.validator.get_warning_count() > 0  # Should warn about unchanged field
        
    def test_field_mapping_completeness_validation(self):
        """Test field mapping completeness validation."""
        required_fields = ['Field1', 'Field2', 'Field3']
        
        # Complete mapping
        complete_mapping = {'Field1': 'value1', 'Field2': 'value2', 'Field3': 'value3'}
        self.validator.clear_results()
        result = self.validator.validate_field_mapping_completeness(required_fields, complete_mapping)
        assert result is True
        assert self.validator.get_error_count() == 0
        
        # Incomplete mapping
        incomplete_mapping = {'Field1': 'value1', 'Field3': 'value3'}  # Missing Field2
        self.validator.clear_results()
        result = self.validator.validate_field_mapping_completeness(required_fields, incomplete_mapping)
        assert result is False
        assert self.validator.get_error_count() > 0
        
    def test_validation_results_management(self):
        """Test validation results management."""
        # Start clean
        assert self.validator.get_error_count() == 0
        assert self.validator.get_warning_count() == 0
        assert not self.validator.has_errors()
        assert not self.validator.has_warnings()
        
        # Add some errors and warnings
        self.validator.errors.append("Test error")
        self.validator.warnings.append("Test warning")
        
        assert self.validator.get_error_count() == 1
        assert self.validator.get_warning_count() == 1
        assert self.validator.has_errors()
        assert self.validator.has_warnings()
        
        # Get results
        results = self.validator.get_validation_results()
        assert results['errors'] == ["Test error"]
        assert results['warnings'] == ["Test warning"]
        
        # Clear results
        self.validator.clear_results()
        assert self.validator.get_error_count() == 0
        assert self.validator.get_warning_count() == 0
        
    def test_edge_case_validation(self):
        """Test validation with edge cases."""
        edge_cases = {
            # Empty data
            'thema_subjects': [],
            'min_age': None,
            'max_age': None,
            'file_paths': {},
            'description': '',
            'series_name': None,
            'field_values': {},
            'blank_fields': []
        }
        
        result = self.validator.validate_all_corrections(edge_cases)
        
        # Should handle empty data gracefully
        assert result is True
        assert self.validator.get_error_count() == 0
        
    def test_validation_with_unicode_data(self):
        """Test validation with Unicode data."""
        unicode_data = {
            'thema_subjects': ['TGBN', 'JNFH'],
            'description': 'This book in the Tëst Sériës series offers insïghts with ünïcödë.',
            'series_name': 'Tëst Sériës',
            'file_paths': {
                'interior': 'interior/tëst_böök_interior.pdf'
            }
        }
        
        result = self.validator.validate_all_corrections(unicode_data)
        
        # Should handle Unicode data properly
        assert result is True
        assert self.validator.get_error_count() == 0
        
    def test_validation_performance_with_large_datasets(self):
        """Test validation performance with large datasets."""
        import time
        
        # Create large dataset
        large_data = {
            'thema_subjects': ['TGBN'] * 1000,  # Will be limited to 3
            'file_paths': {f'path_{i}': f'path/to/file_{i}.pdf' for i in range(100)},
            'field_values': {f'Field_{i}': f'value_{i}' for i in range(1000)},
            'blank_fields': [f'Field_{i}' for i in range(500, 1000)]  # Half should be blank
        }
        
        start_time = time.time()
        result = self.validator.validate_all_corrections(large_data)
        end_time = time.time()
        
        validation_time = end_time - start_time
        
        # Should complete validation in reasonable time (less than 1 second)
        assert validation_time < 1.0, f"Validation too slow: {validation_time:.3f}s"
        
        # Should have some errors (non-blank fields that should be blank)
        assert self.validator.get_error_count() > 0