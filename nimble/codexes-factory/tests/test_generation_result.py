# tests/test_generation_result.py

import pytest
from datetime import datetime
from codexes.modules.distribution.generation_result import (
    GenerationResult, FieldStatistics, GenerationReporter
)
from codexes.modules.verifiers.validation_framework import ValidationResult


class TestFieldStatistics:
    """Test FieldStatistics functionality."""
    
    def test_field_statistics_creation(self):
        """Test creating field statistics."""
        stats = FieldStatistics()
        assert stats.total_fields == 0
        assert stats.populated_fields == 0
        assert stats.empty_fields == 0
        assert stats.population_percentage == 0.0
    
    def test_population_percentage_calculation(self):
        """Test population percentage calculation."""
        stats = FieldStatistics(
            total_fields=100,
            populated_fields=75,
            empty_fields=25
        )
        assert stats.population_percentage == 75.0
    
    def test_population_percentage_zero_total(self):
        """Test population percentage with zero total fields."""
        stats = FieldStatistics(total_fields=0, populated_fields=0)
        assert stats.population_percentage == 0.0
    
    def test_to_dict(self):
        """Test converting field statistics to dictionary."""
        stats = FieldStatistics(
            total_fields=100,
            populated_fields=80,
            empty_fields=20,
            computed_fields=10,
            default_fields=5
        )
        
        result = stats.to_dict()
        expected = {
            "total_fields": 100,
            "populated_fields": 80,
            "empty_fields": 20,
            "computed_fields": 10,
            "default_fields": 5,
            "population_percentage": 80.0
        }
        assert result == expected


class TestGenerationResult:
    """Test GenerationResult functionality."""
    
    def test_generation_result_creation(self):
        """Test creating a generation result."""
        validation_result = ValidationResult(is_valid=True)
        result = GenerationResult(
            success=True,
            output_path="/test/output.csv",
            validation_result=validation_result
        )
        
        assert result.success is True
        assert result.output_path == "/test/output.csv"
        assert result.validation_result == validation_result
        assert isinstance(result.field_statistics, FieldStatistics)
        assert len(result.populated_fields) == 0
        assert len(result.empty_fields) == 0
    
    def test_add_populated_field(self):
        """Test adding populated fields."""
        result = GenerationResult(
            success=True,
            output_path="/test/output.csv",
            validation_result=ValidationResult(is_valid=True)
        )
        
        result.add_populated_field("Title", "Test Book", "direct")
        result.add_populated_field("Weight", "1.5", "computed")
        result.add_populated_field("Publisher", "Default Pub", "default")
        
        assert len(result.populated_fields) == 3
        assert result.populated_fields["Title"] == "Test Book"
        assert len(result.computed_fields) == 1
        assert result.computed_fields["Weight"] == "1.5"
        assert len(result.default_fields) == 1
        assert result.default_fields["Publisher"] == "Default Pub"
    
    def test_add_empty_field(self):
        """Test adding empty fields."""
        result = GenerationResult(
            success=True,
            output_path="/test/output.csv",
            validation_result=ValidationResult(is_valid=True)
        )
        
        result.add_empty_field("ISBN")
        result.add_empty_field("Author")
        
        assert len(result.empty_fields) == 2
        assert "ISBN" in result.empty_fields
        assert "Author" in result.empty_fields
    
    def test_update_field_statistics(self):
        """Test updating field statistics."""
        result = GenerationResult(
            success=True,
            output_path="/test/output.csv",
            validation_result=ValidationResult(is_valid=True)
        )
        
        result.add_populated_field("Title", "Test Book", "direct")
        result.add_populated_field("Weight", "1.5", "computed")
        result.add_empty_field("ISBN")
        result.add_empty_field("Author")
        
        result.update_field_statistics()
        
        assert result.field_statistics.total_fields == 4
        assert result.field_statistics.populated_fields == 2
        assert result.field_statistics.empty_fields == 2
        assert result.field_statistics.computed_fields == 1
        assert result.field_statistics.population_percentage == 50.0
    
    def test_get_summary_success(self):
        """Test getting summary for successful generation."""
        result = GenerationResult(
            success=True,
            output_path="/test/output.csv",
            validation_result=ValidationResult(is_valid=True)
        )
        
        result.field_statistics.total_fields = 100
        result.field_statistics.populated_fields = 85
        
        summary = result.get_summary()
        assert "Generation SUCCESS" in summary
        assert "85/100 fields populated" in summary
        assert "85.0%" in summary
    
    def test_get_summary_failure(self):
        """Test getting summary for failed generation."""
        result = GenerationResult(
            success=False,
            output_path="/test/output.csv",
            validation_result=ValidationResult(is_valid=False)
        )
        
        result.add_generation_error("Test error")
        
        summary = result.get_summary()
        assert "Generation FAILED" in summary
        assert "1 errors" in summary
    
    def test_get_detailed_report(self):
        """Test getting detailed report."""
        validation_result = ValidationResult(is_valid=True)
        validation_result.warnings = ["Test warning"]
        
        result = GenerationResult(
            success=True,
            output_path="/test/output.csv",
            validation_result=validation_result
        )
        
        result.add_populated_field("Title", "Test Book")
        result.add_empty_field("ISBN")
        result.add_generation_warning("Test generation warning")
        result.update_field_statistics()
        
        report = result.get_detailed_report()
        
        assert "LSI ACS GENERATION REPORT" in report
        assert "Status: SUCCESS" in report
        assert "Output File: /test/output.csv" in report
        assert "FIELD STATISTICS:" in report
        assert "VALIDATION RESULTS:" in report
        assert "GENERATION WARNINGS:" in report
        assert "SAMPLE POPULATED FIELDS:" in report
    
    def test_to_dict(self):
        """Test converting generation result to dictionary."""
        validation_result = ValidationResult(is_valid=True)
        result = GenerationResult(
            success=True,
            output_path="/test/output.csv",
            validation_result=validation_result
        )
        
        result.add_populated_field("Title", "Test Book")
        result.add_empty_field("ISBN")
        result.update_field_statistics()
        
        result_dict = result.to_dict()
        
        assert result_dict["success"] is True
        assert result_dict["output_path"] == "/test/output.csv"
        assert "field_statistics" in result_dict
        assert "validation_summary" in result_dict
        assert result_dict["populated_fields_count"] == 1
        assert result_dict["empty_fields_count"] == 1


