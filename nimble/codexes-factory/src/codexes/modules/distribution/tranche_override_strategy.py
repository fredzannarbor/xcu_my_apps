
"""
Tranche Override Strategy

This strategy checks for direct field mappings in tranche configuration
and uses them to override default strategies.
"""

import logging
from typing import Dict, Any, Optional

from ..metadata.metadata_models import CodexMetadata
from .field_mapping import ComputedMappingStrategy, MappingContext

logger = logging.getLogger(__name__)


class TrancheOverrideStrategy(ComputedMappingStrategy):
    """Strategy that uses direct field mappings from tranche configuration."""
    
    def __init__(self, field_name: str, fallback_value: str = ""):
        """
        Initialize tranche override strategy.
        
        Args:
            field_name: The LSI field name to look for in tranche config
            fallback_value: Fallback value if not found in tranche config
        """
        self.field_name = field_name
        self.fallback_value = fallback_value
        super().__init__(self._compute_field_value)
    
    def _compute_field_value(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Get field value from tranche configuration or fallback."""
        try:
            # First, try to get from tranche configuration using multi-level config
            if hasattr(context, 'multi_level_config') and context.multi_level_config:
                from .multi_level_config import ConfigurationContext
                
                # Create configuration context
                config_context = ConfigurationContext(
                    tranche_name=getattr(context, 'tranche_name', None),
                    imprint_name=getattr(metadata, 'imprint', None),
                    publisher_name=getattr(metadata, 'publisher', None)
                )
                
                # Get value from multi-level config
                value = context.multi_level_config.get_value(self.field_name, config_context)
                if value:
                    logger.info(f"Using tranche override for {self.field_name}: {value[:50]}...")
                    return str(value)
            
            # Try to get from context config (legacy support)
            if context and hasattr(context, 'config') and context.config:
                if self.field_name in context.config:
                    value = context.config[self.field_name]
                    logger.info(f"Using context config for {self.field_name}: {value[:50]}...")
                    return str(value)
            
            # Try to get from metadata
            metadata_field = self.field_name.lower().replace(' ', '_')
            if hasattr(metadata, metadata_field):
                value = getattr(metadata, metadata_field)
                if value:
                    logger.info(f"Using metadata for {self.field_name}: {value[:50]}...")
                    return str(value)
            
            # Use fallback
            if self.fallback_value:
                logger.info(f"Using fallback for {self.field_name}: {self.fallback_value[:50]}...")
                return self.fallback_value
            
            logger.debug(f"No value found for {self.field_name}")
            return ""
            
        except Exception as e:
            logger.error(f"Error computing {self.field_name}: {e}")
            return self.fallback_value
