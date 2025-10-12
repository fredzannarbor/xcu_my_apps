"""
Unit tests for CLI utility functions.
"""

import pytest
import json
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from src.arxiv_writer.utils.cli_utils import (
    load_json_file,
    save_json_file,
    load_yaml_file,
    save_yaml_file,
    validate_file_format,
    create_backup_file,
    format_file_size,
    get_file_info,
    find_files_by_pattern,
    create_directory_structure,
    validate_directory_structure,
    generate_cli_report,
    format_cli_output,
    parse_key_value_pairs,
    truncate_text
)
from src.arxiv_writer.core.exceptions import ArxivWriterError, ValidationError


class TestFileOperations:
    """Test file operation utilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def test_load_json_file_success(self):
        """Test successful JSON file loading."""
        test_data = {"key": "value", "number": 42}
        json_file = self.temp_path / "test.json"
        
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_json_file(json_file)
        assert result == test_data
    
    def test_load_json_file_not_found(self):
        """Test JSON file loading with non-existent file."""
        with pytest.raises(ArxivWriterError, match="File not found"):
            load_json_file("nonexistent.json")
    
    def test_load_json_file_invalid_json(self):
        """Test JSON file loading with invalid JSON."""
        json_file = self.temp_path / "invalid.json"
        
        with open(json_file, 'w') as f:
            f.write("invalid json content")
        
        with pytest.raises(ArxivWriterError, match="Invalid JSON"):
            load_json_file(json_file)
    
    def test_save_json_file_success(self):
        """Test successful JSON file saving."""
        test_data = {"key": "value", "number": 42}
        json_file = self.temp_path / "output.json"
        
        save_json_file(test_data, json_file)
        
        assert json_file.exists()
        with open(json_file, 'r') as f:
            result = json.load(f)
        assert result == test_data
    
    def test_save_json_file_creates_directories(self):
        """Test JSON file saving creates parent directories."""
        test_data = {"key": "value"}
        json_file = self.temp_path / "subdir" / "output.json"
        
        save_json_file(test_data, json_file)
        
        assert json_file.exists()
        assert json_file.parent.exists()
    
    def test_load_yaml_file_success(self):
        """Test successful YAML file loading."""
        test_data = {"key": "value", "list": [1, 2, 3]}
        yaml_file = self.temp_path / "test.yaml"
        
        with open(yaml_file, 'w') as f:
            yaml.dump(test_data, f)
        
        result = load_yaml_file(yaml_file)
        assert result == test_data
    
    def test_load_yaml_file_not_found(self):
        """Test YAML file loading with non-existent file."""
        with pytest.raises(ArxivWriterError, match="File not found"):
            load_yaml_file("nonexistent.yaml")
    
    def test_save_yaml_file_success(self):
        """Test successful YAML file saving."""
        test_data = {"key": "value", "list": [1, 2, 3]}
        yaml_file = self.temp_path / "output.yaml"
        
        save_yaml_file(test_data, yaml_file)
        
        assert yaml_file.exists()
        with open(yaml_file, 'r') as f:
            result = yaml.safe_load(f)
        assert result == test_data


class TestFileValidation:
    """Test file validation utilities."""
    
    def test_validate_file_format_valid(self):
        """Test file format validation with valid format."""
        result = validate_file_format("test.json", ["json", "yaml"])
        assert result == "json"
    
    def test_validate_file_format_invalid(self):
        """Test file format validation with invalid format."""
        with pytest.raises(ValidationError, match="Unsupported file format"):
            validate_file_format("test.txt", ["json", "yaml"])
    
    def test_validate_file_format_case_insensitive(self):
        """Test file format validation is case insensitive."""
        result = validate_file_format("test.JSON", ["json", "yaml"])
        assert result == "json"
    
    def test_create_backup_file_success(self):
        """Test successful backup file creation."""
        original_file = Path(tempfile.mktemp())
        original_file.write_text("test content")
        
        backup_path = create_backup_file(original_file)
        
        assert backup_path.exists()
        assert backup_path.read_text() == "test content"
        assert ".backup" in backup_path.name
        
        # Clean up
        original_file.unlink()
        backup_path.unlink()
    
    def test_create_backup_file_not_found(self):
        """Test backup file creation with non-existent file."""
        with pytest.raises(ArxivWriterError, match="Cannot backup non-existent file"):
            create_backup_file("nonexistent.txt")


class TestFileInfo:
    """Test file information utilities."""
    
    def test_format_file_size(self):
        """Test file size formatting."""
        assert format_file_size(0) == "0 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1536) == "1.5 KB"
    
    def test_get_file_info_existing_file(self):
        """Test file info for existing file."""
        test_file = Path(tempfile.mktemp())
        test_file.write_text("test content")
        
        info = get_file_info(test_file)
        
        assert info["exists"] is True
        assert info["name"] == test_file.name
        assert info["is_file"] is True
        assert info["is_dir"] is False
        assert "size_bytes" in info
        assert "created" in info
        assert "modified" in info
        
        # Clean up
        test_file.unlink()
    
    def test_get_file_info_nonexistent_file(self):
        """Test file info for non-existent file."""
        info = get_file_info("nonexistent.txt")
        
        assert info["exists"] is False
        assert "nonexistent.txt" in info["path"]
    
    def test_find_files_by_pattern(self):
        """Test finding files by pattern."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create test files
        (temp_dir / "test1.py").touch()
        (temp_dir / "test2.py").touch()
        (temp_dir / "test.txt").touch()
        (temp_dir / "subdir").mkdir()
        (temp_dir / "subdir" / "test3.py").touch()
        
        # Test pattern matching
        py_files = find_files_by_pattern(temp_dir, ["*.py"])
        assert len(py_files) == 3
        
        # Test non-recursive
        py_files_non_recursive = find_files_by_pattern(temp_dir, ["*.py"], recursive=False)
        assert len(py_files_non_recursive) == 2
        
        # Test exclusion
        py_files_excluded = find_files_by_pattern(temp_dir, ["*.py"], exclude_patterns=["*1*"])
        assert len(py_files_excluded) == 2
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)


