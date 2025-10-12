"""
CodexType class hierarchy for the Codexes Factory.

This module defines the complete class hierarchy for different types of codexes
(books and publications) that can be produced by the factory. Each CodexType
encapsulates the specific requirements, formatting rules, and production
parameters needed for that particular type of publication.

The hierarchy supports:
- Standard book types (novels, textbooks, reference works)
- Literary forms (poetry, epistolary novels, chapbooks)
- Specialized content (cookbooks, puzzle books, journals, workbooks)
- Reference materials (encyclopedias, dictionaries, handbooks)

Usage:
    from codexes.modules.core.codex_types import get_codex_type_by_name, StandardBook

    # Get type by string name
    book_type = get_codex_type_by_name("standard")

    # Use class directly
    standard_book = StandardBook()
    print(standard_book.description)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type, Union
import re


class CodexType(ABC):
    """
    Abstract base class for all CodexType implementations.

    Each CodexType defines the requirements, formatting rules, and production
    parameters needed for a specific type of publication. This includes
    template requirements, typography rules, layout specifications, and
    content organization patterns.
    """

    def __init__(self):
        """Initialize a CodexType instance."""
        self._template_requirements = self._get_template_requirements()
        self._formatting_rules = self._get_formatting_rules()

    @property
    @abstractmethod
    def name(self) -> str:
        """The display name of this CodexType."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A detailed description of this CodexType and its use cases."""
        pass

    @property
    @abstractmethod
    def type_key(self) -> str:
        """The unique string identifier for this CodexType."""
        pass

    @property
    def template_requirements(self) -> List[str]:
        """Template components required for this CodexType."""
        return self._template_requirements

    @property
    def formatting_rules(self) -> Dict[str, str]:
        """Formatting and typography rules specific to this CodexType."""
        return self._formatting_rules

    @abstractmethod
    def _get_template_requirements(self) -> List[str]:
        """Get the list of template requirements for this CodexType."""
        pass

    @abstractmethod
    def _get_formatting_rules(self) -> Dict[str, str]:
        """Get the formatting rules dictionary for this CodexType."""
        pass

    def get_keywords(self) -> List[str]:
        """
        Get keywords that might indicate content suitable for this CodexType.
        Override in subclasses for content-specific detection.
        """
        return [self.type_key.lower(), self.name.lower()]

    def matches_content(self, content: str) -> float:
        """
        Analyze content to determine how well it matches this CodexType.
        Returns a confidence score between 0.0 and 1.0.
        """
        content_lower = content.lower()
        keywords = self.get_keywords()

        matches = sum(1 for keyword in keywords if keyword in content_lower)
        if not keywords:
            return 0.0

        return min(matches / len(keywords), 1.0)

    def __str__(self) -> str:
        return f"{self.name} ({self.type_key})"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.type_key}>"


# Standard Book Types
class StandardBook(CodexType):
    """Traditional book layout with chapters, paragraphs, standard typography."""

    @property
    def name(self) -> str:
        return "Standard Book"

    @property
    def description(self) -> str:
        return "Traditional book layout with chapters, paragraphs, standard typography"

    @property
    def type_key(self) -> str:
        return "standard"

    def _get_template_requirements(self) -> List[str]:
        return ["chapter_headings", "page_numbers", "table_of_contents"]

    def _get_formatting_rules(self) -> Dict[str, str]:
        return {
            "paragraph_spacing": "standard",
            "heading_hierarchy": "h1_h2_h3",
            "quote_formatting": "indented_block",
            "list_formatting": "bulleted_numbered"
        }


