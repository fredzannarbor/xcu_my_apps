#!/usr/bin/env python3
"""
ISBN Ingestion Tool

This tool allows ingesting ISBNs from various sources into the ISBN database.
Supports Bowker spreadsheets, CSV files, and manual entry.

Usage:
    python tools/ingest_isbn.py --file path/to/bowker.xlsx --publisher nimble-books
    python tools/ingest_isbn.py --csv path/to/isbns.csv --publisher nimble-books
    python tools/ingest_isbn.py --manual --isbn 9781234567890 --publisher nimble-books
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.codexes.modules.distribution.isbn_database import ISBNDatabase, ISBNImportError, ISBN, ISBNStatus


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def ingest_from_bowker(db: ISBNDatabase, file_path: str, publisher_id: str) -> Dict[str, Any]:
    """
    Ingest ISBNs from a Bowker spreadsheet.
    
    Args:
        db: ISBN database instance
        file_path: Path to the Bowker spreadsheet
        publisher_id: Publisher identifier
        
    Returns:
        Import statistics dictionary
    """
    print(f"Ingesting ISBNs from Bowker spreadsheet: {file_path}")
    print(f"Publisher: {publisher_id}")
    
    try:
        stats = db.import_from_bowker(file_path, publisher_id)
        
        print("\n=== Import Results ===")
        print(f"Total rows processed: {stats['total']}")
        print(f"Successfully imported: {stats['imported']}")
        print(f"Skipped (invalid/duplicate): {stats['skipped']}")
        print(f"Errors: {stats['errors']}")
        print(f"\nStatus breakdown:")
        print(f"  Available: {stats['available']}")
        print(f"  Privately assigned: {stats['privately_assigned']}")
        print(f"  Publicly assigned: {stats['publicly_assigned']}")
        
        return stats
        
    except ISBNImportError as e:
        print(f"Error importing from Bowker spreadsheet: {e}")
        return {"error": str(e)}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"error": str(e)}


def ingest_from_csv(db: ISBNDatabase, file_path: str, publisher_id: str, 
                   isbn_column: str = "isbn", status_column: Optional[str] = None,
                   title_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Ingest ISBNs from a CSV file.
    
    Args:
        db: ISBN database instance
        file_path: Path to the CSV file
        publisher_id: Publisher identifier
        isbn_column: Name of the ISBN column
        status_column: Name of the status column (optional)
        title_column: Name of the title column (optional)
        
    Returns:
        Import statistics dictionary
    """
    print(f"Ingesting ISBNs from CSV file: {file_path}")
    print(f"Publisher: {publisher_id}")
    print(f"ISBN column: {isbn_column}")
    
    try:
        import pandas as pd
        
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Validate required columns
        if isbn_column not in df.columns:
            raise ValueError(f"ISBN column '{isbn_column}' not found in CSV. Available columns: {list(df.columns)}")
        
        stats = {
            "total": len(df),
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "available": 0,
            "privately_assigned": 0,
            "publicly_assigned": 0
        }
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Get ISBN
                isbn_value = str(row[isbn_column]).strip().replace("-", "").replace(" ", "")
                
                # Skip if ISBN is invalid
                if not isbn_value or not isbn_value.isdigit() or len(isbn_value) != 13:
                    print(f"Skipping invalid ISBN at row {index + 1}: {isbn_value}")
                    stats["skipped"] += 1
                    continue
                
                # Check if ISBN already exists
                if isbn_value in db.isbns:
                    print(f"Skipping duplicate ISBN at row {index + 1}: {isbn_value}")
                    stats["skipped"] += 1
                    continue
                
                # Determine status
                status = ISBNStatus.AVAILABLE
                if status_column and status_column in df.columns and pd.notna(row[status_column]):
                    status_value = str(row[status_column]).lower()
                    if any(s in status_value for s in ["public", "published"]):
                        status = ISBNStatus.PUBLICLY_ASSIGNED
                    elif any(s in status_value for s in ["private", "assigned"]):
                        status = ISBNStatus.PRIVATELY_ASSIGNED
                
                # Get title if available
                title = None
                if title_column and title_column in df.columns and pd.notna(row[title_column]):
                    title = str(row[title_column]).strip()
                
                # Create ISBN object
                isbn_obj = ISBN(
                    isbn=isbn_value,
                    publisher_id=publisher_id,
                    status=status,
                    title=title
                )
                
                # Add to database
                db.isbns[isbn_value] = isbn_obj
                stats["imported"] += 1
                
                # Update status counts
                if status == ISBNStatus.AVAILABLE:
                    stats["available"] += 1
                elif status == ISBNStatus.PRIVATELY_ASSIGNED:
                    stats["privately_assigned"] += 1
                elif status == ISBNStatus.PUBLICLY_ASSIGNED:
                    stats["publicly_assigned"] += 1
                
            except Exception as e:
                print(f"Error processing row {index + 1}: {e}")
                stats["errors"] += 1
        
        # Save the updated database
        db.save_database()
        
        print("\n=== Import Results ===")
        print(f"Total rows processed: {stats['total']}")
        print(f"Successfully imported: {stats['imported']}")
        print(f"Skipped (invalid/duplicate): {stats['skipped']}")
        print(f"Errors: {stats['errors']}")
        print(f"\nStatus breakdown:")
        print(f"  Available: {stats['available']}")
        print(f"  Privately assigned: {stats['privately_assigned']}")
        print(f"  Publicly assigned: {stats['publicly_assigned']}")
        
        return stats
        
    except Exception as e:
        print(f"Error importing from CSV: {e}")
        return {"error": str(e)}


