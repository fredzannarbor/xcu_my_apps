"""
BISAC Field Mapping Module

This module provides specialized mapping strategies for BISAC subject fields.
"""

import logging
from typing import Dict, Any, Optional

from .field_mapping import MappingStrategy, MappingContext
from .bisac_utils import strip_bisac_code
from ..metadata.metadata_models import CodexMetadata

logger = logging.getLogger(__name__)


class BisacCategoryMappingStrategy(MappingStrategy):
    """
    A mapping strategy that strips codes from BISAC subject fields.
    """
    
    def __init__(self, metadata_field: str, default_value: str = "", is_primary: bool = False):
        """
        Initialize the BISAC category mapping strategy.
        
        Args:
            metadata_field: The field in the metadata to map from
            default_value: Default value to use if the field is not found
            is_primary: Whether this is the primary BISAC category (for tranche override)
        """
        self.metadata_field = metadata_field
        self.default_value = default_value
        self.is_primary = is_primary
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Map the metadata field to a BISAC category, stripping any codes.
        
        Args:
            metadata: The metadata object to map from
            context: Mapping context
            
        Returns:
            The BISAC category without the code
        """
        # Check for tranche override if this is the primary BISAC category
        if self.is_primary and context and hasattr(context, 'config') and context.config:
            tranche_bisac = context.config.get('tranche_bisac_subject')
            if tranche_bisac:
                return strip_bisac_code(tranche_bisac)
        
        # Get the raw value from the metadata
        raw_value = getattr(metadata, self.metadata_field, self.default_value)
        
        if not raw_value:
            return self.default_value
        
        # Strip the code from the BISAC subject
        return strip_bisac_code(raw_value)