#!/usr/bin/env python3

"""
Test script for date computation strategies.

This script tests the date computation strategies to ensure they correctly calculate
dates based on available date information with various formats and offsets.
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
    DateComputationStrategy, PublicationDateStrategy, 
    StreetDateStrategy, CopyrightDateStrategy
)
from codexes.modules.distribution.field_mapping import MappingContext

def test_date_computation():
    """Test date computation strategies."""
    logger.info("Starting date computation test")
    
    # Create test metadata with different date formats
    test_books = [
        # Book with standard date format
        CodexMetadata(
            title="Standard Date Format",
            author="Test Author",
            isbn13="9781234567890",
            publication_date="2024-03-15",
            street_date="2024-03-22"
        ),
        # Book with US date format
        CodexMetadata(
            title="US Date Format",
            author="Test Author",
            isbn13="9789876543210",
            publication_date="03/15/2024",
            street_date="03/22/2024"
        ),
        # Book with European date format
        CodexMetadata(
            title="European Date Format",
            author="Test Author",
            isbn13="9785432109876",
            publication_date="15/03/2024",
            street_date="22/03/2024"
        ),
        # Book with long date format
        CodexMetadata(
            title="Long Date Format",
            author="Test Author",
            isbn13="9781357924680",
            publication_date="March 15, 2024",
            street_date="March 22, 2024"
        ),
        # Book with abbreviated date format
        CodexMetadata(
            title="Abbreviated Date Format",
            author="Test Author",
            isbn13="9781122334455",
            publication_date="Mar 15, 2024",
            street_date="Mar 22, 2024"
        ),
        # Book with ISO datetime format
        CodexMetadata(
            title="ISO DateTime Format",
            author="Test Author",
            isbn13="9786677889900",
            publication_date="2024-03-15T10:30:00Z",
            street_date="2024-03-22T10:30:00Z"
        ),
        # Book with only publication date
        CodexMetadata(
            title="Only Publication Date",
            author="Test Author",
            isbn13="9781111222233",
            publication_date="2024-04-01"
        ),
        # Book with only street date
        CodexMetadata(
            title="Only Street Date",
            author="Test Author",
            isbn13="9782222333344",
            street_date="2024-04-08"
        ),
        # Book with copyright year only
        CodexMetadata(
            title="Copyright Year Only",
            author="Test Author",
            isbn13="9783333444455",
            copyright_year="2024"
        ),
        # Book with copyright date
        CodexMetadata(
            title="Copyright Date",
            author="Test Author",
            isbn13="9784444555566",
            copyright_date="2024-01-01"
        ),
        # Book with alternative field names
        CodexMetadata(
            title="Alternative Field Names",
            author="Test Author",
            isbn13="9785555666677",
            pub_date="2024-05-01",
            on_sale_date="2024-05-08",
            release_date="2024-05-15"
        )
    ]
    
    # Create mapping context
    context = MappingContext()
    
    # Test results
    results = {}
    
    # Define date strategies to test
    date_strategies = [
        {"name": "Publication Date", "strategy": PublicationDateStrategy()},
        {"name": "Street Date (7 days)", "strategy": StreetDateStrategy(offset_days=7)},
        {"name": "Street Date (14 days)", "strategy": StreetDateStrategy(offset_days=14)},
        {"name": "Street Date (0 days)", "strategy": StreetDateStrategy(offset_days=0)},
        {"name": "Copyright Date", "strategy": CopyrightDateStrategy()},
        {"name": "Generic Date", "strategy": DateComputationStrategy("generic_date")},
        {"name": "Future Date (+30)", "strategy": DateComputationStrategy("future_date", offset_days=30)},
        {"name": "Past Date (-30)", "strategy": DateComputationStrategy("past_date", offset_days=-30)}
    ]
    
    # Test each book with each strategy
    for i, book in enumerate(test_books):
        book_results = {}
        logger.info(f"Testing book {i+1}: {book.title}")
        
        # Log available dates
        available_dates = []
        for attr in ["publication_date", "pub_date", "street_date", "on_sale_date", 
                    "release_date", "copyright_date", "copyright_year"]:
            value = getattr(book, attr, None)
            if value:
                available_dates.append(f"{attr}: {value}")
        
        logger.info(f"Available dates: {', '.join(available_dates) if available_dates else 'None'}")
        
        for strategy_info in date_strategies:
            strategy_name = strategy_info["name"]
            strategy = strategy_info["strategy"]
            
            # Calculate the date
            computed_date = strategy.map_field(book, context)
            
            # Log the result
            logger.info(f"{strategy_name}: {computed_date}")
            
            # Store the result
            book_results[strategy_name] = computed_date
        
        # Store the book results
        results[book.title] = book_results
    
    # Test edge cases
    logger.info("\\nTesting edge cases")
    edge_case_results = {}
    
    # Book with no dates
    no_dates_book = CodexMetadata(title="No Dates", author="Test Author", isbn13="9781111111111")
    
    for strategy_info in date_strategies:
        strategy_name = strategy_info["name"]
        strategy = strategy_info["strategy"]
        result = strategy.map_field(no_dates_book, context)
        logger.info(f"No dates - {strategy_name}: '{result}'")
        edge_case_results[f"no_dates_{strategy_name}"] = result
    
    # Test with fallback to current date
    logger.info("\\nTesting fallback to current date")
    fallback_strategies = [
        {"name": "Publication Date (fallback)", "strategy": PublicationDateStrategy(fallback_to_current=True)},
        {"name": "Street Date (fallback)", "strategy": StreetDateStrategy(fallback_to_current=True)},
        {"name": "Copyright Date (fallback)", "strategy": CopyrightDateStrategy(fallback_to_current=True)}
    ]
    
    for strategy_info in fallback_strategies:
        strategy_name = strategy_info["name"]
        strategy = strategy_info["strategy"]
        result = strategy.map_field(no_dates_book, context)
        logger.info(f"Fallback - {strategy_name}: {result}")
        edge_case_results[f"fallback_{strategy_name}"] = result
    
    # Test invalid date formats
    logger.info("\\nTesting invalid date formats")
    invalid_date_book = CodexMetadata(
        title="Invalid Dates",
        author="Test Author",
        isbn13="9782222222222",
        publication_date="invalid-date",
        street_date="not-a-date",
        copyright_year="not-a-year"
    )
    
    for strategy_info in date_strategies[:3]:  # Test first 3 strategies
        strategy_name = strategy_info["name"]
        strategy = strategy_info["strategy"]
        result = strategy.map_field(invalid_date_book, context)
        logger.info(f"Invalid dates - {strategy_name}: '{result}'")
        edge_case_results[f"invalid_dates_{strategy_name}"] = result
    
    # Test date parsing with various formats
    logger.info("\\nTesting various date formats")
    date_format_tests = [
        {"format": "YYYY-MM-DD", "date": "2024-06-15"},
        {"format": "YYYY/MM/DD", "date": "2024/06/15"},
        {"format": "MM/DD/YYYY", "date": "06/15/2024"},
        {"format": "DD/MM/YYYY", "date": "15/06/2024"},
        {"format": "Month DD, YYYY", "date": "June 15, 2024"},
        {"format": "Mon DD, YYYY", "date": "Jun 15, 2024"},
        {"format": "DD Month YYYY", "date": "15 June 2024"},
        {"format": "DD Mon YYYY", "date": "15 Jun 2024"},
        {"format": "ISO DateTime", "date": "2024-06-15T14:30:00"},
        {"format": "ISO DateTime Z", "date": "2024-06-15T14:30:00Z"}
    ]
    
    format_results = {}
    for test in date_format_tests:
        test_book = CodexMetadata(
            title=f"Date Format Test - {test['format']}",
            publication_date=test["date"]
        )
        
        strategy = PublicationDateStrategy()
        result = strategy.map_field(test_book, context)
        logger.info(f"Format {test['format']} ('{test['date']}'): {result}")
        format_results[test["format"]] = {
            "input": test["date"],
            "output": result
        }
    
    # Store edge case and format results
    results["Edge Cases"] = edge_case_results
    results["Date Format Tests"] = format_results
    
    # Save results to a JSON file for inspection
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"date_computation_test_{timestamp}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Test results saved to {output_path}")
    
    return results

if __name__ == "__main__":
    test_date_computation()