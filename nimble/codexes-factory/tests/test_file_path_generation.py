#!/usr/bin/env python3

"""
Test script for file path generation strategies.

This script tests the file path generation strategies to ensure they correctly generate
file paths based on ISBN, title, and other metadata with various naming conventions.
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
from codexes.modules.distribution.computed_field_strategies import (
    FilePathStrategy, LSIFilePathStrategy, 
    DetailedFilePathStrategy, OrganizedFilePathStrategy
)
from codexes.modules.distribution.field_mapping import MappingContext

def test_file_path_generation():
    """Test file path generation strategies."""
    logger.info("Starting file path generation test")
    
    # Create test metadata with different configurations
    test_books = [
        # Standard book with all metadata
        CodexMetadata(
            title="The Complete Guide to Python Programming",
            author="John Smith",
            isbn13="9781234567890",
            isbn10="1234567890",
            imprint="Tech Books Press",
            publication_date="2024-03-15"
        ),
        # Book with special characters in title
        CodexMetadata(
            title="C++: The Ultimate Reference & Guide",
            author="Jane Doe",
            isbn13="9789876543210",
            imprint="Code Masters",
            publication_date="2024-04-01"
        ),
        # Book with long title
        CodexMetadata(
            title="Advanced Machine Learning Techniques for Data Science: A Comprehensive Approach to Modern AI",
            author="Dr. Robert Johnson",
            isbn13="9785432109876",
            imprint="AI Publications",
            publication_date="2024-05-15"
        ),
        # Book with minimal metadata
        CodexMetadata(
            title="Simple Book",
            isbn13="9781357924680"
        ),
        # Book with ISBN-10 only
        CodexMetadata(
            title="Legacy Book",
            author="Old Author",
            isbn10="1122334455",
            publication_date="2020-01-01"
        ),
        # Book with hyphens in ISBN
        CodexMetadata(
            title="Formatted ISBN Book",
            author="Format Author",
            isbn13="978-1-23-456789-0",
            imprint="Format Press",
            publication_date="2024-06-01"
        ),
        # Book with alternative field names
        CodexMetadata(
            title="Alternative Fields Book",
            contributor_one="Primary Author",
            sku="9786677889900",
            pub_date="2024-07-01"
        )
    ]
    
    # Create mapping context
    context = MappingContext()
    
    # Test results
    results = {}
    
    # Define file path strategies to test
    file_path_strategies = [
        {
            "name": "Basic Cover Path",
            "strategy": FilePathStrategy("cover")
        },
        {
            "name": "Basic Interior Path",
            "strategy": FilePathStrategy("interior", base_path="interiors")
        },
        {
            "name": "LSI Cover Path",
            "strategy": LSIFilePathStrategy("cover")
        },
        {
            "name": "LSI Interior Path",
            "strategy": LSIFilePathStrategy("interior")
        },
        {
            "name": "LSI Jacket Path",
            "strategy": LSIFilePathStrategy("jacket")
        },
        {
            "name": "Detailed Cover Path",
            "strategy": DetailedFilePathStrategy("cover", include_author=False)
        },
        {
            "name": "Detailed Cover Path with Author",
            "strategy": DetailedFilePathStrategy("cover", include_author=True)
        },
        {
            "name": "Organized EPUB Path",
            "strategy": OrganizedFilePathStrategy("epub", organize_by_date=True)
        },
        {
            "name": "Organized PDF Path by Imprint",
            "strategy": OrganizedFilePathStrategy("pdf", organize_by_imprint=True)
        },
        {
            "name": "Organized Cover Path (Date + Imprint)",
            "strategy": OrganizedFilePathStrategy("cover", organize_by_date=True, organize_by_imprint=True)
        }
    ]
    
    # Test each book with each strategy
    for i, book in enumerate(test_books):
        book_results = {}
        logger.info(f"Testing book {i+1}: {book.title}")
        
        # Log available metadata
        metadata_info = []
        for attr in ["isbn13", "isbn10", "sku", "author", "contributor_one", "imprint", "publication_date", "pub_date"]:
            value = getattr(book, attr, None)
            if value:
                metadata_info.append(f"{attr}: {value}")
        
        logger.info(f"Available metadata: {', '.join(metadata_info) if metadata_info else 'Minimal'}")
        
        for strategy_info in file_path_strategies:
            strategy_name = strategy_info["name"]
            strategy = strategy_info["strategy"]
            
            # Generate the file path
            file_path = strategy.map_field(book, context)
            
            # Log the result
            logger.info(f"{strategy_name}: {file_path}")
            
            # Store the result
            book_results[strategy_name] = file_path
        
        # Store the book results
        results[book.title] = book_results
    
    # Test edge cases
    logger.info("\\nTesting edge cases")
    edge_case_results = {}
    
    # Book with no ISBN
    no_isbn_book = CodexMetadata(title="No ISBN Book", author="Test Author")
    
    for strategy_info in file_path_strategies[:3]:  # Test first 3 strategies
        strategy_name = strategy_info["name"]
        strategy = strategy_info["strategy"]
        result = strategy.map_field(no_isbn_book, context)
        logger.info(f"No ISBN - {strategy_name}: '{result}'")
        edge_case_results[f"no_isbn_{strategy_name}"] = result
    
    # Book with invalid characters in title
    invalid_chars_book = CodexMetadata(
        title="Book/With\\Invalid:Characters<>|?*",
        author="Test Author",
        isbn13="9781111111111"
    )
    
    detailed_strategy = DetailedFilePathStrategy("cover", include_author=True)
    result = detailed_strategy.map_field(invalid_chars_book, context)
    logger.info(f"Invalid characters in title: {result}")
    edge_case_results["invalid_chars_title"] = result
    
    # Book with very long title
    long_title_book = CodexMetadata(
        title="This is an extremely long title that should be truncated because it exceeds the maximum length allowed for filenames in most file systems and should be handled gracefully",
        author="Long Name Author",
        isbn13="9782222222222"
    )
    
    detailed_strategy = DetailedFilePathStrategy("cover", include_author=True)
    result = detailed_strategy.map_field(long_title_book, context)
    logger.info(f"Very long title: {result}")
    edge_case_results["long_title"] = result
    
    # Test different file types
    logger.info("\\nTesting different file types")
    file_type_results = {}
    
    test_book = CodexMetadata(
        title="Multi-Format Book",
        author="Format Author",
        isbn13="9783333333333",
        imprint="Multi Press",
        publication_date="2024-08-01"
    )
    
    file_types = ["cover", "interior", "jacket", "epub", "mobi", "pdf", "audiobook", "thumbnail"]
    
    for file_type in file_types:
        strategy = FilePathStrategy(file_type, base_path=f"{file_type}s")
        result = strategy.map_field(test_book, context)
        logger.info(f"{file_type.upper()} file: {result}")
        file_type_results[file_type] = result
    
    # Test custom naming patterns
    logger.info("\\nTesting custom naming patterns")
    custom_pattern_results = {}
    
    custom_patterns = [
        "{isbn}_{file_type}",
        "{isbn}_{title}_{file_type}",
        "{title}_{isbn}",
        "{lsi_file_type}_{isbn}",
        "{isbn}_{title}_{author}_{file_type}"
    ]
    
    for pattern in custom_patterns:
        try:
            strategy = FilePathStrategy(
                "cover", 
                naming_pattern=pattern,
                include_title=True
            )
            result = strategy.map_field(test_book, context)
            logger.info(f"Pattern '{pattern}': {result}")
            custom_pattern_results[pattern] = result
        except Exception as e:
            logger.warning(f"Pattern '{pattern}' failed: {e}")
            custom_pattern_results[pattern] = f"ERROR: {str(e)}"
    
    # Store edge case and additional test results
    results["Edge Cases"] = edge_case_results
    results["File Type Tests"] = file_type_results
    results["Custom Pattern Tests"] = custom_pattern_results
    
    # Test organized file paths with different dates
    logger.info("\\nTesting organized paths with different dates")
    date_organization_results = {}
    
    date_test_books = [
        CodexMetadata(title="2020 Book", isbn13="9781111111111", publication_date="2020-01-01"),
        CodexMetadata(title="2021 Book", isbn13="9782222222222", publication_date="2021-06-15"),
        CodexMetadata(title="2024 Book", isbn13="9783333333333", publication_date="2024-12-31"),
        CodexMetadata(title="No Date Book", isbn13="9784444444444")
    ]
    
    organized_strategy = OrganizedFilePathStrategy("cover", organize_by_date=True)
    
    for book in date_test_books:
        result = organized_strategy.map_field(book, context)
        logger.info(f"{book.title}: {result}")
        date_organization_results[book.title] = result
    
    results["Date Organization Tests"] = date_organization_results
    
    # Save results to a JSON file for inspection
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"file_path_generation_test_{timestamp}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Test results saved to {output_path}")
    
    return results

if __name__ == "__main__":
    test_file_path_generation()