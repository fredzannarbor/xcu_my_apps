"""
LaTeX Paper Generation and Formatting System

This module provides LaTeX templates and formatting tools for generating
arXiv-compliant academic papers from the generated content sections.
"""

import logging
import json
import os
import re
import subprocess
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

# Import existing proven LaTeX utilities
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.codexes.modules.prepress.tex_utils import escape_latex, markdown_to_latex

logger = logging.getLogger(__name__)


@dataclass
class LaTeXDocument:
    """Represents a complete LaTeX document."""
    title: str
    authors: List[str]
    abstract: str
    sections: Dict[str, str]
    bibliography: str
    metadata: Dict[str, Any]
    template_name: str = "arxiv_paper"


@dataclass
class LaTeXFormattingConfig:
    """Configuration for LaTeX formatting."""
    template_dir: str
    output_dir: str
    bibliography_style: str = "plain"
    document_class: str = "article"
    font_size: str = "11pt"
    paper_size: str = "letterpaper"
    margins: str = "1in"
    line_spacing: str = "1.15"
    citation_style: str = "numeric"
    include_hyperlinks: bool = True
    include_bookmarks: bool = True


class LaTeXTemplateManager:
    """Manages LaTeX templates for academic papers."""
    
    def __init__(self, template_dir: str):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_templates_exist()
    
    def _ensure_templates_exist(self):
        """Ensure all required LaTeX templates exist."""
        templates = {
            "main.tex": self._get_main_template(),
            "preamble.tex": self._get_preamble_template(),
            "title_page.tex": self._get_title_page_template(),
            "abstract.tex": self._get_abstract_template(),
            "section.tex": self._get_section_template(),
            "bibliography.tex": self._get_bibliography_template(),
            "appendix.tex": self._get_appendix_template()
        }
        
        for filename, content in templates.items():
            template_path = self.template_dir / filename
            if not template_path.exists():
                with open(template_path, 'w') as f:
                    f.write(content)
                logger.info(f"Created LaTeX template: {template_path}")
    
    def _get_main_template(self) -> str:
        """Get the main document template."""
        return r"""\documentclass[11pt,letterpaper]{article}

% Include preamble
\input{preamble}

\begin{document}

% Title page
\input{title_page}

% Abstract
\input{abstract}

% Table of contents (optional for arXiv)
% \tableofcontents
% \newpage

% Main content sections
\input{introduction}
\input{related_work}
\input{methodology}
\input{implementation}
\input{results}
\input{discussion}
\input{conclusion}

% Bibliography
\input{bibliography}

% Appendices (if any)
% \input{appendix}

\end{document}
"""
    
    def _get_preamble_template(self) -> str:
        """Get the preamble template with packages and settings."""
        return r"""%% ArXiv Paper Preamble
%% Compliant with arXiv submission standards

% Basic packages
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{microtype}

% Page layout
\usepackage[letterpaper,margin=1in]{geometry}
\usepackage{setspace}
\setstretch{1.15}

% Math packages
\usepackage{amsmath,amssymb,amsthm}
\usepackage{mathtools}

% Graphics and figures
\usepackage{graphicx}
\usepackage{float}
\usepackage{subcaption}
\usepackage{tikz}
\usetikzlibrary{shapes,arrows,positioning}

% Tables
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\usepackage{longtable}

% Code listings
\usepackage{listings}
\usepackage{xcolor}

% Define code listing style
\lstdefinestyle{pythonstyle}{
    language=Python,
    basicstyle=\ttfamily\footnotesize,
    keywordstyle=\color{blue},
    commentstyle=\color{gray},
    stringstyle=\color{red},
    numberstyle=\tiny\color{gray},
    numbers=left,
    numbersep=5pt,
    frame=single,
    breaklines=true,
    breakatwhitespace=true,
    tabsize=4,
    showstringspaces=false
}

\lstdefinestyle{jsonstyle}{
    language=,
    basicstyle=\ttfamily\footnotesize,
    keywordstyle=\color{blue},
    commentstyle=\color{gray},
    stringstyle=\color{red},
    numberstyle=\tiny\color{gray},
    numbers=left,
    numbersep=5pt,
    frame=single,
    breaklines=true,
    breakatwhitespace=true,
    tabsize=2,
    showstringspaces=false
}

\lstdefinestyle{yamlstyle}{
    language=,
    basicstyle=\ttfamily\footnotesize,
    keywordstyle=\color{blue},
    commentstyle=\color{gray},
    stringstyle=\color{red},
    numberstyle=\tiny\color{gray},
    numbers=left,
    numbersep=5pt,
    frame=single,
    breaklines=true,
    breakatwhitespace=true,
    tabsize=2,
    showstringspaces=false
}

\lstdefinestyle{texstyle}{
    language=[LaTeX]TeX,
    basicstyle=\ttfamily\footnotesize,
    keywordstyle=\color{blue},
    commentstyle=\color{gray},
    stringstyle=\color{red},
    numberstyle=\tiny\color{gray},
    numbers=left,
    numbersep=5pt,
    frame=single,
    breaklines=true,
    breakatwhitespace=true,
    tabsize=2,
    showstringspaces=false
}

% Set default listing style
\lstset{style=pythonstyle}

% Hyperlinks and bookmarks
\usepackage[colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue]{hyperref}
\usepackage{bookmark}

% Bibliography
\usepackage{natbib}
\bibliographystyle{plainnat}

% Custom commands
\newcommand{\code}[1]{\texttt{#1}}
\newcommand{\file}[1]{\texttt{#1}}
\newcommand{\package}[1]{\texttt{#1}}

% Theorem environments
\theoremstyle{definition}
\newtheorem{definition}{Definition}
\newtheorem{example}{Example}

\theoremstyle{plain}
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}{Lemma}
\newtheorem{proposition}{Proposition}

\theoremstyle{remark}
\newtheorem{remark}{Remark}
\newtheorem{note}{Note}

% Title and author information (to be filled by generator)
\title{AI-Assisted Creation of a Publishing Imprint: The xynapse\_traces Case Study}
\author{AI Lab for Book-Lovers\\
\texttt{wfz@nimblebooks.com}\\
Nimble Books LLC}
\date{\today}
"""
    
    def _get_title_page_template(self) -> str:
        """Get the title page template."""
        return r"""%% Title Page
\maketitle

\begin{abstract}
{ABSTRACT_CONTENT}
\end{abstract}

\vspace{1em}

\noindent\textbf{Keywords:} artificial intelligence, publishing automation, digital humanities, content generation, multilingual processing, configuration management

\vspace{1em}

\noindent\textbf{Subject Classification:} Computer Science - Artificial Intelligence (cs.AI), Computer Science - Human-Computer Interaction (cs.HC)

\newpage
"""
    
    def _get_abstract_template(self) -> str:
        """Get the abstract template."""
        return r"""%% Abstract (included in title page)
%% This file is for reference only
"""
    
    def _get_section_template(self) -> str:
        """Get the section template."""
        return r"""%% Section Template
%% Use this as a reference for section formatting

\section{Section Title}
\label{sec:section_label}

Section content goes here. Use proper LaTeX formatting:

\begin{itemize}
    \item Bullet points for lists
    \item Use \textbf{bold} and \textit{italic} formatting
    \item Reference figures with \autoref{fig:label}
    \item Reference tables with \autoref{tab:label}
    \item Reference sections with \autoref{sec:label}
\end{itemize}

\subsection{Subsection Title}
\label{subsec:subsection_label}

Subsection content.

\subsubsection{Subsubsection Title}

Subsubsection content (use sparingly).

%% Code listing example
\begin{lstlisting}[style=pythonstyle,caption={Python code example},label=lst:python_example]
def example_function():
    return "Hello, World!"
\end{lstlisting}

%% Figure example
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.8\textwidth]{figures/example_figure.pdf}
    \caption{Example figure caption.}
    \label{fig:example_figure}
\end{figure}

%% Table example
\begin{table}[htbp]
    \centering
    \caption{Example table caption.}
    \label{tab:example_table}
    \begin{tabular}{@{}lcc@{}}
        \toprule
        Item & Value 1 & Value 2 \\
        \midrule
        Row 1 & 123 & 456 \\
        Row 2 & 789 & 012 \\
        \bottomrule
    \end{tabular}
\end{table}
"""
    
    def _get_bibliography_template(self) -> str:
        """Get the bibliography template."""
        return r"""%% Bibliography
\bibliography{references}
"""
    
    def _get_appendix_template(self) -> str:
        """Get the appendix template."""
        return r"""%% Appendix
\appendix

\section{Supplemental Information}
\label{sec:appendix}

Supplemental information goes here.

\subsection{Configuration Examples}
\label{subsec:config_examples}

Detailed configuration examples.

\subsection{Performance Metrics}
\label{subsec:performance_metrics}

Additional performance data and analysis.
"""
    
    def get_template_path(self, template_name: str) -> Path:
        """Get the path to a specific template."""
        return self.template_dir / f"{template_name}.tex"
    
    def load_template(self, template_name: str) -> str:
        """Load a template file."""
        template_path = self.get_template_path(template_name)
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(template_path, 'r') as f:
            return f.read()


