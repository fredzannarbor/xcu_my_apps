"""Tests for Configuration Reference Updater

Tests the system that updates configuration file references in the codebase
after configuration directory unification.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.codexes.core.configuration_reference_updater import (
    ConfigurationReferenceUpdater, ReferenceUpdate, FileAnalysis
)


class TestConfigurationReferenceUpdater:
    """Test suite for ConfigurationReferenceUpdater class."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace with test files containing config references."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create test Python files with various config references
        test_files = {
            "test_script.py": '''
import json
from pathlib import Path

# Various config references to test
config_path = "configs/default_lsi_config.json"
monitoring_config = Path("configs/llm_monitoring_config.json")

def load_config():
    with open("configs/publishers/test_publisher.json", 'r') as f:
        return json.load(f)

# String formatting
config_dir = f"configs/{publisher_name}.json"
''',
            "another_script.py": '''
import os

# Path joining examples
config_file = os.path.join("configs", "imprints", "test.json")
full_path = os.path.join(base_dir, "configs/tranches/sample.json")

# Import statement (hypothetical)
# from configs.utils import load_config
''',
            "documentation.md": '''
# Configuration Guide

The configuration files are located in the `configs/` directory:

- `configs/default_lsi_config.json` - Default settings
- `configs/publishers/` - Publisher-specific configs
- `configs/imprints/` - Imprint configurations

To load a config file:
```python
config_path = "configs/llm_monitoring_config.json"
```
''',
            "shell_script.sh": '''#!/bin/bash
# Shell script with config references
CONFIG_FILE="configs/logging_config.json"
cp "$CONFIG_FILE" backup/
'''
        }
        
        for filename, content in test_files.items():
            file_path = temp_dir / filename
            with open(file_path, 'w') as f:
                f.write(content)
        
        # Create subdirectory with more files
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        
        with open(subdir / "nested_script.py", 'w') as f:
            f.write('''
# Nested file with config reference
CONFIG_PATH = "configs/isbn_schedule.json"
''')
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_initialization(self, temp_workspace):
        """Test ConfigurationReferenceUpdater initialization."""
        updater = ConfigurationReferenceUpdater(str(temp_workspace))
        
        assert updater.root_dir == temp_workspace
        assert updater.backup_dir.exists()
        assert len(updater.path_mappings) > 0
        assert len(updater.reference_patterns) > 0
    
    def test_search_and_replace_config_paths(self, temp_workspace):
        """Test searching for configuration references."""
        updater = ConfigurationReferenceUpdater(str(temp_workspace))
        results = updater.search_and_replace_config_paths()
        
        # Check results structure
        assert "files_scanned" in results
        assert "files_updated" in results
        assert "references_found" in results
        assert "references_updated" in results
        assert "errors" in results
        
        # Should have scanned multiple files
        assert len(results["files_scanned"]) >= 4
        
        # Should have found references
        assert len(results["references_found"]) > 0
        
        # Check that references were found in expected files
        scanned_files = [Path(f).name for f in results["files_scanned"]]
        assert "test_script.py" in scanned_files
        assert "another_script.py" in scanned_files
        assert "documentation.md" in scanned_files
    
    def test_reference_detection_patterns(self, temp_workspace):
        """Test that different reference patterns are detected correctly."""
        updater = ConfigurationReferenceUpdater(str(temp_workspace))
        updater.search_and_replace_config_paths()
        
        # Check that various types of references were found
        reference_types = set(update.reference_type for update in updater.all_updates)
        
        # Should detect at least configs_path references
        assert "configs_path" in reference_types
        
        # Check specific references
        old_references = [update.old_reference for update in updater.all_updates]
        
        # Should find these specific references
        expected_refs = [
            "configs/default_lsi_config.json",
            "configs/llm_monitoring_config.json",
            "configs/publishers/test_publisher.json"
        ]
        
        for expected_ref in expected_refs:
            assert any(expected_ref in ref for ref in old_references)
    
    def test_new_reference_generation(self, temp_workspace):
        """Test that new references are generated correctly."""
        updater = ConfigurationReferenceUpdater(str(temp_workspace))
        updater.search_and_replace_config_paths()
        
        # Check that new references are properly generated
        for update in updater.all_updates:
            assert update.new_reference is not None
            assert update.new_reference != update.old_reference
            
            # Should replace configs/ with config/
            if "configs/" in update.old_reference:
                assert "config/" in update.new_reference
                assert "configs/" not in update.new_reference
    
    def test_file_type_detection(self, temp_workspace):
        """Test file type detection."""
        updater = ConfigurationReferenceUpdater(str(temp_workspace))
        
        # Test different file types
        test_cases = [
            ("test.py", "python"),
            ("config.json", "json"),
            ("readme.md", "markdown"),
            ("script.sh", "shell"),
            ("data.txt", "text"),
            ("unknown.xyz", "other")
        ]
        
        for filename, expected_type in test_cases:
            file_path = Path(filename)
            detected_type = updater._determine_file_type(file_path)
            assert detected_type == expected_type
    
    def test_should_skip_file(self, temp_workspace):
        """Test file skipping logic."""
        updater = ConfigurationReferenceUpdater(str(temp_workspace))
        
        # Files that should be skipped
        skip_files = [
            Path(".git/config"),
            Path("__pycache__/module.pyc"),
            Path(".venv/lib/python3.12/site-packages/module.py"),
            Path("logs/application.log"),
            Path(".DS_Store")
        ]
        
        for file_path in skip_files:
            assert updater._should_skip_file(file_path) is True
        
        # Files that should not be skipped
        keep_files = [
            Path("src/main.py"),
            Path("config/settings.json"),
            Path("docs/readme.md")
        ]
        
        for file_path in keep_files:
            assert updater._should_skip_file(file_path) is False
    
    def test_execute_updates_dry_run(self, temp_workspace):
        """Test executing updates in dry run mode."""
        updater = ConfigurationReferenceUpdater(str(temp_workspace))
        updater.search_and_replace_config_paths()
        
        # Execute in dry run mode
        results = updater.execute_updates(dry_run=True)
        
        # Check results structure
        assert "success" in results
        assert "files_updated" in results
        assert "references_updated" in results
        assert "errors" in results
        assert "dry_run" in results
        assert results["dry_run"] is True
        
        # In dry run, backup location should be None
        assert results["backup_location"] is None
        
        # Files should not actually be modified
        test_file = temp_workspace / "test_script.py"
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Should still contain original configs/ references
        assert "configs/default_lsi_config.json" in content
    
    def test_execute_updates_real(self, temp_workspace):
        """Test actual execution of updates."""
        updater = ConfigurationReferenceUpdater(str(temp_workspace))
        updater.search_and_replace_config_paths()
        
        # Get original content
        test_file = temp_workspace / "test_script.py"
        with open(test_file, 'r') as f:
            original_content = f.read()
        
        # Execute real updates
        results = updater.execute_updates(dry_run=False)
        
        # Check that backup was created
        assert results["backup_location"] is not None
        assert Path(results["backup_location"]).exists()
        
        # Check that files were actually updated
        if results["success"]:
            with open(test_file, 'r') as f:
                updated_content = f.read()
            
            # Should have replaced configs/ with config/
            assert "config/default_lsi_config.json" in updated_content
            assert "configs/default_lsi_config.json" not in updated_content
    
    def test_validate_configuration_loading(self, temp_workspace):
        """Test configuration loading validation."""
        # Create actual config files for validation
        config_dir = temp_workspace / "config"
        config_dir.mkdir()
        
        # Create valid config files
        config_files = {
            "default_lsi_config.json": {"test": "value"},
            "llm_monitoring_config.json": {"monitoring": True},
            "logging_config.json": {"level": "INFO"}
        }
        
        for filename, content in config_files.items():
            with open(config_dir / filename, 'w') as f:
                import json
                json.dump(content, f)
        
        updater = ConfigurationReferenceUpdater(str(temp_workspace))
        validation = updater.validate_configuration_loading()
        
        # Check validation structure
        assert "syntax_valid" in validation
        assert "imports_valid" in validation
        assert "paths_exist" in validation
        assert "config_loadable" in validation
        assert "all_valid" in validation
        assert "errors" in validation
        assert "warnings" in validation
    
    def test_backup_creation(self, temp_workspace):
        """Test backup creation functionality."""
        updater = ConfigurationReferenceUpdater(str(temp_workspace))
        updater.search_and_replace_config_paths()
        
        # Create backups
        backup_success = updater._create_backups()
        assert backup_success is True
        
        # Check that backup files were created
        backup_files = list(updater.backup_dir.glob("*.backup"))
        assert len(backup_files) > 0
    
    def test_find_remaining_configs_references(self, temp_workspace):
        """Test finding remaining configs/ references after updates."""
        updater = ConfigurationReferenceUpdater(str(temp_workspace))
        
        # Before updates, should find configs/ references
        remaining_before = updater._find_remaining_configs_references()
        assert len(remaining_before) > 0
        
        # After updates (simulate by manually updating a file)
        test_file = temp_workspace / "test_script.py"
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Replace configs/ with config/ manually
        updated_content = content.replace("configs/", "config/")
        with open(test_file, 'w') as f:
            f.write(updated_content)
        
        # Should find fewer remaining references
        remaining_after = updater._find_remaining_configs_references()
        assert len(remaining_after) < len(remaining_before)
    
    def test_line_reference_detection(self, temp_workspace):
        """Test reference detection in individual lines."""
        updater = ConfigurationReferenceUpdater(str(temp_workspace))
        
        test_lines = [
            ('config_path = "configs/test.json"', 1),
            ('Path("configs/publishers/test.json")', 1),
            ('os.path.join("configs", "file.json")', 1),
            ('# No config reference here', 0),
            ('from configs.utils import load', 1)
        ]
        
        for line, expected_count in test_lines:
            references = updater._find_references_in_line(
                line, 1, Path("test.py")
            )
            assert len(references) == expected_count