class ReferenceWork(CodexType):
    """Dictionary/encyclopedia style with cross-references and definitions."""

    @property
    def name(self) -> str:
        return "Reference Book"

    @property
    def description(self) -> str:
        return "Dictionary/encyclopedia style with cross-references and definitions"

    @property
    def type_key(self) -> str:
        return "reference"

    def _get_template_requirements(self) -> List[str]:
        return ["alphabetical_organization", "cross_references", "index"]

    def _get_formatting_rules(self) -> Dict[str, str]:
        return {
            "entry_format": "definition_style",
            "cross_reference_style": "linked_or_italic",
            "index_organization": "multiple_levels",
            "appendix_handling": "reference_materials",
            "margin_notes": "additional_information"
        }

    def get_keywords(self) -> List[str]:
        return super().get_keywords() + [
            "dictionary", "encyclopedia", "handbook", "reference", "glossary",
            "index", "cross-reference", "definition", "alphabetical"
        ]


class AcademicTextbook(CodexType):
    """Educational formatting with exercises, sidebars, and learning objectives."""

    @property
    def name(self) -> str:
        return "Academic Textbook"

    @property
    def description(self) -> str:
        return "Educational formatting with exercises, sidebars, and learning objectives"

    @property
    def type_key(self) -> str:
        return "textbook"

    def _get_template_requirements(self) -> List[str]:
        return ["learning_objectives", "exercises", "sidebars", "glossary"]

    def _get_formatting_rules(self) -> Dict[str, str]:
        return {
            "chapter_structure": "educational_hierarchy",
            "sidebar_treatment": "boxed_supplementary",
            "exercise_format": "numbered_with_answers",
            "glossary_style": "alphabetical_definitions",
            "citation_format": "academic_standards"
        }

    def get_keywords(self) -> List[str]:
        return super().get_keywords() + [
            "textbook", "academic", "educational", "learning", "exercises",
            "syllabus", "curriculum", "study", "university", "college"
        ]


# Literary Forms
class Novel(CodexType):
    """Full-length narrative fiction with traditional chapter structure."""

    @property
    def name(self) -> str:
        return "Novel"

    @property
    def description(self) -> str:
        return "Full-length narrative fiction with traditional chapter structure"

    @property
    def type_key(self) -> str:
        return "novel"

    def _get_template_requirements(self) -> List[str]:
        return ["chapter_headings", "page_numbers", "table_of_contents", "scene_breaks"]

    def _get_formatting_rules(self) -> Dict[str, str]:
        return {
            "paragraph_spacing": "standard",
            "chapter_opening": "distinctive_styling",
            "scene_breaks": "section_dividers",
            "dialogue_formatting": "standard_fiction",
            "page_breaks": "chapter_boundaries"
        }

    def get_keywords(self) -> List[str]:
        return super().get_keywords() + [
            "novel", "fiction", "story", "narrative", "chapters",
            "protagonist", "plot", "character", "literary fiction"
        ]


class Chapbook(CodexType):
    """Short literary work, typically poetry or prose, in pamphlet format."""

    @property
    def name(self) -> str:
        return "Chapbook"

    @property
    def description(self) -> str:
        return "Short literary work, typically poetry or prose, in pamphlet format"

    @property
    def type_key(self) -> str:
        return "chapbook"

    def _get_template_requirements(self) -> List[str]:
        return ["title_page", "minimal_structure", "author_bio"]

    def _get_formatting_rules(self) -> Dict[str, str]:
        return {
            "page_layout": "compact_efficient",
            "typography": "literary_emphasis",
            "spacing": "generous_white_space",
            "binding": "saddle_stitched",
            "page_count": "under_40_pages"
        }

    def get_keywords(self) -> List[str]:
        return super().get_keywords() + [
            "chapbook", "pamphlet", "short", "literary", "poetry collection",
            "prose", "limited edition", "small press"
        ]


