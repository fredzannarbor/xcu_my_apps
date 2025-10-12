#!/usr/bin/env python3
"""
Test script for rendition booktype validation.
"""

import os
import sys
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from codexes.modules.distribution.validation_utils import (
    load_valid_rendition_booktypes,
    is_valid_rendition_booktype,
    get_closest_valid_rendition_booktype
)
from codexes.modules.distribution.field_mapping import (
    ValidatedRenditionBooktypeStrategy,
    MappingContext,
    CodexMetadata
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_load_valid_rendition_booktypes():
    """Test loading valid rendition booktypes."""
    valid_types = load_valid_rendition_booktypes()
    logger.info(f"Loaded {len(valid_types)} valid rendition booktypes")
    
    # Print first 5 examples
    for i, booktype in enumerate(list(valid_types)[:5]):
        logger.info(f"Example {i+1}: {booktype}")
    
    return valid_types

def test_validation():
    """Test validation of rendition booktypes."""
    # Valid examples
    valid_examples = [
        "POD: 6 x 9 in or 229 x 152 mm Perfect Bound WHITE",
        "POD: 6 x 9 in or 229 x 152 mm Perfect Bound on White w/Matte Lam",
        "Perfect Bound"
    ]
    
    # Invalid examples
    invalid_examples = [
        "Invalid Booktype",
        "6x9 Perfect Bound",
        "POD: Invalid Size"
    ]
    
    # Test valid examples
    logger.info("Testing valid examples:")
    for example in valid_examples:
        result = is_valid_rendition_booktype(example)
        logger.info(f"'{example}': {'✓' if result else '✗'}")
    
    # Test invalid examples
    logger.info("\nTesting invalid examples:")
    for example in invalid_examples:
        result = is_valid_rendition_booktype(example)
        logger.info(f"'{example}': {'✓' if result else '✗'}")
        if not result:
            closest = get_closest_valid_rendition_booktype(example)
            logger.info(f"  Closest valid: '{closest}'")

def test_mapping_strategy():
    """Test the ValidatedRenditionBooktypeStrategy."""
    # Create test metadata
    metadata = CodexMetadata()
    
    # Test cases
    test_cases = [
        {"value": "POD: 6 x 9 in or 229 x 152 mm Perfect Bound WHITE", "expected": "POD: 6 x 9 in or 229 x 152 mm Perfect Bound WHITE"},
        {"value": "Invalid Booktype", "expected": "POD: 6 x 9 in or 229 x 152 mm Perfect Bound WHITE"},
        {"value": None, "expected": "POD: 6 x 9 in or 229 x 152 mm Perfect Bound WHITE"}
    ]
    
    # Create mapping context
    context = MappingContext(
        field_name="Rendition /Booktype",
        lsi_headers=["Rendition /Booktype"],
        current_row_data={},
        config=None,
        metadata=metadata
    )
    
    # Create strategy
    strategy = ValidatedRenditionBooktypeStrategy("rendition_booktype", "POD: 6 x 9 in or 229 x 152 mm Perfect Bound WHITE")
    
    # Test each case
    logger.info("\nTesting mapping strategy:")
    for i, case in enumerate(test_cases):
        # Set metadata value
        metadata.rendition_booktype = case["value"]
        
        # Map field
        result = strategy.map_field(metadata, context)
        
        # Check result
        success = result == case["expected"]
        logger.info(f"Case {i+1}: '{case['value']}' -> '{result}': {'✓' if success else '✗'}")

def main():
    """Main function."""
    logger.info("Testing rendition booktype validation")
    
    # Test loading valid types
    valid_types = test_load_valid_rendition_booktypes()
    
    # Test validation
    test_validation()
    
    # Test mapping strategy
    test_mapping_strategy()
    
    logger.info("All tests completed")

if __name__ == "__main__":
    main()