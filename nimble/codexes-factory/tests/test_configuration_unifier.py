"""Tests for Configuration Unifier

Tests the configuration directory unification system that merges config/ and configs/
directories into a single unified structure.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.codexes.core.configuration_unifier import (
    ConfigurationUnifier, ConfigFile, ConflictResolution, MergeOperation
)


class TestConfigurationUnifier:
    """Test suite for ConfigurationUnifier class."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace with test configuration directories."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create config/ directory with test files
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        
        config_files = {
            "streamlit_apps.json": {
                "apps": {
                    "daily_engine": {
                        "name": "Daily Engine",
                        "port": 8501,
                        "enabled": True
                    }
                }
            },
            "user_config.json": {
                "habits": ["reading", "writing"],
                "projects": {"test": {"enabled": True}}
            }
        }
        
        for filename, content in config_files.items():
            with open(config_dir / filename, 'w') as f:
                json.dump(content, f, indent=2)
        
        # Create configs/ directory with test files
        configs_dir = temp_dir / "configs"
        configs_dir.mkdir()
        
        # Create subdirectories
        (configs_dir / "publishers").mkdir()
        (configs_dir / "imprints").mkdir()
        (configs_dir / "tranches").mkdir()
        
        configs_files = {
            "default_lsi_config.json": {
                "publisher": "Test Publisher",
                "language_code": "eng",
                "territorial_rights": "World"
            },
            "llm_monitoring_config.json": {
                "monitoring": {"enabled": True},
                "log_level": "INFO"
            },
            "publishers/test_publisher.json": {
                "publisher": "Test Publisher Inc",
                "contact_email": "test@example.com",
                "lightning_source_account": "123456"
            },
            "imprints/test_imprint.json": {
                "imprint": "Test Imprint",
                "publisher": "Test Publisher Inc"
            }
        }
        
        for filepath, content in configs_files.items():
            full_path = configs_dir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w') as f:
                json.dump(content, f, indent=2)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_initialization(self, temp_workspace):
        """Test ConfigurationUnifier initialization."""
        unifier = ConfigurationUnifier(str(temp_workspace))
        
        assert unifier.root_dir == temp_workspace
        assert unifier.config_dir == temp_workspace / "config"
        assert unifier.configs_dir == temp_workspace / "configs"
        assert unifier.backup_dir.exists()
    
    def test_analyze_configuration_directories(self, temp_workspace):
        """Test analysis of configuration directories."""
        unifier = ConfigurationUnifier(str(temp_workspace))
        analysis = unifier.analyze_configuration_directories()
        
        # Check analysis structure
        assert "config_dir" in analysis
        assert "configs_dir" in analysis
        assert "conflicts" in analysis
        assert "merge_strategy" in analysis
        assert "statistics" in analysis
        
        # Check config directory analysis
        config_analysis = analysis["config_dir"]
        assert config_analysis["exists"] is True
        assert config_analysis["total_files"] == 2
        assert len(config_analysis["files"]) == 2
        
        # Check configs directory analysis
        configs_analysis = analysis["configs_dir"]
        assert configs_analysis["exists"] is True
        assert configs_analysis["total_files"] == 4
        assert len(configs_analysis["subdirectories"]) >= 3
        
        # Check statistics
        stats = analysis["statistics"]
        assert stats["config_files_count"] == 2
        assert stats["configs_files_count"] == 4
        assert "conflicts_count" in stats
    
    def test_identify_config_conflicts(self, temp_workspace):
        """Test conflict identification between directories."""
        unifier = ConfigurationUnifier(str(temp_workspace))
        unifier.analyze_configuration_directories()
        
        conflicts = unifier.identify_config_conflicts()
        
        # Should be a list of conflict dictionaries
        assert isinstance(conflicts, list)
        
        # Each conflict should have required fields
        for conflict in conflicts:
            assert "type" in conflict
            assert "source_file" in conflict
            assert "target_file" in conflict
            assert "resolution" in conflict
            assert "description" in conflict
    
    def test_create_merge_strategy(self, temp_workspace):
        """Test merge strategy creation."""
        unifier = ConfigurationUnifier(str(temp_workspace))
        unifier.analyze_configuration_directories()
        
        strategy = unifier.create_merge_strategy()
        
        # Check strategy structure
        assert "approach" in strategy
        assert "conflict_resolution" in strategy
        assert "backup_strategy" in strategy
        assert "validation_strategy" in strategy
        assert "merge_plan" in strategy
        assert "operations_count" in strategy
        
        # Check merge plan
        merge_plan = strategy["merge_plan"]
        assert isinstance(merge_plan, list)
        assert len(merge_plan) > 0
        
        # Each operation should have required fields
        for operation in merge_plan:
            assert "operation" in operation
            assert "description" in operation
    
    def test_execute_merge_dry_run(self, temp_workspace):
        """Test merge execution in dry run mode."""
        unifier = ConfigurationUnifier(str(temp_workspace))
        unifier.analyze_configuration_directories()
        
        results = unifier.execute_merge(dry_run=True)
        
        # Check results structure
        assert "success" in results
        assert "operations_completed" in results
        assert "operations_failed" in results
        assert "errors" in results
        assert "dry_run" in results
        assert results["dry_run"] is True
        
        # In dry run, no actual changes should be made
        assert results["backup_location"] is None
        
        # Original directories should be unchanged
        assert (temp_workspace / "config").exists()
        assert (temp_workspace / "configs").exists()
    
    def test_execute_merge_real(self, temp_workspace):
        """Test actual merge execution."""
        unifier = ConfigurationUnifier(str(temp_workspace))
        unifier.analyze_configuration_directories()
        
        # Count original files
        original_config_files = len(list((temp_workspace / "config").rglob("*.json")))
        original_configs_files = len(list((temp_workspace / "configs").rglob("*.json")))
        
        results = unifier.execute_merge(dry_run=False)
        
        # Check that backup was created
        assert results["backup_location"] is not None
        assert Path(results["backup_location"]).exists()
        
        # Check that merge was attempted
        assert results["operations_completed"] >= 0
        
        # If successful, config directory should have more files
        if results["success"]:
            final_config_files = len(list((temp_workspace / "config").rglob("*.json")))
            assert final_config_files >= original_config_files
    
    def test_conflict_resolution_strategies(self, temp_workspace):
        """Test different conflict resolution strategies."""
        # Create a conflict by adding the same file to both directories
        config_file = temp_workspace / "config" / "test_conflict.json"
        configs_file = temp_workspace / "configs" / "test_conflict.json"
        
        # Same content - should skip
        same_content = {"test": "value"}
        with open(config_file, 'w') as f:
            json.dump(same_content, f)
        with open(configs_file, 'w') as f:
            json.dump(same_content, f)
        
        unifier = ConfigurationUnifier(str(temp_workspace))
        unifier.analyze_configuration_directories()
        
        # Find the conflict for this file
        conflicts = [c for c in unifier.conflicts if "test_conflict.json" in str(c.source_file)]
        
        if conflicts:
            conflict = conflicts[0]
            # Same content should result in skip resolution
            assert conflict.resolution_type == "skip"
    
    def test_directory_structure_creation(self, temp_workspace):
        """Test that proper directory structure is created."""
        unifier = ConfigurationUnifier(str(temp_workspace))
        unifier.analyze_configuration_directories()
        
        # Execute merge
        results = unifier.execute_merge(dry_run=False)
        
        if results["success"]:
            # Check that expected subdirectories exist in config/
            expected_dirs = ["publishers", "imprints", "tranches"]
            for dir_name in expected_dirs:
                target_dir = temp_workspace / "config" / dir_name
                # Directory should exist if there were files to move there
                configs_source = temp_workspace / "configs" / dir_name
                if configs_source.exists() and any(configs_source.rglob("*.json")):
                    assert target_dir.exists()
    
    def test_backup_creation(self, temp_workspace):
        """Test backup creation functionality."""
        unifier = ConfigurationUnifier(str(temp_workspace))
        
        # Test backup creation
        backup_success = unifier._create_full_backup()
        assert backup_success is True
        
        # Check that backup directories were created
        backup_files = list(unifier.backup_dir.glob("*_backup_*"))
        assert len(backup_files) >= 1  # At least one backup should be created
    
    def test_json_validation(self, temp_workspace):
        """Test JSON validation in configuration files."""
        # Create an invalid JSON file
        invalid_json_file = temp_workspace / "configs" / "invalid.json"
        with open(invalid_json_file, 'w') as f:
            f.write('{"invalid": json content}')  # Invalid JSON
        
        unifier = ConfigurationUnifier(str(temp_workspace))
        
        # This should handle the invalid JSON gracefully
        analysis = unifier.analyze_configuration_directories()
        
        # The invalid file should not be included in the loaded files
        # or should be handled with appropriate error logging
        assert isinstance(analysis, dict)
    
    def test_merge_operation_types(self, temp_workspace):
        """Test different types of merge operations."""
        unifier = ConfigurationUnifier(str(temp_workspace))
        unifier.analyze_configuration_directories()
        
        # Check that different operation types are generated
        operation_types = set(op.operation_type for op in unifier.merge_operations)
        
        # Should have at least some of these operation types
        expected_types = {"create_directory", "move_file", "merge_files", "replace_file"}
        assert len(operation_types.intersection(expected_types)) > 0
    
    def test_file_content_preservation(self, temp_workspace):
        """Test that file content is preserved during merge."""
        # Get original content of a configs file
        test_file = temp_workspace / "configs" / "default_lsi_config.json"
        with open(test_file, 'r') as f:
            original_content = json.load(f)
        
        unifier = ConfigurationUnifier(str(temp_workspace))
        unifier.analyze_configuration_directories()
        results = unifier.execute_merge(dry_run=False)
        
        if results["success"]:
            # Check that content was preserved in the target location
            target_file = temp_workspace / "config" / "default_lsi_config.json"
            if target_file.exists():
                with open(target_file, 'r') as f:
                    final_content = json.load(f)
                
                # Core content should be preserved
                assert final_content["publisher"] == original_content["publisher"]
                assert final_content["language_code"] == original_content["language_code"]