class LaTeXContentFormatter:
    """Formats content for LaTeX output."""
    
    def __init__(self):
        # Use the proven escape_latex function from tex_utils
        pass
    
    def format_markdown_to_latex(self, markdown_content: str) -> str:
        """Convert markdown content to LaTeX format."""
        # Remove markdown metadata headers completely
        lines = markdown_content.split('\n')
        content_lines = []
        skip_metadata = False
        in_code_block = False
        code_block_type = None
        
        for i, line in enumerate(lines):
            # Skip title and metadata block
            if i == 0 and line.startswith('#'):
                continue
            if line.strip() == '---':
                skip_metadata = not skip_metadata
                continue
            if skip_metadata:
                continue
            
            # Handle code blocks
            if line.strip().startswith('```'):
                if not in_code_block:
                    # Starting a code block
                    in_code_block = True
                    code_block_type = line.strip()[3:].strip()
                    if code_block_type in ['python', 'json', 'yaml', 'tex']:
                        content_lines.append(f'\\begin{{lstlisting}}[style={code_block_type}style]')
                    else:
                        content_lines.append('\\begin{lstlisting}')
                else:
                    # Ending a code block
                    in_code_block = False
                    content_lines.append('\\end{lstlisting}')
                    code_block_type = None
                continue
            
            # If we're in a code block, add the line as-is (no escaping)
            if in_code_block:
                content_lines.append(line)
                continue
            
            # Skip generation metadata sections
            if line.strip().startswith('**Generation Metadata:**'):
                break
                
            content_lines.append(line)
        
        content = '\n'.join(content_lines).strip()
        
        # Only escape special characters outside of lstlisting environments
        lines = content.split('\n')
        formatted_lines = []
        in_lstlisting = False
        
        for line in lines:
            if '\\begin{lstlisting}' in line:
                in_lstlisting = True
                formatted_lines.append(line)
                continue
            elif '\\end{lstlisting}' in line:
                in_lstlisting = False
                formatted_lines.append(line)
                continue
            elif in_lstlisting:
                # Don't escape anything in code blocks
                formatted_lines.append(line)
                continue
            
            # Escape special characters only outside code blocks
            line = escape_latex(line)
            
            # Convert basic markdown formatting
            # Headers (after escaping)
            line = re.sub(r'^\\# (.*?)$', r'\\subsection{\1}', line)
            line = re.sub(r'^\\#\\# (.*?)$', r'\\subsubsection{\1}', line)
            
            # Bold and italic (handle escaped asterisks)
            line = re.sub(r'\\textbackslash\{\}\\textbackslash\{\}(.*?)\\textbackslash\{\}\\textbackslash\{\}', r'\\textbf{\1}', line)
            line = re.sub(r'\\textbackslash\{\}(.*?)\\textbackslash\{\}', r'\\textit{\1}', line)
            
            # Inline code (handle escaped backticks) - but be careful with braces
            line = re.sub(r'`([^`]+)`', lambda m: f'\\texttt{{{escape_latex(m.group(1))}}}', line)
            
            formatted_lines.append(line)
        
        content = '\n'.join(formatted_lines)
        
        # Handle lists
        content = re.sub(r'^- (.*?)$', r'\\item \1', content, flags=re.MULTILINE)
        
        # Wrap itemize environments
        lines = content.split('\n')
        in_list = False
        final_lines = []
        
        for line in lines:
            if line.strip().startswith('\\item'):
                if not in_list:
                    final_lines.append('\\begin{itemize}')
                    in_list = True
                final_lines.append(line)
            else:
                if in_list:
                    final_lines.append('\\end{itemize}')
                    in_list = False
                final_lines.append(line)
        
        if in_list:
            final_lines.append('\\end{itemize}')
        
        content = '\n'.join(final_lines)
        
        # Clean up extra whitespace
        content = re.sub(r'\n\n\n+', '\n\n', content)
        
        return content.strip()
    
    def format_table_data(self, table_data: List[Dict[str, Any]], caption: str = "", label: str = "") -> str:
        """Format table data as LaTeX table."""
        if not table_data:
            return ""
        
        # Get column headers
        headers = list(table_data[0].keys())
        num_cols = len(headers)
        
        # Create column specification
        col_spec = 'l' * num_cols
        
        # Start table
        latex_table = f"""\\begin{{table}}[htbp]
    \\centering
    \\caption{{{caption}}}
    \\label{{tab:{label}}}
    \\begin{{tabular}}{{@{{}}{col_spec}@{{}}}}
        \\toprule
"""
        
        # Add headers
        header_row = ' & '.join([escape_latex(str(h)) for h in headers])
        latex_table += f"        {header_row} \\\\\n        \\midrule\n"
        
        # Add data rows
        for row in table_data:
            row_data = [escape_latex(str(row.get(h, ''))) for h in headers]
            row_str = ' & '.join(row_data)
            latex_table += f"        {row_str} \\\\\n"
        
        # End table
        latex_table += """        \\bottomrule
    \\end{tabular}
\\end{table}
"""
        
        return latex_table
    
    def format_figure(self, figure_path: str, caption: str = "", label: str = "", width: str = "0.8") -> str:
        """Format figure inclusion."""
        return f"""\\begin{{figure}}[htbp]
    \\centering
    \\includegraphics[width={width}\\textwidth]{{{figure_path}}}
    \\caption{{{caption}}}
    \\label{{fig:{label}}}
\\end{{figure}}
"""


