"""
Tests for Schedule ISBN Manager.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch
from datetime import datetime

try:
    from src.codexes.modules.distribution.schedule_isbn_manager import ScheduleISBNManager
    from src.codexes.modules.distribution.isbn_database import ISBNDatabase, ISBN, ISBNStatus
except ImportError:
    from codexes.modules.distribution.schedule_isbn_manager import ScheduleISBNManager
    from codexes.modules.distribution.isbn_database import ISBNDatabase, ISBN, ISBNStatus


class TestScheduleISBNManager:
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary files
        self.temp_dir = tempfile.mkdtemp()
        self.isbn_db_file = os.path.join(self.temp_dir, "test_isbn_db.json")
        self.schedule_file = os.path.join(self.temp_dir, "test_schedule.json")
        
        # Create test ISBN database
        self.create_test_isbn_database()
        
        # Create test schedule
        self.create_test_schedule()
        
        # Initialize manager
        self.manager = ScheduleISBNManager(self.isbn_db_file)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_isbn_database(self):
        """Create a test ISBN database."""
        test_isbns = {
            "9781234567890": {
                "isbn": "9781234567890",
                "publisher_id": "test-publisher",
                "status": "available",
                "title": None,
                "format": None,
                "imprint": None,
                "assigned_date": None,
                "metadata": {}
            },
            "9781234567891": {
                "isbn": "9781234567891",
                "publisher_id": "test-publisher",
                "status": "available",
                "title": None,
                "format": None,
                "imprint": None,
                "assigned_date": None,
                "metadata": {}
            },
            "9781234567892": {
                "isbn": "9781234567892",
                "publisher_id": "other-publisher",
                "status": "available",
                "title": None,
                "format": None,
                "imprint": None,
                "assigned_date": None,
                "metadata": {}
            }
        }
        
        db_data = {
            "isbns": test_isbns,
            "metadata": {
                "created_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
        
        with open(self.isbn_db_file, 'w') as f:
            json.dump(db_data, f, indent=2)
    
    def create_test_schedule(self):
        """Create a test schedule file."""
        schedule_data = {
            "publishing_schedule": [
                {
                    "month": "July 2025",
                    "books": [
                        {
                            "title": "Test Book 1",
                            "description": "A test book",
                            "stream": "Test Stream",
                            "author": "Test Author",
                            "imprint": "test-imprint"
                        },
                        {
                            "title": "Test Book 2",
                            "description": "Another test book",
                            "stream": "Test Stream",
                            "author": "Test Author",
                            "imprint": "test-imprint",
                            "isbn": "9781234567893"  # Already has ISBN
                        }
                    ]
                },
                {
                    "month": "August 2025",
                    "books": [
                        {
                            "title": "Test Book 3",
                            "description": "Third test book",
                            "stream": "Test Stream",
                            "author": "Test Author",
                            "imprint": "test-imprint"
                        }
                    ]
                }
            ]
        }
        
        with open(self.schedule_file, 'w') as f:
            json.dump(schedule_data, f, indent=2)
    
    def test_assign_isbn_to_book_success(self):
        """Test successful ISBN assignment to a book."""
        book_data = {
            "title": "New Test Book",
            "description": "A new test book",
            "stream": "Test Stream",
            "author": "Test Author",
            "imprint": "test-imprint"
        }
        
        success, message, assigned_isbn = self.manager.assign_isbn_to_book(
            book_data, "test-publisher"
        )
        
        assert success is True
        assert assigned_isbn is not None
        assert len(assigned_isbn) == 13
        assert "isbn" in book_data
        assert book_data["isbn"] == assigned_isbn
        assert "isbn_assigned_date" in book_data
    
    def test_assign_isbn_to_book_already_has_isbn(self):
        """Test ISBN assignment when book already has an ISBN."""
        book_data = {
            "title": "Book with ISBN",
            "isbn": "9781234567890"
        }
        
        success, message, assigned_isbn = self.manager.assign_isbn_to_book(
            book_data, "test-publisher"
        )
        
        assert success is True
        assert "already has ISBN" in message
        assert assigned_isbn == "9781234567890"
    
    def test_assign_isbn_to_book_no_available_isbns(self):
        """Test ISBN assignment when no ISBNs are available."""
        success, message, assigned_isbn = self.manager.assign_isbn_to_book(
            {"title": "Test Book"}, "nonexistent-publisher"
        )
        
        assert success is False
        assert "No available ISBNs" in message
        assert assigned_isbn is None
    
    def test_assign_specific_isbn_success(self):
        """Test assigning a specific ISBN."""
        book_data = {
            "title": "Specific ISBN Book",
            "description": "A book with specific ISBN"
        }
        
        success, message, assigned_isbn = self.manager.assign_isbn_to_book(
            book_data, "test-publisher", preferred_isbn="9781234567890"
        )
        
        assert success is True
        assert assigned_isbn == "9781234567890"
        assert book_data["isbn"] == "9781234567890"
    
    def test_assign_specific_isbn_not_available(self):
        """Test assigning a specific ISBN that's not available."""
        # First assign the ISBN to make it unavailable
        self.manager.isbn_db.assign_isbn("9781234567890", title="Already Assigned")
        
        book_data = {"title": "Test Book"}
        
        success, message, assigned_isbn = self.manager.assign_isbn_to_book(
            book_data, "test-publisher", preferred_isbn="9781234567890"
        )
        
        # Should fall back to next available ISBN
        assert success is True
        assert assigned_isbn != "9781234567890"
        assert assigned_isbn == "9781234567891"
    
    def test_assign_isbns_to_schedule_dry_run(self):
        """Test dry run ISBN assignment to schedule."""
        results = self.manager.assign_isbns_to_schedule(
            self.schedule_file, "test-publisher", dry_run=True
        )
        
        assert results['total_books'] == 3
        assert results['assigned'] == 2  # Two books without ISBNs
        assert results['already_assigned'] == 1  # One book with ISBN
        assert results['failed'] == 0
        assert len(results['assignments']) == 3
    
    def test_assign_isbns_to_schedule_actual(self):
        """Test actual ISBN assignment to schedule."""
        results = self.manager.assign_isbns_to_schedule(
            self.schedule_file, "test-publisher", dry_run=False
        )
        
        assert results['total_books'] == 3
        assert results['assigned'] == 2
        assert results['already_assigned'] == 1
        assert results['failed'] == 0
        
        # Verify schedule file was updated
        with open(self.schedule_file, 'r') as f:
            updated_schedule = json.load(f)
        
        # Check that books without ISBNs now have them
        book1 = updated_schedule['publishing_schedule'][0]['books'][0]
        book3 = updated_schedule['publishing_schedule'][1]['books'][0]
        
        assert 'isbn' in book1
        assert 'isbn' in book3
        assert len(book1['isbn']) == 13
        assert len(book3['isbn']) == 13
    
    def test_validate_schedule_isbns(self):
        """Test ISBN validation in schedule."""
        results = self.manager.validate_schedule_isbns(self.schedule_file)
        
        assert results['total_books'] == 3
        assert results['books_with_isbn'] == 1
        assert results['valid_isbns'] == 0  # ISBN not in database
        assert results['invalid_isbns'] == 1  # ISBN not in database
        assert results['duplicate_isbns'] == 0
        
        assert len(results['validation_details']) == 3
    
    def test_bulk_assign_isbns(self):
        """Test bulk ISBN assignment."""
        assignments = [
            {"title": "Test Book 1", "isbn": "9781111111111"},
            {"title": "Test Book 3", "isbn": "9782222222222"},
            {"title": "Nonexistent Book", "isbn": "9783333333333"}
        ]
        
        results = self.manager.bulk_assign_isbns(
            assignments, self.schedule_file
        )
        
        assert results['total_assignments'] == 3
        assert results['successful'] == 2
        assert results['failed'] == 0
        assert results['not_found'] == 1
        
        # Verify assignments were applied
        with open(self.schedule_file, 'r') as f:
            updated_schedule = json.load(f)
        
        book1 = updated_schedule['publishing_schedule'][0]['books'][0]
        book3 = updated_schedule['publishing_schedule'][1]['books'][0]
        
        assert book1['isbn'] == '9781111111111'
        assert book3['isbn'] == '9782222222222'
    
    def test_generate_isbn_report(self):
        """Test ISBN report generation."""
        report = self.manager.generate_isbn_report(self.schedule_file)
        
        assert 'summary' in report
        assert 'validation_details' in report
        assert 'recommendations' in report
        
        summary = report['summary']
        assert summary['total_books'] == 3
        assert summary['books_with_isbn'] == 1
        assert summary['books_without_isbn'] == 2
        
        # Should have recommendations
        assert len(report['recommendations']) > 0
        assert any('Assign ISBNs' in rec for rec in report['recommendations'])
    
    def test_get_available_isbn_count(self):
        """Test getting available ISBN count."""
        count = self.manager.get_available_isbn_count("test-publisher")
        assert count == 2  # Two available ISBNs for test-publisher
        
        count = self.manager.get_available_isbn_count("other-publisher")
        assert count == 1  # One available ISBN for other-publisher
        
        count = self.manager.get_available_isbn_count("nonexistent-publisher")
        assert count == 0  # No ISBNs for nonexistent publisher
    
    def test_assignment_log(self):
        """Test assignment logging."""
        # Clear log first
        self.manager.clear_assignment_log()
        
        book_data = {"title": "Logged Book"}
        self.manager.assign_isbn_to_book(book_data, "test-publisher")
        
        log = self.manager.get_assignment_log()
        assert len(log) == 1
        assert log[0]['title'] == 'Logged Book'
        assert log[0]['publisher_id'] == 'test-publisher'
        assert 'isbn' in log[0]
        assert 'assigned_date' in log[0]
    
    def test_error_handling_invalid_schedule(self):
        """Test error handling with invalid schedule file."""
        # Create invalid schedule file
        invalid_schedule = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_schedule, 'w') as f:
            f.write("invalid json")
        
        results = self.manager.assign_isbns_to_schedule(
            invalid_schedule, "test-publisher"
        )
        
        assert 'error' in results
    
    def test_error_handling_nonexistent_schedule(self):
        """Test error handling with nonexistent schedule file."""
        results = self.manager.assign_isbns_to_schedule(
            "nonexistent.json", "test-publisher"
        )
        
        assert 'error' in results