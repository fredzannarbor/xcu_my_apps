"""
Unit tests for template management system.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, mock_open

from src.arxiv_writer.templates import (
    TemplateManager,
    TemplateRenderer,
    PromptTemplate,
    LatexTemplate,
    ValidationCriteria,
    RenderedPrompt,
    TemplateValidationResult
)
from src.arxiv_writer.core.exceptions import TemplateError, ValidationError


class TestValidationCriteria:
    """Test ValidationCriteria class."""
    
    def test_init_default(self):
        """Test default initialization."""
        criteria = ValidationCriteria()
        assert criteria.required_opening is None
        assert criteria.word_count_range is None
        assert criteria.must_include_terms == []
        assert criteria.forbidden_terms == []
        assert criteria.max_length is None
        assert criteria.min_length is None
    
    def test_init_with_values(self):
        """Test initialization with values."""
        criteria = ValidationCriteria(
            required_opening="The AI Lab",
            word_count_range=[100, 200],
            must_include_terms=["AI", "research"],
            forbidden_terms=["bad", "wrong"],
            max_length=1000,
            min_length=50
        )
        
        assert criteria.required_opening == "The AI Lab"
        assert criteria.word_count_range == [100, 200]
        assert criteria.must_include_terms == ["AI", "research"]
        assert criteria.forbidden_terms == ["bad", "wrong"]
        assert criteria.max_length == 1000
        assert criteria.min_length == 50
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        criteria = ValidationCriteria(
            required_opening="Test",
            word_count_range=[50, 100]
        )
        
        result = criteria.to_dict()
        expected = {
            'required_opening': "Test",
            'word_count_range': [50, 100],
            'must_include_terms': [],
            'forbidden_terms': [],
            'max_length': None,
            'min_length': None
        }
        
        assert result == expected
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'required_opening': "Test",
            'word_count_range': [50, 100],
            'must_include_terms': ["AI"],
            'forbidden_terms': ["bad"]
        }
        
        criteria = ValidationCriteria.from_dict(data)
        assert criteria.required_opening == "Test"
        assert criteria.word_count_range == [50, 100]
        assert criteria.must_include_terms == ["AI"]
        assert criteria.forbidden_terms == ["bad"]


class TestPromptTemplate:
    """Test PromptTemplate class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        template = PromptTemplate(
            name="test_template",
            system_prompt="You are a helpful assistant.",
            user_prompt="Write about {topic}."
        )
        
        assert template.name == "test_template"
        assert template.system_prompt == "You are a helpful assistant."
        assert template.user_prompt == "Write about {topic}."
        assert template.context_variables == []
        assert isinstance(template.validation_criteria, ValidationCriteria)
    
    def test_init_with_context_variables(self):
        """Test initialization with context variables."""
        template = PromptTemplate(
            name="test_template",
            system_prompt="You are a helpful assistant.",
            user_prompt="Write about {topic} with {details}.",
            context_variables=["topic", "details"]
        )
        
        assert template.context_variables == ["topic", "details"]
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'system_prompt': "You are a helpful assistant.",
            'user_prompt': "Write about {topic}.",
            'context_variables': ["topic"],
            'validation_criteria': {
                'word_count_range': [100, 200]
            },
            'model_parameters': {'temperature': 0.7}
        }
        
        template = PromptTemplate.from_dict("test_template", data)
        assert template.name == "test_template"
        assert template.system_prompt == "You are a helpful assistant."
        assert template.user_prompt == "Write about {topic}."
        assert template.context_variables == ["topic"]
        assert template.validation_criteria.word_count_range == [100, 200]
        assert template.model_parameters == {'temperature': 0.7}
    
    def test_validate_context_success(self):
        """Test successful context validation."""
        template = PromptTemplate(
            name="test",
            system_prompt="System",
            user_prompt="User {topic}",
            context_variables=["topic"]
        )
        
        context = {"topic": "AI"}
        missing = template.validate_context(context)
        assert missing == []
    
    def test_validate_context_missing(self):
        """Test context validation with missing variables."""
        template = PromptTemplate(
            name="test",
            system_prompt="System",
            user_prompt="User {topic} {details}",
            context_variables=["topic", "details"]
        )
        
        context = {"topic": "AI"}
        missing = template.validate_context(context)
        assert missing == ["details"]
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        criteria = ValidationCriteria(word_count_range=[100, 200])
        template = PromptTemplate(
            name="test",
            system_prompt="System",
            user_prompt="User",
            context_variables=["topic"],
            validation_criteria=criteria,
            model_parameters={'temperature': 0.7}
        )
        
        result = template.to_dict()
        assert result['name'] == "test"
        assert result['system_prompt'] == "System"
        assert result['user_prompt'] == "User"
        assert result['context_variables'] == ["topic"]
        assert result['validation_criteria']['word_count_range'] == [100, 200]
        assert result['model_parameters'] == {'temperature': 0.7}


