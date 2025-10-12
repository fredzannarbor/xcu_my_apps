"""
Tests for the Series Assigner module.
"""

import os
import sys
import unittest
import tempfile
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.metadata.metadata_models import CodexMetadata
from codexes.modules.distribution.series_registry import SeriesRegistry
from codexes.modules.distribution.series_assigner import SeriesAssigner, SeriesAssignmentError


class TestSeriesAssigner(unittest.TestCase):
    """Test cases for the Series Assigner module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary file for the registry
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        self.temp_file.close()
        
        # Create the registry and assigner
        self.registry = SeriesRegistry(self.temp_file.name)
        self.assigner = SeriesAssigner(self.registry)
        
        # Create test metadata
        self.metadata = CodexMetadata(
            title="Test Book",
            author="Test Author",
            publisher="test-publisher"
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary registry file
        os.unlink(self.temp_file.name)
    
    def test_assign_book_to_series(self):
        """Test assigning a book to a series."""
        # Assign book to a new series
        series_id, sequence_number = self.assigner.assign_book_to_series(
            self.metadata, "Test Series"
        )
        
        # Check that the series was created
        self.assertIn(series_id, self.registry.series)
        self.assertEqual(self.registry.series[series_id].name, "Test Series")
        
        # Check that the book was added to the series
        books = self.registry.get_books_in_series(series_id)
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].book_id, self.metadata.uuid)
        self.assertEqual(books[0].sequence_number, 1)
        
        # Check that the metadata was updated
        self.assertEqual(self.metadata.series_name, "Test Series")
        self.assertEqual(self.metadata.series_number, "1")
        
        # Assign another book to the same series
        metadata2 = CodexMetadata(
            title="Test Book 2",
            author="Test Author",
            publisher="test-publisher"
        )
        series_id2, sequence_number2 = self.assigner.assign_book_to_series(
            metadata2, "Test Series"
        )
        
        # Check that the same series was used
        self.assertEqual(series_id, series_id2)
        
        # Check that the book was added with the next sequence number
        books = self.registry.get_books_in_series(series_id)
        self.assertEqual(len(books), 2)
        self.assertEqual(sequence_number2, 2)
        
        # Assign a book with a specific sequence number
        metadata3 = CodexMetadata(
            title="Test Book 3",
            author="Test Author",
            publisher="test-publisher"
        )
        series_id3, sequence_number3 = self.assigner.assign_book_to_series(
            metadata3, "Test Series", sequence_number=5
        )
        
        # Check that the book was added with the specified sequence number
        self.assertEqual(sequence_number3, 5)
        self.assertEqual(metadata3.series_number, "5")
    
    def test_assign_book_with_different_publisher(self):
        """Test assigning a book with a different publisher."""
        # Create a series for one publisher
        self.registry.create_series("Publisher Series", "publisher-1")
        
        # Try to assign a book from a different publisher
        metadata = CodexMetadata(
            title="Test Book",
            author="Test Author",
            publisher="publisher-2"
        )
        
        # Should create a new series with the same name for the new publisher
        series_id, sequence_number = self.assigner.assign_book_to_series(
            metadata, "Publisher Series"
        )
        
        # Check that a new series was created
        series_list = self.registry.get_series_by_name("Publisher Series")
        self.assertEqual(len(series_list), 2)
        
        # Check that the book was added to the new series
        books = self.registry.get_books_in_series(series_id)
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].book_id, metadata.uuid)
    
    def test_assign_book_to_multi_publisher_series(self):
        """Test assigning a book to a multi-publisher series."""
        # Create a multi-publisher series
        series_id = self.registry.create_series("Multi-Publisher Series", "publisher-1", multi_publisher=True)
        
        # Assign a book from a different publisher
        metadata = CodexMetadata(
            title="Test Book",
            author="Test Author",
            publisher="publisher-2"
        )
        
        # Should use the existing multi-publisher series
        series_id2, sequence_number = self.assigner.assign_book_to_series(
            metadata, "Multi-Publisher Series", publisher_id="publisher-2"
        )
        
        # Check that the same series was used
        self.assertEqual(series_id, series_id2)
        
        # Check that the book was added to the series
        books = self.registry.get_books_in_series(series_id)
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].book_id, metadata.uuid)
    
    def test_get_series_options(self):
        """Test getting series options for a publisher."""
        # Create series for different publishers
        self.registry.create_series("Series 1", "publisher-1")
        self.registry.create_series("Series 2", "publisher-1")
        self.registry.create_series("Series 3", "publisher-2")
        self.registry.create_series("Multi-Publisher Series", "publisher-2", multi_publisher=True)
        
        # Get series options for publisher-1
        options = self.assigner.get_series_options("publisher-1")
        self.assertEqual(len(options), 3)  # 2 owned + 1 multi-publisher
        
        # Check that the options are sorted by name
        self.assertEqual(options[0]["name"], "Multi-Publisher Series")
        self.assertEqual(options[1]["name"], "Series 1")
        self.assertEqual(options[2]["name"], "Series 2")
        
        # Check owned flag
        self.assertFalse(options[0]["owned"])
        self.assertTrue(options[1]["owned"])
        self.assertTrue(options[2]["owned"])
    
    def test_validate_sequence_number(self):
        """Test validating sequence numbers."""
        # Create a series and add books
        series_id = self.registry.create_series("Test Series", "test-publisher")
        self.registry.add_book_to_series(series_id, "book-1", sequence_number=1)
        self.registry.add_book_to_series(series_id, "book-2", sequence_number=3)
        
        # Check available sequence numbers
        self.assertFalse(self.assigner.validate_sequence_number(series_id, 1))
        self.assertTrue(self.assigner.validate_sequence_number(series_id, 2))
        self.assertFalse(self.assigner.validate_sequence_number(series_id, 3))
        self.assertTrue(self.assigner.validate_sequence_number(series_id, 4))
        
        # Check with non-existent series
        self.assertFalse(self.assigner.validate_sequence_number("non-existent", 1))
    
    def test_get_book_series_info(self):
        """Test getting series info for a book."""
        # Create series and add books
        series_id1 = self.registry.create_series("Series 1", "test-publisher")
        series_id2 = self.registry.create_series("Series 2", "test-publisher")
        
        self.registry.add_book_to_series(series_id1, "book-1", sequence_number=3)
        self.registry.add_book_to_series(series_id2, "book-1", sequence_number=1)
        
        # Get series info for book-1
        series_info = self.assigner.get_book_series_info("book-1")
        self.assertEqual(len(series_info), 2)
        
        # Check series info
        series_names = [info["name"] for info in series_info]
        sequence_numbers = [info["sequence_number"] for info in series_info]
        self.assertIn("Series 1", series_names)
        self.assertIn("Series 2", series_names)
        self.assertIn(3, sequence_numbers)
        self.assertIn(1, sequence_numbers)
        
        # Get series info for non-existent book
        series_info = self.assigner.get_book_series_info("non-existent")
        self.assertEqual(len(series_info), 0)
    
    def test_remove_book_from_all_series(self):
        """Test removing a book from all series."""
        # Create series and add books
        series_id1 = self.registry.create_series("Series 1", "test-publisher")
        series_id2 = self.registry.create_series("Series 2", "test-publisher")
        
        self.registry.add_book_to_series(series_id1, "book-1")
        self.registry.add_book_to_series(series_id2, "book-1")
        self.registry.add_book_to_series(series_id1, "book-2")
        
        # Remove book-1 from all series
        removed_count = self.assigner.remove_book_from_all_series("book-1")
        self.assertEqual(removed_count, 2)
        
        # Check that the book was removed
        series_info = self.assigner.get_book_series_info("book-1")
        self.assertEqual(len(series_info), 0)
        
        # Check that other books were not affected
        books = self.registry.get_books_in_series(series_id1)
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].book_id, "book-2")


if __name__ == '__main__':
    unittest.main()