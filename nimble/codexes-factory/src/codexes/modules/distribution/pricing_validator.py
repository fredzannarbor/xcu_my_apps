"""
Pricing validator to ensure USD prices are supplied for USD markets.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class PricingValidator:
    """Validates and ensures proper pricing for different markets."""
    
    def __init__(self):
        self.default_usd_prices = {
            'paperback': 12.99,
            'hardcover': 24.99,
            'ebook': 7.99
        }
    
    def validate_usd_pricing(self, book_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and ensure USD pricing is present.
        
        Args:
            book_data: Book data dictionary
            
        Returns:
            Updated book data with validated USD pricing
        """
        try:
            # Check for existing USD prices
            usd_prices = book_data.get('usd_prices', {})
            
            if not usd_prices:
                logger.warning("No USD prices found, applying defaults")
                usd_prices = self.default_usd_prices.copy()
                book_data['usd_prices'] = usd_prices
            else:
                # Validate existing prices
                for format_type, default_price in self.default_usd_prices.items():
                    if format_type not in usd_prices or not usd_prices[format_type]:
                        logger.warning(f"Missing USD price for {format_type}, using default: ${default_price}")
                        usd_prices[format_type] = default_price
            
            # Ensure prices are reasonable
            for format_type, price in usd_prices.items():
                if not isinstance(price, (int, float)) or price <= 0:
                    logger.warning(f"Invalid price for {format_type}: {price}, using default")
                    usd_prices[format_type] = self.default_usd_prices.get(format_type, 9.99)
            
            # Add pricing metadata
            book_data['pricing_validated'] = True
            book_data['pricing_currency'] = 'USD'
            book_data['pricing_last_updated'] = self._get_current_timestamp()
            
            logger.info(f"✅ USD pricing validated: {usd_prices}")
            return book_data
            
        except Exception as e:
            logger.error(f"Error validating USD pricing: {e}")
            # Apply defaults on error
            book_data['usd_prices'] = self.default_usd_prices.copy()
            book_data['pricing_validated'] = False
            return book_data
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def generate_pricing_summary(self, book_data: Dict[str, Any]) -> str:
        """
        Generate a pricing summary for the book.
        
        Args:
            book_data: Book data with pricing information
            
        Returns:
            Formatted pricing summary string
        """
        usd_prices = book_data.get('usd_prices', {})
        
        if not usd_prices:
            return "Pricing information not available."
        
        summary_lines = ["Available formats and pricing (USD):"]
        
        for format_type, price in usd_prices.items():
            formatted_price = f"${price:.2f}"
            format_name = format_type.replace('_', ' ').title()
            summary_lines.append(f"• {format_name}: {formatted_price}")
        
        return "\n".join(summary_lines)