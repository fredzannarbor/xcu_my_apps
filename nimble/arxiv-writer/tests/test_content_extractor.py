"""
Tests for content extraction functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.arxiv_writer.core.content_extractor import (
    ContentExtractor,
    ExtractedFigure,
    SFTExample,
    RLExample,
    ExtractionResult
)


class TestContentExtractor:
    """Test cases for ContentExtractor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = ContentExtractor(output_dir=self.temp_dir)
        
        # Sample LaTeX content for testing
        self.sample_latex = """
        \\documentclass{article}
        \\begin{document}
        
        \\section{Introduction}
        This is the introduction section.
        
        \\section{Methodology}
        Our analysis shows that the proposed method is effective.
        The results indicate significant improvements over baseline approaches.
        
        \\begin{figure}
        \\includegraphics{test_image.png}
        \\caption{Test figure showing results}
        \\end{figure}
        
        \\subsection{Case Study}
        Consider the following example to illustrate our approach.
        The problem we address is complex optimization.
        Our method uses gradient descent techniques.
        The results showed 20% improvement in accuracy.
        This demonstrates the effectiveness of our approach.
        
        \\section{Results}
        We found that our approach outperforms existing methods.
        Therefore, we conclude that this method is superior.
        
        \\begin{table}
        \\begin{tabular}{|c|c|}
        \\hline
        Method & Accuracy \\\\
        \\hline
        Baseline & 80% \\\\
        Ours & 95% \\\\
        \\hline
        \\end{tabular}
        \\caption{Comparison results}
        \\end{table}
        
        \\end{document}
        """
        
        # Sample PDF text for testing
        self.sample_pdf_text = """
        INTRODUCTION
        
        This paper presents a novel approach to machine learning.
        
        METHODOLOGY
        
        Our analysis reveals that deep learning models can be improved.
        The evaluation demonstrates significant performance gains.
        We found that attention mechanisms are crucial.
        
        CASE STUDY: IMAGE CLASSIFICATION
        
        Consider the problem of classifying medical images.
        The challenge is to achieve high accuracy with limited data.
        Our approach uses transfer learning techniques.
        Results showed 15% improvement over baseline methods.
        The lesson learned is that pre-training is essential.
        
        CONCLUSION
        
        Therefore, we conclude that our method is effective.
        """
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test ContentExtractor initialization."""
        assert self.extractor.output_dir.exists()
        assert self.extractor.figures_dir.exists()
        assert self.extractor.examples_dir.exists()
        assert len(self.extractor.analysis_patterns) > 0
        assert len(self.extractor.case_study_patterns) > 0
    
    def test_latex_to_markdown_basic_formatting(self):
        """Test basic LaTeX to markdown conversion."""
        latex_text = "\\textbf{bold} and \\textit{italic} and \\texttt{code}"
        result = self.extractor._latex_to_markdown(latex_text)
        
        assert "**bold**" in result
        assert "*italic*" in result
        assert "`code`" in result
    
    def test_latex_to_markdown_headers(self):
        """Test LaTeX header conversion."""
        latex_text = "\\section{Main Section}\\subsection{Sub Section}"
        result = self.extractor._latex_to_markdown(latex_text)
        
        assert "# Main Section" in result
        assert "## Sub Section" in result
    
    def test_convert_latex_tables(self):
        """Test LaTeX table conversion."""
        latex_table = """
        \\begin{tabular}{|c|c|}
        \\hline
        Header1 & Header2 \\\\
        \\hline
        Data1 & Data2 \\\\
        \\end{tabular}
        """
        result = self.extractor._convert_latex_tables(latex_table)
        
        assert "| Header1 | Header2 |" in result
        assert "| Data1 | Data2 |" in result
        assert "|---|---|" in result
    
    def test_convert_latex_lists(self):
        """Test LaTeX list conversion."""
        latex_list = """
        \\begin{itemize}
        \\item First item
        \\item Second item
        \\end{itemize}
        """
        result = self.extractor._convert_latex_lists(latex_list)
        
        assert "- First item" in result
        assert "- Second item" in result
    
    def test_clean_pdf_text_to_markdown(self):
        """Test PDF text cleaning and markdown conversion."""
        result = self.extractor._clean_pdf_text_to_markdown(self.sample_pdf_text)
        
        assert "# INTRODUCTION" in result
        assert "## METHODOLOGY" in result
        assert "### CASE STUDY: IMAGE CLASSIFICATION" in result
    
    def test_extract_figures_from_latex_no_files(self):
        """Test figure extraction from LaTeX when image files don't exist."""
        figures = self.extractor._extract_figures_from_latex(
            self.sample_latex, 
            Path(self.temp_dir)
        )
        
        # Should return empty list since image files don't exist
        assert len(figures) == 0
    
    def test_extract_figures_from_latex_with_files(self):
        """Test figure extraction from LaTeX with existing image files."""
        # Create a dummy image file
        image_path = Path(self.temp_dir) / "test_image.png"
        image_path.write_bytes(b"dummy image data")
        
        figures = self.extractor._extract_figures_from_latex(
            self.sample_latex,
            Path(self.temp_dir)
        )
        
        assert len(figures) == 1
        assert figures[0].caption == "Test figure showing results"
        assert figures[0].figure_type == "image"
        assert Path(figures[0].file_path).exists()
    
    @patch('src.arxiv_writer.core.content_extractor.HAS_PYMUPDF', True)
    @patch('src.arxiv_writer.core.content_extractor.fitz')
    def test_extract_from_pdf_mock(self, mock_fitz):
        """Test PDF extraction with mocked PyMuPDF."""
        # Mock PDF document
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=2)
        mock_page = Mock()
        mock_page.get_text.return_value = self.sample_pdf_text
        mock_page.get_images.return_value = []  # Empty image list
        mock_doc.load_page.return_value = mock_page
        mock_doc.close = Mock()
        mock_fitz.open.return_value = mock_doc
        
        # Create a dummy PDF file
        pdf_path = Path(self.temp_dir) / "test.pdf"
        pdf_path.write_bytes(b"dummy pdf data")
        
        result = self.extractor.extract_from_pdf(pdf_path)
        
        assert isinstance(result, ExtractionResult)
        assert len(result.markdown_content) > 0
        assert "INTRODUCTION" in result.markdown_content
        assert result.extraction_summary["total_pages"] == 2
        mock_doc.close.assert_called_once()
    
    def test_extract_from_pdf_no_pymupdf(self):
        """Test PDF extraction without PyMuPDF raises ImportError."""
        with patch('src.arxiv_writer.core.content_extractor.HAS_PYMUPDF', False):
            pdf_path = Path(self.temp_dir) / "test.pdf"
            pdf_path.write_bytes(b"dummy pdf data")
            
            with pytest.raises(ImportError, match="PyMuPDF is required"):
                self.extractor.extract_from_pdf(pdf_path)
    
    def test_extract_sft_examples(self):
        """Test SFT example extraction."""
        content = """
        Previous context paragraph.
        
        Our analysis shows that the method is effective. The results indicate 
        significant improvements. We found that this approach outperforms others.
        Therefore, we conclude this is the best method.
        
        Next paragraph with conclusion.
        """
        
        figures = [ExtractedFigure("fig_001", "Test figure", "/path/to/fig", figure_type="image")]
        sft_examples = self.extractor._extract_sft_examples(content, figures)
        
        assert len(sft_examples) >= 1
        example = sft_examples[0]
        assert "analysis shows" in example.analysis_passage
        assert example.quality_score > 0
        assert example.section_type in ["methodology", "results", "discussion", "conclusion", "analysis"]
    
    def test_extract_rl_examples(self):
        """Test RL example extraction."""
        content = """
        # Case Study: Machine Learning Application
        
        Consider the following example of applying machine learning to healthcare.
        The problem we address is medical image classification with limited data.
        Our method uses transfer learning techniques to improve accuracy.
        The results showed significant improvements over baseline approaches.
        The lesson learned is that pre-training is crucial for success.
        """
        
        figures = [ExtractedFigure("fig_001", "Test figure", "/path/to/fig", figure_type="image")]
        rl_examples = self.extractor._extract_rl_examples(content, figures)
        
        assert len(rl_examples) >= 1
        example = rl_examples[0]
        assert "Case Study" in example.case_study_title
        assert len(example.problem_description) > 0
        assert len(example.methodology) > 0
    
    def test_determine_section_type(self):
        """Test section type determination."""
        assert self.extractor._determine_section_type("Our method uses algorithms") == "methodology"
        assert self.extractor._determine_section_type("The results show improvement") == "results"
        assert self.extractor._determine_section_type("We discuss the implications") == "discussion"
        assert self.extractor._determine_section_type("In conclusion, we found") == "conclusion"
        assert self.extractor._determine_section_type("General analysis text") == "analysis"
    
    def test_extract_problem_description(self):
        """Test problem description extraction."""
        text = "The main problem is data scarcity. This challenge affects model performance."
        result = self.extractor._extract_problem_description(text)
        
        assert "problem is data scarcity" in result
        assert "challenge affects" in result
    
    def test_extract_methodology(self):
        """Test methodology extraction."""
        text = "Our approach uses deep learning. The method involves training neural networks."
        result = self.extractor._extract_methodology(text)
        
        assert "approach uses" in result
        assert "method involves" in result
    
    def test_extract_results(self):
        """Test results extraction."""
        text = "The results showed 95% accuracy. Our findings demonstrate effectiveness."
        result = self.extractor._extract_results(text)
        
        assert "results showed" in result
        assert "findings demonstrate" in result
    
    def test_extract_lessons_learned(self):
        """Test lessons learned extraction."""
        text = "The key lesson is data quality matters. We learned that preprocessing is crucial."
        result = self.extractor._extract_lessons_learned(text)
        
        assert "lesson is" in result
        assert "learned that" in result
    
    def test_extract_from_latex_full_workflow(self):
        """Test complete LaTeX extraction workflow."""
        # Create a temporary LaTeX file
        latex_file = Path(self.temp_dir) / "test.tex"
        latex_file.write_text(self.sample_latex, encoding='utf-8')
        
        result = self.extractor.extract_from_latex(latex_file)
        
        assert isinstance(result, ExtractionResult)
        assert len(result.markdown_content) > 0
        assert "# Introduction" in result.markdown_content
        assert "# Methodology" in result.markdown_content  # \section becomes #
        assert "## Case Study" in result.markdown_content  # \subsection becomes ##
        assert len(result.sft_examples) > 0
        assert len(result.rl_examples) > 0
        assert result.extraction_summary["source_file"] == str(latex_file)
    
    def test_extract_from_latex_file_not_found(self):
        """Test LaTeX extraction with non-existent file."""
        with pytest.raises(FileNotFoundError):
            self.extractor.extract_from_latex("nonexistent.tex")
    
    def test_save_extraction_result(self):
        """Test saving extraction results to files."""
        # Create sample extraction result
        figures = [ExtractedFigure("fig_001", "Test figure", "/path/to/fig", figure_type="image")]
        sft_examples = [SFTExample(
            "sft_001", "context", "analysis", "conclusion", "results", 0.8, ["fig_001"]
        )]
        rl_examples = [RLExample(
            "rl_001", "Case Study", "problem", "method", "results", "lessons", ["fig_001"]
        )]
        
        result = ExtractionResult(
            markdown_content="# Test Content",
            figures=figures,
            sft_examples=sft_examples,
            rl_examples=rl_examples,
            extraction_summary={"test": "data"}
        )
        
        output_file = self.extractor.save_extraction_result(result, "test_output")
        
        # Check that files were created
        assert Path(output_file).exists()
        assert (self.extractor.examples_dir / "test_output_sft_examples.json").exists()
        assert (self.extractor.examples_dir / "test_output_rl_examples.json").exists()
        assert (self.extractor.output_dir / "test_output_figures.json").exists()
        assert (self.extractor.output_dir / "test_output_summary.json").exists()
        
        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "# Test Content" in content


