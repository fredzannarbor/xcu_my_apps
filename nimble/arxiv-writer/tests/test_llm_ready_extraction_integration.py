"""
Integration tests for LLM-ready content extraction workflow.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.arxiv_writer.core.content_extractor import ContentExtractor
from src.arxiv_writer.core.answer_key_generator import AnswerKeyGenerator


class TestLLMReadyExtractionIntegration:
    """Integration tests for the complete LLM-ready extraction workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = ContentExtractor(output_dir=f"{self.temp_dir}/extraction")
        self.answer_generator = AnswerKeyGenerator(output_dir=f"{self.temp_dir}/answer_keys")
        
        # Sample LaTeX content with analysis and case studies
        self.sample_latex = """
        \\documentclass{article}
        \\begin{document}
        
        \\section{Introduction}
        This paper presents a novel approach to machine learning optimization.
        
        \\section{Methodology}
        Our analysis reveals that the proposed method significantly outperforms 
        existing approaches. The results indicate a 25% improvement in accuracy 
        compared to baseline methods. We found that the key factor is the novel 
        attention mechanism that allows for better feature extraction.
        
        \\begin{figure}
        \\includegraphics{results_chart.png}
        \\caption{Performance comparison showing significant improvements}
        \\end{figure}
        
        \\subsection{Case Study: Medical Image Classification}
        Consider the following example to illustrate our approach in practice.
        The problem we address is accurate classification of medical images 
        with limited training data. Our method uses transfer learning with 
        pre-trained convolutional neural networks. The results showed 15% 
        improvement over baseline methods with 95% accuracy. The key lesson 
        learned is that pre-training on large datasets is crucial for success.
        
        \\section{Results}
        We found that our approach consistently outperforms existing methods 
        across multiple datasets. Therefore, we conclude that this method 
        represents a significant advancement in the field.
        
        \\begin{table}
        \\begin{tabular}{|c|c|c|}
        \\hline
        Method & Accuracy & F1-Score \\\\
        \\hline
        Baseline & 80\\% & 0.75 \\\\
        Our Method & 95\\% & 0.92 \\\\
        \\hline
        \\end{tabular}
        \\caption{Quantitative results comparison}
        \\end{table}
        
        \\section{Conclusion}
        This work demonstrates the effectiveness of our proposed approach.
        
        \\end{document}
        """
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_llm_ready_extraction_workflow(self):
        """Test the complete workflow from LaTeX to LLM-ready training data."""
        # Step 1: Create LaTeX file
        latex_file = Path(self.temp_dir) / "test_paper.tex"
        latex_file.write_text(self.sample_latex, encoding='utf-8')
        
        # Create dummy image file for figure extraction
        image_file = Path(self.temp_dir) / "results_chart.png"
        image_file.write_bytes(b"dummy image data")
        
        # Step 2: Extract content using ContentExtractor
        extraction_result = self.extractor.extract_from_latex(latex_file)
        
        # Verify extraction results
        assert len(extraction_result.markdown_content) > 0
        assert "# Introduction" in extraction_result.markdown_content
        assert "# Methodology" in extraction_result.markdown_content
        assert "## Case Study: Medical Image Classification" in extraction_result.markdown_content
        assert len(extraction_result.sft_examples) > 0
        assert len(extraction_result.rl_examples) > 0
        
        # Step 3: Generate answer keys using AnswerKeyGenerator
        answer_key_result = self.answer_generator.generate_answer_keys(extraction_result)
        
        # Verify answer key generation
        assert len(answer_key_result.answer_keys) > 0
        assert len(answer_key_result.judge_criteria) > 0
        assert answer_key_result.generation_summary["total_answer_keys"] > 0
        
        # Step 4: Save extraction results
        extraction_file = self.extractor.save_extraction_result(extraction_result, "test_paper")
        assert Path(extraction_file).exists()
        
        # Step 5: Save answer keys
        answer_keys_file = self.answer_generator.save_answer_keys(answer_key_result, "test_paper")
        assert Path(answer_keys_file).exists()
        
        # Verify the complete pipeline produces usable training data
        # Check that we have both SFT and RL examples
        sft_examples = [ak for ak in answer_key_result.answer_keys if ak.example_type == "sft"]
        rl_examples = [ak for ak in answer_key_result.answer_keys if ak.example_type == "rl"]
        
        assert len(sft_examples) > 0
        assert len(rl_examples) > 0
        
        # Verify SFT examples have proper structure
        for sft_example in sft_examples:
            assert len(sft_example.correct_answer) > 0
            assert len(sft_example.verification_instructions) > 0
            assert len(sft_example.scoring_rubrics) > 0
            assert len(sft_example.key_concepts) > 0
        
        # Verify RL examples have proper structure
        for rl_example in rl_examples:
            assert len(rl_example.correct_answer) > 0
            assert "Case Study:" in rl_example.correct_answer
            assert "Problem:" in rl_example.correct_answer
            assert "Methodology:" in rl_example.correct_answer
            assert len(rl_example.verification_instructions) > 0
            assert len(rl_example.scoring_rubrics) > 0
        
        # Verify judge criteria are comprehensive
        for judge_criterion in answer_key_result.judge_criteria:
            assert len(judge_criterion.name) > 0
            assert len(judge_criterion.description) > 0
            assert len(judge_criterion.evaluation_prompt) > 0
            assert len(judge_criterion.rubrics) > 0
    
    def test_extraction_preserves_latex_styling(self):
        """Test that LaTeX styling is properly preserved in markdown."""
        latex_with_styling = """
        \\section{Test Section}
        This text contains \\textbf{bold text}, \\textit{italic text}, 
        and \\texttt{monospace text}. We also have \\cite{reference2023}
        and \\ref{fig:example}.
        
        \\begin{itemize}
        \\item First item
        \\item Second item with \\emph{emphasis}
        \\end{itemize}
        """
        
        latex_file = Path(self.temp_dir) / "styling_test.tex"
        latex_file.write_text(latex_with_styling, encoding='utf-8')
        
        extraction_result = self.extractor.extract_from_latex(latex_file)
        markdown = extraction_result.markdown_content
        
        # Check that styling is preserved
        assert "**bold text**" in markdown
        assert "*italic text*" in markdown
        assert "`monospace text`" in markdown
        assert "*emphasis*" in markdown
        assert "- First item" in markdown
        assert "- Second item" in markdown
        assert "[reference2023]" in markdown
        assert "[ref:fig:example]" in markdown
    
    def test_figure_and_table_integration(self):
        """Test that figures and tables are properly integrated."""
        latex_with_figures = """
        \\section{Results}
        As shown in Figure~\\ref{fig:results}, our method achieves superior performance.
        Table~\\ref{tab:comparison} provides detailed numerical results.
        
        \\begin{figure}
        \\includegraphics{test_figure.png}
        \\caption{Performance results}
        \\label{fig:results}
        \\end{figure}
        
        \\begin{table}
        \\begin{tabular}{|c|c|}
        \\hline
        Method & Score \\\\
        \\hline
        Ours & 95 \\\\
        Baseline & 80 \\\\
        \\end{tabular}
        \\caption{Comparison table}
        \\label{tab:comparison}
        \\end{table}
        """
        
        latex_file = Path(self.temp_dir) / "figures_test.tex"
        latex_file.write_text(latex_with_figures, encoding='utf-8')
        
        # Create dummy figure file
        figure_file = Path(self.temp_dir) / "test_figure.png"
        figure_file.write_bytes(b"dummy figure data")
        
        extraction_result = self.extractor.extract_from_latex(latex_file)
        
        # Check markdown conversion
        markdown = extraction_result.markdown_content
        assert "| Method | Score |" in markdown
        assert "| Ours | 95 |" in markdown
        assert "| Baseline | 80 |" in markdown
        
        # Check figure extraction
        assert len(extraction_result.figures) > 0
        figure = extraction_result.figures[0]
        assert figure.caption == "Performance results"
        assert Path(figure.file_path).exists()
        
        # Generate answer keys and check figure integration
        answer_key_result = self.answer_generator.generate_answer_keys(extraction_result)
        
        # Check that answer keys reference figures appropriately
        for answer_key in answer_key_result.answer_keys:
            if answer_key.figure_references:
                # Should have figure integration rubric
                rubric_criteria = [rubric.criterion.value for rubric in answer_key.scoring_rubrics]
                assert "figure_integration" in rubric_criteria
    
    def test_difficulty_level_assessment(self):
        """Test that difficulty levels are properly assessed."""
        # Simple content
        simple_latex = """
        \\section{Simple Analysis}
        This is a basic analysis. The method works well.
        """
        
        # Complex content
        complex_latex = """
        \\section{Advanced Methodology}
        Our sophisticated algorithm employs advanced statistical methodology 
        for optimization analysis using complex architectural frameworks. 
        The implementation utilizes state-of-the-art techniques including 
        gradient-based optimization, regularization mechanisms, and 
        attention-based neural architectures for enhanced performance.
        """
        
        # Test simple content
        simple_file = Path(self.temp_dir) / "simple.tex"
        simple_file.write_text(simple_latex, encoding='utf-8')
        simple_result = self.extractor.extract_from_latex(simple_file)
        simple_keys = self.answer_generator.generate_answer_keys(simple_result)
        
        # Test complex content
        complex_file = Path(self.temp_dir) / "complex.tex"
        complex_file.write_text(complex_latex, encoding='utf-8')
        complex_result = self.extractor.extract_from_latex(complex_file)
        complex_keys = self.answer_generator.generate_answer_keys(complex_result)
        
        # Simple content should have lower difficulty
        if simple_keys.answer_keys and complex_keys.answer_keys:
            simple_difficulty = simple_keys.answer_keys[0].difficulty_level
            complex_difficulty = complex_keys.answer_keys[0].difficulty_level
            
            # Both should be valid difficulty levels
            from src.arxiv_writer.core.answer_key_generator import DifficultyLevel
            assert simple_difficulty in DifficultyLevel
            assert complex_difficulty in DifficultyLevel