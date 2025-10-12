#!/usr/bin/env python3

"""
Test script for physical specifications calculation.

This script tests the PhysicalSpecsStrategy to ensure it correctly calculates
physical specifications like weight, spine width, and thickness based on
page count, trim size, and paper type.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Import the necessary modules
from codexes.modules.metadata.metadata_models import CodexMetadata
from codexes.modules.distribution.computed_field_strategies import PhysicalSpecsStrategy
from codexes.modules.distribution.field_mapping import MappingContext

def test_physical_specifications():
    """Test physical specifications calculation."""
    logger.info("Starting physical specifications test")
    
    # Create test metadata with different book configurations
    test_books = [
        # Small paperback book
        CodexMetadata(
            title="Small Paperback",
            author="Test Author",
            isbn13="9781234567890",
            page_count=150,
            trim_size="5.5 x 8.5",
            binding="paperback"
        ),
        # Standard paperback book
        CodexMetadata(
            title="Standard Paperback",
            author="Test Author",
            isbn13="9789876543210",
            page_count=250,
            trim_size="6 x 9",
            binding="paperback"
        ),
        # Large paperback book
        CodexMetadata(
            title="Large Paperback",
            author="Test Author",
            isbn13="9785432109876",
            page_count=400,
            trim_size="7 x 10",
            binding="paperback"
        ),
        # Hardcover book
        CodexMetadata(
            title="Hardcover Book",
            author="Test Author",
            isbn13="9781357924680",
            page_count=300,
            trim_size="6 x 9",
            binding="hardcover"
        ),
        # Book with string page count
        CodexMetadata(
            title="String Page Count",
            author="Test Author",
            isbn13="9781122334455",
            pages="200 pages",
            trim_size="6 x 9",
            binding="paperback"
        ),
        # Book with minimal information
        CodexMetadata(
            title="Minimal Info Book",
            author="Test Author",
            isbn13="9786677889900",
            page_count=180
        )
    ]
    
    # Define specifications to test
    specifications = [
        {"type": "weight", "paper_type": "standard"},
        {"type": "weight", "paper_type": "premium"},
        {"type": "weight", "paper_type": "lightweight"},
        {"type": "spine_width", "paper_type": "standard"},
        {"type": "spine_width", "paper_type": "premium"},
        {"type": "thickness", "paper_type": "standard"}
    ]
    
    # Create mapping context
    context = MappingContext()
    
    # Test results
    results = {}
    
    # Test each book with each specification
    for i, book in enumerate(test_books):
        book_results = {}
        logger.info(f"Testing book {i+1}: {book.title}")
        
        # Log book details
        page_count = getattr(book, "page_count", None) or getattr(book, "pages", "N/A")
        trim_size = getattr(book, "trim_size", "N/A")
        binding = getattr(book, "binding", "N/A")
        logger.info(f"Page count: {page_count}, Trim size: {trim_size}, Binding: {binding}")
        
        for spec in specifications:
            # Create the strategy
            strategy = PhysicalSpecsStrategy(
                spec_type=spec["type"],
                paper_type=spec["paper_type"]
            )
            
            # Calculate the specification
            spec_value = strategy.map_field(book, context)
            
            # Log the result
            spec_name = f"{spec['type']} ({spec['paper_type']})"
            logger.info(f"{spec_name}: {spec_value}")
            
            # Store the result
            book_results[spec_name] = spec_value
        
        # Store the book results
        results[book.title] = book_results
    
    # Test edge cases
    logger.info("\\nTesting edge cases")
    edge_case_results = {}
    
    # Book with no page count
    no_pages_book = CodexMetadata(title="No Pages", author="Test Author", isbn13="9781111111111")
    strategy = PhysicalSpecsStrategy("weight", "standard")
    result = strategy.map_field(no_pages_book, context)
    logger.info(f"Book with no page count - Weight: {result}")
    edge_case_results["no_page_count"] = result
    
    # Book with very high page count
    thick_book = CodexMetadata(
        title="Very Thick Book",
        author="Test Author",
        isbn13="9782222222222",
        page_count=1000,
        trim_size="8.5 x 11",
        binding="hardcover"
    )
    strategy = PhysicalSpecsStrategy("weight", "standard")
    result = strategy.map_field(thick_book, context)
    logger.info(f"Very thick book - Weight: {result}")
    edge_case_results["thick_book_weight"] = result
    
    strategy = PhysicalSpecsStrategy("spine_width", "standard")
    result = strategy.map_field(thick_book, context)
    logger.info(f"Very thick book - Spine width: {result}")
    edge_case_results["thick_book_spine"] = result
    
    # Book with unusual trim size format
    unusual_trim_book = CodexMetadata(
        title="Unusual Trim",
        author="Test Author",
        isbn13="9783333333333",
        page_count=200,
        trim_size="5.25\" × 8.25\"",
        binding="paperback"
    )
    strategy = PhysicalSpecsStrategy("weight", "standard")
    result = strategy.map_field(unusual_trim_book, context)
    logger.info(f"Unusual trim size format - Weight: {result}")
    edge_case_results["unusual_trim"] = result
    
    # Store edge case results
    results["Edge Cases"] = edge_case_results
    
    # Save results to a JSON file for inspection
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"physical_specs_test_{timestamp}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Test results saved to {output_path}")
    
    return results

if __name__ == "__main__":
    test_physical_specifications()