class TestReferenceUpdate:
    """Test suite for ReferenceUpdate dataclass."""
    
    def test_reference_update_creation(self):
        """Test ReferenceUpdate creation."""
        update = ReferenceUpdate(
            file_path=Path("test.py"),
            line_number=10,
            old_reference="configs/test.json",
            new_reference="config/test.json",
            reference_type="file_path",
            context='config_path = "configs/test.json"'
        )
        
        assert update.file_path == Path("test.py")
        assert update.line_number == 10
        assert update.old_reference == "configs/test.json"
        assert update.new_reference == "config/test.json"
        assert update.reference_type == "file_path"
        assert update.updated is False
        assert update.error is None


class TestFileAnalysis:
    """Test suite for FileAnalysis dataclass."""
    
    def test_file_analysis_creation(self):
        """Test FileAnalysis creation."""
        references = [
            ReferenceUpdate(
                file_path=Path("test.py"),
                line_number=1,
                old_reference="configs/test.json",
                new_reference="config/test.json",
                reference_type="file_path",
                context="test"
            )
        ]
        
        analysis = FileAnalysis(
            file_path=Path("test.py"),
            references_found=references,
            syntax_valid=True,
            file_type="python"
        )
        
        assert analysis.file_path == Path("test.py")
        assert len(analysis.references_found) == 1
        assert analysis.syntax_valid is True
        assert analysis.file_type == "python"
        assert analysis.encoding == "utf-8"


if __name__ == "__main__":
    pytest.main([__file__])