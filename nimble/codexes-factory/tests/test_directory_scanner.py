"""
Unit tests for DirectoryScanner component.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.imprint_builder.directory_scanner import DirectoryScanner, ScanResult, create_directory_scanner
from codexes.modules.imprint_builder.batch_models import ProcessingPlan


class TestDirectoryScanner:
    """Test DirectoryScanner functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scanner = DirectoryScanner()
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test directory structure
        self.create_test_structure()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temp files and directories
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
    
    def create_test_structure(self):
        """Create test directory structure with various file types."""
        # Create CSV files
        (self.temp_dir / "test1.csv").write_text("header1,header2\nvalue1,value2\n")
        (self.temp_dir / "test2.CSV").write_text("col1,col2\ndata1,data2\n")
        (self.temp_dir / "empty.csv").write_text("")
        
        # Create non-CSV files
        (self.temp_dir / "readme.txt").write_text("This is a readme file")
        (self.temp_dir / "data.json").write_text('{"key": "value"}')
        
        # Create files to ignore
        (self.temp_dir / ".hidden.csv").write_text("hidden,file\n")
        (self.temp_dir / "temp.tmp").write_text("temporary file")
        (self.temp_dir / "backup.csv.bak").write_text("backup file")
        
        # Create subdirectory with more files
        subdir = self.temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.csv").write_text("nested,data\ntest,value\n")
        (subdir / "another.txt").write_text("another file")
    
    def test_initialization_default(self):
        """Test DirectoryScanner initialization with defaults."""
        scanner = DirectoryScanner()
        assert scanner.recursive is True
        assert scanner.follow_symlinks is False
    
    def test_initialization_custom(self):
        """Test DirectoryScanner initialization with custom settings."""
        scanner = DirectoryScanner(recursive=False, follow_symlinks=True)
        assert scanner.recursive is False
        assert scanner.follow_symlinks is True
    
    def test_scan_directory_recursive(self):
        """Test recursive directory scanning."""
        files = self.scanner.scan_directory(self.temp_dir)
        
        # Should find all files including in subdirectories
        assert len(files) > 5
        
        # Check that subdirectory files are included
        nested_files = [f for f in files if "nested" in f.name]
        assert len(nested_files) == 1
    
    def test_scan_directory_non_recursive(self):
        """Test non-recursive directory scanning."""
        scanner = DirectoryScanner(recursive=False)
        files = scanner.scan_directory(self.temp_dir)
        
        # Should not include subdirectory files
        nested_files = [f for f in files if "nested" in f.name]
        assert len(nested_files) == 0
        
        # Should still find files in root directory
        csv_files = [f for f in files if f.suffix.lower() == '.csv']
        assert len(csv_files) >= 2
    
    def test_scan_directory_not_found(self):
        """Test scanning non-existent directory."""
        non_existent = self.temp_dir / "does_not_exist"
        
        with pytest.raises(FileNotFoundError):
            self.scanner.scan_directory(non_existent)
    
    def test_scan_directory_not_directory(self):
        """Test scanning a file instead of directory."""
        file_path = self.temp_dir / "test1.csv"
        
        with pytest.raises(ValueError, match="not a directory"):
            self.scanner.scan_directory(file_path)
    
    def test_filter_csv_files(self):
        """Test filtering CSV files from file list."""
        all_files = list(self.temp_dir.rglob('*'))
        all_files = [f for f in all_files if f.is_file()]
        
        csv_files = self.scanner.filter_csv_files(all_files)
        
        # Should include .csv and .CSV files
        assert len(csv_files) >= 2
        
        # Should not include ignored files
        hidden_files = [f for f in csv_files if f.name.startswith('.')]
        assert len(hidden_files) == 0
        
        backup_files = [f for f in csv_files if f.name.endswith('.bak')]
        assert len(backup_files) == 0
    
    def test_should_ignore_file(self):
        """Test file ignore patterns."""
        # Hidden files
        assert self.scanner._should_ignore_file(Path(".hidden.csv"))
        
        # Temporary files
        assert self.scanner._should_ignore_file(Path("temp.tmp"))
        assert self.scanner._should_ignore_file(Path("file.temp"))
        
        # Backup files
        assert self.scanner._should_ignore_file(Path("backup.bak"))
        
        # System files
        assert self.scanner._should_ignore_file(Path("Thumbs.db"))
        assert self.scanner._should_ignore_file(Path(".DS_Store"))
        
        # Normal files should not be ignored
        assert not self.scanner._should_ignore_file(Path("normal.csv"))
        assert not self.scanner._should_ignore_file(Path("data.txt"))
    
    def test_create_processing_plan(self):
        """Test creating processing plan."""
        csv_files = [
            self.temp_dir / "test2.CSV",
            self.temp_dir / "test1.csv",
            self.temp_dir / "subdir" / "nested.csv"
        ]
        
        plan = self.scanner.create_processing_plan(csv_files)
        
        assert isinstance(plan, ProcessingPlan)
        assert len(plan.csv_files) == 3
        assert plan.total_files == 3
        
        # Files should be sorted
        assert plan.processing_order[0].name == "nested.csv"
        assert plan.processing_order[1].name == "test1.csv"
        assert plan.processing_order[2].name == "test2.CSV"
    
    def test_create_processing_plan_empty(self):
        """Test creating processing plan with no files."""
        plan = self.scanner.create_processing_plan([])
        
        assert isinstance(plan, ProcessingPlan)
        assert len(plan.csv_files) == 0
        assert plan.total_files == 0
        assert plan.estimated_rows == 0
    
    def test_estimate_total_rows(self):
        """Test row estimation."""
        csv_files = [
            self.temp_dir / "test1.csv",  # Has 1 data row
            self.temp_dir / "test2.CSV"   # Has 1 data row
        ]
        
        estimated = self.scanner._estimate_total_rows(csv_files)
        
        # Should estimate 2 rows total (1 from each file)
        assert estimated == 2
    
    def test_estimate_total_rows_with_error(self):
        """Test row estimation with unreadable file."""
        csv_files = [
            self.temp_dir / "nonexistent.csv",
            self.temp_dir / "test1.csv"
        ]
        
        estimated = self.scanner._estimate_total_rows(csv_files)
        
        # Should use default estimation for unreadable file + actual count for readable
        assert estimated == 11  # 10 (default) + 1 (actual)
    
    def test_validate_csv_file(self):
        """Test CSV file validation."""
        # Valid CSV
        assert self.scanner._validate_csv_file(self.temp_dir / "test1.csv")
        
        # Empty CSV
        assert not self.scanner._validate_csv_file(self.temp_dir / "empty.csv")
        
        # Non-CSV file
        assert not self.scanner._validate_csv_file(self.temp_dir / "readme.txt")
        
        # Non-existent file
        assert not self.scanner._validate_csv_file(self.temp_dir / "missing.csv")


