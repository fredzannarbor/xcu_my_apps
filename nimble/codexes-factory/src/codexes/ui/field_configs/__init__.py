"""
Field Configuration System

Provides field configurations for different content types in the Stage-Agnostic UI.
"""

from .universal_fields import UniversalFieldConfig
from .idea_fields import IdeaFieldConfig
from .synopsis_fields import SynopsisFieldConfig
from .outline_fields import OutlineFieldConfig
from .draft_fields import DraftFieldConfig

__all__ = [
    'UniversalFieldConfig',
    'IdeaFieldConfig', 
    'SynopsisFieldConfig',
    'OutlineFieldConfig',
    'DraftFieldConfig'
]