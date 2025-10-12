"""
Unit tests for OutputManager component.
"""

import pytest
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.imprint_builder.output_manager import OutputManager, create_output_manager
from codexes.modules.imprint_builder.batch_models import (
    OutputConfig,
    ImprintRow,
    ImprintResult,
    BatchResult,
    ProcessingWarning,
    NamingStrategy,
    OrganizationStrategy
)
from codexes.modules.imprint_builder.imprint_expander import ExpandedImprint, DictWrapper


class TestOutputManager:
    """Test OutputManager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = OutputConfig(
            base_directory=self.temp_dir,
            naming_strategy=NamingStrategy.IMPRINT_NAME,
            organization_strategy=OrganizationStrategy.FLAT,
            create_index=True
        )
        self.output_manager = OutputManager(self.config)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.cleanup_directory(self.temp_dir)
    
    def cleanup_directory(self, directory: Path):
        """Recursively clean up a directory."""
        if directory.exists():
            for item in directory.iterdir():
                if item.is_dir():
                    self.cleanup_directory(item)
                else:
                    item.unlink()
            directory.rmdir()
    
    def create_test_imprint_row(self, row_number: int = 1, concept: str = "Test Imprint") -> ImprintRow:
        """Create a test imprint row."""
        return ImprintRow(
            row_number=row_number,
            imprint_concept=concept,
            source_file=Path("test.csv"),
            additional_data={"extra": "data"}
        )
    
    def create_mock_expanded_imprint(self, imprint_name: str = "Test Imprint") -> ExpandedImprint:
        """Create a mock expanded imprint."""
        mock_concept = Mock()
        mock_concept.name = imprint_name
        
        branding = DictWrapper({
            "imprint_name": imprint_name,
            "mission_statement": "Test mission",
            "brand_values": ["Quality", "Innovation"]
        })
        
        return ExpandedImprint(
            concept=mock_concept,
            branding=branding,
            design_specifications=DictWrapper({}),
            publishing_strategy=DictWrapper({}),
            operational_framework=DictWrapper({}),
            marketing_approach=DictWrapper({}),
            financial_projections=DictWrapper({}),
            expanded_at=datetime.now()
        )
    
    def test_initialization(self):
        """Test OutputManager initialization."""
        assert self.output_manager.config == self.config
        assert self.temp_dir.exists()
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test invalid characters
        assert self.output_manager._sanitize_filename("test<>file") == "test_file"
        
        # Test spaces
        assert self.output_manager._sanitize_filename("test file name") == "test_file_name"
        
        # Test multiple underscores
        assert self.output_manager._sanitize_filename("test___file") == "test_file"
        
        # Test leading/trailing underscores
        assert self.output_manager._sanitize_filename("_test_file_") == "test_file"
        
        # Test empty string
        assert self.output_manager._sanitize_filename("") == "unnamed"
        
        # Test long filename
        long_name = "a" * 150
        result = self.output_manager._sanitize_filename(long_name)
        assert len(result) == 100
    
    def test_generate_filename_imprint_name(self):
        """Test filename generation with imprint name strategy."""
        source_info = {"row_number": 1, "source_file": Path("test.csv")}
        
        filename = self.output_manager._generate_filename("test_imprint", source_info)
        assert filename == "test_imprint"
        
        # Test empty name
        filename = self.output_manager._generate_filename("", source_info)
        assert filename == "unnamed_imprint"
    
    def test_generate_filename_row_number(self):
        """Test filename generation with row number strategy."""
        self.config.naming_strategy = NamingStrategy.ROW_NUMBER
        source_info = {"row_number": 5, "source_file": Path("test.csv")}
        
        filename = self.output_manager._generate_filename("test_imprint", source_info)
        assert filename == "test_row_5"
    
    def test_generate_filename_hybrid(self):
        """Test filename generation with hybrid strategy."""
        self.config.naming_strategy = NamingStrategy.HYBRID
        source_info = {"row_number": 3, "source_file": Path("test.csv")}
        
        # With imprint name
        filename = self.output_manager._generate_filename("test_imprint", source_info)
        assert filename == "test_imprint_row_3"
        
        # Without imprint name
        filename = self.output_manager._generate_filename("", source_info)
        assert filename == "test_row_3"
    
    def test_generate_directory_path_flat(self):
        """Test directory path generation with flat strategy."""
        source_info = {"source_file": Path("test.csv"), "imprint_name": "Test"}
        
        directory = self.output_manager._generate_directory_path(source_info)
        assert directory == self.temp_dir
    
    def test_generate_directory_path_by_source(self):
        """Test directory path generation by source strategy."""
        self.config.organization_strategy = OrganizationStrategy.BY_SOURCE
        source_info = {"source_file": Path("test_file.csv"), "imprint_name": "Test"}
        
        directory = self.output_manager._generate_directory_path(source_info)
        assert directory == self.temp_dir / "test_file"
    
    def test_generate_directory_path_by_imprint(self):
        """Test directory path generation by imprint strategy."""
        self.config.organization_strategy = OrganizationStrategy.BY_IMPRINT
        source_info = {"source_file": Path("test.csv"), "imprint_name": "Test Imprint"}
        
        directory = self.output_manager._generate_directory_path(source_info)
        assert directory == self.temp_dir / "test_imprint"
    
    def test_ensure_unique_naming(self):
        """Test unique naming functionality."""
        # Create a file
        test_file = self.temp_dir / "test.json"
        test_file.write_text("{}")
        
        # Should generate unique name
        unique_path = self.output_manager.ensure_unique_naming(test_file)
        assert unique_path == self.temp_dir / "test_1.json"
        
        # Test with overwrite enabled
        self.config.overwrite_existing = True
        unique_path = self.output_manager.ensure_unique_naming(test_file)
        assert unique_path == test_file
    
    def test_generate_output_path(self):
        """Test complete output path generation."""
        source_info = {
            "row_number": 1,
            "source_file": Path("test.csv"),
            "imprint_name": "Test Imprint"
        }
        
        output_path = self.output_manager.generate_output_path("Test Imprint", source_info)
        
        assert output_path.parent == self.temp_dir
        assert output_path.name == "test_imprint.json"
    
    def test_extract_imprint_name(self):
        """Test imprint name extraction from result."""
        # Create result with expanded imprint
        row = self.create_test_imprint_row()
        expanded = self.create_mock_expanded_imprint("Extracted Name")
        result = ImprintResult(row=row, expanded_imprint=expanded, success=True)
        
        name = self.output_manager._extract_imprint_name(result)
        assert name == "Extracted Name"
        
        # Test fallback to row display name
        result_no_expanded = ImprintResult(row=row, success=False)
        name = self.output_manager._extract_imprint_name(result_no_expanded)
        assert name == row.get_display_name()
    
    def test_prepare_output_data(self):
        """Test output data preparation."""
        row = self.create_test_imprint_row()
        expanded = self.create_mock_expanded_imprint()
        warning = ProcessingWarning("Test warning", {"context": "test"})
        
        result = ImprintResult(
            row=row,
            expanded_imprint=expanded,
            success=True,
            processing_time=1.5,
            warnings=[warning]
        )
        
        output_data = self.output_manager._prepare_output_data(result)
        
        # Check structure
        assert "metadata" in output_data
        assert "source_data" in output_data
        assert "expanded_imprint" in output_data
        assert "warnings" in output_data
        
        # Check metadata
        assert output_data["metadata"]["success"] is True
        assert output_data["metadata"]["processing_time"] == 1.5
        
        # Check source data
        assert output_data["source_data"]["imprint_concept"] == "Test Imprint"
        
        # Check warnings
        assert len(output_data["warnings"]) == 1
    
    def test_prepare_output_data_with_error(self):
        """Test output data preparation with error."""
        row = self.create_test_imprint_row()
        error = ValueError("Test error")
        
        result = ImprintResult(
            row=row,
            success=False,
            error=error
        )
        
        output_data = self.output_manager._prepare_output_data(result)
        
        assert "error" in output_data
        assert output_data["error"]["type"] == "ValueError"
        assert output_data["error"]["message"] == "Test error"
    
    def test_write_imprint_result(self):
        """Test writing imprint result to file."""
        row = self.create_test_imprint_row()
        expanded = self.create_mock_expanded_imprint()
        
        result = ImprintResult(
            row=row,
            expanded_imprint=expanded,
            success=True,
            processing_time=1.0
        )
        
        # Write result
        output_path = self.output_manager.write_imprint_result(result)
        
        # Verify file was created
        assert output_path.exists()
        assert output_path.suffix == ".json"
        
        # Verify content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["metadata"]["success"] is True
        assert "expanded_imprint" in data
        
        # Verify result was updated with output path
        assert result.output_path == output_path
    
    def test_write_imprint_result_with_subdirectories(self):
        """Test writing with subdirectory creation."""
        self.config.organization_strategy = OrganizationStrategy.BY_SOURCE
        self.config.create_subdirectories = True
        
        row = self.create_test_imprint_row()
        expanded = self.create_mock_expanded_imprint()
        
        result = ImprintResult(
            row=row,
            expanded_imprint=expanded,
            success=True
        )
        
        output_path = self.output_manager.write_imprint_result(result)
        
        # Should create subdirectory
        assert output_path.parent.name == "test"
        assert output_path.exists()
    
    def test_write_imprint_result_io_error(self):
        """Test handling of IO errors during writing."""
        # Create read-only directory
        readonly_dir = self.temp_dir / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only
        
        try:
            config = OutputConfig(base_directory=readonly_dir)
            manager = OutputManager(config)
            
            row = self.create_test_imprint_row()
            result = ImprintResult(row=row, success=True)
            
            with pytest.raises(IOError):
                manager.write_imprint_result(result)
        
        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)
    
    def test_create_index_file(self):
        """Test index file creation."""
        # Create batch result
        batch_result = BatchResult(source_files=[Path("test.csv")])
        
        # Add some results
        row1 = self.create_test_imprint_row(1, "Imprint 1")
        result1 = ImprintResult(row=row1, success=True, processing_time=1.0)
        result1.output_path = self.temp_dir / "imprint1.json"
        batch_result.add_result(result1)
        
        row2 = self.create_test_imprint_row(2, "Imprint 2")
        result2 = ImprintResult(row=row2, success=False, error=ValueError("Test error"))
        batch_result.add_result(result2)
        
        batch_result.finalize()
        
        # Create index file
        index_path = self.output_manager.create_index_file(batch_result)
        
        # Verify file was created
        assert index_path is not None
        assert index_path.exists()
        assert "batch_index_" in index_path.name
        
        # Verify content
        with open(index_path, 'r') as f:
            index_data = json.load(f)
        
        assert index_data["batch_summary"]["total_processed"] == 2
        assert index_data["batch_summary"]["successful"] == 1
        assert index_data["batch_summary"]["failed"] == 1
        assert len(index_data["results"]) == 2
    
    def test_create_index_file_disabled(self):
        """Test index file creation when disabled."""
        self.config.create_index = False
        batch_result = BatchResult(source_files=[])
        
        index_path = self.output_manager.create_index_file(batch_result)
        assert index_path is None
    
    def test_write_batch_results(self):
        """Test writing all batch results."""
        # Create batch result with mixed success/failure
        batch_result = BatchResult(source_files=[Path("test.csv")])
        
        # Successful result
        row1 = self.create_test_imprint_row(1, "Success")
        expanded1 = self.create_mock_expanded_imprint("Success")
        result1 = ImprintResult(row=row1, expanded_imprint=expanded1, success=True)
        batch_result.add_result(result1)
        
        # Failed result
        row2 = self.create_test_imprint_row(2, "Failure")
        result2 = ImprintResult(row=row2, success=False, error=ValueError("Failed"))
        batch_result.add_result(result2)
        
        batch_result.finalize()
        
        # Write all results
        written_paths = self.output_manager.write_batch_results(batch_result)
        
        # Should write successful result + index file
        assert len(written_paths) == 2
        
        # Check that successful result was written
        success_files = [p for p in written_paths if "success" in p.name.lower()]
        assert len(success_files) == 1
        
        # Check that index file was created
        index_files = [p for p in written_paths if "batch_index" in p.name]
        assert len(index_files) == 1
        
        # Verify batch result was updated with index file
        assert batch_result.index_file is not None
    
    def test_get_output_summary(self):
        """Test output summary generation."""
        # Create batch result with results
        batch_result = BatchResult(source_files=[Path("test.csv")])
        
        row = self.create_test_imprint_row()
        result = ImprintResult(row=row, success=True)
        result.output_path = self.temp_dir / "test.json"
        batch_result.add_result(result)
        
        batch_result.index_file = self.temp_dir / "index.json"
        
        # Get summary
        summary = self.output_manager.get_output_summary(batch_result)
        
        # Verify summary content
        assert summary["base_directory"] == str(self.temp_dir)
        assert summary["naming_strategy"] == "imprint_name"
        assert summary["organization_strategy"] == "flat"
        assert summary["total_results"] == 1
        assert summary["successful_outputs"] == 1
        assert len(summary["output_files"]) == 1
        assert summary["index_file"] == str(self.temp_dir / "index.json")
    
    def test_serialize_expanded_imprint(self):
        """Test expanded imprint serialization."""
        expanded = self.create_mock_expanded_imprint()
        
        serialized = self.output_manager._serialize_expanded_imprint(expanded)
        
        assert isinstance(serialized, dict)
        assert "branding" in serialized
        assert "concept" in serialized
    
    def test_serialize_expanded_imprint_error(self):
        """Test expanded imprint serialization with error."""
        # Create object without __dict__ attribute
        class ProblematicObject:
            __slots__ = ['value']
            
            def __init__(self):
                self.value = "test"
        
        problematic = ProblematicObject()
        
        # This should trigger the exception handling path
        serialized = self.output_manager._serialize_expanded_imprint(problematic)
        
        # Should handle gracefully by converting to string
        assert isinstance(serialized, str)


class TestFactoryFunction:
    """Test factory function."""
    
    def test_create_output_manager(self):
        """Test creating OutputManager with factory function."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            config = OutputConfig(base_directory=temp_dir)
            manager = create_output_manager(config)
            
            assert isinstance(manager, OutputManager)
            assert manager.config == config
        finally:
            # Cleanup
            if temp_dir.exists():
                temp_dir.rmdir()


if __name__ == "__main__":
    pytest.main([__file__])