def ingest_manual(db: ISBNDatabase, isbn: str, publisher_id: str, 
                 title: Optional[str] = None, status: str = "available",
                 format_type: Optional[str] = None, imprint: Optional[str] = None) -> Dict[str, Any]:
    """
    Manually ingest a single ISBN.
    
    Args:
        db: ISBN database instance
        isbn: ISBN to add
        publisher_id: Publisher identifier
        title: Book title (optional)
        status: ISBN status (available, assigned, published)
        format_type: Book format (optional)
        imprint: Imprint name (optional)
        
    Returns:
        Result dictionary
    """
    print(f"Manually ingesting ISBN: {isbn}")
    print(f"Publisher: {publisher_id}")
    print(f"Status: {status}")
    
    try:
        # Clean ISBN
        isbn_clean = isbn.replace("-", "").replace(" ", "")
        
        # Validate ISBN
        if not isbn_clean.isdigit() or len(isbn_clean) != 13:
            raise ValueError(f"Invalid ISBN format: {isbn}")
        
        # Check if ISBN already exists
        if isbn_clean in db.isbns:
            print(f"ISBN {isbn_clean} already exists in database")
            existing = db.get_isbn_details(isbn_clean)
            print(f"Existing details: {json.dumps(existing, indent=2, default=str)}")
            return {"error": "ISBN already exists"}
        
        # Parse status
        status_map = {
            "available": ISBNStatus.AVAILABLE,
            "assigned": ISBNStatus.PRIVATELY_ASSIGNED,
            "published": ISBNStatus.PUBLICLY_ASSIGNED
        }
        isbn_status = status_map.get(status.lower(), ISBNStatus.AVAILABLE)
        
        # Create ISBN object
        isbn_obj = ISBN(
            isbn=isbn_clean,
            publisher_id=publisher_id,
            status=isbn_status,
            title=title,
            format=format_type,
            imprint=imprint
        )
        
        # Add to database
        db.isbns[isbn_clean] = isbn_obj
        
        # Save the updated database
        db.save_database()
        
        print(f"Successfully added ISBN {isbn_clean} to database")
        
        return {
            "imported": 1,
            "isbn": isbn_clean,
            "status": isbn_status.value
        }
        
    except Exception as e:
        print(f"Error adding ISBN manually: {e}")
        return {"error": str(e)}


def show_database_stats(db: ISBNDatabase) -> None:
    """Show current database statistics."""
    stats = db.get_statistics()
    
    print("\n=== Current Database Statistics ===")
    print(f"Total ISBNs: {stats['total']}")
    print(f"Available: {stats['available']}")
    print(f"Privately assigned: {stats['privately_assigned']}")
    print(f"Publicly assigned: {stats['publicly_assigned']}")
    print(f"Publishers: {len(stats['publishers'])}")
    
    if stats['publishers']:
        print(f"Publisher list: {', '.join(stats['publishers'])}")
    
    if stats['formats']:
        print(f"\nFormats:")
        for format_name, count in stats['formats'].items():
            print(f"  {format_name}: {count}")


def validate_file_path(file_path: str) -> Path:
    """Validate that a file path exists and is readable."""
    path = Path(file_path)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"File does not exist: {file_path}")
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"Path is not a file: {file_path}")
    return path


