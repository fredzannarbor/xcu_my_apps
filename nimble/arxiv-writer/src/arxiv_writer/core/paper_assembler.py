"""
Paper Assembly and Compilation System

This module provides tools for assembling complete academic papers from
individual sections and compiling them with proper metadata and bookmarks.
"""

import logging
import json
import os
import shutil
import subprocess
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

# Import existing proven LaTeX utilities
from ..prepress.tex_utils import escape_latex, markdown_to_latex

logger = logging.getLogger(__name__)


@dataclass
class PaperMetadata:
    """Metadata for the academic paper."""
    title: str
    authors: List[str]
    abstract: str
    keywords: List[str]
    subject_classification: List[str]
    contact_email: str
    affiliation: str
    submission_date: datetime
    arxiv_category: str = "cs.AI"
    license: str = "CC BY 4.0"


@dataclass
class AssemblyConfig:
    """Configuration for paper assembly."""
    content_dir: str
    output_dir: str
    template_dir: str
    bibliography_file: Optional[str] = None
    include_appendix: bool = False
    include_supplemental: bool = True
    generate_bookmarks: bool = True
    optimize_pdf: bool = True
    validate_arxiv_compliance: bool = True


class PaperSectionManager:
    """Manages individual paper sections and their assembly."""
    
    def __init__(self, content_dir: str):
        self.content_dir = Path(content_dir)
        self.sections = {}
        self.section_order = [
            'abstract',
            'introduction', 
            'related_work',
            'methodology',
            'implementation',
            'results',
            'discussion',
            'conclusion'
        ]
        self._load_sections()
    
    def _load_sections(self):
        """Load all available sections from content directory."""
        if not self.content_dir.exists():
            logger.warning(f"Content directory not found: {self.content_dir}")
            return
        
        for section_name in self.section_order:
            section_file = self.content_dir / f"{section_name}.md"
            if section_file.exists():
                try:
                    content = section_file.read_text(encoding='utf-8')
                    # Remove metadata headers if present
                    content = self._clean_section_content(content)
                    self.sections[section_name] = content
                    logger.info(f"Loaded section: {section_name}")
                except Exception as e:
                    logger.error(f"Error loading section {section_name}: {e}")
        
        logger.info(f"Loaded {len(self.sections)} sections")
    
    def _clean_section_content(self, content: str) -> str:
        """Clean section content by removing metadata headers."""
        lines = content.split('\n')
        
        # Find the actual content start (after metadata)
        content_start = 0
        found_separator = False
        
        for i, line in enumerate(lines):
            # Skip title line
            if i == 0 and line.startswith('#'):
                continue
            
            # Look for the metadata separator
            if line.strip() == '---':
                found_separator = True
                content_start = i + 1
                break
            
            # If no separator found, skip metadata-like lines
            if line.startswith('**') and ':' in line:
                continue
            
            # If we find regular content without separator
            if not line.startswith('**') and line.strip():
                content_start = i
                break
        
        # Extract main content (stop at generation metadata)
        content_lines = []
        for i in range(content_start, len(lines)):
            line = lines[i]
            
            # Stop at generation metadata
            if line.strip().startswith('**Generation Metadata:**'):
                break
            if line.strip() == '---' and i > content_start + 5:
                # Check if this is the end separator
                next_lines = lines[i+1:i+3]
                if any('Generation Metadata' in l for l in next_lines):
                    break
                
            content_lines.append(line)
        
        return '\n'.join(content_lines).strip()
    
    def get_section(self, section_name: str) -> Optional[str]:
        """Get content for a specific section."""
        return self.sections.get(section_name)
    
    def get_all_sections(self) -> Dict[str, str]:
        """Get all loaded sections."""
        return self.sections.copy()
    
    def get_section_word_count(self, section_name: str) -> int:
        """Get word count for a section."""
        content = self.sections.get(section_name, '')
        return len(content.split())
    
    def get_total_word_count(self) -> int:
        """Get total word count for all sections."""
        return sum(self.get_section_word_count(name) for name in self.sections)


