"""
Tests for the Series Registry module.
"""

import os
import sys
import unittest
import tempfile
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.distribution.series_registry import (
    SeriesRegistry, Series, SeriesBook, SeriesNotFoundError, 
    SeriesAccessDeniedError, SequenceNumberConflictError, SeriesDeleteError
)


class TestSeriesRegistry(unittest.TestCase):
    """Test cases for the Series Registry module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary file for the registry
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        self.temp_file.close()
        
        # Create the registry
        self.registry = SeriesRegistry(self.temp_file.name)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary registry file
        os.unlink(self.temp_file.name)
    
    def test_create_series(self):
        """Test creating a series."""
        # Create a series
        series_id = self.registry.create_series("Test Series", "test-publisher")
        
        # Check that the series was created
        self.assertIn(series_id, self.registry.series)
        self.assertEqual(self.registry.series[series_id].name, "Test Series")
        self.assertEqual(self.registry.series[series_id].publisher_id, "test-publisher")
        self.assertFalse(self.registry.series[series_id].multi_publisher)
        
        # Create a multi-publisher series
        series_id2 = self.registry.create_series("Multi-Publisher Series", "test-publisher", multi_publisher=True)
        self.assertTrue(self.registry.series[series_id2].multi_publisher)
        
        # Test creating a series with an empty name
        with self.assertRaises(ValueError):
            self.registry.create_series("", "test-publisher")
    
    def test_get_series_by_id(self):
        """Test getting a series by ID."""
        # Create a series
        series_id = self.registry.create_series("Test Series", "test-publisher")
        
        # Get the series
        series = self.registry.get_series_by_id(series_id)
        self.assertEqual(series.name, "Test Series")
        
        # Test getting a non-existent series
        with self.assertRaises(SeriesNotFoundError):
            self.registry.get_series_by_id("non-existent")
    
    def test_get_series_by_name(self):
        """Test getting series by name."""
        # Create series
        self.registry.create_series("Test Series", "publisher-1")
        self.registry.create_series("Test Series", "publisher-2")
        self.registry.create_series("Another Series", "publisher-1")
        
        # Get series by name
        series_list = self.registry.get_series_by_name("Test Series")
        self.assertEqual(len(series_list), 2)
        
        # Get series by name and publisher
        series_list = self.registry.get_series_by_name("Test Series", "publisher-1")
        self.assertEqual(len(series_list), 1)
        self.assertEqual(series_list[0].publisher_id, "publisher-1")
        
        # Get non-existent series
        series_list = self.registry.get_series_by_name("Non-Existent Series")
        self.assertEqual(len(series_list), 0)
    
    def test_update_series(self):
        """Test updating series metadata."""
        # Create a series
        series_id = self.registry.create_series("Test Series", "test-publisher")
        
        # Update the series
        updates = {
            "name": "Updated Series",
            "description": "This is an updated series"
        }
        result = self.registry.update_series(series_id, updates)
        self.assertTrue(result)
        
        # Check that the series was updated
        series = self.registry.get_series_by_id(series_id)
        self.assertEqual(series.name, "Updated Series")
        self.assertEqual(series.description, "This is an updated series")
        
        # Test updating a non-existent series
        with self.assertRaises(SeriesNotFoundError):
            self.registry.update_series("non-existent", updates)
        
        # Test updating with a different publisher
        with self.assertRaises(SeriesAccessDeniedError):
            self.registry.update_series(series_id, updates, publisher_id="different-publisher")
        
        # Test updating a multi-publisher series
        multi_series_id = self.registry.create_series("Multi-Publisher Series", "test-publisher", multi_publisher=True)
        result = self.registry.update_series(multi_series_id, updates, publisher_id="different-publisher")
        self.assertTrue(result)
    
    def test_delete_series(self):
        """Test deleting a series."""
        # Create a series
        series_id = self.registry.create_series("Test Series", "test-publisher")
        
        # Delete the series
        result = self.registry.delete_series(series_id)
        self.assertTrue(result)
        
        # Check that the series was deleted
        with self.assertRaises(SeriesNotFoundError):
            self.registry.get_series_by_id(series_id)
        
        # Test deleting a non-existent series
        with self.assertRaises(SeriesNotFoundError):
            self.registry.delete_series("non-existent")
        
        # Test deleting a series with books
        series_id = self.registry.create_series("Series With Books", "test-publisher")
        self.registry.add_book_to_series(series_id, "book-1")
        
        # Should fail without force
        with self.assertRaises(SeriesDeleteError):
            self.registry.delete_series(series_id)
        
        # Should succeed with force
        result = self.registry.delete_series(series_id, force=True)
        self.assertTrue(result)
        
        # Test deleting with a different publisher
        series_id = self.registry.create_series("Another Series", "test-publisher")
        with self.assertRaises(SeriesAccessDeniedError):
            self.registry.delete_series(series_id, publisher_id="different-publisher")
    
    def test_add_book_to_series(self):
        """Test adding a book to a series."""
        # Create a series
        series_id = self.registry.create_series("Test Series", "test-publisher")
        
        # Add a book to the series
        sequence_number = self.registry.add_book_to_series(series_id, "book-1")
        self.assertEqual(sequence_number, 1)
        
        # Add another book with auto-assigned sequence number
        sequence_number = self.registry.add_book_to_series(series_id, "book-2")
        self.assertEqual(sequence_number, 2)
        
        # Add a book with a specific sequence number
        sequence_number = self.registry.add_book_to_series(series_id, "book-3", sequence_number=5)
        self.assertEqual(sequence_number, 5)
        
        # Add a book with a conflicting sequence number
        with self.assertRaises(SequenceNumberConflictError):
            self.registry.add_book_to_series(series_id, "book-4", sequence_number=5)
        
        # Test adding to a non-existent series
        with self.assertRaises(SeriesNotFoundError):
            self.registry.add_book_to_series("non-existent", "book-1")
        
        # Test adding with a different publisher
        with self.assertRaises(SeriesAccessDeniedError):
            self.registry.add_book_to_series(series_id, "book-4", publisher_id="different-publisher")
        
        # Test adding to a multi-publisher series
        multi_series_id = self.registry.create_series("Multi-Publisher Series", "test-publisher", multi_publisher=True)
        sequence_number = self.registry.add_book_to_series(multi_series_id, "book-1", publisher_id="different-publisher")
        self.assertEqual(sequence_number, 1)
    
    def test_remove_book_from_series(self):
        """Test removing a book from a series."""
        # Create a series and add books
        series_id = self.registry.create_series("Test Series", "test-publisher")
        self.registry.add_book_to_series(series_id, "book-1")
        self.registry.add_book_to_series(series_id, "book-2")
        
        # Remove a book
        result = self.registry.remove_book_from_series(series_id, "book-1")
        self.assertTrue(result)
        
        # Check that the book was removed
        books = self.registry.get_books_in_series(series_id)
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].book_id, "book-2")
        
        # Test removing a non-existent book
        result = self.registry.remove_book_from_series(series_id, "non-existent")
        self.assertFalse(result)
        
        # Test removing from a non-existent series
        with self.assertRaises(SeriesNotFoundError):
            self.registry.remove_book_from_series("non-existent", "book-1")
        
        # Test removing with a different publisher
        with self.assertRaises(SeriesAccessDeniedError):
            self.registry.remove_book_from_series(series_id, "book-2", publisher_id="different-publisher")
        
        # Test removing from a multi-publisher series
        multi_series_id = self.registry.create_series("Multi-Publisher Series", "test-publisher", multi_publisher=True)
        self.registry.add_book_to_series(multi_series_id, "book-1")
        result = self.registry.remove_book_from_series(multi_series_id, "book-1", publisher_id="different-publisher")
        self.assertTrue(result)
    
    def test_get_next_sequence_number(self):
        """Test getting the next sequence number."""
        # Create a series
        series_id = self.registry.create_series("Test Series", "test-publisher")
        
        # Check next sequence number for empty series
        next_seq = self.registry.get_next_sequence_number(series_id)
        self.assertEqual(next_seq, 1)
        
        # Add books with specific sequence numbers
        self.registry.add_book_to_series(series_id, "book-1", sequence_number=3)
        self.registry.add_book_to_series(series_id, "book-2", sequence_number=7)
        
        # Check next sequence number
        next_seq = self.registry.get_next_sequence_number(series_id)
        self.assertEqual(next_seq, 8)
        
        # Test with non-existent series
        with self.assertRaises(SeriesNotFoundError):
            self.registry.get_next_sequence_number("non-existent")
    
    def test_get_books_in_series(self):
        """Test getting books in a series."""
        # Create a series and add books
        series_id = self.registry.create_series("Test Series", "test-publisher")
        self.registry.add_book_to_series(series_id, "book-1", sequence_number=3)
        self.registry.add_book_to_series(series_id, "book-2", sequence_number=1)
        self.registry.add_book_to_series(series_id, "book-3", sequence_number=2)
        
        # Get books in the series
        books = self.registry.get_books_in_series(series_id)
        self.assertEqual(len(books), 3)
        
        # Check that books are sorted by sequence number
        self.assertEqual(books[0].book_id, "book-2")  # sequence 1
        self.assertEqual(books[1].book_id, "book-3")  # sequence 2
        self.assertEqual(books[2].book_id, "book-1")  # sequence 3
        
        # Test with non-existent series
        with self.assertRaises(SeriesNotFoundError):
            self.registry.get_books_in_series("non-existent")
        
        # Test with different publisher
        with self.assertRaises(SeriesAccessDeniedError):
            self.registry.get_books_in_series(series_id, publisher_id="different-publisher")
        
        # Test with multi-publisher series
        multi_series_id = self.registry.create_series("Multi-Publisher Series", "test-publisher", multi_publisher=True)
        self.registry.add_book_to_series(multi_series_id, "book-1")
        books = self.registry.get_books_in_series(multi_series_id, publisher_id="different-publisher")
        self.assertEqual(len(books), 1)
    
    def test_get_series_for_book(self):
        """Test getting series for a book."""
        # Create series and add books
        series_id1 = self.registry.create_series("Series 1", "test-publisher")
        series_id2 = self.registry.create_series("Series 2", "test-publisher")
        
        self.registry.add_book_to_series(series_id1, "book-1", sequence_number=3)
        self.registry.add_book_to_series(series_id2, "book-1", sequence_number=1)
        self.registry.add_book_to_series(series_id1, "book-2", sequence_number=4)
        
        # Get series for book-1
        series_list = self.registry.get_series_for_book("book-1")
        self.assertEqual(len(series_list), 2)
        
        # Check series and sequence numbers
        series_names = [s[0].name for s in series_list]
        sequence_numbers = [s[1] for s in series_list]
        self.assertIn("Series 1", series_names)
        self.assertIn("Series 2", series_names)
        self.assertIn(3, sequence_numbers)
        self.assertIn(1, sequence_numbers)
        
        # Get series for book-2
        series_list = self.registry.get_series_for_book("book-2")
        self.assertEqual(len(series_list), 1)
        self.assertEqual(series_list[0][0].name, "Series 1")
        self.assertEqual(series_list[0][1], 4)
        
        # Get series for non-existent book
        series_list = self.registry.get_series_for_book("non-existent")
        self.assertEqual(len(series_list), 0)
    
    def test_get_series_for_publisher(self):
        """Test getting series for a publisher."""
        # Create series for different publishers
        self.registry.create_series("Series 1", "publisher-1")
        self.registry.create_series("Series 2", "publisher-1")
        self.registry.create_series("Series 3", "publisher-2")
        
        # Get series for publisher-1
        series_list = self.registry.get_series_for_publisher("publisher-1")
        self.assertEqual(len(series_list), 2)
        series_names = [s.name for s in series_list]
        self.assertIn("Series 1", series_names)
        self.assertIn("Series 2", series_names)
        
        # Get series for publisher-2
        series_list = self.registry.get_series_for_publisher("publisher-2")
        self.assertEqual(len(series_list), 1)
        self.assertEqual(series_list[0].name, "Series 3")
        
        # Get series for non-existent publisher
        series_list = self.registry.get_series_for_publisher("non-existent")
        self.assertEqual(len(series_list), 0)
    
    def test_get_accessible_series(self):
        """Test getting accessible series for a publisher."""
        # Create series for different publishers
        self.registry.create_series("Series 1", "publisher-1")
        self.registry.create_series("Series 2", "publisher-1")
        self.registry.create_series("Series 3", "publisher-2")
        self.registry.create_series("Multi-Publisher Series", "publisher-2", multi_publisher=True)
        
        # Get accessible series for publisher-1
        series_list = self.registry.get_accessible_series("publisher-1")
        self.assertEqual(len(series_list), 3)  # 2 owned + 1 multi-publisher
        series_names = [s.name for s in series_list]
        self.assertIn("Series 1", series_names)
        self.assertIn("Series 2", series_names)
        self.assertIn("Multi-Publisher Series", series_names)
        
        # Get accessible series for publisher-2
        series_list = self.registry.get_accessible_series("publisher-2")
        self.assertEqual(len(series_list), 2)  # 1 owned + 1 multi-publisher
        series_names = [s.name for s in series_list]
        self.assertIn("Series 3", series_names)
        self.assertIn("Multi-Publisher Series", series_names)
    
    def test_get_statistics(self):
        """Test getting registry statistics."""
        # Create series and add books
        series_id1 = self.registry.create_series("Series 1", "publisher-1")
        series_id2 = self.registry.create_series("Series 2", "publisher-1")
        series_id3 = self.registry.create_series("Series 3", "publisher-2")
        series_id4 = self.registry.create_series("Multi-Publisher Series", "publisher-2", multi_publisher=True)
        
        self.registry.add_book_to_series(series_id1, "book-1")
        self.registry.add_book_to_series(series_id1, "book-2")
        self.registry.add_book_to_series(series_id2, "book-3")
        self.registry.add_book_to_series(series_id4, "book-4")
        self.registry.add_book_to_series(series_id4, "book-5")
        
        # Get statistics
        stats = self.registry.get_statistics()
        
        # Check statistics
        self.assertEqual(stats["total_series"], 4)
        self.assertEqual(stats["total_books"], 5)
        self.assertEqual(set(stats["publishers"]), {"publisher-1", "publisher-2"})
        self.assertEqual(stats["multi_publisher_series"], 1)
        self.assertEqual(stats["series_by_size"][0], 1)  # Series 3 has 0 books
        self.assertEqual(stats["series_by_size"][1], 1)  # Series 2 has 1 book
        self.assertEqual(stats["series_by_size"][2], 2)  # Series 1 and Multi-Publisher Series have 2 books each
    
    def test_persistence(self):
        """Test that the registry persists data to disk."""
        # Create series and add books
        series_id = self.registry.create_series("Test Series", "test-publisher")
        self.registry.add_book_to_series(series_id, "book-1")
        
        # Create a new registry instance with the same storage path
        new_registry = SeriesRegistry(self.temp_file.name)
        
        # Check that the data was loaded
        self.assertIn(series_id, new_registry.series)
        self.assertEqual(new_registry.series[series_id].name, "Test Series")
        
        books = new_registry.get_books_in_series(series_id)
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].book_id, "book-1")


if __name__ == '__main__':
    unittest.main()