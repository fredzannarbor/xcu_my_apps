"""
Schedule ISBN Manager with CSV and JSON support.

This module provides functionality for assigning and tracking ISBNs in publishing schedules,
supporting both CSV and JSON format schedule files.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

try:
    import chardet
except ImportError:
    chardet = None
    logging.warning("chardet not available - using UTF-8 encoding by default")

from src.codexes.modules.distribution.isbn_database import ISBNDatabase, ISBNStatus

logger = logging.getLogger(__name__)


class ScheduleISBNManager:
    """
    Manager for assigning and tracking ISBNs in publishing schedules.

    This class provides methods to:
    - Assign ISBNs to books in schedules (CSV or JSON format)
    - Track ISBN assignments
    - Validate ISBN availability
    - Generate reports on ISBN usage
    """

    def __init__(self, isbn_db_path: str = "data/isbn_database.json"):
        """
        Initialize the Schedule ISBN Manager.

        Args:
            isbn_db_path: Path to the ISBN database file
        """
        self.isbn_db = ISBNDatabase(isbn_db_path)
        self.assignment_log = []

    def _detect_file_encoding(self, file_path: str) -> str:
        """
        Detect the encoding of a file.

        Args:
            file_path: Path to the file

        Returns:
            Detected encoding string
        """
        if not chardet:
            return 'utf-8'

        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'
                confidence = result['confidence']
                logger.info(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")
                return encoding
        except Exception as e:
            logger.warning(f"Error detecting encoding: {e}, using UTF-8")
            return 'utf-8'

    def _load_schedule_data(self, schedule_path: str) -> Dict[str, Any]:
        """
        Load schedule data from either CSV or JSON format.

        Args:
            schedule_path: Path to the schedule file

        Returns:
            Dictionary with schedule data in standardized format

        Raises:
            ValueError: If file format is not supported
            Exception: If file cannot be loaded
        """
        try:
            file_path = Path(schedule_path)

            if file_path.suffix.lower() == '.csv':
                return self._load_csv_schedule(schedule_path)
            elif file_path.suffix.lower() == '.json':
                return self._load_json_schedule(schedule_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")

        except Exception as e:
            logger.error(f"Error loading schedule data from {schedule_path}: {e}")
            raise

    def _load_csv_schedule(self, schedule_path: str) -> Dict[str, Any]:
        """
        Load schedule data from CSV format.

        Args:
            schedule_path: Path to the CSV file

        Returns:
            Dictionary with schedule data in standardized format
        """
        try:
            # Detect encoding
            encoding = self._detect_file_encoding(schedule_path)
            logger.info(f"Loading CSV schedule with encoding: {encoding}")

            schedule_data = {'publishing_schedule': []}
            current_month = None
            current_books = []

            with open(schedule_path, 'r', encoding=encoding, errors='replace') as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)

                # Common delimiters to try
                delimiter = ','
                for test_delimiter in [',', '\t', ';', '|']:
                    if sample.count(test_delimiter) > sample.count(','):
                        delimiter = test_delimiter
                        break

                logger.info(f"Using delimiter: '{delimiter}'")

                reader = csv.DictReader(f, delimiter=delimiter)

                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header row
                    try:
                        # Clean up the row data
                        row = {k.strip() if k else f'col_{i}': v.strip() if v else ''
                               for i, (k, v) in enumerate(row.items())}

                        # Look for month column (various possible names)
                        month = None
                        month_columns = ['month', 'Month', 'MONTH', 'publication_month', 'pub_month', 'schedule_month']
                        for col in month_columns:
                            if col in row and row[col]:
                                month = row[col]
                                break

                        # If we found a new month, save previous month's books
                        if month and month != current_month:
                            if current_month and current_books:
                                schedule_data['publishing_schedule'].append({
                                    'month': current_month,
                                    'books': current_books
                                })
                            current_month = month
                            current_books = []

                        # Extract book data
                        book_data = {}

                        # Map common CSV columns to book data
                        column_mappings = {
                            'title': ['title', 'Title', 'TITLE', 'book_title', 'Book Title', 'Book_Title'],
                            'author': ['author', 'Author', 'AUTHOR', 'authors', 'Authors'],
                            'isbn': ['isbn', 'ISBN', 'isbn13', 'ISBN13', 'isbn_13', 'ISBN_13'],
                            'description': ['description', 'Description', 'summary', 'Summary', 'Synopsis'],
                            'stream': ['stream', 'Stream', 'series', 'Series', 'category', 'Category'],
                            'imprint': ['imprint', 'Imprint', 'IMPRINT', 'publisher', 'Publisher'],
                            'format': ['format', 'Format', 'binding', 'Binding', 'book_format'],
                            'page_count': ['pages', 'Pages', 'page_count', 'Page Count', 'page_cnt'],
                            'publication_date': ['pub_date', 'publication_date', 'Publication Date', 'publish_date']
                        }

                        for field, possible_columns in column_mappings.items():
                            for col in possible_columns:
                                if col in row and row[col]:
                                    book_data[field] = row[col]
                                    break

                        # Only add if we have at least a title
                        if book_data.get('title'):
                            current_books.append(book_data)

                    except Exception as e:
                        logger.warning(f"Error processing row {row_num}: {e}")
                        continue

            # Don't forget the last month
            if current_month and current_books:
                schedule_data['publishing_schedule'].append({
                    'month': current_month,
                    'books': current_books
                })
            else:
                # No explicit month column found — treat the entire CSV as a single schedule block.
                # This allows CSVs that are simply a flat list of books (one row per book) to be processed.
                if current_books:
                    schedule_data['publishing_schedule'].append({
                        'month': 'Schedule',
                        'books': current_books
                    })

            total_books = sum(len(month_data.get('books', [])) for month_data in schedule_data['publishing_schedule'])
            logger.info(
                f"Loaded {len(schedule_data['publishing_schedule'])} months with {total_books} total books from CSV")

            return schedule_data

        except Exception as e:
            logger.error(f"Error loading CSV schedule from {schedule_path}: {e}")
            raise

    def _load_json_schedule(self, schedule_path: str) -> Dict[str, Any]:
        """
        Load schedule data from JSON format.

        Args:
            schedule_path: Path to the JSON file

        Returns:
            Dictionary with schedule data
        """
        try:
            with open(schedule_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded JSON schedule with {len(data.get('publishing_schedule', []))} months")
                return data
        except Exception as e:
            logger.error(f"Error loading JSON schedule from {schedule_path}: {e}")
            raise

    def assign_isbn_to_book(self, book_data: Dict[str, Any], publisher_id: str,
                            preferred_isbn: Optional[str] = None,
                            format_type: str = "paperback") -> Tuple[bool, str, Optional[str]]:
        """
        Assign an ISBN to a book in the schedule.

        Args:
            book_data: Book data dictionary from schedule
            publisher_id: Publisher identifier
            preferred_isbn: Specific ISBN to assign (optional)
            format_type: Book format (paperback, hardcover, ebook)

        Returns:
            Tuple of (success, message, assigned_isbn)
        """
        try:
            title = book_data.get('title', 'Unknown Title')

            # Check if book already has an ISBN
            if 'isbn' in book_data and book_data['isbn']:
                existing_isbn = str(book_data['isbn']).replace('-', '').replace(' ', '')
                if len(existing_isbn) == 13 and existing_isbn.isdigit():
                    return True, f"Book '{title}' already has ISBN: {existing_isbn}", existing_isbn

            # Try to assign preferred ISBN if provided
            if preferred_isbn:
                success, message, isbn = self._assign_specific_isbn(
                    preferred_isbn, book_data, publisher_id, format_type
                )
                if success:
                    return success, message, isbn
                else:
                    logger.warning(f"Could not assign preferred ISBN {preferred_isbn}: {message}")

            # Find and assign an available ISBN
            available_isbn = self.isbn_db.get_next_available_isbn(publisher_id)
            if not available_isbn:
                return False, f"No available ISBNs found for publisher {publisher_id}", None

            # Assign the ISBN
            success = self.isbn_db.assign_isbn(available_isbn, title)

            if success:
                # Update book data with ISBN
                book_data['isbn'] = available_isbn
                book_data['isbn_assigned_date'] = datetime.now().isoformat()

                # Log the assignment
                self.assignment_log.append({
                    'isbn': available_isbn,
                    'title': title,
                    'publisher_id': publisher_id,
                    'format_type': format_type,
                    'assigned_date': datetime.now().isoformat(),
                    'source': 'schedule_assignment'
                })

                return True, f"Assigned ISBN {available_isbn} to '{title}'", available_isbn
            else:
                return False, f"Failed to assign ISBN {available_isbn} to '{title}'", None

        except Exception as e:
            logger.error(f"Error assigning ISBN to book '{book_data.get('title', 'Unknown')}': {e}")
            return False, f"Error assigning ISBN: {e}", None

    def _assign_specific_isbn(self, isbn: str, book_data: Dict[str, Any],
                              publisher_id: str, format_type: str) -> Tuple[bool, str, Optional[str]]:
        """
        Assign a specific ISBN to a book.

        Args:
            isbn: Specific ISBN to assign
            book_data: Book data dictionary
            publisher_id: Publisher identifier
            format_type: Book format

        Returns:
            Tuple of (success, message, assigned_isbn)
        """
        try:
            # Clean ISBN
            clean_isbn = isbn.replace('-', '').replace(' ', '')

            # Validate ISBN format
            if len(clean_isbn) != 13 or not clean_isbn.isdigit():
                return False, f"Invalid ISBN format: {isbn}", None

            # Check if ISBN exists in database
            if clean_isbn not in self.isbn_db.isbns:
                return False, f"ISBN {clean_isbn} not found in database", None

            # Check if ISBN is available
            isbn_obj = self.isbn_db.isbns[clean_isbn]
            if isbn_obj.status != ISBNStatus.AVAILABLE:
                return False, f"ISBN {clean_isbn} is not available (status: {isbn_obj.status.value})", None

            # Check publisher match
            if isbn_obj.publisher_id != publisher_id:
                return False, f"ISBN {clean_isbn} belongs to different publisher: {isbn_obj.publisher_id}", None

            # Assign the ISBN
            title = book_data.get('title', 'Unknown Title')
            success = self.isbn_db.assign_isbn(clean_isbn, title)

            if success:
                return True, f"Successfully assigned ISBN {clean_isbn} to '{title}'", clean_isbn
            else:
                return False, f"Failed to assign ISBN {clean_isbn}", None

        except Exception as e:
            logger.error(f"Error assigning specific ISBN {isbn}: {e}")
            return False, f"Error assigning specific ISBN: {e}", None

    def assign_isbns_to_schedule(self, schedule_path: str, publisher_id: str,
                                 output_path: Optional[str] = None,
                                 format_type: str = "paperback",
                                 dry_run: bool = False) -> Dict[str, Any]:
        """
        Assign ISBNs to all books in a publishing schedule.

        Args:
            schedule_path: Path to the schedule file (CSV or JSON)
            publisher_id: Publisher identifier
            output_path: Path to save updated schedule (optional)
            format_type: Default book format
            dry_run: If True, don't actually assign ISBNs

        Returns:
            Dictionary with assignment results and statistics
        """
        try:
            # Load schedule data
            schedule_data = self._load_schedule_data(schedule_path)

            # Normalize schedule_path to Path for suffix checks and consistent output naming
            schedule_path_obj = Path(schedule_path)
            if output_path is None:
                # For CSV files, create a JSON output by default unless specified otherwise
                if schedule_path_obj.suffix.lower() == '.csv':
                    output_path = str(schedule_path_obj.with_suffix('')) + '_with_isbns.json'
                else:
                    output_path = str(schedule_path)

            results = {
                'total_books': 0,
                'assigned': 0,
                'already_assigned': 0,
                'failed': 0,
                'assignments': [],
                'errors': []
            }

            # Process each month in the schedule
            for month_data in schedule_data.get('publishing_schedule', []):
                month_name = month_data.get('month', 'Unknown Month')
                logger.info(f"Processing {month_name}")

                for book in month_data.get('books', []):
                    results['total_books'] += 1
                    title = book.get('title', 'Unknown Title')

                    if dry_run:
                        # In dry run mode, just check availability
                        if 'isbn' in book and book['isbn']:
                            results['already_assigned'] += 1
                            results['assignments'].append({
                                'title': title,
                                'month': month_name,
                                'status': 'already_assigned',
                                'isbn': book['isbn']
                            })
                        else:
                            available_isbn = self.isbn_db.get_next_available_isbn(publisher_id)
                            if available_isbn:
                                results['assigned'] += 1
                                results['assignments'].append({
                                    'title': title,
                                    'month': month_name,
                                    'status': 'would_assign',
                                    'isbn': available_isbn
                                })
                            else:
                                results['failed'] += 1
                                results['errors'].append({
                                    'title': title,
                                    'month': month_name,
                                    'error': 'No available ISBNs'
                                })
                    else:
                        # Actually assign ISBN
                        success, message, assigned_isbn = self.assign_isbn_to_book(
                            book, publisher_id, format_type=format_type
                        )

                        if success:
                            if 'already has ISBN' in message:
                                results['already_assigned'] += 1
                                results['assignments'].append({
                                    'title': title,
                                    'month': month_name,
                                    'status': 'already_assigned',
                                    'isbn': assigned_isbn,
                                    'message': message
                                })
                            else:
                                results['assigned'] += 1
                                results['assignments'].append({
                                    'title': title,
                                    'month': month_name,
                                    'status': 'newly_assigned',
                                    'isbn': assigned_isbn,
                                    'message': message
                                })
                        else:
                            results['failed'] += 1
                            results['errors'].append({
                                'title': title,
                                'month': month_name,
                                'error': message
                            })

            # Save updated schedule if not dry run
            if not dry_run and results['assigned'] > 0:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(schedule_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Updated schedule saved to: {output_path}")

            return results

        except Exception as e:
            logger.error(f"Error processing schedule {schedule_path}: {e}")
            return {
                'error': str(e),
                'total_books': 0,
                'assigned': 0,
                'already_assigned': 0,
                'failed': 0,
                'assignments': [],
                'errors': []
            }

    def validate_schedule_isbns(self, schedule_path: str) -> Dict[str, Any]:
        """
        Validate all ISBNs in a schedule.

        Args:
            schedule_path: Path to the schedule file (CSV or JSON)

        Returns:
            Dictionary with validation results
        """
        try:
            schedule_data = self._load_schedule_data(schedule_path)

            results = {
                'total_books': 0,
                'books_with_isbn': 0,
                'valid_isbns': 0,
                'invalid_isbns': 0,
                'duplicate_isbns': 0,
                'validation_details': [],
                'isbn_usage': {}
            }

            seen_isbns = set()

            # Process each month in the schedule
            for month_data in schedule_data.get('publishing_schedule', []):
                month_name = month_data.get('month', 'Unknown Month')

                for book in month_data.get('books', []):
                    results['total_books'] += 1
                    title = book.get('title', 'Unknown Title')

                    if 'isbn' not in book or not book['isbn']:
                        results['validation_details'].append({
                            'title': title,
                            'month': month_name,
                            'status': 'no_isbn',
                            'message': 'No ISBN assigned'
                        })
                        continue

                    results['books_with_isbn'] += 1
                    isbn = str(book['isbn']).replace('-', '').replace(' ', '')

                    # Validate ISBN format
                    if len(isbn) != 13 or not isbn.isdigit():
                        results['invalid_isbns'] += 1
                        results['validation_details'].append({
                            'title': title,
                            'month': month_name,
                            'isbn': book['isbn'],
                            'status': 'invalid_format',
                            'message': 'Invalid ISBN format'
                        })
                        continue

                    # Check for duplicates within schedule
                    if isbn in seen_isbns:
                        results['duplicate_isbns'] += 1
                        results['validation_details'].append({
                            'title': title,
                            'month': month_name,
                            'isbn': isbn,
                            'status': 'duplicate',
                            'message': 'Duplicate ISBN in schedule'
                        })
                    else:
                        seen_isbns.add(isbn)

                    # Check against database
                    if isbn in self.isbn_db.isbns:
                        isbn_obj = self.isbn_db.isbns[isbn]
                        results['valid_isbns'] += 1
                        results['validation_details'].append({
                            'title': title,
                            'month': month_name,
                            'isbn': isbn,
                            'status': 'valid',
                            'db_status': isbn_obj.status.value,
                            'db_title': isbn_obj.title,
                            'message': 'Valid ISBN found in database'
                        })

                        # Track usage
                        if isbn not in results['isbn_usage']:
                            results['isbn_usage'][isbn] = []
                        results['isbn_usage'][isbn].append({
                            'title': title,
                            'month': month_name
                        })
                    else:
                        results['invalid_isbns'] += 1
                        results['validation_details'].append({
                            'title': title,
                            'month': month_name,
                            'isbn': isbn,
                            'status': 'not_in_database',
                            'message': 'ISBN not found in database'
                        })

            return results

        except Exception as e:
            logger.error(f"Error validating schedule ISBNs: {e}")
            return {'error': str(e)}

    def generate_isbn_report(self, schedule_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive ISBN usage report for a schedule.

        Args:
            schedule_path: Path to the schedule file (CSV or JSON)
            output_path: Path to save the report (optional)

        Returns:
            Dictionary with report data
        """
        try:
            validation_results = self.validate_schedule_isbns(schedule_path)

            if 'error' in validation_results:
                return validation_results

            # Generate summary statistics
            report = {
                'schedule_file': str(schedule_path),  # Convert to string
                'generated_date': datetime.now().isoformat(),
                'summary': {
                    'total_books': validation_results['total_books'],
                    'books_with_isbn': validation_results['books_with_isbn'],
                    'books_without_isbn': validation_results['total_books'] - validation_results['books_with_isbn'],
                    'valid_isbns': validation_results['valid_isbns'],
                    'invalid_isbns': validation_results['invalid_isbns'],
                    'duplicate_isbns': validation_results['duplicate_isbns'],
                    'isbn_coverage_percentage': round(
                        (validation_results['books_with_isbn'] / validation_results['total_books'] * 100)
                        if validation_results['total_books'] > 0 else 0, 2
                    )
                },
                'validation_details': validation_results['validation_details'],
                'isbn_usage': validation_results['isbn_usage'],
                'recommendations': []
            }

            # Generate recommendations
            if report['summary']['books_without_isbn'] > 0:
                report['recommendations'].append(
                    f"Assign ISBNs to {report['summary']['books_without_isbn']} books without ISBNs"
                )

            if report['summary']['invalid_isbns'] > 0:
                report['recommendations'].append(
                    f"Fix {report['summary']['invalid_isbns']} invalid ISBNs"
                )

            if report['summary']['duplicate_isbns'] > 0:
                report['recommendations'].append(
                    f"Resolve {report['summary']['duplicate_isbns']} duplicate ISBN assignments"
                )

            if output_path:
                # Ensure output_path is a string and parent directory exists
                output_path_obj = Path(output_path)
                output_path_obj.parent.mkdir(parents=True, exist_ok=True)
                with open(str(output_path_obj), 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False, default=str)
                logger.info(f"ISBN report saved to: {output_path_obj}")

            # Clean up any Path objects before returning
            report = self._sanitize_for_json(report)
            return report

        except Exception as e:
            logger.error(f"Error generating ISBN report: {e}")
            return {'error': str(e)}

    def bulk_assign_isbns(self, isbn_assignments: List[Dict[str, str]],
                          schedule_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Bulk assign specific ISBNs to books in a schedule.

        Args:
            isbn_assignments: List of {'title': 'Book Title', 'isbn': '1234567890123'} mappings
            schedule_path: Path to the schedule file (CSV or JSON)
            output_path: Path to save updated schedule (optional)

        Returns:
            Dictionary with assignment results
        """
        try:
            # Load schedule
            schedule_data = self._load_schedule_data(schedule_path)

            if output_path is None:
                if schedule_path.endswith('.csv'):
                    output_path = schedule_path.replace('.csv', '_bulk_assigned.json')
                else:
                    output_path = schedule_path

            # Create title to ISBN mapping
            title_isbn_map = {assignment['title']: assignment['isbn'] for assignment in isbn_assignments}

            results = {
                'total_assignments': len(isbn_assignments),
                'successful': 0,
                'failed': 0,
                'not_found': 0,
                'details': []
            }

            # Process each month in the schedule
            for month_data in schedule_data.get('publishing_schedule', []):
                month_name = month_data.get('month', 'Unknown Month')

                for book in month_data.get('books', []):
                    title = book.get('title', 'Unknown Title')

                    if title in title_isbn_map:
                        isbn = title_isbn_map[title]

                        # Validate and assign ISBN
                        clean_isbn = isbn.replace('-', '').replace(' ', '')

                        if len(clean_isbn) == 13 and clean_isbn.isdigit():
                            book['isbn'] = clean_isbn
                            book['isbn_assigned_date'] = datetime.now().isoformat()
                            book['isbn_assignment_method'] = 'bulk_assignment'

                            results['successful'] += 1
                            results['details'].append({
                                'title': title,
                                'month': month_name,
                                'isbn': clean_isbn,
                                'status': 'assigned'
                            })
                        else:
                            results['failed'] += 1
                            results['details'].append({
                                'title': title,
                                'month': month_name,
                                'isbn': isbn,
                                'status': 'invalid_format',
                                'error': 'Invalid ISBN format'
                            })

            # Check for titles that weren't found
            found_titles = {detail['title'] for detail in results['details']}
            for assignment in isbn_assignments:
                if assignment['title'] not in found_titles:
                    results['not_found'] += 1
                    results['details'].append({
                        'title': assignment['title'],
                        'isbn': assignment['isbn'],
                        'status': 'not_found',
                        'error': 'Title not found in schedule'
                    })

            # Save updated schedule
            if results['successful'] > 0:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(schedule_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Updated schedule with bulk ISBN assignments saved to: {output_path}")

            return results

        except Exception as e:
            logger.error(f"Error in bulk ISBN assignment: {e}")
            return {'error': str(e)}

    def get_assignment_log(self) -> List[Dict[str, Any]]:
        """
        Get the log of ISBN assignments made during this session.

        Returns:
            List of assignment log entries
        """
        return self.assignment_log.copy()

    def clear_assignment_log(self) -> None:
        """Clear the assignment log."""
        self.assignment_log.clear()

    def get_available_isbn_count(self, publisher_id: str) -> int:
        """
        Get the count of available ISBNs for a publisher.

        Args:
            publisher_id: Publisher identifier

        Returns:
            Number of available ISBNs
        """
        return len([
            isbn for isbn, isbn_obj in self.isbn_db.isbns.items()
            if isbn_obj.publisher_id == publisher_id and isbn_obj.status == ISBNStatus.AVAILABLE
        ])

    def _sanitize_for_json(self, obj):
        """Convert Path objects and other non-serializable objects to strings for JSON serialization."""
        if isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, dict):
            return {key: self._sanitize_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(item) for item in obj]
        else:
            return obj