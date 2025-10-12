"""
Enhanced Pricing Strategy

This module provides a unified pricing strategy for all LSI price fields,
ensuring proper decimal formatting and territorial price calculations.
"""

import logging
from typing import Dict, Any, Optional
from .currency_formatter import CurrencyFormatter
from .field_mapping import MappingStrategy

logger = logging.getLogger(__name__)


class EnhancedPricingStrategy(MappingStrategy):
    """
    Unified pricing strategy that handles all price fields with proper formatting
    and territorial price calculations.
    """
    
    def __init__(self, exchange_rates: Optional[Dict[str, float]] = None, 
                 default_discount: int = 40):
        """
        Initialize the enhanced pricing strategy.
        
        Args:
            exchange_rates: Dictionary of currency exchange rates
            default_discount: Default wholesale discount percentage
        """
        self.exchange_rates = exchange_rates or self._get_default_exchange_rates()
        self.default_discount = default_discount
        
        # Price field mappings
        self.price_field_mappings = {
            'US Suggested List Price': self._map_us_price,
            'UK Suggested List Price': self._map_uk_price,
            'EU Suggested List Price': self._map_eu_price,
            'CA Suggested List Price': self._map_ca_price,
            'AU Suggested List Price': self._map_au_price,
            'GC Suggested List Price': self._map_specialty_price,
            'USBR1 Suggested List Price (mode 2)': self._map_specialty_price,
            'USDE1 Suggested List Price (mode 2)': self._map_specialty_price,
            'USRU1 Suggested List Price (mode 2)': self._map_specialty_price,
            'USPL1 Suggested List Price (mode 2)': self._map_specialty_price,
            'USKR1 Suggested List Price (mode 2)': self._map_specialty_price,
            'USCN1 Suggested List Price (mode 2)': self._map_specialty_price,
            'USIN1 Suggested List Price (mode 2)': self._map_specialty_price,
            'USJP2 Suggested List Price(mode 2)': self._map_specialty_price,
            'UAEUSD Suggested List Price (mode 2)': self._map_specialty_price,
            'US-Ingram-Only* Suggested List Price (mode 2)': self._map_specialty_price,
            'US - Ingram - GAP * Suggested List Price (mode 2)': self._map_specialty_price,
            'SIBI - EDUC - US * Suggested List Price (mode 2)': self._map_specialty_price,
        }
        
        # Discount field mappings
        self.discount_field_mappings = {
            'US Wholesale Discount': self._map_wholesale_discount,
            'UK Wholesale Discount (%)': self._map_wholesale_discount,
            'EU Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
            'AU Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
            'CA Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
            'GC Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
            'USBR1 Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
            'USDE1 Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
            'USRU1 Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
            'USPL1 Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
            'USKR1 Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
            'USCN1 Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
            'USIN1 Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
            'USJP2 Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
            'UAEUSD Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
            'US-Ingram-Only* Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
            'US - Ingram - GAP * Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
            'SIBI - EDUC - US * Wholesale Discount % (Mode 2)': self._map_wholesale_discount,
        }
    
    def map_field(self, field_name: str, metadata: Dict[str, Any], 
                  config: Optional[Dict[str, Any]] = None) -> str:
        """
        Map a pricing field to its properly formatted value.
        
        Args:
            field_name: Name of the field to map
            metadata: Source metadata dictionary
            config: Optional configuration dictionary
            
        Returns:
            Formatted field value as string
        """
        try:
            # Handle price fields
            if field_name in self.price_field_mappings:
                return self.price_field_mappings[field_name](metadata, config)
            
            # Handle discount fields
            if field_name in self.discount_field_mappings:
                return self.discount_field_mappings[field_name](metadata, config)
            
            # Handle generic price fields
            if 'price' in field_name.lower() or 'list price' in field_name.lower():
                return self._map_generic_price(field_name, metadata, config)
            
            # Handle generic discount fields
            if 'discount' in field_name.lower():
                return self._map_wholesale_discount(metadata, config)
            
            # Not a pricing field
            return ""
            
        except Exception as e:
            logger.error(f"Error mapping pricing field '{field_name}': {e}")
            return ""
    
    def _get_base_us_price(self, metadata: Dict[str, Any], 
                          config: Optional[Dict[str, Any]] = None) -> float:
        """Get the base US price for calculations."""
        # Try various price field names
        price_fields = [
            'list_price', 'us_list_price', 'price', 'us_price',
            'US Suggested List Price', 'List Price'
        ]
        
        for field in price_fields:
            if field in metadata and metadata[field]:
                try:
                    return CurrencyFormatter.extract_numeric_value(str(metadata[field]))
                except (ValueError, TypeError):
                    continue
        
        # Try config default
        if config and 'default_price' in config:
            try:
                return CurrencyFormatter.extract_numeric_value(str(config['default_price']))
            except (ValueError, TypeError):
                pass
        
        # Default price
        return 19.95
    
    def _map_us_price(self, metadata: Dict[str, Any], 
                     config: Optional[Dict[str, Any]] = None) -> str:
        """Map US Suggested List Price field."""
        base_price = self._get_base_us_price(metadata, config)
        return CurrencyFormatter.format_decimal_price(base_price)
    
    def _map_uk_price(self, metadata: Dict[str, Any], 
                     config: Optional[Dict[str, Any]] = None) -> str:
        """Map UK Suggested List Price field."""
        base_price = self._get_base_us_price(metadata, config)
        uk_price = base_price * self.exchange_rates.get('GBP', 0.78)
        return CurrencyFormatter.format_decimal_price(uk_price)
    
    def _map_eu_price(self, metadata: Dict[str, Any], 
                     config: Optional[Dict[str, Any]] = None) -> str:
        """Map EU Suggested List Price field."""
        base_price = self._get_base_us_price(metadata, config)
        eu_price = base_price * self.exchange_rates.get('EUR', 0.85)
        return CurrencyFormatter.format_decimal_price(eu_price)
    
    def _map_ca_price(self, metadata: Dict[str, Any], 
                     config: Optional[Dict[str, Any]] = None) -> str:
        """Map CA Suggested List Price field."""
        base_price = self._get_base_us_price(metadata, config)
        ca_price = base_price * self.exchange_rates.get('CAD', 1.35)
        return CurrencyFormatter.format_decimal_price(ca_price)
    
    def _map_au_price(self, metadata: Dict[str, Any], 
                     config: Optional[Dict[str, Any]] = None) -> str:
        """Map AU Suggested List Price field."""
        base_price = self._get_base_us_price(metadata, config)
        au_price = base_price * self.exchange_rates.get('AUD', 1.50)
        return CurrencyFormatter.format_decimal_price(au_price)
    
    def _map_specialty_price(self, metadata: Dict[str, Any], 
                           config: Optional[Dict[str, Any]] = None) -> str:
        """Map specialty market prices (equal to US price)."""
        base_price = self._get_base_us_price(metadata, config)
        return CurrencyFormatter.format_decimal_price(base_price)

    def _map_Ingram_special_program_prices(self, metadata, config):
        """Map Ingram special program prices to empty by default"""
        base_price = ""
        return base_price


    
    def _map_generic_price(self, field_name: str, metadata: Dict[str, Any], 
                          config: Optional[Dict[str, Any]] = None) -> str:
        """Map generic price fields."""
        # Try to find field-specific value first
        field_key = field_name.lower().replace(' ', '_')
        if field_key in metadata and metadata[field_key]:
            return CurrencyFormatter.format_decimal_price(metadata[field_key])
        
        # Fall back to base US price
        base_price = self._get_base_us_price(metadata, config)
        return CurrencyFormatter.format_decimal_price(base_price)
    
    def _map_wholesale_discount(self, metadata: Dict[str, Any], 
                              config: Optional[Dict[str, Any]] = None) -> str:
        """Map wholesale discount fields."""
        # Try various discount field names
        discount_fields = [
            'wholesale_discount', 'discount', 'us_wholesale_discount'
        ]
        
        for field in discount_fields:
            if field in metadata and metadata[field]:
                return CurrencyFormatter.format_wholesale_discount(metadata[field])
        
        # Try config default
        if config and 'default_discount' in config:
            return CurrencyFormatter.format_wholesale_discount(config['default_discount'])
        
        # Use instance default
        return str(self.default_discount)
    
    def _get_default_exchange_rates(self) -> Dict[str, float]:
        """Get default exchange rates for territorial pricing."""
        return {
            'GBP': 0.78,  # USD to GBP
            'EUR': 0.85,  # USD to EUR
            'CAD': 1.35,  # USD to CAD
            'AUD': 1.50,  # USD to AUD
            'JPY': 110.0, # USD to JPY
            'INR': 75.0,  # USD to INR
            'KRW': 1200.0, # USD to KRW
        }
    
    def get_supported_fields(self) -> list:
        """Get list of all supported pricing fields."""
        return list(self.price_field_mappings.keys()) + list(self.discount_field_mappings.keys())
    
    def is_pricing_field(self, field_name: str) -> bool:
        """Check if a field is a pricing field handled by this strategy."""
        return (field_name in self.price_field_mappings or 
                field_name in self.discount_field_mappings or
                'price' in field_name.lower() or 
                'discount' in field_name.lower())
    
    def calculate_all_territorial_prices(self, base_price: float) -> Dict[str, str]:
        """
        Calculate all territorial prices from base US price.
        
        Args:
            base_price: Base US price as float
            
        Returns:
            Dictionary of formatted territorial prices
        """
        return {
            'US': CurrencyFormatter.format_decimal_price(base_price),
            'UK': CurrencyFormatter.format_decimal_price(base_price * self.exchange_rates.get('GBP', 0.78)),
            'EU': CurrencyFormatter.format_decimal_price(base_price * self.exchange_rates.get('EUR', 0.85)),
            'CA': CurrencyFormatter.format_decimal_price(base_price * self.exchange_rates.get('CAD', 1.35)),
            'AU': CurrencyFormatter.format_decimal_price(base_price * self.exchange_rates.get('AUD', 1.50)),
        }
    
    def get_strategy_name(self) -> str:
        """Get the name of this strategy."""
        return "EnhancedPricingStrategy"