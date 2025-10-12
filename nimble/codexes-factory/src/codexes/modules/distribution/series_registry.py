"""
Series Registry Module

This module provides functionality for managing book series metadata, including creating series,
tracking series membership, and assigning sequence numbers to books within series.
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)

@dataclass
class Series:
    """Data class representing a series record."""
    id: str
    name: str
    publisher_id: str
    multi_publisher: bool = False
    creation_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate series data and convert string dates to datetime if needed."""
        # Convert string dates to datetime if needed
        if isinstance(self.creation_date, str):
            try:
                self.creation_date = datetime.fromisoformat(self.creation_date)
            except ValueError:
                try:
                    self.creation_date = datetime.strptime(self.creation_date, "%Y-%m-%d")
                except ValueError:
                    self.creation_date = datetime.now()
        
        if isinstance(self.last_updated, str):
            try:
                self.last_updated = datetime.fromisoformat(self.last_updated)
            except ValueError:
                try:
                    self.last_updated = datetime.strptime(self.last_updated, "%Y-%m-%d")
                except ValueError:
                    self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Series object to dictionary."""
        data = asdict(self)
        # Convert datetime to ISO format string
        if self.creation_date:
            data["creation_date"] = self.creation_date.isoformat()
        if self.last_updated:
            data["last_updated"] = self.last_updated.isoformat()
        return data


@dataclass
class SeriesBook:
    """Data class representing a book's membership in a series."""
    series_id: str
    book_id: str
    sequence_number: int
    addition_date: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate series book data and convert string dates to datetime if needed."""
        # Ensure sequence number is an integer
        if isinstance(self.sequence_number, str):
            try:
                self.sequence_number = int(self.sequence_number)
            except ValueError:
                self.sequence_number = 0
        
        # Convert string dates to datetime if needed
        if isinstance(self.addition_date, str):
            try:
                self.addition_date = datetime.fromisoformat(self.addition_date)
            except ValueError:
                try:
                    self.addition_date = datetime.strptime(self.addition_date, "%Y-%m-%d")
                except ValueError:
                    self.addition_date = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert SeriesBook object to dictionary."""
        data = asdict(self)
        # Convert datetime to ISO format string
        if self.addition_date:
            data["addition_date"] = self.addition_date.isoformat()
        return data


class SeriesError(Exception):
    """Base exception for series-related errors."""
    pass


class SeriesNotFoundError(SeriesError):
    """Exception raised when a series is not found."""
    pass


class SeriesAccessDeniedError(SeriesError):
    """Exception raised when a publisher attempts to access another publisher's series."""
    pass


class SequenceNumberConflictError(SeriesError):
    """Exception raised when there's a conflict in sequence numbers."""
    pass


class SeriesDeleteError(SeriesError):
    """Exception raised when attempting to delete a series with assigned books."""
    pass