class LaTeXCompiler:
    """Compiles LaTeX documents to PDF."""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def compile_document(self, main_tex_file: str, output_name: str = "paper") -> Dict[str, Any]:
        """Compile LaTeX document to PDF."""
        main_tex_path = Path(main_tex_file)
        
        if not main_tex_path.exists():
            raise FileNotFoundError(f"Main LaTeX file not found: {main_tex_path}")
        
        # Change to the directory containing the LaTeX file
        original_cwd = os.getcwd()
        tex_dir = main_tex_path.parent
        
        try:
            os.chdir(tex_dir)
            
            # Run pdflatex multiple times for cross-references
            compilation_results = []
            
            for run_number in range(3):  # Usually 2-3 runs needed for references
                logger.info(f"Running pdflatex (run {run_number + 1}/3)...")
                
                result = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', main_tex_path.name],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                compilation_results.append({
                    'run': run_number + 1,
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                })
                
                if result.returncode != 0:
                    logger.error(f"pdflatex run {run_number + 1} failed with return code {result.returncode}")
                    logger.error(f"Error output: {result.stderr}")
                    break
            
            # Run bibtex if bibliography exists
            bib_files = list(tex_dir.glob("*.bib"))
            if bib_files:
                logger.info("Running bibtex...")
                result = subprocess.run(
                    ['bibtex', main_tex_path.stem],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                compilation_results.append({
                    'tool': 'bibtex',
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                })
                
                # Run pdflatex again after bibtex
                if result.returncode == 0:
                    for run_number in range(2):
                        logger.info(f"Running pdflatex after bibtex (run {run_number + 1}/2)...")
                        
                        result = subprocess.run(
                            ['pdflatex', '-interaction=nonstopmode', main_tex_path.name],
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        
                        compilation_results.append({
                            'run': f'post-bibtex-{run_number + 1}',
                            'returncode': result.returncode,
                            'stdout': result.stdout,
                            'stderr': result.stderr
                        })
            
            # Check if PDF was generated
            pdf_path = tex_dir / f"{main_tex_path.stem}.pdf"
            
            if pdf_path.exists():
                # Move PDF to output directory
                output_pdf_path = self.output_dir / f"{output_name}.pdf"
                pdf_path.rename(output_pdf_path)
                
                logger.info(f"Successfully compiled LaTeX document to: {output_pdf_path}")
                
                return {
                    'success': True,
                    'pdf_path': str(output_pdf_path),
                    'compilation_results': compilation_results
                }
            else:
                logger.error("PDF file was not generated")
                return {
                    'success': False,
                    'error': 'PDF file not generated',
                    'compilation_results': compilation_results
                }
        
        except subprocess.TimeoutExpired:
            logger.error("LaTeX compilation timed out")
            return {
                'success': False,
                'error': 'Compilation timed out',
                'compilation_results': compilation_results
            }
        
        except Exception as e:
            logger.error(f"Error during LaTeX compilation: {e}")
            return {
                'success': False,
                'error': str(e),
                'compilation_results': compilation_results
            }
        
        finally:
            os.chdir(original_cwd)


class ArxivLaTeXGenerator:
    """Main class for generating arXiv-compliant LaTeX papers."""
    
    def __init__(self, config: LaTeXFormattingConfig):
        self.config = config
        self.template_manager = LaTeXTemplateManager(config.template_dir)
        self.formatter = LaTeXContentFormatter()
        self.compiler = LaTeXCompiler(config.output_dir)
        
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_latex_paper(self, content_dir: str, bibliography_file: str = None) -> Dict[str, Any]:
        """Generate complete LaTeX paper from content directory."""
        content_path = Path(content_dir)
        
        if not content_path.exists():
            raise FileNotFoundError(f"Content directory not found: {content_path}")
        
        logger.info(f"Generating LaTeX paper from content in: {content_path}")
        
        # Load content sections
        sections = self._load_content_sections(content_path)
        
        # Generate LaTeX files
        latex_files = {}
        
        # Generate main sections
        section_mapping = {
            'introduction': 'introduction.md',
            'related_work': 'related_work.md',
            'methodology': 'methodology.md',
            'implementation': 'implementation.md',
            'results': 'results.md',
            'discussion': 'discussion.md',
            'conclusion': 'conclusion.md'
        }
        
        for section_name, filename in section_mapping.items():
            if filename in sections:
                latex_content = self.formatter.format_markdown_to_latex(sections[filename])
                latex_files[f"{section_name}.tex"] = latex_content
                
                # Save to file
                section_file = self.output_dir / f"{section_name}.tex"
                with open(section_file, 'w') as f:
                    f.write(latex_content)
                
                logger.info(f"Generated LaTeX section: {section_file}")
        
        # Generate title page with abstract
        if 'abstract.md' in sections:
            abstract_content = self.formatter.format_markdown_to_latex(sections['abstract.md'])
            title_page_template = self.template_manager.load_template('title_page')
            title_page_content = title_page_template.replace('{ABSTRACT_CONTENT}', abstract_content)
            
            title_page_file = self.output_dir / "title_page.tex"
            with open(title_page_file, 'w') as f:
                f.write(title_page_content)
            
            latex_files['title_page.tex'] = title_page_content
            logger.info(f"Generated title page: {title_page_file}")
        
        # Copy preamble
        preamble_content = self.template_manager.load_template('preamble')
        preamble_file = self.output_dir / "preamble.tex"
        with open(preamble_file, 'w') as f:
            f.write(preamble_content)
        latex_files['preamble.tex'] = preamble_content
        
        # Generate main document
        main_content = self.template_manager.load_template('main')
        main_file = self.output_dir / "main.tex"
        with open(main_file, 'w') as f:
            f.write(main_content)
        latex_files['main.tex'] = main_content
        
        # Handle bibliography
        if bibliography_file and Path(bibliography_file).exists():
            bib_content = Path(bibliography_file).read_text()
            bib_file = self.output_dir / "references.bib"
            with open(bib_file, 'w') as f:
                f.write(bib_content)
            latex_files['references.bib'] = bib_content
            logger.info(f"Copied bibliography: {bib_file}")
        
        # Generate bibliography section
        bib_template = self.template_manager.load_template('bibliography')
        bib_section_file = self.output_dir / "bibliography.tex"
        with open(bib_section_file, 'w') as f:
            f.write(bib_template)
        latex_files['bibliography.tex'] = bib_template
        
        logger.info(f"Generated {len(latex_files)} LaTeX files")
        
        return {
            'latex_files': latex_files,
            'main_file': str(main_file),
            'output_directory': str(self.output_dir),
            'sections_processed': list(section_mapping.keys())
        }
    
    def _load_content_sections(self, content_dir: Path) -> Dict[str, str]:
        """Load all content sections from directory."""
        sections = {}
        
        for md_file in content_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                sections[md_file.name] = content
                logger.debug(f"Loaded content section: {md_file.name}")
            except Exception as e:
                logger.error(f"Error loading {md_file}: {e}")
        
        return sections
    
    def compile_to_pdf(self, main_tex_file: str = None, output_name: str = "arxiv_paper") -> Dict[str, Any]:
        """Compile the generated LaTeX to PDF."""
        if main_tex_file is None:
            main_tex_file = str(self.output_dir / "main.tex")
        
        return self.compiler.compile_document(main_tex_file, output_name)


def create_latex_config(
    template_dir: str = "output/arxiv_paper/templates",
    output_dir: str = "output/arxiv_paper/latex",
    **kwargs
) -> LaTeXFormattingConfig:
    """Create LaTeX formatting configuration with defaults."""
    return LaTeXFormattingConfig(
        template_dir=template_dir,
        output_dir=output_dir,
        **kwargs
    )


def generate_arxiv_latex_paper(
    content_dir: str = "output/arxiv_paper/content",
    bibliography_file: str = "output/arxiv_paper/bibliography/references.bib",
    config: LaTeXFormattingConfig = None
) -> Dict[str, Any]:
    """
    Main entry point for generating arXiv LaTeX paper.
    
    Args:
        content_dir: Directory containing markdown content files
        bibliography_file: Path to bibliography file
        config: LaTeX formatting configuration
        
    Returns:
        Dictionary with generation results
    """
    if config is None:
        config = create_latex_config()
    
    generator = ArxivLaTeXGenerator(config)
    
    # Generate LaTeX files
    latex_result = generator.generate_latex_paper(content_dir, bibliography_file)
    
    # Compile to PDF
    pdf_result = generator.compile_to_pdf()
    
    return {
        'latex_generation': latex_result,
        'pdf_compilation': pdf_result,
        'success': pdf_result.get('success', False)
    }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    result = generate_arxiv_latex_paper()
    
    if result['success']:
        print(f"Successfully generated arXiv paper PDF: {result['pdf_compilation']['pdf_path']}")
    else:
        print("Failed to generate PDF")
        print(f"Error: {result['pdf_compilation'].get('error', 'Unknown error')}")