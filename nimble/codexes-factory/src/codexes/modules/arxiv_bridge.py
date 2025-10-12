"""
Arxiv Bridge Module

This module provides a bridge between the legacy arxiv_paper module
and the new arxiv-writer package. It uses the preferred arxiv-writer
package with proper API usage and minimal fallback.
"""

import sys
import os
import json
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


def _generate_paper_simple_fallback(context_data, output_dir, working_directory, error_message):
    """
    Simple fallback function that generates a paper using basic text generation.
    This function creates a simple academic paper when the arxiv-writer package fails.
    """
    logger.warning(f"🔄 Using simple fallback due to: {error_message}")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Look for templates in working directory
    template_file = Path(working_directory) / "prompts" / "arxiv_paper_prompts.json"
    templates = {}
    if template_file.exists():
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                templates = template_data.get('paper_sections', {})
            logger.info(f"📄 Loaded {len(templates)} templates from {template_file}")
        except Exception as e:
            logger.warning(f"Could not load templates: {e}")

    # Generate a basic paper structure
    paper_content = _create_basic_paper_content(context_data, templates)

    # Save the paper
    paper_file = output_path / "xynapse_traces_paper.md"

    try:
        with open(paper_file, 'w', encoding='utf-8') as f:
            f.write(paper_content)

        logger.info(f"✅ Simple fallback paper generated: {paper_file}")

        return {
            "success": True,
            "output_directory": str(output_path),
            "imprint_name": context_data.get("imprint_name", "Unknown"),
            "context_data": context_data,
            "paper_file": str(paper_file),
            "generation_method": "simple_fallback",
            "fallback_reason": error_message
        }

    except Exception as e:
        logger.error(f"❌ Failed to write paper file: {e}")
        return {
            "success": False,
            "error": f"Failed to write paper: {e}",
            "context_data": context_data
        }


def _create_basic_paper_content(context_data, templates):
    """Create basic paper content using available context data."""

    imprint_name = context_data.get("imprint_name", "Unknown Imprint")
    specialization = context_data.get("specialization", "Publishing innovation")
    focus_areas = context_data.get("focus_areas", [])
    complexity = context_data.get("configuration_complexity", {})

    paper_content = f"""# AI-Assisted Development of {imprint_name}: A Case Study

**Authors:** {imprint_name} Editorial Team
**Affiliation:** AI Lab for Book-Lovers, Nimble Books LLC
**Date:** {datetime.now().strftime("%Y-%m-%d")}

## Abstract

The AI Lab for Book-Lovers demonstrates the use of AI-assisted methods to create the {imprint_name} imprint, specializing in {specialization}. This case study documents the first fully automated imprint development using multi-level configuration systems and LLM-powered content generation. The implementation achieved rapid imprint deployment with {complexity.get('complexity_level', 'high')} configuration complexity and demonstrates novel approaches to AI-assisted publishing workflows.

**Keywords:** AI-assisted publishing, imprint development, multi-level configuration, automated content generation

## 1. Introduction

The publishing industry faces increasing pressure to rapidly adapt to new markets and audience segments. Traditional imprint creation involves extensive manual processes for market research, brand development, editorial guidelines, and production workflows. This paper presents the first documented case of fully AI-assisted imprint creation, demonstrating how Large Language Models (LLMs) and configuration-driven automation can compress months of traditional development into days.

{imprint_name} represents a breakthrough in AI-assisted publishing methodology, focusing on {specialization}. The imprint development process leveraged multi-model LLM orchestration, automated configuration generation, and data-driven decision making to create a complete publishing platform.

## 2. Methodology

### 2.1 Configuration-Driven Development

The imprint creation process utilized a hierarchical configuration system with the following levels:

- **Publisher Level:** Global settings and brand standards
- **Imprint Level:** Specialized configurations for {imprint_name}
- **Title Level:** Individual book production parameters

### 2.2 AI Integration Architecture

The system employed multiple LLM models for different aspects of imprint development:

- Content generation and editorial guidance
- Brand positioning and market analysis
- Technical configuration optimization
- Quality assurance and validation

### 2.3 Focus Areas

The {imprint_name} imprint was designed to address the following research and market areas:

{chr(10).join(f"- {area}" for area in focus_areas)}

## 3. Implementation

### 3.1 Technical Architecture

The implementation utilized a modular Python architecture with the following components:

- **Configuration Management:** JSON-based hierarchical configuration system
- **LLM Orchestration:** Multi-model calling with retry logic and error handling
- **Content Generation:** Automated template processing and content creation
- **Quality Validation:** Automated quality assessment and compliance checking

### 3.2 Configuration Complexity Analysis

The {imprint_name} configuration achieved a complexity score of {complexity.get('complexity_score', 'N/A')} with the following characteristics:

- Configuration sections: {complexity.get('total_config_sections', 'N/A')}
- Complexity level: {complexity.get('complexity_level', 'unknown').title()}
- Automation features: {'Advanced' if complexity.get('has_workflow_automation') else 'Basic'}

## 4. Results

### 4.1 Development Efficiency

The AI-assisted approach achieved significant efficiency gains compared to traditional methods:

- **Time to market:** Reduced from months to days
- **Configuration completeness:** Automated generation of comprehensive settings
- **Quality consistency:** Standardized validation and quality assurance

### 4.2 Technical Contributions

Key technical innovations demonstrated in this implementation:

1. **Multi-level configuration inheritance** enabling flexible customization
2. **LLM-powered content generation** with quality validation
3. **Automated workflow orchestration** reducing manual intervention
4. **Data-driven brand positioning** using market analysis

## 5. Discussion

### 5.1 Industry Implications

The successful creation of {imprint_name} demonstrates the viability of AI-assisted publishing workflows for:

- Rapid market response and imprint creation
- Reduced development costs and time-to-market
- Improved consistency and quality standards
- Scalable publishing operations

### 5.2 Technical Innovations

The configuration-driven approach enables:

- Reproducible imprint creation processes
- Systematic knowledge capture and reuse
- Automated compliance and quality validation
- Flexible customization for different markets

## 6. Conclusion

This case study demonstrates the first successful implementation of fully AI-assisted imprint creation. The {imprint_name} imprint represents a significant advancement in publishing automation, achieving rapid deployment while maintaining high quality standards.

The multi-level configuration system and LLM integration patterns developed for this project provide a foundation for scaling AI-assisted publishing operations. Future work will focus on expanding this methodology to additional imprints and market segments.

## References

1. AI Lab for Book-Lovers. (2024). Configuration-Driven Publishing: A Technical Framework.
2. Nimble Books LLC. (2024). Multi-Level Configuration Systems for Publishing Automation.
3. {imprint_name} Editorial Team. (2024). AI-Assisted Content Generation in Academic Publishing.

---

*This paper was generated using AI-assisted methods as part of the {imprint_name} imprint development process.*
"""

    return paper_content


