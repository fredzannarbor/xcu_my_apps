"""
Tests for Currency Formatter Utility
"""

import pytest
from codexes.modules.distribution.currency_formatter import CurrencyFormatter


class TestCurrencyFormatter:
    """Test cases for CurrencyFormatter class."""
    
    def test_format_decimal_price_with_dollar_symbol(self):
        """Test formatting price with dollar symbol."""
        assert CurrencyFormatter.format_decimal_price("$19.95") == "19.95"
        assert CurrencyFormatter.format_decimal_price("$0.99") == "0.99"
        assert CurrencyFormatter.format_decimal_price("$100.00") == "100.00"
    
    def test_format_decimal_price_with_pound_symbol(self):
        """Test formatting price with pound symbol."""
        assert CurrencyFormatter.format_decimal_price("£15.99") == "15.99"
        assert CurrencyFormatter.format_decimal_price("£0.50") == "0.50"
        assert CurrencyFormatter.format_decimal_price("£250.75") == "250.75"
    
    def test_format_decimal_price_with_euro_symbol(self):
        """Test formatting price with euro symbol."""
        assert CurrencyFormatter.format_decimal_price("€18.50") == "18.50"
        assert CurrencyFormatter.format_decimal_price("18.50 €") == "18.50"
        assert CurrencyFormatter.format_decimal_price("€0.01") == "0.01"
    
    def test_format_decimal_price_with_canadian_dollar(self):
        """Test formatting price with Canadian dollar symbol."""
        assert CurrencyFormatter.format_decimal_price("C$26.95") == "26.95"
        assert CurrencyFormatter.format_decimal_price("CAD 26.95") == "26.95"
    
    def test_format_decimal_price_with_australian_dollar(self):
        """Test formatting price with Australian dollar symbol."""
        assert CurrencyFormatter.format_decimal_price("A$29.95") == "29.95"
        assert CurrencyFormatter.format_decimal_price("AUD 29.95") == "29.95"
    
    def test_format_decimal_price_numeric_inputs(self):
        """Test formatting with numeric inputs."""
        assert CurrencyFormatter.format_decimal_price(19.95) == "19.95"
        assert CurrencyFormatter.format_decimal_price(19) == "19.00"
        assert CurrencyFormatter.format_decimal_price(0) == "0.00"
        assert CurrencyFormatter.format_decimal_price(0.5) == "0.50"
    
    def test_format_decimal_price_edge_cases(self):
        """Test formatting with edge cases."""
        assert CurrencyFormatter.format_decimal_price("") == "0.00"
        assert CurrencyFormatter.format_decimal_price(None) == "0.00"
        assert CurrencyFormatter.format_decimal_price("0") == "0.00"
        assert CurrencyFormatter.format_decimal_price("invalid") == "0.00"
    
    def test_format_decimal_price_european_format(self):
        """Test formatting with European decimal format (comma separator)."""
        assert CurrencyFormatter.format_decimal_price("19,95") == "19.95"
        assert CurrencyFormatter.format_decimal_price("€19,95") == "19.95"
        assert CurrencyFormatter.format_decimal_price("1.234,56") == "1234.56"
    
    def test_extract_numeric_value_basic(self):
        """Test basic numeric value extraction."""
        assert CurrencyFormatter.extract_numeric_value("$19.95") == 19.95
        assert CurrencyFormatter.extract_numeric_value("£15.99") == 15.99
        assert CurrencyFormatter.extract_numeric_value("€18.50") == 18.50
        assert CurrencyFormatter.extract_numeric_value("19.95") == 19.95
    
    def test_extract_numeric_value_complex_formats(self):
        """Test numeric extraction from complex formats."""
        assert CurrencyFormatter.extract_numeric_value("USD 19.95") == 19.95
        assert CurrencyFormatter.extract_numeric_value("19.95 USD") == 19.95
        assert CurrencyFormatter.extract_numeric_value("C$ 26.95") == 26.95
        assert CurrencyFormatter.extract_numeric_value("A$ 29.95") == 29.95
    
    def test_extract_numeric_value_thousands_separators(self):
        """Test extraction with thousands separators."""
        assert CurrencyFormatter.extract_numeric_value("$1,234.56") == 1234.56
        assert CurrencyFormatter.extract_numeric_value("€1.234,56") == 1234.56
        assert CurrencyFormatter.extract_numeric_value("£10,000.00") == 10000.00
    
    def test_extract_numeric_value_edge_cases(self):
        """Test extraction edge cases."""
        assert CurrencyFormatter.extract_numeric_value("") == 0.0
        assert CurrencyFormatter.extract_numeric_value(None) == 0.0
        assert CurrencyFormatter.extract_numeric_value("$") == 0.0
        assert CurrencyFormatter.extract_numeric_value("invalid") == 0.0
        assert CurrencyFormatter.extract_numeric_value("$0") == 0.0
    
    def test_validate_decimal_format_valid(self):
        """Test validation of valid decimal formats."""
        assert CurrencyFormatter.validate_decimal_format("19.95") == True
        assert CurrencyFormatter.validate_decimal_format("0.00") == True
        assert CurrencyFormatter.validate_decimal_format("1234.56") == True
        assert CurrencyFormatter.validate_decimal_format("0.01") == True
    
    def test_validate_decimal_format_invalid(self):
        """Test validation of invalid decimal formats."""
        assert CurrencyFormatter.validate_decimal_format("$19.95") == False
        assert CurrencyFormatter.validate_decimal_format("19.950") == False
        assert CurrencyFormatter.validate_decimal_format("19") == False
        assert CurrencyFormatter.validate_decimal_format("19.9") == False
        assert CurrencyFormatter.validate_decimal_format("") == False
        assert CurrencyFormatter.validate_decimal_format(None) == False
    
    def test_format_wholesale_discount_basic(self):
        """Test basic wholesale discount formatting."""
        assert CurrencyFormatter.format_wholesale_discount("40%") == "40"
        assert CurrencyFormatter.format_wholesale_discount("40") == "40"
        assert CurrencyFormatter.format_wholesale_discount(40) == "40"
        assert CurrencyFormatter.format_wholesale_discount(40.0) == "40"
    
    def test_format_wholesale_discount_rounding(self):
        """Test wholesale discount rounding."""
        assert CurrencyFormatter.format_wholesale_discount("40.5%") == "41"
        assert CurrencyFormatter.format_wholesale_discount("40.4%") == "40"
        assert CurrencyFormatter.format_wholesale_discount(40.7) == "41"
    
    def test_format_wholesale_discount_edge_cases(self):
        """Test wholesale discount edge cases."""
        assert CurrencyFormatter.format_wholesale_discount("") == "40"
        assert CurrencyFormatter.format_wholesale_discount(None) == "40"
        assert CurrencyFormatter.format_wholesale_discount("invalid") == "40"
        assert CurrencyFormatter.format_wholesale_discount("0%") == "0"
    
    def test_clean_price_fields(self):
        """Test cleaning all price fields in a dictionary."""
        data = {
            'US Suggested List Price': '$19.95',
            'UK Suggested List Price': '£15.99',
            'EU Suggested List Price': '€18.50',
            'US Wholesale Discount': '40%',
            'UK Wholesale Discount': '35%',
            'other_field': 'unchanged'
        }
        
        cleaned = CurrencyFormatter.clean_price_fields(data)
        
        assert cleaned['US Suggested List Price'] == "19.95"
        assert cleaned['UK Suggested List Price'] == "15.99"
        assert cleaned['EU Suggested List Price'] == "18.50"
        assert cleaned['US Wholesale Discount'] == "40"
        assert cleaned['UK Wholesale Discount'] == "35"
        assert cleaned['other_field'] == 'unchanged'
    
    def test_clean_price_fields_missing_fields(self):
        """Test cleaning when some price fields are missing."""
        data = {
            'US Suggested List Price': '$19.95',
            'other_field': 'unchanged'
        }
        
        cleaned = CurrencyFormatter.clean_price_fields(data)
        
        assert cleaned['US Suggested List Price'] == "19.95"
        assert cleaned['other_field'] == 'unchanged'
        assert len(cleaned) == 2  # No new fields added
    
    def test_clean_price_fields_empty_values(self):
        """Test cleaning with empty price values."""
        data = {
            'US Suggested List Price': '',
            'UK Suggested List Price': None,
            'US Wholesale Discount': ''
        }
        
        cleaned = CurrencyFormatter.clean_price_fields(data)
        
        assert cleaned['US Suggested List Price'] == "0.00"
        assert cleaned['UK Suggested List Price'] == "0.00"
        assert cleaned['US Wholesale Discount'] == "40"  # Default discount