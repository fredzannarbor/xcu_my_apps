"""
Unit tests for CSVReader component.
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.imprint_builder.csv_reader import CSVReader, create_csv_reader
from codexes.modules.imprint_builder.batch_models import ValidationResult, ImprintRow


class TestCSVReader:
    """Test CSVReader functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.csv_reader = CSVReader()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temp files
        for file in self.temp_dir.glob("*"):
            file.unlink()
        self.temp_dir.rmdir()
    
    def create_test_csv(self, filename: str, data: dict, columns: list = None) -> Path:
        """Create a test CSV file."""
        csv_path = self.temp_dir / filename
        df = pd.DataFrame(data)
        if columns:
            df.columns = columns
        df.to_csv(csv_path, index=False)
        return csv_path
    
    def test_initialization_default(self):
        """Test CSVReader initialization with defaults."""
        reader = CSVReader()
        assert reader.column_mapping == {}
        assert "imprint_concept" in reader.effective_mapping.values()
        assert "concept" in reader.effective_mapping
    
    def test_initialization_custom_mapping(self):
        """Test CSVReader initialization with custom mapping."""
        custom_mapping = {"my_concept": "imprint_concept"}
        reader = CSVReader(column_mapping=custom_mapping)
        assert reader.column_mapping == custom_mapping
        assert "my_concept" in reader.effective_mapping
    
    def test_read_csv_valid_file(self):
        """Test reading a valid CSV file."""
        data = {
            "imprint_concept": ["Modern Literary Press", "Tech Publishing House"],
            "additional_info": ["Focus on contemporary fiction", "Technology books"]
        }
        csv_path = self.create_test_csv("valid.csv", data)
        
        rows = self.csv_reader.read_csv(csv_path)
        
        assert len(rows) == 2
        assert rows[0].imprint_concept == "Modern Literary Press"
        assert rows[1].imprint_concept == "Tech Publishing House"
        assert rows[0].row_number == 1
        assert rows[1].row_number == 2
        assert rows[0].source_file == csv_path
    
    def test_read_csv_with_column_mapping(self):
        """Test reading CSV with column mapping."""
        data = {
            "concept": ["Literary Imprint", "Science Imprint"],
            "description": ["Focus on literature", "Focus on science"]
        }
        csv_path = self.create_test_csv("mapped.csv", data)
        
        rows = self.csv_reader.read_csv(csv_path)
        
        assert len(rows) == 2
        assert rows[0].imprint_concept == "Literary Imprint"
        assert "description" in rows[0].additional_data
    
    def test_read_csv_file_not_found(self):
        """Test reading non-existent CSV file."""
        non_existent = self.temp_dir / "missing.csv"
        
        with pytest.raises(FileNotFoundError):
            self.csv_reader.read_csv(non_existent)
    
    def test_read_csv_empty_file(self):
        """Test reading empty CSV file."""
        empty_csv = self.temp_dir / "empty.csv"
        empty_csv.write_text("")
        
        with pytest.raises(ValueError, match="CSV file is empty"):
            self.csv_reader.read_csv(empty_csv)
    
    def test_read_csv_malformed(self):
        """Test reading malformed CSV file."""
        malformed_csv = self.temp_dir / "malformed.csv"
        malformed_csv.write_text("header1,header2\nvalue1,value2,extra_value\n")
        
        with pytest.raises(ValueError, match="CSV validation failed"):
            self.csv_reader.read_csv(malformed_csv)
    
    def test_read_csv_skip_empty_concepts(self):
        """Test that empty concepts are skipped."""
        data = {
            "imprint_concept": ["Valid Concept", "", None, "Another Valid"],
            "info": ["Info1", "Info2", "Info3", "Info4"]
        }
        csv_path = self.create_test_csv("with_empty.csv", data)
        
        rows = self.csv_reader.read_csv(csv_path)
        
        assert len(rows) == 2
        assert rows[0].imprint_concept == "Valid Concept"
        assert rows[1].imprint_concept == "Another Valid"


