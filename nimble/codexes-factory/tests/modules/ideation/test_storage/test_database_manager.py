"""
Unit tests for DatabaseManager and IdeationDatabase.
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime

from codexes.modules.ideation.storage.database_manager import (
    DatabaseManager, IdeationDatabase
)
from codexes.modules.ideation.core.codex_object import (
    CodexObject, CodexObjectType, DevelopmentStage
)


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""
    
    def setup_method(self):
        """Set up test fixtures with temporary database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_ideation.db"
        self.db_manager = DatabaseManager(str(self.db_path), pool_size=2)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_database_initialization(self):
        """Test database initialization and schema creation."""
        assert self.db_path.exists()
        
        # Check that tables were created
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'codex_objects', 'tournaments', 'tournament_matches', 'series',
                'reader_panels', 'reader_evaluations', 'story_elements',
                'element_combinations', 'batch_jobs', 'collaboration_sessions',
                'collaboration_contributions'
            ]
            
            for table in expected_tables:
                assert table in tables
    
    def test_connection_pool(self):
        """Test connection pool functionality."""
        # Test getting connections
        with self.db_manager.get_connection() as conn1:
            assert conn1 is not None
            
            with self.db_manager.get_connection() as conn2:
                assert conn2 is not None
                assert conn1 != conn2  # Should be different connections
    
    def test_execute_query(self):
        """Test query execution."""
        # Insert test data
        query = "INSERT INTO codex_objects (uuid, shortuuid, object_type, development_stage, title, created_timestamp, last_modified) VALUES (?, ?, ?, ?, ?, ?, ?)"
        params = ("test-uuid", "test123", "idea", "concept", "Test Title", datetime.now().isoformat(), datetime.now().isoformat())
        
        affected = self.db_manager.execute_update(query, params)
        assert affected == 1
        
        # Query the data back
        results = self.db_manager.execute_query("SELECT * FROM codex_objects WHERE uuid = ?", ("test-uuid",))
        assert len(results) == 1
        assert results[0]['title'] == "Test Title"
    
    def test_execute_transaction(self):
        """Test transaction execution."""
        operations = [
            ("INSERT INTO codex_objects (uuid, shortuuid, object_type, development_stage, title, created_timestamp, last_modified) VALUES (?, ?, ?, ?, ?, ?, ?)",
             ("uuid1", "uuid1", "idea", "concept", "Title 1", datetime.now().isoformat(), datetime.now().isoformat())),
            ("INSERT INTO codex_objects (uuid, shortuuid, object_type, development_stage, title, created_timestamp, last_modified) VALUES (?, ?, ?, ?, ?, ?, ?)",
             ("uuid2", "uuid2", "synopsis", "development", "Title 2", datetime.now().isoformat(), datetime.now().isoformat()))
        ]
        
        success = self.db_manager.execute_transaction(operations)
        assert success is True
        
        # Verify both records were inserted
        results = self.db_manager.execute_query("SELECT COUNT(*) FROM codex_objects")
        assert results[0][0] == 2


