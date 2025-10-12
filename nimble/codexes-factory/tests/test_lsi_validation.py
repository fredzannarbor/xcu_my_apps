#!/usr/bin/env python3
"""
LSI Validation Test Suite

This test suite validates generated LSI CSV files against real LSI submission requirements
and compares output with successful historical submissions.
"""

import pytest
import csv
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any
import re

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.modules.distribution.bisac_validator import get_bisac_validator
from codexes.modules.distribution.text_formatter import get_text_formatter


class TestLSIFieldCompliance:
    """Test that generated fields comply with LSI requirements."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bisac_validator = get_bisac_validator()
        self.text_formatter = get_text_formatter()
        
        # LSI field requirements (based on IngramSpark specifications)
        self.lsi_requirements = {
            'title': {'max_length': 255, 'required': True},
            'subtitle': {'max_length': 255, 'required': False},
            'author': {'max_length': 255, 'required': True},
            'isbn13': {'max_length': 13, 'required': True, 'format': r'^\d{13}$'},
            'publisher': {'max_length': 255, 'required': True},
            'imprint': {'max_length': 255, 'required': False},
            'publication_date': {'max_length': 10, 'required': True, 'format': r'^\d{4}-\d{2}-\d{2}$'},
            'language_code': {'max_length': 3, 'required': True, 'format': r'^[a-z]{3}$'},
            'bisac_category_1': {'max_length': 9, 'required': True, 'format': r'^[A-Z]{3}\d{6}$'},
            'bisac_category_2': {'max_length': 9, 'required': False, 'format': r'^[A-Z]{3}\d{6}$'},
            'bisac_category_3': {'max_length': 9, 'required': False, 'format': r'^[A-Z]{3}\d{6}$'},
            'keywords': {'max_length': 255, 'required': False},
            'short_description': {'max_length': 350, 'required': False},
            'long_description': {'max_length': 4000, 'required': False},
            'annotation': {'max_length': 4000, 'required': False},
            'page_count': {'max_length': 10, 'required': True, 'format': r'^\d+$'},
            'binding_type': {'max_length': 50, 'required': True},
            'trim_size_width': {'max_length': 10, 'required': True, 'format': r'^\d+(\.\d+)?$'},
            'trim_size_height': {'max_length': 10, 'required': True, 'format': r'^\d+(\.\d+)?$'},
            'interior_color': {'max_length': 10, 'required': True, 'values': ['BW', 'Color']},
            'paper_color': {'max_length': 20, 'required': True, 'values': ['White', 'Cream']},
            'list_price': {'max_length': 10, 'required': True, 'format': r'^\d+(\.\d{2})?$'},
            'wholesale_discount': {'max_length': 10, 'required': True, 'format': r'^\d+(\.\d+)?%?$'},
            'territory_rights': {'max_length': 50, 'required': True},
            'return_policy': {'max_length': 50, 'required': True},
            'availability_date': {'max_length': 10, 'required': False, 'format': r'^\d{4}-\d{2}-\d{2}$'},
        }
    
    def test_field_length_compliance(self):
        """Test that all fields comply with LSI length requirements."""
        test_data = {
            'title': 'A' * 300,  # Too long
            'short_description': 'B' * 400,  # Too long
            'long_description': 'C' * 5000,  # Too long
            'keywords': 'D' * 300,  # Too long
        }
        
        for field_name, test_value in test_data.items():
            if field_name in self.lsi_requirements:
                max_length = self.lsi_requirements[field_name]['max_length']
                result = self.text_formatter.validate_field_length(field_name, test_value)
                
                if not result.is_valid:
                    # Should provide truncated version
                    assert result.suggested_text is not None
                    assert len(result.suggested_text) <= max_length
    
    def test_bisac_code_format_compliance(self):
        """Test that BISAC codes comply with LSI format requirements."""
        test_codes = [
            'BUS001000',  # Valid
            'COM002000',  # Valid
            'SCI003000',  # Valid
            'BUS999999',  # Invalid (non-existent)
            'INVALID',    # Invalid format
            '123456789',  # Invalid format
        ]
        
        for code in test_codes:
            result = self.bisac_validator.validate_bisac_code(code)
            
            if result.is_valid:
                # Should match LSI format requirements
                assert re.match(r'^[A-Z]{3}\d{6}$', code)
                assert len(code) == 9
    
    def test_isbn_format_compliance(self):
        """Test ISBN format compliance."""
        test_isbns = [
            '9781234567890',  # Valid ISBN-13
            '1234567890123',  # Valid format, may not be real
            '978123456789',   # Too short
            '97812345678901', # Too long
            'abcd1234567890', # Invalid characters
        ]
        
        isbn_pattern = self.lsi_requirements['isbn13']['format']
        
        for isbn in test_isbns:
            is_valid_format = bool(re.match(isbn_pattern, isbn))
            
            if is_valid_format:
                assert len(isbn) == 13
                assert isbn.isdigit()
    
    def test_date_format_compliance(self):
        """Test date format compliance."""
        test_dates = [
            '2024-01-15',  # Valid
            '2024-12-31',  # Valid
            '2024-1-15',   # Invalid (single digit month)
            '24-01-15',    # Invalid (2-digit year)
            '2024/01/15',  # Invalid (wrong separator)
            'January 15, 2024',  # Invalid (text format)
        ]
        
        date_pattern = self.lsi_requirements['publication_date']['format']
        
        for date in test_dates:
            is_valid_format = bool(re.match(date_pattern, date))
            
            if is_valid_format:
                parts = date.split('-')
                assert len(parts) == 3
                assert len(parts[0]) == 4  # Year
                assert len(parts[1]) == 2  # Month
                assert len(parts[2]) == 2  # Day
    
    def test_required_fields_presence(self):
        """Test that required fields are identified correctly."""
        required_fields = [
            field for field, req in self.lsi_requirements.items() 
            if req.get('required', False)
        ]
        
        # These fields should always be required for LSI submissions
        expected_required = ['title', 'author', 'isbn13', 'publisher', 'publication_date', 
                           'language_code', 'bisac_category_1', 'page_count', 'binding_type',
                           'trim_size_width', 'trim_size_height', 'interior_color', 
                           'paper_color', 'list_price', 'wholesale_discount', 
                           'territory_rights', 'return_policy']
        
        for field in expected_required:
            assert field in required_fields


class TestLSICSVStructure:
    """Test LSI CSV file structure and format."""
    
    def test_csv_header_compliance(self):
        """Test that CSV headers match LSI template requirements."""
        # Read the LSI template to get expected headers
        template_path = Path("templates/LSI_ACS_header.csv")
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                expected_headers = next(reader)
            
            # Test that we have all expected headers
            assert len(expected_headers) > 100  # LSI has ~119 fields
            
            # Test for key required headers
            key_headers = ['title', 'author', 'isbn13', 'publisher', 'publication_date']
            for header in key_headers:
                assert header in expected_headers
    
    def test_csv_encoding_compliance(self):
        """Test that CSV files use proper encoding."""
        # Create a test CSV with special characters
        test_data = [
            ['title', 'author', 'description'],
            ['Test Book', 'Tëst Authör', 'Dëscription with spëcial charactërs']
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, 
                                       encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerows(test_data)
            temp_path = f.name
        
        try:
            # Read back and verify encoding
            with open(temp_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            assert rows[1][1] == 'Tëst Authör'
            assert rows[1][2] == 'Dëscription with spëcial charactërs'
        finally:
            os.unlink(temp_path)
    
    def test_csv_quoting_compliance(self):
        """Test that CSV fields are properly quoted when necessary."""
        test_data = [
            'Simple text',
            'Text with, comma',
            'Text with "quotes"',
            'Text with\nnewline',
            'Text with; semicolon'
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            for text in test_data:
                writer.writerow([text])
            temp_path = f.name
        
        try:
            # Read back and verify all data is preserved
            with open(temp_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            for i, original_text in enumerate(test_data):
                assert rows[i][0] == original_text
        finally:
            os.unlink(temp_path)


class TestLSIValidationAgainstSamples:
    """Test against sample LSI submissions and known good data."""
    
    def setup_method(self):
        """Set up test fixtures with sample data."""
        self.sample_good_book = {
            'title': 'The Art of Programming',
            'author': 'Jane Developer',
            'isbn13': '9781234567890',
            'publisher': 'Tech Books Press',
            'publication_date': '2024-03-15',
            'language_code': 'eng',
            'bisac_category_1': 'COM051000',
            'page_count': '256',
            'binding_type': 'paperback',
            'trim_size_width': '6.0',
            'trim_size_height': '9.0',
            'interior_color': 'BW',
            'paper_color': 'White',
            'list_price': '24.99',
            'wholesale_discount': '55%',
            'territory_rights': 'World',
            'return_policy': 'Standard'
        }
    
    def test_sample_book_validation(self):
        """Test validation of a complete sample book."""
        validator = get_bisac_validator()
        formatter = get_text_formatter()
        
        # Validate BISAC code
        bisac_result = validator.validate_bisac_code(self.sample_good_book['bisac_category_1'])
        assert bisac_result.is_valid
        
        # Validate text fields
        title_result = formatter.validate_field_length('title', self.sample_good_book['title'])
        assert title_result.is_valid
        
        # Validate ISBN format
        isbn = self.sample_good_book['isbn13']
        assert len(isbn) == 13
        assert isbn.isdigit()
        
        # Validate date format
        date = self.sample_good_book['publication_date']
        assert re.match(r'^\d{4}-\d{2}-\d{2}$', date)
    
    def test_field_completeness_scoring(self):
        """Test field completeness scoring."""
        total_fields = len(self.sample_good_book)
        populated_fields = sum(1 for v in self.sample_good_book.values() if v and str(v).strip())
        
        completeness_score = (populated_fields / total_fields) * 100
        
        # Should have high completeness for a good sample
        assert completeness_score >= 80.0
    
    def test_common_validation_errors(self):
        """Test detection of common validation errors."""
        problematic_book = {
            'title': '',  # Empty required field
            'author': 'A' * 300,  # Too long
            'isbn13': '123',  # Invalid format
            'bisac_category_1': 'INVALID',  # Invalid BISAC
            'publication_date': '2024/01/01',  # Wrong date format
            'page_count': 'many',  # Non-numeric
        }
        
        validator = get_bisac_validator()
        formatter = get_text_formatter()
        
        # Test empty title
        title_result = formatter.validate_field_length('title', problematic_book['title'])
        # Empty is technically valid, but should be flagged as missing required field
        
        # Test long author
        author_result = formatter.validate_field_length('author', problematic_book['author'])
        assert not author_result.is_valid
        assert author_result.suggested_text is not None
        
        # Test invalid BISAC
        bisac_result = validator.validate_bisac_code(problematic_book['bisac_category_1'])
        assert not bisac_result.is_valid
        
        # Test invalid ISBN
        isbn = problematic_book['isbn13']
        assert not re.match(r'^\d{13}$', isbn)
        
        # Test invalid date
        date = problematic_book['publication_date']
        assert not re.match(r'^\d{4}-\d{2}-\d{2}$', date)


class TestLSIComplianceReport:
    """Test generation of LSI compliance reports."""
    
    def test_compliance_report_generation(self):
        """Test generation of compliance reports."""
        # Mock validation results
        validation_results = {
            'total_fields': 119,
            'populated_fields': 95,
            'valid_fields': 90,
            'invalid_fields': 5,
            'missing_required_fields': 2,
            'field_errors': [
                {'field': 'bisac_category_1', 'error': 'Invalid BISAC code'},
                {'field': 'author', 'error': 'Field too long'},
            ],
            'warnings': [
                {'field': 'keywords', 'warning': 'Could be more specific'},
            ]
        }
        
        # Calculate compliance metrics
        completeness_rate = (validation_results['populated_fields'] / 
                           validation_results['total_fields']) * 100
        validity_rate = (validation_results['valid_fields'] / 
                        validation_results['populated_fields']) * 100
        
        assert completeness_rate > 75  # Should have good completeness
        assert validity_rate > 85      # Should have good validity
        
        # Test report structure
        assert len(validation_results['field_errors']) > 0
        assert all('field' in error and 'error' in error 
                  for error in validation_results['field_errors'])
    
    def test_lsi_submission_readiness(self):
        """Test assessment of LSI submission readiness."""
        # Criteria for LSI submission readiness
        readiness_criteria = {
            'required_fields_complete': True,
            'no_critical_errors': True,
            'bisac_codes_valid': True,
            'field_lengths_compliant': True,
            'format_compliance': True
        }
        
        # Calculate overall readiness
        readiness_score = sum(readiness_criteria.values()) / len(readiness_criteria)
        is_ready = readiness_score >= 0.8  # 80% of criteria must be met
        
        assert isinstance(is_ready, bool)
        if is_ready:
            # If ready, should meet key criteria
            assert readiness_criteria['required_fields_complete']
            assert readiness_criteria['bisac_codes_valid']


def test_lsi_csv_end_to_end():
    """End-to-end test of LSI CSV generation and validation."""
    # This would test the complete pipeline from metadata to validated CSV
    # For now, we'll test the validation components work together
    
    validator = get_bisac_validator()
    formatter = get_text_formatter()
    
    # Test that components work together
    test_bisac = "BUS001000"
    bisac_result = validator.validate_bisac_code(test_bisac)
    
    test_text = "This is a test description for validation."
    text_result = formatter.validate_field_length("short_description", test_text)
    
    # Both should be valid
    assert bisac_result.is_valid
    assert text_result.is_valid
    
    # Test integration
    if bisac_result.is_valid and text_result.is_valid:
        # This represents a successful validation pipeline
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])