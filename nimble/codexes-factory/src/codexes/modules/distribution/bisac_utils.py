"""
BISAC Subject Field Utilities

This module provides utilities for handling BISAC subject fields,
including stripping codes from BISAC subject fields.
"""

import re
from typing import Optional


def strip_bisac_code(bisac_field: str) -> str:
    """
    Strip the code from a BISAC subject field, returning only the category name.
    
    Args:
        bisac_field: The BISAC field value, potentially containing a code
        
    Returns:
        The BISAC category name without the code
        
    Examples:
        >>> strip_bisac_code("FIC000000 FICTION / General")
        "FICTION / General"
        >>> strip_bisac_code("BUS000000 BUSINESS & ECONOMICS / General")
        "BUSINESS & ECONOMICS / General"
        >>> strip_bisac_code("FICTION / General")  # No code to strip
        "FICTION / General"
    """
    if not bisac_field:
        return ""
    
    # Pattern to match BISAC code at the beginning of the string
    # Format is typically 3 letters followed by 6 digits, then a space
    pattern = r'^[A-Z]{3}\d{6}\s+'
    
    # Replace the pattern with an empty string
    return re.sub(pattern, '', bisac_field)


def get_bisac_code(bisac_field: str) -> Optional[str]:
    """
    Extract just the code portion from a BISAC subject field.
    
    Args:
        bisac_field: The BISAC field value
        
    Returns:
        The BISAC code if found, None otherwise
        
    Examples:
        >>> get_bisac_code("FIC000000 FICTION / General")
        "FIC000000"
        >>> get_bisac_code("FICTION / General")  # No code to extract
        None
    """
    if not bisac_field:
        return None
    
    # Pattern to match BISAC code at the beginning of the string
    pattern = r'^([A-Z]{3}\d{6})'
    
    match = re.search(pattern, bisac_field)
    if match:
        return match.group(1)
    
    return None