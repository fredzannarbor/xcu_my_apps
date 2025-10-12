"""
Validation utilities for LSI field validation.

This module provides validation functions for LSI fields to ensure they meet
the requirements of the Lightning Source ACS system.
"""

import os
import logging
from typing import List, Set, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Cache for valid values
_VALID_RENDITION_BOOKTYPES: Optional[Set[str]] = None
_VALID_CONTRIBUTOR_CODES: Optional[Dict[str, str]] = None

def load_valid_rendition_booktypes() -> Set[str]:
    """
    Load valid rendition booktypes from the validation file.
    
    Returns:
        Set of valid rendition booktype strings
    """
    global _VALID_RENDITION_BOOKTYPES
    
    # Return cached values if already loaded
    if _VALID_RENDITION_BOOKTYPES is not None:
        return _VALID_RENDITION_BOOKTYPES
    
    # Path to the validation file
    file_path = os.path.join(
        os.path.dirname(__file__),
        "lsi_valid_rendition_booktypes.txt"
    )
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read all lines and strip whitespace
            valid_types = {line.strip() for line in f if line.strip()}
        
        logger.info(f"Loaded {len(valid_types)} valid rendition booktypes")
        _VALID_RENDITION_BOOKTYPES = valid_types
        return valid_types
    except Exception as e:
        logger.error(f"Error loading valid rendition booktypes: {e}")
        # Return an empty set as fallback
        return set()

def is_valid_rendition_booktype(booktype: str) -> bool:
    """
    Check if a rendition booktype is valid.
    
    Args:
        booktype: The rendition booktype to validate
        
    Returns:
        True if valid, False otherwise
    """
    valid_types = load_valid_rendition_booktypes()
    
    # Direct match
    if booktype in valid_types:
        return True
    
    # Try with "POD: " prefix if not present
    if not booktype.startswith("POD: ") and f"POD: {booktype}" in valid_types:
        logger.info(f"Booktype '{booktype}' is valid with 'POD: ' prefix")
        return True
    
    # Try without "POD: " prefix if present
    if booktype.startswith("POD: ") and booktype[5:] in valid_types:
        logger.info(f"Booktype '{booktype}' is valid without 'POD: ' prefix")
        return True
    
    # Not found
    logger.warning(f"Invalid rendition booktype: '{booktype}'")
    return False

def get_closest_valid_rendition_booktype(booktype: str) -> str:
    """
    Get the closest valid rendition booktype for an invalid one.
    
    Args:
        booktype: The invalid rendition booktype
        
    Returns:
        A valid rendition booktype that is closest to the input
    """
    valid_types = load_valid_rendition_booktypes()
    
    # If already valid, return as is
    if booktype in valid_types:
        return booktype
    
    # Try with "POD: " prefix if not present
    if not booktype.startswith("POD: ") and f"POD: {booktype}" in valid_types:
        return f"POD: {booktype}"
    
    # Try without "POD: " prefix if present
    if booktype.startswith("POD: ") and booktype[5:] in valid_types:
        return booktype[5:]
    
    # Common default values
    common_defaults = [
        "POD: 6 x 9 in or 229 x 152 mm Perfect Bound WHITE",
        "POD: 6 x 9 in or 229 x 152 mm Perfect Bound on White w/Matte Lam",
        "Perfect Bound"
    ]
    
    for default in common_defaults:
        if default in valid_types:
            logger.info(f"Using default rendition booktype: '{default}' for invalid value: '{booktype}'")
            return default
    
    # If all else fails, return the first valid type
    if valid_types:
        default = next(iter(valid_types))
        logger.info(f"Using first available rendition booktype: '{default}' for invalid value: '{booktype}'")
        return default
    
    # Absolute fallback
    logger.error(f"No valid rendition booktypes available, using hardcoded default for: '{booktype}'")
    return "POD: 6 x 9 in or 229 x 152 mm Perfect Bound WHITE"

# Additional validation functions can be added here