"""
Unit tests for batch processing data models.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.imprint_builder.batch_models import (
    BatchConfig,
    OutputConfig,
    ProcessingOptions,
    ErrorHandlingConfig,
    ImprintRow,
    ImprintResult,
    BatchResult,
    ProcessingError,
    ProcessingWarning,
    ValidationResult,
    ProcessingPlan,
    ProcessingContext,
    SourceInfo,
    NamingStrategy,
    OrganizationStrategy,
    ErrorHandlingMode,
    create_default_config,
    validate_config
)


class TestDataModels:
    """Test basic data model functionality."""
    
    def test_processing_options_defaults(self):
        """Test ProcessingOptions default values."""
        options = ProcessingOptions()
        assert options.parallel_processing is False
        assert options.max_workers == 4
        assert options.continue_on_error is True
        assert options.validate_output is True
        assert options.timeout_seconds == 300
        assert options.retry_attempts == 3
        assert options.retry_delay == 1.0
    
    def test_output_config_path_conversion(self):
        """Test OutputConfig converts string paths to Path objects."""
        config = OutputConfig(base_directory="test/path")
        assert isinstance(config.base_directory, Path)
        assert str(config.base_directory) == "test/path"
    
    def test_output_config_defaults(self):
        """Test OutputConfig default values."""
        config = OutputConfig()
        assert config.naming_strategy == NamingStrategy.IMPRINT_NAME
        assert config.organization_strategy == OrganizationStrategy.BY_SOURCE
        assert config.create_index is True
        assert config.overwrite_existing is False
        assert config.create_subdirectories is True
    
    def test_batch_config_defaults(self):
        """Test BatchConfig default values."""
        config = BatchConfig()
        assert isinstance(config.column_mapping, dict)
        assert config.attributes is None
        assert config.subattributes is None
        assert isinstance(config.output_config, OutputConfig)
        assert isinstance(config.error_handling, ErrorHandlingConfig)
        assert isinstance(config.processing_options, ProcessingOptions)


class TestBatchConfigValidation:
    """Test BatchConfig validation functionality."""
    
    def test_valid_config(self):
        """Test validation of a valid configuration."""
        config = create_default_config()
        # Ensure parent directory exists for test
        config.output_config.base_directory.parent.mkdir(parents=True, exist_ok=True)
        
        errors = config.validate()
        assert len(errors) == 0
    
    def test_invalid_column_mapping(self):
        """Test validation with invalid column mapping."""
        config = BatchConfig(column_mapping="not_a_dict")
        errors = config.validate()
        assert any("column_mapping must be a dictionary" in error for error in errors)
    
    def test_invalid_attributes(self):
        """Test validation with invalid attributes."""
        config = BatchConfig(attributes="not_a_list")
        errors = config.validate()
        assert any("attributes must be a list or None" in error for error in errors)
        
        config = BatchConfig(attributes=[1, 2, 3])
        errors = config.validate()
        assert any("all attributes must be strings" in error for error in errors)
    
    def test_invalid_subattributes(self):
        """Test validation with invalid subattributes."""
        config = BatchConfig(subattributes="not_a_list")
        errors = config.validate()
        assert any("subattributes must be a list or None" in error for error in errors)
        
        config = BatchConfig(subattributes=[1, 2, 3])
        errors = config.validate()
        assert any("all subattributes must be strings" in error for error in errors)
    
    def test_invalid_max_workers(self):
        """Test validation with invalid max_workers."""
        config = BatchConfig()
        config.processing_options.max_workers = 0
        errors = config.validate()
        assert any("max_workers must be at least 1" in error for error in errors)
    
    def test_invalid_timeout(self):
        """Test validation with invalid timeout."""
        config = BatchConfig()
        config.processing_options.timeout_seconds = 0
        errors = config.validate()
        assert any("timeout_seconds must be at least 1" in error for error in errors)


class TestImprintRow:
    """Test ImprintRow functionality."""
    
    def test_path_conversion(self):
        """Test that string paths are converted to Path objects."""
        row = ImprintRow(
            row_number=1,
            imprint_concept="Test concept",
            source_file="test.csv"
        )
        assert isinstance(row.source_file, Path)
        assert str(row.source_file) == "test.csv"
    
    def test_source_info_creation(self):
        """Test automatic SourceInfo creation."""
        row = ImprintRow(
            row_number=1,
            imprint_concept="Test concept",
            source_file=Path("test.csv")
        )
        assert row.source_info is not None
        assert row.source_info.row_number == 1
        assert row.source_info.file_name == "test.csv"
    
    def test_get_display_name(self):
        """Test display name generation."""
        row = ImprintRow(
            row_number=1,
            imprint_concept="Modern Literary Press",
            source_file=Path("test.csv")
        )
        display_name = row.get_display_name()
        assert display_name == "modern_literary_press"
        
        # Test with empty concept
        row = ImprintRow(
            row_number=5,
            imprint_concept="",
            source_file=Path("test.csv")
        )
        display_name = row.get_display_name()
        assert display_name == "imprint_row_5"


class TestProcessingError:
    """Test ProcessingError functionality."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        error = ProcessingError(
            error_type="CSV_PARSING",
            message="Invalid CSV format",
            context={"file": "test.csv", "line": 5},
            exception=ValueError("Test error")
        )
        
        result = error.to_dict()
        assert result["error_type"] == "CSV_PARSING"
        assert result["message"] == "Invalid CSV format"
        assert result["context"]["file"] == "test.csv"
        assert result["exception_type"] == "ValueError"
        assert "timestamp" in result


