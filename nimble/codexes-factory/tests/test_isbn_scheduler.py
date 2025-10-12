"""
Tests for ISBN scheduling system.
"""
import pytest
import os
import sys
import tempfile
import json
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.modules.distribution.isbn_scheduler import (
    ISBNScheduler, ISBNStatus, ISBNAssignment, ISBNBlock
)

class TestISBNScheduler:
    def setup_method(self):
        """Set up test fixtures with temporary schedule file"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.scheduler = ISBNScheduler(schedule_file=self.temp_file.name)
    
    def teardown_method(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_add_isbn_block(self):
        """Test adding ISBN blocks"""
        block_id = self.scheduler.add_isbn_block(
            prefix="978",
            start_number=1000,
            end_number=1999,
            publisher_code="123456",
            imprint_code="TEST"
        )
        
        assert block_id != ""
        assert block_id in self.scheduler.isbn_blocks
        
        block = self.scheduler.isbn_blocks[block_id]
        assert block.prefix == "978"
        assert block.start_number == 1000
        assert block.end_number == 1999
        assert block.total_count == 1000
        assert block.used_count == 0
    
    def test_schedule_isbn_assignment(self):
        """Test scheduling ISBN assignments"""
        # First add an ISBN block
        self.scheduler.add_isbn_block(
            prefix="978",
            start_number=1000,
            end_number=1999,
            publisher_code="123456"
        )
        
        # Schedule an assignment
        isbn = self.scheduler.schedule_isbn_assignment(
            book_title="Test Book",
            book_id="test_book_1",
            scheduled_date="2024-12-01",
            imprint="test_imprint",
            publisher="test_publisher"
        )
        
        assert isbn is not None
        assert isbn in self.scheduler.assignments
        
        assignment = self.scheduler.assignments[isbn]
        assert assignment.book_title == "Test Book"
        assert assignment.book_id == "test_book_1"
        assert assignment.status == ISBNStatus.SCHEDULED.value
    
    def test_assign_isbn_now(self):
        """Test assigning ISBN immediately"""
        # Add block and schedule assignment
        self.scheduler.add_isbn_block("978", 1000, 1999, "123456")
        isbn = self.scheduler.schedule_isbn_assignment(
            "Test Book", "test_book_1", "2024-12-01"
        )
        
        # Assign the ISBN
        success = self.scheduler.assign_isbn_now(isbn)
        assert success is True
        
        assignment = self.scheduler.assignments[isbn]
        assert assignment.status == ISBNStatus.ASSIGNED.value
        assert assignment.assigned_date is not None
    
    def test_get_scheduled_assignments(self):
        """Test getting scheduled assignments with date filtering"""
        # Add block
        self.scheduler.add_isbn_block("978", 1000, 1999, "123456")
        
        # Schedule multiple assignments
        isbn1 = self.scheduler.schedule_isbn_assignment("Book 1", "book_1", "2024-12-01")
        isbn2 = self.scheduler.schedule_isbn_assignment("Book 2", "book_2", "2024-12-15")
        isbn3 = self.scheduler.schedule_isbn_assignment("Book 3", "book_3", "2025-01-01")
        
        # Get assignments in date range
        assignments = self.scheduler.get_scheduled_assignments(
            start_date="2024-12-01",
            end_date="2024-12-31"
        )
        
        assert len(assignments) == 2
        assert any(a.isbn == isbn1 for a in assignments)
        assert any(a.isbn == isbn2 for a in assignments)
        assert not any(a.isbn == isbn3 for a in assignments)
    
    def test_get_assignments_by_status(self):
        """Test filtering assignments by status"""
        # Add block and create assignments
        self.scheduler.add_isbn_block("978", 1000, 1999, "123456")
        isbn1 = self.scheduler.schedule_isbn_assignment("Book 1", "book_1", "2024-12-01")
        isbn2 = self.scheduler.schedule_isbn_assignment("Book 2", "book_2", "2024-12-01")
        
        # Assign one ISBN
        self.scheduler.assign_isbn_now(isbn1)
        
        # Test filtering
        scheduled = self.scheduler.get_assignments_by_status(ISBNStatus.SCHEDULED)
        assigned = self.scheduler.get_assignments_by_status(ISBNStatus.ASSIGNED)
        
        assert len(scheduled) == 1
        assert len(assigned) == 1
        assert scheduled[0].isbn == isbn2
        assert assigned[0].isbn == isbn1
    
    def test_reserve_isbn(self):
        """Test reserving ISBNs"""
        # Add block and schedule assignment
        self.scheduler.add_isbn_block("978", 1000, 1999, "123456")
        isbn = self.scheduler.schedule_isbn_assignment("Book 1", "book_1", "2024-12-01")
        
        # Reserve the ISBN
        success = self.scheduler.reserve_isbn(isbn, "Special project")
        assert success is True
        
        assignment = self.scheduler.assignments[isbn]
        assert assignment.status == ISBNStatus.RESERVED.value
        assert "Special project" in assignment.notes
    
    def test_update_assignment(self):
        """Test updating existing assignments"""
        # Add block and schedule assignment
        self.scheduler.add_isbn_block("978", 1000, 1999, "123456")
        isbn = self.scheduler.schedule_isbn_assignment("Book 1", "book_1", "2024-12-01")
        
        # Update assignment
        success = self.scheduler.update_assignment(
            isbn,
            book_title="Updated Book Title",
            priority=2,
            notes="Updated notes"
        )
        assert success is True
        
        assignment = self.scheduler.assignments[isbn]
        assert assignment.book_title == "Updated Book Title"
        assert assignment.priority == 2
        assert assignment.notes == "Updated notes"
    
    def test_isbn_availability_report(self):
        """Test generating availability report"""
        # Add block with some assignments
        self.scheduler.add_isbn_block("978", 1000, 1099, "123456")  # 100 ISBNs
        
        # Schedule some assignments
        for i in range(5):
            self.scheduler.schedule_isbn_assignment(f"Book {i}", f"book_{i}", "2024-12-01")
        
        # Generate report
        report = self.scheduler.get_isbn_availability_report()
        
        assert report['total_blocks'] == 1
        assert report['total_isbns'] == 100
        assert report['used_isbns'] == 5
        assert report['available_isbns'] == 95
        assert 'assignments_by_status' in report
        assert 'blocks_detail' in report
    
    def test_persistence(self):
        """Test that schedule persists across sessions"""
        # Add block and assignment
        self.scheduler.add_isbn_block("978", 1000, 1999, "123456")
        isbn = self.scheduler.schedule_isbn_assignment("Test Book", "test_book", "2024-12-01")
        
        # Create new scheduler instance with same file
        new_scheduler = ISBNScheduler(schedule_file=self.temp_file.name)
        
        # Verify data was loaded
        assert len(new_scheduler.isbn_blocks) == 1
        assert len(new_scheduler.assignments) == 1
        assert isbn in new_scheduler.assignments
    
    def test_bulk_schedule_from_csv(self):
        """Test bulk scheduling from CSV file"""
        # Add ISBN block
        self.scheduler.add_isbn_block("978", 1000, 1999, "123456")
        
        # Create test CSV
        csv_content = """title,book_id,scheduled_date,imprint,publisher,format,priority,notes
