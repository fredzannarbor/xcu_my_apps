"""
ISBN Assignment Module

This module provides functionality for assigning ISBNs to books based on distribution requirements.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

from src.codexes.modules.metadata.metadata_models import CodexMetadata
from src.codexes.modules.distribution.isbn_database import ISBNDatabase, ISBNStatus

logger = logging.getLogger(__name__)

class ISBNAssignmentError(Exception):
    """Exception raised for errors during ISBN assignment."""
    pass

def determine_isbn_requirement(metadata: CodexMetadata, distribution_channels: Optional[list] = None) -> bool:
    """
    Determine if a book requires an ISBN based on its distribution channels.
    
    Args:
        metadata: Book metadata
        distribution_channels: List of distribution channels (e.g., ["ingram", "kdp", "storefront"])
        
    Returns:
        True if ISBN is required, False otherwise
    """
    # If distribution channels are explicitly provided, use them
    if distribution_channels:
        # Ingram (LSI) always requires an ISBN
        if "ingram" in distribution_channels or "lsi" in distribution_channels:
            return True
        
        # KDP makes ISBN optional
        if "kdp" in distribution_channels and "storefront" not in distribution_channels:
            # For KDP-only, ISBN is optional but recommended
            return True
        
        # Storefront-only doesn't require ISBN
        if "storefront" in distribution_channels and "kdp" not in distribution_channels and "ingram" not in distribution_channels:
            return False
    
    # If no distribution channels are provided, check if LSI fields are present
    # which would indicate Ingram distribution
    if hasattr(metadata, 'lightning_source_account') and metadata.lightning_source_account:
        return True
    
    # Default to requiring ISBN for safety
    return True

def assign_isbn_to_book(
    metadata: CodexMetadata, 
    isbn_db: ISBNDatabase,
    publisher_id: str,
    force_assign: bool = False,
    distribution_channels: Optional[list] = None
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Assign an ISBN to a book if needed.
    
    Args:
        metadata: Book metadata
        isbn_db: ISBN database
        publisher_id: Publisher ID
        force_assign: Force ISBN assignment even if not required
        distribution_channels: List of distribution channels
        
    Returns:
        Tuple of (success, isbn, details)
    """
    result = {
        "success": False,
        "isbn_required": False,
        "isbn_already_assigned": False,
        "isbn_assigned": False,
        "message": "",
        "isbn": None
    }
    
    # Check if ISBN is already assigned
    if hasattr(metadata, 'isbn13') and metadata.isbn13 and metadata.isbn13 != "Unknown":
        result["isbn_already_assigned"] = True
        result["isbn"] = metadata.isbn13
        result["message"] = f"ISBN already assigned: {metadata.isbn13}"
        result["success"] = True
        logger.info(f"ISBN already assigned to book: {metadata.isbn13}")
        return result["success"], result["isbn"], result
    
    # Determine if ISBN is required
    isbn_required = determine_isbn_requirement(metadata, distribution_channels)
    result["isbn_required"] = isbn_required
    
    # If ISBN is not required and not forced, return
    if not isbn_required and not force_assign:
        result["message"] = "ISBN not required for this distribution channel and force_assign is False"
        logger.info("ISBN not required for this book")
        return result["success"], result["isbn"], result
    
    # Generate a unique book ID if not available
    book_id = getattr(metadata, 'uuid', None)
    if not book_id:
        book_id = str(uuid.uuid4())
        if hasattr(metadata, 'uuid'):
            setattr(metadata, 'uuid', book_id)
    
    # Get next available ISBN
    isbn = isbn_db.get_next_available_isbn(publisher_id)
    if not isbn:
        result["message"] = f"No available ISBNs found for publisher {publisher_id}"
        logger.error(result["message"])
        return result["success"], result["isbn"], result
    
    # Assign ISBN to book
    assignment_success = isbn_db.assign_isbn(isbn, book_id)
    if not assignment_success:
        result["message"] = f"Failed to assign ISBN {isbn} to book {book_id}"
        logger.error(result["message"])
        return result["success"], result["isbn"], result
    
    # Update metadata with ISBN
    if hasattr(metadata, 'isbn13'):
        setattr(metadata, 'isbn13', isbn)
    
    result["success"] = True
    result["isbn_assigned"] = True
    result["isbn"] = isbn
    result["message"] = f"Successfully assigned ISBN {isbn} to book {book_id}"
    logger.info(result["message"])
    
    return result["success"], result["isbn"], result

def mark_isbn_as_published(isbn_db: ISBNDatabase, isbn: str) -> bool:
    """
    Mark an ISBN as published.
    
    Args:
        isbn_db: ISBN database
        isbn: ISBN to mark as published
        
    Returns:
        True if successful, False otherwise
    """
    if not isbn:
        logger.error("Cannot mark empty ISBN as published")
        return False
    
    success = isbn_db.mark_as_published(isbn)
    if success:
        logger.info(f"Marked ISBN {isbn} as published")
    else:
        logger.error(f"Failed to mark ISBN {isbn} as published")
    
    return success

def release_isbn(isbn_db: ISBNDatabase, isbn: str) -> bool:
    """
    Release an ISBN back to the available pool.
    
    Args:
        isbn_db: ISBN database
        isbn: ISBN to release
        
    Returns:
        True if successful, False otherwise
    """
    if not isbn:
        logger.error("Cannot release empty ISBN")
        return False
    
    success = isbn_db.release_isbn(isbn)
    if success:
        logger.info(f"Released ISBN {isbn} back to available pool")
    else:
        logger.error(f"Failed to release ISBN {isbn}")
    
    return success