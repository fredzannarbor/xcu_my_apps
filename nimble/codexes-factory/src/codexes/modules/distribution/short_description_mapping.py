"""
Short Description Mapping Module

This module provides specialized mapping strategies for short description fields
with length validation and truncation.
"""

import logging
from typing import Optional

from .field_mapping import MappingStrategy, MappingContext
from .text_length_validator import validate_and_truncate_short_description
from ..metadata.metadata_models import CodexMetadata

logger = logging.getLogger(__name__)


class ShortDescriptionMappingStrategy(MappingStrategy):
    """
    A mapping strategy for short description fields with length validation.
    """
    
    def __init__(self, metadata_field: str, max_bytes: int = 350, default_value: str = ""):
        """
        Initialize the short description mapping strategy.
        
        Args:
            metadata_field: The field in the metadata to map from
            max_bytes: Maximum allowed byte length (default: 350)
            default_value: Default value to use if the field is not found
        """
        self.metadata_field = metadata_field
        self.max_bytes = max_bytes
        self.default_value = default_value
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Map the metadata field to a short description, validating and truncating if necessary.
        
        Args:
            metadata: The metadata object to map from
            context: Mapping context
            
        Returns:
            Valid short description that doesn't exceed the maximum byte length
        """
        # Get the raw value from the metadata
        raw_value = getattr(metadata, self.metadata_field, self.default_value)
        
        if not raw_value:
            return self.default_value
        
        # Validate and truncate if necessary
        return validate_and_truncate_short_description(raw_value, self.max_bytes)