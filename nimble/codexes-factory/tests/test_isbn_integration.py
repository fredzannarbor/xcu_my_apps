"""
Integration tests for ISBN scheduling system.
"""
import pytest
import os
import sys
import tempfile
import subprocess
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.modules.distribution.isbn_scheduler import ISBNScheduler, ISBNStatus

class TestISBNIntegration:
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.scheduler = ISBNScheduler(schedule_file=self.temp_file.name)
    
    def teardown_method(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_complete_workflow(self):
        """Test complete ISBN assignment workflow"""
        # 1. Add ISBN block
        block_id = self.scheduler.add_isbn_block(
            prefix="978",
            start_number=1000,
            end_number=1099,
            publisher_code="123456",
            imprint_code="TEST"
        )
        assert block_id != ""
        
        # 2. Schedule multiple assignments with future dates
        future_date1 = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        future_date2 = (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d')
        future_date3 = (datetime.now() + timedelta(days=40)).strftime('%Y-%m-%d')
        
        isbn1 = self.scheduler.schedule_isbn_assignment(
            "Book One", "book_1", future_date1, priority=1
        )
        isbn2 = self.scheduler.schedule_isbn_assignment(
            "Book Two", "book_2", future_date2, priority=2
        )
        isbn3 = self.scheduler.schedule_isbn_assignment(
            "Book Three", "book_3", future_date3, priority=1
        )
        
        assert all([isbn1, isbn2, isbn3])
        assert len(self.scheduler.assignments) == 3
        
        # 3. Check upcoming assignments
        upcoming = self.scheduler.get_upcoming_assignments(30)
        assert len(upcoming) >= 2  # At least the December books
        
        # 4. Assign one ISBN
        success = self.scheduler.assign_isbn_now(isbn1)
        assert success is True
        
        assignment = self.scheduler.assignments[isbn1]
        assert assignment.status == ISBNStatus.ASSIGNED.value
        assert assignment.assigned_date is not None
        
        # 5. Reserve one ISBN
        success = self.scheduler.reserve_isbn(isbn2, "Special edition")
        assert success is True
        
        assignment = self.scheduler.assignments[isbn2]
        assert assignment.status == ISBNStatus.RESERVED.value
        assert "Special edition" in assignment.notes
        
        # 6. Generate report
        report = self.scheduler.get_isbn_availability_report()
        assert report['total_blocks'] == 1
        assert report['total_isbns'] == 100
        assert report['used_isbns'] == 3
        assert report['available_isbns'] == 97
        
        # Check status counts
        status_counts = report['assignments_by_status']
        assert status_counts['scheduled'] == 1  # isbn3
        assert status_counts['assigned'] == 1   # isbn1
        assert status_counts['reserved'] == 1   # isbn2
        
        # 7. Update assignment
        success = self.scheduler.update_assignment(
            isbn3, 
            book_title="Updated Book Three",
            notes="Updated for new edition"
        )
        assert success is True
        
        updated_assignment = self.scheduler.assignments[isbn3]
        assert updated_assignment.book_title == "Updated Book Three"
        assert updated_assignment.notes == "Updated for new edition"
    
    def test_cli_integration(self):
        """Test CLI tool integration"""
        cli_path = os.path.join(os.path.dirname(__file__), '..', 'tools', 'isbn_schedule_cli.py')
        
        # Test adding block via CLI
        result = subprocess.run([
            'uv', 'run', 'python', cli_path,
            '--schedule-file', self.temp_file.name,
            'add-block',
            '--prefix', '978',
            '--publisher-code', '654321',
            '--start', '2000',
            '--end', '2099'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Successfully added ISBN block" in result.stdout
        
        # Test scheduling via CLI
        result = subprocess.run([
            'uv', 'run', 'python', cli_path,
            '--schedule-file', self.temp_file.name,
            'schedule',
            '--title', 'CLI Test Book',
            '--book-id', 'cli_test_1',
            '--date', '2024-12-01'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Successfully scheduled ISBN assignment" in result.stdout
        
        # Test report via CLI
        result = subprocess.run([
            'uv', 'run', 'python', cli_path,
            '--schedule-file', self.temp_file.name,
            'report'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "ISBN Availability Report" in result.stdout
        assert "Total ISBNs: 100" in result.stdout
    
    def test_persistence_across_sessions(self):
        """Test data persistence across multiple sessions"""
        # Session 1: Create data
        scheduler1 = ISBNScheduler(schedule_file=self.temp_file.name)
        
        block_id = scheduler1.add_isbn_block("978", 3000, 3099, "789012")
        isbn = scheduler1.schedule_isbn_assignment(
            "Persistence Test", "persist_1", "2024-12-01"
        )
        
        assert block_id != ""
        assert isbn is not None
        
        # Session 2: Load and verify data
        scheduler2 = ISBNScheduler(schedule_file=self.temp_file.name)
        
        assert len(scheduler2.isbn_blocks) == 1
        assert len(scheduler2.assignments) == 1
        assert isbn in scheduler2.assignments
        
        # Session 2: Modify data
        success = scheduler2.assign_isbn_now(isbn)
        assert success is True
        
        # Session 3: Verify modifications
        scheduler3 = ISBNScheduler(schedule_file=self.temp_file.name)
        
        assignment = scheduler3.assignments[isbn]
        assert assignment.status == ISBNStatus.ASSIGNED.value
        assert assignment.assigned_date is not None
    
    def test_error_handling_integration(self):
        """Test error handling in integrated scenarios"""
        # Try to schedule without blocks
        isbn = self.scheduler.schedule_isbn_assignment(
            "No Block Test", "no_block_1", "2024-12-01"
        )
        assert isbn is None
        
        # Add block and schedule
        self.scheduler.add_isbn_block("978", 4000, 4099, "111111")  # 100 ISBNs
        
        future_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        isbn1 = self.scheduler.schedule_isbn_assignment("Book 1", "b1", future_date)
        isbn2 = self.scheduler.schedule_isbn_assignment("Book 2", "b2", future_date)
        
        assert isbn1 is not None
        assert isbn2 is not None
        
        # Schedule many books to exhaust the block
        for i in range(98):  # Use up remaining ISBNs
            self.scheduler.schedule_isbn_assignment(f"Book {i+3}", f"b{i+3}", future_date)
        
        # Try to schedule one more book (should fail - no more ISBNs)
        isbn_fail = self.scheduler.schedule_isbn_assignment("Book Fail", "b_fail", future_date)
        assert isbn_fail is None
        
        # Try to assign non-existent ISBN
        success = self.scheduler.assign_isbn_now("9999999999999")
        assert success is False
        
        # Try to update non-existent assignment
        success = self.scheduler.update_assignment("9999999999999", book_title="New Title")
        assert success is False