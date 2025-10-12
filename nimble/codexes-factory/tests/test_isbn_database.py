"""
Tests for the ISBN Database module.
"""

import os
import sys
import unittest
import tempfile
import pandas as pd
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.distribution.isbn_database import ISBNDatabase, ISBN, ISBNStatus, ISBNImportError


class TestISBNDatabase(unittest.TestCase):
    """Test cases for the ISBN Database module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary file for the database
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        self.temp_file.close()
        
        # Create the database
        self.db = ISBNDatabase(self.temp_file.name)
        
        # Ensure the test data directory exists
        os.makedirs('tests/test_data/isbn_samples', exist_ok=True)
        
        # Create a simple test CSV if it doesn't exist
        self.test_csv = 'tests/test_data/isbn_samples/test_bowker.csv'
        if not os.path.exists(self.test_csv):
            df = pd.DataFrame({
                'ISBN': ['9781608881001', '9781608881018', '9781608881025'],
                'Title': ['Test Book 1', 'Test Book 2', 'Test Book 3'],
                'Status': ['Available', 'Privately Assigned', 'Publicly Assigned'],
                'Publisher': ['Nimble Books LLC'] * 3,
                'Format': ['Paperback'] * 3
            })
            df.to_csv(self.test_csv, index=False)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary database file
        os.unlink(self.temp_file.name)
    
    def test_isbn_validation(self):
        """Test ISBN validation."""
        # Valid ISBN
        isbn = ISBN(isbn='9781608881001', publisher_id='test')
        self.assertEqual(isbn.isbn, '9781608881001')
        
        # Invalid ISBN
        with self.assertRaises(ValueError):
            ISBN(isbn='invalid', publisher_id='test')
    
    def test_import_from_bowker(self):
        """Test importing ISBNs from a Bowker spreadsheet."""
        # Import from CSV
        stats = self.db.import_from_bowker(self.test_csv, 'test-publisher')
        
        # Check statistics
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['imported'], 3)
        self.assertEqual(stats['available'], 1)
        self.assertEqual(stats['privately_assigned'], 1)
        self.assertEqual(stats['publicly_assigned'], 1)
        
        # Check database
        self.assertEqual(len(self.db.isbns), 3)
        self.assertEqual(self.db.get_isbn_status('9781608881001'), 'available')
        self.assertEqual(self.db.get_isbn_status('9781608881018'), 'privately_assigned')
        self.assertEqual(self.db.get_isbn_status('9781608881025'), 'publicly_assigned')
    
    def test_get_next_available_isbn(self):
        """Test getting the next available ISBN."""
        # Add some ISBNs
        self.db.isbns['9781608881001'] = ISBN(isbn='9781608881001', publisher_id='test-publisher', status=ISBNStatus.AVAILABLE)
        self.db.isbns['9781608881018'] = ISBN(isbn='9781608881018', publisher_id='test-publisher', status=ISBNStatus.PRIVATELY_ASSIGNED)
        self.db.isbns['9781608881025'] = ISBN(isbn='9781608881025', publisher_id='other-publisher', status=ISBNStatus.AVAILABLE)
        
        # Get next available ISBN for specific publisher
        isbn = self.db.get_next_available_isbn('test-publisher')
        self.assertEqual(isbn, '9781608881001')
        
        # Get next available ISBN for any publisher
        isbn = self.db.get_next_available_isbn()
        self.assertIn(isbn, ['9781608881001', '9781608881025'])
    
    def test_assign_isbn(self):
        """Test assigning an ISBN to a book."""
        # Add an available ISBN
        self.db.isbns['9781608881001'] = ISBN(isbn='9781608881001', publisher_id='test-publisher', status=ISBNStatus.AVAILABLE)
        
        # Assign the ISBN
        result = self.db.assign_isbn('9781608881001', 'book-123')
        self.assertTrue(result)
        
        # Check the ISBN status
        self.assertEqual(self.db.get_isbn_status('9781608881001'), 'privately_assigned')
        self.assertEqual(self.db.isbns['9781608881001'].assigned_to, 'book-123')
        self.assertIsNotNone(self.db.isbns['9781608881001'].assignment_date)
        
        # Try to assign an already assigned ISBN
        result = self.db.assign_isbn('9781608881001', 'book-456')
        self.assertFalse(result)
        
        # Try to assign a non-existent ISBN
        result = self.db.assign_isbn('9781608881999', 'book-456')
        self.assertFalse(result)
    
    def test_mark_as_published(self):
        """Test marking an ISBN as published."""
        # Add a privately assigned ISBN
        self.db.isbns['9781608881001'] = ISBN(isbn='9781608881001', publisher_id='test-publisher', status=ISBNStatus.PRIVATELY_ASSIGNED)
        
        # Mark as published
        result = self.db.mark_as_published('9781608881001')
        self.assertTrue(result)
        
        # Check the ISBN status
        self.assertEqual(self.db.get_isbn_status('9781608881001'), 'publicly_assigned')
        self.assertIsNotNone(self.db.isbns['9781608881001'].publication_date)
        
        # Try to mark an already published ISBN
        result = self.db.mark_as_published('9781608881001')
        self.assertFalse(result)
        
        # Try to mark an available ISBN
        self.db.isbns['9781608881018'] = ISBN(isbn='9781608881018', publisher_id='test-publisher', status=ISBNStatus.AVAILABLE)
        result = self.db.mark_as_published('9781608881018')
        self.assertFalse(result)
    
    def test_release_isbn(self):
        """Test releasing an ISBN."""
        # Add a privately assigned ISBN
        self.db.isbns['9781608881001'] = ISBN(
            isbn='9781608881001',
            publisher_id='test-publisher',
            status=ISBNStatus.PRIVATELY_ASSIGNED,
            assigned_to='book-123',
            assignment_date=datetime.now()
        )
        
        # Release the ISBN
        result = self.db.release_isbn('9781608881001')
        self.assertTrue(result)
        
        # Check the ISBN status
        self.assertEqual(self.db.get_isbn_status('9781608881001'), 'available')
        self.assertIsNone(self.db.isbns['9781608881001'].assigned_to)
        self.assertIsNone(self.db.isbns['9781608881001'].assignment_date)
        
        # Try to release an available ISBN
        result = self.db.release_isbn('9781608881001')
        self.assertFalse(result)
        
        # Try to release a published ISBN
        self.db.isbns['9781608881018'] = ISBN(isbn='9781608881018', publisher_id='test-publisher', status=ISBNStatus.PUBLICLY_ASSIGNED)
        result = self.db.release_isbn('9781608881018')
        self.assertFalse(result)
    
    def test_get_statistics(self):
        """Test getting database statistics."""
        # Add some ISBNs
        self.db.isbns['9781608881001'] = ISBN(isbn='9781608881001', publisher_id='test-publisher', status=ISBNStatus.AVAILABLE, format='Paperback')
        self.db.isbns['9781608881018'] = ISBN(isbn='9781608881018', publisher_id='test-publisher', status=ISBNStatus.PRIVATELY_ASSIGNED, format='Hardcover')
        self.db.isbns['9781608881025'] = ISBN(isbn='9781608881025', publisher_id='other-publisher', status=ISBNStatus.PUBLICLY_ASSIGNED, format='Paperback')
        
        # Get statistics
        stats = self.db.get_statistics()
        
        # Check statistics
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['available'], 1)
        self.assertEqual(stats['privately_assigned'], 1)
        self.assertEqual(stats['publicly_assigned'], 1)
        self.assertEqual(set(stats['publishers']), {'test-publisher', 'other-publisher'})
        self.assertEqual(stats['formats']['Paperback'], 2)
        self.assertEqual(stats['formats']['Hardcover'], 1)


if __name__ == '__main__':
    unittest.main()