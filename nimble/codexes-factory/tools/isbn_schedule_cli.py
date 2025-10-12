#!/usr/bin/env python3
"""
ISBN Schedule CLI - Command line interface for managing ISBN assignments.
"""
import argparse
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from codexes.modules.distribution.isbn_scheduler import ISBNScheduler, ISBNStatus
except ImportError:
    print("Error: Could not import ISBN scheduler. Please check your Python path.")
    sys.exit(1)

def get_or_assign_isbn(scheduler: ISBNScheduler, args):
    """Get existing ISBN or assign new one for book ID"""
    isbn = scheduler.get_or_assign_isbn(
        book_id=args.book_id,
        book_title=args.title,
        scheduled_date=args.date,
        imprint=args.imprint or "",
        publisher=args.publisher or "",
        format=args.format,
        priority=args.priority,
        notes=args.notes or ""
    )
    
    if isbn:
        assignment = scheduler.get_assignment_by_book_id(args.book_id)
        is_existing = assignment.assigned_date is not None or assignment.status != ISBNStatus.SCHEDULED.value
        
        print(f"✅ {'Found existing' if is_existing else 'Assigned new'} ISBN for book ID '{args.book_id}':")
        print(f"   ISBN: {isbn}")
        print(f"   Title: {args.title}")
        print(f"   Status: {assignment.status}")
        print(f"   Date: {args.date}")
    else:
        print(f"❌ Failed to get or assign ISBN for book ID '{args.book_id}'")
        print("   No available ISBNs found. Add an ISBN block first.")
        sys.exit(1)

def lookup_isbn(scheduler: ISBNScheduler, args):
    """Look up ISBN by book ID"""
    isbn = scheduler.get_isbn_by_book_id(args.book_id)
    if isbn:
        assignment = scheduler.get_assignment_by_book_id(args.book_id)
        print(f"✅ Found ISBN for book ID '{args.book_id}':")
        print(f"   ISBN: {isbn}")
        print(f"   Title: {assignment.book_title}")
        print(f"   Status: {assignment.status}")
        print(f"   Scheduled Date: {assignment.scheduled_date}")
        if assignment.assigned_date:
            print(f"   Assigned Date: {assignment.assigned_date}")
    else:
        print(f"❌ No ISBN found for book ID '{args.book_id}'")
        sys.exit(1)

def import_schedule(scheduler: ISBNScheduler, args):
    """Import schedule from CSV or JSON file"""
    file_path = args.file
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    # Determine file type
    if file_path.lower().endswith('.csv'):
        results = scheduler.import_schedule_from_csv(file_path)
    elif file_path.lower().endswith('.json'):
        results = scheduler.import_schedule_from_json(file_path)
    else:
        print("❌ Unsupported file format. Use .csv or .json files.")
        sys.exit(1)
    
    # Display results
    print(f"📊 Schedule Import Results:")
    print(f"   ✅ Processed: {results['processed']}")
    print(f"   🎯 Manual ISBNs: {results['assigned_manual']}")
    print(f"   🤖 Auto ISBNs: {results['assigned_auto']}")
    print(f"   🔄 Updated: {results['updated']}")
    
    if results['errors']:
        print(f"   ❌ Errors: {len(results['errors'])}")
        if args.show_errors:
            print("\n📋 Error Details:")
            for error in results['errors']:
                print(f"      • {error}")
    
    if results['processed'] > 0:
        print(f"\n🎉 Successfully imported {results['processed']} book assignments!")
    else:
        print("\n❌ No books were successfully imported.")
        sys.exit(1)

