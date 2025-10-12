#!/usr/bin/env python3
"""
Corrected script to import ISBNs from Bowker spreadsheets with proper status logic.

Rule: ISBNs with Title, Format, and Status non-empty are publicly assigned.
"""

import os
import sys
import logging
import argparse
import pandas as pd
import uuid

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.codexes.modules.distribution.isbn_database import ISBNDatabase, ISBN, ISBNStatus, ISBNImportError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/isbn_import.log')
    ]
)

logger = logging.getLogger(__name__)


def import_bowker_corrected(db: ISBNDatabase, file_path: str, publisher_id: str, append_unique: bool = False) -> dict:
    """
    Import ISBNs from a Bowker spreadsheet with corrected status logic.

    Args:
        db: ISBNDatabase instance
        file_path: Path to the Bowker spreadsheet
        publisher_id: ID of the publisher
        append_unique: If True, only import ISBNs not already in the database

    Returns:
        Dictionary with import statistics
    """
    try:
        # Read the CSV file
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith((".xlsx", ".xls")):
            xl = pd.ExcelFile(file_path)
            sheet_name = next((s for s in xl.sheet_names if "isbn" in s.lower()), xl.sheet_names[0])
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            raise ISBNImportError(f"Unsupported file format: {file_path}")

        logger.info(f"Found {len(df)} rows in {file_path}")
        logger.info(f"Columns: {list(df.columns)}")

        # Find columns (case-insensitive)
        isbn_col = None
        title_col = None
        format_col = None
        status_col = None
        imprint_col = None
        pub_date_col = None
        assign_date_col = None
        notes_col = None

        for col in df.columns:
            col_lower = col.lower()
            if "isbn" in col_lower and not isbn_col:
                isbn_col = col
            elif "title" in col_lower and not title_col:
                title_col = col
            elif any(f in col_lower for f in ["format", "binding", "type"]) and not format_col:
                format_col = col
            elif "status" in col_lower and not status_col:
                status_col = col
            elif "imprint" in col_lower and not imprint_col:
                imprint_col = col
            elif any(p in col_lower for p in ["pub date", "publication date", "pub_date"]) and not pub_date_col:
                pub_date_col = col
            elif any(a in col_lower for a in ["assign date", "assignment date", "assign_date"]) and not assign_date_col:
                assign_date_col = col
            elif any(n in col_lower for n in ["notes", "note", "comments"]) and not notes_col:
                notes_col = col

        if not isbn_col:
            raise ISBNImportError("No ISBN column found in the spreadsheet")

        logger.info(f"Using columns - ISBN: {isbn_col}, Title: {title_col}, Format: {format_col}, Status: {status_col}")

        # Import statistics
        stats = {
            "total": len(df),
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "available": 0,
            "privately_assigned": 0,
            "publicly_assigned": 0,
            "duplicates": 0
        }

        # Process each row
        for idx, row in df.iterrows():
            try:
                # Get ISBN
                isbn_value = str(row[isbn_col]).strip().replace("-", "").replace(" ", "")

                # Skip if ISBN is invalid
                if not isbn_value or isbn_value == 'nan' or not isbn_value.isdigit() or len(isbn_value) != 13:
                    logger.debug(f"Skipping invalid ISBN: {isbn_value}")
                    stats["skipped"] += 1
                    continue

                # Check for duplicate if append_unique is True
                if append_unique and isbn_value in db.isbns:
                    logger.debug(f"Skipping duplicate ISBN: {isbn_value}")
                    stats["duplicates"] += 1
                    stats["skipped"] += 1
                    continue

                # Get other fields
                title = row[title_col] if title_col and pd.notna(row[title_col]) else None
                format_value = row[format_col] if format_col and pd.notna(row[format_col]) else None
                status_value = row[status_col] if status_col and pd.notna(row[status_col]) else None
                imprint = row[imprint_col] if imprint_col and pd.notna(row[imprint_col]) else None
                pub_date = row[pub_date_col] if pub_date_col and pd.notna(row[pub_date_col]) else None
                assign_date = row[assign_date_col] if assign_date_col and pd.notna(row[assign_date_col]) else None
                notes = row[notes_col] if notes_col and pd.notna(row[notes_col]) else None

                # Determine status using corrected logic:
                # ISBNs with Title, Format, and Status non-empty are publicly assigned
                if (title and str(title).strip() and
                        format_value and str(format_value).strip() and
                        status_value and str(status_value).strip()):
                    status = ISBNStatus.PUBLICLY_ASSIGNED
                    stats["publicly_assigned"] += 1
                else:
                    status = ISBNStatus.AVAILABLE
                    stats["available"] += 1

                # Create ISBN object
                isbn_obj = ISBN(
                    isbn=isbn_value,
                    publisher_id=publisher_id,
                    status=status,
                    title=str(title).strip() if title else None,
                    format=str(format_value).strip() if format_value else None,
                    imprint=str(imprint).strip() if imprint else None,
                    publication_date=pub_date,
                    assignment_date=assign_date,
                    notes=str(notes).strip() if notes else None
                )

                # Add to database
                db.isbns[isbn_value] = isbn_obj
                stats["imported"] += 1

                if idx < 5:  # Log first 5 for debugging
                    logger.info(
                        f"Row {idx}: ISBN={isbn_value}, Title='{title}', Format='{format_value}', Status='{status_value}' -> {status.value}")

            except Exception as e:
                logger.error(f"Error importing ISBN from row {idx}: {e}")
                stats["errors"] += 1

        return stats

    except Exception as e:
        logger.error(f"Error importing ISBNs from {file_path}: {e}")
        raise ISBNImportError(f"Error importing ISBNs: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Import ISBNs from Bowker spreadsheets with corrected status logic.')
    parser.add_argument('--file', dest='file_path', help='Path to a single Bowker spreadsheet')
    parser.add_argument('--directory', help='Path to directory containing Bowker spreadsheet files')
    parser.add_argument('publisher_id', help='ID of the publisher')
    parser.add_argument('--output', '-o', default='data/isbn_database.json', help='Path to the output database file')
    parser.add_argument('--clear', action='store_true', help='Clear existing database before import')
    parser.add_argument('--append-unique', action='store_true', help='Only import ISBNs not already in the database')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    # Validate arguments
    if not args.file_path and not args.directory:
        logger.error("Either --file or --directory must be specified")
        return 1
    if args.file_path and args.directory:
        logger.error("Cannot specify both --file and --directory")
        return 1

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create or load the ISBN database
    if args.clear:
        # Clear the database
        with open(args.output, 'w') as f:
            f.write('{"isbns": []}')
        logger.info(f"Cleared database at {args.output}")

    db = ISBNDatabase(args.output)

    # Initialize aggregate statistics
    aggregate_stats = {
        "total": 0,
        "imported": 0,
        "skipped": 0,
        "errors": 0,
        "available": 0,
        "privately_assigned": 0,
        "publicly_assigned": 0,
        "duplicates": 0
    }

    try:
        if args.directory:
            # Check if directory exists
            if not os.path.isdir(args.directory):
                logger.error(f"Directory not found: {args.directory}")
                return 1

            # Get all CSV and Excel files in the directory
            files = [
                os.path.join(args.directory, f)
                for f in os.listdir(args.directory)
                if f.endswith(('.csv', '.xlsx', '.xls'))
            ]

            if not files:
                logger.error(f"No CSV or Excel files found in directory: {args.directory}")
                return 1

            logger.info(f"Found {len(files)} files to process in {args.directory}")

            # Process each file
            for file_path in files:
                logger.info(f"Processing file: {file_path}")
                if not os.path.exists(file_path):
                    logger.error(f"File not found: {file_path}")
                    aggregate_stats["errors"] += 1
                    continue

                stats = import_bowker_corrected(db, file_path, args.publisher_id, args.append_unique)

                # Aggregate statistics
                for key in aggregate_stats:
                    aggregate_stats[key] += stats[key]

                # Log file-specific statistics
                logger.info(f"File {file_path} import completed")
                logger.info(f"  Total rows: {stats['total']}")
                logger.info(f"  Imported: {stats['imported']}")
                logger.info(f"  Skipped: {stats['skipped']}")
                if args.append_unique:
                    logger.info(f"  Duplicates skipped: {stats['duplicates']}")
                logger.info(f"  Errors: {stats['errors']}")
                logger.info(f"  Available: {stats['available']}")
                logger.info(f"  Privately assigned: {stats['privately_assigned']}")
                logger.info(f"  Publicly assigned: {stats['publicly_assigned']}")

        else:
            # Process single file
            if not os.path.exists(args.file_path):
                logger.error(f"File not found: {args.file_path}")
                return 1

            logger.info(f"Importing ISBNs from {args.file_path} for publisher {args.publisher_id}")
            aggregate_stats = import_bowker_corrected(db, args.file_path, args.publisher_id, args.append_unique)

        # Save the database
        db.save_database()

        # Print aggregate statistics
        logger.info("Import completed successfully")
        logger.info(f"Total rows processed: {aggregate_stats['total']}")
        logger.info(f"Imported: {aggregate_stats['imported']}")
        logger.info(f"Skipped: {aggregate_stats['skipped']}")
        if args.append_unique:
            logger.info(f"Duplicates skipped: {aggregate_stats['duplicates']}")
        logger.info(f"Errors: {aggregate_stats['errors']}")
        logger.info(f"Available: {aggregate_stats['available']}")
        logger.info(f"Privately assigned: {aggregate_stats['privately_assigned']}")
        logger.info(f"Publicly assigned: {aggregate_stats['publicly_assigned']}")

        # Get database statistics
        db_stats = db.get_statistics()
        logger.info(f"Database now contains {db_stats['total']} ISBNs")
        logger.info(f"Available: {db_stats['available']}")
        logger.info(f"Privately assigned: {db_stats['privately_assigned']}")
        logger.info(f"Publicly assigned: {db_stats['publicly_assigned']}")

        return 0

    except ISBNImportError as e:
        logger.error(f"Import error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())