class EpistolaryNovel(CodexType):
    """Narrative told through letters, diary entries, or other documents."""

    @property
    def name(self) -> str:
        return "Epistolary Novel"

    @property
    def description(self) -> str:
        return "Narrative told through letters, diary entries, or other documents"

    @property
    def type_key(self) -> str:
        return "epistolary"

    def _get_template_requirements(self) -> List[str]:
        return ["date_headers", "sender_recipient", "document_formatting", "chronological_organization"]

    def _get_formatting_rules(self) -> Dict[str, str]:
        return {
            "letter_format": "traditional_correspondence",
            "date_placement": "header_position",
            "signature_style": "handwritten_appearance",
            "document_variety": "mixed_formats",
            "authenticity_markers": "period_appropriate"
        }

    def get_keywords(self) -> List[str]:
        return super().get_keywords() + [
            "epistolary", "letters", "diary", "correspondence", "documents",
            "memoir", "journal entries", "testimonies", "confessions"
        ]


class Poetry(CodexType):
    """Verse formatting with proper line breaks and stanza spacing."""

    @property
    def name(self) -> str:
        return "Poetry Collection"

    @property
    def description(self) -> str:
        return "Verse formatting with proper line breaks and stanza spacing"

    @property
    def type_key(self) -> str:
        return "poetry"

    def _get_template_requirements(self) -> List[str]:
        return ["line_breaks", "stanza_spacing", "poem_titles"]

    def _get_formatting_rules(self) -> Dict[str, str]:
        return {
            "line_spacing": "preserved_poet_intent",
            "indentation": "verse_specific",
            "title_treatment": "distinctive_typography",
            "page_breaks": "poem_boundary_respect",
            "margin_usage": "white_space_emphasis"
        }

    def get_keywords(self) -> List[str]:
        return super().get_keywords() + [
            "poetry", "poems", "verse", "stanza", "rhyme", "meter",
            "sonnet", "haiku", "free verse", "lyric", "ballad"
        ]


# Specialized Content Types
class OralHistory(CodexType):
    """Interview format with speaker identification, question/answer structure."""

    @property
    def name(self) -> str:
        return "Oral History"

    @property
    def description(self) -> str:
        return "Interview format with speaker identification, question/answer structure"

    @property
    def type_key(self) -> str:
        return "oral_history"

    def _get_template_requirements(self) -> List[str]:
        return ["speaker_tags", "timestamp_markers", "question_answer_format"]

    def _get_formatting_rules(self) -> Dict[str, str]:
        return {
            "speaker_name": "bold_at_paragraph_start",
            "question_format": "italic_or_bold_q_prefix",
            "answer_format": "regular_text_with_indent",
            "section_breaks": "topic_or_time_based",
            "quote_preservation": "verbatim_with_markers"
        }

    def get_keywords(self) -> List[str]:
        return super().get_keywords() + [
            "oral history", "interview", "testimony", "memoir", "biography",
            "conversation", "dialogue", "witness", "storytelling"
        ]


class Cookbook(CodexType):
    """Recipe formatting with ingredient lists and step-by-step instructions."""

    @property
    def name(self) -> str:
        return "Cookbook"

    @property
    def description(self) -> str:
        return "Recipe formatting with ingredient lists and step-by-step instructions"

    @property
    def type_key(self) -> str:
        return "cookbook"

    def _get_template_requirements(self) -> List[str]:
        return ["ingredient_lists", "instruction_steps", "cooking_times"]

    def _get_formatting_rules(self) -> Dict[str, str]:
        return {
            "ingredient_format": "bulleted_with_measurements",
            "instruction_format": "numbered_steps",
            "timing_indicators": "highlighted_or_boxed",
            "difficulty_ratings": "visual_scale",
            "nutritional_info": "tabulated_data"
        }

    def get_keywords(self) -> List[str]:
        return super().get_keywords() + [
            "cookbook", "recipe", "cooking", "ingredients", "instructions",
            "culinary", "kitchen", "food", "chef", "cuisine"
        ]