def export_template(scheduler: ISBNScheduler, args):
    """Export schedule template file"""
    output_file = args.output
    
    if args.format == 'csv':
        success = scheduler.export_schedule_template_csv(output_file)
    elif args.format == 'json':
        success = scheduler.export_schedule_template_json(output_file)
    else:
        print("❌ Invalid format. Use 'csv' or 'json'.")
        sys.exit(1)
    
    if success:
        print(f"✅ Template exported to: {output_file}")
        print(f"📝 Edit the file to add your books, then import with:")
        print(f"   python isbn_schedule_cli.py import-schedule --file {output_file}")
    else:
        print("❌ Failed to export template")
        sys.exit(1)

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="ISBN Schedule Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export a template for manual ISBN assignment
  python isbn_schedule_cli.py export-template --format csv --output my_schedule.csv
  
  # Import schedule with manual ISBNs
  python isbn_schedule_cli.py import-schedule --file my_schedule.csv
  
  # Get existing or assign new ISBN (perfect for rebuilds)
  python isbn_schedule_cli.py get-or-assign --book-id book_1 --title "My Book" --date 2024-12-01
  
  # Look up existing ISBN
  python isbn_schedule_cli.py lookup --book-id book_1
        """
    )
    
    parser.add_argument('--schedule-file', default='configs/isbn_schedule.json', help='Path to ISBN schedule file')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Get or assign command
    get_or_assign_parser = subparsers.add_parser('get-or-assign', help='Get existing ISBN or assign new one for book ID')
    get_or_assign_parser.add_argument('--book-id', required=True, help='Book ID')
    get_or_assign_parser.add_argument('--title', required=True, help='Book title')
    get_or_assign_parser.add_argument('--date', required=True, help='Scheduled date (YYYY-MM-DD)')
    get_or_assign_parser.add_argument('--imprint', help='Imprint name')
    get_or_assign_parser.add_argument('--publisher', help='Publisher name')
    get_or_assign_parser.add_argument('--format', choices=['paperback', 'hardcover', 'ebook'], default='paperback')
    get_or_assign_parser.add_argument('--priority', type=int, choices=[1, 2, 3], default=1)
    get_or_assign_parser.add_argument('--notes', help='Additional notes')
    
    # Lookup command
    lookup_parser = subparsers.add_parser('lookup', help='Look up ISBN by book ID')
    lookup_parser.add_argument('--book-id', required=True, help='Book ID to look up')
    
    # Import schedule command
    import_parser = subparsers.add_parser('import-schedule', help='Import schedule from CSV or JSON file')
    import_parser.add_argument('--file', required=True, help='Path to CSV or JSON schedule file')
    import_parser.add_argument('--show-errors', action='store_true', help='Show detailed error messages')
    
    # Export template command
    export_parser = subparsers.add_parser('export-template', help='Export schedule template file')
    export_parser.add_argument('--format', choices=['csv', 'json'], required=True, help='Template format')
    export_parser.add_argument('--output', required=True, help='Output file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    scheduler = ISBNScheduler(schedule_file=args.schedule_file)
    
    try:
        if args.command == 'get-or-assign':
            get_or_assign_isbn(scheduler, args)
        elif args.command == 'lookup':
            lookup_isbn(scheduler, args)
        elif args.command == 'import-schedule':
            import_schedule(scheduler, args)
        elif args.command == 'export-template':
            export_template(scheduler, args)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()d
ef convert_schedule(scheduler: ISBNScheduler, args):
    """Convert schedule file between formats"""
    from tools.schedule_converter import ScheduleConverter
    
    converter = ScheduleConverter()
    
    if not os.path.exists(args.input):
        print(f"❌ Input file not found: {args.input}")
        sys.exit(1)
    
    # Determine conversion direction
    input_ext = args.input.lower().split('.')[-1]
    output_ext = args.output.lower().split('.')[-1]
    
    if input_ext == 'csv' and output_ext == 'json':
        success = converter.csv_to_json(args.input, args.output, pretty=not args.compact)
    elif input_ext == 'json' and output_ext == 'csv':
        success = converter.json_to_csv(args.input, args.output)
    else:
        print("❌ Unsupported conversion. Supported: CSV ↔ JSON")
        sys.exit(1)
    
    if success:
        print(f"✅ Successfully converted {args.input} to {args.output}")
    else:
        print("❌ Conversion failed")
        sys.exit(1)

def validate_schedule_file(scheduler: ISBNScheduler, args):
    """Validate schedule file"""
    from tools.schedule_converter import ScheduleConverter
    
    converter = ScheduleConverter()
    
    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        sys.exit(1)
    
    stats = converter.validate_schedule_file(args.file)
    
    print(f"📊 Validation Results for {args.file}:")
    print(f"   📚 Total books: {stats['total_books']}")
    print(f"   ✅ Valid books: {stats['valid_books']}")
    print(f"   🎯 Manual ISBNs: {stats['manual_isbns']}")
    print(f"   🤖 Auto ISBNs: {stats['auto_isbns']}")
    print(f"   ❌ Missing required fields: {stats['missing_required']}")
    print(f"   📖 Invalid ISBNs: {stats['invalid_isbns']}")
    
    if stats['errors']:
        print(f"   🚨 Total errors: {len(stats['errors'])}")
        if args.show_errors:
            print("\n📋 Error Details:")
            for error in stats['errors']:
                print(f"      • {error}")
    
    if stats['valid_books'] == stats['total_books'] and not stats['errors']:
        print("\n🎉 File is valid and ready for import!")
    else:
        print(f"\n⚠️  File has issues that should be addressed before import")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="ISBN Schedule Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export a template for manual ISBN assignment
  python isbn_schedule_cli.py export-template --format csv --output my_schedule.csv
  
  # Import schedule with manual ISBNs
  python isbn_schedule_cli.py import-schedule --file my_schedule.csv
  
  # Convert between formats
  python isbn_schedule_cli.py convert --input schedule.csv --output schedule.json
  
  # Validate schedule file
  python isbn_schedule_cli.py validate --file schedule.csv --show-errors
  
  # Get existing or assign new ISBN (perfect for rebuilds)
  python isbn_schedule_cli.py get-or-assign --book-id book_1 --title "My Book" --date 2024-12-01
  
  # Look up existing ISBN
  python isbn_schedule_cli.py lookup --book-id book_1
        """
    )
    
    parser.add_argument('--schedule-file', default='configs/isbn_schedule.json', help='Path to ISBN schedule file')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Get or assign command
    get_or_assign_parser = subparsers.add_parser('get-or-assign', help='Get existing ISBN or assign new one for book ID')
    get_or_assign_parser.add_argument('--book-id', required=True, help='Book ID')
    get_or_assign_parser.add_argument('--title', required=True, help='Book title')
    get_or_assign_parser.add_argument('--date', required=True, help='Scheduled date (YYYY-MM-DD)')
    get_or_assign_parser.add_argument('--imprint', help='Imprint name')
    get_or_assign_parser.add_argument('--publisher', help='Publisher name')
    get_or_assign_parser.add_argument('--format', choices=['paperback', 'hardcover', 'ebook'], default='paperback')
    get_or_assign_parser.add_argument('--priority', type=int, choices=[1, 2, 3], default=1)
    get_or_assign_parser.add_argument('--notes', help='Additional notes')
    
    # Lookup command
    lookup_parser = subparsers.add_parser('lookup', help='Look up ISBN by book ID')
    lookup_parser.add_argument('--book-id', required=True, help='Book ID to look up')
    
    # Import schedule command
    import_parser = subparsers.add_parser('import-schedule', help='Import schedule from CSV or JSON file')
    import_parser.add_argument('--file', required=True, help='Path to CSV or JSON schedule file')
    import_parser.add_argument('--show-errors', action='store_true', help='Show detailed error messages')
    
    # Export template command
    export_parser = subparsers.add_parser('export-template', help='Export schedule template file')
    export_parser.add_argument('--format', choices=['csv', 'json'], required=True, help='Template format')
    export_parser.add_argument('--output', required=True, help='Output file path')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert schedule file between CSV and JSON formats')
    convert_parser.add_argument('--input', required=True, help='Input file path')
    convert_parser.add_argument('--output', required=True, help='Output file path')
    convert_parser.add_argument('--compact', action='store_true', help='Compact JSON output (no pretty printing)')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate schedule file')
    validate_parser.add_argument('--file', required=True, help='Schedule file to validate')
    validate_parser.add_argument('--show-errors', action='store_true', help='Show detailed error messages')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    scheduler = ISBNScheduler(schedule_file=args.schedule_file)
    
    try:
        if args.command == 'get-or-assign':
            get_or_assign_isbn(scheduler, args)
        elif args.command == 'lookup':
            lookup_isbn(scheduler, args)
        elif args.command == 'import-schedule':
            import_schedule(scheduler, args)
        elif args.command == 'export-template':
            export_template(scheduler, args)
        elif args.command == 'convert':
            convert_schedule(scheduler, args)
        elif args.command == 'validate':
            validate_schedule_file(scheduler, args)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)