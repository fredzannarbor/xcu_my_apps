"""
Tests for section generation system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.arxiv_writer.core.section_generator import (
    SectionGenerator,
    create_standard_section_configs,
    validate_section_dependencies
)
from src.arxiv_writer.core.models import Section, SectionConfig, ValidationResult
from src.arxiv_writer.core.exceptions import GenerationError, TemplateError, LLMError
from src.arxiv_writer.llm.models import LLMConfig
from src.arxiv_writer.templates.models import PromptTemplate, RenderedPrompt, ValidationCriteria


class TestSectionGenerator:
    """Test SectionGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.llm_config = LLMConfig(
            provider="openai",
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000
        )
        
        self.mock_template_manager = Mock()
        self.section_generator = SectionGenerator(self.llm_config, self.mock_template_manager)
    
    def test_initialization(self):
        """Test section generator initialization."""
        assert self.section_generator.llm_config == self.llm_config
        assert self.section_generator.template_manager == self.mock_template_manager
    
    @patch('src.arxiv_writer.core.section_generator.call_model_with_prompt')
    def test_generate_section_success(self, mock_llm_call):
        """Test successful section generation."""
        # Setup mocks
        template = PromptTemplate(
            name="test_template",
            system_prompt="You are a helpful assistant.",
            user_prompt="Write about {{topic}}.",
            context_variables=["topic"]
        )
        
        rendered_prompt = RenderedPrompt(
            template_name="test_template",
            system_prompt="You are a helpful assistant.",
            user_prompt="Write about machine learning.",
            context_used={"topic": "machine learning"}
        )
        
        self.mock_template_manager.get_prompt_template.return_value = template
        self.mock_template_manager.render_template.return_value = rendered_prompt
        
        mock_llm_call.return_value = {
            "parsed_content": "This is a test section about machine learning.",
            "raw_content": "This is a test section about machine learning."
        }
        
        # Test section generation
        section_config = SectionConfig(
            name="test_section",
            title="Test Section",
            template_key="test_template",
            min_words=5,
            max_words=20
        )
        
        context = {"topic": "machine learning"}
        
        section = self.section_generator.generate_section(section_config, context)
        
        # Assertions
        assert isinstance(section, Section)
        assert section.name == "test_section"
        assert section.title == "Test Section"
        assert section.content == "This is a test section about machine learning."
        assert section.word_count == 8  # "This is a test section about machine learning."
        assert section.llm_model == "gpt-4"
        assert section.generated_at is not None
        assert section.generation_time > 0
    
    def test_generate_section_template_not_found(self):
        """Test section generation with missing template."""
        self.mock_template_manager.get_prompt_template.return_value = None
        
        section_config = SectionConfig(
            name="test_section",
            title="Test Section",
            template_key="missing_template"
        )
        
        with pytest.raises(GenerationError) as exc_info:
            self.section_generator.generate_section(section_config, {})
        
        assert "Template 'missing_template' not found" in str(exc_info.value)
    
    @patch('src.arxiv_writer.core.section_generator.call_model_with_prompt')
    def test_generate_section_llm_error(self, mock_llm_call):
        """Test section generation with LLM error."""
        # Setup mocks
        template = PromptTemplate(
            name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_variables=[]
        )
        
        rendered_prompt = RenderedPrompt(
            template_name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_used={}
        )
        
        self.mock_template_manager.get_prompt_template.return_value = template
        self.mock_template_manager.render_template.return_value = rendered_prompt
        
        mock_llm_call.side_effect = Exception("LLM API error")
        
        section_config = SectionConfig(
            name="test_section",
            title="Test Section",
            template_key="test_template"
        )
        
        with pytest.raises(GenerationError):
            self.section_generator.generate_section(section_config, {})
    
    @patch('src.arxiv_writer.core.section_generator.call_model_with_prompt')
    def test_generate_section_empty_response(self, mock_llm_call):
        """Test section generation with empty LLM response."""
        # Setup mocks
        template = PromptTemplate(
            name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_variables=[]
        )
        
        rendered_prompt = RenderedPrompt(
            template_name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_used={}
        )
        
        self.mock_template_manager.get_prompt_template.return_value = template
        self.mock_template_manager.render_template.return_value = rendered_prompt
        
        mock_llm_call.return_value = {
            "parsed_content": "",
            "raw_content": ""
        }
        
        section_config = SectionConfig(
            name="test_section",
            title="Test Section",
            template_key="test_template"
        )
        
        with pytest.raises(GenerationError) as exc_info:
            self.section_generator.generate_section(section_config, {})
        
        assert "Empty response from LLM" in str(exc_info.value)
    
    @patch('src.arxiv_writer.core.section_generator.call_model_with_prompt')
    def test_generate_multiple_sections(self, mock_llm_call):
        """Test generating multiple sections."""
        # Setup mocks
        template = PromptTemplate(
            name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_variables=[]
        )
        
        rendered_prompt = RenderedPrompt(
            template_name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_used={}
        )
        
        self.mock_template_manager.get_prompt_template.return_value = template
        self.mock_template_manager.render_template.return_value = rendered_prompt
        
        mock_llm_call.return_value = {
            "parsed_content": "Generated content.",
            "raw_content": "Generated content."
        }
        
        section_configs = [
            SectionConfig(name="section1", title="Section 1", template_key="test_template"),
            SectionConfig(name="section2", title="Section 2", template_key="test_template")
        ]
        
        results = self.section_generator.generate_multiple_sections(section_configs, {})
        
        assert len(results) == 2
        assert "section1" in results
        assert "section2" in results
        assert isinstance(results["section1"], Section)
        assert isinstance(results["section2"], Section)
    
    @patch('src.arxiv_writer.core.section_generator.call_model_with_prompt')
    def test_generate_multiple_sections_with_error(self, mock_llm_call):
        """Test generating multiple sections with one failing."""
        # Setup mocks - first call succeeds, second fails
        template = PromptTemplate(
            name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_variables=[]
        )
        
        rendered_prompt = RenderedPrompt(
            template_name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_used={}
        )
        
        self.mock_template_manager.get_prompt_template.return_value = template
        self.mock_template_manager.render_template.return_value = rendered_prompt
        
        mock_llm_call.side_effect = [
            {"parsed_content": "Generated content.", "raw_content": "Generated content."},
            Exception("LLM error")
        ]
        
        section_configs = [
            SectionConfig(name="section1", title="Section 1", template_key="test_template"),
            SectionConfig(name="section2", title="Section 2", template_key="test_template")
        ]
        
        results = self.section_generator.generate_multiple_sections(
            section_configs, {}, continue_on_error=True
        )
        
        assert len(results) == 2
        assert isinstance(results["section1"], Section)
        assert isinstance(results["section2"], Exception)
    
    def test_validate_content_success(self):
        """Test successful content validation."""
        content = "This is a well-written section with appropriate length and good content quality."
        
        section_config = SectionConfig(
            name="test_section",
            title="Test Section",
            template_key="test_template",
            min_words=5,
            max_words=20
        )
        
        validation_criteria = ValidationCriteria(
            word_count_range=[10, 25],
            must_include_terms=["section"],
            forbidden_terms=["bad"]
        )
        
        result = self.section_generator._validate_content(content, section_config, validation_criteria)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.metrics["word_count"] == 12  # Actual word count
    
    def test_validate_content_too_short(self):
        """Test content validation with too short content."""
        content = "Short."
        
        section_config = SectionConfig(
            name="test_section",
            title="Test Section",
            template_key="test_template",
            min_words=10,
            max_words=100
        )
        
        result = self.section_generator._validate_content(content, section_config, None)
        
        assert result.is_valid is False
        assert any("too short" in error for error in result.errors)
    
    def test_validate_content_forbidden_terms(self):
        """Test content validation with forbidden terms."""
        content = "This content contains bad words that should not be allowed."
        
        section_config = SectionConfig(
            name="test_section",
            title="Test Section",
            template_key="test_template"
        )
        
        validation_criteria = ValidationCriteria(
            forbidden_terms=["bad", "forbidden"]
        )
        
        result = self.section_generator._validate_content(content, section_config, validation_criteria)
        
        assert result.is_valid is False
        assert any("forbidden term" in error for error in result.errors)
    
    def test_validate_content_missing_required_terms(self):
        """Test content validation with missing required terms."""
        content = "This is some content without the required terms."
        
        section_config = SectionConfig(
            name="test_section",
            title="Test Section",
            template_key="test_template"
        )
        
        validation_criteria = ValidationCriteria(
            must_include_terms=["methodology", "results"]
        )
        
        result = self.section_generator._validate_content(content, section_config, validation_criteria)
        
        # Should have warnings for missing terms
        assert len(result.warnings) >= 2
        assert any("methodology" in warning for warning in result.warnings)
        assert any("results" in warning for warning in result.warnings)
    
    def test_validate_section(self):
        """Test section validation."""
        section = Section(
            name="test_section",
            title="Test Section",
            content="This is a test section with good content.",
            word_count=9
        )
        
        criteria = ValidationCriteria(
            word_count_range=[5, 15],
            must_include_terms=["test"]
        )
        
        result = self.section_generator.validate_section(section, criteria)
        
        assert result.is_valid is True
        assert result.metrics["word_count"] == 8  # Actual word count
    
    @patch('src.arxiv_writer.core.section_generator.call_model_with_prompt')
    def test_regenerate_section(self, mock_llm_call):
        """Test section regeneration with feedback."""
        # Setup mocks
        template = PromptTemplate(
            name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_variables=[]
        )
        
        rendered_prompt = RenderedPrompt(
            template_name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_used={}
        )
        
        self.mock_template_manager.get_prompt_template.return_value = template
        self.mock_template_manager.render_template.return_value = rendered_prompt
        
        mock_llm_call.return_value = {
            "parsed_content": "Regenerated content with improvements.",
            "raw_content": "Regenerated content with improvements."
        }
        
        original_section = Section(
            name="test_section",
            title="Test Section",
            content="Original content.",
            word_count=2
        )
        
        section_config = SectionConfig(
            name="test_section",
            title="Test Section",
            template_key="test_template"
        )
        
        new_section = self.section_generator.regenerate_section(
            original_section,
            section_config,
            {},
            feedback="Make it more detailed"
        )
        
        assert new_section.name == "test_section"
        assert new_section.title == "Test Section"
        assert new_section.content == "Regenerated content with improvements."
        assert new_section.word_count == 4
    
    def test_get_section_statistics(self):
        """Test section statistics generation."""
        sections = [
            Section(name="section1", title="Section 1", content="Content one.", word_count=2, generation_time=1.0, llm_model="gpt-4"),
            Section(name="section2", title="Section 2", content="Content two with more words.", word_count=5, generation_time=2.0, llm_model="gpt-4"),
            Section(name="section3", title="Section 3", content="Content three.", word_count=2, generation_time=1.5, llm_model="gpt-3.5")
        ]
        
        stats = self.section_generator.get_section_statistics(sections)
        
        assert stats["total_sections"] == 3
        assert stats["total_words"] == 9
        assert stats["total_generation_time"] == 4.5
        assert stats["average_words_per_section"] == 3.0
        assert stats["average_generation_time"] == 1.5
        assert "gpt-4" in stats["models_used"]
        assert "gpt-3.5" in stats["models_used"]
        assert stats["word_count_stats"]["min"] == 2
        assert stats["word_count_stats"]["max"] == 5
    
    def test_get_section_statistics_empty(self):
        """Test section statistics with empty list."""
        stats = self.section_generator.get_section_statistics([])
        
        assert stats["total_sections"] == 0


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_create_standard_section_configs(self):
        """Test creation of standard section configurations."""
        configs = create_standard_section_configs()
        
        assert len(configs) == 7
        
        # Check that all expected sections are present
        section_names = [config.name for config in configs]
        expected_sections = ["abstract", "introduction", "related_work", "methodology", "results", "discussion", "conclusion"]
        
        for expected in expected_sections:
            assert expected in section_names
        
        # Check that abstract is required and has appropriate word limits
        abstract_config = next(config for config in configs if config.name == "abstract")
        assert abstract_config.required is True
        assert abstract_config.min_words == 100
        assert abstract_config.max_words == 300
        
        # Check dependencies
        methodology_config = next(config for config in configs if config.name == "methodology")
        assert "introduction" in methodology_config.dependencies
    
    def test_validate_section_dependencies_success(self):
        """Test successful dependency validation."""
        configs = [
            SectionConfig(name="intro", title="Introduction", template_key="intro"),
            SectionConfig(name="methods", title="Methods", template_key="methods", dependencies=["intro"]),
            SectionConfig(name="results", title="Results", template_key="results", dependencies=["methods"])
        ]
        
        errors = validate_section_dependencies(configs)
        
        assert len(errors) == 0
    
    def test_validate_section_dependencies_missing(self):
        """Test dependency validation with missing dependencies."""
        configs = [
            SectionConfig(name="intro", title="Introduction", template_key="intro"),
            SectionConfig(name="results", title="Results", template_key="results", dependencies=["methods", "data"])
        ]
        
        errors = validate_section_dependencies(configs)
        
        assert len(errors) == 2
        assert any("methods" in error for error in errors)
        assert any("data" in error for error in errors)
    
    def test_validate_section_dependencies_empty(self):
        """Test dependency validation with empty list."""
        errors = validate_section_dependencies([])
        
        assert len(errors) == 0


class TestSectionConfig:
    """Test SectionConfig model."""
    
    def test_section_config_creation(self):
        """Test section config creation."""
        config = SectionConfig(
            name="test_section",
            title="Test Section",
            template_key="test_template",
            required=True,
            min_words=100,
            max_words=500,
            dependencies=["intro"]
        )
        
        assert config.name == "test_section"
        assert config.title == "Test Section"
        assert config.template_key == "test_template"
        assert config.required is True
        assert config.min_words == 100
        assert config.max_words == 500
        assert config.dependencies == ["intro"]
    
    def test_section_config_defaults(self):
        """Test section config default values."""
        config = SectionConfig(
            name="test_section",
            title="Test Section",
            template_key="test_template"
        )
        
        assert config.required is True
        assert config.min_words == 50
        assert config.max_words == 5000
        assert config.dependencies == []


if __name__ == "__main__":
    pytest.main([__file__])