# Try to import from arxiv-writer first
try:
    # Import from arxiv-writer package
    from arxiv_writer import ArxivPaperGenerator, PaperConfig, PaperResult, Section
    from arxiv_writer.config.loader import ConfigLoader
    from arxiv_writer.core.codexes_factory_adapter import CodexesFactoryAdapter, create_codexes_factory_paper_generator
    from arxiv_writer.core.models import LLMConfig, TemplateConfig, ValidationConfig

    logger.info("Successfully imported arxiv-writer package")
    ARXIV_WRITER_AVAILABLE = True

    def generate_arxiv_paper(
        context_data=None,
        output_dir="./output/arxiv_paper",
        config_file=None,
        working_directory=None,
        **kwargs
    ):
        """
        Generate arxiv paper using the arxiv-writer package.

        This function provides backward compatibility with the legacy
        generate_arxiv_paper function from the arxiv_paper module.

        Args:
            context_data: Context data for paper generation
            output_dir: Output directory (relative to working_directory)
            config_file: Configuration file path (relative to working_directory)
            working_directory: Base directory for all file operations (defaults to cwd)
            **kwargs: Additional configuration parameters
        """
        # Set working directory (caller's project directory)
        if working_directory is None:
            working_directory = os.getcwd()

        # Resolve absolute paths
        abs_working_dir = Path(working_directory).resolve()
        abs_output_dir = abs_working_dir / output_dir

        logger.info(f"Generating paper in working directory: {abs_working_dir}")
        logger.info(f"Output directory: {abs_output_dir}")

        try:
            # Create configuration using the CodexesFactoryAdapter
            if config_file:
                config_path = abs_working_dir / config_file
                if config_path.exists():
                    logger.info(f"Loading configuration from: {config_path}")
                    adapter = CodexesFactoryAdapter(str(config_path))
                else:
                    logger.warning(f"Config file not found: {config_path}, using defaults")
                    adapter = create_codexes_factory_paper_generator(
                        workspace_root=abs_working_dir,
                        imprint_name=kwargs.get('imprint_name', 'default')
                    )
            else:
                # Create adapter with default configuration
                adapter = create_codexes_factory_paper_generator(
                    workspace_root=abs_working_dir,
                    imprint_name=kwargs.get('imprint_name', 'default')
                )

            # Set output directory on the adapter's configuration
            adapter.paper_config.output_directory = str(abs_output_dir)

            # Look for templates in the calling project
            template_file = abs_working_dir / "prompts" / "arxiv_paper_prompts.json"
            if template_file.exists():
                logger.info(f"Found templates at: {template_file}")
                adapter.paper_config.template_config.template_file = str(template_file)
                adapter.paper_config.templates.template_file = str(template_file)
            else:
                logger.info("No custom templates found, using defaults")

            # Generate paper using the adapter
            if context_data:
                logger.info("Generating paper with provided context data")
                result = adapter.generate_paper(additional_context=context_data)
            else:
                logger.info("Generating paper with auto-collected context data")
                result = adapter.generate_paper()

            # Convert result to legacy format
            legacy_result = {
                "success": True,
                "output_directory": str(abs_output_dir),
                "context_data": result.get("context_summary", {}),
                "generation_summary": result.get("generation_summary", {}),
                "paper_content": result.get("paper_content", ""),
                "output_files": result.get("output_files", []),
                "generation_method": "arxiv_writer_adapter"
            }

            logger.info("Paper generation completed successfully")
            return legacy_result

        except Exception as e:
            logger.error(f"ArXiv-writer generation failed: {e}")
            # Fall back to simple generation only if arxiv-writer fails
            return _generate_paper_simple_fallback(
                context_data=context_data,
                output_dir=abs_output_dir,
                working_directory=abs_working_dir,
                error_message=str(e)
            )

    def create_paper_generation_config(**kwargs):
        """Create configuration compatible with legacy interface."""
        try:
            adapter = create_codexes_factory_paper_generator(
                workspace_root=kwargs.get('working_directory', '.'),
                imprint_name=kwargs.get('imprint_name', 'default')
            )
            return adapter.paper_config
        except Exception as e:
            logger.warning(f"Could not create full config: {e}, using minimal config")
            return PaperConfig(
                output_directory=kwargs.get('output_directory', './output/arxiv_paper')
            )

    # Export main functions for backward compatibility
    __all__ = [
        'ArxivPaperGenerator',
        'PaperConfig',
        'PaperResult',
        'Section',
        'generate_arxiv_paper',
        'create_paper_generation_config',
        'ConfigLoader',
        'CodexesFactoryAdapter'
    ]