class TestGenerationReporter:
    """Test GenerationReporter functionality."""
    
    def test_start_generation(self):
        """Test starting generation tracking."""
        reporter = GenerationReporter()
        result = reporter.start_generation("/test/output.csv")
        
        assert result is not None
        assert result.output_path == "/test/output.csv"
        assert result.success is False  # Initially false
        assert reporter.start_time is not None
        assert reporter.result == result
    
    def test_complete_generation_success(self):
        """Test completing successful generation."""
        reporter = GenerationReporter()
        result = reporter.start_generation("/test/output.csv")
        
        validation_result = ValidationResult(is_valid=True)
        reporter.complete_generation(True, validation_result)
        
        assert result.success is True
        assert result.validation_result == validation_result
        assert result.generation_duration_ms > 0
    
    def test_complete_generation_failure(self):
        """Test completing failed generation."""
        reporter = GenerationReporter()
        result = reporter.start_generation("/test/output.csv")
        
        validation_result = ValidationResult(is_valid=False)
        validation_result.errors = ["Test error"]
        
        reporter.complete_generation(False, validation_result)
        
        assert result.success is False
        assert result.validation_result == validation_result
        assert result.generation_duration_ms > 0
    
    def test_track_field_mapping(self):
        """Test tracking field mappings."""
        reporter = GenerationReporter()
        result = reporter.start_generation("/test/output.csv")
        
        reporter.track_field_mapping("Title", "Test Book", "direct")
        reporter.track_field_mapping("Weight", "1.5", "computed")
        reporter.track_field_mapping("ISBN", "", "empty")
        
        assert len(result.populated_fields) == 2
        assert len(result.empty_fields) == 1
        assert result.populated_fields["Title"] == "Test Book"
        assert result.computed_fields["Weight"] == "1.5"
        assert "ISBN" in result.empty_fields
    
    def test_add_error_and_warning(self):
        """Test adding errors and warnings."""
        reporter = GenerationReporter()
        result = reporter.start_generation("/test/output.csv")
        
        reporter.add_error("Test error")
        reporter.add_warning("Test warning")
        
        assert len(result.generation_errors) == 1
        assert len(result.generation_warnings) == 1
        assert result.generation_errors[0] == "Test error"
        assert result.generation_warnings[0] == "Test warning"
    
    def test_complete_generation_without_start(self):
        """Test completing generation without starting."""
        reporter = GenerationReporter()
        
        with pytest.raises(ValueError, match="Generation tracking not started"):
            reporter.complete_generation(True)
    
    def test_get_result(self):
        """Test getting the current result."""
        reporter = GenerationReporter()
        
        # Initially no result
        assert reporter.get_result() is None
        
        # After starting generation
        result = reporter.start_generation("/test/output.csv")
        assert reporter.get_result() == result