class PuzzleBook(CodexType):
    """Grid-based layouts for puzzles with answer sections."""

    @property
    def name(self) -> str:
        return "Puzzle Book"

    @property
    def description(self) -> str:
        return "Grid-based layouts for puzzles with answer sections"

    @property
    def type_key(self) -> str:
        return "puzzle"

    def _get_template_requirements(self) -> List[str]:
        return ["grid_layouts", "answer_keys", "difficulty_indicators"]

    def _get_formatting_rules(self) -> Dict[str, str]:
        return {
            "puzzle_grid": "fixed_width_monospace",
            "instructions": "boxed_or_highlighted",
            "answer_section": "separate_or_back_matter",
            "difficulty_rating": "visual_indicators",
            "numbering_system": "sequential_or_by_section"
        }

    def get_keywords(self) -> List[str]:
        return super().get_keywords() + [
            "puzzle", "crossword", "sudoku", "word search", "brain teaser",
            "logic", "game", "challenge", "solution", "grid"
        ]


class Journal(CodexType):
    """Personal writing format with dated entries and reflection space."""

    @property
    def name(self) -> str:
        return "Journal/Diary"

    @property
    def description(self) -> str:
        return "Personal writing format with dated entries and reflection space"

    @property
    def type_key(self) -> str:
        return "journal"

    def _get_template_requirements(self) -> List[str]:
        return ["date_headers", "writing_space", "prompt_sections"]

    def _get_formatting_rules(self) -> Dict[str, str]:
        return {
            "date_format": "prominent_header",
            "writing_lines": "adequate_spacing",
            "prompt_placement": "inspiring_quotes",
            "page_layout": "personal_friendly",
            "binding_considerations": "lay_flat_design"
        }

    def get_keywords(self) -> List[str]:
        return super().get_keywords() + [
            "journal", "diary", "notebook", "reflection", "personal",
            "writing", "thoughts", "daily", "meditation", "gratitude"
        ]


class Workbook(CodexType):
    """Exercise-based format with fill-in blanks and practice spaces."""

    @property
    def name(self) -> str:
        return "Interactive Workbook"

    @property
    def description(self) -> str:
        return "Exercise-based format with fill-in blanks and practice spaces"

    @property
    def type_key(self) -> str:
        return "workbook"

    def _get_template_requirements(self) -> List[str]:
        return ["exercise_spaces", "answer_sections", "progress_tracking"]

    def _get_formatting_rules(self) -> Dict[str, str]:
        return {
            "exercise_layout": "clear_instructions",
            "fill_in_blanks": "adequate_space",
            "answer_key_placement": "separate_section",
            "progress_indicators": "tracking_elements",
            "instruction_clarity": "step_by_step"
        }

    def get_keywords(self) -> List[str]:
        return super().get_keywords() + [
            "workbook", "exercises", "practice", "activities", "interactive",
            "fill-in", "worksheet", "training", "self-study", "tutorial"
        ]


# Reference Types (extending ReferenceWork)
class Encyclopedia(ReferenceWork):
    """Comprehensive reference work with detailed articles on many subjects."""

    @property
    def name(self) -> str:
        return "Encyclopedia"

    @property
    def description(self) -> str:
        return "Comprehensive reference work with detailed articles on many subjects"

    @property
    def type_key(self) -> str:
        return "encyclopedia"

    def _get_template_requirements(self) -> List[str]:
        base_requirements = super()._get_template_requirements()
        return base_requirements + ["volume_organization", "subject_categories"]

    def get_keywords(self) -> List[str]:
        return super().get_keywords() + ["encyclopedia", "comprehensive", "volumes"]


class Dictionary(ReferenceWork):
    """Alphabetical listing of words with definitions and usage information."""

    @property
    def name(self) -> str:
        return "Dictionary"

    @property
    def description(self) -> str:
        return "Alphabetical listing of words with definitions and usage information"

    @property
    def type_key(self) -> str:
        return "dictionary"

    def _get_template_requirements(self) -> List[str]:
        base_requirements = super()._get_template_requirements()
        return base_requirements + ["pronunciation_guides", "etymology_sections"]

    def get_keywords(self) -> List[str]:
        return super().get_keywords() + [
            "dictionary", "definitions", "pronunciation", "etymology", "lexicon"
        ]