Book One,book_1,2024-12-01,test_imprint,test_pub,paperback,1,First book
Book Two,book_2,2024-12-15,test_imprint,test_pub,hardcover,2,Second book
Book Three,book_3,2025-01-01,test_imprint,test_pub,ebook,1,Third book"""
        
        # Write to temporary CSV file
        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        csv_file.write(csv_content)
        csv_file.close()
        
        try:
            # Process bulk assignment
            scheduled_count = self.scheduler.bulk_schedule_from_csv(csv_file.name)
            assert scheduled_count == 3
            assert len(self.scheduler.assignments) == 3
            
            # Verify assignment details
            assignments = list(self.scheduler.assignments.values())
            titles = [a.book_title for a in assignments]
            assert "Book One" in titles
            assert "Book Two" in titles
            assert "Book Three" in titles
        finally:
            os.unlink(csv_file.name)
    
    def test_isbn_formatting(self):
        """Test ISBN formatting and check digit calculation"""
        # Test check digit calculation
        check_digit = self.scheduler._calculate_check_digit("978123456789")
        assert isinstance(check_digit, str)
        assert len(check_digit) == 1
        assert check_digit.isdigit()
        
        # Test ISBN formatting
        isbn = self.scheduler._format_isbn("978", "123456", 1000)
        assert isbn.startswith("978123456")
        assert len(isbn) == 13
        assert isbn.isdigit()
    
    def test_error_handling(self):
        """Test error handling for various edge cases"""
        # Test scheduling without ISBN blocks
        isbn = self.scheduler.schedule_isbn_assignment("Test", "test", "2024-12-01")
        assert isbn is None
        
        # Test assigning non-existent ISBN
        success = self.scheduler.assign_isbn_now("9781234567890")
        assert success is False
        
        # Test updating non-existent assignment
        success = self.scheduler.update_assignment("9781234567890", book_title="New Title")
        assert success is False  
  
    def test_get_isbn_by_book_id(self):
        """Test getting ISBN by book ID"""
        # Add block and schedule assignment
        self.scheduler.add_isbn_block("978", 1000, 1999, "123456")
        isbn = self.scheduler.schedule_isbn_assignment("Test Book", "test_book_1", "2024-12-01")
        
        # Test lookup
        found_isbn = self.scheduler.get_isbn_by_book_id("test_book_1")
        assert found_isbn == isbn
        
        # Test non-existent book ID
        not_found = self.scheduler.get_isbn_by_book_id("non_existent")
        assert not_found is None
    
    def test_assign_specific_isbn(self):
        """Test assigning a specific ISBN"""
        # Test assigning new specific ISBN
        success = self.scheduler.assign_specific_isbn(
            isbn="9781234567890",
            book_title="Specific ISBN Book",
            book_id="specific_1",
            scheduled_date="2024-12-01"
        )
        assert success is True
        assert "9781234567890" in self.scheduler.assignments
        
        assignment = self.scheduler.assignments["9781234567890"]
        assert assignment.book_title == "Specific ISBN Book"
        assert assignment.book_id == "specific_1"
        assert assignment.status == ISBNStatus.ASSIGNED.value
        
        # Test updating existing assignment with same book ID
        success = self.scheduler.assign_specific_isbn(
            isbn="9781234567890",
            book_title="Updated Specific Book",
            book_id="specific_1",
            scheduled_date="2024-12-15"
        )
        assert success is True
        
        updated_assignment = self.scheduler.assignments["9781234567890"]
        assert updated_assignment.book_title == "Updated Specific Book"
        
        # Test assigning same ISBN to different book ID (should fail)
        success = self.scheduler.assign_specific_isbn(
            isbn="9781234567890",
            book_title="Different Book",
            book_id="different_1",
            scheduled_date="2024-12-01"
        )
        assert success is False
    
    def test_get_or_assign_isbn(self):
        """Test getting existing ISBN or assigning new one"""
        # Add block
        self.scheduler.add_isbn_block("978", 1000, 1999, "123456")
        
        # First call should assign new ISBN
        isbn1 = self.scheduler.get_or_assign_isbn(
            book_id="test_book_1",
            book_title="Test Book",
            scheduled_date="2024-12-01"
        )
        assert isbn1 is not None
        assert len(self.scheduler.assignments) == 1
        
        # Second call with same book ID should return existing ISBN
        isbn2 = self.scheduler.get_or_assign_isbn(
            book_id="test_book_1",
            book_title="Updated Test Book",
            scheduled_date="2024-12-15"
        )
        assert isbn2 == isbn1
        assert len(self.scheduler.assignments) == 1
        
        # Assignment should be updated with new details
        assignment = self.scheduler.assignments[isbn1]
        assert assignment.book_title == "Updated Test Book"
        assert assignment.scheduled_date == "2024-12-15"
    
    def test_search_assignments(self):
        """Test searching assignments"""
        # Add block and create test assignments
        self.scheduler.add_isbn_block("978", 1000, 1999, "123456")
        
        isbn1 = self.scheduler.schedule_isbn_assignment("Python Programming", "python_1", "2024-12-01")
        isbn2 = self.scheduler.schedule_isbn_assignment("Java Development", "java_1", "2024-12-01")
        isbn3 = self.scheduler.schedule_isbn_assignment("Web Design", "web_1", "2024-12-01")
        
        # Search by title
        results = self.scheduler.search_assignments("Python")
        assert len(results) == 1
        assert results[0].book_title == "Python Programming"
        
        # Search by book ID
        results = self.scheduler.search_assignments("java_1")
        assert len(results) == 1
        assert results[0].book_id == "java_1"
        
        # Search by ISBN (partial)
        isbn_part = isbn3[:10]  # First 10 digits
        results = self.scheduler.search_assignments(isbn_part)
        assert len(results) == 1
        assert results[0].isbn == isbn3
        
        # Search with no results
        results = self.scheduler.search_assignments("nonexistent")
        assert len(results) == 0
    
    def test_rebuild_workflow(self):
        """Test complete rebuild workflow"""
        # Add block
        self.scheduler.add_isbn_block("978", 1000, 1999, "123456")
        
        # Initial book assignment
        isbn = self.scheduler.get_or_assign_isbn(
            book_id="my_book_v1",
            book_title="My Great Book",
            scheduled_date="2024-12-01",
            format="paperback"
        )
        assert isbn is not None
        
        # Assign the ISBN (simulate publication)
        success = self.scheduler.assign_isbn_now(isbn)
        assert success is True
        
        # Later rebuild - should get same ISBN
        rebuild_isbn = self.scheduler.get_or_assign_isbn(
            book_id="my_book_v1",
            book_title="My Great Book (Revised)",
            scheduled_date="2024-12-15",
            format="paperback",
            notes="Rebuild with corrections"
        )
        
        # Should be the same ISBN
        assert rebuild_isbn == isbn
        
        # Assignment should be updated
        assignment = self.scheduler.assignments[isbn]
        assert assignment.book_title == "My Great Book (Revised)"
        assert assignment.scheduled_date == "2024-12-15"
        assert assignment.notes == "Rebuild with corrections"
        assert assignment.status == ISBNStatus.ASSIGNED.value  # Should remain assigned
    
    def test_import_schedule_from_csv_with_manual_isbns(self):
        """Test importing schedule from CSV with manual ISBN assignments"""
        # Add ISBN block for auto-assignments
        self.scheduler.add_isbn_block("978", 1000, 1999, "123456")
        
        # Create test CSV with mixed manual and auto assignments
        csv_content = """title,book_id,scheduled_date,isbn,imprint,publisher,format,priority,notes
