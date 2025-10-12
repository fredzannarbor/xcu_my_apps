"""
Tests for Content Type Detection Components
"""

import pytest
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.codexes.ui.components.content_detector import (
    RuleBasedClassifier, 
    ContentTypeDetector, 
    MockLLMClassifier
)
from src.codexes.ui.core.simple_codex_object import CodexObjectType
from src.codexes.ui.config.model_config import ModelConfigManager


class TestRuleBasedClassifier:
    """Test cases for RuleBasedClassifier."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = RuleBasedClassifier()
    
    def test_empty_content(self):
        """Test handling of empty content."""
        result = self.classifier.classify("")
        assert result['type'] == CodexObjectType.IDEA
        assert result['confidence'] == 0.1
    
    def test_very_short_idea(self):
        """Test classification of very short ideas."""
        result = self.classifier.classify("Magic story")
        assert result['type'] == CodexObjectType.IDEA
        assert result['confidence'] == 0.9
    
    def test_logline_detection(self):
        """Test logline detection."""
        logline = "When a young wizard discovers his powers, he must save the world."
        result = self.classifier.classify(logline)
        assert result['type'] == CodexObjectType.LOGLINE
        assert result['confidence'] > 0.8
    
    def test_outline_detection(self):
        """Test outline structure detection."""
        outline = "Chapter 1: Beginning\nChapter 2: Middle\nChapter 3: End"
        result = self.classifier.classify(outline)
        assert result['type'] == CodexObjectType.OUTLINE
        assert result['confidence'] > 0.8
    
    def test_numbered_list_outline(self):
        """Test numbered list outline detection."""
        outline = "1. Introduction\n2. Rising Action\n3. Climax\n4. Resolution"
        result = self.classifier.classify(outline)
        assert result['type'] == CodexObjectType.OUTLINE
        assert result['confidence'] > 0.8
    
    def test_narrative_detection(self):
        """Test narrative structure detection."""
        narrative = '''
        "Hello," she said, looking out the window. The rain was falling steadily now.
        She had been waiting for this moment for years. He walked into the room.
        "Are you ready?" he asked. She nodded, knowing that everything would change.
        The story continues with more dialogue and narrative elements.
        '''
        result = self.classifier.classify(narrative)
        # Should detect as some form of narrative content (could be summary, draft, or manuscript)
        assert result['type'] in [CodexObjectType.SUMMARY, CodexObjectType.DRAFT, CodexObjectType.MANUSCRIPT, CodexObjectType.IDEA]
    
    def test_synopsis_indicators(self):
        """Test synopsis indicator detection."""
        synopsis = '''
        The story follows a young protagonist who discovers magical powers.
        The character must learn to control these abilities while facing an antagonist.
        The narrative explores themes of growth and the conflict between good and evil.
        The plot develops through three acts with rising action leading to climax.
        '''
        result = self.classifier.classify(synopsis)
        # Should detect as some form of story description
        assert result['type'] in [CodexObjectType.SYNOPSIS, CodexObjectType.SUMMARY, CodexObjectType.IDEA]


class TestContentTypeDetector:
    """Test cases for ContentTypeDetector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = ContentTypeDetector()
    
    def test_rule_based_detection(self):
        """Test rule-based detection."""
        content = "A story about dragons"
        detected_type, confidence, reasoning = self.detector.detect_type(content, use_llm=False)
        
        assert isinstance(detected_type, CodexObjectType)
        assert 0.0 <= confidence <= 1.0
        assert isinstance(reasoning, str)
        assert "Rule-based" in reasoning
    
    def test_llm_detection(self):
        """Test LLM-based detection (mock)."""
        content = "Chapter 1: The Adventure Begins"
        detected_type, confidence, reasoning = self.detector.detect_type(content, use_llm=True)
        
        assert isinstance(detected_type, CodexObjectType)
        assert 0.0 <= confidence <= 1.0
        assert isinstance(reasoning, str)
        assert "LLM analysis" in reasoning
    
    def test_caching(self):
        """Test that caching works correctly."""
        content = "Test content for caching"
        
        # First call
        type1, conf1, reason1 = self.detector.detect_type(content, use_llm=False)
        
        # Second call should use cache
        type2, conf2, reason2 = self.detector.detect_type(content, use_llm=False)
        
        assert type1 == type2
        assert conf1 == conf2
        assert reason1 == reason2
    
    def test_detection_details(self):
        """Test detailed detection information."""
        content = "Chapter 1: Test\nThis is a test chapter."
        details = self.detector.get_detection_details(content, use_llm=True)
        
        assert 'content_length' in details
        assert 'word_count' in details
        assert 'line_count' in details
        assert 'rule_based' in details
        assert 'llm_based' in details
        assert 'selected_model' in details
        
        assert details['word_count'] == len(content.split())
        assert details['content_length'] == len(content)


