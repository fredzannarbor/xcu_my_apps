"""
Unit tests for FileManager and IdeationFileManager.
"""

import pytest
import tempfile
import json
from pathlib import Path

from codexes.modules.ideation.storage.file_manager import (
    FileManager, IdeationFileManager
)
from codexes.modules.ideation.core.codex_object import (
    CodexObject, CodexObjectType, DevelopmentStage
)


class TestFileManager:
    """Test cases for FileManager class."""
    
    def setup_method(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_directory_initialization(self):
        """Test that directory structure is created properly."""
        base_path = Path(self.temp_dir)
        
        # Check that key directories exist
        assert (base_path / "objects" / "ideas").exists()
        assert (base_path / "objects" / "synopses").exists()
        assert (base_path / "tournaments").exists()
        assert (base_path / "series").exists()
        assert (base_path / "synthetic_readers" / "panels").exists()
        assert (base_path / "exports").exists()
    
    def test_get_object_directory(self):
        """Test getting correct directory for object types."""
        ideas_dir = self.file_manager.get_object_directory(CodexObjectType.IDEA)
        assert ideas_dir.name == "ideas"
        
        synopses_dir = self.file_manager.get_object_directory(CodexObjectType.SYNOPSIS)
        assert synopses_dir.name == "synopses"
        
        unknown_dir = self.file_manager.get_object_directory(CodexObjectType.UNKNOWN)
        assert unknown_dir.name == "unknown"
    
    def test_save_and_load_codex_object_file(self):
        """Test saving and loading CodexObject files."""
        # Create test object
        obj = CodexObject(
            title="Test File Object",
            content="Content for file testing",
            object_type=CodexObjectType.IDEA,
            genre="Fantasy"
        )
        
        # Save to file
        file_path = self.file_manager.save_codex_object_file(obj)
        assert Path(file_path).exists()
        
        # Load from file
        loaded_obj = self.file_manager.load_codex_object_file(file_path)
        assert loaded_obj is not None
        assert loaded_obj.title == obj.title
        assert loaded_obj.content == obj.content
        assert loaded_obj.object_type == obj.object_type
        assert loaded_obj.genre == obj.genre
    
    def test_find_object_files(self):
        """Test finding object files."""
        # Create test objects
        objects = [
            CodexObject(title="Idea 1", object_type=CodexObjectType.IDEA),
            CodexObject(title="Idea 2", object_type=CodexObjectType.IDEA),
            CodexObject(title="Synopsis 1", object_type=CodexObjectType.SYNOPSIS)
        ]
        
        # Save objects
        for obj in objects:
            self.file_manager.save_codex_object_file(obj)
        
        # Find all files
        all_files = self.file_manager.find_object_files()
        assert len(all_files) == 3
        
        # Find idea files only
        idea_files = self.file_manager.find_object_files(CodexObjectType.IDEA)
        assert len(idea_files) == 2
        
        # Find synopsis files only
        synopsis_files = self.file_manager.find_object_files(CodexObjectType.SYNOPSIS)
        assert len(synopsis_files) == 1
    
    def test_delete_codex_object_file(self):
        """Test deleting CodexObject files."""
        # Create and save test object
        obj = CodexObject(title="Delete Test", object_type=CodexObjectType.IDEA)
        file_path = self.file_manager.save_codex_object_file(obj)
        
        # Verify file exists
        assert Path(file_path).exists()
        
        # Delete file
        success = self.file_manager.delete_codex_object_file(obj)
        assert success is True
        assert not Path(file_path).exists()
        
        # Try to delete again (should return False)
        success = self.file_manager.delete_codex_object_file(obj)
        assert success is False
    
    def test_save_tournament_data(self):
        """Test saving tournament data."""
        tournament_data = {
            "uuid": "tournament-123",
            "name": "Test Tournament",
            "type": "single_elimination",
            "participants": ["obj1", "obj2", "obj3"],
            "bracket": {"round1": [{"match1": ["obj1", "obj2"]}]},
            "results": {"winner": "obj1"}
        }
        
        tournament_dir = self.file_manager.save_tournament_data("tournament-123", tournament_data)
        
        # Verify files were created
        dir_path = Path(tournament_dir)
        assert dir_path.exists()
        assert (dir_path / "tournament.json").exists()
        assert (dir_path / "bracket.json").exists()
        assert (dir_path / "results.json").exists()
    
    def test_load_tournament_data(self):
        """Test loading tournament data."""
        tournament_data = {
            "uuid": "tournament-456",
            "name": "Load Test Tournament",
            "type": "round_robin"
        }
        
        # Save first
        self.file_manager.save_tournament_data("tournament-456", tournament_data)
        
        # Load back
        loaded_data = self.file_manager.load_tournament_data("tournament-456")
        assert loaded_data is not None
        assert loaded_data["name"] == "Load Test Tournament"
        assert loaded_data["type"] == "round_robin"
        
        # Test loading non-existent tournament
        missing_data = self.file_manager.load_tournament_data("non-existent")
        assert missing_data is None
    
    def test_export_to_csv(self):
        """Test CSV export functionality."""
        test_data = [
            {"name": "Object 1", "type": "idea", "score": 8.5},
            {"name": "Object 2", "type": "synopsis", "score": 7.2},
            {"name": "Object 3", "type": "outline", "score": 9.1}
        ]
        
        csv_path = self.file_manager.export_to_csv(test_data, "test_export.csv", "tournaments")
        
        # Verify file was created
        assert Path(csv_path).exists()
        
        # Verify content
        with open(csv_path, 'r') as f:
            content = f.read()
            assert "name,type,score" in content
            assert "Object 1,idea,8.5" in content
    
    def test_export_to_json(self):
        """Test JSON export functionality."""
        test_data = {
            "tournament": "test-tournament",
            "results": [
                {"participant": "obj1", "score": 8.5},
                {"participant": "obj2", "score": 7.2}
            ]
        }
        
        json_path = self.file_manager.export_to_json(test_data, "test_export.json", "analytics")
        
        # Verify file was created
        assert Path(json_path).exists()
        
        # Verify content
        with open(json_path, 'r') as f:
            loaded_data = json.load(f)
            assert loaded_data["tournament"] == "test-tournament"
            assert len(loaded_data["results"]) == 2
    
    def test_create_backup(self):
        """Test backup creation."""
        # Create some test data first
        obj = CodexObject(title="Backup Test", object_type=CodexObjectType.IDEA)
        self.file_manager.save_codex_object_file(obj)
        
        tournament_data = {"uuid": "backup-tournament", "name": "Backup Tournament"}
        self.file_manager.save_tournament_data("backup-tournament", tournament_data)
        
        # Create backup
        backup_dir = self.file_manager.create_backup("test_backup")
        
        # Verify backup was created
        backup_path = Path(backup_dir)
        assert backup_path.exists()
        assert (backup_path / "backup_manifest.json").exists()
        assert (backup_path / "objects").exists()
        assert (backup_path / "tournaments").exists()
        
        # Verify manifest content
        with open(backup_path / "backup_manifest.json", 'r') as f:
            manifest = json.load(f)
            assert manifest["backup_name"] == "test_backup"
            assert "created_timestamp" in manifest
    
    def test_cleanup_temp_files(self):
        """Test temporary file cleanup."""
        # Create temp directory and files
        temp_dir = Path(self.temp_dir) / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        # Create a test temp file
        temp_file = temp_dir / "test_temp.txt"
        temp_file.write_text("temporary content")
        
        # Cleanup (with 0 hours max age to clean everything)
        cleaned_count = self.file_manager.cleanup_temp_files(max_age_hours=0)
        
        # Should have cleaned at least 1 file
        assert cleaned_count >= 1
    
    def test_get_storage_stats(self):
        """Test storage statistics."""
        # Create some test data
        obj = CodexObject(title="Stats Test", object_type=CodexObjectType.IDEA)
        self.file_manager.save_codex_object_file(obj)
        
        # Get stats
        stats = self.file_manager.get_storage_stats()
        
        assert "base_path" in stats
        assert "total_size_mb" in stats
        assert "directory_stats" in stats
        assert isinstance(stats["total_size_mb"], (int, float))


class TestIdeationFileManager:
    """Test cases for IdeationFileManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.ideation_file_manager = IdeationFileManager(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_object(self):
        """Test high-level save and load operations."""
        obj = CodexObject(
            title="High Level Test",
            content="Testing high-level interface",
            object_type=CodexObjectType.SYNOPSIS,
            genre="Science Fiction"
        )
        
        # Save object
        file_path = self.ideation_file_manager.save_object(obj)
        assert Path(file_path).exists()
        
        # Load object
        loaded_obj = self.ideation_file_manager.load_object(file_path)
        assert loaded_obj is not None
        assert loaded_obj.title == obj.title
        assert loaded_obj.genre == obj.genre
    
    def test_find_objects(self):
        """Test finding objects with high-level interface."""
        # Create test objects
        objects = [
            CodexObject(title="Find Test 1", object_type=CodexObjectType.IDEA),
            CodexObject(title="Find Test 2", object_type=CodexObjectType.IDEA),
            CodexObject(title="Find Test 3", object_type=CodexObjectType.SYNOPSIS)
        ]
        
        # Save objects
        for obj in objects:
            self.ideation_file_manager.save_object(obj)
        
        # Find all objects
        all_objects = self.ideation_file_manager.find_objects()
        assert len(all_objects) == 3
        
        # Find ideas only
        ideas = self.ideation_file_manager.find_objects(CodexObjectType.IDEA)
        assert len(ideas) == 2
        assert all(obj.object_type == CodexObjectType.IDEA for obj in ideas)
    
    def test_delete_object(self):
        """Test deleting objects with high-level interface."""
        obj = CodexObject(title="Delete Test", object_type=CodexObjectType.IDEA)
        
        # Save and verify
        file_path = self.ideation_file_manager.save_object(obj)
        assert Path(file_path).exists()
        
        # Delete and verify
        success = self.ideation_file_manager.delete_object(obj)
        assert success is True
        assert not Path(file_path).exists()
    
    def test_export_objects_csv(self):
        """Test exporting objects to CSV."""
        objects = [
            CodexObject(
                title="Export Test 1",
                content="First export test",
                object_type=CodexObjectType.IDEA,
                genre="Fantasy"
            ),
            CodexObject(
                title="Export Test 2", 
                content="Second export test",
                object_type=CodexObjectType.SYNOPSIS,
                genre="Mystery"
            )
        ]
        
        # Add some evaluation data
        objects[0].add_evaluation_score("judge1", 8.5)
        objects[1].add_evaluation_score("judge1", 7.2)
        
        # Export to CSV
        csv_path = self.ideation_file_manager.export_objects_csv(objects, "test_objects.csv")
        
        # Verify file was created and has correct content
        assert Path(csv_path).exists()
        
        with open(csv_path, 'r') as f:
            content = f.read()
            assert "Export Test 1" in content
            assert "Export Test 2" in content
            assert "Fantasy" in content
            assert "Mystery" in content
    
    def test_create_backup(self):
        """Test creating backup with high-level interface."""
        # Create some test data
        obj = CodexObject(title="Backup Test", object_type=CodexObjectType.IDEA)
        self.ideation_file_manager.save_object(obj)
        
        # Create backup
        backup_path = self.ideation_file_manager.create_backup("high_level_backup")
        
        # Verify backup exists
        assert Path(backup_path).exists()
        assert Path(backup_path, "backup_manifest.json").exists()
    
    def test_get_stats(self):
        """Test getting statistics with high-level interface."""
        # Create some test data
        obj = CodexObject(title="Stats Test", object_type=CodexObjectType.IDEA)
        self.ideation_file_manager.save_object(obj)
        
        # Get stats
        stats = self.ideation_file_manager.get_stats()
        
        assert isinstance(stats, dict)
        assert "base_path" in stats
        assert "total_size_mb" in stats