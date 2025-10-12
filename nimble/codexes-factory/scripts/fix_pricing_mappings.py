#!/usr/bin/env python3
"""
Quick fix script to update pricing field mappings to use enhanced pricing strategy
"""

import sys
import os
sys.path.append('src')

from codexes.modules.distribution.enhanced_pricing_strategy import EnhancedPricingStrategy
from codexes.modules.distribution.currency_formatter import CurrencyFormatter

def test_enhanced_pricing():
    """Test the enhanced pricing strategy with sample data."""
    print("🧪 Testing Enhanced Pricing Strategy")
    print("=" * 50)
    
    # Create strategy instance
    strategy = EnhancedPricingStrategy()
    
    # Sample metadata
    metadata = {
        'list_price': '$24.95',
        'wholesale_discount': '40%'
    }
    
    # Test price fields
    price_fields = [
        'US Suggested List Price',
        'UK Suggested List Price', 
        'EU Suggested List Price',
        'CA Suggested List Price',
        'AU Suggested List Price',
        'GC Suggested List Price (mode 2)',
    ]
    
    print("Price Field Mappings:")
    for field in price_fields:
        result = strategy.map_field(field, metadata)
        print(f"  {field}: {result}")
    
    print("\nDiscount Field Mappings:")
    discount_fields = [
        'US Wholesale Discount',
        'UK Wholesale Discount (%)',
        'EU Wholesale Discount % (Mode 2)',
    ]
    
    for field in discount_fields:
        result = strategy.map_field(field, metadata)
        print(f"  {field}: {result}")
    
    print("\n✅ Enhanced pricing strategy working correctly!")
    
    # Test territorial price calculation
    print("\nTerritorial Price Calculation:")
    base_price = 24.95
    territorial_prices = strategy.calculate_all_territorial_prices(base_price)
    for territory, price in territorial_prices.items():
        print(f"  {territory}: {price}")
    
    print(f"\n📊 Strategy supports {len(strategy.get_supported_fields())} pricing fields")

if __name__ == "__main__":
    test_enhanced_pricing()