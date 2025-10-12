"""
Tests for the ISBN Assignment module.
"""

import os
import sys
import unittest
import tempfile
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.distribution.isbn_database import ISBNDatabase, ISBN, ISBNStatus
from codexes.modules.distribution.isbn_assignment import determine_isbn_requirement, assign_isbn_to_book
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestISBNAssignment(unittest.TestCase):
    """Test cases for the ISBN Assignment module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary file for the database
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        self.temp_file.close()
        
        # Create the database
        self.db = ISBNDatabase(self.temp_file.name)
        
        # Add some test ISBNs
        self.db.isbns['9781608881001'] = ISBN(isbn='9781608881001', publisher_id='test-publisher', status=ISBNStatus.AVAILABLE)
        self.db.isbns['9781608881018'] = ISBN(isbn='9781608881018', publisher_id='test-publisher', status=ISBNStatus.PRIVATELY_ASSIGNED)
        self.db.isbns['9781608881025'] = ISBN(isbn='9781608881025', publisher_id='test-publisher', status=ISBNStatus.PUBLICLY_ASSIGNED)
        self.db.isbns['9781608881032'] = ISBN(isbn='9781608881032', publisher_id='other-publisher', status=ISBNStatus.AVAILABLE)
        
        # Save the database
        self.db.save_database()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary database file
        os.unlink(self.temp_file.name)
    
    def test_determine_isbn_requirement(self):
        """Test determining if a book requires an ISBN."""
        # Create test metadata
        metadata = CodexMetadata()
        
        # Test with different distribution channels
        self.assertTrue(determine_isbn_requirement(metadata, ["ingram"]))
        self.assertTrue(determine_isbn_requirement(metadata, ["lsi"]))
        self.assertTrue(determine_isbn_requirement(metadata, ["kdp"]))
        self.assertFalse(determine_isbn_requirement(metadata, ["storefront"]))
        self.assertTrue(determine_isbn_requirement(metadata, ["kdp", "storefront"]))
        self.assertTrue(determine_isbn_requirement(metadata, ["ingram", "storefront"]))
        
        # Test with LSI fields
        metadata.lightning_source_account = "12345"
        self.assertTrue(determine_isbn_requirement(metadata, None))
        
        # Test default behavior
        metadata = CodexMetadata()
        self.assertTrue(determine_isbn_requirement(metadata, None))
    
    def test_assign_isbn_to_book(self):
        """Test assigning an ISBN to a book."""
        # Create test metadata
        metadata = CodexMetadata()
        metadata.title = "Test Book"
        metadata.uuid = "test-book-123"
        
        # Test assigning ISBN
        success, isbn, details = assign_isbn_to_book(
            metadata=metadata,
            isbn_db=self.db,
            publisher_id='test-publisher',
            distribution_channels=["ingram"]
        )
        
        # Check results
        self.assertTrue(success)
        self.assertEqual(isbn, '9781608881001')
        self.assertEqual(metadata.isbn13, '9781608881001')
        self.assertTrue(details['isbn_assigned'])
        
        # Check database
        self.assertEqual(self.db.get_isbn_status('9781608881001'), 'privately_assigned')
        self.assertEqual(self.db.isbns['9781608881001'].assigned_to, 'test-book-123')
        
        # Test with already assigned ISBN
        metadata = CodexMetadata()
        metadata.title = "Test Book 2"
        metadata.isbn13 = "9781234567890"
        
        success, isbn, details = assign_isbn_to_book(
            metadata=metadata,
            isbn_db=self.db,
            publisher_id='test-publisher',
            distribution_channels=["ingram"]
        )
        
        # Check results
        self.assertTrue(success)
        self.assertEqual(isbn, '9781234567890')
        self.assertTrue(details['isbn_already_assigned'])
        self.assertFalse(details['isbn_assigned'])
        
        # Test with no available ISBNs
        # First, assign the remaining available ISBN
        self.db.assign_isbn('9781608881032', 'another-book')
        
        metadata = CodexMetadata()
        metadata.title = "Test Book 3"
        
        success, isbn, details = assign_isbn_to_book(
            metadata=metadata,
            isbn_db=self.db,
            publisher_id='test-publisher',
            distribution_channels=["ingram"]
        )
        
        # Check results
        self.assertFalse(success)
        self.assertIsNone(isbn)
        self.assertFalse(details['isbn_assigned'])
        
        # Test with non-required ISBN
        metadata = CodexMetadata()
        metadata.title = "Test Book 4"
        
        success, isbn, details = assign_isbn_to_book(
            metadata=metadata,
            isbn_db=self.db,
            publisher_id='test-publisher',
            distribution_channels=["storefront"],
            force_assign=False
        )
        
        # Check results
        self.assertFalse(success)
        self.assertIsNone(isbn)
        self.assertFalse(details['isbn_required'])
        self.assertFalse(details['isbn_assigned'])


if __name__ == '__main__':
    unittest.main()