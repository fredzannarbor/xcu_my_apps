#!/usr/bin/env python3
"""
Pricing Strategy Module

Implements proper pricing field mapping strategies for LSI CSV generation.
"""

import logging
from typing import Any, Dict, Optional
from .pricing_formatter import PricingFormatter
from .field_mapping import MappingStrategy, MappingContext
from ..metadata.metadata_models import CodexMetadata

logger = logging.getLogger(__name__)


class PricingMappingStrategy(MappingStrategy):
    """Strategy for mapping pricing fields with proper formatting."""
    
    def __init__(self):
        """Initialize the pricing mapping strategy."""
        super().__init__()
        self.formatter = PricingFormatter()
        self.pricing_cache = {}  # Cache formatted prices to avoid recalculation
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Map pricing fields with proper formatting."""
        
        # Convert metadata to dict for the formatter
        source_data = metadata.to_dict() if hasattr(metadata, 'to_dict') else metadata.__dict__
        
        # Check if we've already calculated prices for this metadata
        metadata_id = id(metadata)  # Use object id as cache key
        if metadata_id not in self.pricing_cache:
            self.pricing_cache[metadata_id] = self.formatter.format_all_prices(source_data)
        
        formatted_prices = self.pricing_cache[metadata_id]
        
        # Return the formatted price for this field
        field_name = context.field_name
        if field_name in formatted_prices:
            value = formatted_prices[field_name]
            logger.debug(f"Mapped pricing field '{field_name}': {value}")
            return value
        else:
            # Field not found in pricing, return empty
            return ""
    
    def clear_cache(self):
        """Clear the pricing cache."""
        self.pricing_cache.clear()


class USPricingStrategy(PricingMappingStrategy):
    """Strategy specifically for US pricing fields."""
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Map US pricing fields."""
        field_name = context.field_name
        if 'US' not in field_name or 'List Price' not in field_name:
            return ""
        
        return super().map_field(metadata, context)


class TerritorialPricingStrategy(PricingMappingStrategy):
    """Strategy for territorial pricing fields (UK, EU, CA, AU)."""
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Map territorial pricing fields."""
        field_name = context.field_name
        territorial_markets = ['UK', 'EU', 'CA', 'AU']
        if not any(market in field_name for market in territorial_markets) or 'List Price' not in field_name:
            return ""
        
        return super().map_field(metadata, context)


class MarketPricingStrategy(PricingMappingStrategy):
    """Strategy for market-specific pricing fields (GC, USBR1, etc.)."""
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Map market-specific pricing fields."""
        field_name = context.field_name
        market_codes = ['GC', 'USBR1', 'USDE1', 'USRU1', 'USPL1', 'USKR1', 'USCN1', 'USIN1', 'USJP2', 'UAEUSD', 'US-Ingram-Only', 'US - Ingram - GAP', 'SIBI - EDUC - US']
        if not any(code in field_name for code in market_codes) or 'List Price' not in field_name:
            return ""
        
        return super().map_field(metadata, context)


class DiscountStrategy(PricingMappingStrategy):
    """Strategy for discount percentage fields."""
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Map discount percentage fields."""
        field_name = context.field_name
        if 'Discount' not in field_name:
            return ""
        
        return super().map_field(metadata, context)