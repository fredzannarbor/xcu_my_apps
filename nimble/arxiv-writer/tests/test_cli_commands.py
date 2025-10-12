"""
Unit tests for CLI commands and utilities.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from src.arxiv_writer.cli.main import cli, generate, validate, template
from src.arxiv_writer.utils.cli_utils import (
    load_context_data,
    validate_output_directory,
    setup_logging,
    format_validation_results,
    print_generation_summary
)


class TestCLICommands:
    """Test cases for CLI command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cli_main_command(self):
        """Test main CLI command."""
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'ArXiv Writer' in result.output or 'Usage:' in result.output
    
    @patch('src.arxiv_writer.cli.main.ArxivPaperGenerator')
    def test_generate_command_basic(self, mock_generator_class):
        """Test basic generate command."""
        # Mock the generator
        mock_generator = Mock()
        mock_generator.generate_paper.return_value = Mock(
            success=True,
            output_files=['paper.tex', 'paper.pdf'],
            generation_summary={'sections': 5, 'total_words': 5000}
        )
        mock_generator_class.return_value = mock_generator
        
        # Create test context file
        context_file = Path(self.temp_dir) / "context.json"
        context_data = {"title": "Test Paper", "abstract": "Test abstract"}
        context_file.write_text(json.dumps(context_data))
        
        result = self.runner.invoke(generate, [
            '--context', str(context_file),
            '--output', self.temp_dir
        ])
        
        assert result.exit_code == 0
        mock_generator_class.assert_called_once()
        mock_generator.generate_paper.assert_called_once()
    
    @patch('src.arxiv_writer.cli.main.ArxivPaperGenerator')
    def test_generate_command_with_pdf_compilation(self, mock_generator_class):
        """Test generate command with PDF compilation."""
        # Mock the generator
        mock_generator = Mock()
        mock_generator.generate_paper.return_value = Mock(
            success=True,
            output_files=['paper.tex', 'paper.pdf'],
            generation_summary={'sections': 5, 'total_words': 5000}
        )
        mock_generator_class.return_value = mock_generator
        
        # Create test context file
        context_file = Path(self.temp_dir) / "context.json"
        context_data = {"title": "Test Paper", "abstract": "Test abstract"}
        context_file.write_text(json.dumps(context_data))
        
        result = self.runner.invoke(generate, [
            '--context', str(context_file),
            '--output', self.temp_dir,
            '--compile-pdf'
        ])
        
        assert result.exit_code == 0
        # Verify that compile_pdf=True was passed
        call_args = mock_generator.generate_paper.call_args
        assert call_args[1]['compile_pdf'] is True
    
    def test_generate_command_missing_context(self):
        """Test generate command with missing context file."""
        result = self.runner.invoke(generate, [
            '--context', '/nonexistent/context.json',
            '--output', self.temp_dir
        ])
        
        assert result.exit_code != 0
        assert 'error' in result.output.lower() or 'not found' in result.output.lower()
    
    def test_generate_command_invalid_context(self):
        """Test generate command with invalid context file."""
        # Create invalid JSON file
        context_file = Path(self.temp_dir) / "invalid.json"
        context_file.write_text("{ invalid json content")
        
        result = self.runner.invoke(generate, [
            '--context', str(context_file),
            '--output', self.temp_dir
        ])
        
        assert result.exit_code != 0
    
    @patch('src.arxiv_writer.cli.main.ArxivValidator')
    def test_validate_command_basic(self, mock_validator_class):
        """Test basic validate command."""
        # Mock the validator
        mock_validator = Mock()
        mock_validator.validate.return_value = {
            'valid': True,
            'errors': [],
            'warnings': ['Minor formatting issue'],
            'summary': 'Validation passed with warnings'
        }
        mock_validator_class.return_value = mock_validator
        
        # Create test LaTeX directory
        latex_dir = Path(self.temp_dir) / "latex"
        latex_dir.mkdir()
        main_tex = latex_dir / "main.tex"
        main_tex.write_text(r"\documentclass{article}\begin{document}Test\end{document}")
        
        result = self.runner.invoke(validate, ['--latex-dir', str(latex_dir)])
        
        assert result.exit_code == 0
        mock_validator_class.assert_called_once_with(str(latex_dir))
        mock_validator.validate.assert_called_once()
    
    @patch('src.arxiv_writer.cli.main.ArxivValidator')
    def test_validate_command_with_errors(self, mock_validator_class):
        """Test validate command with validation errors."""
        # Mock the validator with errors
        mock_validator = Mock()
        mock_validator.validate.return_value = {
            'valid': False,
            'errors': ['Missing required file', 'Invalid LaTeX syntax'],
            'warnings': [],
            'summary': 'Validation failed'
        }
        mock_validator_class.return_value = mock_validator
        
        latex_dir = Path(self.temp_dir) / "latex"
        latex_dir.mkdir()
        
        result = self.runner.invoke(validate, ['--latex-dir', str(latex_dir)])
        
        # Should still exit successfully but show errors
        assert result.exit_code == 0
        assert 'error' in result.output.lower() or 'failed' in result.output.lower()
    
    def test_validate_command_missing_directory(self):
        """Test validate command with missing LaTeX directory."""
        result = self.runner.invoke(validate, ['--latex-dir', '/nonexistent/directory'])
        
        assert result.exit_code != 0
    
    @patch('src.arxiv_writer.cli.main.TemplateManager')
    def test_template_list_command(self, mock_template_manager_class):
        """Test template list command."""
        # Mock the template manager
        mock_manager = Mock()
        mock_manager.list_templates.return_value = {
            'template1': {'type': 'prompt', 'description': 'Test template 1'},
            'template2': {'type': 'latex', 'description': 'Test template 2'}
        }
        mock_template_manager_class.return_value = mock_manager
        
        result = self.runner.invoke(template, ['list'])
        
        assert result.exit_code == 0
        assert 'template1' in result.output
        assert 'template2' in result.output
        mock_manager.list_templates.assert_called_once()
    
    @patch('src.arxiv_writer.cli.main.TemplateManager')
    def test_template_validate_command(self, mock_template_manager_class):
        """Test template validate command."""
        # Mock the template manager
        mock_manager = Mock()
        mock_manager.validate_template.return_value = Mock(
            is_valid=True,
            errors=[],
            warnings=['Minor issue'],
            summary='Template is valid'
        )
        mock_template_manager_class.return_value = mock_manager
        
        result = self.runner.invoke(template, ['validate', 'test_template'])
        
        assert result.exit_code == 0
        mock_manager.validate_template.assert_called_once_with('test_template')
    
    def test_cli_global_options(self):
        """Test CLI global options like verbose and quiet."""
        # Test verbose option
        result = self.runner.invoke(cli, ['--verbose', '--help'])
        assert result.exit_code == 0
        
        # Test quiet option
        result = self.runner.invoke(cli, ['--quiet', '--help'])
        assert result.exit_code == 0
    
    def test_cli_version_option(self):
        """Test CLI version option."""
        result = self.runner.invoke(cli, ['--version'])
        
        # Should show version information
        assert result.exit_code == 0
        # Version output typically contains version number or package name


