"""
GC Market Pricing Module

This module provides functionality for setting GC market prices equal to US price.
"""

import logging
from typing import Dict, Any, Optional, List

from .field_mapping import MappingStrategy, MappingContext
from ..metadata.metadata_models import CodexMetadata

logger = logging.getLogger(__name__)


class GCMarketPricingStrategy(MappingStrategy):
    """
    Strategy for setting GC market prices equal to US price.
    """
    
    def __init__(self):
        """Initialize GC market pricing strategy."""
        pass
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Map GC market price to US price.
        
        Args:
            metadata: The source CodexMetadata object
            context: Additional context for the mapping operation
            
        Returns:
            String value for the GC market price field
        """
        try:
            # Get US price from metadata
            us_price = metadata.list_price_usd
            if not us_price:
                return ""
            
            # Convert to float if needed
            if isinstance(us_price, str):
                # Remove dollar sign if present
                us_price = us_price.replace('$', '')
                try:
                    us_price = float(us_price)
                except ValueError:
                    return ""
            
            # Format as US price
            return f"${us_price:.2f}"
        except Exception as e:
            logger.warning(f"Error computing GC market price: {e}")
            return ""
    
    def validate_input(self, metadata: CodexMetadata, context: MappingContext) -> bool:
        """
        Validates that the input is suitable for this mapping strategy.
        
        Args:
            metadata: The source CodexMetadata object
            context: Additional context for the mapping operation
            
        Returns:
            True if input is valid, False otherwise
        """
        # Check if US price is available
        return hasattr(metadata, 'list_price_usd') and metadata.list_price_usd is not None


def register_gc_market_pricing_strategies(registry):
    """
    Register GC market pricing strategies with the field mapping registry.
    
    Args:
        registry: FieldMappingRegistry to register strategies with
    """
    # Create GC market pricing strategy
    gc_strategy = GCMarketPricingStrategy()
    
    # Register for GC market price field
    registry.register_strategy("GC Suggested List Price (mode 2)", gc_strategy)
    
    # Register for US-prefixed territory price fields
    us_territories = ["USBR1", "USDE1", "USRU1", "USPL1", "USKR1", "USCN1", "USIN1", "USJP2", "UAEUSD"]
    for territory in us_territories:
        registry.register_strategy(f"{territory} Suggested List Price (mode 2)", gc_strategy)
    
    logger.info("Registered GC market pricing strategies")