def main():
    """Main function to parse arguments and run the ingestion."""
    parser = argparse.ArgumentParser(
        description="Ingest ISBNs into the ISBN database from various sources.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import from Bowker spreadsheet
  python tools/ingest_isbn.py --bowker path/to/bowker.xlsx --publisher nimble-books
  
  # Import from CSV file
  python tools/ingest_isbn.py --csv path/to/isbns.csv --publisher nimble-books
  
  # Import from CSV with custom column names
  python tools/ingest_isbn.py --csv path/to/isbns.csv --publisher nimble-books \\
    --isbn-column "ISBN-13" --status-column "Status" --title-column "Book Title"
  
  # Manually add a single ISBN
  python tools/ingest_isbn.py --manual --isbn 9781234567890 --publisher nimble-books \\
    --title "My Book" --status available
  
  # Show database statistics
  python tools/ingest_isbn.py --stats
        """
    )
    
    # Database options
    parser.add_argument(
        "--db-file",
        default="data/isbn_database.json",
        help="Path to the ISBN database JSON file (default: data/isbn_database.json)"
    )
    
    # Input source options (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--bowker",
        type=validate_file_path,
        help="Import from Bowker spreadsheet (Excel or CSV)"
    )
    source_group.add_argument(
        "--csv",
        type=validate_file_path,
        help="Import from CSV file"
    )
    source_group.add_argument(
        "--manual",
        action="store_true",
        help="Manually add a single ISBN"
    )
    source_group.add_argument(
        "--stats",
        action="store_true",
        help="Show current database statistics"
    )
    
    # Publisher (required for import operations)
    parser.add_argument(
        "--publisher",
        help="Publisher identifier (required for import operations)"
    )
    
    # CSV-specific options
    parser.add_argument(
        "--isbn-column",
        default="isbn",
        help="Name of the ISBN column in CSV (default: isbn)"
    )
    parser.add_argument(
        "--status-column",
        help="Name of the status column in CSV (optional)"
    )
    parser.add_argument(
        "--title-column",
        help="Name of the title column in CSV (optional)"
    )
    
    # Manual entry options
    parser.add_argument(
        "--isbn",
        help="ISBN to add manually (required with --manual)"
    )
    parser.add_argument(
        "--title",
        help="Book title for manual entry (optional)"
    )
    parser.add_argument(
        "--status",
        choices=["available", "assigned", "published"],
        default="available",
        help="ISBN status for manual entry (default: available)"
    )
    parser.add_argument(
        "--format",
        help="Book format for manual entry (optional)"
    )
    parser.add_argument(
        "--imprint",
        help="Imprint name for manual entry (optional)"
    )
    
    # General options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without actually importing"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Validate arguments
    if not args.stats and not args.publisher:
        parser.error("--publisher is required for import operations")
    
    if args.manual and not args.isbn:
        parser.error("--isbn is required with --manual")
    
    # Initialize database
    try:
        db = ISBNDatabase(args.db_file)
        print(f"Loaded ISBN database from: {args.db_file}")
    except Exception as e:
        print(f"Error loading ISBN database: {e}")
        sys.exit(1)
    
    # Show stats if requested
    if args.stats:
        show_database_stats(db)
        return
    
    # Perform the requested operation
    result = None
    
    if args.bowker:
        if args.dry_run:
            print("DRY RUN: Would import from Bowker spreadsheet")
            print(f"File: {args.bowker}")
            print(f"Publisher: {args.publisher}")
        else:
            result = ingest_from_bowker(db, str(args.bowker), args.publisher)
    
    elif args.csv:
        if args.dry_run:
            print("DRY RUN: Would import from CSV file")
            print(f"File: {args.csv}")
            print(f"Publisher: {args.publisher}")
            print(f"ISBN column: {args.isbn_column}")
        else:
            result = ingest_from_csv(
                db, str(args.csv), args.publisher,
                args.isbn_column, args.status_column, args.title_column
            )
    
    elif args.manual:
        if args.dry_run:
            print("DRY RUN: Would add ISBN manually")
            print(f"ISBN: {args.isbn}")
            print(f"Publisher: {args.publisher}")
            print(f"Title: {args.title}")
            print(f"Status: {args.status}")
        else:
            result = ingest_manual(
                db, args.isbn, args.publisher,
                args.title, args.status, args.format, args.imprint
            )
    
    # Show final statistics
    if not args.dry_run and result and "error" not in result:
        show_database_stats(db)
    
    # Exit with appropriate code
    if result and "error" in result:
        sys.exit(1)
    else:
        print("\nIngestion completed successfully!")


if __name__ == "__main__":
    main()