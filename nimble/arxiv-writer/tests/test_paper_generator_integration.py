"""
Integration tests for the complete paper generation workflow.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.arxiv_writer.core.generator import ArxivPaperGenerator
from src.arxiv_writer.core.models import PaperConfig, LLMConfig, TemplateConfig, OutputConfig, ValidationConfig, SectionConfig
from src.arxiv_writer.core.context_collector import ContextCollector, ContextConfig
from src.arxiv_writer.templates.models import PromptTemplate, RenderedPrompt


class TestArxivPaperGeneratorIntegration:
    """Integration tests for ArxivPaperGenerator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = PaperConfig(
            llm=LLMConfig(
                provider="openai",
                model="gpt-4",
                temperature=0.7
            ),
            templates=TemplateConfig(
                prompts_file="templates/default_prompts.json"
            ),
            output=OutputConfig(
                format="markdown",
                output_dir="test_output"
            ),
            validation=ValidationConfig(
                enabled=True,
                min_word_count=100,
                max_word_count=10000
            ),
            paper_title="Test Paper",
            authors=["Test Author"],
            keywords=["test", "paper"]
        )
    
    @patch('src.arxiv_writer.core.section_generator.call_model_with_prompt')
    def test_complete_paper_generation_workflow(self, mock_llm_call):
        """Test complete paper generation workflow."""
        # Setup mocks
        mock_llm_call.return_value = {
            "parsed_content": "This is a generated section with sufficient content to meet minimum requirements.",
            "raw_content": "This is a generated section with sufficient content to meet minimum requirements."
        }
        
        # Create generator
        generator = ArxivPaperGenerator(self.config)
        
        # Mock template manager to return templates
        mock_template = PromptTemplate(
            name="test_template",
            system_prompt="You are a helpful assistant.",
            user_prompt="Write a section about {{topic}}.",
            context_variables=["topic"]
        )
        
        generator.template_manager.get_prompt_template = Mock(return_value=mock_template)
        generator.template_manager.render_template = Mock(return_value=RenderedPrompt(
            template_name="test_template",
            system_prompt="You are a helpful assistant.",
            user_prompt="Write a section about the topic.",
            context_used={"topic": "test"}
        ))
        
        # Create test context
        context_data = {"topic": "machine learning", "domain": "artificial intelligence"}
        
        # Create simple section configs
        section_configs = [
            SectionConfig(name="abstract", title="Abstract", template_key="abstract", min_words=10, max_words=100),
            SectionConfig(name="introduction", title="Introduction", template_key="introduction", min_words=10, max_words=200)
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate paper
            result = generator.generate_paper(
                context_data=context_data,
                section_configs=section_configs,
                output_dir=temp_dir
            )
            
            # Assertions
            assert result.success is True
            assert result.output_path is not None
            assert Path(result.output_path).exists()
            assert result.word_count > 0
            assert result.generation_time > 0
            assert len(result.sections_generated) == 2
            assert "abstract" in result.sections_generated
            assert "introduction" in result.sections_generated
            
            # Check that file was created
            output_file = Path(result.output_path)
            assert output_file.exists()
            
            # Check file content
            content = output_file.read_text()
            assert "Test Paper" in content
            assert "Test Author" in content
            assert "Abstract" in content
            assert "Introduction" in content
    
    @patch('src.arxiv_writer.core.section_generator.call_model_with_prompt')
    def test_paper_generation_with_context_collection(self, mock_llm_call):
        """Test paper generation with automatic context collection."""
        # Setup mocks
        mock_llm_call.return_value = {
            "parsed_content": "Generated content based on collected context data.",
            "raw_content": "Generated content based on collected context data."
        }
        
        generator = ArxivPaperGenerator(self.config)
        
        # Mock template manager
        mock_template = PromptTemplate(
            name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_variables=[]
        )
        
        generator.template_manager.get_prompt_template = Mock(return_value=mock_template)
        generator.template_manager.render_template = Mock(return_value=RenderedPrompt(
            template_name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_used={}
        ))
        
        # Set up context collector
        context_config = ContextConfig(
            sources=[
                {"name": "test_data", "type": "dict", "data": {"key": "value"}}
            ],
            validation_enabled=False
        )
        context_collector = ContextCollector(context_config)
        generator.set_context_collector(context_collector)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate paper without providing context (should collect automatically)
            result = generator.generate_paper(
                section_configs=[
                    SectionConfig(name="abstract", title="Abstract", template_key="abstract")
                ],
                output_dir=temp_dir
            )
            
            assert result.success is True
            assert result.output_path is not None
    
    @patch('src.arxiv_writer.core.section_generator.call_model_with_prompt')
    def test_single_section_generation(self, mock_llm_call):
        """Test generating a single section."""
        # Setup mocks
        mock_llm_call.return_value = {
            "parsed_content": "This is a single generated section with good content.",
            "raw_content": "This is a single generated section with good content."
        }
        
        generator = ArxivPaperGenerator(self.config)
        
        # Mock template manager
        mock_template = PromptTemplate(
            name="abstract",
            system_prompt="Write an abstract.",
            user_prompt="Write an abstract for {{topic}}.",
            context_variables=["topic"]
        )
        
        generator.template_manager.get_prompt_template = Mock(return_value=mock_template)
        generator.template_manager.render_template = Mock(return_value=RenderedPrompt(
            template_name="abstract",
            system_prompt="Write an abstract.",
            user_prompt="Write an abstract for machine learning.",
            context_used={"topic": "machine learning"}
        ))
        
        # Generate single section
        section_config = SectionConfig(
            name="abstract",
            title="Abstract",
            template_key="abstract"
        )
        
        context_data = {"topic": "machine learning"}
        
        section = generator.generate_section(section_config, context_data)
        
        assert section.name == "abstract"
        assert section.title == "Abstract"
        assert section.content == "This is a single generated section with good content."
        assert section.word_count == 9  # "This is a single generated section with good content."
        assert section.llm_model == "gpt-4"
    
    def test_paper_validation(self):
        """Test paper content validation."""
        generator = ArxivPaperGenerator(self.config)
        
        # Test valid paper (make it longer to meet minimum word count)
        valid_paper = """# Test Paper

## Abstract
This is a comprehensive abstract that provides sufficient detail about the research methodology, findings, and contributions. The abstract summarizes the key aspects of the work and provides readers with a clear understanding of the research scope and outcomes.

## Introduction
This introduction section provides extensive background and context for the research work. It establishes the problem domain, reviews relevant literature, and clearly articulates the research questions and objectives. The introduction sets the foundation for understanding the significance and novelty of the proposed approach.

## Conclusion
This conclusion comprehensively summarizes the findings and contributions of the work. It discusses the implications of the results, acknowledges limitations, and suggests directions for future research. The conclusion reinforces the value and impact of the research contributions.
"""
        
        result = generator.validate_paper(valid_paper)
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.metrics["word_count"] > 0
    
    def test_paper_validation_too_short(self):
        """Test paper validation with content that's too short."""
        generator = ArxivPaperGenerator(self.config)
        
        short_paper = "# Short Paper\n\nThis is too short."
        
        result = generator.validate_paper(short_paper)
        assert result.is_valid is False
        assert any("too short" in error for error in result.errors)
    
    def test_paper_validation_missing_sections(self):
        """Test paper validation with missing required sections."""
        # Update config to require specific sections
        self.config.validation.required_sections = ["abstract", "introduction", "conclusion"]
        generator = ArxivPaperGenerator(self.config)
        
        incomplete_paper = """# Test Paper

## Introduction
This paper has an introduction but is missing other required sections.
""" * 20  # Make it long enough to pass word count
        
        result = generator.validate_paper(incomplete_paper)
        assert result.is_valid is False
        assert any("abstract" in error for error in result.errors)
        assert any("conclusion" in error for error in result.errors)
    
    def test_get_available_templates(self):
        """Test getting available templates."""
        generator = ArxivPaperGenerator(self.config)
        
        # Mock template manager
        generator.template_manager.list_templates = Mock(return_value=["abstract", "introduction", "conclusion"])
        
        templates = generator.get_available_templates()
        assert "abstract" in templates
        assert "introduction" in templates
        assert "conclusion" in templates
    
    def test_get_paper_statistics(self):
        """Test getting paper statistics."""
        generator = ArxivPaperGenerator(self.config)
        
        # Mock template manager
        generator.template_manager.list_templates = Mock(return_value=["template1", "template2"])
        
        stats = generator.get_paper_statistics()
        
        assert stats["llm_model"] == "gpt-4"
        assert stats["llm_provider"] == "openai"
        assert stats["output_format"] == "markdown"
        assert stats["validation_enabled"] is True
        assert stats["available_templates"] == 2
        assert stats["paper_title"] == "Test Paper"
        assert stats["authors_count"] == 1
        assert stats["keywords_count"] == 2
    
    @patch('src.arxiv_writer.core.section_generator.call_model_with_prompt')
    def test_paper_generation_with_failures(self, mock_llm_call):
        """Test paper generation with some section failures."""
        # Setup mocks - first call succeeds, second fails
        mock_llm_call.side_effect = [
            {"parsed_content": "Successful section content.", "raw_content": "Successful section content."},
            Exception("LLM API error")
        ]
        
        generator = ArxivPaperGenerator(self.config)
        
        # Mock template manager
        mock_template = PromptTemplate(
            name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_variables=[]
        )
        
        generator.template_manager.get_prompt_template = Mock(return_value=mock_template)
        generator.template_manager.render_template = Mock(return_value=RenderedPrompt(
            template_name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_used={}
        ))
        
        section_configs = [
            SectionConfig(name="abstract", title="Abstract", template_key="abstract"),
            SectionConfig(name="introduction", title="Introduction", template_key="introduction")
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Should still succeed with partial results
            result = generator.generate_paper(
                context_data={},
                section_configs=section_configs,
                output_dir=temp_dir
            )
            
            assert result.success is True  # Should succeed with at least one section
            # Note: sections_generated includes all attempted sections, but summary shows actual success/failure
            assert result.summary.successful_sections == 1
            assert result.summary.failed_sections == 1
            assert result.summary.successful_sections == 1
            assert result.summary.failed_sections == 1
            assert len(result.summary.errors) == 1
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Test with invalid config
        with pytest.raises(Exception):
            ArxivPaperGenerator("invalid_config")
        
        # Test with missing LLM config
        invalid_config = PaperConfig()
        invalid_config.llm = None
        
        with pytest.raises(Exception):
            ArxivPaperGenerator(invalid_config)
    
    @patch('subprocess.run')
    @patch('src.arxiv_writer.core.section_generator.call_model_with_prompt')
    def test_latex_compilation(self, mock_llm_call, mock_subprocess):
        """Test LaTeX compilation functionality."""
        # Setup mocks
        mock_llm_call.return_value = {
            "parsed_content": "Generated section content for LaTeX compilation test.",
            "raw_content": "Generated section content for LaTeX compilation test."
        }
        
        # Mock successful pdflatex execution
        mock_subprocess.return_value = Mock(returncode=0, stderr="")
        
        # Update config for LaTeX output
        self.config.output.format = "latex"
        generator = ArxivPaperGenerator(self.config)
        
        # Mock template manager
        mock_template = PromptTemplate(
            name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_variables=[]
        )
        
        generator.template_manager.get_prompt_template = Mock(return_value=mock_template)
        generator.template_manager.render_template = Mock(return_value=RenderedPrompt(
            template_name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_used={}
        ))
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock PDF file that would be generated by pdflatex
            temp_path = Path(temp_dir)
            
            def create_pdf_file(*args, **kwargs):
                # Find the LaTeX file and create corresponding PDF
                for file in temp_path.glob("*.tex"):
                    pdf_file = file.with_suffix('.pdf')
                    pdf_file.write_text("Mock PDF content")
                return Mock(returncode=0, stderr="")
            
            mock_subprocess.side_effect = create_pdf_file
            
            result = generator.generate_paper(
                context_data={},
                section_configs=[
                    SectionConfig(name="abstract", title="Abstract", template_key="abstract")
                ],
                output_dir=temp_dir,
                compile_pdf=True
            )
            
            assert result.success is True
            assert result.output_path is not None
            assert result.pdf_path is not None
            
            # Check that LaTeX file was created
            latex_file = Path(result.output_path)
            assert latex_file.exists()
            assert latex_file.suffix == ".tex"
            
            # Check LaTeX content
            latex_content = latex_file.read_text()
            assert "\\documentclass{article}" in latex_content
            assert "\\begin{document}" in latex_content
            assert "\\end{document}" in latex_content


class TestPaperGeneratorErrorHandling:
    """Test error handling in paper generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = PaperConfig(
            llm=LLMConfig(provider="openai", model="gpt-4"),
            templates=TemplateConfig(),
            output=OutputConfig(),
            validation=ValidationConfig()
        )
    
    @patch('src.arxiv_writer.core.section_generator.call_model_with_prompt')
    def test_all_sections_fail(self, mock_llm_call):
        """Test behavior when all sections fail to generate."""
        # All LLM calls fail
        mock_llm_call.side_effect = Exception("LLM API error")
        
        generator = ArxivPaperGenerator(self.config)
        
        # Mock template manager
        mock_template = PromptTemplate(
            name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_variables=[]
        )
        
        generator.template_manager.get_prompt_template = Mock(return_value=mock_template)
        generator.template_manager.render_template = Mock(return_value=RenderedPrompt(
            template_name="test_template",
            system_prompt="System prompt",
            user_prompt="User prompt",
            context_used={}
        ))
        
        section_configs = [
            SectionConfig(name="abstract", title="Abstract", template_key="abstract")
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(Exception):  # Should raise GenerationError
                generator.generate_paper(
                    context_data={},
                    section_configs=section_configs,
                    output_dir=temp_dir
                )
    
    def test_invalid_output_directory(self):
        """Test handling of invalid output directory."""
        generator = ArxivPaperGenerator(self.config)
        
        # Try to write to a file instead of directory
        with tempfile.NamedTemporaryFile() as temp_file:
            with pytest.raises(Exception):
                generator.generate_paper(
                    context_data={},
                    section_configs=[],
                    output_dir=temp_file.name  # This is a file, not a directory
                )


if __name__ == "__main__":
    pytest.main([__file__])