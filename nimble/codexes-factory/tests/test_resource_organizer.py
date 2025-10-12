"""
Tests for ResourceOrganizer class.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.core.resource_organizer import ResourceOrganizer, ResourceMoveOperation


class TestResourceOrganizer:
    """Test cases for ResourceOrganizer."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure for testing."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create directory structure
        (project_path / "images").mkdir()
        (project_path / "resources").mkdir()
        (project_path / "resources" / "images").mkdir()
        
        # Create some test files
        (project_path / "images" / "test_image.png").write_text("fake image content")
        (project_path / "images" / "subdir").mkdir()
        (project_path / "images" / "subdir" / "nested_image.jpg").write_text("nested image")
        
        # Create exported config files
        (project_path / "exported_config_20250101_120000.json").write_text('{"test": "config"}')
        (project_path / "exported_config_20250102_130000.json").write_text('{"test": "config2"}')
        
        # Create some files with references to update
        (project_path / "test_file.py").write_text('image_path = "images/test_image.png"')
        (project_path / "docs").mkdir()
        (project_path / "docs" / "readme.md").write_text("![Image](images/test_image.png)")
        
        yield project_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
    def test_init(self, temp_project):
        """Test ResourceOrganizer initialization."""
        organizer = ResourceOrganizer(str(temp_project))
        
        # Use resolve() to handle symlinks and path normalization
        assert organizer.root_path == temp_project.resolve()
        assert organizer.operations == []
        
    def test_find_exported_files(self, temp_project):
        """Test finding exported config files."""
        organizer = ResourceOrganizer(str(temp_project))
        
        exported_files = organizer.find_exported_files()
        
        assert len(exported_files) == 2
        assert any("exported_config_20250101_120000.json" in f for f in exported_files)
        assert any("exported_config_20250102_130000.json" in f for f in exported_files)
        
    def test_process_images_directory(self, temp_project):
        """Test processing images directory."""
        organizer = ResourceOrganizer(str(temp_project))
        
        moved_files = organizer.process_images_directory()
        
        # Check that files were moved
        assert len(moved_files) == 2
        assert "images/test_image.png" in moved_files
        assert "images/subdir/nested_image.jpg" in moved_files
        
        # Check that files exist in new location
        assert (temp_project / "resources" / "images" / "test_image.png").exists()
        assert (temp_project / "resources" / "images" / "subdir" / "nested_image.jpg").exists()
        
        # Check that original files are gone
        assert not (temp_project / "images" / "test_image.png").exists()
        assert not (temp_project / "images" / "subdir" / "nested_image.jpg").exists()
        
    def test_process_empty_images_directory(self, temp_project):
        """Test processing empty images directory."""
        # Remove all files from images directory
        shutil.rmtree(temp_project / "images")
        (temp_project / "images").mkdir()
        
        organizer = ResourceOrganizer(str(temp_project))
        
        moved_files = organizer.process_images_directory()
        
        # Should return empty dict for empty directory
        assert moved_files == {}
        
        # Should track cleanup operation
        assert len(organizer.operations) == 1
        assert organizer.operations[0].operation_type == "cleanup_directory"
        
    def test_organize_exported_files(self, temp_project):
        """Test organizing exported config files."""
        organizer = ResourceOrganizer(str(temp_project))
        
        moved_files = organizer.organize_exported_files()
        
        # Check that files were moved
        assert len(moved_files) == 2
        
        # Check that exports directory was created
        assert (temp_project / "exports").exists()
        
        # Check that files exist in new location
        assert (temp_project / "exports" / "exported_config_20250101_120000.json").exists()
        assert (temp_project / "exports" / "exported_config_20250102_130000.json").exists()
        
        # Check that original files are gone
        assert not (temp_project / "exported_config_20250101_120000.json").exists()
        assert not (temp_project / "exported_config_20250102_130000.json").exists()
        
    def test_cleanup_empty_directories(self, temp_project):
        """Test cleaning up empty directories."""
        # First move all images
        organizer = ResourceOrganizer(str(temp_project))
        organizer.process_images_directory()
        
        # Now cleanup empty directories
        removed_dirs = organizer.cleanup_empty_directories()
        
        # Should remove the empty images directory
        assert len(removed_dirs) == 1
        # Check that the images directory was removed (path resolution may differ)
        assert not (temp_project / "images").exists()
        
    def test_update_resource_references(self, temp_project):
        """Test updating resource references in files."""
        organizer = ResourceOrganizer(str(temp_project))
        
        updates = {
            "images/test_image.png": "resources/images/test_image.png"
        }
        
        organizer.update_resource_references(updates)
        
        # Check that Python file was updated
        py_content = (temp_project / "test_file.py").read_text()
        assert "resources/images/test_image.png" in py_content
        # Check that the original path was replaced (not just that it doesn't exist as substring)
        assert 'image_path = "resources/images/test_image.png"' in py_content
        
        # Check that Markdown file was updated
        md_content = (temp_project / "docs" / "readme.md").read_text()
        assert "resources/images/test_image.png" in md_content
        assert "![Image](resources/images/test_image.png)" in md_content
        
    def test_validate_resource_organization(self, temp_project):
        """Test validation of resource organization."""
        organizer = ResourceOrganizer(str(temp_project))
        
        # Perform organization
        organizer.process_images_directory()
        organizer.organize_exported_files()
        organizer.cleanup_empty_directories()
        
        # Validate
        results = organizer.validate_resource_organization()
        
        assert results["images_moved"] is True
        assert results["exports_created"] is True
        assert results["references_updated"] is True
        assert results["empty_dirs_cleaned"] is True
        
    def test_rollback_operations(self, temp_project):
        """Test rolling back operations."""
        organizer = ResourceOrganizer(str(temp_project))
        
        # Perform some operations
        organizer.process_images_directory()
        organizer.organize_exported_files()
        
        # Verify files were moved
        assert not (temp_project / "images" / "test_image.png").exists()
        assert (temp_project / "resources" / "images" / "test_image.png").exists()
        
        # Rollback
        success = organizer.rollback_operations()
        
        assert success is True
        
        # Verify files were moved back
        assert (temp_project / "images" / "test_image.png").exists()
        assert not (temp_project / "resources" / "images" / "test_image.png").exists()
        
    def test_move_resources_with_mappings(self, temp_project):
        """Test moving resources with custom mappings."""
        organizer = ResourceOrganizer(str(temp_project))
        
        # Create a custom file to move
        (temp_project / "custom_file.txt").write_text("custom content")
        
        mappings = {
            "custom_file.txt": "resources/custom_file.txt"
        }
        
        success = organizer.move_resources(mappings)
        
        assert success is True
        assert (temp_project / "resources" / "custom_file.txt").exists()
        assert not (temp_project / "custom_file.txt").exists()


class TestResourceMoveOperation:
    """Test cases for ResourceMoveOperation dataclass."""
    
    def test_resource_move_operation_creation(self):
        """Test creating ResourceMoveOperation."""
        operation = ResourceMoveOperation(
            source_path="/old/path",
            destination_path="/new/path",
            operation_type="move_image"
        )
        
        assert operation.source_path == "/old/path"
        assert operation.destination_path == "/new/path"
        assert operation.operation_type == "move_image"
        assert operation.backup_path is None
        assert operation.completed is False
        assert operation.references_updated is False