except ImportError as e:
    logger.error(f"Failed to import arxiv-writer package: {e}")
    ARXIV_WRITER_AVAILABLE = False

    # Create minimal fallback implementations
    def generate_arxiv_paper(
        context_data=None,
        output_dir="./output/arxiv_paper",
        config_file=None,
        working_directory=None,
        **kwargs
    ):
        """Minimal fallback implementation when arxiv-writer is not available."""
        if working_directory is None:
            working_directory = os.getcwd()

        abs_working_dir = Path(working_directory).resolve()
        abs_output_dir = abs_working_dir / output_dir

        logger.warning("ArXiv-writer package not available, using minimal fallback")

        return _generate_paper_simple_fallback(
            context_data=context_data,
            output_dir=abs_output_dir,
            working_directory=abs_working_dir,
            error_message="arxiv-writer package not available"
        )

    def create_paper_generation_config(**kwargs):
        """Minimal fallback config creation."""
        return {
            "output_directory": kwargs.get('output_directory', './output/arxiv_paper'),
            "working_directory": kwargs.get('working_directory', '.'),
            **kwargs
        }

    # Minimal compatibility classes
    class PaperConfig(dict):
        pass

    class PaperResult(dict):
        pass

    class Section(dict):
        pass

    class ArxivPaperGenerator:
        def __init__(self, config):
            self.config = config

        def generate_paper(self, context_data=None):
            return generate_arxiv_paper(context_data=context_data)

    class ConfigLoader:
        @staticmethod
        def load_default():
            return PaperConfig()

    __all__ = [
        'generate_arxiv_paper',
        'ArxivPaperGenerator',
        'create_paper_generation_config',
        'PaperConfig',
        'PaperResult',
        'Section',
        'ConfigLoader'
    ]

    logger.warning("Using minimal fallback implementations for arxiv paper generation")