class SeriesRegistry:
    """
    Registry for managing book series metadata.
    
    This class provides functionality for creating series, tracking series membership,
    and assigning sequence numbers to books within series.
    """
    
    def __init__(self, storage_path: str = "data/series_registry.json"):
        """
        Initialize the series registry.
        
        Args:
            storage_path: Path to the JSON file for persistent storage
        """
        self.storage_path = storage_path
        self.series: Dict[str, Series] = {}
        self.series_books: Dict[str, List[SeriesBook]] = {}  # series_id -> list of SeriesBook
        self.load_registry()
    
    def load_registry(self) -> None:
        """Load the series registry from disk."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                
                # Load series
                for series_data in data.get("series", []):
                    try:
                        series = Series(
                            id=series_data["id"],
                            name=series_data["name"],
                            publisher_id=series_data["publisher_id"],
                            multi_publisher=series_data.get("multi_publisher", False),
                            creation_date=series_data.get("creation_date"),
                            last_updated=series_data.get("last_updated"),
                            description=series_data.get("description")
                        )
                        self.series[series.id] = series
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Error loading series {series_data.get('id', 'unknown')}: {e}")
                
                # Load series books
                for book_data in data.get("series_books", []):
                    try:
                        series_book = SeriesBook(
                            series_id=book_data["series_id"],
                            book_id=book_data["book_id"],
                            sequence_number=book_data["sequence_number"],
                            addition_date=book_data.get("addition_date")
                        )
                        
                        if series_book.series_id not in self.series_books:
                            self.series_books[series_book.series_id] = []
                        
                        self.series_books[series_book.series_id].append(series_book)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Error loading series book {book_data.get('book_id', 'unknown')}: {e}")
                
                logger.info(f"Loaded {len(self.series)} series and {sum(len(books) for books in self.series_books.values())} series books from registry")
            else:
                logger.info(f"No existing registry found at {self.storage_path}")
        except Exception as e:
            logger.error(f"Error loading series registry: {e}")
    
    def save_registry(self) -> None:
        """Save the series registry to disk."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            # Convert series and series books to dictionaries
            series_dicts = [series.to_dict() for series in self.series.values()]
            series_book_dicts = []
            for books in self.series_books.values():
                series_book_dicts.extend([book.to_dict() for book in books])
            
            # Save to JSON
            with open(self.storage_path, "w") as f:
                json.dump({
                    "series": series_dicts,
                    "series_books": series_book_dicts
                }, f, indent=2)
            
            logger.info(f"Saved {len(self.series)} series and {len(series_book_dicts)} series books to registry")
        except Exception as e:
            logger.error(f"Error saving series registry: {e}")
    
    def create_series(self, name: str, publisher_id: str, multi_publisher: bool = False, description: Optional[str] = None) -> str:
        """
        Create a new series and return its ID.
        
        Args:
            name: Name of the series
            publisher_id: ID of the publisher creating the series
            multi_publisher: Whether the series allows multiple publishers
            description: Optional description of the series
            
        Returns:
            ID of the created series
            
        Raises:
            ValueError: If the series name is empty
        """
        if not name:
            raise ValueError("Series name cannot be empty")
        
        # Generate a unique ID for the series
        series_id = str(uuid.uuid4())
        
        # Create the series
        series = Series(
            id=series_id,
            name=name,
            publisher_id=publisher_id,
            multi_publisher=multi_publisher,
            description=description
        )
        
        # Add to registry
        self.series[series_id] = series
        self.series_books[series_id] = []
        
        # Save the updated registry
        self.save_registry()
        
        logger.info(f"Created series '{name}' with ID {series_id} for publisher {publisher_id}")
        return series_id
    
    def get_series_by_id(self, series_id: str) -> Series:
        """
        Get series metadata by ID.
        
        Args:
            series_id: ID of the series
            
        Returns:
            Series object
            
        Raises:
            SeriesNotFoundError: If the series is not found
        """
        if series_id not in self.series:
            raise SeriesNotFoundError(f"Series with ID {series_id} not found")
        
        return self.series[series_id]
    
    def get_series_by_name(self, name: str, publisher_id: Optional[str] = None) -> List[Series]:
        """
        Get series by name, optionally filtered by publisher.
        
        Args:
            name: Name of the series
            publisher_id: Optional ID of the publisher
            
        Returns:
            List of matching Series objects
        """
        matches = []
        for series in self.series.values():
            if series.name == name:
                if publisher_id is None or series.publisher_id == publisher_id or series.multi_publisher:
                    matches.append(series)
        
        return matches
    
    def update_series(self, series_id: str, updates: Dict[str, Any], publisher_id: Optional[str] = None) -> bool:
        """
        Update series metadata.
        
        Args:
            series_id: ID of the series to update
            updates: Dictionary of fields to update
            publisher_id: Optional ID of the publisher making the update
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            SeriesNotFoundError: If the series is not found
            SeriesAccessDeniedError: If the publisher doesn't have access to the series
        """
        if series_id not in self.series:
            raise SeriesNotFoundError(f"Series with ID {series_id} not found")
        
        series = self.series[series_id]
        
        # Check publisher access
        if publisher_id is not None and publisher_id != series.publisher_id and not series.multi_publisher:
            raise SeriesAccessDeniedError(f"Publisher {publisher_id} does not have access to series {series_id}")
        
        # Update fields
        for key, value in updates.items():
            if hasattr(series, key) and key not in ["id", "publisher_id"]:  # Prevent changing immutable fields
                setattr(series, key, value)
        
        # Update last_updated timestamp
        series.last_updated = datetime.now()
        
        # Save the updated registry
        self.save_registry()
        
        logger.info(f"Updated series {series_id}")
        return True
    
    def delete_series(self, series_id: str, publisher_id: Optional[str] = None, force: bool = False) -> bool:
        """
        Delete a series.
        
        Args:
            series_id: ID of the series to delete
            publisher_id: Optional ID of the publisher making the deletion
            force: Whether to force deletion even if books are assigned
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            SeriesNotFoundError: If the series is not found
            SeriesAccessDeniedError: If the publisher doesn't have access to the series
            SeriesDeleteError: If books are assigned to the series and force is False
        """
        if series_id not in self.series:
            raise SeriesNotFoundError(f"Series with ID {series_id} not found")
        
        series = self.series[series_id]
        
        # Check publisher access
        if publisher_id is not None and publisher_id != series.publisher_id:
            raise SeriesAccessDeniedError(f"Publisher {publisher_id} does not have access to series {series_id}")
        
        # Check if books are assigned
        if series_id in self.series_books and self.series_books[series_id] and not force:
            raise SeriesDeleteError(f"Cannot delete series {series_id} with assigned books")
        
        # Delete the series
        del self.series[series_id]
        if series_id in self.series_books:
            del self.series_books[series_id]
        
        # Save the updated registry
        self.save_registry()
        
        logger.info(f"Deleted series {series_id}")
        return True
    
    def add_book_to_series(self, series_id: str, book_id: str, sequence_number: Optional[int] = None, publisher_id: Optional[str] = None) -> int:
        """
        Add a book to a series with an optional sequence number.
        
        Args:
            series_id: ID of the series
            book_id: ID of the book
            sequence_number: Optional sequence number (auto-assigned if None)
            publisher_id: Optional ID of the publisher adding the book
            
        Returns:
            Assigned sequence number
            
        Raises:
            SeriesNotFoundError: If the series is not found
            SeriesAccessDeniedError: If the publisher doesn't have access to the series
            SequenceNumberConflictError: If the sequence number is already taken
        """
        if series_id not in self.series:
            raise SeriesNotFoundError(f"Series with ID {series_id} not found")
        
        series = self.series[series_id]
        
        # Check publisher access
        if publisher_id is not None and publisher_id != series.publisher_id and not series.multi_publisher:
            raise SeriesAccessDeniedError(f"Publisher {publisher_id} does not have access to series {series_id}")
        
        # Initialize series books list if it doesn't exist
        if series_id not in self.series_books:
            self.series_books[series_id] = []
        
        # Check if book is already in the series
        for book in self.series_books[series_id]:
            if book.book_id == book_id:
                # Book is already in the series, update sequence number if provided
                if sequence_number is not None and book.sequence_number != sequence_number:
                    # Check for sequence number conflict
                    for other_book in self.series_books[series_id]:
                        if other_book.book_id != book_id and other_book.sequence_number == sequence_number:
                            raise SequenceNumberConflictError(f"Sequence number {sequence_number} is already taken in series {series_id}")
                    
                    # Update sequence number
                    book.sequence_number = sequence_number
                    self.save_registry()
                    logger.info(f"Updated sequence number for book {book_id} in series {series_id} to {sequence_number}")
                
                return book.sequence_number
        
        # Auto-assign sequence number if not provided
        if sequence_number is None:
            sequence_number = self.get_next_sequence_number(series_id)
        else:
            # Check for sequence number conflict
            for book in self.series_books[series_id]:
                if book.sequence_number == sequence_number:
                    raise SequenceNumberConflictError(f"Sequence number {sequence_number} is already taken in series {series_id}")
        
        # Create series book
        series_book = SeriesBook(
            series_id=series_id,
            book_id=book_id,
            sequence_number=sequence_number
        )
        
        # Add to registry
        self.series_books[series_id].append(series_book)
        
        # Save the updated registry
        self.save_registry()
        
        logger.info(f"Added book {book_id} to series {series_id} with sequence number {sequence_number}")
        return sequence_number
    
    def remove_book_from_series(self, series_id: str, book_id: str, publisher_id: Optional[str] = None) -> bool:
        """
        Remove a book from a series.
        
        Args:
            series_id: ID of the series
            book_id: ID of the book
            publisher_id: Optional ID of the publisher removing the book
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            SeriesNotFoundError: If the series is not found
            SeriesAccessDeniedError: If the publisher doesn't have access to the series
        """
        if series_id not in self.series:
            raise SeriesNotFoundError(f"Series with ID {series_id} not found")
        
        series = self.series[series_id]
        
        # Check publisher access
        if publisher_id is not None and publisher_id != series.publisher_id and not series.multi_publisher:
            raise SeriesAccessDeniedError(f"Publisher {publisher_id} does not have access to series {series_id}")
        
        # Check if series books list exists
        if series_id not in self.series_books:
            return False
        
        # Find and remove the book
        for i, book in enumerate(self.series_books[series_id]):
            if book.book_id == book_id:
                self.series_books[series_id].pop(i)
                self.save_registry()
                logger.info(f"Removed book {book_id} from series {series_id}")
                return True
        
        return False
    
    def get_next_sequence_number(self, series_id: str) -> int:
        """
        Get the next available sequence number for a series.
        
        Args:
            series_id: ID of the series
            
        Returns:
            Next available sequence number
            
        Raises:
            SeriesNotFoundError: If the series is not found
        """
        if series_id not in self.series:
            raise SeriesNotFoundError(f"Series with ID {series_id} not found")
        
        # Check if series books list exists
        if series_id not in self.series_books or not self.series_books[series_id]:
            return 1
        
        # Find the highest sequence number
        max_sequence = max(book.sequence_number for book in self.series_books[series_id])
        return max_sequence + 1
    
    def get_books_in_series(self, series_id: str, publisher_id: Optional[str] = None) -> List[SeriesBook]:
        """
        Get all books in a series.
        
        Args:
            series_id: ID of the series
            publisher_id: Optional ID of the publisher
            
        Returns:
            List of SeriesBook objects
            
        Raises:
            SeriesNotFoundError: If the series is not found
            SeriesAccessDeniedError: If the publisher doesn't have access to the series
        """
        if series_id not in self.series:
            raise SeriesNotFoundError(f"Series with ID {series_id} not found")
        
        series = self.series[series_id]
        
        # Check publisher access
        if publisher_id is not None and publisher_id != series.publisher_id and not series.multi_publisher:
            raise SeriesAccessDeniedError(f"Publisher {publisher_id} does not have access to series {series_id}")
        
        # Return books in the series
        if series_id not in self.series_books:
            return []
        
        return sorted(self.series_books[series_id], key=lambda book: book.sequence_number)
    
    def get_series_for_book(self, book_id: str) -> List[Tuple[Series, int]]:
        """
        Get all series that a book belongs to.
        
        Args:
            book_id: ID of the book
            
        Returns:
            List of tuples (Series, sequence_number)
        """
        result = []
        for series_id, books in self.series_books.items():
            for book in books:
                if book.book_id == book_id:
                    result.append((self.series[series_id], book.sequence_number))
        
        return result
    
    def get_series_for_publisher(self, publisher_id: str) -> List[Series]:
        """
        Get all series owned by a publisher.
        
        Args:
            publisher_id: ID of the publisher
            
        Returns:
            List of Series objects
        """
        return [series for series in self.series.values() if series.publisher_id == publisher_id]
    
    def get_accessible_series(self, publisher_id: str) -> List[Series]:
        """
        Get all series accessible to a publisher (owned or multi-publisher).
        
        Args:
            publisher_id: ID of the publisher
            
        Returns:
            List of Series objects
        """
        return [
            series for series in self.series.values()
            if series.publisher_id == publisher_id or series.multi_publisher
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the series registry.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_series": len(self.series),
            "total_books": sum(len(books) for books in self.series_books.values()),
            "publishers": set(),
            "multi_publisher_series": 0,
            "series_by_size": {}
        }
        
        for series in self.series.values():
            # Count by publisher
            stats["publishers"].add(series.publisher_id)
            
            # Count multi-publisher series
            if series.multi_publisher:
                stats["multi_publisher_series"] += 1
            
            # Count by series size
            series_size = len(self.series_books.get(series.id, []))
            stats["series_by_size"][series_size] = stats["series_by_size"].get(series_size, 0) + 1
        
        # Convert set to list for JSON serialization
        stats["publishers"] = list(stats["publishers"])
        
        return stats


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create series registry
    registry = SeriesRegistry("data/series_registry_test.json")
    
    # Create a series
    series_id = registry.create_series("Test Series", "test-publisher")
    
    # Add books to the series
    registry.add_book_to_series(series_id, "book-1")
    registry.add_book_to_series(series_id, "book-2")
    registry.add_book_to_series(series_id, "book-3", sequence_number=5)
    
    # Get books in the series
    books = registry.get_books_in_series(series_id)
    print(f"Books in series: {books}")
    
    # Get registry statistics
    stats = registry.get_statistics()
    print(f"Registry statistics: {stats}")