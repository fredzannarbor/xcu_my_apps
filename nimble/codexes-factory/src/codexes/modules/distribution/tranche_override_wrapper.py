"""
Tranche Override Wrapper for Field Mapping Strategies

This module provides a wrapper that applies tranche overrides to existing
field mapping strategies, implementing the precedence logic for tranche
configuration values over LLM-generated values.
"""

from typing import Any, Dict, Optional
import logging

from .field_mapping import MappingStrategy, MappingContext
from .tranche_override_manager import TrancheOverrideManager
from ..metadata.metadata_models import CodexMetadata

logger = logging.getLogger(__name__)


class TrancheOverrideWrapper(MappingStrategy):
    """
    Wrapper that applies tranche overrides to existing mapping strategies.
    
    This wrapper executes the base strategy first, then applies tranche
    overrides according to the configured precedence rules.
    """
    
    def __init__(self, base_strategy: MappingStrategy, override_manager: TrancheOverrideManager):
        """
        Initialize the tranche override wrapper.
        
        Args:
            base_strategy: The base mapping strategy to wrap
            override_manager: Manager for tranche override logic
        """
        self.base_strategy = base_strategy
        self.override_manager = override_manager
        
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Map field using base strategy, then apply tranche overrides.
        
        Args:
            metadata: Source CodexMetadata object
            context: Mapping context with field information
            
        Returns:
            Final field value after applying overrides
        """
        try:
            # Get the base value from the wrapped strategy
            base_value = self.base_strategy.map_field(metadata, context)
            
            # Apply tranche overrides
            field_name = context.field_name
            final_value = self.override_manager.apply_overrides(
                field_name=field_name,
                llm_value=base_value,
                tranche_value=None,  # Will be looked up from config
                field_type="replace"  # Default, will be determined by manager
            )
            
            # Log override application if value changed
            if final_value != base_value:
                override_type = self.override_manager.get_override_type(field_name)
                logger.debug(f"Applied {override_type} override for field '{field_name}': "
                           f"'{base_value}' -> '{final_value}'")
            
            return final_value
            
        except Exception as e:
            logger.error(f"Error in tranche override wrapper for field '{context.field_name}': {e}")
            # Fall back to base strategy on error
            try:
                return self.base_strategy.map_field(metadata, context)
            except Exception as fallback_error:
                logger.error(f"Fallback strategy also failed: {fallback_error}")
                return ""
                
    def validate_input(self, metadata: CodexMetadata, context: MappingContext) -> bool:
        """
        Validate input using the base strategy's validation.
        
        Args:
            metadata: Source CodexMetadata object
            context: Mapping context
            
        Returns:
            True if input is valid for the base strategy
        """
        return self.base_strategy.validate_input(metadata, context)


def wrap_registry_with_tranche_overrides(registry, tranche_config: Optional[Dict[str, Any]] = None):
    """
    Wrap all strategies in a registry with tranche override functionality.
    
    Args:
        registry: FieldMappingRegistry to wrap
        tranche_config: Tranche configuration dictionary
        
    Returns:
        Modified registry with wrapped strategies
    """
    if not tranche_config:
        logger.debug("No tranche config provided, skipping override wrapping")
        return registry
        
    override_manager = TrancheOverrideManager(tranche_config)
    
    # Get all registered fields
    registered_fields = registry.get_registered_fields()
    
    # Wrap each strategy with tranche override functionality
    for field_name in registered_fields:
        base_strategy = registry.get_strategy(field_name)
        if base_strategy:
            wrapped_strategy = TrancheOverrideWrapper(base_strategy, override_manager)
            registry.register_strategy(field_name, wrapped_strategy)
            logger.debug(f"Wrapped strategy for field '{field_name}' with tranche overrides")
    
    logger.info(f"Wrapped {len(registered_fields)} strategies with tranche override functionality")
    return registry


class TrancheAwareStrategy(MappingStrategy):
    """
    Base class for strategies that are inherently tranche-aware.
    
    These strategies can access tranche configuration directly and don't
    need to be wrapped with TrancheOverrideWrapper.
    """
    
    def __init__(self):
        """Initialize tranche-aware strategy."""
        pass
        
    def get_tranche_config(self, context: MappingContext) -> Dict[str, Any]:
        """
        Get tranche configuration from context.
        
        Args:
            context: Mapping context
            
        Returns:
            Tranche configuration dictionary
        """
        if context and context.config:
            return context.config.get('tranche_config', {})
        return {}
        
    def get_tranche_override(self, field_name: str, context: MappingContext) -> Any:
        """
        Get tranche override value for a specific field.
        
        Args:
            field_name: Name of the field
            context: Mapping context
            
        Returns:
            Override value or None if not configured
        """
        tranche_config = self.get_tranche_config(context)
        field_overrides = tranche_config.get('field_overrides', {})
        return field_overrides.get(field_name)
        
    def is_append_field(self, field_name: str, context: MappingContext) -> bool:
        """
        Check if field should use append behavior.
        
        Args:
            field_name: Name of the field
            context: Mapping context
            
        Returns:
            True if field should append tranche value
        """
        tranche_config = self.get_tranche_config(context)
        append_fields = set(tranche_config.get('append_fields', []))
        return field_name in append_fields