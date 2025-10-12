#!/usr/bin/env python3
"""
Example: Schedule Import with Manual ISBN Assignment

This example demonstrates how to import publishing schedules with manual ISBN assignments.
"""
import sys
import os
import tempfile
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.modules.distribution.isbn_scheduler import ISBNScheduler

def demonstrate_schedule_import():
    """Demonstrate schedule import functionality"""
    print("=" * 60)
    print("📚 Schedule Import with Manual ISBN Assignment Demo")
    print("=" * 60)
    
    # Initialize scheduler
    scheduler = ISBNScheduler()
    
    # Add an ISBN block for auto-assignments
    print("➕ Adding ISBN block for auto-assignments...")
    scheduler.add_isbn_block(
        prefix="978",
        start_number=8000,
        end_number=8099,
        publisher_code="555555",
        imprint_code="DEMO"
    )
    print("✅ ISBN block added")
    
    print("\n" + "=" * 40)
    print("STEP 1: Create Schedule with Mixed Assignments")
    print("=" * 40)
    
    # Create example CSV with manual and auto ISBNs
    csv_content = """title,book_id,scheduled_date,isbn,imprint,publisher,format,priority,notes
"Python for Beginners",python_101,2024-12-01,9780111111111,Demo Books,Demo Publisher,paperback,1,Manual ISBN - specific requirement
"Advanced Python",python_201,2024-12-15,,Demo Books,Demo Publisher,hardcover,2,Auto-assign ISBN
"Python Web Development",python_301,2025-01-01,9780222222222,Demo Books,Demo Publisher,paperback,1,Manual ISBN - pre-purchased
"Python Data Science",python_401,2025-01-15,,Demo Books,Demo Publisher,ebook,3,Auto-assign ISBN"""
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_file = f.name
    
    print("📄 Created schedule CSV with 4 books:")
    print("   - 2 with manual ISBNs (9780111111111, 9780222222222)")
    print("   - 2 with auto-assignment")
    
    print("\n" + "=" * 40)
    print("STEP 2: Import the Schedule")
    print("=" * 40)
    
    try:
        # Import the schedule
        results = scheduler.import_schedule_from_csv(csv_file)
        
        print(f"📊 Import Results:")
        print(f"   ✅ Processed: {results['processed']}")
        print(f"   🎯 Manual ISBNs: {results['assigned_manual']}")
        print(f"   🤖 Auto ISBNs: {results['assigned_auto']}")
        print(f"   🔄 Updated: {results['updated']}")
        print(f"   ❌ Errors: {len(results['errors'])}")
        
        if results['errors']:
            print("\n📋 Errors:")
            for error in results['errors']:
                print(f"      • {error}")
    
    finally:
        os.unlink(csv_file)
    
    print("\n" + "=" * 40)
    print("STEP 3: Verify Assignments")
    print("=" * 40)
    
    # Check manual assignments
    manual_books = ["python_101", "python_301"]
    expected_isbns = ["9780111111111", "9780222222222"]
    
    for book_id, expected_isbn in zip(manual_books, expected_isbns):
        actual_isbn = scheduler.get_isbn_by_book_id(book_id)
        if actual_isbn == expected_isbn:
            print(f"✅ {book_id}: Manual ISBN {actual_isbn} assigned correctly")
        else:
            print(f"❌ {book_id}: Expected {expected_isbn}, got {actual_isbn}")
    
    # Check auto assignments
    auto_books = ["python_201", "python_401"]
    for book_id in auto_books:
        actual_isbn = scheduler.get_isbn_by_book_id(book_id)
        if actual_isbn and actual_isbn.startswith("978555555"):
            print(f"✅ {book_id}: Auto-assigned ISBN {actual_isbn}")
        else:
            print(f"❌ {book_id}: Auto-assignment failed")
    
    print("\n" + "=" * 40)
    print("STEP 4: Demonstrate JSON Import")
    print("=" * 40)
    
    # Create JSON example
    json_data = [
        {
            "title": "JSON Manual Book",
            "book_id": "json_manual_1",
            "scheduled_date": "2024-12-01",
            "isbn": "9780333333333",
            "imprint": "JSON Books",
            "publisher": "JSON Publisher",
            "format": "paperback",
            "priority": 1,
            "notes": "Manual ISBN from JSON"
        },
        {
            "title": "JSON Auto Book",
            "book_id": "json_auto_1",
            "scheduled_date": "2024-12-15",
            "isbn": "",
            "imprint": "JSON Books",
            "publisher": "JSON Publisher",
            "format": "hardcover",
            "priority": 2,
            "notes": "Auto-assign from JSON"
        }
    ]
    
    # Write JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(json_data, f, indent=2)
        json_file = f.name
    
    try:
        results = scheduler.import_schedule_from_json(json_file)
        print(f"📊 JSON Import Results:")
        print(f"   ✅ Processed: {results['processed']}")
        print(f"   🎯 Manual ISBNs: {results['assigned_manual']}")
        print(f"   🤖 Auto ISBNs: {results['assigned_auto']}")
        
        # Verify JSON assignments
        json_manual_isbn = scheduler.get_isbn_by_book_id("json_manual_1")
        json_auto_isbn = scheduler.get_isbn_by_book_id("json_auto_1")
        
        if json_manual_isbn == "9780333333333":
            print(f"✅ JSON manual assignment: {json_manual_isbn}")
        if json_auto_isbn and json_auto_isbn.startswith("978555555"):
            print(f"✅ JSON auto assignment: {json_auto_isbn}")
    
    finally:
        os.unlink(json_file)
    
    print("\n" + "=" * 40)
    print("STEP 5: Generate Final Report")
    print("=" * 40)
    
    report = scheduler.get_isbn_availability_report()
    print(f"📊 Final Statistics:")
    print(f"   Total ISBNs: {report['total_isbns']}")
    print(f"   Used ISBNs: {report['used_isbns']}")
    print(f"   Available ISBNs: {report['available_isbns']}")
    print(f"   Total Assignments: {sum(report['assignments_by_status'].values())}")
    
    print("\n" + "=" * 60)
    print("✅ Schedule Import Demonstration Complete!")
    print("=" * 60)
    
    print("\n💡 Key Features Demonstrated:")
    print("   ✅ Manual ISBN assignment from CSV/JSON")
    print("   ✅ Auto-assignment for books without ISBNs")
    print("   ✅ Mixed manual/auto in same import")
    print("   ✅ Error handling and reporting")
    print("   ✅ Support for both CSV and JSON formats")
    print("   ✅ Validation and duplicate prevention")

if __name__ == "__main__":
    demonstrate_schedule_import()