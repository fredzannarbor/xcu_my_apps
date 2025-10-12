"""
Core paper generation functionality.

This module contains the main paper generation engine, section generators,
context collectors, and validation components.
"""

from .generator import ArxivPaperGenerator
from .context_collector import ContextCollector, ContextConfig
from .section_generator import SectionGenerator
from .content_extractor import (
    ContentExtractor,
    ExtractedFigure,
    SFTExample,
    RLExample,
    ExtractionResult
)
from .answer_key_generator import (
    AnswerKeyGenerator,
    AnswerKey,
    AnswerKeyResult,
    VerificationInstruction,
    ScoringRubric,
    JudgeEvaluationCriteria,
    DifficultyLevel,
    EvaluationCriteria
)
from .models import (
    PaperConfig,
    PaperResult, 
    Section,
    SectionConfig,
    ValidationResult,
    GenerationSummary
)
from .exceptions import (
    ArxivWriterError,
    ConfigurationError,
    TemplateError, 
    LLMError,
    ValidationError,
    PluginError
)

__all__ = [
    "ArxivPaperGenerator",
    "ContextCollector",
    "ContextConfig",
    "SectionGenerator",
    "ContentExtractor",
    "ExtractedFigure",
    "SFTExample",
    "RLExample",
    "ExtractionResult",
    "AnswerKeyGenerator",
    "AnswerKey",
    "AnswerKeyResult",
    "VerificationInstruction",
    "ScoringRubric",
    "JudgeEvaluationCriteria",
    "DifficultyLevel",
    "EvaluationCriteria",
    "PaperConfig",
    "PaperResult",
    "Section",
    "SectionConfig", 
    "ValidationResult",
    "GenerationSummary",
    "ArxivWriterError",
    "ConfigurationError",
    "TemplateError",
    "LLMError", 
    "ValidationError",
    "PluginError"
]
