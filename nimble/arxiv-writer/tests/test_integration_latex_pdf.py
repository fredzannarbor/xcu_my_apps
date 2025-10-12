"""
Integration tests for LaTeX compilation and PDF generation.
"""

import pytest
import tempfile
import subprocess
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.arxiv_writer.core.paper_assembler import ArxivPaperAssembler, PDFGenerator
from src.arxiv_writer.core.models import PaperConfig, PaperMetadata
from src.arxiv_writer.core.arxiv_validator import ArxivValidator


class TestLaTeXPDFIntegration:
    """Integration tests for LaTeX compilation and PDF generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = PaperConfig(output_directory=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_complete_latex_document(self) -> str:
        """Create a complete LaTeX document for testing."""
        return r"""
\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amsfonts,amssymb}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{natbib}
\usepackage{geometry}
\geometry{margin=1in}

\title{Integration Test Paper: Advanced Machine Learning Techniques}
\author{John Doe\thanks{University of Example} \and Jane Smith\thanks{Tech Institute}}
\date{\today}

\begin{document}

\maketitle

\begin{abstract}
This paper presents a comprehensive analysis of advanced machine learning techniques, 
focusing on deep neural networks and their applications in computer vision and natural 
language processing. We demonstrate significant improvements over existing methods 
through extensive experimental validation on multiple benchmark datasets.
\end{abstract}

\section{Introduction}
\label{sec:introduction}

Machine learning has revolutionized numerous fields in recent years, with deep learning 
techniques achieving unprecedented performance in tasks ranging from image recognition 
to language translation~\cite{lecun2015deep}. This work builds upon these foundations 
to propose novel architectures that address current limitations.

The main contributions of this paper are:
\begin{itemize}
\item A novel neural network architecture combining convolutional and recurrent layers
\item Comprehensive evaluation on ImageNet, CIFAR-10, and custom datasets
\item Open-source implementation ensuring reproducibility
\item Theoretical analysis of convergence properties
\end{itemize}

\section{Related Work}
\label{sec:related}

Recent advances in deep learning have been driven by several key innovations. 
Convolutional Neural Networks (CNNs) have shown remarkable success in computer 
vision tasks~\cite{krizhevsky2012imagenet}, while Recurrent Neural Networks (RNNs) 
and their variants have excelled in sequential data processing~\cite{hochreiter1997long}.

\subsection{Convolutional Architectures}

The development of CNN architectures has progressed from simple LeNet-style networks 
to sophisticated designs like ResNet~\cite{he2016deep} and DenseNet~\cite{huang2017densely}. 
These architectures address the vanishing gradient problem through skip connections 
and dense connectivity patterns.

\subsection{Attention Mechanisms}

The introduction of attention mechanisms~\cite{bahdanau2014neural} has significantly 
improved model performance across various domains. The Transformer architecture~\cite{vaswani2017attention} 
has become the foundation for many state-of-the-art models in natural language processing.

\section{Methodology}
\label{sec:methodology}

Our approach combines the strengths of convolutional and recurrent architectures 
through a novel attention-based fusion mechanism. The proposed model consists of 
three main components:

\begin{enumerate}
\item Feature extraction module using residual convolutional blocks
\item Temporal modeling component with bidirectional LSTM layers
\item Attention-based fusion layer for combining spatial and temporal features
\end{enumerate}

\subsection{Architecture Details}

The feature extraction module employs a series of convolutional blocks with batch 
normalization and ReLU activation functions. Each block follows the structure:

\begin{equation}
\label{eq:conv_block}
y = \text{ReLU}(\text{BatchNorm}(\text{Conv}(x) + x))
\end{equation}

where $x$ is the input tensor and $y$ is the output after applying the residual connection.

\subsection{Training Procedure}

We train our model using the Adam optimizer with an initial learning rate of $10^{-3}$. 
The learning rate is reduced by a factor of 0.1 when the validation loss plateaus 
for more than 10 epochs. We use a batch size of 32 and train for a maximum of 200 epochs.

\section{Experiments}
\label{sec:experiments}

We evaluate our approach on three benchmark datasets: ImageNet-1K, CIFAR-10, and 
a custom dataset collected for this study. All experiments are conducted using 
PyTorch on NVIDIA V100 GPUs.

