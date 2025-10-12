"""
Content extraction framework for LLM-ready training data generation.

This module implements the Karpathy strategy for converting academic papers
into LLM training data by extracting content, figures, and creating structured
examples for supervised fine-tuning and reinforcement learning.
"""

import re
import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import base64

try:
    import fitz  # PyMuPDF for PDF processing
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


@dataclass
class ExtractedFigure:
    """Represents an extracted figure from a document."""
    figure_id: str
    caption: str
    file_path: str
    page_number: Optional[int] = None
    bbox: Optional[Tuple[float, float, float, float]] = None  # x0, y0, x1, y1
    figure_type: str = "image"  # image, table, diagram
    references: List[str] = field(default_factory=list)  # Where it's referenced in text
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SFTExample:
    """Supervised Fine-Tuning example extracted from well-executed analysis."""
    example_id: str
    context: str
    analysis_passage: str
    conclusion: str
    section_type: str  # methodology, results, discussion, etc.
    quality_score: float = 0.0
    figures_referenced: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RLExample:
    """Reinforcement Learning environment example from case studies."""
    example_id: str
    case_study_title: str
    problem_description: str
    methodology: str
    results: str
    lessons_learned: str
    figures_referenced: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Result of content extraction process."""
    markdown_content: str
    figures: List[ExtractedFigure] = field(default_factory=list)
    sft_examples: List[SFTExample] = field(default_factory=list)
    rl_examples: List[RLExample] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    extraction_summary: Dict[str, Any] = field(default_factory=dict)


class ContentExtractor:
    """
    Main content extraction class implementing the Karpathy strategy.
    
    Converts LaTeX/PDF documents to LLM-ready training data by:
    1. Converting content to markdown with preserved styling
    2. Extracting figures as separate files
    3. Identifying well-executed analysis for SFT examples
    4. Extracting case studies for RL environment examples
    """
    
    def __init__(self, output_dir: str = "extracted_content"):
        """
        Initialize the content extractor.
        
        Args:
            output_dir: Directory to save extracted content and figures
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.figures_dir = self.output_dir / "figures"
        self.figures_dir.mkdir(exist_ok=True)
        
        self.examples_dir = self.output_dir / "examples"
        self.examples_dir.mkdir(exist_ok=True)
        
        # Patterns for identifying different content types
        self.analysis_patterns = [
            r"(?i)(analysis|evaluation|assessment|examination)\s+(?:shows?|reveals?|demonstrates?|indicates?)",
            r"(?i)(results?\s+(?:show|indicate|demonstrate|reveal))",
            r"(?i)(we\s+(?:found|observed|discovered|determined))",
            r"(?i)(this\s+(?:suggests?|implies?|indicates?))",
            r"(?i)(therefore|thus|consequently|as\s+a\s+result)",
        ]
        
        self.case_study_patterns = [
            r"(?i)(case\s+study|example|illustration|instance)",
            r"(?i)(consider\s+the\s+(?:following|case|example))",
            r"(?i)(for\s+(?:example|instance))",
            r"(?i)(to\s+illustrate)",
        ]
        
        # LaTeX to markdown conversion patterns
        self.latex_to_md_patterns = [
            (r'\\textbf\{([^}]+)\}', r'**\1**'),  # Bold
            (r'\\textit\{([^}]+)\}', r'*\1*'),    # Italic
            (r'\\emph\{([^}]+)\}', r'*\1*'),      # Emphasis
            (r'\\texttt\{([^}]+)\}', r'`\1`'),    # Code/monospace
            (r'\\section\{([^}]+)\}', r'# \1'),   # Section headers
            (r'\\subsection\{([^}]+)\}', r'## \1'), # Subsection headers
            (r'\\subsubsection\{([^}]+)\}', r'### \1'), # Subsubsection headers
            (r'\\paragraph\{([^}]+)\}', r'#### \1'), # Paragraph headers
            (r'\\cite\{([^}]+)\}', r'[\1]'),      # Citations
            (r'\\ref\{([^}]+)\}', r'[ref:\1]'),   # References
            (r'\\label\{([^}]+)\}', r''),         # Remove labels
        ]
    
    def extract_from_latex(self, latex_file: Union[str, Path]) -> ExtractionResult:
        """
        Extract content from LaTeX file.
        
        Args:
            latex_file: Path to LaTeX file
            
        Returns:
            ExtractionResult with extracted content and examples
        """
        latex_path = Path(latex_file)
        if not latex_path.exists():
            raise FileNotFoundError(f"LaTeX file not found: {latex_path}")
        
        with open(latex_path, 'r', encoding='utf-8') as f:
            latex_content = f.read()
        
        # Convert LaTeX to markdown
        markdown_content = self._latex_to_markdown(latex_content)
        
        # Extract figures from LaTeX
        figures = self._extract_figures_from_latex(latex_content, latex_path.parent)
        
        # Extract SFT examples
        sft_examples = self._extract_sft_examples(markdown_content, figures)
        
        # Extract RL examples
        rl_examples = self._extract_rl_examples(markdown_content, figures)
        
        # Create extraction summary
        extraction_summary = {
            "source_file": str(latex_path),
            "extraction_date": datetime.now().isoformat(),
            "total_figures": len(figures),
            "sft_examples": len(sft_examples),
            "rl_examples": len(rl_examples),
            "markdown_length": len(markdown_content)
        }
        
        return ExtractionResult(
            markdown_content=markdown_content,
            figures=figures,
            sft_examples=sft_examples,
            rl_examples=rl_examples,
            extraction_summary=extraction_summary
        )
    
    def extract_from_pdf(self, pdf_file: Union[str, Path]) -> ExtractionResult:
        """
        Extract content from PDF file.
        
        Args:
            pdf_file: Path to PDF file
            
        Returns:
            ExtractionResult with extracted content and examples
        """
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF is required for PDF extraction. Install with: pip install PyMuPDF")
        
        pdf_path = Path(pdf_file)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Open PDF document
        doc = fitz.open(str(pdf_path))
        
        # Extract text content
        full_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            full_text += page.get_text()
        
        # Convert to markdown (basic conversion for PDF text)
        markdown_content = self._clean_pdf_text_to_markdown(full_text)
        
        # Extract figures from PDF
        figures = self._extract_figures_from_pdf(doc, pdf_path.stem)
        
        # Extract SFT examples
        sft_examples = self._extract_sft_examples(markdown_content, figures)
        
        # Extract RL examples
        rl_examples = self._extract_rl_examples(markdown_content, figures)
        
        # Close PDF document
        doc.close()
        
        # Create extraction summary
        extraction_summary = {
            "source_file": str(pdf_path),
            "extraction_date": datetime.now().isoformat(),
            "total_pages": len(doc),
            "total_figures": len(figures),
            "sft_examples": len(sft_examples),
            "rl_examples": len(rl_examples),
            "markdown_length": len(markdown_content)
        }
        
        return ExtractionResult(
            markdown_content=markdown_content,
            figures=figures,
            sft_examples=sft_examples,
            rl_examples=rl_examples,
            extraction_summary=extraction_summary
        )
    
    def _latex_to_markdown(self, latex_content: str) -> str:
        """
        Convert LaTeX content to markdown format.
        
        Args:
            latex_content: Raw LaTeX content
            
        Returns:
            Markdown formatted content
        """
        markdown = latex_content
        
        # Apply LaTeX to markdown conversion patterns
        for latex_pattern, md_replacement in self.latex_to_md_patterns:
            markdown = re.sub(latex_pattern, md_replacement, markdown)
        
        # Handle tables
        markdown = self._convert_latex_tables(markdown)
        
        # Handle lists
        markdown = self._convert_latex_lists(markdown)
        
        # Clean up extra whitespace and formatting
        markdown = self._clean_markdown(markdown)
        
        return markdown
    
    def _convert_latex_tables(self, content: str) -> str:
        """Convert LaTeX tables to markdown tables."""
        # Simple table conversion - this is a basic implementation
        # More sophisticated parsing would be needed for complex tables
        
        # Find tabular environments
        table_pattern = r'\\begin\{tabular\}.*?\\end\{tabular\}'
        tables = re.findall(table_pattern, content, re.DOTALL)
        
        for table in tables:
            # Split table into lines and process each line
            lines = table.split('\n')
            md_table = []
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines, hline commands, and begin/end statements
                if (not line or 
                    '\\hline' in line or 
                    '\\begin{tabular}' in line or 
                    '\\end{tabular}' in line):
                    continue
                
                # Check if line ends with \\
                if line.endswith('\\\\'):
                    # Remove the \\ and process as table row
                    row_content = line[:-2].strip()
                    
                    # Split by & and clean up
                    cells = [cell.strip() for cell in row_content.split('&')]
                    cells = [cell for cell in cells if cell]  # Remove empty cells
                    
                    if cells:  # Only add non-empty rows
                        md_row = '| ' + ' | '.join(cells) + ' |'
                        md_table.append(md_row)
                        
                        # Add header separator after first row
                        if len(md_table) == 1:
                            separator = '|' + '---|' * len(cells)
                            md_table.append(separator)
            
            if md_table:
                md_table_str = '\n'.join(md_table)
                content = content.replace(table, md_table_str)
        
        return content
    
    def _convert_latex_lists(self, content: str) -> str:
        """Convert LaTeX lists to markdown lists."""
        # Convert itemize environments
        content = re.sub(r'\\begin\{itemize\}', '', content)
        content = re.sub(r'\\end\{itemize\}', '', content)
        content = re.sub(r'\\item\s+', '- ', content)
        
        # Convert enumerate environments
        content = re.sub(r'\\begin\{enumerate\}', '', content)
        content = re.sub(r'\\end\{enumerate\}', '', content)
        
        # For enumerate, we'd need more sophisticated handling to maintain numbering
        # For now, convert to bullet points
        content = re.sub(r'\\item\s+', '1. ', content)
        
        return content
    
    def _clean_markdown(self, content: str) -> str:
        """Clean up markdown content."""
        # Remove LaTeX comments
        content = re.sub(r'%.*$', '', content, flags=re.MULTILINE)
        
        # Remove extra whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Remove remaining LaTeX commands that weren't converted
        content = re.sub(r'\\[a-zA-Z]+\*?\{[^}]*\}', '', content)
        content = re.sub(r'\\[a-zA-Z]+\*?', '', content)
        
        return content.strip()
    
    def _clean_pdf_text_to_markdown(self, pdf_text: str) -> str:
        """Clean and format PDF extracted text to markdown."""
        # Basic cleaning for PDF text
        lines = pdf_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect headers (simple heuristic: short lines in all caps or title case)
            if len(line) < 100 and (line.isupper() or line.istitle()):
                # Determine header level based on context
                if any(word in line.lower() for word in ['abstract', 'introduction', 'conclusion']):
                    line = f"# {line}"
                elif any(word in line.lower() for word in ['method', 'result', 'discussion']):
                    line = f"## {line}"
                else:
                    line = f"### {line}"
            
            cleaned_lines.append(line)
        
        return '\n\n'.join(cleaned_lines)
    
    def _extract_figures_from_latex(self, latex_content: str, base_dir: Path) -> List[ExtractedFigure]:
        """Extract figure information from LaTeX content."""
        figures = []
        
        # Find figure environments
        figure_pattern = r'\\begin\{figure\}.*?\\end\{figure\}'
        figure_matches = re.findall(figure_pattern, latex_content, re.DOTALL)
        
        for i, figure_match in enumerate(figure_matches):
            # Extract caption
            caption_match = re.search(r'\\caption\{([^}]+)\}', figure_match)
            caption = caption_match.group(1) if caption_match else f"Figure {i+1}"
            
            # Extract includegraphics
            graphics_match = re.search(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', figure_match)
            if graphics_match:
                image_path = graphics_match.group(1)
                
                # Try to find the actual image file
                possible_extensions = ['.png', '.jpg', '.jpeg', '.pdf', '.eps']
                actual_path = None
                
                for ext in possible_extensions:
                    test_path = base_dir / f"{image_path}{ext}"
                    if test_path.exists():
                        actual_path = test_path
                        break
                    
                    # Try without adding extension
                    test_path = base_dir / image_path
                    if test_path.exists():
                        actual_path = test_path
                        break
                
                if actual_path:
                    # Copy figure to output directory
                    figure_id = f"fig_{i+1:03d}"
                    output_path = self.figures_dir / f"{figure_id}{actual_path.suffix}"
                    
                    try:
                        import shutil
                        shutil.copy2(actual_path, output_path)
                        
                        figure = ExtractedFigure(
                            figure_id=figure_id,
                            caption=caption,
                            file_path=str(output_path),
                            figure_type="image",
                            metadata={"original_path": str(actual_path)}
                        )
                        figures.append(figure)
                    except Exception as e:
                        print(f"Warning: Could not copy figure {actual_path}: {e}")
        
        return figures
    
    def _extract_figures_from_pdf(self, doc, pdf_name: str) -> List[ExtractedFigure]:
        """Extract figures from PDF document."""
        if not HAS_PIL:
            print("Warning: PIL not available, skipping figure extraction")
            return []
        
        figures = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # Get image data
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        figure_id = f"fig_{page_num+1:03d}_{img_index+1:03d}"
                        output_path = self.figures_dir / f"{figure_id}.png"
                        
                        pix.save(str(output_path))
                        
                        figure = ExtractedFigure(
                            figure_id=figure_id,
                            caption=f"Figure from page {page_num+1}",
                            file_path=str(output_path),
                            page_number=page_num + 1,
                            figure_type="image",
                            metadata={"pdf_source": pdf_name}
                        )
                        figures.append(figure)
                    
                    pix = None  # Free memory
                    
                except Exception as e:
                    print(f"Warning: Could not extract image {img_index} from page {page_num}: {e}")
        
        return figures
    
    def _extract_sft_examples(self, content: str, figures: List[ExtractedFigure]) -> List[SFTExample]:
        """Extract supervised fine-tuning examples from well-executed analysis passages."""
        sft_examples = []
        
        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        for i, paragraph in enumerate(paragraphs):
            # Check if paragraph contains analysis patterns
            analysis_score = 0
            for pattern in self.analysis_patterns:
                if re.search(pattern, paragraph):
                    analysis_score += 1
            
            # If paragraph shows signs of analysis, create SFT example
            if analysis_score >= 2 and len(paragraph) > 100:
                # Get context (previous paragraph)
                context = paragraphs[i-1] if i > 0 else ""
                
                # Try to find conclusion (next paragraph or end of current)
                conclusion = ""
                if i < len(paragraphs) - 1:
                    next_para = paragraphs[i+1]
                    if any(word in next_para.lower() for word in ['therefore', 'thus', 'consequently', 'conclusion']):
                        conclusion = next_para
                
                # Determine section type
                section_type = self._determine_section_type(paragraph)
                
                # Find referenced figures
                referenced_figures = []
                for figure in figures:
                    if figure.figure_id in paragraph or f"Figure {figure.figure_id[-1]}" in paragraph:
                        referenced_figures.append(figure.figure_id)
                
                example = SFTExample(
                    example_id=f"sft_{len(sft_examples)+1:03d}",
                    context=context,
                    analysis_passage=paragraph,
                    conclusion=conclusion,
                    section_type=section_type,
                    quality_score=min(analysis_score / len(self.analysis_patterns), 1.0),
                    figures_referenced=referenced_figures
                )
                sft_examples.append(example)
        
        return sft_examples
    
    def _extract_rl_examples(self, content: str, figures: List[ExtractedFigure]) -> List[RLExample]:
        """Extract reinforcement learning examples from case studies and illustrations."""
        rl_examples = []
        
        # Split content into sections
        sections = re.split(r'\n#+\s+', content)
        
        for section in sections:
            # Check if section contains case study patterns
            case_study_score = 0
            for pattern in self.case_study_patterns:
                if re.search(pattern, section):
                    case_study_score += 1
            
            # If section shows signs of case study, create RL example
            if case_study_score >= 1 and len(section) > 200:
                lines = section.split('\n')
                # Extract title from first line, looking for case study indicators
                title = ""
                for line in lines:
                    line = line.strip()
                    if line and any(indicator in line.lower() for indicator in ['case study', 'example', 'illustration']):
                        title = line
                        break
                
                if not title:
                    title = f"Case Study {len(rl_examples)+1}"
                
                # Extract different parts of the case study
                problem_desc = self._extract_problem_description(section)
                methodology = self._extract_methodology(section)
                results = self._extract_results(section)
                lessons = self._extract_lessons_learned(section)
                
                # Find referenced figures
                referenced_figures = []
                for figure in figures:
                    if figure.figure_id in section or f"Figure {figure.figure_id[-1]}" in section:
                        referenced_figures.append(figure.figure_id)
                
                example = RLExample(
                    example_id=f"rl_{len(rl_examples)+1:03d}",
                    case_study_title=title,
                    problem_description=problem_desc,
                    methodology=methodology,
                    results=results,
                    lessons_learned=lessons,
                    figures_referenced=referenced_figures
                )
                rl_examples.append(example)
        
        return rl_examples
    
    def _determine_section_type(self, text: str) -> str:
        """Determine the type of section based on content."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['conclude', 'conclusion', 'summary', 'final']):
            return "conclusion"
        elif any(word in text_lower for word in ['method', 'approach', 'algorithm']):
            return "methodology"
        elif any(word in text_lower for word in ['result', 'finding', 'outcome']):
            return "results"
        elif any(word in text_lower for word in ['discuss', 'interpret', 'implication']):
            return "discussion"
        else:
            return "analysis"
    
    def _extract_problem_description(self, text: str) -> str:
        """Extract problem description from case study text."""
        # Look for problem-related keywords and extract surrounding context
        problem_keywords = ['problem', 'challenge', 'issue', 'difficulty', 'question']
        
        sentences = re.split(r'[.!?]+', text)
        problem_sentences = []
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in problem_keywords):
                problem_sentences.append(sentence.strip())
        
        return '. '.join(problem_sentences[:3])  # Take first 3 relevant sentences
    
    def _extract_methodology(self, text: str) -> str:
        """Extract methodology from case study text."""
        method_keywords = ['method', 'approach', 'technique', 'procedure', 'process']
        
        sentences = re.split(r'[.!?]+', text)
        method_sentences = []
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in method_keywords):
                method_sentences.append(sentence.strip())
        
        return '. '.join(method_sentences[:3])
    
    def _extract_results(self, text: str) -> str:
        """Extract results from case study text."""
        result_keywords = ['result', 'outcome', 'finding', 'showed', 'demonstrated']
        
        sentences = re.split(r'[.!?]+', text)
        result_sentences = []
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in result_keywords):
                result_sentences.append(sentence.strip())
        
        return '. '.join(result_sentences[:3])
    
    def _extract_lessons_learned(self, text: str) -> str:
        """Extract lessons learned from case study text."""
        lesson_keywords = ['lesson', 'learn', 'insight', 'takeaway', 'conclusion', 'implication']
        
        sentences = re.split(r'[.!?]+', text)
        lesson_sentences = []
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in lesson_keywords):
                lesson_sentences.append(sentence.strip())
        
        return '. '.join(lesson_sentences[:3])
    
    def save_extraction_result(self, result: ExtractionResult, filename: str = "extraction_result") -> str:
        """
        Save extraction result to files.
        
        Args:
            result: ExtractionResult to save
            filename: Base filename for output files
            
        Returns:
            Path to the main output file
        """
        # Save markdown content
        md_file = self.output_dir / f"{filename}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(result.markdown_content)
        
        # Save SFT examples
        if result.sft_examples:
            sft_file = self.examples_dir / f"{filename}_sft_examples.json"
            sft_data = [
                {
                    "example_id": ex.example_id,
                    "context": ex.context,
                    "analysis_passage": ex.analysis_passage,
                    "conclusion": ex.conclusion,
                    "section_type": ex.section_type,
                    "quality_score": ex.quality_score,
                    "figures_referenced": ex.figures_referenced,
                    "metadata": ex.metadata
                }
                for ex in result.sft_examples
            ]
            
            with open(sft_file, 'w', encoding='utf-8') as f:
                json.dump(sft_data, f, indent=2, ensure_ascii=False)
        
        # Save RL examples
        if result.rl_examples:
            rl_file = self.examples_dir / f"{filename}_rl_examples.json"
            rl_data = [
                {
                    "example_id": ex.example_id,
                    "case_study_title": ex.case_study_title,
                    "problem_description": ex.problem_description,
                    "methodology": ex.methodology,
                    "results": ex.results,
                    "lessons_learned": ex.lessons_learned,
                    "figures_referenced": ex.figures_referenced,
                    "metadata": ex.metadata
                }
                for ex in result.rl_examples
            ]
            
            with open(rl_file, 'w', encoding='utf-8') as f:
                json.dump(rl_data, f, indent=2, ensure_ascii=False)
        
        # Save figures metadata
        if result.figures:
            figures_file = self.output_dir / f"{filename}_figures.json"
            figures_data = [
                {
                    "figure_id": fig.figure_id,
                    "caption": fig.caption,
                    "file_path": fig.file_path,
                    "page_number": fig.page_number,
                    "bbox": fig.bbox,
                    "figure_type": fig.figure_type,
                    "references": fig.references,
                    "metadata": fig.metadata
                }
                for fig in result.figures
            ]
            
            with open(figures_file, 'w', encoding='utf-8') as f:
                json.dump(figures_data, f, indent=2, ensure_ascii=False)
        
        # Save extraction summary
        summary_file = self.output_dir / f"{filename}_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(result.extraction_summary, f, indent=2, ensure_ascii=False)
        
        return str(md_file)