class TestExtractedFigure:
    """Test cases for ExtractedFigure dataclass."""
    
    def test_extracted_figure_creation(self):
        """Test ExtractedFigure creation and attributes."""
        figure = ExtractedFigure(
            figure_id="fig_001",
            caption="Test caption",
            file_path="/path/to/figure.png",
            page_number=1,
            bbox=(0, 0, 100, 100),
            figure_type="image",
            references=["ref1", "ref2"],
            metadata={"source": "test"}
        )
        
        assert figure.figure_id == "fig_001"
        assert figure.caption == "Test caption"
        assert figure.file_path == "/path/to/figure.png"
        assert figure.page_number == 1
        assert figure.bbox == (0, 0, 100, 100)
        assert figure.figure_type == "image"
        assert figure.references == ["ref1", "ref2"]
        assert figure.metadata["source"] == "test"


class TestSFTExample:
    """Test cases for SFTExample dataclass."""
    
    def test_sft_example_creation(self):
        """Test SFTExample creation and attributes."""
        example = SFTExample(
            example_id="sft_001",
            context="Previous context",
            analysis_passage="Analysis content",
            conclusion="Conclusion text",
            section_type="results",
            quality_score=0.85,
            figures_referenced=["fig_001"],
            metadata={"source": "test"}
        )
        
        assert example.example_id == "sft_001"
        assert example.context == "Previous context"
        assert example.analysis_passage == "Analysis content"
        assert example.conclusion == "Conclusion text"
        assert example.section_type == "results"
        assert example.quality_score == 0.85
        assert example.figures_referenced == ["fig_001"]
        assert example.metadata["source"] == "test"


