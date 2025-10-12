"""
Contributor Role Mapping Module

This module provides specialized mapping strategies for contributor role fields
with validation against LSI's valid contributor codes.
"""

import logging
from typing import Optional

from .field_mapping import MappingStrategy, MappingContext
from .contributor_role_validator import ContributorRoleValidator
from ..metadata.metadata_models import CodexMetadata

logger = logging.getLogger(__name__)


class ContributorRoleMappingStrategy(MappingStrategy):
    """
    A mapping strategy for contributor role fields with validation.
    """
    
    def __init__(self, metadata_field: str, default_value: str = "A"):
        """
        Initialize the contributor role mapping strategy.
        
        Args:
            metadata_field: The field in the metadata to map from
            default_value: Default value to use if the field is not found
        """
        self.metadata_field = metadata_field
        self.default_value = default_value
        self.validator = ContributorRoleValidator()
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Map the metadata field to a valid contributor role code.
        
        Args:
            metadata: The metadata object to map from
            context: Mapping context
            
        Returns:
            Valid contributor role code
        """
        # Get the raw value from the metadata
        raw_value = getattr(metadata, self.metadata_field, self.default_value)
        
        if not raw_value:
            logger.info(f"No contributor role found for {self.metadata_field}, using default '{self.default_value}'")
            return self.default_value
        
        # Validate and correct if necessary
        is_valid, corrected_code, error_message = self.validator.validate_and_correct(raw_value)
        
        if not is_valid:
            logger.warning(error_message)
        
        return corrected_code