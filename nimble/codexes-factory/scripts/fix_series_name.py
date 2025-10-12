#!/usr/bin/env python3

"""
Fix Series Name Issue

This script addresses the remaining Series Name field that's still blank.
"""

import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tranche_aware_series_strategy():
    """Create a tranche-aware series strategy."""
    
    strategy_code = '''
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
'''
    
    # Write the strategy file
    strategy_path = "src/codexes/modules/distribution/tranche_aware_series_strategy.py"
    with open(strategy_path, 'w') as f:
        f.write(strategy_code)
    
    logger.info(f"Created tranche-aware series strategy: {strategy_path}")
    return True


def update_field_mappings_for_series():
    """Update field mappings to use the tranche-aware series strategy."""
    
    mappings_path = "src/codexes/modules/distribution/enhanced_field_mappings.py"
    
    try:
        with open(mappings_path, 'r') as f:
            content = f.read()
        
        # Add import for new strategy
        import_addition = '''from .tranche_aware_series_strategy import TrancheAwareSeriesStrategy
'''
        
        # Find the imports section and add our import
        if "from .tranche_aware_series_strategy import" not in content:
            # Add after the existing enhanced strategies import
            import_pos = content.find("from .enhanced_file_path_strategies import")
            if import_pos != -1:
                end_pos = content.find("\n", import_pos) + 1
                content = content[:end_pos] + import_addition + content[end_pos:]
        
        # Replace the series name strategy
        old_series_strategy = '''    # Series Information (use tranche config if available, otherwise default)
    registry.register_strategy("Series Name", 
                             DefaultMappingStrategy("Transcriptive Meditation"))'''
        
        new_series_strategy = '''    # Series Information (tranche-aware strategy)
    registry.register_strategy("Series Name", 
                             TrancheAwareSeriesStrategy())'''
        
        if old_series_strategy in content:
            content = content.replace(old_series_strategy, new_series_strategy)
        else:
            # If not found, try to find just the Series Name registration
            old_pattern = '''registry.register_strategy("Series Name", 
                             DefaultMappingStrategy("Transcriptive Meditation"))'''
            new_pattern = '''registry.register_strategy("Series Name", 
                             TrancheAwareSeriesStrategy())'''
            content = content.replace(old_pattern, new_pattern)
        
        # Write the updated content
        with open(mappings_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Updated field mappings for series: {mappings_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update field mappings: {e}")
        return False


def main():
    """Main function to fix series name."""
    logger.info("Starting Series Name fix...")
    
    success = True
    
    # Create tranche-aware series strategy
    if not create_tranche_aware_series_strategy():
        success = False
    
    # Update field mappings
    if not update_field_mappings_for_series():
        success = False
    
    if success:
        logger.info("Series Name fix applied successfully!")
        logger.info("The Series Name field should now use the tranche configuration.")
    else:
        logger.error("Series Name fix failed. Please check the logs above.")
    
    return success


if __name__ == "__main__":
    main()