class TestIdeationDatabase:
    """Test cases for IdeationDatabase class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_ideation.db"
        self.db_manager = DatabaseManager(str(self.db_path))
        self.ideation_db = IdeationDatabase(self.db_manager)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_codex_object(self):
        """Test saving and loading CodexObjects."""
        # Create test object
        obj = CodexObject(
            title="Test Idea",
            content="This is a test idea for a science fiction story.",
            object_type=CodexObjectType.IDEA,
            development_stage=DevelopmentStage.CONCEPT,
            genre="Science Fiction",
            target_audience="Young Adult",
            tags=["sci-fi", "adventure"]
        )
        
        # Add some evaluation data
        obj.add_evaluation_score("test_judge", 8.5)
        obj.add_reader_feedback({"rating": 4.2, "comment": "Interesting concept"})
        
        # Save to database
        success = self.ideation_db.save_codex_object(obj)
        assert success is True
        
        # Load from database
        loaded_obj = self.ideation_db.load_codex_object(obj.uuid)
        assert loaded_obj is not None
        
        # Verify data integrity
        assert loaded_obj.uuid == obj.uuid
        assert loaded_obj.title == obj.title
        assert loaded_obj.content == obj.content
        assert loaded_obj.object_type == obj.object_type
        assert loaded_obj.development_stage == obj.development_stage
        assert loaded_obj.genre == obj.genre
        assert loaded_obj.target_audience == obj.target_audience
        assert loaded_obj.tags == obj.tags
        assert loaded_obj.evaluation_scores == obj.evaluation_scores
        assert loaded_obj.reader_feedback == obj.reader_feedback
    
    def test_find_codex_objects(self):
        """Test finding CodexObjects with filters."""
        # Create test objects
        objects = [
            CodexObject(
                title="Idea 1",
                content="First idea",
                object_type=CodexObjectType.IDEA,
                development_stage=DevelopmentStage.CONCEPT,
                genre="Fantasy"
            ),
            CodexObject(
                title="Synopsis 1",
                content="First synopsis",
                object_type=CodexObjectType.SYNOPSIS,
                development_stage=DevelopmentStage.DEVELOPMENT,
                genre="Fantasy"
            ),
            CodexObject(
                title="Idea 2",
                content="Second idea",
                object_type=CodexObjectType.IDEA,
                development_stage=DevelopmentStage.CONCEPT,
                genre="Mystery"
            )
        ]
        
        # Save all objects
        for obj in objects:
            self.ideation_db.save_codex_object(obj)
        
        # Test finding by object type
        ideas = self.ideation_db.find_codex_objects(object_type=CodexObjectType.IDEA)
        assert len(ideas) == 2
        assert all(obj.object_type == CodexObjectType.IDEA for obj in ideas)
        
        # Test finding by development stage
        concepts = self.ideation_db.find_codex_objects(development_stage=DevelopmentStage.CONCEPT)
        assert len(concepts) == 2
        assert all(obj.development_stage == DevelopmentStage.CONCEPT for obj in concepts)
        
        # Test finding with multiple filters
        fantasy_ideas = self.ideation_db.find_codex_objects(
            object_type=CodexObjectType.IDEA,
            development_stage=DevelopmentStage.CONCEPT
        )
        assert len(fantasy_ideas) == 2
    
    def test_count_codex_objects(self):
        """Test counting CodexObjects."""
        # Create test objects
        objects = [
            CodexObject(title="Idea 1", object_type=CodexObjectType.IDEA),
            CodexObject(title="Idea 2", object_type=CodexObjectType.IDEA),
            CodexObject(title="Synopsis 1", object_type=CodexObjectType.SYNOPSIS)
        ]
        
        # Save all objects
        for obj in objects:
            self.ideation_db.save_codex_object(obj)
        
        # Test total count
        total_count = self.ideation_db.count_codex_objects()
        assert total_count == 3
        
        # Test count by type
        idea_count = self.ideation_db.count_codex_objects(object_type=CodexObjectType.IDEA)
        assert idea_count == 2
        
        synopsis_count = self.ideation_db.count_codex_objects(object_type=CodexObjectType.SYNOPSIS)
        assert synopsis_count == 1
    
    def test_delete_codex_object(self):
        """Test deleting CodexObjects."""
        # Create and save test object
        obj = CodexObject(title="Test Object", content="Test content")
        self.ideation_db.save_codex_object(obj)
        
        # Verify it exists
        loaded = self.ideation_db.load_codex_object(obj.uuid)
        assert loaded is not None
        
        # Delete it
        success = self.ideation_db.delete_codex_object(obj.uuid)
        assert success is True
        
        # Verify it's gone
        loaded = self.ideation_db.load_codex_object(obj.uuid)
        assert loaded is None
        
        # Test deleting non-existent object
        success = self.ideation_db.delete_codex_object("non-existent-uuid")
        assert success is False
    
    def test_save_and_load_tournament(self):
        """Test tournament data operations."""
        tournament_data = {
            'uuid': 'tournament-123',
            'name': 'Test Tournament',
            'tournament_type': 'single_elimination',
            'status': 'created',
            'config': {'max_participants': 16},
            'created_timestamp': datetime.now().isoformat(),
            'participant_count': 8,
            'round_count': 3
        }
        
        # Save tournament
        success = self.ideation_db.save_tournament(tournament_data)
        assert success is True
        
        # Load tournament
        loaded = self.ideation_db.load_tournament('tournament-123')
        assert loaded is not None
        assert loaded['name'] == 'Test Tournament'
        assert loaded['tournament_type'] == 'single_elimination'
        assert loaded['config']['max_participants'] == 16
    
    def test_save_series(self):
        """Test series data operations."""
        series_data = {
            'uuid': 'series-123',
            'name': 'Test Series',
            'description': 'A test book series',
            'formulaicness_level': 0.7,
            'franchise_mode': True,
            'consistency_rules': {'character_consistency': True},
            'created_timestamp': datetime.now().isoformat(),
            'book_count': 3
        }
        
        # Save series
        success = self.ideation_db.save_series(series_data)
        assert success is True
        
        # Verify it was saved by checking count
        results = self.ideation_db.db.execute_query("SELECT COUNT(*) FROM series")
        assert results[0][0] == 1
    
    def test_get_database_stats(self):
        """Test database statistics."""
        # Create some test data
        objects = [
            CodexObject(title="Idea 1", object_type=CodexObjectType.IDEA),
            CodexObject(title="Synopsis 1", object_type=CodexObjectType.SYNOPSIS),
            CodexObject(title="Outline 1", object_type=CodexObjectType.OUTLINE)
        ]
        
        for obj in objects:
            self.ideation_db.save_codex_object(obj)
        
        # Get stats
        stats = self.ideation_db.get_database_stats()
        
        assert 'codex_objects_idea' in stats
        assert 'codex_objects_synopsis' in stats
        assert 'codex_objects_outline' in stats
        assert 'tournaments' in stats
        assert 'series' in stats
        
        assert stats['codex_objects_idea'] == 1
        assert stats['codex_objects_synopsis'] == 1
        assert stats['codex_objects_outline'] == 1
    
    def test_cleanup_orphaned_records(self):
        """Test cleanup of orphaned records."""
        # This test would require setting up orphaned data
        # For now, just test that the method runs without error
        cleaned_count = self.ideation_db.cleanup_orphaned_records()
        assert isinstance(cleaned_count, int)
        assert cleaned_count >= 0
    
    def test_row_to_codex_object_conversion(self):
        """Test conversion from database row to CodexObject."""
        # Create and save an object with complex data
        obj = CodexObject(
            title="Complex Object",
            content="Complex content with various data",
            object_type=CodexObjectType.SYNOPSIS,
            development_stage=DevelopmentStage.REVISION,
            genre="Fantasy",
            tags=["fantasy", "magic", "adventure"],
            parent_uuid="parent-123",
            source_elements=["element1", "element2"],
            derived_from=["source1", "source2"]
        )
        
        # Add complex metadata
        obj.tournament_performance = {"wins": 3, "losses": 1, "score": 8.5}
        obj.generation_metadata = {"model": "gpt-4", "temperature": 0.7}
        obj.add_evaluation_score("judge1", 8.0)
        obj.add_evaluation_score("judge2", 7.5)
        obj.add_reader_feedback({"reader": "reader1", "rating": 4.0})
        
        # Save and reload
        self.ideation_db.save_codex_object(obj)
        loaded = self.ideation_db.load_codex_object(obj.uuid)
        
        # Verify all complex data is preserved
        assert loaded.tournament_performance == obj.tournament_performance
        assert loaded.generation_metadata == obj.generation_metadata
        assert loaded.evaluation_scores == obj.evaluation_scores
        assert loaded.reader_feedback == obj.reader_feedback
        assert loaded.tags == obj.tags
        assert loaded.parent_uuid == obj.parent_uuid
        assert loaded.source_elements == obj.source_elements
        assert loaded.derived_from == obj.derived_from


class TestDatabaseIntegration:
    """Integration tests for database operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_integration.db"
        self.db_manager = DatabaseManager(str(self.db_path))
        self.ideation_db = IdeationDatabase(self.db_manager)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_object_relationship_integrity(self):
        """Test that object relationships are maintained."""
        # Create parent object
        parent = CodexObject(
            title="Parent Idea",
            content="Original idea",
            object_type=CodexObjectType.IDEA
        )
        self.ideation_db.save_codex_object(parent)
        
        # Create child object
        child = parent.transform_to_type(CodexObjectType.SYNOPSIS)
        child.update_content("Expanded synopsis content", "transformation")
        self.ideation_db.save_codex_object(child)
        
        # Verify relationships
        loaded_child = self.ideation_db.load_codex_object(child.uuid)
        assert loaded_child.parent_uuid == parent.uuid
        assert parent.uuid in loaded_child.derived_from
        
        # Find children of parent
        children = self.ideation_db.find_codex_objects(parent_uuid=parent.uuid)
        assert len(children) == 1
        assert children[0].uuid == child.uuid
    
    def test_concurrent_access(self):
        """Test concurrent database access."""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                for i in range(5):
                    obj = CodexObject(
                        title=f"Worker {worker_id} Object {i}",
                        content=f"Content from worker {worker_id}",
                        object_type=CodexObjectType.IDEA
                    )
                    success = self.ideation_db.save_codex_object(obj)
                    results.append((worker_id, i, success))
                    time.sleep(0.01)  # Small delay to encourage concurrency
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Start multiple worker threads
        threads = []
        for worker_id in range(3):
            thread = threading.Thread(target=worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 15  # 3 workers * 5 objects each
        assert all(success for _, _, success in results)
        
        # Verify all objects were saved
        total_count = self.ideation_db.count_codex_objects()
        assert total_count == 15