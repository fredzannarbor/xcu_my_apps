"""
Series Assigner Module

This module provides functionality for assigning books to series and managing sequence numbers.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple

from ..metadata.metadata_models import CodexMetadata
from .series_registry import SeriesRegistry, SeriesNotFoundError, SeriesAccessDeniedError, SequenceNumberConflictError

logger = logging.getLogger(__name__)


class SeriesAssignmentError(Exception):
    """Exception raised for errors during series assignment."""
    pass


class SeriesAssigner:
    """
    Class for assigning books to series and managing sequence numbers.
    
    This class provides functionality for adding books to series, automatically
    assigning sequence numbers, and validating series assignments.
    """
    
    def __init__(self, series_registry: SeriesRegistry):
        """
        Initialize the series assigner.
        
        Args:
            series_registry: SeriesRegistry instance to use for series management
        """
        self.series_registry = series_registry
    
    def assign_book_to_series(self, metadata: CodexMetadata, series_name: str, 
                             sequence_number: Optional[int] = None,
                             publisher_id: Optional[str] = None) -> Tuple[str, int]:
        """
        Assign a book to a series.
        
        Args:
            metadata: CodexMetadata object for the book
            series_name: Name of the series
            sequence_number: Optional sequence number (auto-assigned if None)
            publisher_id: Optional ID of the publisher (defaults to metadata.publisher)
            
        Returns:
            Tuple of (series_id, sequence_number)
            
        Raises:
            SeriesAssignmentError: If there's an error during assignment
        """
        try:
            # Use publisher from metadata if not provided
            if publisher_id is None:
                publisher_id = metadata.publisher
            
            # Get book ID from metadata
            book_id = metadata.uuid
            
            # Find or create the series
            series_id = self._find_or_create_series(series_name, publisher_id)
            
            # Assign the book to the series
            assigned_sequence = self.series_registry.add_book_to_series(
                series_id, book_id, sequence_number, publisher_id
            )
            
            # Update metadata with series information
            metadata.series_name = series_name
            metadata.series_number = str(assigned_sequence)
            
            logger.info(f"Assigned book {book_id} to series '{series_name}' with sequence number {assigned_sequence}")
            return series_id, assigned_sequence
            
        except (SeriesNotFoundError, SeriesAccessDeniedError, SequenceNumberConflictError) as e:
            logger.error(f"Error assigning book to series: {e}")
            raise SeriesAssignmentError(f"Error assigning book to series: {e}")
    
    def _find_or_create_series(self, series_name: str, publisher_id: str) -> str:
        """
        Find an existing series or create a new one.
        
        Args:
            series_name: Name of the series
            publisher_id: ID of the publisher
            
        Returns:
            ID of the found or created series
        """
        # Look for existing series with the same name for this publisher
        matching_series = self.series_registry.get_series_by_name(series_name, publisher_id)
        
        if matching_series:
            # Use the first matching series
            return matching_series[0].id
        
        # No matching series found, create a new one
        return self.series_registry.create_series(series_name, publisher_id)
    
    def get_series_options(self, publisher_id: str) -> List[Dict[str, Any]]:
        """
        Get available series options for a publisher.
        
        Args:
            publisher_id: ID of the publisher
            
        Returns:
            List of dictionaries with series information
        """
        # Get all series accessible to the publisher
        accessible_series = self.series_registry.get_accessible_series(publisher_id)
        
        # Format series information for UI
        series_options = []
        for series in accessible_series:
            # Get books in the series
            try:
                books = self.series_registry.get_books_in_series(series.id, publisher_id)
                book_count = len(books)
                next_sequence = self.series_registry.get_next_sequence_number(series.id)
            except (SeriesNotFoundError, SeriesAccessDeniedError):
                book_count = 0
                next_sequence = 1
            
            # Add series information
            series_options.append({
                "id": series.id,
                "name": series.name,
                "publisher_id": series.publisher_id,
                "multi_publisher": series.multi_publisher,
                "book_count": book_count,
                "next_sequence": next_sequence,
                "description": series.description,
                "owned": series.publisher_id == publisher_id
            })
        
        # Sort by name
        series_options.sort(key=lambda s: s["name"])
        
        return series_options
    
    def validate_sequence_number(self, series_id: str, sequence_number: int) -> bool:
        """
        Validate that a sequence number is available in a series.
        
        Args:
            series_id: ID of the series
            sequence_number: Sequence number to validate
            
        Returns:
            True if the sequence number is available, False otherwise
        """
        try:
            # Get books in the series
            books = self.series_registry.get_books_in_series(series_id)
            
            # Check if the sequence number is already taken
            for book in books:
                if book.sequence_number == sequence_number:
                    return False
            
            return True
            
        except (SeriesNotFoundError, SeriesAccessDeniedError):
            return False
    
    def get_book_series_info(self, book_id: str) -> List[Dict[str, Any]]:
        """
        Get information about all series a book belongs to.
        
        Args:
            book_id: ID of the book
            
        Returns:
            List of dictionaries with series information
        """
        # Get all series for the book
        series_info = self.series_registry.get_series_for_book(book_id)
        
        # Format series information
        result = []
        for series, sequence_number in series_info:
            result.append({
                "id": series.id,
                "name": series.name,
                "publisher_id": series.publisher_id,
                "multi_publisher": series.multi_publisher,
                "sequence_number": sequence_number
            })
        
        return result
    
    def remove_book_from_all_series(self, book_id: str) -> int:
        """
        Remove a book from all series it belongs to.
        
        Args:
            book_id: ID of the book
            
        Returns:
            Number of series the book was removed from
        """
        # Get all series for the book
        series_info = self.series_registry.get_series_for_book(book_id)
        
        # Remove the book from each series
        removed_count = 0
        for series, _ in series_info:
            try:
                if self.series_registry.remove_book_from_series(series.id, book_id):
                    removed_count += 1
            except (SeriesNotFoundError, SeriesAccessDeniedError) as e:
                logger.warning(f"Error removing book {book_id} from series {series.id}: {e}")
        
        return removed_count