class TestColumnValidation:
    """Test column validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.csv_reader = CSVReader()
    
    def test_validate_columns_valid(self):
        """Test validation of valid columns."""
        df = pd.DataFrame({"imprint_concept": ["Test"], "other": ["Data"]})
        
        result = self.csv_reader.validate_columns(df)
        
        assert result.valid is True
        assert len(result.errors) == 0
    
    def test_validate_columns_empty_dataframe(self):
        """Test validation of empty DataFrame."""
        df = pd.DataFrame()
        
        result = self.csv_reader.validate_columns(df)
        
        assert result.valid is False
        assert any("no columns" in error.lower() for error in result.errors)
    
    def test_validate_columns_no_columns(self):
        """Test validation with no columns."""
        df = pd.DataFrame(index=[0, 1, 2])  # DataFrame with rows but no columns
        
        result = self.csv_reader.validate_columns(df)
        
        assert result.valid is False
        assert any("no columns" in error.lower() for error in result.errors)
    
    def test_validate_columns_missing_required(self):
        """Test validation with missing required columns."""
        df = pd.DataFrame({"other_column": ["data1", "data2"]})
        
        result = self.csv_reader.validate_columns(df)
        
        assert result.valid is False
        assert any("missing required columns" in error.lower() for error in result.errors)
    
    def test_validate_columns_with_candidates(self):
        """Test validation with mappable columns."""
        df = pd.DataFrame({"description": ["concept1"], "other": ["data"]})
        
        result = self.csv_reader.validate_columns(df)
        
        # Should be valid since description maps to imprint_concept
        assert result.valid is True
        
        # Test with unmappable columns
        df_unmappable = pd.DataFrame({"random_column": ["concept1"], "other": ["data"]})
        result_unmappable = self.csv_reader.validate_columns(df_unmappable)
        
        assert result_unmappable.valid is False
        assert len(result_unmappable.errors) > 0
    
    def test_validate_columns_empty_columns_warning(self):
        """Test validation warns about empty columns."""
        df = pd.DataFrame({
            "imprint_concept": ["Test"],
            "empty_col": [None],
            "another_empty": [pd.NA]
        })
        
        result = self.csv_reader.validate_columns(df)
        
        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("empty columns" in warning.lower() for warning in result.warnings)


class TestColumnMapping:
    """Test column mapping functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.csv_reader = CSVReader()
    
    def test_map_columns_basic(self):
        """Test basic column mapping."""
        df = pd.DataFrame({"concept": ["Test"], "other": ["Data"]})
        
        mapped_df = self.csv_reader.map_columns(df)
        
        assert "imprint_concept" in mapped_df.columns
        assert "other" in mapped_df.columns
        assert mapped_df["imprint_concept"].iloc[0] == "Test"
    
    def test_map_columns_case_insensitive(self):
        """Test case-insensitive column mapping."""
        df = pd.DataFrame({"CONCEPT": ["Test"], "Description": ["Data"]})
        
        mapped_df = self.csv_reader.map_columns(df)
        
        assert "imprint_concept" in mapped_df.columns
    
    def test_map_columns_no_mapping(self):
        """Test mapping when no columns match."""
        df = pd.DataFrame({"unknown_col": ["Test"], "another": ["Data"]})
        
        mapped_df = self.csv_reader.map_columns(df)
        
        # Should return original DataFrame unchanged
        assert list(mapped_df.columns) == list(df.columns)
    
    def test_map_columns_custom_mapping(self):
        """Test mapping with custom column mapping."""
        custom_reader = CSVReader(column_mapping={"my_concept": "imprint_concept"})
        df = pd.DataFrame({"my_concept": ["Test"], "other": ["Data"]})
        
        mapped_df = custom_reader.map_columns(df)
        
        assert "imprint_concept" in mapped_df.columns
        assert mapped_df["imprint_concept"].iloc[0] == "Test"


