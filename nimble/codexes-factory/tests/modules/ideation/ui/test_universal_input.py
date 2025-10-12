"""
Tests for Universal Content Input Component
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.codexes.modules.ideation.ui.components.universal_input import UniversalContentInput
from src.codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType


class TestUniversalContentInput:
    """Test cases for UniversalContentInput component."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.input_component = UniversalContentInput()
    
    def test_initialization(self):
        """Test component initialization."""
        assert self.input_component.session_key == "universal_input_state"
        assert hasattr(self.input_component, '_initialize_session_state')
    
    def test_suggest_title_from_short_content(self):
        """Test title suggestion from short content."""
        content = "A story about time travel"
        suggested_title = self.input_component._suggest_title(content)
        assert suggested_title == "A story about time travel"
    
    def test_suggest_title_from_long_content(self):
        """Test title suggestion from longer content."""
        content = "This is a very long piece of content that should be truncated when used as a title because it's too long to be a good title."
        suggested_title = self.input_component._suggest_title(content)
        assert len(suggested_title) <= 100
        assert suggested_title.startswith("This is a very long piece")
    
    def test_suggest_title_from_multiline_content(self):
        """Test title suggestion from multiline content."""
        content = "The Great Adventure\n\nThis is the story of a hero who goes on a great adventure..."
        suggested_title = self.input_component._suggest_title(content)
        assert suggested_title == "The Great Adventure"
    
    def test_create_codex_object(self):
        """Test CodexObject creation."""
        content = "A story about dragons and magic"
        content_type = CodexObjectType.IDEA
        title = "Dragon Story"
        
        codex_object = self.input_component._create_codex_object(content, content_type, title)
        
        assert isinstance(codex_object, CodexObject)
        assert codex_object.content == content
        assert codex_object.object_type == content_type
        assert codex_object.title == title
        assert codex_object.word_count == 6  # "A story about dragons and magic"
        assert codex_object.uuid is not None
        assert codex_object.created_timestamp is not None
    
    def test_create_codex_object_with_auto_title(self):
        """Test CodexObject creation with automatic title generation."""
        content = "A mysterious tale of adventure"
        content_type = CodexObjectType.SYNOPSIS
        title = ""  # Empty title should trigger auto-generation
        
        codex_object = self.input_component._create_codex_object(content, content_type, title)
        
        assert codex_object.title == "A mysterious tale of adventure"
    
    def test_empty_content_handling(self):
        """Test handling of empty content."""
        suggested_title = self.input_component._suggest_title("")
        assert suggested_title == ""
        
        suggested_title = self.input_component._suggest_title("   ")
        assert suggested_title == ""


if __name__ == "__main__":
    pytest.main([__file__])