class TestDirectoryOperations:
    """Test directory operation utilities."""
    
    def test_create_directory_structure(self):
        """Test directory structure creation."""
        temp_dir = Path(tempfile.mkdtemp())
        
        structure = {
            "dir1": {
                "subdir1": {
                    "file1.txt": "content1"
                },
                "file2.txt": "content2"
            },
            "dir2": {},
            "file3.txt": "content3"
        }
        
        create_directory_structure(temp_dir, structure)
        
        assert (temp_dir / "dir1").is_dir()
        assert (temp_dir / "dir1" / "subdir1").is_dir()
        assert (temp_dir / "dir1" / "subdir1" / "file1.txt").read_text() == "content1"
        assert (temp_dir / "dir1" / "file2.txt").read_text() == "content2"
        assert (temp_dir / "dir2").is_dir()
        assert (temp_dir / "file3.txt").read_text() == "content3"
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_validate_directory_structure_valid(self):
        """Test directory structure validation with valid structure."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create structure
        structure = {
            "dir1": {
                "file1.txt": "content"
            },
            "file2.txt": "content"
        }
        create_directory_structure(temp_dir, structure)
        
        # Validate structure
        result = validate_directory_structure(temp_dir, structure)
        
        assert result["valid"] is True
        assert len(result["missing_directories"]) == 0
        assert len(result["missing_files"]) == 0
        assert len(result["errors"]) == 0
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_validate_directory_structure_missing_items(self):
        """Test directory structure validation with missing items."""
        temp_dir = Path(tempfile.mkdtemp())
        
        required_structure = {
            "dir1": {
                "file1.txt": "content"
            },
            "file2.txt": "content"
        }
        
        # Only create partial structure
        (temp_dir / "dir1").mkdir()
        
        result = validate_directory_structure(temp_dir, required_structure)
        
        assert result["valid"] is False
        assert "dir1/file1.txt" in result["missing_files"]
        assert "file2.txt" in result["missing_files"]
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)


class TestCLIUtilities:
    """Test CLI-specific utilities."""
    
    def test_generate_cli_report(self):
        """Test CLI report generation."""
        details = {
            "items_processed": 5,
            "duration": "2.5s",
            "errors": ["Error 1"],
            "warnings": ["Warning 1"]
        }
        
        report = generate_cli_report("test_operation", True, details)
        
        assert report["operation"] == "test_operation"
        assert report["success"] is True
        assert report["details"] == details
        assert report["summary"]["status"] == "SUCCESS"
        assert report["summary"]["items_processed"] == 5
        assert "timestamp" in report
    
    def test_format_cli_output(self):
        """Test CLI output formatting."""
        # Test basic formatting
        result = format_cli_output("Test message", "info", color=False)
        assert "Test message" in result
        
        # Test with color
        result = format_cli_output("Test message", "success", color=True)
        assert "Test message" in result
        assert "✅" in result
        
        # Test with custom prefix
        result = format_cli_output("Test message", "info", prefix="[TEST]", color=False)
        assert "[TEST] Test message" == result
    
    def test_parse_key_value_pairs_valid(self):
        """Test parsing valid key=value pairs."""
        pairs = ["key1=value1", "key2=value2", "key3=value with spaces"]
        result = parse_key_value_pairs(pairs)
        
        expected = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value with spaces"
        }
        assert result == expected
    
    def test_parse_key_value_pairs_invalid(self):
        """Test parsing invalid key=value pairs."""
        with pytest.raises(ValidationError, match="Invalid key=value pair"):
            parse_key_value_pairs(["invalid_pair"])
        
        with pytest.raises(ValidationError, match="Empty key"):
            parse_key_value_pairs(["=value"])
    
    def test_truncate_text(self):
        """Test text truncation."""
        # Test no truncation needed
        result = truncate_text("short", 10)
        assert result == "short"
        
        # Test truncation
        result = truncate_text("this is a very long text", 10)
        assert len(result) == 10
        assert result.endswith("...")
        
        # Test custom suffix
        result = truncate_text("long text", 8, suffix=">>")
        assert result.endswith(">>")
        assert len(result) == 8


class TestMockOperations:
    """Test utilities with mocked operations."""
    
    @patch('builtins.input', return_value='y')
    def test_confirm_action_yes(self, mock_input):
        """Test confirmation with yes response."""
        from src.arxiv_writer.utils.cli_utils import confirm_action
        result = confirm_action("Continue?")
        assert result is True
    
    @patch('builtins.input', return_value='n')
    def test_confirm_action_no(self, mock_input):
        """Test confirmation with no response."""
        from src.arxiv_writer.utils.cli_utils import confirm_action
        result = confirm_action("Continue?")
        assert result is False
    
    @patch('builtins.input', return_value='')
    def test_confirm_action_default(self, mock_input):
        """Test confirmation with default response."""
        from src.arxiv_writer.utils.cli_utils import confirm_action
        result = confirm_action("Continue?", default=True)
        assert result is True
    
    @patch('builtins.input', side_effect=KeyboardInterrupt)
    def test_confirm_action_keyboard_interrupt(self, mock_input):
        """Test confirmation with keyboard interrupt."""
        from src.arxiv_writer.utils.cli_utils import confirm_action
        result = confirm_action("Continue?")
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__])