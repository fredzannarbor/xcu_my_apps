#!/usr/bin/env python3
"""
Example: ISBN Scheduler Integration for Book Rebuilds

This example shows how to integrate the ISBN scheduler into your book pipeline
to handle rebuilds properly by reusing existing ISBNs.
"""
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.modules.distribution.isbn_scheduler import ISBNScheduler

def build_book_with_isbn(book_id: str, book_title: str, is_rebuild: bool = False):
    """
    Example function showing how to integrate ISBN assignment into book pipeline
    """
    print(f"{'🔄 Rebuilding' if is_rebuild else '📚 Building'} book: {book_title} (ID: {book_id})")
    
    # Initialize ISBN scheduler
    scheduler = ISBNScheduler()
    
    # Get existing ISBN or assign new one - perfect for rebuilds!
    isbn = scheduler.get_or_assign_isbn(
        book_id=book_id,
        book_title=book_title,
        scheduled_date=datetime.now().strftime('%Y-%m-%d'),
        format="paperback",
        notes=f"{'Rebuild' if is_rebuild else 'Initial build'} - {datetime.now().isoformat()}"
    )
    
    if isbn:
        # Check if this was an existing ISBN (rebuild) or new assignment
        assignment = scheduler.get_assignment_by_book_id(book_id)
        is_existing = assignment.assigned_date is not None
        
        print(f"📖 {'Reusing existing' if is_existing else 'Assigned new'} ISBN: {isbn}")
        print(f"📊 Status: {assignment.status.replace('_', ' ').title()}")
        
        # Mark as assigned if it's ready for publication
        if not is_existing:
            scheduler.assign_isbn_now(isbn)
            print(f"✅ ISBN {isbn} marked as assigned and ready for publication")
        
        # Here you would continue with your book generation process
        print(f"🏗️  Continuing with book generation using ISBN {isbn}...")
        
        return isbn
    else:
        print("❌ Failed to get ISBN - no blocks available")
        return None

def demonstrate_rebuild_workflow():
    """Demonstrate the complete rebuild workflow"""
    print("=" * 60)
    print("📚 ISBN Scheduler Rebuild Workflow Demonstration")
    print("=" * 60)
    
    # First, ensure we have an ISBN block
    scheduler = ISBNScheduler()
    
    # Add a test block if none exists
    if not scheduler.isbn_blocks:
        print("➕ Adding test ISBN block...")
        scheduler.add_isbn_block(
            prefix="978",
            start_number=5000,
            end_number=5099,
            publisher_code="999999",
            imprint_code="TEST"
        )
        print("✅ Test ISBN block added")
    
    print("\n" + "=" * 40)
    print("STEP 1: Initial Book Build")
    print("=" * 40)
    
    # Initial build
    isbn1 = build_book_with_isbn("example_book_v1", "The Complete Guide to Publishing", is_rebuild=False)
    
    print("\n" + "=" * 40)
    print("STEP 2: Book Rebuild (Same Book ID)")
    print("=" * 40)
    
    # Rebuild - should reuse the same ISBN
    isbn2 = build_book_with_isbn("example_book_v1", "The Complete Guide to Publishing (Revised)", is_rebuild=True)
    
    print("\n" + "=" * 40)
    print("STEP 3: Verification")
    print("=" * 40)
    
    if isbn1 == isbn2:
        print(f"✅ SUCCESS: Both builds used the same ISBN: {isbn1}")
        print("🎉 Rebuild workflow working correctly!")
    else:
        print(f"❌ ERROR: Different ISBNs used - {isbn1} vs {isbn2}")
    
    print("\n" + "=" * 40)
    print("STEP 4: Lookup Existing ISBN")
    print("=" * 40)
    
    # Demonstrate lookup functionality
    existing_isbn = scheduler.get_isbn_by_book_id("example_book_v1")
    if existing_isbn:
        assignment = scheduler.get_assignment_by_book_id("example_book_v1")
        print(f"🔍 Found existing ISBN for 'example_book_v1': {existing_isbn}")
        print(f"📖 Title: {assignment.book_title}")
        print(f"📊 Status: {assignment.status}")
        print(f"📅 Last Updated: {assignment.scheduled_date}")
    
    print("\n" + "=" * 60)
    print("✅ Demonstration Complete!")
    print("=" * 60)

if __name__ == "__main__":
    demonstrate_rebuild_workflow()