"""
Tests for SeriesDescriptionProcessor
"""

import pytest
from codexes.modules.distribution.series_description_processor import SeriesDescriptionProcessor


class TestSeriesDescriptionProcessor:
    """Test cases for SeriesDescriptionProcessor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = SeriesDescriptionProcessor()
        
    def test_process_description_no_series(self):
        """Test processing description with no series."""
        description = "This book offers valuable insights."
        result = self.processor.process_description(description, None)
        assert result == description
        
    def test_process_description_empty_series(self):
        """Test processing description with empty series."""
        description = "This book offers valuable insights."
        result = self.processor.process_description(description, "")
        assert result == description
        
    def test_process_description_with_series(self):
        """Test processing description with valid series."""
        description = "This book offers valuable insights."
        series_name = "Test Series"
        result = self.processor.process_description(description, series_name)
        expected = "This book in the Test Series series offers valuable insights."
        assert result == expected
        
    def test_process_description_lowercase_this_book(self):
        """Test processing description with lowercase 'this book'."""
        description = "In conclusion, this book provides comprehensive coverage."
        series_name = "Academic Series"
        result = self.processor.process_description(description, series_name)
        expected = "In conclusion, this book in the Academic Series series provides comprehensive coverage."
        assert result == expected
        
    def test_process_description_multiple_occurrences(self):
        """Test processing description with multiple 'this book' occurrences."""
        description = "This book is great. Later, this book explains more."
        series_name = "Multi Series"
        result = self.processor.process_description(description, series_name)
        expected = "This book in the Multi Series series is great. Later, this book in the Multi Series series explains more."
        assert result == expected
        
    def test_process_description_no_this_book(self):
        """Test processing description without 'this book'."""
        description = "A comprehensive guide to advanced topics."
        series_name = "Guide Series"
        result = self.processor.process_description(description, series_name)
        assert result == description  # Should remain unchanged
        
    def test_process_description_empty_description(self):
        """Test processing empty description."""
        result = self.processor.process_description("", "Test Series")
        assert result == ""
        
    def test_process_description_none_description(self):
        """Test processing None description."""
        result = self.processor.process_description(None, "Test Series")
        assert result == ""
        
    def test_has_series_context_valid(self):
        """Test has_series_context with valid series names."""
        assert self.processor.has_series_context("Test Series")
        assert self.processor.has_series_context("Academic Collection")
        assert self.processor.has_series_context("X")  # Single character but valid
        
    def test_has_series_context_invalid(self):
        """Test has_series_context with invalid series names."""
        assert not self.processor.has_series_context(None)
        assert not self.processor.has_series_context("")
        assert not self.processor.has_series_context("   ")
        assert not self.processor.has_series_context("n/a")
        assert not self.processor.has_series_context("N/A")
        assert not self.processor.has_series_context("none")
        assert not self.processor.has_series_context("null")
        assert not self.processor.has_series_context("series")
        assert not self.processor.has_series_context("A")  # Too short
        
    def test_extract_series_from_description(self):
        """Test extracting series name from description."""
        descriptions = [
            ("This book in the Fantasy Adventures series explores...", "Fantasy Adventures"),
            ("Part of the Science Fiction series, this work...", "Science Fiction"),
            ("From the Mystery Collection series comes...", "Mystery Collection"),
            ("A Historical Fiction series book that...", "Historical Fiction"),
            ("No series reference here.", None),
        ]
        
        for description, expected in descriptions:
            result = self.processor.extract_series_from_description(description)
            assert result == expected
            
    def test_validate_processed_description_no_series(self):
        """Test validation with no series."""
        description = "This book offers insights."
        assert self.processor.validate_processed_description(description, None)
        assert self.processor.validate_processed_description(description, "")
        
    def test_validate_processed_description_with_series(self):
        """Test validation with series."""
        series_name = "Test Series"
        valid_description = "This book in the Test Series series offers insights."
        invalid_description = "This book offers insights."
        
        assert self.processor.validate_processed_description(valid_description, series_name)
        assert not self.processor.validate_processed_description(invalid_description, series_name)
        
    def test_get_series_aware_replacement(self):
        """Test getting series-aware replacements."""
        series_name = "Adventure Series"
        
        test_cases = [
            ("This book", "This book in the Adventure Series series"),
            ("this book", "this book in the Adventure Series series"),
            ("This book offers", "This book in the Adventure Series series offers"),
            ("other phrase", "other phrase in the Adventure Series series"),
        ]
        
        for original, expected in test_cases:
            result = self.processor.get_series_aware_replacement(original, series_name)
            assert result == expected
            
    def test_process_description_whitespace_series(self):
        """Test processing with series name that has extra whitespace."""
        description = "This book is excellent."
        series_name = "  Spaced Series  "
        result = self.processor.process_description(description, series_name)
        expected = "This book in the Spaced Series series is excellent."
        assert result == expected
        
    def test_process_description_special_characters_series(self):
        """Test processing with series name containing special characters."""
        description = "This book covers advanced topics."
        series_name = "Tech & Science"
        result = self.processor.process_description(description, series_name)
        expected = "This book in the Tech & Science series covers advanced topics."
        assert result == expected