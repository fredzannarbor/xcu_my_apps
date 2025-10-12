"""
Main ArXiv paper generator class.
"""

from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import logging
import time
from datetime import datetime

from .exceptions import ArxivWriterError, GenerationError, TemplateError, ValidationError
from .models import PaperConfig, PaperResult, Section, SectionConfig, GenerationSummary, ValidationResult, LLMConfig
from .context_collector import ContextCollector, ContextConfig
from .section_generator import SectionGenerator, create_standard_section_configs
from ..templates.manager import TemplateManager

logger = logging.getLogger(__name__)


class ArxivPaperGenerator:
    """
    Main class for generating academic papers in arXiv format.
    
    This class orchestrates the paper generation process, including:
    - Loading and validating configuration
    - Collecting context data
    - Generating paper sections using LLMs
    - Assembling the final paper
    - Compiling to PDF if requested
    """
    
    def __init__(self, config: PaperConfig):
        """
        Initialize the paper generator.
        
        Args:
            config: Paper generation configuration
        """
        self.config = config
        self._validate_config()
        
        # Initialize components
        self.template_manager = TemplateManager(self.config.templates.__dict__)
        self.section_generator = SectionGenerator(self.config.llm, self.template_manager)
        
        # Context collector will be initialized when needed
        self._context_collector = None
        
        logger.info("ArxivPaperGenerator initialized")
    
    def _validate_config(self) -> None:
        """Validate the configuration."""
        if not isinstance(self.config, PaperConfig):
            raise GenerationError("Invalid configuration type")
        
        # Validate required configuration sections
        if not hasattr(self.config, 'llm') or not isinstance(self.config.llm, LLMConfig):
            raise GenerationError("Invalid or missing LLM configuration")
        
        if not hasattr(self.config, 'templates'):
            raise GenerationError("Missing template configuration")
        
        if not hasattr(self.config, 'output'):
            raise GenerationError("Missing output configuration")
        
        logger.debug("Configuration validated")
    
    def generate_paper(
        self,
        context_data: Optional[Dict[str, Any]] = None,
        section_configs: Optional[List[SectionConfig]] = None,
        output_dir: Optional[str] = None,
        compile_pdf: bool = False
    ) -> PaperResult:
        """
        Generate a complete academic paper.
        
        Args:
            context_data: Context data for paper generation (optional, will collect if not provided)
            section_configs: Section configurations (optional, will use standard if not provided)
            output_dir: Output directory path
            compile_pdf: Whether to compile LaTeX to PDF
            
        Returns:
            Paper generation result
            
        Raises:
            GenerationError: If paper generation fails
        """
        try:
            logger.info("Starting paper generation")
            start_time = time.time()
            
            # Set output directory
            if output_dir is None:
                output_dir = self.config.output_dir or "output"
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Collect context data if not provided
            if context_data is None:
                context_data = self._collect_context()
            
            # Use standard section configs if not provided
            if section_configs is None:
                section_configs = create_standard_section_configs()
            
            # Generate sections
            sections_result = self._generate_sections(section_configs, context_data)
            
            # Assemble paper
            paper_content = self._assemble_paper(sections_result, context_data)
            
            # Write output files
            output_files = self._write_output_files(paper_content, output_path, compile_pdf)
            
            # Create generation summary
            generation_time = time.time() - start_time
            summary = self._create_generation_summary(sections_result, generation_time)
            
            # Create result
            result = PaperResult(
                success=True,
                output_path=output_files.get("latex") or output_files.get("markdown"),
                pdf_path=output_files.get("pdf"),
                sections_generated=list(sections_result.keys()),
                generation_time=generation_time,
                word_count=sum(s.word_count for s in sections_result.values() if isinstance(s, Section)),
                validation_results={},
                summary=summary
            )
            
            logger.info(f"Paper generation completed: {result.output_path} ({result.word_count} words, {generation_time:.2f}s)")
            return result
            
        except Exception as e:
            logger.error(f"Paper generation failed: {e}")
            raise GenerationError(f"Failed to generate paper: {e}") from e
    
    def generate_section(
        self,
        section_config: SectionConfig,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Section:
        """
        Generate a single paper section.
        
        Args:
            section_config: Configuration for the section to generate
            context_data: Context data for section generation
            
        Returns:
            Generated Section object
        """
        if context_data is None:
            context_data = self._collect_context()
        
        return self.section_generator.generate_section(section_config, context_data)
    
    def _collect_context(self) -> Dict[str, Any]:
        """Collect context data for paper generation."""
        if self._context_collector is None:
            # Create default context collector configuration
            context_config = ContextConfig(
                sources=[],  # No default sources, will be empty context
                validation_enabled=False
            )
            self._context_collector = ContextCollector(context_config)
        
        return self._context_collector.collect_context()
    
    def _generate_sections(
        self,
        section_configs: List[SectionConfig],
        context_data: Dict[str, Any]
    ) -> Dict[str, Union[Section, Exception]]:
        """
        Generate all paper sections.
        
        Args:
            section_configs: List of section configurations
            context_data: Context data for section generation
            
        Returns:
            Dictionary mapping section names to Section objects or exceptions
        """
        logger.info(f"Generating {len(section_configs)} sections")
        
        # Filter to only required sections if validation is enabled
        if self.config.validation.enabled:
            required_sections = [config for config in section_configs if config.required]
            if required_sections != section_configs:
                logger.info(f"Filtering to {len(required_sections)} required sections")
                section_configs = required_sections
        
        # Generate sections
        return self.section_generator.generate_multiple_sections(
            section_configs,
            context_data,
            continue_on_error=True
        )
    
    def _assemble_paper(
        self,
        sections_result: Dict[str, Union[Section, Exception]],
        context_data: Dict[str, Any]
    ) -> str:
        """
        Assemble sections into a complete paper.
        
        Args:
            sections_result: Generated sections
            context_data: Context data
            
        Returns:
            Complete paper content as string
        """
        logger.info("Assembling paper from sections")
        
        # Extract successful sections
        sections = {name: section for name, section in sections_result.items() 
                   if isinstance(section, Section)}
        
        if not sections:
            raise GenerationError("No sections were successfully generated")
        
        # Create paper header
        paper_parts = []
        
        # Add title and metadata
        if self.config.paper_title:
            paper_parts.append(f"# {self.config.paper_title}\n")
        
        if self.config.authors:
            authors_str = ", ".join(self.config.authors)
            paper_parts.append(f"**Authors:** {authors_str}\n")
        
        if self.config.abstract:
            paper_parts.append(f"**Abstract:** {self.config.abstract}\n")
        
        if self.config.keywords:
            keywords_str = ", ".join(self.config.keywords)
            paper_parts.append(f"**Keywords:** {keywords_str}\n")
        
        paper_parts.append("\n---\n\n")
        
        # Add sections in order
        section_order = ["abstract", "introduction", "related_work", "methodology", 
                        "results", "discussion", "conclusion"]
        
        for section_name in section_order:
            if section_name in sections:
                section = sections[section_name]
                paper_parts.append(f"## {section.title}\n\n")
                paper_parts.append(f"{section.content}\n\n")
        
        # Add any remaining sections not in standard order
        for section_name, section in sections.items():
            if section_name not in section_order:
                paper_parts.append(f"## {section.title}\n\n")
                paper_parts.append(f"{section.content}\n\n")
        
        return "".join(paper_parts)
    
    def _write_output_files(
        self,
        paper_content: str,
        output_path: Path,
        compile_pdf: bool = False
    ) -> Dict[str, str]:
        """
        Write paper content to output files.
        
        Args:
            paper_content: Complete paper content
            output_path: Output directory path
            compile_pdf: Whether to compile to PDF
            
        Returns:
            Dictionary with paths to created files
        """
        output_files = {}
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = self.config.paper_title or "paper"
        base_filename = base_filename.replace(" ", "_").lower()
        
        # Write markdown file
        md_file = output_path / f"{base_filename}_{timestamp}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(paper_content)
        output_files["markdown"] = str(md_file)
        logger.info(f"Wrote markdown file: {md_file}")
        
        # Convert to LaTeX if requested
        if self.config.output.format == "latex" or compile_pdf:
            latex_content = self._convert_to_latex(paper_content)
            latex_file = output_path / f"{base_filename}_{timestamp}.tex"
            with open(latex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            output_files["latex"] = str(latex_file)
            logger.info(f"Wrote LaTeX file: {latex_file}")
            
            # Compile to PDF if requested
            if compile_pdf:
                try:
                    pdf_file = self._compile_latex_to_pdf(latex_file)
                    output_files["pdf"] = str(pdf_file)
                    logger.info(f"Compiled PDF file: {pdf_file}")
                except Exception as e:
                    logger.warning(f"Failed to compile PDF: {e}")
        
        return output_files
    
    def _convert_to_latex(self, markdown_content: str) -> str:
        """
        Convert markdown content to LaTeX.
        
        Args:
            markdown_content: Markdown content to convert
            
        Returns:
            LaTeX content
        """
        # Basic markdown to LaTeX conversion
        latex_content = markdown_content
        
        # Replace markdown headers with LaTeX sections
        latex_content = latex_content.replace("# ", "\\title{").replace("\n", "}\n", 1)
        latex_content = latex_content.replace("## ", "\\section{")
        latex_content = latex_content.replace("### ", "\\subsection{")
        latex_content = latex_content.replace("#### ", "\\subsubsection{")
        
        # Replace bold text
        latex_content = latex_content.replace("**", "\\textbf{").replace("**", "}")
        
        # Replace italic text
        latex_content = latex_content.replace("*", "\\textit{").replace("*", "}")
        
        # Add LaTeX document structure
        latex_template = """\\documentclass{article}
\\usepackage[utf8]{inputenc}
\\usepackage{amsmath}
\\usepackage{amsfonts}
\\usepackage{amssymb}
\\usepackage{graphicx}
\\usepackage{hyperref}

\\begin{document}

""" + latex_content + """

\\end{document}"""
        
        return latex_template
    
    def _compile_latex_to_pdf(self, latex_file: Path) -> Path:
        """
        Compile LaTeX file to PDF.
        
        Args:
            latex_file: Path to LaTeX file
            
        Returns:
            Path to generated PDF file
            
        Raises:
            GenerationError: If compilation fails
        """
        import subprocess
        
        try:
            # Run pdflatex
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", str(latex_file)],
                cwd=latex_file.parent,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            pdf_file = latex_file.with_suffix('.pdf')
            
            if result.returncode == 0 and pdf_file.exists():
                return pdf_file
            else:
                raise GenerationError(f"LaTeX compilation failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise GenerationError("LaTeX compilation timed out")
        except FileNotFoundError:
            raise GenerationError("pdflatex not found. Please install a LaTeX distribution.")
        except Exception as e:
            raise GenerationError(f"LaTeX compilation error: {e}")
    
    def _create_generation_summary(
        self,
        sections_result: Dict[str, Union[Section, Exception]],
        total_time: float
    ) -> GenerationSummary:
        """
        Create generation summary.
        
        Args:
            sections_result: Results from section generation
            total_time: Total generation time
            
        Returns:
            GenerationSummary object
        """
        successful_sections = [s for s in sections_result.values() if isinstance(s, Section)]
        failed_sections = [s for s in sections_result.values() if isinstance(s, Exception)]
        
        total_word_count = sum(s.word_count for s in successful_sections)
        llm_calls = len(sections_result)  # One call per section attempt
        
        errors = [str(e) for e in failed_sections]
        
        return GenerationSummary(
            total_sections=len(sections_result),
            successful_sections=len(successful_sections),
            failed_sections=len(failed_sections),
            total_time=total_time,
            total_word_count=total_word_count,
            llm_calls=llm_calls,
            errors=errors
        )
    
    def validate_paper(self, paper_content: str) -> ValidationResult:
        """
        Validate generated paper content.
        
        Args:
            paper_content: Paper content to validate
            
        Returns:
            ValidationResult object
        """
        errors = []
        warnings = []
        metrics = {}
        
        # Basic validation
        if not paper_content or not paper_content.strip():
            errors.append("Paper content is empty")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                metrics=metrics
            )
        
        # Word count validation
        word_count = len(paper_content.split())
        metrics["word_count"] = word_count
        
        if word_count < self.config.validation.min_word_count:
            errors.append(f"Paper too short: {word_count} words (minimum: {self.config.validation.min_word_count})")
        
        if word_count > self.config.validation.max_word_count:
            warnings.append(f"Paper very long: {word_count} words (maximum: {self.config.validation.max_word_count})")
        
        # Section validation
        required_sections = self.config.validation.required_sections
        for section in required_sections:
            section_header = f"## {section.title()}"
            if section_header not in paper_content:
                errors.append(f"Required section missing: {section}")
        
        # Additional quality checks
        sentences = paper_content.split('.')
        metrics["sentence_count"] = len([s for s in sentences if s.strip()])
        
        if metrics["sentence_count"] > 0:
            metrics["avg_words_per_sentence"] = word_count / metrics["sentence_count"]
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metrics=metrics
        )
    
    def set_context_collector(self, context_collector: ContextCollector) -> None:
        """
        Set a custom context collector.
        
        Args:
            context_collector: ContextCollector instance to use
        """
        self._context_collector = context_collector
        logger.info("Custom context collector set")
    
    def get_available_templates(self) -> List[str]:
        """
        Get list of available templates.
        
        Returns:
            List of template names
        """
        return self.template_manager.list_templates("prompt")
    
    def get_paper_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the paper generator configuration.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "llm_model": self.config.llm.model,
            "llm_provider": self.config.llm.provider,
            "output_format": self.config.output.format,
            "validation_enabled": self.config.validation.enabled,
            "available_templates": len(self.get_available_templates()),
            "paper_title": self.config.paper_title,
            "authors_count": len(self.config.authors),
            "keywords_count": len(self.config.keywords)
        }
