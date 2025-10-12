"""
Text Length Validator Module

This module provides utilities for validating and truncating text fields
to ensure they meet specific length requirements.
"""

import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)


def validate_short_description_length(description: str, max_bytes: int = 350) -> Tuple[bool, int]:
    """
    Validate that a short description does not exceed the maximum byte length.
    
    Args:
        description: The short description text
        max_bytes: Maximum allowed byte length (default: 350)
        
    Returns:
        Tuple of (is_valid, current_byte_length)
    """
    if not description:
        return True, 0
    
    byte_length = len(description.encode('utf-8'))
    return byte_length <= max_bytes, byte_length


def truncate_at_word_boundary(text: str, max_bytes: int = 350) -> str:
    """
    Truncate text at a word boundary to ensure it doesn't exceed the maximum byte length.
    
    Args:
        text: The text to truncate
        max_bytes: Maximum allowed byte length (default: 350)
        
    Returns:
        Truncated text that doesn't exceed the maximum byte length
    """
    if not text:
        return ""
    
    # Check if truncation is needed
    byte_length = len(text.encode('utf-8'))
    if byte_length <= max_bytes:
        return text
    
    # Start with a conservative estimate (bytes per char can vary in UTF-8)
    avg_bytes_per_char = max(1, byte_length / len(text))
    safe_char_count = int(max_bytes / avg_bytes_per_char * 0.9)  # 90% to be safe
    
    # Truncate at character level first
    truncated = text[:safe_char_count]
    
    # Find the last word boundary
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    
    # Add ellipsis
    truncated += "..."
    
    # Check if we're still over the limit
    while len(truncated.encode('utf-8')) > max_bytes and len(truncated) > 5:
        # Find the last word boundary again
        last_space = truncated[:-3].rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space] + "..."
        else:
            # No more word boundaries, just truncate characters
            truncated = truncated[:-4] + "..."
    
    logger.info(f"Truncated text from {byte_length} to {len(truncated.encode('utf-8'))} bytes")
    return truncated


def validate_and_truncate_short_description(description: str, max_bytes: int = 350) -> str:
    """
    Validate and truncate a short description if it exceeds the maximum byte length.
    
    Args:
        description: The short description text
        max_bytes: Maximum allowed byte length (default: 350)
        
    Returns:
        Valid short description that doesn't exceed the maximum byte length
    """
    is_valid, byte_length = validate_short_description_length(description, max_bytes)
    
    if is_valid:
        return description
    
    logger.warning(f"Short description exceeds maximum length ({byte_length} > {max_bytes} bytes). Truncating...")
    return truncate_at_word_boundary(description, max_bytes)