"""
ISBN Integration Module - Consolidates all ISBN functionality for the Book Pipeline.

This module provides a unified interface to all ISBN-related functionality,
integrating the existing ISBN database with new scheduling features.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .isbn_database import ISBNDatabase, ISBN, ISBNStatus
from .schedule_isbn_manager import ScheduleISBNManager

logger = logging.getLogger(__name__)

class ISBNIntegration:
    """
    Unified ISBN management for the Book Pipeline.
    
    This class consolidates all ISBN functionality:
    - Uses existing ISBN database (data/isbn_database.json)
    - Provides scheduling capabilities
    - Integrates with book pipeline
    - Handles both manual and automatic assignment
    """
    
    def __init__(self, isbn_db_path: str = "data/isbn_database.json"):
        """Initialize with existing ISBN database"""
        self.isbn_db = ISBNDatabase(isbn_db_path)
        self.schedule_manager = ScheduleISBNManager(isbn_db_path)
        
        # Load database statistics
        self.stats = self.isbn_db.get_statistics()
        logger.info(f"Loaded ISBN database: {self.stats['total']} total, "
                   f"{self.stats['available']} available")
    
    def get_isbn_for_book(self, book_id: str, book_title: str, 
                         publisher_id: str = "nimble-books", 
                         manual_isbn: Optional[str] = None) -> Dict[str, Any]:
        """
        Get ISBN for a book - handles both manual and automatic assignment.
        
        This is the main method for the Book Pipeline to get ISBNs.
        
        Args:
            book_id: Unique book identifier
            book_title: Book title
            publisher_id: Publisher ID (defaults to nimble-books)
            manual_isbn: Optional manual ISBN to assign
            
        Returns:
            Dict with success, isbn, and details
        """
        try:
            # If manual ISBN provided, validate and assign it
            if manual_isbn:
                return self._assign_manual_isbn(manual_isbn, book_id, book_title, publisher_id)
            
            # Check if book already has an ISBN (for rebuilds)
            existing_isbn = self._find_existing_isbn(book_id)
            if existing_isbn:
                logger.info(f"Found existing ISBN {existing_isbn} for book {book_id}")
                return {
                    'success': True,
                    'isbn': existing_isbn,
                    'source': 'existing',
                    'message': f'Reusing existing ISBN {existing_isbn}'
                }
            
            # Assign new ISBN from available pool
            return self._assign_new_isbn(book_id, book_title, publisher_id)
            
        except Exception as e:
            logger.error(f"Error getting ISBN for book {book_id}: {e}")
            return {
                'success': False,
                'isbn': None,
                'error': str(e),
                'message': f'Failed to get ISBN: {e}'
            }
    
    def _assign_manual_isbn(self, isbn: str, book_id: str, book_title: str, 
                           publisher_id: str) -> Dict[str, Any]:
        """Assign a manually specified ISBN"""
        try:
            # Clean ISBN
            clean_isbn = isbn.replace('-', '').replace(' ', '')
            
            # Validate format
            if len(clean_isbn) != 13 or not clean_isbn.isdigit():
                return {
                    'success': False,
                    'isbn': None,
                    'error': 'Invalid ISBN format',
                    'message': f'ISBN must be 13 digits, got: {isbn}'
                }
            
            # Check if ISBN exists in database
            if clean_isbn not in self.isbn_db.isbns:
                return {
                    'success': False,
                    'isbn': None,
                    'error': 'ISBN not in database',
                    'message': f'ISBN {clean_isbn} not found in database'
                }
            
            # Check if ISBN is available
            isbn_obj = self.isbn_db.isbns[clean_isbn]
            if isbn_obj.status != ISBNStatus.AVAILABLE:
                return {
                    'success': False,
                    'isbn': None,
                    'error': 'ISBN not available',
                    'message': f'ISBN {clean_isbn} is {isbn_obj.status.value}'
                }
            
            # Assign the ISBN
            success = self.isbn_db.assign_isbn(clean_isbn, book_id)
            if success:
                logger.info(f"Manually assigned ISBN {clean_isbn} to {book_title}")
                return {
                    'success': True,
                    'isbn': clean_isbn,
                    'source': 'manual',
                    'message': f'Manually assigned ISBN {clean_isbn}'
                }
            else:
                return {
                    'success': False,
                    'isbn': None,
                    'error': 'Assignment failed',
                    'message': f'Failed to assign ISBN {clean_isbn}'
                }
                
        except Exception as e:
            logger.error(f"Error assigning manual ISBN {isbn}: {e}")
            return {
                'success': False,
                'isbn': None,
                'error': str(e),
                'message': f'Error assigning manual ISBN: {e}'
            }
    
    def _find_existing_isbn(self, book_id: str) -> Optional[str]:
        """Find existing ISBN for a book ID"""
        try:
            for isbn, isbn_obj in self.isbn_db.isbns.items():
                if isbn_obj.assigned_to == book_id:
                    return isbn
            return None
        except Exception as e:
            logger.error(f"Error finding existing ISBN for {book_id}: {e}")
            return None
    
    def _assign_new_isbn(self, book_id: str, book_title: str, 
                        publisher_id: str) -> Dict[str, Any]:
        """Assign a new ISBN from available pool"""
        try:
            # Find available ISBN
            available_isbn = None
            for isbn, isbn_obj in self.isbn_db.isbns.items():
                if (isbn_obj.status == ISBNStatus.AVAILABLE and 
                    isbn_obj.publisher_id == publisher_id):
                    available_isbn = isbn
                    break
            
            if not available_isbn:
                return {
                    'success': False,
                    'isbn': None,
                    'error': 'No available ISBNs',
                    'message': f'No available ISBNs found for publisher {publisher_id}'
                }
            
            # Assign the ISBN
            success = self.isbn_db.assign_isbn(available_isbn, book_id)
            if success:
                logger.info(f"Auto-assigned ISBN {available_isbn} to {book_title}")
                return {
                    'success': True,
                    'isbn': available_isbn,
                    'source': 'auto',
                    'message': f'Auto-assigned ISBN {available_isbn}'
                }
            else:
                return {
                    'success': False,
                    'isbn': None,
                    'error': 'Assignment failed',
                    'message': f'Failed to assign ISBN {available_isbn}'
                }
                
        except Exception as e:
            logger.error(f"Error assigning new ISBN for {book_id}: {e}")
            return {
                'success': False,
                'isbn': None,
                'error': str(e),
                'message': f'Error assigning new ISBN: {e}'
            }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get current database statistics"""
        raw_stats = self.isbn_db.get_statistics()
        
        # Convert to expected format for UI compatibility
        return {
            'total_isbns': raw_stats['total'],
            'available_count': raw_stats['available'],
            'assigned_count': raw_stats['privately_assigned'],
            'published_count': raw_stats['publicly_assigned'],
            'publicly_assigned_count': raw_stats['publicly_assigned'],
            'publishers': raw_stats['publishers'],
            'formats': raw_stats['formats']
        }
    
    def search_isbns(self, query: str) -> List[Dict[str, Any]]:
        """Search ISBNs by title, ISBN, or assigned book"""
        try:
            results = []
            query_lower = query.lower()
            
            for isbn, isbn_obj in self.isbn_db.isbns.items():
                if (query_lower in isbn.lower() or
                    (isbn_obj.title and query_lower in isbn_obj.title.lower()) or
                    (isbn_obj.assigned_to and query_lower in isbn_obj.assigned_to.lower())):
                    
                    results.append({
                        'isbn': isbn,
                        'title': isbn_obj.title or '',
                        'status': isbn_obj.status.value,
                        'assigned_to': isbn_obj.assigned_to or '',
                        'assignment_date': isbn_obj.assignment_date or '',
                        'publisher_id': isbn_obj.publisher_id,
                        'format': isbn_obj.format or ''
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching ISBNs: {e}")
            return []
    
    def release_isbn(self, isbn: str) -> bool:
        """Release an ISBN back to available pool"""
        try:
            return self.isbn_db.release_isbn(isbn)
        except Exception as e:
            logger.error(f"Error releasing ISBN {isbn}: {e}")
            return False
    
    def mark_as_published(self, isbn: str) -> bool:
        """Mark an ISBN as published"""
        try:
            return self.isbn_db.mark_as_published(isbn)
        except Exception as e:
            logger.error(f"Error marking ISBN {isbn} as published: {e}")
            return False
    
    def get_isbn_details(self, isbn: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an ISBN"""
        try:
            clean_isbn = isbn.replace('-', '').replace(' ', '')
            if clean_isbn in self.isbn_db.isbns:
                isbn_obj = self.isbn_db.isbns[clean_isbn]
                return {
                    'isbn': clean_isbn,
                    'title': isbn_obj.title or '',
                    'status': isbn_obj.status.value,
                    'assigned_to': isbn_obj.assigned_to or '',
                    'assignment_date': isbn_obj.assignment_date or '',
                    'publication_date': isbn_obj.publication_date or '',
                    'publisher_id': isbn_obj.publisher_id,
                    'format': isbn_obj.format or '',
                    'imprint': isbn_obj.imprint or '',
                    'notes': isbn_obj.notes or ''
                }
            return None
        except Exception as e:
            logger.error(f"Error getting ISBN details for {isbn}: {e}")
            return None

# Global instance for easy access
_isbn_integration = None

def get_isbn_integration() -> ISBNIntegration:
    """Get global ISBN integration instance"""
    global _isbn_integration
    if _isbn_integration is None:
        _isbn_integration = ISBNIntegration()
    return _isbn_integration