class TestScanForCSVFiles:
    """Test comprehensive CSV file scanning."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scanner = DirectoryScanner()
        self.temp_dir = Path(tempfile.mkdtemp())
    
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
    
    def test_scan_for_csv_files_success(self):
        """Test successful CSV file scanning."""
        # Create test files
        (self.temp_dir / "valid.csv").write_text("col1,col2\ndata1,data2\n")
        (self.temp_dir / "another.csv").write_text("header\nvalue\n")
        (self.temp_dir / "readme.txt").write_text("Not a CSV")
        
        result = self.scanner.scan_for_csv_files(self.temp_dir)
        
        assert isinstance(result, ScanResult)
        assert result.directory == self.temp_dir
        assert len(result.csv_files) == 2
        assert len(result.errors) == 0
        assert result.total_files == 3
    
    def test_scan_for_csv_files_with_ignored(self):
        """Test scanning with ignored files."""
        # Create test files including ignored ones
        (self.temp_dir / "valid.csv").write_text("col1,col2\ndata1,data2\n")
        (self.temp_dir / ".hidden.csv").write_text("hidden,data\n")
        (self.temp_dir / "backup.csv.bak").write_text("backup,data\n")
        
        result = self.scanner.scan_for_csv_files(self.temp_dir)
        
        assert len(result.csv_files) == 1  # Only valid.csv
        assert len(result.ignored_files) == 2  # .hidden.csv and backup.csv.bak
        assert len(result.warnings) >= 1  # Warning about ignored CSV
    
    def test_scan_for_csv_files_directory_not_found(self):
        """Test scanning non-existent directory."""
        non_existent = self.temp_dir / "missing"
        
        result = self.scanner.scan_for_csv_files(non_existent)
        
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].lower()
        assert len(result.csv_files) == 0
    
    def test_scan_for_csv_files_permission_error(self):
        """Test scanning directory with permission issues."""
        # Create directory and remove read permissions
        restricted_dir = self.temp_dir / "restricted"
        restricted_dir.mkdir()
        
        # Mock permission error
        with patch.object(self.scanner, 'scan_directory', side_effect=PermissionError("Access denied")):
            result = self.scanner.scan_for_csv_files(restricted_dir)
            
            assert len(result.errors) > 0
            assert "permission denied" in result.errors[0].lower()


class TestDirectoryInfo:
    """Test directory information functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scanner = DirectoryScanner()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            for item in self.temp_dir.iterdir():
                if item.is_file():
                    item.unlink()
            self.temp_dir.rmdir()
    
    def test_get_directory_info_valid(self):
        """Test getting info for valid directory."""
        # Create test files
        (self.temp_dir / "test.csv").write_text("data")
        (self.temp_dir / "readme.txt").write_text("text")
        
        info = self.scanner.get_directory_info(self.temp_dir)
        
        assert info["exists"] is True
        assert info["is_directory"] is True
        assert info["total_files"] == 2
        assert info["csv_files"] == 1
        assert info["readable"] is True
    
    def test_get_directory_info_not_found(self):
        """Test getting info for non-existent directory."""
        non_existent = self.temp_dir / "missing"
        
        info = self.scanner.get_directory_info(non_existent)
        
        assert info["exists"] is False
        assert "error" in info
    
    def test_get_directory_info_not_directory(self):
        """Test getting info for file instead of directory."""
        file_path = self.temp_dir / "test.txt"
        file_path.write_text("content")
        
        info = self.scanner.get_directory_info(file_path)
        
        assert info["exists"] is True
        assert info["is_directory"] is False
        assert "error" in info


class TestFactoryFunction:
    """Test factory function."""
    
    def test_create_directory_scanner_default(self):
        """Test creating DirectoryScanner with defaults."""
        scanner = create_directory_scanner()
        
        assert isinstance(scanner, DirectoryScanner)
        assert scanner.recursive is True
        assert scanner.follow_symlinks is False
    
    def test_create_directory_scanner_custom(self):
        """Test creating DirectoryScanner with custom settings."""
        scanner = create_directory_scanner(recursive=False, follow_symlinks=True)
        
        assert isinstance(scanner, DirectoryScanner)
        assert scanner.recursive is False
        assert scanner.follow_symlinks is True


class TestScanResult:
    """Test ScanResult dataclass."""
    
    def test_scan_result_path_conversion(self):
        """Test that string paths are converted to Path objects."""
        result = ScanResult(
            directory="test/path",
            total_files=1,
            csv_files=[],
            ignored_files=[],
            errors=[],
            warnings=[]
        )
        
        assert isinstance(result.directory, Path)
        assert str(result.directory) == "test/path"


if __name__ == "__main__":
    pytest.main([__file__])