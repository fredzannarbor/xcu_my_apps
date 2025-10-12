"""
Thema Subject Mapping Module

This module provides specialized mapping strategies for Thema subject fields
to ensure they are complete and valid.
"""

import logging
import re
from typing import Dict, Optional

from .field_mapping import MappingStrategy, MappingContext
from ..metadata.metadata_models import CodexMetadata

logger = logging.getLogger(__name__)


# Complete Thema subject codes mapping
THEMA_CODE_MAPPING = {
    # Top-level categories
    "A": "The Arts",
    "C": "Language & Linguistics",
    "D": "Biography, Literature & Literary Studies",
    "F": "Fiction & Related Items",
    "G": "Reference, Information & Interdisciplinary Subjects",
    "J": "Society & Social Sciences",
    "K": "Economics, Finance, Business & Management",
    "L": "Law",
    "M": "Medicine & Nursing",
    "N": "History & Archaeology",
    "P": "Mathematics & Science",
    "Q": "Philosophy & Religion",
    "R": "Earth Sciences, Geography, Environment, Planning",
    "S": "Sports & Active Outdoor Recreation",
    "T": "Technology, Engineering, Agriculture, Industrial Processes",
    "U": "Computing & Information Technology",
    "V": "Health, Relationships & Personal Development",
    "W": "Lifestyle, Hobbies & Leisure",
    "Y": "Children's, Teenage & Educational",
    
    # Second-level categories (examples)
    "FA": "Fiction: General & Literary",
    "FB": "Fiction: Special Features",
    "FC": "Fiction: Classic",
    "FD": "Fiction: Crime & Mystery",
    "FF": "Fiction: Science Fiction & Fantasy",
    "FH": "Fiction: Historical",
    "FJ": "Fiction: Adventure",
    "FK": "Fiction: Religious & Spiritual",
    "FL": "Fiction: Narrative Themes",
    "FM": "Fiction: Romance",
    "FP": "Fiction: Family & Home",
    "FT": "Fiction: Myths & Legends",
    "FU": "Fiction: Humorous",
    "FV": "Fiction: Horror & Supernatural",
    "FW": "Fiction: Biographical",
    "FX": "Fiction: Graphic Novels, Comics & Manga",
    "FY": "Fiction: Speculative",
    "FZ": "Fiction: Popular & Contemporary",
    
    "JH": "Sociology & Anthropology",
    "JM": "Psychology",
    "JP": "Politics & Government",
    
    "KJ": "Business & Management",
    "KN": "Industry & Industrial Studies",
    
    "NH": "History",
    "NB": "History: Earliest Times to Present Day",
    
    "PD": "Science: General Issues",
    "PG": "Astronomy, Space & Time",
    "PH": "Physics",
    
    "UD": "Programming & Scripting Languages",
    "UF": "Operating Systems",
    "UG": "Hardware",
    
    "VS": "Self-help & Personal Development",
    "VX": "Mind, Body, Spirit",
    
    # Third-level categories (examples)
    "FBA": "Modern & Contemporary Fiction",
    "FCA": "Classic Fiction",
    "FDA": "Crime & Mystery: General",
    "FDB": "Crime & Mystery: Cozy Mystery",
    "FDC": "Crime & Mystery: Police Procedural",
    "FDK": "Crime & Mystery: Historical",
    "FDM": "Crime & Mystery: Women Sleuths",
    
    "JHB": "Sociology",
    "JMC": "Child & Developmental Psychology",
    "JMH": "Social, Group or Collective Psychology",
    
    "KJM": "Management & Management Techniques",
    "KJV": "Sales & Marketing",
    
    "NHB": "History: General & World",
    "NHC": "Ancient History",
    
    "PDZ": "Popular Science",
    "PHQ": "Quantum Physics",
    
    "UDA": "Programming & Scripting Languages: General",
    "UDF": "Programming & Scripting Languages: Python",
    
    "VSP": "Popular Psychology",
    "VXA": "Mind, Body, Spirit: Meditation & Visualization"
}


def expand_thema_code(code: str) -> str:
    """
    Expand a potentially truncated Thema code to its full form.
    
    Args:
        code: The Thema code to expand
        
    Returns:
        The expanded Thema code with description
    """
    if not code:
        return ""
    
    # Clean up the code
    clean_code = code.strip()
    
    # If it's already a full code with description, return as is
    if len(clean_code) > 3 and " " in clean_code:
        return clean_code
    
    # If it's just a single letter or short code, look up the full description
    if clean_code in THEMA_CODE_MAPPING:
        return f"{clean_code} {THEMA_CODE_MAPPING[clean_code]}"
    
    # If we don't have a mapping, return the original code
    return clean_code


class ThemaSubjectMappingStrategy(MappingStrategy):
    """
    A mapping strategy for Thema subject fields that ensures complete codes.
    """
    
    def __init__(self, metadata_field: str, default_value: str = ""):
        """
        Initialize the Thema subject mapping strategy.
        
        Args:
            metadata_field: The field in the metadata to map from
            default_value: Default value to use if the field is not found
        """
        self.metadata_field = metadata_field
        self.default_value = default_value
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Map the metadata field to a complete Thema subject.
        
        Args:
            metadata: The metadata object to map from
            context: Mapping context
            
        Returns:
            Complete Thema subject with code and description
        """
        # Get the raw value from the metadata
        raw_value = getattr(metadata, self.metadata_field, self.default_value)
        
        if not raw_value:
            return self.default_value
        
        # Expand the Thema code
        expanded = expand_thema_code(raw_value)
        
        # Log if we expanded the code
        if expanded != raw_value:
            logger.info(f"Expanded Thema subject from '{raw_value}' to '{expanded}'")
        
        return expanded