Manual ISBN Book,manual_1,2024-12-01,9781234567890,Test Imprint,Test Pub,paperback,1,Has manual ISBN
Auto ISBN Book,auto_1,2024-12-15,,Test Imprint,Test Pub,hardcover,2,Will get auto ISBN
Another Manual,manual_2,2024-12-20,9789876543210,Test Imprint,Test Pub,ebook,1,Another manual"""
        
        # Write to temporary CSV file
        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        csv_file.write(csv_content)
        csv_file.close()
        
        try:
            # Import the schedule
            results = self.scheduler.import_schedule_from_csv(csv_file.name)
            
            # Verify results
            assert results['processed'] == 3
            assert results['assigned_manual'] == 2  # Two manual ISBNs
            assert results['assigned_auto'] == 1    # One auto-assigned
            assert results['updated'] == 0
            assert len(results['errors']) == 0
            
            # Verify assignments were created correctly
            assert len(self.scheduler.assignments) == 3
            
            # Check manual assignments
            assert "9781234567890" in self.scheduler.assignments
            assert "9789876543210" in self.scheduler.assignments
            
            manual_assignment = self.scheduler.assignments["9781234567890"]
            assert manual_assignment.book_title == "Manual ISBN Book"
            assert manual_assignment.book_id == "manual_1"
            assert manual_assignment.status == ISBNStatus.ASSIGNED.value
            
            # Check auto assignment
            auto_isbn = self.scheduler.get_isbn_by_book_id("auto_1")
            assert auto_isbn is not None
            assert auto_isbn.startswith("978123456")
            
        finally:
            os.unlink(csv_file.name)
    
    def test_import_schedule_from_json_with_manual_isbns(self):
        """Test importing schedule from JSON with manual ISBN assignments"""
        # Add ISBN block
        self.scheduler.add_isbn_block("978", 2000, 2999, "654321")
        
        # Create test JSON
        json_data = [
            {
                "title": "JSON Manual Book",
                "book_id": "json_manual_1",
                "scheduled_date": "2024-12-01",
                "isbn": "9781111111111",
                "imprint": "JSON Imprint",
                "publisher": "JSON Pub",
                "format": "paperback",
                "priority": 1,
                "notes": "Manual ISBN from JSON"
            },
            {
                "title": "JSON Auto Book",
                "book_id": "json_auto_1",
                "scheduled_date": "2024-12-15",
                "isbn": "",
                "imprint": "JSON Imprint",
                "publisher": "JSON Pub",
                "format": "hardcover",
                "priority": 2,
                "notes": "Auto ISBN from JSON"
            }
        ]
        
        # Write to temporary JSON file
        json_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(json_data, json_file, indent=2)
        json_file.close()
        
        try:
            # Import the schedule
            results = self.scheduler.import_schedule_from_json(json_file.name)
            
            # Verify results
            assert results['processed'] == 2
            assert results['assigned_manual'] == 1
            assert results['assigned_auto'] == 1
            assert len(results['errors']) == 0
            
            # Verify assignments
            assert "9781111111111" in self.scheduler.assignments
            
            manual_assignment = self.scheduler.assignments["9781111111111"]
            assert manual_assignment.book_title == "JSON Manual Book"
            assert manual_assignment.book_id == "json_manual_1"
            
            auto_isbn = self.scheduler.get_isbn_by_book_id("json_auto_1")
            assert auto_isbn is not None
            
        finally:
            os.unlink(json_file.name)
    
    def test_import_schedule_error_handling(self):
        """Test error handling in schedule import"""
        # Create CSV with errors
        csv_content = """title,book_id,scheduled_date,isbn,notes
