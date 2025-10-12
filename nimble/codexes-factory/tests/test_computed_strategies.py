#!/usr/bin/env python3

"""
Comprehensive test script for all computed field strategies.

This script tests all the computed field strategies including territorial pricing,
physical specifications, date computation, and file path strategies.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Import the necessary modules
from codexes.modules.metadata.metadata_models import CodexMetadata
from codexes.modules.distribution.computed_field_strategies import (
    TerritorialPricingStrategy, PhysicalSpecsStrategy,
    DateComputationStrategy, FilePathStrategy
)
from codexes.modules.distribution.field_mapping import MappingContext

def test_all_computed_strategies():
    """Test all computed field strategies."""
    logger.info("Starting comprehensive computed strategies test")
    
    # Create a comprehensive test book
    test_book = CodexMetadata(
        title="Comprehensive Test Book",
        author="Test Author",
        isbn13="9781234567890",
        isbn10="1234567890",
        page_count=250,
        trim_size="6 x 9",
        binding="paperback",
        list_price_usd=19.99,
        publication_date="2024-03-15",
        street_date="2024-03-22"
    )
    
    # Create mapping context
    context = MappingContext()
    
    # Test results
    results = {
        "book_info": {
            "title": test_book.title,
            "isbn13": test_book.isbn13,
            "page_count": test_book.page_count,
            "trim_size": test_book.trim_size,
            "binding": test_book.binding,
            "list_price_usd": test_book.list_price_usd,
            "publication_date": test_book.publication_date
        },
        "territorial_pricing": {},
        "physical_specifications": {},
        "date_computations": {},
        "file_paths": {}
    }
    
    # Test territorial pricing strategies
    logger.info("Testing territorial pricing strategies")
    territories = [
        {"code": "CA", "exchange_rate": 1.35, "price_format": "${price:.2f}", "rounding_rule": "nearest_99"},
        {"code": "UK", "exchange_rate": 0.78, "price_format": "£{price:.2f}", "rounding_rule": "nearest_99"},
        {"code": "EU", "exchange_rate": 0.91, "price_format": "€{price:.2f}", "rounding_rule": "nearest_99"},
        {"code": "AU", "exchange_rate": 1.48, "price_format": "${price:.2f}", "rounding_rule": "nearest_99"},
        {"code": "JP", "exchange_rate": 150.0, "price_format": "¥{price}", "rounding_rule": "nearest"}
    ]
    
    for territory in territories:
        strategy = TerritorialPricingStrategy(
            territory_code=territory["code"],
            exchange_rate=territory["exchange_rate"],
            price_format=territory["price_format"],
            rounding_rule=territory["rounding_rule"]
        )
        
        price = strategy.map_field(test_book, context)
        logger.info(f"{territory['code']} price: {price}")
        results["territorial_pricing"][territory["code"]] = price
    
    # Test physical specifications strategies
    logger.info("Testing physical specifications strategies")
    physical_specs = [
        {"type": "weight", "paper_type": "standard"},
        {"type": "weight", "paper_type": "premium"},
        {"type": "weight", "paper_type": "lightweight"},
        {"type": "spine_width", "paper_type": "standard"},
        {"type": "spine_width", "paper_type": "premium"},
        {"type": "thickness", "paper_type": "standard"}
    ]
    
    for spec in physical_specs:
        strategy = PhysicalSpecsStrategy(
            spec_type=spec["type"],
            paper_type=spec["paper_type"]
        )
        
        spec_value = strategy.map_field(test_book, context)
        spec_name = f"{spec['type']}_{spec['paper_type']}"
        logger.info(f"{spec_name}: {spec_value}")
        results["physical_specifications"][spec_name] = spec_value
    
    # Test date computation strategies
    logger.info("Testing date computation strategies")
    date_computations = [
        {"type": "pub_date", "offset": 0},
        {"type": "street_date", "offset": 7},
        {"type": "street_date", "offset": 14},
        {"type": "street_date", "offset": -7}
    ]
    
    for date_comp in date_computations:
        strategy = DateComputationStrategy(
            date_type=date_comp["type"],
            offset_days=date_comp["offset"]
        )
        
        computed_date = strategy.map_field(test_book, context)
        comp_name = f"{date_comp['type']}_offset_{date_comp['offset']}"
        logger.info(f"{comp_name}: {computed_date}")
        results["date_computations"][comp_name] = computed_date
    
    # Test file path strategies
    logger.info("Testing file path strategies")
    file_types = [
        {"type": "cover", "base_path": "covers"},
        {"type": "interior", "base_path": "interiors"},
        {"type": "jacket", "base_path": "jackets"},
        {"type": "epub", "base_path": "ebooks"},
        {"type": "cover", "base_path": ""}  # No base path
    ]
    
    for file_type in file_types:
        strategy = FilePathStrategy(
            file_type=file_type["type"],
            base_path=file_type["base_path"]
        )
        
        file_path = strategy.map_field(test_book, context)
        path_name = f"{file_type['type']}_{file_type['base_path'] or 'no_base'}"
        logger.info(f"{path_name}: {file_path}")
        results["file_paths"][path_name] = file_path
    
    # Test error handling with incomplete metadata
    logger.info("Testing error handling with incomplete metadata")
    incomplete_book = CodexMetadata(
        title="Incomplete Book",
        author="Test Author"
        # Missing ISBN, page count, price, etc.
    )
    
    error_results = {}
    
    # Test territorial pricing with missing price
    strategy = TerritorialPricingStrategy("CA", exchange_rate=1.35)
    result = strategy.map_field(incomplete_book, context)
    logger.info(f"Territorial pricing with missing price: '{result}'")
    error_results["territorial_pricing_no_price"] = result
    
    # Test physical specs with missing page count
    strategy = PhysicalSpecsStrategy("weight", "standard")
    result = strategy.map_field(incomplete_book, context)
    logger.info(f"Physical specs with missing page count: '{result}'")
    error_results["physical_specs_no_pages"] = result
    
    # Test file path with missing ISBN
    strategy = FilePathStrategy("cover", "covers")
    result = strategy.map_field(incomplete_book, context)
    logger.info(f"File path with missing ISBN: '{result}'")
    error_results["file_path_no_isbn"] = result
    
    results["error_handling"] = error_results
    
    # Test with different price formats
    logger.info("Testing different price formats")
    price_format_books = [
        CodexMetadata(title="Price with $", list_price_usd="$24.99"),
        CodexMetadata(title="Price with commas", list_price_usd="$1,299.99"),
        CodexMetadata(title="Price as float", list_price_usd=29.95),
        CodexMetadata(title="Price in different field", us_suggested_list_price="$34.99")
    ]
    
    price_format_results = {}
    for book in price_format_books:
        strategy = TerritorialPricingStrategy("UK", exchange_rate=0.78, price_format="£{price:.2f}")
        result = strategy.map_field(book, context)
        logger.info(f"{book.title}: {result}")
        price_format_results[book.title] = result
    
    results["price_format_tests"] = price_format_results
    
    # Save results to a JSON file for inspection
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"computed_strategies_test_{timestamp}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Test results saved to {output_path}")
    
    return results

if __name__ == "__main__":
    test_all_computed_strategies()