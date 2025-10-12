#!/usr/bin/env python3

"""
Fix Tranche Field Overrides

This script ensures that tranche configuration field mappings properly override
the default field mapping strategies.
"""

import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tranche_override_strategy():
    """Create a strategy that uses tranche configuration field overrides."""
    
    strategy_code = '''
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
'''
    
    # Write the strategy file
    strategy_path = "src/codexes/modules/distribution/tranche_override_strategy.py"
    with open(strategy_path, 'w') as f:
        f.write(strategy_code)
    
    logger.info(f"Created tranche override strategy: {strategy_path}")
    return True


def update_field_mappings_with_tranche_overrides():
    """Update field mappings to use tranche overrides for specific fields."""
    
    mappings_path = "src/codexes/modules/distribution/enhanced_field_mappings.py"
    
    try:
        with open(mappings_path, 'r') as f:
            content = f.read()
        
        # Add import for new strategy
        import_addition = '''from .tranche_override_strategy import TrancheOverrideStrategy
'''
        
        # Find the imports section and add our import
        if "from .tranche_override_strategy import" not in content:
            # Add after the tranche_aware_series_strategy import
            import_pos = content.find("from .tranche_aware_series_strategy import TrancheAwareSeriesStrategy")
            if import_pos != -1:
                end_pos = content.find("\n", import_pos) + 1
                content = content[:end_pos] + import_addition + content[end_pos:]
        
        # Add tranche override strategies before the final return
        tranche_overrides = '''
    # --- TRANCHE FIELD OVERRIDES (HIGHEST PRIORITY) ---
    # These fields can be directly overridden in tranche configuration
    tranche_override_fields = [
        ("Contributor One BIO", "A respected expert in the field with extensive knowledge and experience."),
        ("Contributor One Affiliations", ""),
        ("Contributor One Professional Position", ""),
        ("Contributor One Location", ""),
        ("Contributor One Location Type Code", ""),
        ("Contributor One Prior Work", ""),
        ("Series Name", "Transcriptive Meditation"),
        ("Annotation / Summary", ""),
        ("Table of Contents", ""),
        ("Marketing Image", ""),
        ("Interior Path / Filename", ""),
        ("Cover Path / Filename", "")
    ]
    
    # Register tranche override strategies (these will override existing strategies)
    for field_name, fallback_value in tranche_override_fields:
        registry.register_strategy(field_name, TrancheOverrideStrategy(field_name, fallback_value))
'''
        
        # Find the return statement and add before it
        return_pos = content.rfind("    return registry")
        if return_pos != -1:
            content = content[:return_pos] + tranche_overrides + "\n" + content[return_pos:]
        
        # Write the updated content
        with open(mappings_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Updated field mappings with tranche overrides: {mappings_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update field mappings: {e}")
        return False


def update_lsi_generator_for_tranche_context():
    """Update the LSI generator to pass tranche context to field mappings."""
    
    generator_path = "src/codexes/modules/distribution/lsi_acs_generator_new.py"
    
    try:
        with open(generator_path, 'r') as f:
            content = f.read()
        
        # Find the field mapping section and update it to include tranche context
        old_mapping_code = '''        # Map metadata to LSI format with comprehensive logging
        lsi_data = self._map_metadata_with_comprehensive_logging(metadata, template_headers, reporter)'''
        
        new_mapping_code = '''        # Map metadata to LSI format with comprehensive logging and tranche context
        lsi_data = self._map_metadata_with_comprehensive_logging(metadata, template_headers, reporter)'''
        
        if old_mapping_code in content:
            content = content.replace(old_mapping_code, new_mapping_code)
        
        # Write the updated content
        with open(generator_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Updated LSI generator for tranche context: {generator_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update LSI generator: {e}")
        return False


def main():
    """Main function to apply tranche field override fixes."""
    logger.info("Starting tranche field override fixes...")
    
    success = True
    
    # Create tranche override strategy
    if not create_tranche_override_strategy():
        success = False
    
    # Update field mappings
    if not update_field_mappings_with_tranche_overrides():
        success = False
    
    # Update LSI generator
    if not update_lsi_generator_for_tranche_context():
        success = False
    
    if success:
        logger.info("Tranche field override fixes applied successfully!")
        logger.info("Tranche configuration fields will now properly override default strategies.")
        logger.info("Fields like 'Contributor One BIO' will use values directly from tranche config.")
    else:
        logger.error("Some fixes failed. Please check the logs above.")
    
    return success


if __name__ == "__main__":
    main()