class TestRLExample:
    """Test cases for RLExample dataclass."""
    
    def test_rl_example_creation(self):
        """Test RLExample creation and attributes."""
        example = RLExample(
            example_id="rl_001",
            case_study_title="Test Case Study",
            problem_description="Problem description",
            methodology="Method used",
            results="Results obtained",
            lessons_learned="Lessons learned",
            figures_referenced=["fig_001"],
            metadata={"source": "test"}
        )
        
        assert example.example_id == "rl_001"
        assert example.case_study_title == "Test Case Study"
        assert example.problem_description == "Problem description"
        assert example.methodology == "Method used"
        assert example.results == "Results obtained"
        assert example.lessons_learned == "Lessons learned"
        assert example.figures_referenced == ["fig_001"]
        assert example.metadata["source"] == "test"


class TestExtractionResult:
    """Test cases for ExtractionResult dataclass."""
    
    def test_extraction_result_creation(self):
        """Test ExtractionResult creation and attributes."""
        figures = [ExtractedFigure("fig_001", "Test", "/path", figure_type="image")]
        sft_examples = [SFTExample("sft_001", "ctx", "analysis", "concl", "results")]
        rl_examples = [RLExample("rl_001", "title", "prob", "method", "res", "lessons")]
        
        result = ExtractionResult(
            markdown_content="# Test",
            figures=figures,
            sft_examples=sft_examples,
            rl_examples=rl_examples,
            metadata={"test": "data"},
            extraction_summary={"count": 1}
        )
        
        assert result.markdown_content == "# Test"
        assert len(result.figures) == 1
        assert len(result.sft_examples) == 1
        assert len(result.rl_examples) == 1
        assert result.metadata["test"] == "data"
        assert result.extraction_summary["count"] == 1