class TestLatexTemplate:
    """Test LatexTemplate class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        template = LatexTemplate(
            name="article_template",
            content="\\documentclass{article}\\begin{document}Hello\\end{document}",
            template_type="latex"
        )
        
        assert template.name == "article_template"
        assert template.template_type == "latex"
        assert template.document_class == "article"
        assert template.packages == []
        assert template.custom_commands == {}
    
    def test_init_with_options(self):
        """Test initialization with options."""
        template = LatexTemplate(
            name="custom_template",
            content="\\documentclass{book}",
            template_type="latex",
            document_class="book",
            packages=["amsmath", "graphicx"],
            custom_commands={"\\mycommand": "\\textbf{#1}"}
        )
        
        assert template.document_class == "book"
        assert template.packages == ["amsmath", "graphicx"]
        assert template.custom_commands == {"\\mycommand": "\\textbf{#1}"}
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'name': 'test_template',
            'content': '\\documentclass{article}',
            'template_type': 'latex',
            'document_class': 'book',
            'packages': ['amsmath'],
            'custom_commands': {'\\cmd': '\\textbf{#1}'},
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        template = LatexTemplate.from_dict(data)
        assert template.name == 'test_template'
        assert template.document_class == 'book'
        assert template.packages == ['amsmath']
        assert template.custom_commands == {'\\cmd': '\\textbf{#1}'}


class TestTemplateRenderer:
    """Test TemplateRenderer class."""
    
    def test_init_default(self):
        """Test default initialization."""
        renderer = TemplateRenderer()
        assert renderer.enable_jinja2 is True  # Assuming Jinja2 is available
    
    def test_init_disable_jinja2(self):
        """Test initialization with Jinja2 disabled."""
        renderer = TemplateRenderer(enable_jinja2=False)
        assert renderer.enable_jinja2 is False
        assert renderer.jinja_env is None
    
    def test_extract_variables_simple(self):
        """Test variable extraction from simple templates."""
        renderer = TemplateRenderer()
        
        template_string = "Hello {name}, welcome to {place}!"
        variables = renderer.extract_variables(template_string)
        assert set(variables) == {"name", "place"}
    
    def test_extract_variables_with_format(self):
        """Test variable extraction with format specifiers."""
        renderer = TemplateRenderer()
        
        template_string = "Value: {value:0.2f}, Count: {count:d}"
        variables = renderer.extract_variables(template_string)
        assert set(variables) == {"value", "count"}
    
    def test_extract_variables_jinja2(self):
        """Test variable extraction from Jinja2 templates."""
        renderer = TemplateRenderer()
        
        template_string = "Hello {{ name }}, you have {{ count | default(0) }} items"
        variables = renderer.extract_variables(template_string)
        assert "name" in variables
        assert "count" in variables
    
    def test_render_simple_substitution(self):
        """Test simple string substitution rendering."""
        renderer = TemplateRenderer(enable_jinja2=False)
        
        template_string = "Hello {name}, welcome to {place}!"
        context = {"name": "Alice", "place": "Wonderland"}
        
        result = renderer._render_string(template_string, context)
        assert result == "Hello Alice, welcome to Wonderland!"
    
    def test_render_simple_substitution_missing_var(self):
        """Test simple substitution with missing variable."""
        renderer = TemplateRenderer(enable_jinja2=False)
        
        template_string = "Hello {name}, welcome to {place}!"
        context = {"name": "Alice"}
        
        with pytest.raises(TemplateError, match="Missing context variable"):
            renderer._render_string(template_string, context)
    
    @pytest.mark.skipif(not hasattr(TemplateRenderer, 'jinja_env'), reason="Jinja2 not available")
    def test_render_jinja2(self):
        """Test Jinja2 rendering."""
        renderer = TemplateRenderer(enable_jinja2=True)
        
        template_string = "Hello {{ name }}, you have {{ items | length }} items"
        context = {"name": "Alice", "items": ["apple", "banana"]}
        
        result = renderer._render_string(template_string, context)
        assert result == "Hello Alice, you have 2 items"
    
    def test_render_prompt_template_success(self):
        """Test successful prompt template rendering."""
        renderer = TemplateRenderer()
        
        template = PromptTemplate(
            name="test_template",
            system_prompt="You are a {role}.",
            user_prompt="Write about {topic}.",
            context_variables=["role", "topic"]
        )
        
        context = {"role": "assistant", "topic": "AI"}
        
        result = renderer.render(template, context)
        
        assert isinstance(result, RenderedPrompt)
        assert result.template_name == "test_template"
        assert result.system_prompt == "You are a assistant."
        assert result.user_prompt == "Write about AI."
        assert result.context_used == context
    
    def test_render_prompt_template_missing_context(self):
        """Test prompt template rendering with missing context."""
        renderer = TemplateRenderer()
        
        template = PromptTemplate(
            name="test_template",
            system_prompt="You are a {role}.",
            user_prompt="Write about {topic}.",
            context_variables=["role", "topic"]
        )
        
        context = {"role": "assistant"}  # Missing 'topic'
        
        with pytest.raises(TemplateError, match="Missing required context variables"):
            renderer.render(template, context)
    
    def test_render_basic_template(self):
        """Test basic template rendering."""
        renderer = TemplateRenderer()
        
        template = LatexTemplate(
            name="test_template",
            content="\\title{title}\\author{author}",
            template_type="latex"
        )
        
        context = {"title": "My Paper", "author": "John Doe"}
        
        result = renderer.render(template, context)
        assert result == "\\title{My Paper}\\author{John Doe}"
    
    def test_validate_rendered_content_success(self):
        """Test successful content validation."""
        renderer = TemplateRenderer()
        
        criteria = ValidationCriteria(
            required_opening="The AI Lab",
            word_count_range=[5, 20],
            must_include_terms=["AI", "research"]
        )
        
        rendered = RenderedPrompt(
            template_name="test",
            system_prompt="System prompt",
            user_prompt="The AI Lab demonstrates AI research capabilities.",
            context_used={}
        )
        
        # Should not raise an exception
        renderer._validate_rendered_content(rendered, criteria)
    
    def test_validate_rendered_content_failure(self):
        """Test content validation failure."""
        renderer = TemplateRenderer()
        
        criteria = ValidationCriteria(
            required_opening="The AI Lab",
            must_include_terms=["AI", "research"]
        )
        
        rendered = RenderedPrompt(
            template_name="test",
            system_prompt="System prompt",
            user_prompt="This is a different opening without required terms.",
            context_used={}
        )
        
        with pytest.raises(ValidationError):
            renderer._validate_rendered_content(rendered, criteria)
    
    def test_test_template(self):
        """Test template testing functionality."""
        renderer = TemplateRenderer()
        
        template_string = "Hello {name}, you have {count} items."
        context = {"name": "Alice", "count": 5}
        
        result = renderer.test_template(template_string, context)
        
        assert result['success'] is True
        assert result['rendered_content'] == "Hello Alice, you have 5 items."
        assert set(result['variables_found']) == {"name", "count"}
        assert set(result['variables_used']) == {"name", "count"}
        assert result['variables_missing'] == []
        assert result['error'] is None
    
    def test_test_template_missing_variables(self):
        """Test template testing with missing variables."""
        renderer = TemplateRenderer()
        
        template_string = "Hello {name}, you have {count} items."
        context = {"name": "Alice"}  # Missing 'count'
        
        result = renderer.test_template(template_string, context)
        
        assert result['success'] is False
        assert result['variables_found'] == ["count", "name"]
        assert result['variables_used'] == ["name"]
        assert result['variables_missing'] == ["count"]
        assert result['error'] is not None


class TestTemplateManager:
    """Test TemplateManager class."""
    
    def test_init_default(self):
        """Test default initialization."""
        # Initialize without loading default templates
        manager = TemplateManager({})
        assert manager.config == {}
        assert isinstance(manager.renderer, TemplateRenderer)
    
    def test_init_with_config(self):
        """Test initialization with configuration."""
        config = {"prompts_file": "custom_prompts.json"}
        
        with patch.object(TemplateManager, 'load_prompt_templates'):
            manager = TemplateManager(config)
            assert manager.config == config
    
    def test_load_prompt_templates_json(self):
        """Test loading prompt templates from JSON file."""
        template_data = {
            "paper_sections": {
                "abstract": {
                    "system_prompt": "You are an expert writer.",
                    "user_prompt": "Write an abstract about {topic}.",
                    "context_variables": ["topic"]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(template_data, f)
            temp_path = f.name
        
        try:
            manager = TemplateManager({})
            manager.load_prompt_templates(temp_path)
            
            assert "abstract" in manager.prompt_templates
            template = manager.prompt_templates["abstract"]
            assert template.name == "abstract"
            assert template.system_prompt == "You are an expert writer."
            assert template.user_prompt == "Write an abstract about {topic}."
            assert template.context_variables == ["topic"]
        finally:
            Path(temp_path).unlink()
    
    def test_load_prompt_templates_file_not_found(self):
        """Test loading templates from non-existent file."""
        manager = TemplateManager({})
        
        with pytest.raises(TemplateError, match="Template file not found"):
            manager.load_prompt_templates("nonexistent.json")
    
    def test_load_prompt_templates_invalid_json(self):
        """Test loading templates from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name
        
        try:
            manager = TemplateManager({})
            with pytest.raises(TemplateError, match="Invalid JSON"):
                manager.load_prompt_templates(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_load_latex_template(self):
        """Test loading LaTeX template from file."""
        latex_content = "\\documentclass{article}\n\\begin{document}\n{content}\n\\end{document}"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(latex_content)
            temp_path = f.name
        
        try:
            manager = TemplateManager({})
            manager.load_latex_template("article", temp_path)
            
            assert "article" in manager.latex_templates
            template = manager.latex_templates["article"]
            assert template.name == "article"
            assert template.content == latex_content
            assert "content" in template.variables
        finally:
            Path(temp_path).unlink()
    
    def test_add_custom_template(self):
        """Test adding custom template."""
        manager = TemplateManager({})
        
        template = PromptTemplate(
            name="custom_template",
            system_prompt="Custom system prompt",
            user_prompt="Custom user prompt"
        )
        
        manager.add_custom_template(template)
        
        assert "custom_template" in manager.prompt_templates
        assert manager.prompt_templates["custom_template"] == template
    
    def test_get_prompt_template(self):
        """Test getting prompt template."""
        manager = TemplateManager({})
        
        template = PromptTemplate(
            name="test_template",
            system_prompt="System",
            user_prompt="User"
        )
        
        manager.prompt_templates["test_template"] = template
        
        result = manager.get_prompt_template("test_template")
        assert result == template
        
        result = manager.get_prompt_template("nonexistent")
        assert result is None
    
    def test_get_latex_template(self):
        """Test getting LaTeX template."""
        manager = TemplateManager({})
        
        template = LatexTemplate(
            name="test_template",
            content="\\documentclass{article}",
            template_type="latex"
        )
        
        manager.latex_templates["test_template"] = template
        
        result = manager.get_latex_template("test_template")
        assert result == template
        
        result = manager.get_latex_template("nonexistent")
        assert result is None
    
    def test_get_template(self):
        """Test getting any template by name."""
        manager = TemplateManager({})
        
        prompt_template = PromptTemplate(
            name="prompt_test",
            system_prompt="System",
            user_prompt="User"
        )
        
        latex_template = LatexTemplate(
            name="latex_test",
            content="\\documentclass{article}",
            template_type="latex"
        )
        
        manager.prompt_templates["prompt_test"] = prompt_template
        manager.latex_templates["latex_test"] = latex_template
        
        assert manager.get_template("prompt_test") == prompt_template
        assert manager.get_template("latex_test") == latex_template
        assert manager.get_template("nonexistent") is None
    
    def test_list_templates(self):
        """Test listing templates."""
        manager = TemplateManager({})
        
        # Clear any loaded templates
        manager.prompt_templates.clear()
        manager.latex_templates.clear()
        manager.custom_templates.clear()
        
        prompt_template = PromptTemplate(name="prompt1", system_prompt="", user_prompt="")
        latex_template = LatexTemplate(name="latex1", content="", template_type="latex")
        
        manager.prompt_templates["prompt1"] = prompt_template
        manager.latex_templates["latex1"] = latex_template
        
        # List all templates
        all_templates = manager.list_templates()
        assert set(all_templates) == {"prompt1", "latex1"}
        
        # List only prompt templates
        prompt_templates = manager.list_templates("prompt")
        assert prompt_templates == ["prompt1"]
        
        # List only LaTeX templates
        latex_templates = manager.list_templates("latex")
        assert latex_templates == ["latex1"]
    
    def test_validate_template_success(self):
        """Test successful template validation."""
        manager = TemplateManager({})
        
        template = PromptTemplate(
            name="valid_template",
            system_prompt="You are a helpful assistant.",
            user_prompt="Write about {topic}.",
            context_variables=["topic"]
        )
        
        manager.prompt_templates["valid_template"] = template
        
        result = manager.validate_template("valid_template")
        
        assert isinstance(result, TemplateValidationResult)
        assert result.is_valid is True
        assert result.template_name == "valid_template"
        assert result.errors == []
    
    def test_validate_template_not_found(self):
        """Test validation of non-existent template."""
        manager = TemplateManager({})
        
        result = manager.validate_template("nonexistent")
        
        assert result.is_valid is False
        assert result.template_name == "nonexistent"
        assert "not found" in result.errors[0]
    
    def test_validate_template_empty_user_prompt(self):
        """Test validation of template with empty user prompt."""
        manager = TemplateManager({})
        
        template = PromptTemplate(
            name="invalid_template",
            system_prompt="System prompt",
            user_prompt="",  # Empty user prompt
            context_variables=[]
        )
        
        manager.prompt_templates["invalid_template"] = template
        
        result = manager.validate_template("invalid_template")
        
        assert result.is_valid is False
        assert "User prompt is empty" in result.errors
    
    def test_render_template_success(self):
        """Test successful template rendering."""
        manager = TemplateManager({})
        
        template = PromptTemplate(
            name="test_template",
            system_prompt="You are a {role}.",
            user_prompt="Write about {topic}.",
            context_variables=["role", "topic"]
        )
        
        manager.prompt_templates["test_template"] = template
        
        context = {"role": "assistant", "topic": "AI"}
        result = manager.render_template("test_template", context)
        
        assert isinstance(result, RenderedPrompt)
        assert result.template_name == "test_template"
        assert result.system_prompt == "You are a assistant."
        assert result.user_prompt == "Write about AI."
    
    def test_render_template_not_found(self):
        """Test rendering non-existent template."""
        manager = TemplateManager({})
        
        with pytest.raises(TemplateError, match="Template 'nonexistent' not found"):
            manager.render_template("nonexistent", {})
    
    def test_get_template_info(self):
        """Test getting template information."""
        manager = TemplateManager({})
        
        template = PromptTemplate(
            name="test_template",
            system_prompt="System",
            user_prompt="User {topic}",
            context_variables=["topic"],
            model_parameters={"temperature": 0.7}
        )
        
        manager.prompt_templates["test_template"] = template
        
        info = manager.get_template_info("test_template")
        
        assert info is not None
        assert info['name'] == "test_template"
        assert info['type'] == "PromptTemplate"
        assert info['context_variables'] == ["topic"]
        assert info['model_parameters'] == {"temperature": 0.7}
    
    def test_get_template_info_not_found(self):
        """Test getting info for non-existent template."""
        manager = TemplateManager({})
        
        info = manager.get_template_info("nonexistent")
        assert info is None
    
    def test_validate_all_templates(self):
        """Test validating all templates."""
        manager = TemplateManager({})
        
        # Clear any loaded templates
        manager.prompt_templates.clear()
        manager.latex_templates.clear()
        manager.custom_templates.clear()
        
        valid_template = PromptTemplate(
            name="valid",
            system_prompt="System",
            user_prompt="User",
            context_variables=[]
        )
        
        invalid_template = PromptTemplate(
            name="invalid",
            system_prompt="System",
            user_prompt="",  # Empty user prompt
            context_variables=[]
        )
        
        manager.prompt_templates["valid"] = valid_template
        manager.prompt_templates["invalid"] = invalid_template
        
        results = manager.validate_all_templates()
        
        assert len(results) == 2
        assert results["valid"].is_valid is True
        assert results["invalid"].is_valid is False
    
    def test_export_templates_json(self):
        """Test exporting templates to JSON."""
        manager = TemplateManager({})
        
        template = PromptTemplate(
            name="test_template",
            system_prompt="System",
            user_prompt="User"
        )
        
        manager.prompt_templates["test_template"] = template
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            manager.export_templates(temp_path, "prompt")
            
            # Verify exported content
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert 'metadata' in data
            assert 'templates' in data
            assert 'prompt' in data['templates']
            assert 'test_template' in data['templates']['prompt']
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__])