"""
ISBN scheduling system for managing ISBN assignments across publishing schedules.
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class ISBNStatus(Enum):
    """ISBN assignment status"""
    AVAILABLE = "available"
    SCHEDULED = "scheduled"
    ASSIGNED = "assigned"
    PUBLISHED = "published"
    RESERVED = "reserved"

@dataclass
class ISBNAssignment:
    """ISBN assignment record"""
    isbn: str
    book_title: str
    book_id: str
    scheduled_date: str
    assigned_date: Optional[str] = None
    status: str = ISBNStatus.SCHEDULED.value
    imprint: str = ""
    publisher: str = ""
    format: str = "paperback"
    notes: str = ""
    priority: int = 1

@dataclass
class ISBNBlock:
    """ISBN block/range information"""
    prefix: str
    start_number: int
    end_number: int
    publisher_code: str
    imprint_code: str
    total_count: int
    used_count: int = 0
    reserved_count: int = 0

class ISBNScheduler:
    """Manage ISBN assignments in publishing schedules"""
    
    def __init__(self, schedule_file: str = "configs/isbn_schedule.json"):
        self.schedule_file = schedule_file
        self.assignments: Dict[str, ISBNAssignment] = {}
        self.isbn_blocks: Dict[str, ISBNBlock] = {}
        self.load_schedule()
    
    def load_schedule(self) -> None:
        """Load existing ISBN schedule from file"""
        try:
            if os.path.exists(self.schedule_file):
                with open(self.schedule_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for isbn, assignment_data in data.get('assignments', {}).items():
                    self.assignments[isbn] = ISBNAssignment(**assignment_data)
                
                for block_id, block_data in data.get('isbn_blocks', {}).items():
                    self.isbn_blocks[block_id] = ISBNBlock(**block_data)
                
                logger.info(f"Loaded {len(self.assignments)} assignments and {len(self.isbn_blocks)} blocks")
            else:
                logger.info("No existing ISBN schedule found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading ISBN schedule: {e}")
            self.assignments = {}
            self.isbn_blocks = {}
    
    def save_schedule(self) -> None:
        """Save ISBN schedule to file"""
        try:
            os.makedirs(os.path.dirname(self.schedule_file), exist_ok=True)
            data = {
                'assignments': {isbn: asdict(assignment) for isbn, assignment in self.assignments.items()},
                'isbn_blocks': {block_id: asdict(block) for block_id, block in self.isbn_blocks.items()},
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved ISBN schedule with {len(self.assignments)} assignments")
        except Exception as e:
            logger.error(f"Error saving ISBN schedule: {e}")
    
    def add_isbn_block(self, prefix: str, start_number: int, end_number: int, 
                       publisher_code: str, imprint_code: str = "") -> str:
        """Add a new ISBN block/range"""
        try:
            block_id = f"{prefix}_{publisher_code}_{start_number}_{end_number}"
            total_count = end_number - start_number + 1
            
            isbn_block = ISBNBlock(
                prefix=prefix,
                start_number=start_number,
                end_number=end_number,
                publisher_code=publisher_code,
                imprint_code=imprint_code,
                total_count=total_count
            )
            
            self.isbn_blocks[block_id] = isbn_block
            self.save_schedule()
            logger.info(f"Added ISBN block: {block_id} with {total_count} ISBNs")
            return block_id
        except Exception as e:
            logger.error(f"Error adding ISBN block: {e}")
            return ""
    
    def _format_isbn(self, prefix: str, publisher_code: str, number: int) -> str:
        """Format ISBN from components"""
        try:
            # Create a 12-digit base (prefix + publisher + title number)
            # Adjust formatting to ensure total is 12 digits before check digit
            title_number = f"{number:04d}"  # 4 digits for title number
            isbn_base = f"{prefix}{publisher_code}{title_number}"
            
            # Ensure we have exactly 12 digits
            if len(isbn_base) > 12:
                isbn_base = isbn_base[:12]
            elif len(isbn_base) < 12:
                isbn_base = isbn_base.ljust(12, '0')
            
            check_digit = self._calculate_check_digit(isbn_base)
            return f"{isbn_base}{check_digit}"
        except Exception as e:
            logger.error(f"Error formatting ISBN: {e}")
            return ""
    
    def _calculate_check_digit(self, isbn_base: str) -> str:
        """Calculate ISBN-13 check digit"""
        try:
            total = 0
            for i, digit in enumerate(isbn_base):
                weight = 1 if i % 2 == 0 else 3
                total += int(digit) * weight
            check_digit = (10 - (total % 10)) % 10
            return str(check_digit)
        except Exception as e:
            logger.error(f"Error calculating check digit: {e}")
            return "0"
    
    def schedule_isbn_assignment(self, book_title: str, book_id: str, 
                                scheduled_date: str, imprint: str = "", 
                                publisher: str = "", format: str = "paperback",
                                priority: int = 1, notes: str = "") -> Optional[str]:
        """Schedule an ISBN assignment for a book"""
        try:
            isbn = self._get_next_available_isbn(imprint, publisher)
            if not isbn:
                logger.error("No available ISBNs found")
                return None
            
            assignment = ISBNAssignment(
                isbn=isbn,
                book_title=book_title,
                book_id=book_id,
                scheduled_date=scheduled_date,
                status=ISBNStatus.SCHEDULED.value,
                imprint=imprint,
                publisher=publisher,
                format=format,
                priority=priority,
                notes=notes
            )
            
            self.assignments[isbn] = assignment
            self._update_block_usage(isbn)
            self.save_schedule()
            logger.info(f"Scheduled ISBN {isbn} for '{book_title}' on {scheduled_date}")
            return isbn
        except Exception as e:
            logger.error(f"Error scheduling ISBN assignment: {e}")
            return None
    
    def _get_next_available_isbn(self, imprint: str = "", publisher: str = "") -> Optional[str]:
        """Get the next available ISBN from blocks"""
        try:
            for block_id, block in self.isbn_blocks.items():
                if imprint and block.imprint_code and block.imprint_code != imprint:
                    continue
                if publisher and block.publisher_code != publisher:
                    continue
                
                if block.used_count + block.reserved_count < block.total_count:
                    for num in range(block.start_number, block.end_number + 1):
                        isbn = self._format_isbn(block.prefix, block.publisher_code, num)
                        if isbn not in self.assignments:
                            return isbn
            return None
        except Exception as e:
            logger.error(f"Error getting next available ISBN: {e}")
            return None
    
    def _update_block_usage(self, isbn: str) -> None:
        """Update block usage count when ISBN is assigned"""
        try:
            for block in self.isbn_blocks.values():
                isbn_prefix = isbn[:len(block.prefix)]
                if isbn_prefix == block.prefix and block.publisher_code in isbn:
                    # Extract the title number part (4 digits after publisher code)
                    try:
                        start_pos = len(block.prefix) + len(block.publisher_code)
                        number_part = isbn[start_pos:start_pos+4]
                        number = int(number_part)
                        if block.start_number <= number <= block.end_number:
                            block.used_count += 1
                            break
                    except (ValueError, IndexError):
                        continue
        except Exception as e:
            logger.error(f"Error updating block usage: {e}")
    
    def assign_isbn_now(self, isbn: str) -> bool:
        """Mark an ISBN as assigned (ready for use)"""
        try:
            if isbn not in self.assignments:
                logger.error(f"ISBN {isbn} not found in schedule")
                return False
            
            assignment = self.assignments[isbn]
            assignment.status = ISBNStatus.ASSIGNED.value
            assignment.assigned_date = datetime.now().isoformat()
            self.save_schedule()
            logger.info(f"ISBN {isbn} marked as assigned")
            return True
        except Exception as e:
            logger.error(f"Error assigning ISBN {isbn}: {e}")
            return False
    
    def reserve_isbn(self, isbn: str, reason: str = "") -> bool:
        """Reserve an ISBN (prevent it from being assigned)"""
        try:
            if isbn in self.assignments:
                assignment = self.assignments[isbn]
                assignment.status = ISBNStatus.RESERVED.value
                assignment.notes = f"Reserved: {reason}"
            else:
                assignment = ISBNAssignment(
                    isbn=isbn,
                    book_title="RESERVED",
                    book_id="reserved",
                    scheduled_date=datetime.now().strftime('%Y-%m-%d'),
                    status=ISBNStatus.RESERVED.value,
                    notes=f"Reserved: {reason}"
                )
                self.assignments[isbn] = assignment
            
            self.save_schedule()
            logger.info(f"ISBN {isbn} reserved: {reason}")
            return True
        except Exception as e:
            logger.error(f"Error reserving ISBN {isbn}: {e}")
            return False
    
    def update_assignment(self, isbn: str, **kwargs) -> bool:
        """Update an existing assignment"""
        try:
            if isbn not in self.assignments:
                logger.error(f"ISBN {isbn} not found in schedule")
                return False
            
            assignment = self.assignments[isbn]
            allowed_fields = ['book_title', 'book_id', 'scheduled_date', 'status', 
                            'imprint', 'publisher', 'format', 'priority', 'notes']
            
            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(assignment, field):
                    setattr(assignment, field, value)
            
            self.save_schedule()
            logger.info(f"Updated assignment for ISBN {isbn}")
            return True
        except Exception as e:
            logger.error(f"Error updating assignment for ISBN {isbn}: {e}")
            return False
    
    def get_scheduled_assignments(self, start_date: str = None, end_date: str = None) -> List[ISBNAssignment]:
        """Get scheduled assignments within date range"""
        try:
            assignments = []
            for assignment in self.assignments.values():
                if start_date and assignment.scheduled_date < start_date:
                    continue
                if end_date and assignment.scheduled_date > end_date:
                    continue
                assignments.append(assignment)
            
            assignments.sort(key=lambda x: (x.scheduled_date, x.priority))
            return assignments
        except Exception as e:
            logger.error(f"Error getting scheduled assignments: {e}")
            return []
    
    def get_assignments_by_status(self, status: ISBNStatus) -> List[ISBNAssignment]:
        """Get assignments by status"""
        try:
            return [assignment for assignment in self.assignments.values() 
                   if assignment.status == status.value]
        except Exception as e:
            logger.error(f"Error getting assignments by status: {e}")
            return []
    
    def get_upcoming_assignments(self, days_ahead: int = 30) -> List[ISBNAssignment]:
        """Get assignments scheduled within the next N days"""
        try:
            end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            today = datetime.now().strftime('%Y-%m-%d')
            return self.get_scheduled_assignments(start_date=today, end_date=end_date)
        except Exception as e:
            logger.error(f"Error getting upcoming assignments: {e}")
            return []
    
    def get_isbn_availability_report(self) -> Dict[str, Any]:
        """Generate ISBN availability report"""
        try:
            report = {
                'total_blocks': len(self.isbn_blocks),
                'total_isbns': sum(block.total_count for block in self.isbn_blocks.values()),
                'used_isbns': sum(block.used_count for block in self.isbn_blocks.values()),
                'reserved_isbns': sum(block.reserved_count for block in self.isbn_blocks.values()),
                'available_isbns': 0,
                'assignments_by_status': {},
                'blocks_detail': []
            }
            
            report['available_isbns'] = report['total_isbns'] - report['used_isbns'] - report['reserved_isbns']
            
            for status in ISBNStatus:
                count = len(self.get_assignments_by_status(status))
                report['assignments_by_status'][status.value] = count
            
            for block_id, block in self.isbn_blocks.items():
                available = block.total_count - block.used_count - block.reserved_count
                utilization = (block.used_count + block.reserved_count) / block.total_count * 100
                report['blocks_detail'].append({
                    'block_id': block_id,
                    'prefix': block.prefix,
                    'publisher_code': block.publisher_code,
                    'imprint_code': block.imprint_code,
                    'total': block.total_count,
                    'used': block.used_count,
                    'reserved': block.reserved_count,
                    'available': available,
                    'utilization_percent': round(utilization, 2)
                })
            
            return report
        except Exception as e:
            logger.error(f"Error generating availability report: {e}")
            return {}
    
    def bulk_schedule_from_csv(self, csv_file: str) -> int:
        """Bulk schedule ISBN assignments from CSV file"""
        try:
            import csv
            scheduled_count = 0
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    isbn = self.schedule_isbn_assignment(
                        book_title=row.get('title', ''),
                        book_id=row.get('book_id', ''),
                        scheduled_date=row.get('scheduled_date', ''),
                        imprint=row.get('imprint', ''),
                        publisher=row.get('publisher', ''),
                        format=row.get('format', 'paperback'),
                        priority=int(row.get('priority', 1)),
                        notes=row.get('notes', '')
                    )
                    if isbn:
                        scheduled_count += 1
            
            logger.info(f"Bulk scheduled {scheduled_count} ISBN assignments from {csv_file}")
            return scheduled_count
        except Exception as e:
            logger.error(f"Error bulk scheduling from CSV: {e}")
            return 0   
 
    def get_isbn_by_book_id(self, book_id: str) -> Optional[str]:
        """Get ISBN for a specific book ID (for rebuilds)"""
        try:
            for isbn, assignment in self.assignments.items():
                if assignment.book_id == book_id:
                    return isbn
            return None
        except Exception as e:
            logger.error(f"Error getting ISBN for book ID {book_id}: {e}")
            return None
    
    def get_assignment_by_book_id(self, book_id: str) -> Optional[ISBNAssignment]:
        """Get full assignment record for a specific book ID"""
        try:
            for assignment in self.assignments.values():
                if assignment.book_id == book_id:
                    return assignment
            return None
        except Exception as e:
            logger.error(f"Error getting assignment for book ID {book_id}: {e}")
            return None
    
    def assign_specific_isbn(self, isbn: str, book_title: str, book_id: str, 
                           scheduled_date: str, imprint: str = "", 
                           publisher: str = "", format: str = "paperback",
                           priority: int = 1, notes: str = "") -> bool:
        """Assign a specific ISBN to a book (for rebuilds or manual assignment)"""
        try:
            # Check if ISBN already exists in assignments
            if isbn in self.assignments:
                existing = self.assignments[isbn]
                logger.warning(f"ISBN {isbn} already assigned to '{existing.book_title}' (ID: {existing.book_id})")
                
                # If it's the same book ID, update the assignment
                if existing.book_id == book_id:
                    success = self.update_assignment(
                        isbn,
                        book_title=book_title,
                        scheduled_date=scheduled_date,
                        imprint=imprint,
                        publisher=publisher,
                        format=format,
                        priority=priority,
                        notes=notes
                    )
                    if success:
                        logger.info(f"Updated existing assignment for ISBN {isbn} and book ID {book_id}")
                    return success
                else:
                    logger.error(f"ISBN {isbn} is already assigned to a different book (ID: {existing.book_id})")
                    return False
            
            # Create new assignment with specific ISBN
            assignment = ISBNAssignment(
                isbn=isbn,
                book_title=book_title,
                book_id=book_id,
                scheduled_date=scheduled_date,
                status=ISBNStatus.ASSIGNED.value,  # Directly assign since it's manual
                assigned_date=datetime.now().isoformat(),
                imprint=imprint,
                publisher=publisher,
                format=format,
                priority=priority,
                notes=notes
            )
            
            self.assignments[isbn] = assignment
            self.save_schedule()
            logger.info(f"Assigned specific ISBN {isbn} to '{book_title}' (ID: {book_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error assigning specific ISBN {isbn}: {e}")
            return False
    
    def get_or_assign_isbn(self, book_id: str, book_title: str, 
                          scheduled_date: str, imprint: str = "", 
                          publisher: str = "", format: str = "paperback",
                          priority: int = 1, notes: str = "") -> Optional[str]:
        """Get existing ISBN for book ID, or assign new one if none exists"""
        try:
            # First check if book already has an ISBN
            existing_isbn = self.get_isbn_by_book_id(book_id)
            if existing_isbn:
                logger.info(f"Found existing ISBN {existing_isbn} for book ID {book_id}")
                
                # Update the assignment details in case they changed
                self.update_assignment(
                    existing_isbn,
                    book_title=book_title,
                    scheduled_date=scheduled_date,
                    imprint=imprint,
                    publisher=publisher,
                    format=format,
                    priority=priority,
                    notes=notes
                )
                return existing_isbn
            
            # No existing ISBN, assign a new one
            new_isbn = self.schedule_isbn_assignment(
                book_title=book_title,
                book_id=book_id,
                scheduled_date=scheduled_date,
                imprint=imprint,
                publisher=publisher,
                format=format,
                priority=priority,
                notes=notes
            )
            
            if new_isbn:
                logger.info(f"Assigned new ISBN {new_isbn} for book ID {book_id}")
            
            return new_isbn
            
        except Exception as e:
            logger.error(f"Error getting or assigning ISBN for book ID {book_id}: {e}")
            return None
    
    def search_assignments(self, query: str) -> List[ISBNAssignment]:
        """Search assignments by title, book ID, or ISBN"""
        try:
            query_lower = query.lower()
            results = []
            
            for assignment in self.assignments.values():
                if (query_lower in assignment.book_title.lower() or
                    query_lower in assignment.book_id.lower() or
                    query_lower in assignment.isbn.lower()):
                    results.append(assignment)
            
            return results
        except Exception as e:
            logger.error(f"Error searching assignments: {e}")
            return []    

    def import_schedule_from_csv(self, csv_file: str) -> Dict[str, Any]:
        """Import schedule from CSV with optional manual ISBN assignments"""
        try:
            import csv
            results = {
                'processed': 0,
                'assigned_manual': 0,
                'assigned_auto': 0,
                'updated': 0,
                'errors': []
            }
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    try:
                        book_title = row.get('title', '').strip()
                        book_id = row.get('book_id', '').strip()
                        scheduled_date = row.get('scheduled_date', '').strip()
                        manual_isbn = row.get('isbn', '').strip()  # Manual ISBN column
                        
                        if not all([book_title, book_id, scheduled_date]):
                            results['errors'].append(f"Row {row_num}: Missing required fields (title, book_id, scheduled_date)")
                            continue
                        
                        # Optional fields
                        imprint = row.get('imprint', '').strip()
                        publisher = row.get('publisher', '').strip()
                        format_type = row.get('format', 'paperback').strip()
                        priority = int(row.get('priority', 1))
                        notes = row.get('notes', '').strip()
                        
                        if manual_isbn:
                            # Manual ISBN provided - use assign_specific_isbn
                            if len(manual_isbn) != 13 or not manual_isbn.isdigit():
                                results['errors'].append(f"Row {row_num}: Invalid ISBN format '{manual_isbn}' - must be 13 digits")
                                continue
                            
                            success = self.assign_specific_isbn(
                                isbn=manual_isbn,
                                book_title=book_title,
                                book_id=book_id,
                                scheduled_date=scheduled_date,
                                imprint=imprint,
                                publisher=publisher,
                                format=format_type,
                                priority=priority,
                                notes=f"Manual assignment from schedule. {notes}".strip()
                            )
                            
                            if success:
                                results['assigned_manual'] += 1
                                logger.info(f"Manually assigned ISBN {manual_isbn} to '{book_title}' (ID: {book_id})")
                            else:
                                results['errors'].append(f"Row {row_num}: Failed to assign manual ISBN {manual_isbn} - may already be assigned")
                                continue
                        else:
                            # No manual ISBN - use get_or_assign (for rebuilds/auto-assignment)
                            isbn = self.get_or_assign_isbn(
                                book_id=book_id,
                                book_title=book_title,
                                scheduled_date=scheduled_date,
                                imprint=imprint,
                                publisher=publisher,
                                format=format_type,
                                priority=priority,
                                notes=f"Auto assignment from schedule. {notes}".strip()
                            )
                            
                            if isbn:
                                # Check if it was existing or new
                                assignment = self.get_assignment_by_book_id(book_id)
                                if assignment.assigned_date is not None:
                                    results['updated'] += 1
                                    logger.info(f"Updated existing assignment for '{book_title}' (ID: {book_id}) with ISBN {isbn}")
                                else:
                                    results['assigned_auto'] += 1
                                    logger.info(f"Auto-assigned new ISBN {isbn} to '{book_title}' (ID: {book_id})")
                            else:
                                results['errors'].append(f"Row {row_num}: Failed to assign ISBN - no available ISBNs")
                                continue
                        
                        results['processed'] += 1
                        
                    except Exception as e:
                        results['errors'].append(f"Row {row_num}: Error processing row - {str(e)}")
                        continue
            
            logger.info(f"Schedule import completed: {results['processed']} processed, "
                       f"{results['assigned_manual']} manual, {results['assigned_auto']} auto, "
                       f"{results['updated']} updated, {len(results['errors'])} errors")
            
            return results
            
        except Exception as e:
            logger.error(f"Error importing schedule from CSV: {e}")
            return {'processed': 0, 'assigned_manual': 0, 'assigned_auto': 0, 'updated': 0, 'errors': [str(e)]}
    
    def import_schedule_from_json(self, json_file: str) -> Dict[str, Any]:
        """Import schedule from JSON with optional manual ISBN assignments"""
        try:
            results = {
                'processed': 0,
                'assigned_manual': 0,
                'assigned_auto': 0,
                'updated': 0,
                'errors': []
            }
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both single object and array of objects
            if isinstance(data, dict):
                books = [data]
            elif isinstance(data, list):
                books = data
            else:
                raise ValueError("JSON must contain an object or array of objects")
            
            for idx, book in enumerate(books):
                try:
                    book_title = book.get('title', '').strip()
                    book_id = book.get('book_id', '').strip()
                    scheduled_date = book.get('scheduled_date', '').strip()
                    manual_isbn = book.get('isbn', '').strip()  # Manual ISBN field
                    
                    if not all([book_title, book_id, scheduled_date]):
                        results['errors'].append(f"Book {idx + 1}: Missing required fields (title, book_id, scheduled_date)")
                        continue
                    
                    # Optional fields
                    imprint = book.get('imprint', '').strip()
                    publisher = book.get('publisher', '').strip()
                    format_type = book.get('format', 'paperback').strip()
                    priority = int(book.get('priority', 1))
                    notes = book.get('notes', '').strip()
                    
                    if manual_isbn:
                        # Manual ISBN provided
                        if len(manual_isbn) != 13 or not manual_isbn.isdigit():
                            results['errors'].append(f"Book {idx + 1}: Invalid ISBN format '{manual_isbn}' - must be 13 digits")
                            continue
                        
                        success = self.assign_specific_isbn(
                            isbn=manual_isbn,
                            book_title=book_title,
                            book_id=book_id,
                            scheduled_date=scheduled_date,
                            imprint=imprint,
                            publisher=publisher,
                            format=format_type,
                            priority=priority,
                            notes=f"Manual assignment from schedule. {notes}".strip()
                        )
                        
                        if success:
                            results['assigned_manual'] += 1
                            logger.info(f"Manually assigned ISBN {manual_isbn} to '{book_title}' (ID: {book_id})")
                        else:
                            results['errors'].append(f"Book {idx + 1}: Failed to assign manual ISBN {manual_isbn}")
                            continue
                    else:
                        # Auto assignment
                        isbn = self.get_or_assign_isbn(
                            book_id=book_id,
                            book_title=book_title,
                            scheduled_date=scheduled_date,
                            imprint=imprint,
                            publisher=publisher,
                            format=format_type,
                            priority=priority,
                            notes=f"Auto assignment from schedule. {notes}".strip()
                        )
                        
                        if isbn:
                            assignment = self.get_assignment_by_book_id(book_id)
                            if assignment.assigned_date is not None:
                                results['updated'] += 1
                            else:
                                results['assigned_auto'] += 1
                        else:
                            results['errors'].append(f"Book {idx + 1}: Failed to assign ISBN")
                            continue
                    
                    results['processed'] += 1
                    
                except Exception as e:
                    results['errors'].append(f"Book {idx + 1}: Error processing - {str(e)}")
                    continue
            
            logger.info(f"JSON schedule import completed: {results['processed']} processed")
            return results
            
        except Exception as e:
            logger.error(f"Error importing schedule from JSON: {e}")
            return {'processed': 0, 'assigned_manual': 0, 'assigned_auto': 0, 'updated': 0, 'errors': [str(e)]}
    
    def export_schedule_template_csv(self, output_file: str) -> bool:
        """Export a CSV template for schedule imports"""
        try:
            import csv
            
            # Template with example data
            template_data = [
                {
                    'title': 'Example Book Title',
                    'book_id': 'example_book_1',
                    'scheduled_date': '2024-12-01',
                    'isbn': '9781234567890',  # Optional - leave empty for auto-assignment
                    'imprint': 'My Imprint',
                    'publisher': 'My Publisher',
                    'format': 'paperback',
                    'priority': '1',
                    'notes': 'Example notes'
                },
                {
                    'title': 'Another Book (Auto ISBN)',
                    'book_id': 'example_book_2',
                    'scheduled_date': '2024-12-15',
                    'isbn': '',  # Empty = auto-assign
                    'imprint': 'My Imprint',
                    'publisher': 'My Publisher',
                    'format': 'hardcover',
                    'priority': '2',
                    'notes': 'Will get auto-assigned ISBN'
                }
            ]
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=template_data[0].keys())
                writer.writeheader()
                writer.writerows(template_data)
            
            logger.info(f"Exported schedule template to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting schedule template: {e}")
            return False
    
    def export_schedule_template_json(self, output_file: str) -> bool:
        """Export a JSON template for schedule imports"""
        try:
            template_data = [
                {
                    "title": "Example Book Title",
                    "book_id": "example_book_1",
                    "scheduled_date": "2024-12-01",
                    "isbn": "9781234567890",
                    "imprint": "My Imprint",
                    "publisher": "My Publisher",
                    "format": "paperback",
                    "priority": 1,
                    "notes": "Example with manual ISBN"
                },
                {
                    "title": "Another Book (Auto ISBN)",
                    "book_id": "example_book_2",
                    "scheduled_date": "2024-12-15",
                    "isbn": "",
                    "imprint": "My Imprint",
                    "publisher": "My Publisher",
                    "format": "hardcover",
                    "priority": 2,
                    "notes": "Will get auto-assigned ISBN"
                }
            ]
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported JSON schedule template to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting JSON schedule template: {e}")
            return False