class TestImprintResult:
    """Test ImprintResult functionality."""
    
    def test_path_conversion(self):
        """Test that string output paths are converted to Path objects."""
        row = ImprintRow(1, "Test", Path("test.csv"))
        result = ImprintResult(row=row, output_path="output.json")
        assert isinstance(result.output_path, Path)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        row = ImprintRow(1, "Test concept", Path("test.csv"))
        result = ImprintResult(
            row=row,
            success=True,
            processing_time=1.5,
            output_path=Path("output.json")
        )
        
        result_dict = result.to_dict()
        assert result_dict["row_number"] == 1
        assert result_dict["success"] is True
        assert result_dict["processing_time"] == 1.5
        assert result_dict["output_path"] == "output.json"


class TestBatchResult:
    """Test BatchResult functionality."""
    
    def test_path_conversion(self):
        """Test that string paths are converted to Path objects."""
        result = BatchResult(
            source_files=["file1.csv", "file2.csv"],
            index_file="index.json"
        )
        assert all(isinstance(f, Path) for f in result.source_files)
        assert isinstance(result.index_file, Path)
    
    def test_add_result(self):
        """Test adding results and counter updates."""
        batch_result = BatchResult(source_files=[])
        
        # Add successful result
        row = ImprintRow(1, "Test", Path("test.csv"))
        success_result = ImprintResult(row=row, success=True)
        batch_result.add_result(success_result)
        
        assert batch_result.total_processed == 1
        assert batch_result.successful == 1
        assert batch_result.failed == 0
        
        # Add failed result
        failed_result = ImprintResult(row=row, success=False)
        batch_result.add_result(failed_result)
        
        assert batch_result.total_processed == 2
        assert batch_result.successful == 1
        assert batch_result.failed == 1
    
    def test_success_rate(self):
        """Test success rate calculation."""
        batch_result = BatchResult(source_files=[])
        
        # Empty batch
        assert batch_result.get_success_rate() == 0.0
        
        # Add results
        row = ImprintRow(1, "Test", Path("test.csv"))
        batch_result.add_result(ImprintResult(row=row, success=True))
        batch_result.add_result(ImprintResult(row=row, success=True))
        batch_result.add_result(ImprintResult(row=row, success=False))
        
        assert batch_result.get_success_rate() == pytest.approx(66.67, rel=1e-2)
    
    def test_finalize(self):
        """Test batch result finalization."""
        batch_result = BatchResult(source_files=[])
        start_time = batch_result.start_time
        
        batch_result.finalize()
        
        assert batch_result.end_time is not None
        assert batch_result.end_time >= start_time
        assert batch_result.processing_time >= 0
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        batch_result = BatchResult(source_files=[Path("test.csv")])
        batch_result.finalize()
        
        result_dict = batch_result.to_dict()
        assert "source_files" in result_dict
        assert "total_processed" in result_dict
        assert "success_rate" in result_dict
        assert "processing_time" in result_dict


class TestValidationResult:
    """Test ValidationResult functionality."""
    
    def test_add_error(self):
        """Test adding errors."""
        result = ValidationResult(valid=True)
        result.add_error("Test error")
        
        assert result.valid is False
        assert "Test error" in result.errors
    
    def test_add_warning(self):
        """Test adding warnings."""
        result = ValidationResult(valid=True)
        result.add_warning("Test warning")
        
        assert result.valid is True  # Warnings don't affect validity
        assert "Test warning" in result.warnings


class TestProcessingPlan:
    """Test ProcessingPlan functionality."""
    
    def test_auto_ordering(self):
        """Test automatic processing order generation."""
        files = [Path("c.csv"), Path("a.csv"), Path("b.csv")]
        plan = ProcessingPlan(csv_files=files)
        
        assert plan.total_files == 3
        assert plan.processing_order == [Path("a.csv"), Path("b.csv"), Path("c.csv")]
    
    def test_custom_ordering(self):
        """Test custom processing order."""
        files = [Path("c.csv"), Path("a.csv"), Path("b.csv")]
        custom_order = [Path("b.csv"), Path("a.csv"), Path("c.csv")]
        plan = ProcessingPlan(csv_files=files, processing_order=custom_order)
        
        assert plan.processing_order == custom_order


class TestProcessingContext:
    """Test ProcessingContext functionality."""
    
    def test_path_conversion(self):
        """Test that string paths are converted to Path objects."""
        context = ProcessingContext(
            operation="test",
            file_path="test.csv"
        )
        assert isinstance(context.file_path, Path)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        context = ProcessingContext(
            operation="CSV_PARSING",
            file_path=Path("test.csv"),
            row_number=5,
            imprint_name="Test Imprint",
            additional_info={"column": "concept"}
        )
        
        result = context.to_dict()
        assert result["operation"] == "CSV_PARSING"
        assert result["file_path"] == "test.csv"
        assert result["row_number"] == 5
        assert result["imprint_name"] == "Test Imprint"
        assert result["column"] == "concept"


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_create_default_config(self):
        """Test default configuration creation."""
        config = create_default_config()
        
        assert isinstance(config, BatchConfig)
        assert "imprint_concept" in config.column_mapping.values()
        assert config.output_config.create_index is True
        assert config.processing_options.continue_on_error is True
    
    def test_validate_config(self):
        """Test configuration validation function."""
        config = create_default_config()
        # Ensure parent directory exists for test
        config.output_config.base_directory.parent.mkdir(parents=True, exist_ok=True)
        
        result = validate_config(config)
        assert result.valid is True
        assert len(result.errors) == 0
        
        # Test invalid config
        invalid_config = BatchConfig(column_mapping="invalid")
        result = validate_config(invalid_config)
        assert result.valid is False
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__])