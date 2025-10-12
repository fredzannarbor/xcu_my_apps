"""
Tests for the TemporaryFileCleaner class.

This module tests the functionality of temporary file identification,
categorization, safety validation, and cleanup operations.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.core.temporary_file_cleaner import TemporaryFileCleaner, TemporaryFileCategory
from codexes.core.file_analysis_engine import FileAnalysisEngine


class TestTemporaryFileCleaner:
    """Test cases for TemporaryFileCleaner class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.cleaner = TemporaryFileCleaner(str(self.test_dir))
        
        # Create test files
        self._create_test_files()
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def _create_test_files(self):
        """Create test files for cleanup testing."""
        # Exported config files
        (self.test_dir / "exported_config_20240101_120000.json").write_text('{"test": true}')
        (self.test_dir / "exported_config_20240102_130000.json").write_text('{"test": true}')
        
        # Python cache
        pycache_dir = self.test_dir / "__pycache__"
        pycache_dir.mkdir()
        (pycache_dir / "test.cpython-312.pyc").write_bytes(b"fake bytecode")
        
        # System files
        (self.test_dir / ".DS_Store").write_bytes(b"fake ds store")
        
        # LaTeX temp files
        (self.test_dir / "document.aux").write_text("\\relax")
        (self.test_dir / "texput.log").write_text("This is pdfTeX")
        
        # Regular files (should not be cleaned)
        (self.test_dir / "important.py").write_text("print('hello')")
        (self.test_dir / "config.json").write_text('{"important": true}')
        
        # Log files (requires confirmation)
        (self.test_dir / "application.log").write_text("INFO: Application started")
    
    def test_identify_temp_patterns(self):
        """Test identification of temporary file patterns."""
        patterns = self.cleaner.identify_temp_patterns()
        
        assert len(patterns) > 0
        assert any("exported_config_" in pattern for pattern in patterns)
        assert any("__pycache__" in pattern for pattern in patterns)
        assert any("DS_Store" in pattern for pattern in patterns)
    
    def test_categorize_temp_files(self):
        """Test categorization of temporary files."""
        categorized = self.cleaner.categorize_temp_files()
        
        # Check that exported configs are found
        assert "exported_configs" in categorized
        assert len(categorized["exported_configs"]) == 2
        assert any("exported_config_20240101_120000.json" in f for f in categorized["exported_configs"])
        
        # Check that python cache is found
        assert "python_cache" in categorized
        assert any("__pycache__" in f for f in categorized["python_cache"])
        
        # Check that system files are found
        assert "system_files" in categorized
        assert any(".DS_Store" in f for f in categorized["system_files"])
        
        # Check that LaTeX temp files are found
        assert "latex_temp" in categorized
        assert any("document.aux" in f for f in categorized["latex_temp"])
        assert any("texput.log" in f for f in categorized["latex_temp"])
    
    def test_validate_removal_safety(self):
        """Test safety validation for file removal."""
        # Create list of files to test
        test_files = [
            "exported_config_20240101_120000.json",
            "important.py",  # Should be marked as unsafe
            ".DS_Store",
            "__pycache__"
        ]
        
        # Mock the additional safety checks to bypass the recent file check
        with patch.object(self.cleaner, '_additional_temp_file_safety_checks', return_value=True):
            safety_results = self.cleaner.validate_removal_safety(test_files)
            
            # Exported config should be safe (when bypassing recent file check)
            assert safety_results.get("exported_config_20240101_120000.json", False)
            
            # .DS_Store should be safe (when bypassing recent file check)
            assert safety_results.get(".DS_Store", False)
            
            # __pycache__ should be safe (when bypassing recent file check)
            assert safety_results.get("__pycache__", False)
    
    def test_clean_temporary_files_dry_run(self):
        """Test dry run cleanup operation."""
        files_to_clean = [
            "exported_config_20240101_120000.json",
            ".DS_Store"
        ]
        
        results = self.cleaner.clean_temporary_files(files_to_clean, dry_run=True)
        
        # Check that files still exist (dry run)
        assert (self.test_dir / "exported_config_20240101_120000.json").exists()
        assert (self.test_dir / ".DS_Store").exists()
        
        # Check results indicate dry run
        for file_path, result in results.items():
            if not result.startswith("SKIPPED"):
                assert "DRY RUN" in result
    
    def test_clean_temporary_files_execute(self):
        """Test actual cleanup operation."""
        files_to_clean = [
            "exported_config_20240101_120000.json",
            ".DS_Store"
        ]
        
        # Verify files exist before cleanup
        assert (self.test_dir / "exported_config_20240101_120000.json").exists()
        assert (self.test_dir / ".DS_Store").exists()
        
        # Mock the additional safety checks to bypass the recent file check
        with patch.object(self.cleaner, '_additional_temp_file_safety_checks', return_value=True):
            results = self.cleaner.clean_temporary_files(files_to_clean, dry_run=False)
            
            # Check that files are removed
            assert not (self.test_dir / "exported_config_20240101_120000.json").exists()
            assert not (self.test_dir / ".DS_Store").exists()
            
            # Check results indicate removal
            for file_path, result in results.items():
                if not result.startswith("SKIPPED"):
                    assert "REMOVED" in result
    
    def test_update_gitignore(self):
        """Test gitignore update functionality."""
        gitignore_path = self.test_dir / ".gitignore"
        
        # Create initial .gitignore
        gitignore_path.write_text("# Initial content\n*.tmp\n")
        
        # Update with new patterns
        patterns = [
            r"exported_config_\d{8}_\d{6}\.json$",
            r"\.DS_Store$",
            r"__pycache__"
        ]
        
        self.cleaner.update_gitignore(patterns)
        
        # Check that .gitignore was updated
        gitignore_content = gitignore_path.read_text()
        assert "exported_config_*.json" in gitignore_content
        assert ".DS_Store" in gitignore_content
        assert "__pycache__/" in gitignore_content
        
        # Original content should still be there
        assert "*.tmp" in gitignore_content
    
    def test_temp_categories_initialization(self):
        """Test that temporary file categories are properly initialized."""
        categories = self.cleaner.temp_categories
        
        # Check that all expected categories exist
        expected_categories = [
            "exported_configs", "python_cache", "system_files",
            "latex_temp", "log_files", "build_artifacts"
        ]
        
        for category in expected_categories:
            assert category in categories
            assert isinstance(categories[category], TemporaryFileCategory)
            assert categories[category].name == category
            assert len(categories[category].patterns) > 0
    
    def test_safety_checks_for_recent_files(self):
        """Test that very recent files are not removed for safety."""
        # Create a very recent file
        recent_file = self.test_dir / "recent_export.json"
        recent_file.write_text('{"recent": true}')
        
        # Mock the file to appear very recent (less than 1 hour old)
        with patch('os.path.getmtime') as mock_getmtime:
            import time
            mock_getmtime.return_value = time.time() - 1800  # 30 minutes ago
            
            safety_result = self.cleaner._additional_temp_file_safety_checks("recent_export.json")
            assert not safety_result  # Should be marked as unsafe due to recent timestamp
    
    def test_backup_creation(self):
        """Test that backups are created before cleanup."""
        files_to_backup = [
            "exported_config_20240101_120000.json",
            ".DS_Store"
        ]
        
        backup_path = self.cleaner._create_cleanup_backup(files_to_backup)
        
        assert backup_path is not None
        backup_dir = Path(backup_path)
        assert backup_dir.exists()
        assert (backup_dir / "exported_config_20240101_120000.json").exists()
        assert (backup_dir / ".DS_Store").exists()
    
    def test_regex_to_gitignore_conversion(self):
        """Test conversion of regex patterns to gitignore patterns."""
        test_cases = [
            (r"exported_config_\d{8}_\d{6}\.json$", "exported_config_*.json"),
            (r"__pycache__", "__pycache__/"),
            (r"\.DS_Store$", ".DS_Store"),
            (r"\.pyc$", "*.pyc"),
        ]
        
        for regex_pattern, expected_gitignore in test_cases:
            result = self.cleaner._regex_to_gitignore_pattern(regex_pattern)
            assert result == expected_gitignore


if __name__ == "__main__":
    pytest.main([__file__])