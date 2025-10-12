"""
Tests for JSONMetadataExtractor
"""

import pytest
import json
from codexes.modules.distribution.json_metadata_extractor import JSONMetadataExtractor


class TestJSONMetadataExtractor:
    """Test cases for JSONMetadataExtractor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = JSONMetadataExtractor()
        
    def test_extract_thema_subjects_empty(self):
        """Test thema extraction with empty metadata."""
        metadata = {}
        result = self.extractor.extract_thema_subjects(metadata)
        assert result == []
        
    def test_extract_thema_subjects_list(self):
        """Test thema extraction with list format."""
        metadata = {'thema': ['TGBN', 'JNFH', 'JFFG']}
        result = self.extractor.extract_thema_subjects(metadata)
        assert result == ['TGBN', 'JNFH', 'JFFG']
        
    def test_extract_thema_subjects_dict(self):
        """Test thema extraction with dictionary format."""
        metadata = {
            'thema': {
                'thema_subject_1': 'TGBN',
                'thema_subject_2': 'JNFH',
                'thema_subject_3': 'JFFG'
            }
        }
        result = self.extractor.extract_thema_subjects(metadata)
        assert result == ['TGBN', 'JNFH', 'JFFG']
        
    def test_extract_thema_subjects_json_string(self):
        """Test thema extraction with JSON string format."""
        thema_json = json.dumps({
            'thema_subject_1': 'TGBN',
            'thema_subject_2': 'JNFH'
        })
        metadata = {'thema': thema_json}
        result = self.extractor.extract_thema_subjects(metadata)
        assert result == ['TGBN', 'JNFH']
        
    def test_extract_thema_subjects_limit_three(self):
        """Test thema extraction limits to 3 subjects."""
        metadata = {'thema': ['TGBN', 'JNFH', 'JFFG', 'EXTRA1', 'EXTRA2']}
        result = self.extractor.extract_thema_subjects(metadata)
        assert len(result) == 3
        assert result == ['TGBN', 'JNFH', 'JFFG']
        
    def test_extract_thema_subjects_invalid_codes(self):
        """Test thema extraction with invalid codes."""
        metadata = {'thema': ['TGBN', '123', 'VALID', '']}
        result = self.extractor.extract_thema_subjects(metadata)
        assert result == ['TGBN', 'VALID']
        assert len(self.extractor.get_warnings()) > 0
        
    def test_validate_age_value_valid(self):
        """Test age validation with valid values."""
        assert self.extractor.validate_age_value(18) == 18
        assert self.extractor.validate_age_value('25') == 25
        assert self.extractor.validate_age_value('18.0') == 18
        
    def test_validate_age_value_invalid(self):
        """Test age validation with invalid values."""
        assert self.extractor.validate_age_value(-5) is None
        assert self.extractor.validate_age_value(200) is None
        assert self.extractor.validate_age_value('adult') is None
        assert self.extractor.validate_age_value('invalid') is None
        assert self.extractor.validate_age_value(None) is None
        assert self.extractor.validate_age_value('') is None
        
    def test_extract_age_range_direct(self):
        """Test age range extraction with direct fields."""
        metadata = {'min_age': 18, 'max_age': 65}
        min_age, max_age = self.extractor.extract_age_range(metadata)
        assert min_age == 18
        assert max_age == 65
        
    def test_extract_age_range_nested(self):
        """Test age range extraction with nested structure."""
        metadata = {
            'age_range': {
                'min': 16,
                'max': 'adult'
            }
        }
        min_age, max_age = self.extractor.extract_age_range(metadata)
        assert min_age == 16
        assert max_age is None
        
    def test_extract_age_range_json_string(self):
        """Test age range extraction with JSON string."""
        metadata = {
            'min_age': '{"min_age": "18", "max_age": "Adult"}',
            'max_age': '{"min_age": "18", "max_age": "Adult"}'
        }
        min_age, max_age = self.extractor.extract_age_range(metadata)
        assert min_age == 18
        assert max_age is None
        
    def test_extract_age_range_invalid_range(self):
        """Test age range extraction with invalid range."""
        metadata = {'min_age': 65, 'max_age': 18}
        min_age, max_age = self.extractor.extract_age_range(metadata)
        assert min_age == 65
        assert max_age == 18
        assert len(self.extractor.get_warnings()) > 0
        
    def test_extract_series_info_simple(self):
        """Test series info extraction with simple fields."""
        metadata = {
            'series_name': 'Test Series',
            'series_number': 2
        }
        name, number = self.extractor.extract_series_info(metadata)
        assert name == 'Test Series'
        assert number == 2
        
    def test_extract_series_info_nested(self):
        """Test series info extraction with nested structure."""
        metadata = {
            'series': {
                'name': 'Nested Series',
                'number': 3
            }
        }
        name, number = self.extractor.extract_series_info(metadata)
        assert name == 'Nested Series'
        assert number == 3
        
    def test_extract_series_info_string_series(self):
        """Test series info extraction with string series field."""
        metadata = {
            'series': 'String Series Name',
            'number_in_series': '5'
        }
        name, number = self.extractor.extract_series_info(metadata)
        assert name == 'String Series Name'
        assert number == 5
        
    def test_extract_series_info_empty(self):
        """Test series info extraction with empty metadata."""
        metadata = {}
        name, number = self.extractor.extract_series_info(metadata)
        assert name is None
        assert number is None
        
    def test_extract_series_info_empty_name(self):
        """Test series info extraction with empty series name."""
        metadata = {'series_name': '   ', 'series_number': 1}
        name, number = self.extractor.extract_series_info(metadata)
        assert name is None
        assert number == 1
        
    def test_validate_thema_code_valid(self):
        """Test thema code validation with valid codes."""
        assert self.extractor._validate_thema_code('TGBN')
        assert self.extractor._validate_thema_code('JNFH')
        assert self.extractor._validate_thema_code('ABC123')
        
    def test_validate_thema_code_invalid(self):
        """Test thema code validation with invalid codes."""
        assert not self.extractor._validate_thema_code('')
        assert not self.extractor._validate_thema_code('1ABC')
        assert not self.extractor._validate_thema_code('A')
        assert not self.extractor._validate_thema_code('TOOLONGCODE123')
        assert not self.extractor._validate_thema_code('AB-CD')
        assert not self.extractor._validate_thema_code(None)
        
    def test_clear_messages(self):
        """Test clearing warnings and errors."""
        # Generate some warnings
        self.extractor.validate_age_value(-5)
        self.extractor.validate_age_value('invalid')
        
        assert len(self.extractor.get_warnings()) > 0
        
        self.extractor.clear_messages()
        assert len(self.extractor.get_warnings()) == 0
        assert len(self.extractor.get_errors()) == 0