class Handbook(ReferenceWork):
    """Practical guide with instructions and reference information for specific topics."""

    @property
    def name(self) -> str:
        return "Handbook"

    @property
    def description(self) -> str:
        return "Practical guide with instructions and reference information for specific topics"

    @property
    def type_key(self) -> str:
        return "handbook"

    def _get_template_requirements(self) -> List[str]:
        base_requirements = super()._get_template_requirements()
        return base_requirements + ["quick_reference_sections", "practical_examples"]

    def get_keywords(self) -> List[str]:
        return super().get_keywords() + [
            "handbook", "manual", "guide", "how-to", "practical", "instructions"
        ]


# Registry and Utility Functions
class CodexTypeRegistry:
    """Registry for managing all available CodexType classes."""

    def __init__(self):
        self._types: Dict[str, Type[CodexType]] = {}
        self._instances: Dict[str, CodexType] = {}
        self._register_default_types()

    def _register_default_types(self):
        """Register all default CodexType classes."""
        default_types = [
            StandardBook, ReferenceWork, AcademicTextbook,
            Novel, Chapbook, EpistolaryNovel, Poetry,
            OralHistory, Cookbook, PuzzleBook, Journal, Workbook,
            Encyclopedia, Dictionary, Handbook
        ]

        for type_class in default_types:
            self.register_type(type_class)

    def register_type(self, type_class: Type[CodexType]):
        """Register a new CodexType class."""
        # Create instance to get type_key
        instance = type_class()
        self._types[instance.type_key] = type_class
        self._instances[instance.type_key] = instance

    def get_type_class(self, type_key: str) -> Optional[Type[CodexType]]:
        """Get the class for a given type key."""
        return self._types.get(type_key)

    def get_type_instance(self, type_key: str) -> Optional[CodexType]:
        """Get an instance for a given type key."""
        return self._instances.get(type_key)

    def list_type_keys(self) -> List[str]:
        """Get a list of all registered type keys."""
        return list(self._types.keys())

    def list_type_instances(self) -> List[CodexType]:
        """Get a list of all registered type instances."""
        return list(self._instances.values())


# Global registry instance
_registry = CodexTypeRegistry()


# Public API Functions
def get_codex_type_by_name(name: str) -> Optional[CodexType]:
    """
    Get a CodexType instance by its string identifier.

    Args:
        name: The type key (e.g., 'standard', 'poetry', 'cookbook')

    Returns:
        CodexType instance if found, None otherwise
    """
    return _registry.get_type_instance(name)


def list_all_codex_types() -> List[CodexType]:
    """
    Get a list of all available CodexType instances.

    Returns:
        List of all registered CodexType instances
    """
    return _registry.list_type_instances()


def detect_codex_type_from_keywords(content: str) -> List[tuple[CodexType, float]]:
    """
    Analyze content to detect the most suitable CodexType(s).

    Args:
        content: Text content to analyze

    Returns:
        List of (CodexType, confidence_score) tuples, sorted by confidence (highest first)
    """
    results = []

    for codex_type in _registry.list_type_instances():
        confidence = codex_type.matches_content(content)
        if confidence > 0:
            results.append((codex_type, confidence))

    # Sort by confidence score (highest first)
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def register_codex_type(type_class: Type[CodexType]):
    """
    Register a new CodexType class with the global registry.

    Args:
        type_class: The CodexType class to register
    """
    _registry.register_type(type_class)


def get_codex_type_keys() -> List[str]:
    """
    Get a list of all available CodexType keys.

    Returns:
        List of type key strings
    """
    return _registry.list_type_keys()


# Backward compatibility aliases
def get_type_by_key(key: str) -> Optional[CodexType]:
    """Alias for get_codex_type_by_name for backward compatibility."""
    return get_codex_type_by_name(key)


def get_all_types() -> List[CodexType]:
    """Alias for list_all_codex_types for backward compatibility."""
    return list_all_codex_types()