\subsection{Datasets}

\begin{itemize}
\item \textbf{ImageNet-1K}: 1.2M training images, 50K validation images, 1000 classes
\item \textbf{CIFAR-10}: 50K training images, 10K test images, 10 classes
\item \textbf{Custom Dataset}: 100K images across 50 categories, collected from various sources
\end{itemize}

\subsection{Evaluation Metrics}

We report results using standard metrics:
\begin{itemize}
\item Top-1 and Top-5 accuracy for classification tasks
\item F1-score for multi-class classification
\item Computational efficiency measured in FLOPs and inference time
\end{itemize}

\section{Results}
\label{sec:results}

Our experimental results demonstrate significant improvements over baseline methods. 
Table~\ref{tab:results} summarizes the performance across all datasets.

\begin{table}[htbp]
\centering
\caption{Performance comparison on benchmark datasets}
\label{tab:results}
\begin{tabular}{|l|c|c|c|}
\hline
Method & ImageNet Top-1 & CIFAR-10 & Custom Dataset \\
\hline
ResNet-50 & 76.2\% & 93.1\% & 87.5\% \\
DenseNet-121 & 74.9\% & 94.2\% & 88.1\% \\
Our Method & \textbf{78.5\%} & \textbf{95.7\%} & \textbf{90.3\%} \\
\hline
\end{tabular}
\end{table}

The results show consistent improvements across all datasets, with particularly 
strong performance on the custom dataset where domain-specific features are crucial.

\subsection{Ablation Studies}

We conduct comprehensive ablation studies to understand the contribution of each 
component. The attention mechanism contributes the most to performance improvement, 
followed by the residual connections in the feature extraction module.

\section{Discussion}
\label{sec:discussion}

The experimental results validate our hypothesis that combining convolutional and 
recurrent architectures through attention mechanisms can lead to improved performance. 
The attention weights learned by our model provide interpretable insights into which 
features are most important for classification decisions.

\subsection{Computational Efficiency}

Despite the increased model complexity, our approach maintains reasonable computational 
efficiency. The inference time is only 15\% higher than ResNet-50 while achieving 
significantly better accuracy.

\subsection{Limitations}

Our approach has several limitations that should be addressed in future work:
\begin{itemize}
\item Increased memory requirements during training
\item Sensitivity to hyperparameter choices
\item Limited evaluation on very large-scale datasets
\end{itemize}

\section{Conclusion}
\label{sec:conclusion}

This paper presents a novel neural network architecture that effectively combines 
convolutional and recurrent components through attention mechanisms. Our extensive 
experimental evaluation demonstrates consistent improvements over existing methods 
across multiple benchmark datasets.

Future work will focus on scaling the approach to larger datasets and exploring 
applications in other domains such as natural language processing and speech recognition. 
We also plan to investigate more efficient attention mechanisms to reduce computational overhead.

\section*{Acknowledgments}

We thank the anonymous reviewers for their valuable feedback. This work was supported 
by grants from the National Science Foundation and the Department of Energy.

\bibliographystyle{plain}
\bibliography{references}

\appendix

\section{Implementation Details}
\label{sec:appendix}

