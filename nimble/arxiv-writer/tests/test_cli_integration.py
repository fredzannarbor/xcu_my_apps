"""
Integration tests for CLI interface.
"""

import pytest
import json
import tempfile
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from src.arxiv_writer.cli.main import cli
from src.arxiv_writer.core.models import PaperConfig, LLMConfig, ValidationConfig, TemplateConfig
from src.arxiv_writer.core.exceptions import ArxivWriterError


class TestCLIIntegration:
    """Test CLI integration functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def create_test_config(self) -> Path:
        """Create a test configuration file."""
        config_data = {
            "output_directory": "test_output",
            "llm": {
                "default_model": "anthropic/claude-3-5-sonnet-20241022",
                "available_models": ["anthropic/claude-3-5-sonnet-20241022"],
                "model_parameters": {}
            },
            "templates": {
                "prompts_file": "templates/default_prompts.json",
                "section_order": ["abstract", "introduction", "conclusion"]
            },
            "validation": {
                "enabled": True,
                "strict_mode": False
            }
        }
        
        config_file = self.temp_path / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        return config_file
    
    def create_test_context(self) -> Path:
        """Create a test context file."""
        context_data = {
            "title": "Test Paper",
            "authors": ["Test Author"],
            "abstract": "Test abstract content",
            "sections": {
                "introduction": "Test introduction content",
                "methodology": "Test methodology content"
            }
        }
        
        context_file = self.temp_path / "test_context.json"
        with open(context_file, 'w') as f:
            json.dump(context_data, f, indent=2)
        
        return context_file
    
    def create_test_paper(self) -> Path:
        """Create a test paper file."""
        paper_content = """
        # Test Paper
        
        ## Abstract
        This is a test abstract with sufficient content for validation.
        
        ## Introduction
        This is the introduction section with detailed content.
        
        ## Methodology
        This section describes the methodology used in the research.
        
        ## Results
        This section presents the results of the study.
        
        ## Conclusion
        This section concludes the paper with final thoughts.
        """
        
        paper_file = self.temp_path / "test_paper.md"
        with open(paper_file, 'w') as f:
            f.write(paper_content)
        
        return paper_file
    
    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "ArXiv Writer" in result.output
        assert "generate" in result.output
        assert "validate" in result.output
    
    def test_cli_verbose_flag(self):
        """Test CLI verbose flag."""
        result = self.runner.invoke(cli, ['--verbose', '--help'])
        assert result.exit_code == 0
    
    @patch('src.arxiv_writer.core.generator.ArxivPaperGenerator')
    def test_generate_command(self, mock_generator):
        """Test paper generation command."""
        # Setup mocks
        mock_result = MagicMock()
        mock_result.output_path = "test_output/paper.tex"
        mock_result.pdf_path = "test_output/paper.pdf"
        
        mock_instance = MagicMock()
        mock_instance.generate_paper.return_value = mock_result
        mock_generator.return_value = mock_instance
        
        # Create test files
        config_file = self.create_test_config()
        context_file = self.create_test_context()
        
        # Run command
        result = self.runner.invoke(cli, [
            '--config', str(config_file),
            'generate',
            '--context', str(context_file),
            '--output', str(self.temp_path / 'output')
        ])
        
        assert result.exit_code == 0
        assert "Paper generated successfully" in result.output
        assert mock_generator.called
        assert mock_instance.generate_paper.called
    
    @patch('src.arxiv_writer.core.generator.ArxivPaperGenerator')
    def test_generate_section_command(self, mock_generator):
        """Test section generation command."""
        # Setup mocks
        mock_result = MagicMock()
        mock_result.content = "Test section content"
        mock_result.word_count = 100
        mock_result.model_used = "test-model"
        
        mock_instance = MagicMock()
        mock_instance.generate_section.return_value = mock_result
        mock_generator.return_value = mock_instance
        
        # Create test files
        config_file = self.create_test_config()
        context_file = self.create_test_context()
        
        # Run command
        result = self.runner.invoke(cli, [
            '--config', str(config_file),
            'generate-section', 'introduction',
            '--context', str(context_file),
            '--output', str(self.temp_path / 'output')
        ])
        
        assert result.exit_code == 0
        assert "Section 'introduction' generated successfully" in result.output
        assert mock_instance.generate_section.called
    
    def test_validate_command_with_config(self):
        """Test configuration validation command."""
        config_file = self.create_test_config()
        
        with patch('src.arxiv_writer.config.loader.ConfigLoader.load_from_file') as mock_load:
            mock_config = MagicMock()
            mock_config.llm.default_model = "test-model"
            mock_config.output_directory = "test_output"
            mock_load.return_value = mock_config
            
            result = self.runner.invoke(cli, [
                '--config', str(config_file),
                'validate'
            ])
            
            assert result.exit_code == 0
            assert "Configuration loaded and validated successfully" in result.output
    
    def test_validate_command_no_config(self):
        """Test validation command without config file."""
        result = self.runner.invoke(cli, ['validate'])
        
        assert result.exit_code == 1
        assert "No configuration file specified" in result.output
    
    @patch('src.arxiv_writer.core.quality_assessor.PaperQualityAssessor')
    def test_assess_quality_command(self, mock_assessor):
        """Test paper quality assessment command."""
        # Setup mocks
        mock_metrics = MagicMock()
        mock_metrics.overall_score = 8.5
        mock_metrics.readability_score = 8.0
        mock_metrics.technical_depth_score = 9.0
        mock_metrics.academic_tone_score = 8.5
        mock_metrics.structure_score = 8.0
        mock_metrics.citation_score = 7.5
        mock_metrics.arxiv_compliance_score = 9.0
        
        mock_assessment = MagicMock()
        mock_assessment.metrics = mock_metrics
        mock_assessment.issues = []
        mock_assessment.recommendations = ["Consider adding more citations"]
        
        mock_instance = MagicMock()
        mock_instance.assess_paper.return_value = mock_assessment
        mock_assessor.return_value = mock_instance
        
        # Create test paper
        paper_file = self.create_test_paper()
        
        # Run command
        result = self.runner.invoke(cli, [
            'assess-quality', str(paper_file)
        ])
        
        assert result.exit_code == 0
        assert "Quality Assessment" in result.output
        assert "Overall Score: 8.50" in result.output
        assert mock_instance.assess_paper.called
    
    @patch('src.arxiv_writer.core.validator.ContentValidator')
    def test_validate_paper_command(self, mock_validator):
        """Test paper content validation command."""
        # Setup mocks
        mock_result = MagicMock()
        mock_result.is_valid = True
        mock_result.warnings = ["Minor formatting issue"]
        
        mock_instance = MagicMock()
        mock_instance.validate_content.return_value = mock_result
        mock_validator.return_value = mock_instance
        
        # Create test paper
        paper_file = self.create_test_paper()
        
        # Run command
        result = self.runner.invoke(cli, [
            'validate-paper', str(paper_file)
        ])
        
        assert result.exit_code == 0
        assert "passed validation" in result.output
        assert "Warnings:" in result.output
        assert mock_instance.validate_content.called
    
    @patch('src.arxiv_writer.templates.manager.TemplateManager')
    def test_template_list_command(self, mock_manager):
        """Test template list command."""
        # Setup mocks
        mock_templates = {
            "abstract": {"description": "Abstract template", "type": "prompt"},
            "introduction": {"description": "Introduction template", "type": "prompt"}
        }
        
        mock_instance = MagicMock()
        mock_instance.list_available_templates.return_value = mock_templates
        mock_manager.return_value = mock_instance
        
        # Run command
        result = self.runner.invoke(cli, ['template', 'list'])
        
        assert result.exit_code == 0
        assert "Available templates:" in result.output
        assert "abstract" in result.output
        assert "introduction" in result.output
    
    @patch('src.arxiv_writer.templates.manager.TemplateManager')
    def test_template_validate_command(self, mock_manager):
        """Test template validation command."""
        # Setup mocks
        mock_result = MagicMock()
        mock_result.is_valid = True
        mock_result.warnings = []
        
        mock_instance = MagicMock()
        mock_instance.validate_template.return_value = mock_result
        mock_manager.return_value = mock_instance
        
        # Run command
        result = self.runner.invoke(cli, ['template', 'validate', 'abstract'])
        
        assert result.exit_code == 0
        assert "Template 'abstract' is valid" in result.output
        assert mock_instance.validate_template.called
    
    @patch('src.arxiv_writer.templates.manager.TemplateManager')
    def test_template_test_command(self, mock_manager):
        """Test template testing command."""
        # Setup mocks
        mock_rendered = MagicMock()
        mock_rendered.content = "Rendered template content for testing purposes"
        
        mock_instance = MagicMock()
        mock_instance.render_template.return_value = mock_rendered
        mock_manager.return_value = mock_instance
        
        # Run command
        result = self.runner.invoke(cli, ['template', 'test', 'abstract'])
        
        assert result.exit_code == 0
        assert "Template 'abstract' rendered successfully" in result.output
        assert "Rendered content preview:" in result.output
        assert mock_instance.render_template.called
    
    @patch('src.arxiv_writer.core.codexes_factory_adapter.migrate_from_codexes_factory')
    def test_config_migrate_command(self, mock_migrate):
        """Test configuration migration command."""
        # Setup mocks
        mock_config = MagicMock()
        mock_config.llm.default_model = "migrated-model"
        mock_migrate.return_value = mock_config
        
        # Create test files
        codexes_config = self.temp_path / "codexes_config.json"
        with open(codexes_config, 'w') as f:
            json.dump({"test": "config"}, f)
        
        output_config = self.temp_path / "output_config.json"
        
        # Run command
        result = self.runner.invoke(cli, [
            'config', 'migrate',
            str(codexes_config),
            str(output_config)
        ])
        
        assert result.exit_code == 0
        assert "Configuration migrated successfully" in result.output
        assert mock_migrate.called
    
    def test_config_validate_command(self):
        """Test configuration validation command."""
        config_file = self.create_test_config()
        
        with patch('src.arxiv_writer.config.loader.ConfigLoader.load_from_file') as mock_load:
            mock_config = MagicMock()
            mock_config.llm.default_model = "test-model"
            mock_config.output_directory = "test_output"
            mock_config.templates.prompts_file = "templates/test.json"
            mock_load.return_value = mock_config
            
            result = self.runner.invoke(cli, [
                'config', 'validate',
                str(config_file)
            ])
            
            assert result.exit_code == 0
            assert "Configuration" in result.output
            assert "is valid" in result.output
    
    @patch('src.arxiv_writer.core.context_collector.ContextCollector')
    def test_utils_collect_context_command(self, mock_collector):
        """Test context collection utility command."""
        # Setup mocks
        mock_context = {
            "files": ["file1.py", "file2.md"],
            "summary": "Test context data"
        }
        
        mock_instance = MagicMock()
        mock_instance.collect_context.return_value = mock_context
        mock_collector.return_value = mock_instance
        
        # Create test source directory
        source_dir = self.temp_path / "source"
        source_dir.mkdir()
        (source_dir / "test.py").write_text("print('test')")
        
        output_file = self.temp_path / "context.json"
        
        # Run command
        result = self.runner.invoke(cli, [
            'utils', 'collect-context',
            str(source_dir),
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        assert "Context data collected successfully" in result.output
        assert mock_instance.collect_context.called
    
    def test_error_handling(self):
        """Test CLI error handling."""
        # Test with non-existent config file
        result = self.runner.invoke(cli, [
            '--config', 'nonexistent.json',
            'generate',
            '--context', 'nonexistent.json'
        ])
        
        assert result.exit_code == 1
        assert "Error" in result.output
    
    def test_verbose_error_handling(self):
        """Test verbose error handling."""
        # Test with verbose flag for detailed error output
        result = self.runner.invoke(cli, [
            '--verbose',
            '--config', 'nonexistent.json',
            'generate',
            '--context', 'nonexistent.json'
        ])
        
        assert result.exit_code == 1
        assert "Error" in result.output


class TestCLICommands:
    """Test individual CLI command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_cli_groups_exist(self):
        """Test that all CLI command groups exist."""
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "template" in result.output
        assert "config" in result.output
        assert "utils" in result.output
    
    def test_template_subcommands(self):
        """Test template subcommands exist."""
        result = self.runner.invoke(cli, ['template', '--help'])
        
        assert result.exit_code == 0
        assert "list" in result.output
        assert "validate" in result.output
        assert "test" in result.output
    
    def test_config_subcommands(self):
        """Test config subcommands exist."""
        result = self.runner.invoke(cli, ['config', '--help'])
        
        assert result.exit_code == 0
        assert "migrate" in result.output
        assert "validate" in result.output
    
    def test_utils_subcommands(self):
        """Test utils subcommands exist."""
        result = self.runner.invoke(cli, ['utils', '--help'])
        
        assert result.exit_code == 0
        assert "collect-context" in result.output
    
    def test_main_commands(self):
        """Test main commands exist."""
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "generate" in result.output
        assert "generate-section" in result.output
        assert "validate" in result.output
        assert "assess-quality" in result.output
        assert "validate-paper" in result.output


if __name__ == '__main__':
    pytest.main([__file__])