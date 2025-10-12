#!/usr/bin/env python3
"""
Pricing Formatter Module

Handles proper formatting of prices for LSI CSV generation.
Ensures all prices are decimal floats without currency symbols.
"""

import re
import logging
from typing import Optional, Dict, Any
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


class PricingFormatter:
    """Formats prices according to LSI requirements."""
    
    def __init__(self):
        """Initialize the pricing formatter."""
        # Exchange rates for territorial pricing
        self.exchange_rates = {
            'USD': 1.0,
            'GBP': 0.78,  # UK Pound
            'EUR': 0.85,  # Euro
            'CAD': 1.35,  # Canadian Dollar
            'AUD': 1.50,  # Australian Dollar
        }
        
        # Currency symbol patterns to remove
        self.currency_patterns = [
            r'\$',  # Dollar sign
            r'£',   # Pound sign
            r'€',   # Euro sign
            r'¥',   # Yen sign
            r'₹',   # Rupee sign
            r'C\$', # Canadian dollar
            r'A\$', # Australian dollar
        ]
    
    def clean_price_string(self, price_str: str) -> Optional[str]:
        """Remove currency symbols and clean price string."""
        if not price_str or price_str.strip() == '':
            return None
        
        # Remove currency symbols
        cleaned = str(price_str).strip()
        for pattern in self.currency_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # Remove any remaining non-numeric characters except decimal point
        cleaned = re.sub(r'[^0-9.]', '', cleaned)
        
        if not cleaned:
            return None
        
        try:
            # Validate it's a valid decimal
            decimal_value = Decimal(cleaned)
            # Format to 2 decimal places
            return f"{decimal_value:.2f}"
        except (InvalidOperation, ValueError):
            logger.warning(f"Invalid price format: {price_str}")
            return None
    
    def format_us_price(self, price: Any) -> Optional[str]:
        """Format US price as decimal float."""
        if price is None:
            return None
        
        # Handle different input types
        if isinstance(price, (int, float)):
            return f"{float(price):.2f}"
        elif isinstance(price, str):
            return self.clean_price_string(price)
        else:
            return self.clean_price_string(str(price))
    
    def calculate_territorial_price(self, us_price: str, target_currency: str) -> Optional[str]:
        """Calculate territorial price based on US price and exchange rate."""
        if not us_price or target_currency not in self.exchange_rates:
            return None
        
        try:
            us_decimal = Decimal(us_price)
            rate = Decimal(str(self.exchange_rates[target_currency]))
            territorial_price = us_decimal * rate
            return f"{territorial_price:.2f}"
        except (InvalidOperation, ValueError) as e:
            logger.warning(f"Error calculating territorial price: {e}")
            return None
    
    def format_all_prices(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Format all pricing fields according to LSI requirements."""
        formatted_prices = {}
        
        # Get and format US base price
        us_price_raw = (metadata.get('us_list_price') or 
                       metadata.get('list_price') or 
                       metadata.get('price') or
                       metadata.get('list_price_usd') or
                       metadata.get('List Price') or
                       metadata.get('US Suggested List Price'))
        us_price = self.format_us_price(us_price_raw)
        
        if us_price:
            # US pricing
            formatted_prices['US Suggested List Price'] = us_price
            
            # Calculate territorial prices
            uk_price = self.calculate_territorial_price(us_price, 'GBP')
            if uk_price:
                formatted_prices['UK Suggested List Price'] = uk_price
            
            eu_price = self.calculate_territorial_price(us_price, 'EUR')
            if eu_price:
                formatted_prices['EU Suggested List Price (mode 2)'] = eu_price
            
            ca_price = self.calculate_territorial_price(us_price, 'CAD')
            if ca_price:
                formatted_prices['CA Suggested List Price (mode 2)'] = ca_price
            
            au_price = self.calculate_territorial_price(us_price, 'AUD')
            if au_price:
                formatted_prices['AU Suggested List Price (mode 2)'] = au_price
            
            # GC and other markets should equal US list price
            formatted_prices['GC Suggested List Price (mode 2)'] = us_price
            formatted_prices['USBR1 Suggested List Price (mode 2)'] = us_price
            formatted_prices['USDE1 Suggested List Price (mode 2)'] = us_price
            formatted_prices['USRU1 Suggested List Price (mode 2)'] = us_price
            formatted_prices['USPL1 Suggested List Price (mode 2)'] = us_price
            formatted_prices['USKR1 Suggested List Price (mode 2)'] = us_price
            formatted_prices['USCN1 Suggested List Price (mode 2)'] = us_price
            formatted_prices['USIN1 Suggested List Price (mode 2)'] = us_price
            formatted_prices['USJP2 Suggested List Price(mode 2)'] = us_price
            formatted_prices['UAEUSD Suggested List Price (mode 2)'] = us_price
            formatted_prices['US-Ingram-Only* Suggested List Price (mode 2)'] = us_price
            formatted_prices['US - Ingram - GAP * Suggested List Price (mode 2)'] = us_price
            formatted_prices['SIBI - EDUC - US * Suggested List Price (mode 2)'] = us_price
        
        # Handle discount percentages (should be integers without % symbol)
        discount_fields = [
            'US Wholesale Discount',
            'UK Wholesale Discount (%)',
            'EU Wholesale Discount % (Mode 2)',
            'AU Wholesale Discount % (Mode 2)',
            'CA Wholesale Discount % (Mode 2)',
            'GC Wholesale Discount % (Mode 2)',
            'USBR1 Wholesale Discount % (Mode 2)',
            'USDE1 Wholesale Discount % (Mode 2)',
            'USRU1 Wholesale Discount % (Mode 2)',
            'USPL1 Wholesale Discount % (Mode 2)',
            'USKR1 Wholesale Discount % (Mode 2)',
            'USCN1 Wholesale Discount % (Mode 2)',
            'USIN1 Wholesale Discount % (Mode 2)',
            'USJP2 Wholesale Discount % (Mode 2)',
            'UAEUSD Wholesale Discount % (Mode 2)',
            'US-Ingram-Only* Wholesale Discount % (Mode 2)',
            'US - Ingram - GAP * Wholesale Discount % (Mode 2)',
            'SIBI - EDUC - US * Wholesale Discount % (Mode 2)'
        ]
        
        # Set standard discount rate (40% is common for POD)
        standard_discount = '40'
        for field in discount_fields:
            formatted_prices[field] = standard_discount
        
        logger.info(f"Formatted {len(formatted_prices)} pricing fields")
        return formatted_prices


def format_price_for_lsi(price: Any) -> Optional[str]:
    """Convenience function to format a single price for LSI."""
    formatter = PricingFormatter()
    return formatter.format_us_price(price)


def get_formatted_prices(metadata: Dict[str, Any]) -> Dict[str, str]:
    """Convenience function to get all formatted prices."""
    formatter = PricingFormatter()
    return formatter.format_all_prices(metadata)