"""
Basic test to verify the Stage-Agnostic UI components work
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_model_config():
    """Test the ModelConfigManager works."""
    from src.codexes.ui.config.model_config import ModelConfigManager
    
    config = ModelConfigManager()
    
    # Test default models are loaded
    models = config.get_available_models()
    assert len(models) == 9
    assert "ollama/mistral" in models
    assert "gemini/gemini-2.5-flash" in models
    
    # Test component override
    config.set_component_override("test_component", ["custom/model"])
    override_models = config.get_available_models("test_component")
    assert override_models == ["custom/model"]
    
    print("✅ ModelConfigManager test passed")

def test_universal_input_basic():
    """Test basic functionality of UniversalContentInput without full imports."""
    from src.codexes.ui.components.universal_input import UniversalContentInput
    from src.codexes.ui.core.simple_codex_object import CodexObjectType
    
    input_component = UniversalContentInput()
    
    # Test title suggestion
    title = input_component._suggest_title("A story about dragons")
    assert title == "A story about dragons"
    
    # Test multiline title suggestion
    title = input_component._suggest_title("The Great Adventure\n\nThis is a story...")
    assert title == "The Great Adventure"
    
    # Test CodexObject creation
    content = "A magical story about wizards"
    codex_obj = input_component._create_codex_object(content, CodexObjectType.IDEA, "Magic Story")
    assert codex_obj.content == content
    assert codex_obj.title == "Magic Story"
    assert codex_obj.object_type == CodexObjectType.IDEA
    expected_word_count = len(content.split())  # Should be 5 words
    assert codex_obj.word_count == expected_word_count
    
    print("✅ UniversalContentInput basic test passed")

if __name__ == "__main__":
    test_model_config()
    test_universal_input_basic()
    print("🎉 All basic tests passed!")