This appendix provides additional implementation details and hyperparameter settings 
used in our experiments. The complete source code is available at: 
\url{https://github.com/example/ml-integration-test}

\subsection{Hyperparameter Settings}

\begin{itemize}
\item Learning rate: $10^{-3}$ with cosine annealing
\item Batch size: 32 for all experiments
\item Weight decay: $10^{-4}$
\item Dropout rate: 0.1 in fully connected layers
\end{itemize}

\end{document}
        """
    
    def create_bibliography_file(self) -> str:
        """Create a bibliography file for testing."""
        return r"""
@article{lecun2015deep,
  title={Deep learning},
  author={LeCun, Yann and Bengio, Yoshua and Hinton, Geoffrey},
  journal={nature},
  volume={521},
  number={7553},
  pages={436--444},
  year={2015},
  publisher={Nature Publishing Group}
}

@inproceedings{krizhevsky2012imagenet,
  title={Imagenet classification with deep convolutional neural networks},
  author={Krizhevsky, Alex and Sutskever, Ilya and Hinton, Geoffrey E},
  booktitle={Advances in neural information processing systems},
  pages={1097--1105},
  year={2012}
}

@article{hochreiter1997long,
  title={Long short-term memory},
  author={Hochreiter, Sepp and Schmidhuber, J{\"u}rgen},
  journal={Neural computation},
  volume={9},
  number={8},
  pages={1735--1780},
  year={1997},
  publisher={MIT Press}
}

@inproceedings{he2016deep,
  title={Deep residual learning for image recognition},
  author={He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
  booktitle={Proceedings of the IEEE conference on computer vision and pattern recognition},
  pages={770--778},
  year={2016}
}

@inproceedings{huang2017densely,
  title={Densely connected convolutional networks},
  author={Huang, Gao and Liu, Zhuang and Van Der Maaten, Laurens and Weinberger, Kilian Q},
  booktitle={Proceedings of the IEEE conference on computer vision and pattern recognition},
  pages={4700--4708},
  year={2017}
}

@article{bahdanau2014neural,
  title={Neural machine translation by jointly learning to align and translate},
  author={Bahdanau, Dzmitry and Cho, Kyunghyun and Bengio, Yoshua},
  journal={arXiv preprint arXiv:1409.0473},
  year={2014}
}

@inproceedings{vaswani2017attention,
  title={Attention is all you need},
  author={Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N and Kaiser, {\L}ukasz and Polosukhin, Illia},
  booktitle={Advances in neural information processing systems},
  pages={5998--6008},
  year={2017}
}
        """
    
    @patch('subprocess.run')
    def test_complete_latex_compilation_workflow(self, mock_run):
        """Test complete LaTeX compilation workflow with realistic document."""
        # Create LaTeX document and bibliography
        latex_content = self.create_complete_latex_document()
        bib_content = self.create_bibliography_file()
        
        # Write files
        main_tex = Path(self.temp_dir) / "main.tex"
        main_tex.write_text(latex_content)
        
        bib_file = Path(self.temp_dir) / "references.bib"
        bib_file.write_text(bib_content)
        
        # Mock successful compilation runs
        def mock_subprocess_run(*args, **kwargs):
            command = args[0]
            if 'lualatex' in command:
                # Create mock PDF output
                pdf_path = Path(kwargs.get('cwd', self.temp_dir)) / "main.pdf"
                pdf_path.write_bytes(b"Mock PDF content " * 1000)  # Realistic size
                
                return Mock(
                    returncode=0,
                    stdout="LaTeX compilation successful\nOutput written to main.pdf",
                    stderr=""
                )
            elif 'bibtex' in command:
                # Create mock auxiliary files
                aux_path = Path(kwargs.get('cwd', self.temp_dir)) / "main.aux"
                aux_path.write_text("\\bibdata{references}\n\\bibstyle{plain}")
                
                bbl_path = Path(kwargs.get('cwd', self.temp_dir)) / "main.bbl"
                bbl_path.write_text("\\begin{thebibliography}{1}\n\\end{thebibliography}")
                
                return Mock(
                    returncode=0,
                    stdout="BibTeX compilation successful",
                    stderr=""
                )
            else:
                return Mock(returncode=0, stdout="", stderr="")
        
        mock_run.side_effect = mock_subprocess_run
        
        # Test compilation
        pdf_generator = PDFGenerator(self.temp_dir)
        result = pdf_generator.compile_to_pdf(str(main_tex))
        
        # Verify successful compilation
        assert result['success'] is True
        assert result['final_pdf'] == str(Path(self.temp_dir) / "main.pdf")
        assert len(result['compilation_log']) >= 3  # lualatex + bibtex + lualatex
        
        # Verify that all compilation steps were called
        lualatex_calls = [call for call in mock_run.call_args_list 
                         if 'lualatex' in str(call)]
        bibtex_calls = [call for call in mock_run.call_args_list 
                       if 'bibtex' in str(call)]
        
        assert len(lualatex_calls) >= 2  # At least 2 lualatex runs
        assert len(bibtex_calls) >= 1   # At least 1 bibtex run
    
    @patch('subprocess.run')
    def test_latex_compilation_error_handling(self, mock_run):
        """Test LaTeX compilation error handling and recovery."""
        # Create LaTeX document with intentional errors
        latex_with_errors = r"""
\documentclass{article}
\begin{document}

\section{Test Section}
This has an undefined command: \undefinedcommand

And a missing closing brace: \textbf{bold text

\cite{nonexistent_reference}

\end{document}
        """
        
        main_tex = Path(self.temp_dir) / "main.tex"
        main_tex.write_text(latex_with_errors)
        
        # Mock failed compilation
        def mock_failed_compilation(*args, **kwargs):
            return Mock(
                returncode=1,
                stdout="LaTeX compilation output",
                stderr="""
! Undefined control sequence.
l.6 This has an undefined command: \\undefinedcommand

! Missing } inserted.
l.8 And a missing closing brace: \\textbf{bold text

! Citation 'nonexistent_reference' on page 1 undefined.
                """
            )
        
        mock_run.side_effect = mock_failed_compilation
        
        # Test error handling
        pdf_generator = PDFGenerator(self.temp_dir)
        result = pdf_generator.compile_to_pdf(str(main_tex))
        
        # Verify error handling
        assert result['success'] is False
        assert len(result['errors']) > 0
        assert "First lualatex run failed" in result['errors']
        
        # Verify error details are captured
        log_entry = result['compilation_log'][0]
        assert log_entry['returncode'] == 1
        assert "Undefined control sequence" in log_entry['stderr']
        assert "Missing } inserted" in log_entry['stderr']
    
    @patch('subprocess.run')
    def test_arxiv_paper_assembler_integration(self, mock_run):
        """Test complete ArXiv paper assembler integration."""
        # Mock successful compilation
        def mock_successful_run(*args, **kwargs):
            command = args[0]
            if 'lualatex' in command:
                # Create realistic PDF output
                pdf_path = Path(kwargs.get('cwd', self.temp_dir)) / "arxiv_paper.pdf"
                pdf_path.write_bytes(b"PDF content " * 5000)  # 40KB PDF
                
                return Mock(
                    returncode=0,
                    stdout="This is pdfTeX, Version 3.14159265-2.6-1.40.21\nOutput written on arxiv_paper.pdf (8 pages, 40960 bytes).",
                    stderr=""
                )
            return Mock(returncode=0, stdout="", stderr="")
        
        mock_run.side_effect = mock_successful_run
        
        # Create paper metadata
        metadata = PaperMetadata(
            title="Integration Test Paper",
            authors=["John Doe", "Jane Smith"],
            abstract="This is a test abstract for integration testing.",
            keywords=["integration", "testing", "latex", "pdf"],
            sections={
                "introduction": "This is the introduction section.",
                "methodology": "This describes our methodology.",
                "results": "These are our results.",
                "conclusion": "This is our conclusion."
            }
        )
        
        # Test complete assembly and compilation
        assembler = ArxivPaperAssembler(self.config)
        result = assembler.assemble_and_compile_paper(metadata)
        
        # Verify successful assembly and compilation
        assert result['success'] is True
        assert 'final_pdf' in result
        assert Path(result['final_pdf']).exists()
        assert Path(result['final_pdf']).stat().st_size > 1000  # Reasonable PDF size
        
        # Verify LaTeX files were created
        assert 'main_file' in result
        assert Path(result['main_file']).exists()
        assert Path(result['main_file']).suffix == '.tex'
    
    def test_arxiv_validator_integration(self):
        """Test ArXiv validator integration with real LaTeX files."""
        # Create a complete LaTeX structure
        latex_content = self.create_complete_latex_document()
        bib_content = self.create_bibliography_file()
        
        # Create LaTeX directory structure
        latex_dir = Path(self.temp_dir) / "latex"
        latex_dir.mkdir()
        
        main_tex = latex_dir / "main.tex"
        main_tex.write_text(latex_content)
        
        bib_file = latex_dir / "references.bib"
        bib_file.write_text(bib_content)
        
        # Create additional required files
        (latex_dir / "main.aux").write_text("\\relax")
        (latex_dir / "main.log").write_text("LaTeX log file content")
        
        # Test validation
        validator = ArxivValidator(str(latex_dir))
        
        with patch('subprocess.run') as mock_run:
            # Mock successful compilation for validation
            mock_run.return_value = Mock(
                returncode=0,
                stdout="LaTeX compilation successful",
                stderr=""
            )
            
            # Create mock PDF for validation
            (latex_dir / "main.pdf").write_bytes(b"Mock PDF content")
            
            validation_result = validator.validate()
        
        # Verify validation results
        assert validation_result['valid'] is True
        assert len(validation_result['errors']) == 0
        
        # Check specific validation criteria
        success_results = [r for r in validator.results if r['status']]
        assert len(success_results) > 0
        
        # Should have validated compilation
        compilation_results = [r for r in success_results 
                             if 'compiles' in r['message'].lower()]
        assert len(compilation_results) > 0
    
    @patch('subprocess.run')
    def test_pdf_generation_with_figures(self, mock_run):
        """Test PDF generation with figures and complex LaTeX elements."""
        # Create LaTeX document with figures
        latex_with_figures = r"""
\documentclass{article}
\usepackage{graphicx}
\usepackage{tikz}
\usepackage{pgfplots}

\begin{document}

\title{Test Paper with Figures}
\author{Test Author}
\maketitle

\section{Introduction}

This paper includes various types of figures and complex LaTeX elements.

\begin{figure}[htbp]
\centering
\begin{tikzpicture}
\draw (0,0) -- (2,0) -- (2,2) -- (0,2) -- cycle;
\draw (1,1) circle (0.5);
\end{tikzpicture}
\caption{A simple TikZ figure}
\label{fig:tikz}
\end{figure}

\begin{figure}[htbp]
\centering
\begin{tikzpicture}
\begin{axis}[
    xlabel={X axis},
    ylabel={Y axis},
    title={Sample Plot}
]
\addplot coordinates {(0,0) (1,1) (2,4) (3,9)};
\end{axis}
\end{tikzpicture}
\caption{A sample plot using pgfplots}
\label{fig:plot}
\end{figure}

As shown in Figure~\ref{fig:tikz} and Figure~\ref{fig:plot}, 
our approach handles complex visual elements effectively.

\section{Mathematical Content}

The following equation demonstrates complex mathematical typesetting:

\begin{align}
\mathcal{L}(\theta) &= \sum_{i=1}^{N} \log p(y_i | x_i, \theta) \\
&= \sum_{i=1}^{N} \log \frac{\exp(f_\theta(x_i)_{y_i})}{\sum_{j=1}^{C} \exp(f_\theta(x_i)_j)} \\
&= \sum_{i=1}^{N} \left[ f_\theta(x_i)_{y_i} - \log \sum_{j=1}^{C} \exp(f_\theta(x_i)_j) \right]
\end{align}

\end{document}
        """
        
        main_tex = Path(self.temp_dir) / "main.tex"
        main_tex.write_text(latex_with_figures)
        
        # Mock successful compilation with figure processing
        def mock_figure_compilation(*args, **kwargs):
            # Simulate longer compilation time for figures
            import time
            time.sleep(0.1)
            
            # Create mock PDF with figures
            pdf_path = Path(kwargs.get('cwd', self.temp_dir)) / "main.pdf"
            pdf_path.write_bytes(b"PDF with figures " * 2000)  # Larger PDF
            
            return Mock(
                returncode=0,
                stdout="""
This is LuaTeX, Version 1.13.0
Output written on main.pdf (3 pages, 65536 bytes).
Transcript written on main.log.
                """,
                stderr=""
            )
        
        mock_run.side_effect = mock_figure_compilation
        
        # Test compilation with figures
        pdf_generator = PDFGenerator(self.temp_dir)
        result = pdf_generator.compile_to_pdf(str(main_tex))
        
        # Verify successful compilation
        assert result['success'] is True
        assert Path(result['final_pdf']).stat().st_size > 10000  # Larger PDF due to figures
        
        # Verify compilation log includes figure processing
        assert len(result['compilation_log']) >= 2  # Multiple runs for figures
    
    def test_latex_compilation_timeout_handling(self):
        """Test handling of LaTeX compilation timeouts."""
        latex_content = self.create_complete_latex_document()
        main_tex = Path(self.temp_dir) / "main.tex"
        main_tex.write_text(latex_content)
        
        with patch('subprocess.run') as mock_run:
            # Mock timeout
            mock_run.side_effect = subprocess.TimeoutExpired(['lualatex'], 300)
            
            pdf_generator = PDFGenerator(self.temp_dir)
            result = pdf_generator.compile_to_pdf(str(main_tex))
            
            # Verify timeout handling
            assert result['success'] is False
            assert len(result['errors']) > 0
            
            # Check that timeout was properly recorded
            log_entry = result['compilation_log'][0]
            assert log_entry['returncode'] == -1
            assert 'timeout' in log_entry['error'].lower()
    
    @patch('subprocess.run')
    def test_multi_file_latex_project(self, mock_run):
        """Test compilation of multi-file LaTeX projects."""
        # Create main document
        main_content = r"""
\documentclass{article}
\usepackage{subfiles}

\title{Multi-file LaTeX Project}
\author{Test Author}

\begin{document}
\maketitle

\subfile{sections/introduction}
\subfile{sections/methodology}
\subfile{sections/results}
\subfile{sections/conclusion}

\bibliographystyle{plain}
\bibliography{references}

\end{document}
        """
        
        # Create section files
        sections = {
            "introduction": r"""
\documentclass[../main.tex]{subfiles}
\begin{document}
\section{Introduction}
This is the introduction section from a separate file.
\end{document}
            """,
            "methodology": r"""
\documentclass[../main.tex]{subfiles}
\begin{document}
\section{Methodology}
This describes our methodology from a separate file.
\end{document}
            """,
            "results": r"""
\documentclass[../main.tex]{subfiles}
\begin{document}
\section{Results}
These are our results from a separate file.
\end{document}
            """,
            "conclusion": r"""
\documentclass[../main.tex]{subfiles}
\begin{document}
\section{Conclusion}
This is our conclusion from a separate file.
\end{document}
            """
        }
        
        # Write main file
        main_tex = Path(self.temp_dir) / "main.tex"
        main_tex.write_text(main_content)
        
        # Create sections directory and files
        sections_dir = Path(self.temp_dir) / "sections"
        sections_dir.mkdir()
        
        for section_name, section_content in sections.items():
            section_file = sections_dir / f"{section_name}.tex"
            section_file.write_text(section_content)
        
        # Create bibliography
        bib_file = Path(self.temp_dir) / "references.bib"
        bib_file.write_text(self.create_bibliography_file())
        
        # Mock successful compilation
        def mock_multi_file_compilation(*args, **kwargs):
            # Create PDF output
            pdf_path = Path(kwargs.get('cwd', self.temp_dir)) / "main.pdf"
            pdf_path.write_bytes(b"Multi-file PDF content " * 1000)
            
            return Mock(
                returncode=0,
                stdout="Multi-file LaTeX compilation successful",
                stderr=""
            )
        
        mock_run.side_effect = mock_multi_file_compilation
        
        # Test multi-file compilation
        pdf_generator = PDFGenerator(self.temp_dir)
        result = pdf_generator.compile_to_pdf(str(main_tex))
        
        # Verify successful compilation
        assert result['success'] is True
        assert Path(result['final_pdf']).exists()
        
        # Verify that all section files are accessible
        for section_name in sections.keys():
            section_file = sections_dir / f"{section_name}.tex"
            assert section_file.exists()


class TestLaTeXPDFPerformance:
    """Performance tests for LaTeX compilation and PDF generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_large_document_compilation_performance(self, mock_run):
        """Test compilation performance with large documents."""
        # Create a large LaTeX document
        large_content = r"""
\documentclass{article}
\usepackage{lipsum}
\begin{document}
\title{Large Document Performance Test}
\author{Test Author}
\maketitle
        """
        
        # Add many sections with Lorem ipsum text
        for i in range(50):
            large_content += f"""
\section{{Section {i+1}}}
\\lipsum[1-10]

\\subsection{{Subsection {i+1}.1}}
\\lipsum[11-20]

\\subsection{{Subsection {i+1}.2}}
\\lipsum[21-30]
            """
        
        large_content += r"\end{document}"
        
        main_tex = Path(self.temp_dir) / "large_document.tex"
        main_tex.write_text(large_content)
        
        # Mock compilation with realistic timing
        def mock_large_compilation(*args, **kwargs):
            import time
            time.sleep(0.5)  # Simulate longer compilation time
            
            # Create large PDF
            pdf_path = Path(kwargs.get('cwd', self.temp_dir)) / "large_document.pdf"
            pdf_path.write_bytes(b"Large PDF content " * 10000)  # ~400KB
            
            return Mock(
                returncode=0,
                stdout="Large document compilation successful",
                stderr=""
            )
        
        mock_run.side_effect = mock_large_compilation
        
        # Test performance
        pdf_generator = PDFGenerator(self.temp_dir)
        
        import time
        start_time = time.time()
        result = pdf_generator.compile_to_pdf(str(main_tex))
        compilation_time = time.time() - start_time
        
        # Verify performance
        assert result['success'] is True
        assert compilation_time < 10  # Should complete within 10 seconds
        assert Path(result['final_pdf']).stat().st_size > 100000  # Large PDF
    
    @patch('subprocess.run')
    def test_concurrent_compilation_safety(self, mock_run):
        """Test safety of concurrent LaTeX compilations."""
        import threading
        import time
        
        compilation_results = []
        
        def mock_concurrent_compilation(*args, **kwargs):
            # Simulate compilation time
            time.sleep(0.2)
            
            # Create unique PDF for each compilation
            cwd = kwargs.get('cwd', self.temp_dir)
            pdf_name = Path(cwd).name + ".pdf"
            pdf_path = Path(cwd) / pdf_name
            pdf_path.write_bytes(f"PDF content for {cwd}".encode() * 100)
            
            return Mock(
                returncode=0,
                stdout=f"Compilation successful in {cwd}",
                stderr=""
            )
        
        mock_run.side_effect = mock_concurrent_compilation
        
        def compile_document(doc_id):
            # Create separate directory for each compilation
            doc_dir = Path(self.temp_dir) / f"doc_{doc_id}"
            doc_dir.mkdir()
            
            latex_content = f"""
\\documentclass{{article}}
\\begin{{document}}
\\title{{Document {doc_id}}}
\\author{{Test Author}}
\\maketitle
\\section{{Content}}
This is document {doc_id}.
\\end{{document}}
            """
            
            tex_file = doc_dir / f"doc_{doc_id}.tex"
            tex_file.write_text(latex_content)
            
            pdf_generator = PDFGenerator(str(doc_dir))
            result = pdf_generator.compile_to_pdf(str(tex_file))
            compilation_results.append((doc_id, result))
        
        # Start multiple concurrent compilations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=compile_document, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all compilations to complete
        for thread in threads:
            thread.join()
        
        # Verify all compilations succeeded
        assert len(compilation_results) == 5
        for doc_id, result in compilation_results:
            assert result['success'] is True
            assert Path(result['final_pdf']).exists()
    
    def test_memory_usage_during_compilation(self):
        """Test memory usage during LaTeX compilation."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create memory-intensive LaTeX document
        memory_intensive_content = r"""
\documentclass{article}
\usepackage{tikz}
\usepackage{pgfplots}
\begin{document}
\title{Memory Usage Test}
\maketitle
        """
        
        # Add many complex figures
        for i in range(20):
            memory_intensive_content += f"""
\\begin{{figure}}[htbp]
\\centering
\\begin{{tikzpicture}}
\\begin{{axis}}[
    width=10cm,
    height=8cm,
    xlabel={{X axis {i}}},
    ylabel={{Y axis {i}}},
    title={{Complex Plot {i}}}
]
\\addplot coordinates {{
    {' '.join([f'({j},{j*j+i})' for j in range(100)])}
}};
\\end{{axis}}
\\end{{tikzpicture}}
\\caption{{Complex figure {i}}}
\\end{{figure}}
            """
        
        memory_intensive_content += r"\end{document}"
        
        tex_file = Path(self.temp_dir) / "memory_test.tex"
        tex_file.write_text(memory_intensive_content)
        
        with patch('subprocess.run') as mock_run:
            # Mock compilation that doesn't actually consume memory
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Memory test compilation successful",
                stderr=""
            )
            
            # Create mock PDF
            pdf_path = Path(self.temp_dir) / "memory_test.pdf"
            pdf_path.write_bytes(b"Memory test PDF " * 1000)
            
            pdf_generator = PDFGenerator(self.temp_dir)
            result = pdf_generator.compile_to_pdf(str(tex_file))
        
        # Check memory usage after processing
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 100, f"Memory usage increased by {memory_increase}MB"
        assert result['success'] is True