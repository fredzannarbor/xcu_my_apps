"""
Exception classes for arxiv-writer.
"""


class ArxivWriterError(Exception):
    """Base exception class for arxiv-writer."""
    pass


class ConfigurationError(ArxivWriterError):
    """Raised when there's an error in configuration."""
    pass


class TemplateError(ArxivWriterError):
    """Raised when there's an error with templates."""
    pass


class LLMError(ArxivWriterError):
    """Raised when there's an error with LLM calls."""
    pass


class ValidationError(ArxivWriterError):
    """Raised when validation fails."""
    pass


class PluginError(ArxivWriterError):
    """Raised when there's an error with plugins."""
    pass


class GenerationError(ArxivWriterError):
    """Raised when paper generation fails."""
    pass


class CompilationError(ArxivWriterError):
    """Raised when LaTeX compilation fails."""
    pass