class TestCLIUtilities:
    """Test cases for CLI utility functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_context_data_json(self):
        """Test loading context data from JSON file."""
        context_data = {
            "title": "Test Paper",
            "abstract": "This is a test abstract",
            "keywords": ["test", "paper", "research"]
        }
        
        context_file = Path(self.temp_dir) / "context.json"
        context_file.write_text(json.dumps(context_data))
        
        loaded_data = load_context_data(str(context_file))
        
        assert loaded_data == context_data
    
    def test_load_context_data_invalid_json(self):
        """Test loading context data from invalid JSON file."""
        context_file = Path(self.temp_dir) / "invalid.json"
        context_file.write_text("{ invalid json")
        
        with pytest.raises(Exception):  # Should raise JSON decode error
            load_context_data(str(context_file))
    
    def test_load_context_data_nonexistent_file(self):
        """Test loading context data from non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_context_data("/nonexistent/file.json")
    
    def test_validate_output_directory_existing(self):
        """Test validating existing output directory."""
        # Should not raise exception for existing directory
        validate_output_directory(self.temp_dir)
    
    def test_validate_output_directory_nonexistent(self):
        """Test validating non-existent output directory."""
        nonexistent_dir = Path(self.temp_dir) / "nonexistent"
        
        # Should create the directory
        validate_output_directory(str(nonexistent_dir))
        assert nonexistent_dir.exists()
        assert nonexistent_dir.is_dir()
    
    def test_validate_output_directory_file_exists(self):
        """Test validating output directory when file exists with same name."""
        # Create a file with the target directory name
        file_path = Path(self.temp_dir) / "test_file"
        file_path.write_text("test content")
        
        with pytest.raises(Exception):  # Should raise error
            validate_output_directory(str(file_path))
    
    @patch('logging.basicConfig')
    def test_setup_logging_verbose(self, mock_basic_config):
        """Test setting up logging in verbose mode."""
        setup_logging(verbose=True, quiet=False)
        
        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args
        assert call_args[1]['level'] == 10  # DEBUG level
    
    @patch('logging.basicConfig')
    def test_setup_logging_quiet(self, mock_basic_config):
        """Test setting up logging in quiet mode."""
        setup_logging(verbose=False, quiet=True)
        
        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args
        assert call_args[1]['level'] == 40  # ERROR level
    
    @patch('logging.basicConfig')
    def test_setup_logging_normal(self, mock_basic_config):
        """Test setting up logging in normal mode."""
        setup_logging(verbose=False, quiet=False)
        
        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args
        assert call_args[1]['level'] == 20  # INFO level
    
    def test_format_validation_results_success(self):
        """Test formatting successful validation results."""
        results = {
            'valid': True,
            'errors': [],
            'warnings': ['Minor formatting issue'],
            'summary': 'Validation passed with warnings'
        }
        
        formatted = format_validation_results(results)
        
        assert 'success' in formatted.lower() or 'passed' in formatted.lower()
        assert 'warning' in formatted.lower()
        assert 'Minor formatting issue' in formatted
    
    def test_format_validation_results_failure(self):
        """Test formatting failed validation results."""
        results = {
            'valid': False,
            'errors': ['Missing required file', 'Invalid syntax'],
            'warnings': ['Minor issue'],
            'summary': 'Validation failed'
        }
        
        formatted = format_validation_results(results)
        
        assert 'error' in formatted.lower() or 'failed' in formatted.lower()
        assert 'Missing required file' in formatted
        assert 'Invalid syntax' in formatted
        assert 'Minor issue' in formatted
    
    def test_format_validation_results_empty(self):
        """Test formatting empty validation results."""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'summary': 'All checks passed'
        }
        
        formatted = format_validation_results(results)
        
        assert 'passed' in formatted.lower() or 'success' in formatted.lower()
        assert len(formatted) > 0
    
    def test_print_generation_summary(self):
        """Test printing generation summary."""
        summary = {
            'sections_generated': 5,
            'total_words': 5000,
            'generation_time': 120.5,
            'output_files': ['paper.tex', 'paper.pdf'],
            'success': True
        }
        
        # Capture output
        with patch('builtins.print') as mock_print:
            print_generation_summary(summary)
            
            # Should have printed multiple lines
            assert mock_print.call_count > 0
            
            # Check that key information was printed
            printed_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
            assert '5' in printed_text  # sections
            assert '5000' in printed_text  # words
            assert '120.5' in printed_text or '2:00' in printed_text  # time
    
    def test_print_generation_summary_failure(self):
        """Test printing generation summary for failed generation."""
        summary = {
            'success': False,
            'error': 'Generation failed due to invalid template',
            'sections_generated': 2,
            'total_words': 1000
        }
        
        with patch('builtins.print') as mock_print:
            print_generation_summary(summary)
            
            printed_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
            assert 'failed' in printed_text.lower() or 'error' in printed_text.lower()
            assert 'invalid template' in printed_text.lower()


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.arxiv_writer.cli.main.ArxivPaperGenerator')
    def test_end_to_end_generation_workflow(self, mock_generator_class):
        """Test complete end-to-end generation workflow."""
        # Set up mock generator
        mock_generator = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.output_files = [
            str(Path(self.temp_dir) / "paper.tex"),
            str(Path(self.temp_dir) / "paper.pdf")
        ]
        mock_result.generation_summary = {
            'sections_generated': 6,
            'total_words': 8500,
            'generation_time': 180.0,
            'llm_calls': 12,
            'total_tokens': 25000
        }
        mock_generator.generate_paper.return_value = mock_result
        mock_generator_class.return_value = mock_generator
        
        # Create comprehensive context data
        context_data = {
            "title": "Advanced Machine Learning Techniques",
            "abstract": "This paper explores advanced machine learning techniques...",
            "keywords": ["machine learning", "neural networks", "deep learning"],
            "authors": [
                {"name": "John Doe", "affiliation": "University of Example"},
                {"name": "Jane Smith", "affiliation": "Tech Institute"}
            ],
            "sections": {
                "introduction": "Introduction content...",
                "methodology": "Methodology content...",
                "results": "Results content...",
                "conclusion": "Conclusion content..."
            },
            "references": [
                {"title": "Reference 1", "authors": ["Author 1"], "year": 2023},
                {"title": "Reference 2", "authors": ["Author 2"], "year": 2022}
            ]
        }
        
        context_file = Path(self.temp_dir) / "context.json"
        context_file.write_text(json.dumps(context_data, indent=2))
        
        # Run the complete workflow
        result = self.runner.invoke(generate, [
            '--context', str(context_file),
            '--output', self.temp_dir,
            '--compile-pdf',
            '--verbose'
        ])
        
        assert result.exit_code == 0
        
        # Verify generator was called with correct parameters
        mock_generator_class.assert_called_once()
        mock_generator.generate_paper.assert_called_once()
        
        call_args = mock_generator.generate_paper.call_args
        assert call_args[1]['context_data'] == context_data
        assert call_args[1]['output_dir'] == self.temp_dir
        assert call_args[1]['compile_pdf'] is True
    
    def test_error_handling_and_user_feedback(self):
        """Test error handling and user feedback in CLI."""
        # Test various error scenarios
        error_scenarios = [
            # Missing context file
            {
                'args': ['--context', '/nonexistent.json', '--output', self.temp_dir],
                'expected_error': 'not found'
            },
            # Invalid output directory (file exists with same name)
            {
                'setup': lambda: Path(self.temp_dir, 'output_file').write_text('test'),
                'args': ['--context', 'test.json', '--output', str(Path(self.temp_dir, 'output_file'))],
                'expected_error': 'directory'
            }
        ]
        
        for scenario in error_scenarios:
            # Set up scenario if needed
            if 'setup' in scenario:
                scenario['setup']()
            
            result = self.runner.invoke(generate, scenario['args'])
            
            assert result.exit_code != 0
            assert scenario['expected_error'].lower() in result.output.lower()
    
    @patch('src.arxiv_writer.cli.main.TemplateManager')
    def test_template_management_workflow(self, mock_template_manager_class):
        """Test template management workflow."""
        # Mock template manager
        mock_manager = Mock()
        mock_template_manager_class.return_value = mock_manager
        
        # Test listing templates
        mock_manager.list_templates.return_value = {
            'academic_paper': {
                'type': 'prompt',
                'description': 'Standard academic paper template',
                'variables': ['title', 'abstract', 'sections']
            },
            'arxiv_format': {
                'type': 'latex',
                'description': 'ArXiv-compatible LaTeX template',
                'variables': ['documentclass', 'packages']
            }
        }
        
        result = self.runner.invoke(template, ['list'])
        assert result.exit_code == 0
        assert 'academic_paper' in result.output
        assert 'arxiv_format' in result.output
        
        # Test validating a template
        mock_manager.validate_template.return_value = Mock(
            is_valid=True,
            errors=[],
            warnings=['Consider adding more context variables'],
            summary='Template validation passed'
        )
        
        result = self.runner.invoke(template, ['validate', 'academic_paper'])
        assert result.exit_code == 0
        assert 'passed' in result.output.lower() or 'valid' in result.output.lower()
    
    def test_cli_help_and_documentation(self):
        """Test CLI help and documentation."""
        # Test main help
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        
        # Test subcommand help
        result = self.runner.invoke(generate, ['--help'])
        assert result.exit_code == 0
        assert 'context' in result.output.lower()
        assert 'output' in result.output.lower()
        
        result = self.runner.invoke(validate, ['--help'])
        assert result.exit_code == 0
        assert 'latex' in result.output.lower()
        
        result = self.runner.invoke(template, ['--help'])
        assert result.exit_code == 0
        assert 'list' in result.output.lower() or 'validate' in result.output.lower()