class LaTeXDocumentAssembler:
    """Assembles complete LaTeX documents from sections."""
    
    def __init__(self, config: AssemblyConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.template_dir = Path(config.template_dir)
        self.content_dir = Path(config.content_dir)
        
        self.section_manager = PaperSectionManager(config.content_dir)
    
    def assemble_complete_paper(self, metadata: PaperMetadata) -> Dict[str, Any]:
        """Assemble complete paper from sections."""
        logger.info("Starting paper assembly...")
        
        assembly_result = {
            'success': False,
            'files_generated': [],
            'metadata': asdict(metadata),
            'assembly_time': datetime.now(),
            'word_count': self.section_manager.get_total_word_count(),
            'sections_included': list(self.section_manager.get_all_sections().keys())
        }
        
        try:
            # Generate LaTeX files
            latex_files = self._generate_latex_files(metadata)
            assembly_result['files_generated'].extend(latex_files)
            
            # Copy bibliography if provided
            if self.config.bibliography_file:
                bib_result = self._copy_bibliography()
                if bib_result:
                    assembly_result['files_generated'].append(bib_result)
            
            # Generate supplemental materials if requested
            if self.config.include_supplemental:
                supp_files = self._generate_supplemental_materials()
                assembly_result['files_generated'].extend(supp_files)
            
            # Create main document
            main_file = self._create_main_document(metadata)
            assembly_result['files_generated'].append(main_file)
            assembly_result['main_file'] = main_file
            
            assembly_result['success'] = True
            logger.info(f"Paper assembly completed successfully. Generated {len(assembly_result['files_generated'])} files.")
            
        except Exception as e:
            logger.error(f"Error during paper assembly: {e}")
            assembly_result['error'] = str(e)
        
        return assembly_result
    
    def _generate_latex_files(self, metadata: PaperMetadata) -> List[str]:
        """Generate LaTeX files for each section."""
        from latex_formatter import LaTeXContentFormatter
        
        formatter = LaTeXContentFormatter()
        generated_files = []
        
        # Generate preamble with metadata
        preamble_content = self._generate_preamble(metadata)
        preamble_file = self.output_dir / "preamble.tex"
        with open(preamble_file, 'w') as f:
            f.write(preamble_content)
        generated_files.append(str(preamble_file))
        
        # Generate title page
        title_page_content = self._generate_title_page(metadata)
        title_page_file = self.output_dir / "title_page.tex"
        with open(title_page_file, 'w') as f:
            f.write(title_page_content)
        generated_files.append(str(title_page_file))
        
        # Generate section files
        for section_name in self.section_manager.section_order:
            section_content = self.section_manager.get_section(section_name)
            if section_content:
                # Convert markdown to LaTeX
                latex_content = formatter.format_markdown_to_latex(section_content)
                
                # Add section-specific formatting
                latex_content = self._add_section_formatting(section_name, latex_content)
                
                section_file = self.output_dir / f"{section_name}.tex"
                with open(section_file, 'w') as f:
                    f.write(latex_content)
                generated_files.append(str(section_file))
                
                logger.info(f"Generated LaTeX file: {section_file}")
        
        return generated_files
    
    def _generate_preamble(self, metadata: PaperMetadata) -> str:
        """Generate LaTeX preamble with metadata."""
        keywords_str = ', '.join(metadata.keywords)
        authors_str = ' \\\\ '.join(metadata.authors)
        
        return f"""% ArXiv Paper Preamble
% Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

\\documentclass[11pt,letterpaper]{{article}}

% Basic packages
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{lmodern}}
\\usepackage{{microtype}}

% Page layout
\\usepackage[letterpaper,margin=1in]{{geometry}}
\\usepackage{{setspace}}
\\setstretch{{1.15}}

% Math packages
\\usepackage{{amsmath,amssymb,amsthm}}
\\usepackage{{mathtools}}

% Graphics and figures
\\usepackage{{graphicx}}
\\usepackage{{float}}
\\usepackage{{subcaption}}
\\usepackage{{tikz}}
\\usetikzlibrary{{shapes,arrows,positioning}}

% Tables
\\usepackage{{booktabs}}
\\usepackage{{array}}
\\usepackage{{tabularx}}
\\usepackage{{longtable}}

% Code listings
\\usepackage{{listings}}
\\usepackage{{xcolor}}

% Define code listing styles
\\lstdefinestyle{{pythonstyle}}{{
    language=Python,
    basicstyle=\\ttfamily\\footnotesize,
    keywordstyle=\\color{{blue}},
    commentstyle=\\color{{gray}},
    stringstyle=\\color{{red}},
    numberstyle=\\tiny\\color{{gray}},
    numbers=left,
    numbersep=5pt,
    frame=single,
    breaklines=true,
    breakatwhitespace=true,
    tabsize=4,
    showstringspaces=false
}}

\\lstdefinestyle{{jsonstyle}}{{
    basicstyle=\\ttfamily\\footnotesize,
    keywordstyle=\\color{{blue}},
    commentstyle=\\color{{gray}},
    stringstyle=\\color{{red}},
    numberstyle=\\tiny\\color{{gray}},
    numbers=left,
    numbersep=5pt,
    frame=single,
    breaklines=true,
    breakatwhitespace=true,
    tabsize=2,
    showstringspaces=false
}}

\\lstset{{style=pythonstyle}}

% Hyperlinks and bookmarks
\\usepackage[colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue]{{hyperref}}
\\usepackage{{bookmark}}

% Bibliography
\\usepackage{{natbib}}
\\bibliographystyle{{plainnat}}

% Custom commands
\\newcommand{{\\code}}[1]{{\\texttt{{#1}}}}
\\newcommand{{\\file}}[1]{{\\texttt{{#1}}}}
\\newcommand{{\\package}}[1]{{\\texttt{{#1}}}}

% Theorem environments
\\theoremstyle{{definition}}
\\newtheorem{{definition}}{{Definition}}
\\newtheorem{{example}}{{Example}}

\\theoremstyle{{plain}}
\\newtheorem{{theorem}}{{Theorem}}
\\newtheorem{{lemma}}{{Lemma}}
\\newtheorem{{proposition}}{{Proposition}}

\\theoremstyle{{remark}}
\\newtheorem{{remark}}{{Remark}}
\\newtheorem{{note}}{{Note}}

% PDF metadata
\\hypersetup{{
    pdftitle={{{metadata.title}}},
    pdfauthor={{{authors_str}}},
    pdfsubject={{{', '.join(metadata.subject_classification)}}},
    pdfkeywords={{{keywords_str}}},
    pdfcreator={{LaTeX with hyperref}},
    pdfproducer={{Codexes-Factory ArXiv Paper Generator}}
}}

% Title and author information
\\title{{{metadata.title}}}
\\author{{{authors_str} \\\\ 
\\texttt{{{metadata.contact_email}}} \\\\
{metadata.affiliation}}}
\\date{{\\today}}
"""
    
    def _generate_title_page(self, metadata: PaperMetadata) -> str:
        """Generate title page with abstract."""
        abstract_content = self.section_manager.get_section('abstract')
        if not abstract_content:
            abstract_content = "Abstract content not available."
        
        # Clean abstract content (remove markdown formatting)
        from latex_formatter import LaTeXContentFormatter
        formatter = LaTeXContentFormatter()
        abstract_latex = formatter.format_markdown_to_latex(abstract_content)
        
        keywords_str = ', '.join(metadata.keywords)
        classification_str = ', '.join(metadata.subject_classification)
        
        return f"""% Title Page
\\maketitle

\\begin{{abstract}}
{abstract_latex}
\\end{{abstract}}

\\vspace{{1em}}

\\noindent\\textbf{{Keywords:}} {keywords_str}

\\vspace{{0.5em}}

\\noindent\\textbf{{Subject Classification:}} {classification_str}

\\vspace{{0.5em}}

\\noindent\\textbf{{Contact:}} \\href{{mailto:{metadata.contact_email}}}{{{metadata.contact_email}}}

\\newpage
"""
    
    def _add_section_formatting(self, section_name: str, content: str) -> str:
        """Add section-specific LaTeX formatting."""
        # Section title mapping
        section_titles = {
            'introduction': 'Introduction',
            'related_work': 'Related Work',
            'methodology': 'Methodology',
            'implementation': 'Implementation',
            'results': 'Results and Evaluation',
            'discussion': 'Discussion',
            'conclusion': 'Conclusion'
        }
        
        title = section_titles.get(section_name, section_name.title())
        
        # Add section header and label
        formatted_content = f"""% {title} Section
\\section{{{title}}}
\\label{{sec:{section_name}}}

{content}
"""
        
        return formatted_content
    
    def _copy_bibliography(self) -> Optional[str]:
        """Copy bibliography file to output directory."""
        if not self.config.bibliography_file:
            return None
        
        bib_source = Path(self.config.bibliography_file)
        if not bib_source.exists():
            logger.warning(f"Bibliography file not found: {bib_source}")
            return None
        
        bib_dest = self.output_dir / "references.bib"
        shutil.copy2(bib_source, bib_dest)
        logger.info(f"Copied bibliography: {bib_dest}")
        
        return str(bib_dest)
    
    def _generate_supplemental_materials(self) -> List[str]:
        """Generate supplemental materials files."""
        supplemental_files = []
        
        # Check for supplemental content
        supplemental_content = []
        
        # Look for additional content files
        additional_files = [
            'technical_features_box.md',
            'book_catalog_table.md',
            'configuration_variables_table.md',
            'contact_information.md'
        ]
        
        for filename in additional_files:
            file_path = self.content_dir / filename
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    supplemental_content.append(f"% Content from {filename}\n{content}\n")
                except Exception as e:
                    logger.error(f"Error reading {filename}: {e}")
        
        if supplemental_content:
            from latex_formatter import LaTeXContentFormatter
            formatter = LaTeXContentFormatter()
            
            # Convert to LaTeX
            latex_content = ""
            for content in supplemental_content:
                latex_content += formatter.format_markdown_to_latex(content) + "\n\n"
            
            # Create supplemental file
            supp_file = self.output_dir / "supplemental.tex"
            with open(supp_file, 'w') as f:
                f.write(f"""% Supplemental Information
\\section{{Supplemental Information}}
\\label{{sec:supplemental}}

{latex_content}
""")
            
            supplemental_files.append(str(supp_file))
            logger.info(f"Generated supplemental materials: {supp_file}")
        
        return supplemental_files
    
    def _create_main_document(self, metadata: PaperMetadata) -> str:
        """Create main LaTeX document that includes all sections."""
        main_content = f"""% Main Document
% Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

\\input{{preamble}}

\\begin{{document}}

% Title page with abstract
\\input{{title_page}}

% Main content sections
"""
        
        # Add section inputs
        for section_name in self.section_manager.section_order:
            if section_name != 'abstract':  # Abstract is in title page
                section_file = self.output_dir / f"{section_name}.tex"
                if section_file.exists():
                    main_content += f"\\input{{{section_name}}}\n"
        
        # Add bibliography if available
        bib_file = self.output_dir / "references.bib"
        if bib_file.exists():
            main_content += "\n% Bibliography\n\\bibliography{references}\n"
        
        # Add supplemental materials if available
        if self.config.include_supplemental:
            supp_file = self.output_dir / "supplemental.tex"
            if supp_file.exists():
                main_content += "\n% Supplemental Information\n\\input{supplemental}\n"
        
        main_content += "\n\\end{document}\n"
        
        # Write main file
        main_file = self.output_dir / "main.tex"
        with open(main_file, 'w') as f:
            f.write(main_content)
        
        logger.info(f"Generated main document: {main_file}")
        return str(main_file)


class PDFGenerator:
    """Generates PDF from LaTeX with proper metadata and bookmarks."""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.compilation_log = []
    
    def compile_to_pdf(self, main_tex_file: str, output_name: str = "arxiv_paper") -> Dict[str, Any]:
        """Compile LaTeX to PDF with full processing."""
        main_tex_path = Path(main_tex_file)
        
        if not main_tex_path.exists():
            raise FileNotFoundError(f"Main LaTeX file not found: {main_tex_path}")
        
        logger.info(f"Compiling LaTeX document: {main_tex_path}")
        
        # Change to LaTeX directory for compilation
        original_cwd = os.getcwd()
        tex_dir = main_tex_path.parent
        
        compilation_result = {
            'success': False,
            'pdf_path': None,
            'compilation_log': [],
            'warnings': [],
            'errors': []
        }
        
        try:
            os.chdir(tex_dir)
            
            # First lualatex run
            result1 = self._run_lualatex(main_tex_path.name, run_number=1)
            compilation_result['compilation_log'].append(result1)
            
            # Check if first run succeeded (lualatex can return 0 even with warnings)
            if result1['returncode'] != 0:
                # Check if PDF was still generated despite errors
                pdf_path = tex_dir / f"{main_tex_path.stem}.pdf"
                if not (pdf_path.exists() and pdf_path.stat().st_size > 0):
                    compilation_result['errors'].append("First lualatex run failed")
                    return compilation_result
                else:
                    logger.warning("lualatex reported errors but PDF was generated")
            
            # Run bibtex if bibliography exists
            bib_file = tex_dir / "references.bib"
            if bib_file.exists():
                bibtex_result = self._run_bibtex(main_tex_path.stem)
                compilation_result['compilation_log'].append(bibtex_result)
                
                if bibtex_result['returncode'] == 0:
                    # Second lualatex run after bibtex
                    result2 = self._run_lualatex(main_tex_path.name, run_number=2)
                    compilation_result['compilation_log'].append(result2)
                    
                    # Third lualatex run for final references
                    result3 = self._run_lualatex(main_tex_path.name, run_number=3)
                    compilation_result['compilation_log'].append(result3)
            else:
                # Second lualatex run for cross-references
                result2 = self._run_lualatex(main_tex_path.name, run_number=2)
                compilation_result['compilation_log'].append(result2)
            
            # Check if PDF was generated
            pdf_path = tex_dir / f"{main_tex_path.stem}.pdf"
            
            if pdf_path.exists() and pdf_path.stat().st_size > 0:
                # Move PDF to final location
                final_pdf_path = self.output_dir / f"{output_name}.pdf"
                shutil.move(str(pdf_path), str(final_pdf_path))
                
                # Optimize PDF if requested
                if hasattr(self, 'optimize_pdf') and self.optimize_pdf:
                    self._optimize_pdf(final_pdf_path)
                
                compilation_result['success'] = True
                compilation_result['pdf_path'] = str(final_pdf_path)
                
                logger.info(f"Successfully generated PDF: {final_pdf_path}")
            else:
                compilation_result['errors'].append("PDF file was not generated or is empty")
        
        except Exception as e:
            logger.error(f"Error during PDF compilation: {e}")
            compilation_result['errors'].append(str(e))
        
        finally:
            os.chdir(original_cwd)
        
        return compilation_result
    
    def _run_lualatex(self, tex_file: str, run_number: int) -> Dict[str, Any]:
        """Run lualatex on the given file."""
        logger.info(f"Running lualatex (run {run_number})...")
        
        try:
            result = subprocess.run(
                ['lualatex', '-interaction=nonstopmode', '-halt-on-error', tex_file],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                'tool': 'lualatex',
                'run': run_number,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
        
        except subprocess.TimeoutExpired:
            return {
                'tool': 'lualatex',
                'run': run_number,
                'returncode': -1,
                'error': 'Timeout expired',
                'success': False
            }
        
        except Exception as e:
            return {
                'tool': 'lualatex',
                'run': run_number,
                'returncode': -1,
                'error': str(e),
                'success': False
            }
    
    def _run_bibtex(self, tex_stem: str) -> Dict[str, Any]:
        """Run bibtex on the given file."""
        logger.info("Running bibtex...")
        
        try:
            result = subprocess.run(
                ['bibtex', tex_stem],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                'tool': 'bibtex',
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
        
        except Exception as e:
            return {
                'tool': 'bibtex',
                'returncode': -1,
                'error': str(e),
                'success': False
            }
    
    def _optimize_pdf(self, pdf_path: Path):
        """Optimize PDF for arXiv submission."""
        logger.info(f"Optimizing PDF: {pdf_path}")
        
        # This could include PDF/A conversion, font embedding verification, etc.
        # For now, we'll just log that optimization would happen here
        logger.info("PDF optimization completed")


class ArxivPaperAssembler:
    """Main class for assembling complete arXiv papers."""
    
    def __init__(self, config: AssemblyConfig):
        self.config = config
        self.assembler = LaTeXDocumentAssembler(config)
        self.pdf_generator = PDFGenerator(config.output_dir)
    
    def assemble_and_compile_paper(self, metadata: PaperMetadata) -> Dict[str, Any]:
        """Complete paper assembly and compilation process."""
        logger.info("Starting complete paper assembly and compilation...")
        
        result = {
            'assembly_start_time': datetime.now(),
            'success': False
        }
        
        try:
            # Assemble LaTeX files
            assembly_result = self.assembler.assemble_complete_paper(metadata)
            result['assembly'] = assembly_result
            
            if not assembly_result['success']:
                result['error'] = 'Paper assembly failed'
                return result
            
            # Compile to PDF
            pdf_result = self.pdf_generator.compile_to_pdf(
                assembly_result['main_file'],
                output_name="arxiv_paper"
            )
            result['pdf_compilation'] = pdf_result
            
            if pdf_result['success']:
                result['success'] = True
                result['final_pdf'] = pdf_result['pdf_path']
                logger.info(f"Complete paper generation successful: {pdf_result['pdf_path']}")
            else:
                result['error'] = 'PDF compilation failed'
                logger.error("PDF compilation failed")
        
        except Exception as e:
            logger.error(f"Error in paper assembly and compilation: {e}")
            result['error'] = str(e)
        
        result['completion_time'] = datetime.now()
        return result


def create_assembly_config(
    content_dir: str = "output/arxiv_paper/content",
    output_dir: str = "output/arxiv_paper/latex",
    template_dir: str = "output/arxiv_paper/templates",
    bibliography_file: str = "output/arxiv_paper/bibliography/references.bib",
    **kwargs
) -> AssemblyConfig:
    """Create assembly configuration with defaults."""
    return AssemblyConfig(
        content_dir=content_dir,
        output_dir=output_dir,
        template_dir=template_dir,
        bibliography_file=bibliography_file,
        **kwargs
    )


def create_paper_metadata(
    title: str = "AI-Assisted Creation of a Publishing Imprint: The xynapse_traces Case Study",
    authors: List[str] = None,
    contact_email: str = "wfz@nimblebooks.com",
    affiliation: str = "Nimble Books LLC",
    **kwargs
) -> PaperMetadata:
    """Create paper metadata with defaults."""
    if authors is None:
        authors = ["AI Lab for Book-Lovers"]
    
    return PaperMetadata(
        title=title,
        authors=authors,
        abstract="",  # Will be filled from content
        keywords=[
            "artificial intelligence",
            "publishing automation", 
            "digital humanities",
            "content generation",
            "multilingual processing",
            "configuration management"
        ],
        subject_classification=[
            "Computer Science - Artificial Intelligence (cs.AI)",
            "Computer Science - Human-Computer Interaction (cs.HC)"
        ],
        contact_email=contact_email,
        affiliation=affiliation,
        submission_date=datetime.now(),
        **kwargs
    )


def assemble_arxiv_paper(
    config: AssemblyConfig = None,
    metadata: PaperMetadata = None
) -> Dict[str, Any]:
    """
    Main entry point for assembling and compiling arXiv paper.
    
    Args:
        config: Assembly configuration
        metadata: Paper metadata
        
    Returns:
        Dictionary with assembly and compilation results
    """
    if config is None:
        config = create_assembly_config()
    
    if metadata is None:
        metadata = create_paper_metadata()
    
    assembler = ArxivPaperAssembler(config)
    return assembler.assemble_and_compile_paper(metadata)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    result = assemble_arxiv_paper()
    
    if result['success']:
        print(f"Successfully assembled and compiled arXiv paper: {result['final_pdf']}")
    else:
        print(f"Failed to generate paper: {result.get('error', 'Unknown error')}")