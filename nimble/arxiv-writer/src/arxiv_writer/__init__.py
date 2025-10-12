"""
ArXiv Writer - A standalone package for AI-assisted academic paper generation.

This package provides a clean, configurable API for generating academic papers
in arXiv format using Large Language Models (LLMs). It abstracts the paper
generation functionality from the Codexes Factory codebase into a reusable library.

Key Features:
- Multi-LLM support with retry logic and error handling
- Configurable paper structure and content generation
- Plugin architecture for extensibility
- LaTeX output with PDF compilation
- Academic writing validation and quality assessment
- Template-based prompt management

Example Usage:
    from arxiv_writer import ArxivPaperGenerator, PaperConfig
    
    config = PaperConfig.from_file("config.json")
    generator = ArxivPaperGenerator(config)
    result = generator.generate_paper(context_data)
"""

__version__ = "0.1.0"
__author__ = "AI Lab for Book-Lovers"
__email__ = "contact@ailabforbooklovers.com"

# Core imports for public API
from .core.generator import ArxivPaperGenerator
from .core.models import PaperConfig, PaperResult, Section
from .config.loader import ConfigLoader

# Exception classes
from .core.exceptions import (
    ArxivWriterError,
    ConfigurationError,
    TemplateError,
    LLMError,
    ValidationError,
    PluginError
)

__all__ = [
    # Core classes
    "ArxivPaperGenerator",
    "PaperConfig", 
    "PaperResult",
    "Section",
    "ConfigLoader",
    
    # Exceptions
    "ArxivWriterError",
    "ConfigurationError", 
    "TemplateError",
    "LLMError",
    "ValidationError",
    "PluginError",
    
    # Metadata
    "__version__",
    "__author__",
    "__email__"
]
