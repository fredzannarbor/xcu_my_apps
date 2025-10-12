"""
Currency Formatter Utility

This module provides utilities for formatting prices as decimal numbers
without currency symbols, ensuring LSI compliance.
"""

import re
import logging
from typing import Union, Optional

logger = logging.getLogger(__name__)


class CurrencyFormatter:
    """Utility class for formatting currency values for LSI CSV output."""
    
    # Common currency symbols to remove
    CURRENCY_SYMBOLS = ['$', '£', '€', '¥', '₹', '₽', 'C$', 'A$', 'NZ$', '¢', '₩', '₪']
    
    # Regex pattern to match currency symbols and formatting
    CURRENCY_PATTERN = re.compile(r'[\$£€¥₹₽¢₩₪]|C\$|A\$|NZ\$|USD|GBP|EUR|CAD|AUD|JPY|INR|RUB|KRW|ILS')
    
    @classmethod
    def format_decimal_price(cls, price_input: Union[str, float, int]) -> str:
        """
        Convert price input to decimal format without currency symbols.
        
        Args:
            price_input: Price as string, float, or int
            
        Returns:
            Formatted price as decimal string (e.g., "19.95")
            
        Examples:
            "$19.95" -> "19.95"
            "£15.99" -> "15.99"
            "€18.50" -> "18.50"
            19.95 -> "19.95"
            "0" -> "0.00"
        """
        if price_input is None or price_input == '':
            return "0.00"
        
        try:
            # Handle numeric inputs
            if isinstance(price_input, (int, float)):
                return f"{float(price_input):.2f}"
            
            # Handle string inputs
            price_str = str(price_input).strip()
            if not price_str:
                return "0.00"
            
            # Extract numeric value
            numeric_value = cls.extract_numeric_value(price_str)
            
            # Format to 2 decimal places
            return f"{numeric_value:.2f}"
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to format price '{price_input}': {e}")
            return "0.00"
    
    @classmethod
    def extract_numeric_value(cls, price_str: str) -> float:
        """
        Extract numeric value from price string, removing currency symbols.
        
        Args:
            price_str: Price string with potential currency symbols
            
        Returns:
            Numeric value as float
            
        Examples:
            "$19.95" -> 19.95
            "£15.99" -> 15.99
            "19,95 €" -> 19.95
            "C$26.95" -> 26.95
        """
        if not price_str or not isinstance(price_str, str):
            return 0.0
        
        # Remove whitespace
        clean_str = price_str.strip()
        
        if not clean_str:
            return 0.0
        
        # Remove currency symbols using regex
        clean_str = cls.CURRENCY_PATTERN.sub('', clean_str)
        
        # Remove any remaining non-numeric characters except decimal points and commas
        clean_str = re.sub(r'[^\d.,\-]', '', clean_str)
        
        # Handle European decimal format (comma as decimal separator)
        if ',' in clean_str and '.' in clean_str:
            # Format like "1,234.56" - comma is thousands separator
            clean_str = clean_str.replace(',', '')
        elif ',' in clean_str and clean_str.count(',') == 1:
            # Check if comma is likely decimal separator (European format)
            parts = clean_str.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Likely decimal separator: "19,95" -> "19.95"
                clean_str = clean_str.replace(',', '.')
        
        # Remove any remaining commas (thousands separators)
        clean_str = clean_str.replace(',', '')
        
        # Handle empty string after cleaning
        if not clean_str or clean_str == '.':
            return 0.0
        
        try:
            return float(clean_str)
        except ValueError:
            logger.warning(f"Could not parse numeric value from '{price_str}' -> '{clean_str}'")
            return 0.0
    
    @classmethod
    def validate_decimal_format(cls, price_str: str) -> bool:
        """
        Validate that price string is in proper decimal format for LSI.
        
        Args:
            price_str: Price string to validate
            
        Returns:
            True if valid decimal format, False otherwise
            
        Examples:
            "19.95" -> True
            "$19.95" -> False
            "19.950" -> False (too many decimal places)
            "19" -> False (missing decimal places)
        """
        if not price_str or not isinstance(price_str, str):
            return False
        
        # Check for currency symbols
        if cls.CURRENCY_PATTERN.search(price_str):
            return False
        
        # Check decimal format with exactly 2 decimal places
        decimal_pattern = re.compile(r'^\d+\.\d{2}$')
        return bool(decimal_pattern.match(price_str.strip()))
    
    @classmethod
    def format_wholesale_discount(cls, discount_input: Union[str, int, float]) -> str:
        """
        Format wholesale discount as integer string without percentage symbol.
        
        Args:
            discount_input: Discount as string, int, or float
            
        Returns:
            Formatted discount as integer string (e.g., "40")
            
        Examples:
            "40%" -> "40"
            40.0 -> "40"
            "40.5%" -> "41" (rounded)
        """
        if discount_input is None or discount_input == '':
            return "40"  # Default discount
        
        try:
            # Handle numeric inputs
            if isinstance(discount_input, (int, float)):
                return str(int(round(discount_input)))
            
            # Handle string inputs
            discount_str = str(discount_input).strip()
            if not discount_str:
                return "40"
            
            # Remove percentage symbol and other non-numeric characters
            clean_str = re.sub(r'[^\d.]', '', discount_str)
            
            if not clean_str:
                return "40"
            
            # Convert to integer (rounded)
            discount_value = float(clean_str)
            return str(int(round(discount_value)))
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to format discount '{discount_input}': {e}")
            return "40"  # Default discount
    
    @classmethod
    def clean_price_fields(cls, data: dict) -> dict:
        """
        Clean all price fields in a data dictionary.
        
        Args:
            data: Dictionary containing price fields
            
        Returns:
            Dictionary with cleaned price fields
        """
        price_fields = [
            'US Suggested List Price',
            'UK Suggested List Price', 
            'EU Suggested List Price',
            'CA Suggested List Price',
            'AU Suggested List Price',
            'GC Suggested List Price',
            'List Price',
            'list_price'
        ]
        
        discount_fields = [
            'US Wholesale Discount',
            'UK Wholesale Discount',
            'EU Wholesale Discount',
            'CA Wholesale Discount',
            'AU Wholesale Discount',
            'wholesale_discount'
        ]
        
        cleaned_data = data.copy()
        
        # Clean price fields
        for field in price_fields:
            if field in cleaned_data:
                cleaned_data[field] = cls.format_decimal_price(cleaned_data[field])
        
        # Clean discount fields
        for field in discount_fields:
            if field in cleaned_data:
                cleaned_data[field] = cls.format_wholesale_discount(cleaned_data[field])
        
        return cleaned_data