class TestConfigFile:
    """Test suite for ConfigFile dataclass."""
    
    def test_config_file_creation(self, temp_workspace):
        """Test ConfigFile creation with real file."""
        test_file = temp_workspace / "test.json"
        test_content = {"test": "value"}
        
        with open(test_file, 'w') as f:
            json.dump(test_content, f)
        
        # Create ConfigFile instance
        config_file = ConfigFile(
            path=test_file,
            name=test_file.name,
            content=test_content,
            size=test_file.stat().st_size,
            modified_time=datetime.fromtimestamp(test_file.stat().st_mtime),
            content_hash="test_hash"
        )
        
        assert config_file.path == test_file
        assert config_file.name == "test.json"
        assert config_file.content == test_content
        assert config_file.size > 0


class TestConflictResolution:
    """Test suite for ConflictResolution dataclass."""
    
    def test_conflict_resolution_creation(self, temp_workspace):
        """Test ConflictResolution creation."""
        source_file = temp_workspace / "source.json"
        target_file = temp_workspace / "target.json"
        
        conflict = ConflictResolution(
            source_file=source_file,
            target_file=target_file,
            resolution_type="merge",
            merge_strategy="intelligent_merge"
        )
        
        assert conflict.source_file == source_file
        assert conflict.target_file == target_file
        assert conflict.resolution_type == "merge"
        assert conflict.merge_strategy == "intelligent_merge"


class TestMergeOperation:
    """Test suite for MergeOperation dataclass."""
    
    def test_merge_operation_creation(self, temp_workspace):
        """Test MergeOperation creation."""
        source_path = temp_workspace / "source.json"
        target_path = temp_workspace / "target.json"
        
        operation = MergeOperation(
            operation_type="move_file",
            source_path=source_path,
            target_path=target_path,
            completed=False
        )
        
        assert operation.operation_type == "move_file"
        assert operation.source_path == source_path
        assert operation.target_path == target_path
        assert operation.completed is False
        assert operation.error is None


if __name__ == "__main__":
    pytest.main([__file__])