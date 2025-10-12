"""
Core module for Codexes Factory.

This module provides fundamental classes and utilities for the Codexes Factory
system, including the complete CodexType hierarchy for defining different
types of publications and their specific requirements.

Key Components:
- CodexType: Abstract base class for all publication types
- Standard Types: StandardBook, ReferenceWork, AcademicTextbook
- Literary Forms: Novel, Chapbook, EpistolaryNovel, Poetry
- Specialized Content: OralHistory, Cookbook, PuzzleBook, Journal, Workbook
- Reference Types: Encyclopedia, Dictionary, Handbook
- Utility Functions: Type discovery, registration, and content analysis

Usage:
    from codexes.modules.core import get_codex_type_by_name, StandardBook
    from codexes.modules.core.codex_types import detect_codex_type_from_keywords
"""

# Import all CodexType classes
from .codex_types import (
    # Base class
    CodexType,

    # Standard types
    StandardBook,
    ReferenceWork,
    AcademicTextbook,

    # Literary forms
    Novel,
    Chapbook,
    EpistolaryNovel,
    Poetry,

    # Specialized content
    OralHistory,
    Cookbook,
    PuzzleBook,
    Journal,
    Workbook,

    # Reference types
    Encyclopedia,
    Dictionary,
    Handbook,

    # Registry and utilities
    CodexTypeRegistry,
    get_codex_type_by_name,
    list_all_codex_types,
    detect_codex_type_from_keywords,
    register_codex_type,
    get_codex_type_keys,

    # Backward compatibility aliases
    get_type_by_key,
    get_all_types,
)

# Re-export commonly used functions at module level
__all__ = [
    # Base class
    "CodexType",

    # Standard types
    "StandardBook",
    "ReferenceWork",
    "AcademicTextbook",

    # Literary forms
    "Novel",
    "Chapbook",
    "EpistolaryNovel",
    "Poetry",

    # Specialized content
    "OralHistory",
    "Cookbook",
    "PuzzleBook",
    "Journal",
    "Workbook",

    # Reference types
    "Encyclopedia",
    "Dictionary",
    "Handbook",

    # Registry and utilities
    "CodexTypeRegistry",
    "get_codex_type_by_name",
    "list_all_codex_types",
    "detect_codex_type_from_keywords",
    "register_codex_type",
    "get_codex_type_keys",

    # Backward compatibility
    "get_type_by_key",
    "get_all_types",
]