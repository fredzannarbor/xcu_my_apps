"""
Unit tests for CodexObject base class.
"""

import pytest
import json
import tempfile
from datetime import datetime
from pathlib import Path

from codexes.modules.ideation.core.codex_object import (
    CodexObject, CodexObjectType, DevelopmentStage
)
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestCodexObject:
    """Test cases for CodexObject class."""
    
    def test_codex_object_creation(self):
        """Test basic CodexObject creation."""
        obj = CodexObject(
            title="Test Idea",
            content="This is a test idea for a book about space exploration.",
            object_type=CodexObjectType.IDEA,
            genre="Science Fiction"
        )
        
        assert obj.title == "Test Idea"
        assert obj.object_type == CodexObjectType.IDEA
        assert obj.genre == "Science Fiction"
        assert obj.shortuuid == obj.uuid[:8]
        assert obj.word_count > 0
        assert len(obj.processing_history) == 1
        assert obj.processing_history[0]["action"] == "created"
    
    def test_codex_object_post_init(self):
        """Test post-initialization logic."""
        obj = CodexObject(
            content="A short story about robots and humans living together in harmony."
        )
        
        # Should auto-calculate word count
        assert obj.word_count == 11
        
        # Should have processing history
        assert len(obj.processing_history) == 1
        assert obj.processing_history[0]["action"] == "created"
    
    def test_update_content(self):
        """Test content updating with history tracking."""
        obj = CodexObject(title="Test", content="Original content")
        original_word_count = obj.word_count
        
        new_content = "This is much longer content with many more words than before."
        obj.update_content(new_content, "manual_edit")
        
        assert obj.content == new_content
        assert obj.word_count != original_word_count
        assert len(obj.processing_history) == 2
        assert obj.processing_history[1]["action"] == "content_updated"
        assert obj.processing_history[1]["details"]["update_type"] == "manual_edit"
    
    def test_set_classification(self):
        """Test classification setting with history tracking."""
        obj = CodexObject(title="Test", content="Test content")
        
        obj.set_classification(
            CodexObjectType.SYNOPSIS, 
            0.85, 
            {"classifier": "test_classifier"}
        )
        
        assert obj.object_type == CodexObjectType.SYNOPSIS
        assert obj.confidence_score == 0.85
        assert obj.status == "classified"
        
        # Check processing history
        classification_entry = obj.processing_history[-1]
        assert classification_entry["action"] == "classified"
        assert classification_entry["details"]["new_type"] == "synopsis"
        assert classification_entry["details"]["confidence"] == 0.85
    
    def test_add_evaluation_score(self):
        """Test adding evaluation scores."""
        obj = CodexObject(title="Test", content="Test content")
        
        obj.add_evaluation_score("tournament_judge", 8.5, {"round": "semifinals"})
        
        assert "tournament_judge" in obj.evaluation_scores
        assert obj.evaluation_scores["tournament_judge"] == 8.5
        
        # Check processing history
        eval_entry = obj.processing_history[-1]
        assert eval_entry["action"] == "evaluated"
        assert eval_entry["details"]["evaluator"] == "tournament_judge"
        assert eval_entry["details"]["score"] == 8.5
    
    def test_add_reader_feedback(self):
        """Test adding reader feedback."""
        obj = CodexObject(title="Test", content="Test content")
        
        feedback = {
            "reader_id": "reader_001",
            "rating": 4.2,
            "comments": "Interesting premise but needs more character development"
        }
        
        obj.add_reader_feedback(feedback)
        
        assert len(obj.reader_feedback) == 1
        assert obj.reader_feedback[0]["reader_id"] == "reader_001"
        assert "timestamp" in obj.reader_feedback[0]
        
        # Check processing history
        feedback_entry = obj.processing_history[-1]
        assert feedback_entry["action"] == "reader_feedback_added"
    
    def test_transform_to_type(self):
        """Test transformation to different type."""
        original = CodexObject(
            title="Original Idea",
            content="A story about time travel",
            object_type=CodexObjectType.IDEA,
            genre="Science Fiction"
        )
        
        transformed = original.transform_to_type(
            CodexObjectType.SYNOPSIS,
            {"method": "manual_expansion"}
        )
        
        assert transformed.object_type == CodexObjectType.SYNOPSIS
        assert transformed.parent_uuid == original.uuid
        assert original.uuid in transformed.derived_from
        assert transformed.development_stage == DevelopmentStage.DEVELOPMENT
        
        # Both objects should have transformation records
        assert len(original.processing_history) == 2
        assert len(transformed.processing_history) == 2
        assert original.processing_history[-1]["action"] == "transformed"
        assert transformed.processing_history[-1]["action"] == "transformed"
    
    def test_to_codex_metadata(self):
        """Test conversion to CodexMetadata."""
        obj = CodexObject(
            title="Test Book",
            content="A comprehensive story about adventure and discovery.",
            logline="A young explorer discovers a hidden world.",
            genre="Adventure",
            target_audience="Young Adult",
            tags=["adventure", "discovery", "young adult"]
        )
        
        metadata = obj.to_codex_metadata()
        
        assert isinstance(metadata, CodexMetadata)
        assert metadata.title == "Test Book"
        assert metadata.summary_short == "A young explorer discovers a hidden world."
        assert metadata.summary_long == "A comprehensive story about adventure and discovery."
        assert metadata.keywords == "adventure; discovery; young adult"
        assert metadata.bisac_text == "Adventure"
        assert metadata.audience == "Young Adult"
        
        # Check that ideation data is preserved
        ideation_data = metadata.raw_llm_responses.get("ideation_data")
        assert ideation_data is not None
        assert ideation_data["object_type"] == obj.object_type.value
    
    def test_from_codex_metadata(self):
        """Test creation from CodexMetadata."""
        metadata = CodexMetadata(
            title="Test Book",
            summary_short="A brief description",
            summary_long="A longer description of the book content",
            bisac_text="Fiction",
            audience="General",
            word_count=150,
            keywords="fiction; general; test"
        )
        
        # Add ideation data
        metadata.raw_llm_responses["ideation_data"] = {
            "object_type": "synopsis",
            "development_stage": "development",
            "confidence_score": 0.8,
            "tournament_performance": {"wins": 3, "losses": 1},
            "reader_feedback": [{"rating": 4.0}]
        }
        
        obj = CodexObject.from_codex_metadata(metadata)
        
        assert obj.title == "Test Book"
        assert obj.object_type == CodexObjectType.SYNOPSIS
        assert obj.development_stage == DevelopmentStage.DEVELOPMENT
        assert obj.confidence_score == 0.8
        assert obj.tournament_performance == {"wins": 3, "losses": 1}
        assert len(obj.reader_feedback) == 1
    
    def test_to_dict_and_from_dict(self):
        """Test dictionary serialization and deserialization."""
        original = CodexObject(
            title="Test Object",
            content="Test content for serialization",
            object_type=CodexObjectType.OUTLINE,
            development_stage=DevelopmentStage.REVISION,
            genre="Fantasy",
            tags=["fantasy", "magic"]
        )
        
        # Convert to dict
        data = original.to_dict()
        
        assert data["title"] == "Test Object"
        assert data["object_type"] == "outline"
        assert data["development_stage"] == "revision"
        assert data["genre"] == "Fantasy"
        
        # Convert back from dict
        restored = CodexObject.from_dict(data)
        
        assert restored.title == original.title
        assert restored.object_type == original.object_type
        assert restored.development_stage == original.development_stage
        assert restored.genre == original.genre
        assert restored.tags == original.tags
    
    def test_save_and_load_file(self):
        """Test file save and load operations."""
        original = CodexObject(
            title="File Test Object",
            content="Content for file testing",
            object_type=CodexObjectType.TREATMENT,
            genre="Drama"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_object.json"
            
            # Save to file
            original.save_to_file(str(file_path))
            assert file_path.exists()
            
            # Load from file
            loaded = CodexObject.load_from_file(str(file_path))
            
            assert loaded.title == original.title
            assert loaded.content == original.content
            assert loaded.object_type == original.object_type
            assert loaded.genre == original.genre
    
    def test_is_specific_enough_for_development(self):
        """Test development readiness assessment."""
        # Insufficient idea
        insufficient = CodexObject(title="Vague")
        assert not insufficient.is_specific_enough_for_development()
        
        # Sufficient idea
        sufficient_idea = CodexObject(
            title="Detailed Idea",
            content="A comprehensive story about a detective solving mysteries in Victorian London",
            object_type=CodexObjectType.IDEA
        )
        assert sufficient_idea.is_specific_enough_for_development()
        
        # Sufficient logline
        sufficient_logline = CodexObject(
            logline="A young wizard must save his school from an ancient evil that threatens to destroy everything he holds dear",
            object_type=CodexObjectType.LOGLINE
        )
        assert sufficient_logline.is_specific_enough_for_development()
        
        # Insufficient synopsis
        insufficient_synopsis = CodexObject(
            title="Short Synopsis",
            content="A story.",
            object_type=CodexObjectType.SYNOPSIS
        )
        assert not insufficient_synopsis.is_specific_enough_for_development()
    
    def test_get_development_suggestions(self):
        """Test development suggestions generation."""
        obj = CodexObject(
            title="Incomplete Object",
            content="Short content"
        )
        
        suggestions = obj.get_development_suggestions()
        
        assert "Create a one-sentence logline" in suggestions
        assert "Specify the genre" in suggestions
        assert "Define the target audience" in suggestions
        assert "Add relevant tags for categorization" in suggestions
    
    def test_string_representations(self):
        """Test string representation methods."""
        obj = CodexObject(
            title="Test Object for String Representation",
            object_type=CodexObjectType.IDEA,
            status="classified"
        )
        
        str_repr = str(obj)
        assert "CodexObject(idea)" in str_repr
        assert "Test Object for String Representation" in str_repr
        
        repr_str = repr(obj)
        assert "CodexObject(" in repr_str
        assert obj.shortuuid in repr_str
        assert "type='idea'" in repr_str
        assert "status='classified'" in repr_str


class TestCodexObjectEnums:
    """Test cases for CodexObject enums."""
    
    def test_codex_object_type_enum(self):
        """Test CodexObjectType enum values."""
        assert CodexObjectType.IDEA.value == "idea"
        assert CodexObjectType.SYNOPSIS.value == "synopsis"
        assert CodexObjectType.MANUSCRIPT.value == "manuscript"
        assert CodexObjectType.UNKNOWN.value == "unknown"
    
    def test_development_stage_enum(self):
        """Test DevelopmentStage enum values."""
        assert DevelopmentStage.CONCEPT.value == "concept"
        assert DevelopmentStage.DEVELOPMENT.value == "development"
        assert DevelopmentStage.COMPLETE.value == "complete"
        assert DevelopmentStage.PUBLISHED.value == "published"


class TestCodexObjectIntegration:
    """Integration tests for CodexObject with other components."""
    
    def test_metadata_roundtrip_preservation(self):
        """Test that ideation data is preserved through metadata conversion."""
        original = CodexObject(
            title="Integration Test",
            content="Content for integration testing",
            object_type=CodexObjectType.SYNOPSIS,
            development_stage=DevelopmentStage.REVISION
        )
        
        # Add some ideation-specific data
        original.add_evaluation_score("test_evaluator", 7.5)
        original.add_reader_feedback({"rating": 4.0, "comment": "Good story"})
        original.tournament_performance = {"wins": 2, "losses": 1}
        
        # Convert to metadata and back
        metadata = original.to_codex_metadata()
        restored = CodexObject.from_codex_metadata(metadata)
        
        # Check that ideation data is preserved
        assert restored.object_type == original.object_type
        assert restored.development_stage == original.development_stage
        assert restored.evaluation_scores == original.evaluation_scores
        assert restored.reader_feedback == original.reader_feedback
        assert restored.tournament_performance == original.tournament_performance
    
    def test_processing_history_tracking(self):
        """Test that processing history is properly maintained."""
        obj = CodexObject(title="History Test", content="Initial content")
        
        # Perform various operations
        obj.update_content("Updated content", "manual_edit")
        obj.set_classification(CodexObjectType.SYNOPSIS, 0.8)
        obj.add_evaluation_score("judge1", 8.0)
        obj.add_reader_feedback({"rating": 4.5})
        
        # Check history entries
        assert len(obj.processing_history) == 5  # created + 4 operations
        
        actions = [entry["action"] for entry in obj.processing_history]
        assert "created" in actions
        assert "content_updated" in actions
        assert "classified" in actions
        assert "evaluated" in actions
        assert "reader_feedback_added" in actions
        
        # Check timestamps are present and valid
        for entry in obj.processing_history:
            assert "timestamp" in entry
            # Should be valid ISO format
            datetime.fromisoformat(entry["timestamp"])