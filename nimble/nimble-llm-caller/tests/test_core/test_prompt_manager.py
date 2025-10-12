"""
Tests for the prompt manager functionality.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path

from nimble_llm_caller.core.prompt_manager import PromptManager


class TestPromptManager:
    """Test cases for PromptManager class."""
    
    def test_initialization_without_file(self):
        """Test PromptManager initialization without prompt file."""
        manager = PromptManager()
        
        assert manager.prompt_file_path is None
        assert manager.prompts_cache == {}
        assert manager.template_env is None
    
    def test_initialization_with_file(self, temp_prompts_file):
        """Test PromptManager initialization with prompt file."""
        manager = PromptManager(temp_prompts_file)
        
        assert manager.prompt_file_path == temp_prompts_file
        assert len(manager.prompts_cache) > 0
        assert "simple_prompt" in manager.prompts_cache
    
    def test_load_prompts_success(self, sample_prompts):
        """Test successful prompt loading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_prompts, f)
            temp_path = f.name
        
        try:
            manager = PromptManager()
            result = manager.load_prompts(temp_path)
            
            assert result is True
            assert len(manager.prompts_cache) == len(sample_prompts)
            assert "simple_prompt" in manager.prompts_cache
        finally:
            os.unlink(temp_path)
    
    def test_load_prompts_file_not_found(self):
        """Test prompt loading with non-existent file."""
        manager = PromptManager()
        result = manager.load_prompts("nonexistent_file.json")
        
        assert result is False
        assert len(manager.prompts_cache) == 0
    
    def test_load_prompts_invalid_json(self):
        """Test prompt loading with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            manager = PromptManager()
            result = manager.load_prompts(temp_path)
            
            assert result is False
            assert len(manager.prompts_cache) == 0
        finally:
            os.unlink(temp_path)
    
    def test_load_multiple_prompt_files(self, sample_prompts):
        """Test loading multiple prompt files."""
        # Create two temporary files
        prompts1 = {"prompt1": sample_prompts["simple_prompt"]}
        prompts2 = {"prompt2": sample_prompts["complex_prompt"]}
        
        files = []
        for prompts in [prompts1, prompts2]:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(prompts, f)
                files.append(f.name)
        
        try:
            manager = PromptManager()
            result = manager.load_multiple_prompt_files(files)
            
            assert result is True
            assert "prompt1" in manager.prompts_cache
            assert "prompt2" in manager.prompts_cache
        finally:
            for file_path in files:
                os.unlink(file_path)
    
    def test_get_prompt(self, prompt_manager):
        """Test getting a prompt by key."""
        prompt = prompt_manager.get_prompt("simple_prompt")
        
        assert prompt is not None
        assert "messages" in prompt
        assert prompt["messages"][0]["content"] == "Say hello to {name}"
    
    def test_get_prompt_not_found(self, prompt_manager):
        """Test getting a non-existent prompt."""
        prompt = prompt_manager.get_prompt("nonexistent_prompt")
        
        assert prompt is None
    
    def test_has_prompt(self, prompt_manager):
        """Test checking if prompt exists."""
        assert prompt_manager.has_prompt("simple_prompt") is True
        assert prompt_manager.has_prompt("nonexistent_prompt") is False
    
    def test_list_prompt_keys(self, prompt_manager):
        """Test listing all prompt keys."""
        keys = prompt_manager.list_prompt_keys()
        
        assert isinstance(keys, list)
        assert "simple_prompt" in keys
        assert "complex_prompt" in keys
        assert "json_prompt" in keys
    
    def test_prepare_prompt_success(self, prompt_manager):
        """Test successful prompt preparation."""
        prepared = prompt_manager.prepare_prompt(
            "simple_prompt",
            {"name": "World"}
        )
        
        assert prepared is not None
        assert "messages" in prepared
        assert prepared["messages"][0]["content"] == "Say hello to World"
        assert "params" in prepared
        assert prepared["prompt_key"] == "simple_prompt"
    
    def test_prepare_prompt_missing_substitution(self, prompt_manager):
        """Test prompt preparation with missing substitution."""
        prepared = prompt_manager.prepare_prompt(
            "simple_prompt",
            {}  # Missing 'name' substitution
        )
        
        assert prepared is not None
        # Should use original content as fallback
        assert "{name}" in prepared["messages"][0]["content"]
    
    def test_prepare_prompt_not_found(self, prompt_manager):
        """Test preparing a non-existent prompt."""
        prepared = prompt_manager.prepare_prompt(
            "nonexistent_prompt",
            {"name": "World"}
        )
        
        assert prepared is None
    
    def test_prepare_prompt_complex(self, prompt_manager):
        """Test preparing a complex prompt with multiple substitutions."""
        prepared = prompt_manager.prepare_prompt(
            "complex_prompt",
            {"topic": "AI", "detail_level": "high"}
        )
        
        assert prepared is not None
        assert len(prepared["messages"]) == 2
        assert "AI" in prepared["messages"][1]["content"]
        assert "high" in prepared["messages"][1]["content"]
    
    def test_prepare_multiple_prompts(self, prompt_manager):
        """Test preparing multiple prompts."""
        prepared_list = prompt_manager.prepare_multiple_prompts(
            ["simple_prompt", "complex_prompt"],
            {"name": "World", "topic": "AI", "detail_level": "medium"}
        )
        
        assert len(prepared_list) == 2
        assert prepared_list[0]["key"] == "simple_prompt"
        assert prepared_list[1]["key"] == "complex_prompt"
        assert "prompt_config" in prepared_list[0]
        assert "prompt_config" in prepared_list[1]
    
    def test_prepare_multiple_prompts_with_missing(self, prompt_manager):
        """Test preparing multiple prompts with some missing."""
        prepared_list = prompt_manager.prepare_multiple_prompts(
            ["simple_prompt", "nonexistent_prompt", "complex_prompt"],
            {"name": "World", "topic": "AI", "detail_level": "medium"}
        )
        
        # Should only return the valid prompts
        assert len(prepared_list) == 2
        keys = [item["key"] for item in prepared_list]
        assert "simple_prompt" in keys
        assert "complex_prompt" in keys
        assert "nonexistent_prompt" not in keys
    
    def test_validate_prompt_structure_valid(self, prompt_manager):
        """Test validation of valid prompt structure."""
        validation = prompt_manager.validate_prompt_structure("simple_prompt")
        
        assert validation["valid"] is True
        assert len(validation["issues"]) == 0
        assert validation["has_messages"] is True
        assert validation["has_params"] is True
    
    def test_validate_prompt_structure_invalid(self):
        """Test validation of invalid prompt structure."""
        manager = PromptManager()
        manager.prompts_cache = {
            "invalid_prompt": {
                "invalid_key": "invalid_value"
            }
        }
        
        validation = manager.validate_prompt_structure("invalid_prompt")
        
        assert validation["valid"] is False
        assert len(validation["issues"]) > 0
        assert "must have either 'messages' or 'prompt' key" in validation["issues"][0]
    
    def test_validate_prompt_structure_not_found(self, prompt_manager):
        """Test validation of non-existent prompt."""
        validation = prompt_manager.validate_prompt_structure("nonexistent_prompt")
        
        assert validation["valid"] is False
        assert validation["error"] == "Prompt key not found"
    
    def test_extract_variables(self, prompt_manager):
        """Test extracting variables from prompt."""
        variables = prompt_manager.extract_variables("simple_prompt")
        
        assert "name" in variables
        assert isinstance(variables, list)
    
    def test_extract_variables_complex(self, prompt_manager):
        """Test extracting variables from complex prompt."""
        variables = prompt_manager.extract_variables("complex_prompt")
        
        assert "topic" in variables
        assert "detail_level" in variables
        assert len(variables) == 2
    
    def test_extract_variables_not_found(self, prompt_manager):
        """Test extracting variables from non-existent prompt."""
        variables = prompt_manager.extract_variables("nonexistent_prompt")
        
        assert variables == []
    
    def test_extract_variables_from_text(self, prompt_manager):
        """Test the internal variable extraction method."""
        text = "Hello {name}, how are you? The weather is {weather}."
        variables = prompt_manager._extract_variables_from_text(text)
        
        assert "name" in variables
        assert "weather" in variables
        assert len(variables) == 2
    
    def test_extract_variables_from_text_with_format_specifiers(self, prompt_manager):
        """Test variable extraction ignoring format specifiers."""
        text = "The price is {price:.2f} and the name is {name}."
        variables = prompt_manager._extract_variables_from_text(text)
        
        # Should only extract 'name', not 'price:.2f'
        assert "name" in variables
        assert "price:.2f" not in variables
        assert len(variables) == 1
    
    def test_get_prompt_statistics(self, prompt_manager):
        """Test getting prompt statistics."""
        stats = prompt_manager.get_prompt_statistics()
        
        assert stats["total_prompts"] > 0
        assert stats["message_format_prompts"] > 0
        assert stats["prompts_with_params"] > 0
        assert stats["prompt_file"] is not None
        assert stats["jinja_enabled"] is False
    
    def test_prepare_prompt_with_jinja(self):
        """Test prompt preparation with Jinja2 templating."""
        # Create a temporary template directory
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = PromptManager(template_dir=temp_dir)
            
            # Add a prompt that could use Jinja2 features
            manager.prompts_cache = {
                "jinja_prompt": {
                    "messages": [
                        {"role": "user", "content": "Hello {{ name|upper }}!"}
                    ]
                }
            }
            
            prepared = manager.prepare_prompt(
                "jinja_prompt",
                {"name": "world"},
                use_jinja=True
            )
            
            assert prepared is not None
            # Note: This test might need adjustment based on actual Jinja2 implementation
    
    def test_simple_prompt_format(self):
        """Test handling of simple prompt format (non-messages)."""
        manager = PromptManager()
        manager.prompts_cache = {
            "simple_format": {
                "prompt": "Say hello to {name}",
                "params": {"temperature": 0.7}
            }
        }
        
        prepared = manager.prepare_prompt(
            "simple_format",
            {"name": "World"}
        )
        
        assert prepared is not None
        assert "messages" in prepared
        assert len(prepared["messages"]) == 1
        assert prepared["messages"][0]["role"] == "user"
        assert "Say hello to World" in prepared["messages"][0]["content"]