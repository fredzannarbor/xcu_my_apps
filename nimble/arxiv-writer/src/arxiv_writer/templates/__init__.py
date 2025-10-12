"""
Template management and rendering functionality.

This module handles loading, validation, and rendering of prompt templates
and LaTeX templates for paper generation.
"""

from .manager import TemplateManager
from .renderer import TemplateRenderer
from .models import (
    Template, 
    PromptTemplate, 
    LatexTemplate, 
    ValidationCriteria,
    RenderedPrompt,
    TemplateValidationResult
)

__all__ = [
    "TemplateManager",
    "TemplateRenderer",
    "Template",
    "PromptTemplate", 
    "LatexTemplate",
    "ValidationCriteria",
    "RenderedPrompt",
    "TemplateValidationResult"
]
