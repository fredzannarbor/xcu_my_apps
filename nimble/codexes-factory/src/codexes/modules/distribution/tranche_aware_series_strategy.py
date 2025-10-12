
"""
Tranche-Aware Series Strategy

This strategy gets the series name from tranche configuration.
"""

import logging
from typing import Dict, Any, Optional

from ..metadata.metadata_models import CodexMetadata
from .field_mapping import ComputedMappingStrategy, MappingContext

logger = logging.getLogger(__name__)


class TrancheAwareSeriesStrategy(ComputedMappingStrategy):
    """Series strategy that uses tranche configuration."""
    
    def __init__(self):
        """Initialize tranche-aware series strategy."""
        super().__init__(self._compute_series_name)
    
    def _compute_series_name(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Get series name from tranche configuration or fallback."""
        try:
            # Try to get from tranche configuration
            if context and hasattr(context, 'config') and context.config:
                series_info = context.config.get('series_info', {})
                series_name = series_info.get('series_name', '')
                if series_name:
                    logger.info(f"Using tranche series name: {series_name}")
                    return series_name
            
            # Try to get from metadata
            if hasattr(metadata, 'series_name') and metadata.series_name:
                logger.info(f"Using metadata series name: {metadata.series_name}")
                return metadata.series_name
            
            # Fallback to default
            default_series = "Transcriptive Meditation"
            logger.info(f"Using fallback series name: {default_series}")
            return default_series
            
        except Exception as e:
            logger.error(f"Error computing series name: {e}")
            return "Transcriptive Meditation"