Valid Book,valid_1,2024-12-01,,Valid entry
,missing_title,2024-12-01,,Missing title
Invalid ISBN Book,invalid_isbn,2024-12-01,123,Invalid ISBN format
Duplicate ISBN,duplicate_1,2024-12-01,9781234567890,First use
Duplicate ISBN 2,duplicate_2,2024-12-01,9781234567890,Duplicate ISBN"""
        
        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        csv_file.write(csv_content)
        csv_file.close()
        
        try:
            # Add ISBN block for auto-assignment
            self.scheduler.add_isbn_block("978", 3000, 3999, "111111")
            
            results = self.scheduler.import_schedule_from_csv(csv_file.name)
            
            # Should have processed some entries but with errors
            assert results['processed'] == 2  # valid_1 and duplicate_1
            assert len(results['errors']) == 3  # missing title, invalid ISBN, duplicate
            
            # Check that valid entries were processed
            auto_isbn = self.scheduler.get_isbn_by_book_id("valid_1")
            assert auto_isbn is not None
            
            assert "9781234567890" in self.scheduler.assignments
            
        finally:
            os.unlink(csv_file.name)
    
    def test_export_schedule_templates(self):
        """Test exporting schedule templates"""
        # Test CSV template export
        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        csv_file.close()
        
        success = self.scheduler.export_schedule_template_csv(csv_file.name)
        assert success is True
        
        # Verify CSV content
        import csv
        with open(csv_file.name, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2  # Two example rows
            assert 'title' in rows[0]
            assert 'isbn' in rows[0]
            assert rows[0]['isbn'] == '9781234567890'  # Manual ISBN example
            assert rows[1]['isbn'] == ''  # Auto-assign example
        
        os.unlink(csv_file.name)
        
        # Test JSON template export
        json_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json_file.close()
        
        success = self.scheduler.export_schedule_template_json(json_file.name)
        assert success is True
        
        # Verify JSON content
        with open(json_file.name, 'r') as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 2
            assert 'title' in data[0]
            assert 'isbn' in data[0]
            assert data[0]['isbn'] == '9781234567890'
            assert data[1]['isbn'] == ''
        
        os.unlink(json_file.name)
    
    def test_schedule_import_with_existing_assignments(self):
        """Test importing schedule that updates existing assignments"""
        # Add ISBN block
        self.scheduler.add_isbn_block("978", 4000, 4999, "222222")
        
        # Create initial assignment
        initial_isbn = self.scheduler.get_or_assign_isbn(
            book_id="update_test_1",
            book_title="Original Title",
            scheduled_date="2024-12-01"
        )
        
        # Create CSV that updates the existing assignment
        csv_content = """title,book_id,scheduled_date,isbn,notes
Updated Title,update_test_1,2024-12-15,,Updated via import
New Book,new_book_1,2024-12-20,9785555555555,New manual assignment"""
        
        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        csv_file.write(csv_content)
        csv_file.close()
        
        try:
            results = self.scheduler.import_schedule_from_csv(csv_file.name)
            
            # Should have updated existing and created new
            assert results['processed'] == 2
            assert results['updated'] == 1  # Updated existing
            assert results['assigned_manual'] == 1  # New manual assignment
            
            # Verify the update
            updated_assignment = self.scheduler.get_assignment_by_book_id("update_test_1")
            assert updated_assignment.book_title == "Updated Title"
            assert updated_assignment.scheduled_date == "2024-12-15"
            assert updated_assignment.isbn == initial_isbn  # Same ISBN
            
            # Verify new assignment
            assert "9785555555555" in self.scheduler.assignments
            
        finally:
            os.unlink(csv_file.name)