class TestExtractImprintConcepts:
    """Test imprint concept extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.csv_reader = CSVReader()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        for file in self.temp_dir.glob("*"):
            file.unlink()
        self.temp_dir.rmdir()
    
    def test_extract_basic(self):
        """Test basic concept extraction."""
        df = pd.DataFrame({
            "imprint_concept": ["Concept 1", "Concept 2"],
            "additional": ["Data 1", "Data 2"]
        })
        source_file = self.temp_dir / "test.csv"
        
        rows = self.csv_reader.extract_imprint_concepts(df, source_file)
        
        assert len(rows) == 2
        assert rows[0].imprint_concept == "Concept 1"
        assert rows[0].additional_data["additional"] == "Data 1"
        assert rows[0].source_info.total_rows == 2
    
    def test_extract_skip_empty(self):
        """Test skipping empty concepts."""
        df = pd.DataFrame({
            "imprint_concept": ["Valid", "", None, "Also Valid"],
            "data": ["D1", "D2", "D3", "D4"]
        })
        source_file = self.temp_dir / "test.csv"
        
        rows = self.csv_reader.extract_imprint_concepts(df, source_file)
        
        assert len(rows) == 2
        assert rows[0].imprint_concept == "Valid"
        assert rows[1].imprint_concept == "Also Valid"
    
    def test_extract_with_nulls(self):
        """Test extraction with null values in additional data."""
        df = pd.DataFrame({
            "imprint_concept": ["Test Concept"],
            "optional_field": [None],
            "valid_field": ["Valid Data"]
        })
        source_file = self.temp_dir / "test.csv"
        
        rows = self.csv_reader.extract_imprint_concepts(df, source_file)
        
        assert len(rows) == 1
        assert "optional_field" not in rows[0].additional_data
        assert "valid_field" in rows[0].additional_data


class TestUtilityMethods:
    """Test utility methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.csv_reader = CSVReader()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        for file in self.temp_dir.glob("*"):
            file.unlink()
        self.temp_dir.rmdir()
    
    def create_test_csv(self, filename: str, data: dict) -> Path:
        """Create a test CSV file."""
        csv_path = self.temp_dir / filename
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return csv_path
    
    def test_get_column_info(self):
        """Test getting column information."""
        data = {"concept": ["Test"], "description": ["Data"]}
        csv_path = self.create_test_csv("info_test.csv", data)
        
        info = self.csv_reader.get_column_info(csv_path)
        
        assert info["total_columns"] == 2
        assert "concept" in info["available_columns"]
        assert info["has_required_mappings"] is True
        assert len(info["mappable_columns"]) > 0
    
    def test_get_column_info_error(self):
        """Test column info with invalid file."""
        invalid_path = self.temp_dir / "nonexistent.csv"
        
        info = self.csv_reader.get_column_info(invalid_path)
        
        assert "error" in info
        assert info["total_columns"] == 0
        assert info["has_required_mappings"] is False
    
    def test_preview_csv(self):
        """Test CSV preview functionality."""
        data = {
            "concept": ["Concept 1", "Concept 2", "Concept 3"],
            "info": ["Info 1", "Info 2", "Info 3"]
        }
        csv_path = self.create_test_csv("preview_test.csv", data)
        
        preview = self.csv_reader.preview_csv(csv_path, num_rows=2)
        
        assert preview["success"] is True
        assert preview["total_columns"] == 2
        assert preview["preview_rows"] == 2
        assert len(preview["sample_data"]) == 2
        assert "column_info" in preview
    
    def test_preview_csv_error(self):
        """Test preview with invalid file."""
        invalid_path = self.temp_dir / "nonexistent.csv"
        
        preview = self.csv_reader.preview_csv(invalid_path)
        
        assert preview["success"] is False
        assert "error" in preview
        assert preview["total_columns"] == 0


class TestFactoryFunction:
    """Test factory function."""
    
    def test_create_csv_reader_default(self):
        """Test creating CSVReader with defaults."""
        reader = create_csv_reader()
        
        assert isinstance(reader, CSVReader)
        assert reader.column_mapping == {}
    
    def test_create_csv_reader_custom(self):
        """Test creating CSVReader with custom mapping."""
        mapping = {"custom": "imprint_concept"}
        reader = create_csv_reader(column_mapping=mapping)
        
        assert isinstance(reader, CSVReader)
        assert reader.column_mapping == mapping


if __name__ == "__main__":
    pytest.main([__file__])