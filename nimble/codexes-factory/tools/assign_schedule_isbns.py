#!/usr/bin/env python3
"""
Schedule ISBN Assignment Tool

This tool provides command-line functionality for assigning and managing ISBNs in publishing schedules.

Usage:
    # Assign ISBNs to all books in a schedule
    python tools/assign_schedule_isbns.py --schedule imprints/xynapse_traces/schedule.json --publisher nimble-books
    
    # Dry run to see what would be assigned
    python tools/assign_schedule_isbns.py --schedule imprints/xynapse_traces/schedule.json --publisher nimble-books --dry-run
    
    # Validate ISBNs in a schedule
    python tools/assign_schedule_isbns.py --validate --schedule imprints/xynapse_traces/schedule.json
    
    # Generate ISBN report
    python tools/assign_schedule_isbns.py --report --schedule imprints/xynapse_traces/schedule.json --output isbn_report.json
    
    # Bulk assign specific ISBNs
    python tools/assign_schedule_isbns.py --bulk-assign assignments.json --schedule imprints/xynapse_traces/schedule.json
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.codexes.modules.distribution.schedule_isbn_manager import ScheduleISBNManager


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def assign_isbns_command(args) -> None:
    """Handle the assign ISBNs command."""
    print(f"{'DRY RUN: ' if args.dry_run else ''}Assigning ISBNs to schedule: {args.schedule}")
    print(f"Publisher: {args.publisher}")
    print(f"Format: {args.format}")
    
    manager = ScheduleISBNManager(args.isbn_db)
    
    # Check available ISBNs
    available_count = manager.get_available_isbn_count(args.publisher)
    print(f"Available ISBNs for {args.publisher}: {available_count}")
    
    if available_count == 0 and not args.dry_run:
        print("❌ No available ISBNs found for this publisher!")
        print("Please add ISBNs to the database using tools/ingest_isbn.py")
        sys.exit(1)
    
    # Perform assignment
    results = manager.assign_isbns_to_schedule(
        schedule_path=args.schedule,
        publisher_id=args.publisher,
        output_path=args.output,
        format_type=args.format,
        dry_run=args.dry_run
    )
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        sys.exit(1)
    
    # Display results
    print("\n=== Assignment Results ===")
    print(f"Total books processed: {results['total_books']}")
    print(f"ISBNs assigned: {results['assigned']}")
    print(f"Already had ISBNs: {results['already_assigned']}")
    print(f"Failed assignments: {results['failed']}")
    
    if results['assignments']:
        print(f"\n=== {'Would Assign' if args.dry_run else 'Assignments'} ===")
        for assignment in results['assignments']:
            status_icon = "📖" if assignment['status'] == 'newly_assigned' else "✅"
            print(f"{status_icon} {assignment['title']} ({assignment['month']}) -> {assignment['isbn']}")
    
    if results['errors']:
        print(f"\n=== Errors ===")
        for error in results['errors']:
            print(f"❌ {error['title']} ({error['month']}): {error['error']}")
    
    if not args.dry_run and results['assigned'] > 0:
        print(f"\n✅ Updated schedule saved to: {args.output or args.schedule}")


def validate_command(args) -> None:
    """Handle the validate ISBNs command."""
    print(f"Validating ISBNs in schedule: {args.schedule}")
    
    manager = ScheduleISBNManager(args.isbn_db)
    results = manager.validate_schedule_isbns(args.schedule)
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        sys.exit(1)
    
    # Display validation results
    print("\n=== Validation Results ===")
    print(f"Total books: {results['total_books']}")
    print(f"Books with ISBNs: {results['books_with_isbn']}")
    print(f"Valid ISBNs: {results['valid_isbns']}")
    print(f"Invalid ISBNs: {results['invalid_isbns']}")
    print(f"Duplicate ISBNs: {results['duplicate_isbns']}")
    
    # Show coverage percentage
    if results['total_books'] > 0:
        coverage = (results['books_with_isbn'] / results['total_books']) * 100
        print(f"ISBN Coverage: {coverage:.1f}%")
    
    # Show validation details
    if args.verbose:
        print(f"\n=== Validation Details ===")
        for detail in results['validation_details']:
            status_icons = {
                'valid': '✅',
                'no_isbn': '📝',
                'invalid_format': '❌',
                'duplicate': '⚠️',
                'not_in_database': '🔍'
            }
            icon = status_icons.get(detail['status'], '❓')
            print(f"{icon} {detail['title']} ({detail.get('month', 'Unknown')}): {detail['message']}")
            if 'isbn' in detail:
                print(f"    ISBN: {detail['isbn']}")
    
    # Show duplicates if any
    if results['duplicate_isbns'] > 0:
        print(f"\n=== Duplicate ISBNs ===")
        duplicates = {}
        for detail in results['validation_details']:
            if detail['status'] == 'duplicate':
                isbn = detail['isbn']
                if isbn not in duplicates:
                    duplicates[isbn] = []
                duplicates[isbn].append(f"{detail['title']} ({detail['month']})")
        
        for isbn, books in duplicates.items():
            print(f"📚 ISBN {isbn} used by:")
            for book in books:
                print(f"    - {book}")


def report_command(args) -> None:
    """Handle the generate report command."""
    print(f"Generating ISBN report for schedule: {args.schedule}")
    
    manager = ScheduleISBNManager(args.isbn_db)
    report = manager.generate_isbn_report(args.schedule, args.output)
    
    if 'error' in report:
        print(f"❌ Error: {report['error']}")
        sys.exit(1)
    
    # Display report summary
    summary = report['summary']
    print("\n=== ISBN Report Summary ===")
    print(f"Total books: {summary['total_books']}")
    print(f"Books with ISBNs: {summary['books_with_isbn']}")
    print(f"Books without ISBNs: {summary['books_without_isbn']}")
    print(f"Valid ISBNs: {summary['valid_isbns']}")
    print(f"Invalid ISBNs: {summary['invalid_isbns']}")
    print(f"Duplicate ISBNs: {summary['duplicate_isbns']}")
    print(f"ISBN Coverage: {summary['isbn_coverage_percentage']}%")
    
    # Show recommendations
    if report['recommendations']:
        print(f"\n=== Recommendations ===")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"{i}. {recommendation}")
    
    if args.output:
        print(f"\n✅ Detailed report saved to: {args.output}")
    else:
        print(f"\n📊 Use --output to save detailed report to file")


def bulk_assign_command(args) -> None:
    """Handle the bulk assign command."""
    print(f"Bulk assigning ISBNs from: {args.bulk_assign}")
    print(f"Schedule: {args.schedule}")
    
    # Load assignments file
    try:
        with open(args.bulk_assign, 'r', encoding='utf-8') as f:
            assignments = json.load(f)
    except Exception as e:
        print(f"❌ Error loading assignments file: {e}")
        sys.exit(1)
    
    # Validate assignments format
    if not isinstance(assignments, list):
        print("❌ Assignments file must contain a JSON array")
        sys.exit(1)
    
    for i, assignment in enumerate(assignments):
        if not isinstance(assignment, dict) or 'title' not in assignment or 'isbn' not in assignment:
            print(f"❌ Invalid assignment at index {i}: must have 'title' and 'isbn' fields")
            sys.exit(1)
    
    print(f"Loaded {len(assignments)} ISBN assignments")
    
    # Perform bulk assignment
    manager = ScheduleISBNManager(args.isbn_db)
    results = manager.bulk_assign_isbns(assignments, args.schedule, args.output)
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        sys.exit(1)
    
    # Display results
    print("\n=== Bulk Assignment Results ===")
    print(f"Total assignments: {results['total_assignments']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Not found: {results['not_found']}")
    
    # Show details
    if args.verbose:
        print(f"\n=== Assignment Details ===")
        for detail in results['details']:
            status_icons = {
                'assigned': '✅',
                'invalid_format': '❌',
                'not_found': '🔍'
            }
            icon = status_icons.get(detail['status'], '❓')
            print(f"{icon} {detail['title']}: {detail.get('isbn', 'N/A')}")
            if 'error' in detail:
                print(f"    Error: {detail['error']}")
    
    if results['successful'] > 0:
        print(f"\n✅ Updated schedule saved to: {args.output or args.schedule}")


def show_stats_command(args) -> None:
    """Handle the show statistics command."""
    print("ISBN Database Statistics")
    
    manager = ScheduleISBNManager(args.isbn_db)
    stats = manager.isbn_db.get_statistics()
    
    print(f"\n=== Database Overview ===")
    print(f"Total ISBNs: {stats['total']}")
    print(f"Available: {stats['available']}")
    print(f"Privately assigned: {stats['privately_assigned']}")
    print(f"Publicly assigned: {stats['publicly_assigned']}")
    print(f"Publishers: {len(stats['publishers'])}")
    
    if stats['publishers']:
        print(f"\n=== Publisher Breakdown ===")
        for publisher in stats['publishers']:
            available = manager.get_available_isbn_count(publisher)
            print(f"  {publisher}: {available} available ISBNs")


def validate_file_path(file_path: str) -> Path:
    """Validate that a file path exists and is readable."""
    path = Path(file_path)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"File does not exist: {file_path}")
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"Path is not a file: {file_path}")
    return path


def main():
    """Main function to parse arguments and run the appropriate command."""
    parser = argparse.ArgumentParser(
        description="Assign and manage ISBNs in publishing schedules.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Assign ISBNs to all books in a schedule
  python tools/assign_schedule_isbns.py --schedule imprints/xynapse_traces/schedule.json --publisher nimble-books
  
  # Dry run to see what would be assigned
  python tools/assign_schedule_isbns.py --schedule imprints/xynapse_traces/schedule.json --publisher nimble-books --dry-run
  
  # Validate ISBNs in a schedule
  python tools/assign_schedule_isbns.py --validate --schedule imprints/xynapse_traces/schedule.json
  
  # Generate detailed ISBN report
  python tools/assign_schedule_isbns.py --report --schedule imprints/xynapse_traces/schedule.json --output isbn_report.json
  
  # Bulk assign specific ISBNs from file
  python tools/assign_schedule_isbns.py --bulk-assign assignments.json --schedule imprints/xynapse_traces/schedule.json
  
  # Show ISBN database statistics
  python tools/assign_schedule_isbns.py --stats
        """
    )
    
    # Database options
    parser.add_argument(
        "--isbn-db",
        default="data/isbn_database.json",
        help="Path to the ISBN database JSON file (default: data/isbn_database.json)"
    )
    
    # Schedule file (required for most operations)
    parser.add_argument(
        "--schedule",
        type=validate_file_path,
        help="Path to the publishing schedule JSON file"
    )
    
    # Operation mode (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--assign",
        action="store_true",
        help="Assign ISBNs to books in the schedule (default operation)"
    )
    mode_group.add_argument(
        "--validate",
        action="store_true",
        help="Validate ISBNs in the schedule"
    )
    mode_group.add_argument(
        "--report",
        action="store_true",
        help="Generate ISBN usage report"
    )
    mode_group.add_argument(
        "--bulk-assign",
        type=validate_file_path,
        help="Bulk assign ISBNs from JSON file"
    )
    mode_group.add_argument(
        "--stats",
        action="store_true",
        help="Show ISBN database statistics"
    )
    
    # Assignment options
    parser.add_argument(
        "--publisher",
        help="Publisher identifier (required for --assign)"
    )
    parser.add_argument(
        "--format",
        choices=["paperback", "hardcover", "ebook"],
        default="paperback",
        help="Book format for ISBN assignment (default: paperback)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be assigned without actually assigning"
    )
    
    # Output options
    parser.add_argument(
        "--output",
        help="Output file path (for updated schedule or report)"
    )
    
    # General options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Validate arguments
    if args.assign and not args.publisher:
        parser.error("--publisher is required with --assign")
    
    if (args.assign or args.validate or args.report or args.bulk_assign) and not args.schedule:
        parser.error("--schedule is required for this operation")
    
    # Set default operation to assign if no specific mode is chosen
    if not any([args.validate, args.report, args.bulk_assign, args.stats]):
        args.assign = True
    
    # Execute the appropriate command
    try:
        if args.assign:
            assign_isbns_command(args)
        elif args.validate:
            validate_command(args)
        elif args.report:
            report_command(args)
        elif args.bulk_assign:
            bulk_assign_command(args)
        elif args.stats:
            show_stats_command(args)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()