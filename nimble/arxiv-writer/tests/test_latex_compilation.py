"""
Unit tests for LaTeX compilation and PDF generation.
"""

import pytest
import tempfile
import subprocess
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any

from src.arxiv_writer.core.paper_assembler import PDFGenerator, ArxivPaperAssembler
from src.arxiv_writer.core.arxiv_validator import ArxivValidator
from src.arxiv_writer.core.test_framework import TestFramework


class TestPDFGenerator:
    """Test cases for PDF generation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.pdf_generator = PDFGenerator(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_pdf_generator_initialization(self):
        """Test PDFGenerator initialization."""
        assert self.pdf_generator.output_dir == self.temp_dir
        assert hasattr(self.pdf_generator, 'compilation_log')
        assert isinstance(self.pdf_generator.compilation_log, list)
    
    @patch('subprocess.run')
    def test_run_lualatex_success(self, mock_run):
        """Test successful lualatex execution."""
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "LaTeX compilation successful"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.pdf_generator._run_lualatex("test.tex", 1)
        
        assert result['tool'] == 'lualatex'
        assert result['run'] == 1
        assert result['returncode'] == 0
        assert result['stdout'] == "LaTeX compilation successful"
        assert result['stderr'] == ""
        
        mock_run.assert_called_once_with(
            ['lualatex', '-interaction=nonstopmode', '-halt-on-error', 'test.tex'],
            capture_output=True,
            text=True,
            timeout=300
        )
    
    @patch('subprocess.run')
    def test_run_lualatex_failure(self, mock_run):
        """Test failed lualatex execution."""
        # Mock failed subprocess run
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "LaTeX compilation output"
        mock_result.stderr = "Error: Undefined control sequence"
        mock_run.return_value = mock_result
        
        result = self.pdf_generator._run_lualatex("test.tex", 1)
        
        assert result['tool'] == 'lualatex'
        assert result['run'] == 1
        assert result['returncode'] == 1
        assert "Error: Undefined control sequence" in result['stderr']
    
    @patch('subprocess.run')
    def test_run_lualatex_timeout(self, mock_run):
        """Test lualatex execution timeout."""
        # Mock timeout exception
        mock_run.side_effect = subprocess.TimeoutExpired(['lualatex'], 300)
        
        result = self.pdf_generator._run_lualatex("test.tex", 1)
        
        assert result['tool'] == 'lualatex'
        assert result['run'] == 1
        assert result['returncode'] == -1
        assert 'timeout' in result['error'].lower()
    
    @patch('subprocess.run')
    def test_run_lualatex_exception(self, mock_run):
        """Test lualatex execution with general exception."""
        # Mock general exception
        mock_run.side_effect = FileNotFoundError("lualatex command not found")
        
        result = self.pdf_generator._run_lualatex("test.tex", 1)
        
        assert result['tool'] == 'lualatex'
        assert result['run'] == 1
        assert result['returncode'] == -1
        assert 'lualatex command not found' in result['error']
    
    @patch('os.chdir')
    @patch('subprocess.run')
    def test_compile_to_pdf_success(self, mock_run, mock_chdir):
        """Test successful PDF compilation."""
        # Create test LaTeX file
        tex_file = Path(self.temp_dir) / "test.tex"
        tex_file.write_text(r"""
        \documentclass{article}
        \begin{document}
        Test document
        \end{document}
        """)
        
        # Mock successful lualatex runs
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Create mock PDF file
        pdf_file = Path(self.temp_dir) / "test.pdf"
        pdf_file.write_bytes(b"Mock PDF content")
        
        result = self.pdf_generator.compile_to_pdf(str(tex_file))
        
        assert result['success'] is True
        assert result['final_pdf'] == str(pdf_file)
        assert len(result['compilation_log']) >= 2  # At least 2 lualatex runs
        assert mock_run.call_count >= 2
    
    @patch('os.chdir')
    @patch('subprocess.run')
    def test_compile_to_pdf_first_run_failure(self, mock_run, mock_chdir):
        """Test PDF compilation when first lualatex run fails."""
        # Create test LaTeX file
        tex_file = Path(self.temp_dir) / "test.tex"
        tex_file.write_text(r"""
        \documentclass{article}
        \begin{document}
        Test document with error
        \end{document}
        """)
        
        # Mock failed lualatex run
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "LaTeX Error"
        mock_result.stderr = "Compilation failed"
        mock_run.return_value = mock_result
        
        result = self.pdf_generator.compile_to_pdf(str(tex_file))
        
        assert result['success'] is False
        assert "First lualatex run failed" in result['errors']
        assert len(result['compilation_log']) >= 1
    
    @patch('os.chdir')
    @patch('subprocess.run')
    def test_compile_to_pdf_with_bibliography(self, mock_run, mock_chdir):
        """Test PDF compilation with bibliography."""
        # Create test LaTeX file
        tex_file = Path(self.temp_dir) / "test.tex"
        tex_file.write_text(r"""
        \documentclass{article}
        \begin{document}
        Test document \cite{test}
        \bibliography{references}
        \end{document}
        """)
        
        # Create bibliography file
        bib_file = Path(self.temp_dir) / "references.bib"
        bib_file.write_text("@article{test, title={Test}, author={Author}, year={2023}}")
        
        # Mock successful runs
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Create mock PDF file
        pdf_file = Path(self.temp_dir) / "test.pdf"
        pdf_file.write_bytes(b"Mock PDF content")
        
        result = self.pdf_generator.compile_to_pdf(str(tex_file))
        
        assert result['success'] is True
        # Should have multiple lualatex runs + bibtex run
        assert len(result['compilation_log']) >= 3
        
        # Check that bibtex was called
        bibtex_calls = [call for call in mock_run.call_args_list 
                       if 'bibtex' in str(call)]
        assert len(bibtex_calls) >= 1
    
    def test_compile_to_pdf_nonexistent_file(self):
        """Test PDF compilation with non-existent LaTeX file."""
        result = self.pdf_generator.compile_to_pdf("/nonexistent/file.tex")
        
        assert result['success'] is False
        assert "LaTeX file not found" in result['errors']


class TestArxivValidator:
    """Test cases for ArXiv validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.validator = ArxivValidator(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validator_initialization(self):
        """Test ArxivValidator initialization."""
        assert self.validator.latex_dir == Path(self.temp_dir)
        assert hasattr(self.validator, 'results')
        assert isinstance(self.validator.results, list)
    
    @patch('subprocess.run')
    def test_validate_compilation_success(self, mock_run):
        """Test successful compilation validation."""
        # Create main.tex file
        main_tex = Path(self.temp_dir) / "main.tex"
        main_tex.write_text(r"""
        \documentclass{article}
        \begin{document}
        Test document
        \end{document}
        """)
        
        # Mock successful lualatex run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Create mock PDF output
        pdf_file = Path(self.temp_dir) / "main.pdf"
        pdf_file.write_bytes(b"Mock PDF content")
        
        self.validator._validate_compilation()
        
        # Check that a success result was added
        success_results = [r for r in self.validator.results if r['status']]
        assert len(success_results) > 0
        assert any("compiles successfully" in r['message'] for r in success_results)
    
    @patch('subprocess.run')
    def test_validate_compilation_failure(self, mock_run):
        """Test failed compilation validation."""
        # Create main.tex file
        main_tex = Path(self.temp_dir) / "main.tex"
        main_tex.write_text(r"""
        \documentclass{article}
        \begin{document}
        \undefined_command
        \end{document}
        """)
        
        # Mock failed lualatex run
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "LaTeX Error"
        mock_result.stderr = "Undefined control sequence"
        mock_run.return_value = mock_result
        
        self.validator._validate_compilation()
        
        # Check that a failure result was added
        failure_results = [r for r in self.validator.results if not r['status']]
        assert len(failure_results) > 0
        assert any("compilation failed" in r['message'].lower() for r in failure_results)
    
    @patch('subprocess.run')
    def test_validate_compilation_no_latex(self, mock_run):
        """Test compilation validation when LaTeX is not installed."""
        # Create main.tex file
        main_tex = Path(self.temp_dir) / "main.tex"
        main_tex.write_text(r"""
        \documentclass{article}
        \begin{document}
        Test document
        \end{document}
        """)
        
        # Mock FileNotFoundError (LaTeX not found)
        mock_run.side_effect = FileNotFoundError("lualatex command not found")
        
        self.validator._validate_compilation()
        
        # Check that a warning result was added
        warning_results = [r for r in self.validator.results if r['level'] == 'warning']
        assert len(warning_results) > 0
        assert any("compiler not found" in r['message'].lower() for r in warning_results)
    
    def test_validate_compilation_no_main_tex(self):
        """Test compilation validation when main.tex doesn't exist."""
        self.validator._validate_compilation()
        
        # Check that an error result was added
        error_results = [r for r in self.validator.results if not r['status']]
        assert len(error_results) > 0
        assert any("main.tex not found" in r['message'].lower() for r in error_results)
    
    def test_allowed_tex_engines(self):
        """Test that allowed TeX engines are properly defined."""
        assert hasattr(ArxivValidator, 'ALLOWED_TEX_ENGINES')
        engines = ArxivValidator.ALLOWED_TEX_ENGINES
        
        assert 'pdflatex' in engines
        assert 'latex' in engines
        assert 'xelatex' in engines
        assert 'lualatex' in engines


class TestTestFramework:
    """Test cases for LaTeX compilation testing framework."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_framework = TestFramework()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_latex_compilation_test_success(self, mock_run):
        """Test successful LaTeX compilation test."""
        # Create test LaTeX content
        latex_content = r"""
        \documentclass{article}
        \begin{document}
        Test document for compilation
        \end{document}
        """
        
        # Mock successful lualatex run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Mock PDF creation
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            result = self.test_framework.test_latex_compilation(latex_content)
        
        assert result.passed is True
        assert "LaTeX Compilation" in result.test_name
        assert "successfully compiled" in result.message.lower()
    
    @patch('subprocess.run')
    def test_latex_compilation_test_failure(self, mock_run):
        """Test failed LaTeX compilation test."""
        # Create test LaTeX content with error
        latex_content = r"""
        \documentclass{article}
        \begin{document}
        \undefined_command
        \end{document}
        """
        
        # Mock failed lualatex run
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "LaTeX Error"
        mock_result.stderr = "Undefined control sequence"
        mock_run.return_value = mock_result
        
        result = self.test_framework.test_latex_compilation(latex_content)
        
        assert result.passed is False
        assert "LaTeX Compilation" in result.test_name
        assert "compilation failed" in result.message.lower()
    
    @patch('subprocess.run')
    def test_latex_compilation_test_timeout(self, mock_run):
        """Test LaTeX compilation test with timeout."""
        latex_content = r"""
        \documentclass{article}
        \begin{document}
        Test document
        \end{document}
        """
        
        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired(['lualatex'], 30)
        
        result = self.test_framework.test_latex_compilation(latex_content)
        
        assert result.passed is False
        assert "LaTeX Compilation" in result.test_name
        assert "timed out" in result.message.lower()
    
    @patch('subprocess.run')
    def test_latex_compilation_test_no_latex(self, mock_run):
        """Test LaTeX compilation test when LaTeX is not available."""
        latex_content = r"""
        \documentclass{article}
        \begin{document}
        Test document
        \end{document}
        """
        
        # Mock LaTeX not found
        mock_run.side_effect = FileNotFoundError("lualatex command not found")
        
        result = self.test_framework.test_latex_compilation(latex_content)
        
        assert result.passed is False
        assert "LaTeX Compilation" in result.test_name
        assert "compiler not found" in result.message.lower()


class TestLaTeXCompilationIntegration:
    """Integration tests for LaTeX compilation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_compilation_workflow(self):
        """Test complete LaTeX compilation workflow."""
        # Create a complete LaTeX document
        latex_content = r"""
        \documentclass[11pt]{article}
        \usepackage[utf8]{inputenc}
        \usepackage{amsmath}
        \usepackage{graphicx}
        
        \title{Test Paper}
        \author{Test Author}
        \date{\today}
        
        \begin{document}
        
        \maketitle
        
        \begin{abstract}
        This is a test abstract for the paper.
        \end{abstract}
        
        \section{Introduction}
        This is the introduction section with some math: $E = mc^2$.
        
        \section{Methods}
        Here we describe our methods.
        
        \begin{equation}
        \int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
        \end{equation}
        
        \section{Results}
        Our results show interesting findings.
        
        \section{Conclusion}
        In conclusion, this test document compiles successfully.
        
        \end{document}
        """
        
        # Write LaTeX file
        tex_file = Path(self.temp_dir) / "test_paper.tex"
        tex_file.write_text(latex_content)
        
        # Test with PDFGenerator
        pdf_generator = PDFGenerator(self.temp_dir)
        
        with patch('subprocess.run') as mock_run:
            # Mock successful compilation
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "LaTeX compilation successful"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            # Mock PDF creation
            pdf_file = Path(self.temp_dir) / "test_paper.pdf"
            pdf_file.write_bytes(b"Mock PDF content")
            
            result = pdf_generator.compile_to_pdf(str(tex_file))
            
            assert result['success'] is True
            assert result['final_pdf'] == str(pdf_file)
            assert len(result['compilation_log']) >= 2
    
    def test_error_recovery_and_reporting(self):
        """Test error recovery and detailed reporting."""
        # Create LaTeX document with common errors
        latex_with_errors = r"""
        \documentclass{article}
        \begin{document}
        
        \section{Test Section}
        This has an undefined command: \undefinedcommand
        
        And a missing closing brace: \textbf{bold text
        
        \end{document}
        """
        
        tex_file = Path(self.temp_dir) / "error_test.tex"
        tex_file.write_text(latex_with_errors)
        
        pdf_generator = PDFGenerator(self.temp_dir)
        
        with patch('subprocess.run') as mock_run:
            # Mock failed compilation with detailed error output
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = "LaTeX compilation output"
            mock_result.stderr = r"""
            ! Undefined control sequence.
            l.6 This has an undefined command: \undefinedcommand
            
            ! Missing } inserted.
            l.8 And a missing closing brace: \textbf{bold text
            """
            mock_run.return_value = mock_result
            
            result = pdf_generator.compile_to_pdf(str(tex_file))
            
            assert result['success'] is False
            assert len(result['errors']) > 0
            assert len(result['compilation_log']) >= 1
            
            # Check that error details are captured
            log_entry = result['compilation_log'][0]
            assert log_entry['returncode'] == 1
            assert "Undefined control sequence" in log_entry['stderr']
    
    def test_compilation_with_multiple_files(self):
        """Test compilation with multiple LaTeX files."""
        # Create main document
        main_content = r"""
        \documentclass{article}
        \begin{document}
        
        \input{section1}
        \input{section2}
        
        \end{document}
        """
        
        # Create included files
        section1_content = r"""
        \section{First Section}
        This is the first section content.
        """
        
        section2_content = r"""
        \section{Second Section}
        This is the second section content.
        """
        
        # Write all files
        main_file = Path(self.temp_dir) / "main.tex"
        main_file.write_text(main_content)
        
        section1_file = Path(self.temp_dir) / "section1.tex"
        section1_file.write_text(section1_content)
        
        section2_file = Path(self.temp_dir) / "section2.tex"
        section2_file.write_text(section2_content)
        
        pdf_generator = PDFGenerator(self.temp_dir)
        
        with patch('subprocess.run') as mock_run:
            # Mock successful compilation
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Success"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            # Mock PDF creation
            pdf_file = Path(self.temp_dir) / "main.pdf"
            pdf_file.write_bytes(b"Mock PDF content")
            
            result = pdf_generator.compile_to_pdf(str(main_file))
            
            assert result['success'] is True
            assert result['final_pdf'] == str(pdf_file)