class TestModelConfigManager:
    """Test cases for ModelConfigManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ModelConfigManager()
    
    def test_default_models(self):
        """Test default model list."""
        models = self.config.get_available_models()
        assert len(models) == 9
        assert "ollama/mistral" in models
        assert "gemini/gemini-2.5-flash" in models
    
    def test_component_override(self):
        """Test component-specific model overrides."""
        custom_models = ["custom/model1", "custom/model2"]
        self.config.set_component_override("test_component", custom_models)
        
        override_models = self.config.get_available_models("test_component")
        assert override_models == custom_models
        
        # Default should still work for other components
        default_models = self.config.get_available_models("other_component")
        assert len(default_models) == 9
    
    def test_model_validation(self):
        """Test model validation."""
        assert self.config.validate_model("ollama/mistral") == True
        assert self.config.validate_model("nonexistent/model") == False


class TestMultipleObjectDetection:
    """Test cases for multiple object detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = ContentTypeDetector()
    
    def test_numbered_list_detection(self):
        """Test detection of numbered lists as multiple objects."""
        content = "1. A story about time travel\n2. Dragons in modern cities\n3. Magic school adventures"
        result = self.detector.detect_type_and_multiplicity(content)
        
        assert result['is_multiple'] == True
        assert result['count'] == 3
        assert result['confidence'] > 0.7
        assert 'numbered' in result['reasoning'].lower()
    
    def test_bullet_list_detection(self):
        """Test detection of bullet lists as multiple objects."""
        content = "- Vampire detective story\n- Alien invasion comedy\n- Robot uprising drama"
        result = self.detector.detect_type_and_multiplicity(content)
        
        assert result['is_multiple'] == True
        assert result['count'] == 3
        assert result['confidence'] > 0.7
        assert 'bulleted' in result['reasoning'].lower()
    
    def test_single_object_not_multiple(self):
        """Test that single objects are not detected as multiple."""
        content = "This is a single story about a hero who goes on a journey."
        result = self.detector.detect_type_and_multiplicity(content)
        
        assert result['is_multiple'] == False
        assert result['count'] == 1
    
    def test_paragraph_separation(self):
        """Test detection of paragraph-separated objects."""
        content = """A magical adventure in a fantasy realm.

A science fiction story about space exploration.

A mystery novel set in Victorian London."""
        result = self.detector.detect_type_and_multiplicity(content)
        
        assert result['is_multiple'] == True
        assert result['count'] == 3
        assert 'paragraphs' in result['reasoning'].lower()
    
    def test_object_splitting(self):
        """Test splitting of multiple objects."""
        content = "1. First idea\n2. Second concept\n3. Third thought"
        classifier = self.detector.rule_classifier
        
        objects = classifier.split_multiple_objects(content)
        assert len(objects) == 3
        assert "First idea" in objects[0]
        assert "Second concept" in objects[1]
        assert "Third thought" in objects[2]
    
    def test_empty_content_multiplicity(self):
        """Test multiplicity detection with empty content."""
        result = self.detector.detect_type_and_multiplicity("")
        
        assert result['is_multiple'] == False
        assert result['count'] == 0
        assert result['type'] == CodexObjectType.IDEA


if __name__ == "__main__":
    pytest.main([__file__])