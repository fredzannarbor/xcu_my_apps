"""
Last verso page manager for adding Notes heading to blank pages.
"""

from typing import Dict, List, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


class LastVersoPageManager:
    """Manage last verso page formatting with Notes heading when blank"""
    
    def __init__(self, typography_manager=None):
        self.typography_manager = typography_manager
    
    def check_last_verso_blank(self, book_content: str) -> bool:
        """Check if the last verso page is blank"""
        try:
            # Split content into pages
            pages = book_content.split('\\newpage')
            
            if len(pages) < 2:
                return False
            
            # Get the last verso page (even-numbered page, 0-indexed)
            # In a book, verso pages are typically on the left (even page numbers)
            last_verso_index = len(pages) - 2 if len(pages) % 2 == 0 else len(pages) - 1
            
            if last_verso_index >= 0:
                last_verso_content = pages[last_verso_index].strip()
                
                # Check if page is effectively blank (only whitespace or minimal content)
                content_without_whitespace = re.sub(r'\s+', '', last_verso_content)
                
                # Consider blank if less than 50 characters of actual content
                return len(content_without_whitespace) < 50
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking last verso page: {e}")
            return False
    
    def add_notes_heading(self, page_content: str) -> str:
        """Add 'Notes' chapter heading to blank last verso page"""
        try:
            # Create Notes heading with proper chapter formatting
            notes_heading = self.format_notes_page()
            
            # If page is essentially blank, replace with Notes heading
            if page_content.strip():
                # Page has some content, append Notes heading
                return page_content + "\n\n" + notes_heading
            else:
                # Page is blank, use Notes heading as content
                return notes_heading
                
        except Exception as e:
            logger.error(f"Error adding notes heading: {e}")
            return page_content
    
    def format_notes_page(self) -> str:
        """Format Notes page with proper chapter heading styling"""
        try:
            # Create Notes page with chapter heading
            notes_content = []
            
            # Add chapter heading for Notes
            notes_content.append("\\chapter*{Notes}")
            notes_content.append("")
            
            # Add some instructional text
            notes_content.append("\\vspace{2em}")
            notes_content.append("")
            notes_content.append("\\textit{Use this space for additional notes, thoughts, and reflections.}")
            notes_content.append("")
            
            # Add ruled lines for writing (optional)
            notes_content.append("\\vspace{1em}")
            for i in range(20):  # Add 20 lines for writing
                notes_content.append("\\rule{\\textwidth}{0.4pt}")
                notes_content.append("\\vspace{0.8em}")
            
            return "\n".join(notes_content)
            
        except Exception as e:
            logger.error(f"Error formatting notes page: {e}")
            return "\\chapter*{Notes}\n\n\\textit{Use this space for notes and reflections.}"
    
    def validate_notes_page_position(self, book_structure: Dict[str, Any]) -> bool:
        """Validate Notes page is properly positioned as final verso"""
        try:
            pages = book_structure.get('pages', [])
            
            if not pages:
                return False
            
            # Find Notes page
            notes_page_index = None
            for i, page in enumerate(pages):
                if 'Notes' in page.get('content', '') and '\\chapter' in page.get('content', ''):
                    notes_page_index = i
                    break
            
            if notes_page_index is None:
                return True  # No Notes page found, which is okay
            
            # Check if Notes page is on a verso (left-hand, even-numbered page)
            # Page numbering starts at 1, so verso pages have even indices (0-based)
            is_verso = notes_page_index % 2 == 1  # Odd index = even page number = verso
            
            # Check if it's the last or second-to-last page
            is_near_end = notes_page_index >= len(pages) - 2
            
            return is_verso and is_near_end
            
        except Exception as e:
            logger.error(f"Error validating notes page position: {e}")
            return False
    
    def process_book_for_notes_page(self, book_content: str) -> str:
        """Process entire book to add Notes page if needed"""
        try:
            # Check if last verso page is blank
            if self.check_last_verso_blank(book_content):
                # Split into pages
                pages = book_content.split('\\newpage')
                
                # Find last verso page
                last_verso_index = len(pages) - 2 if len(pages) % 2 == 0 else len(pages) - 1
                
                if last_verso_index >= 0:
                    # Add Notes heading to last verso page
                    pages[last_verso_index] = self.add_notes_heading(pages[last_verso_index])
                    
                    # Rejoin pages
                    book_content = '\\newpage'.join(pages)
                    
                    logger.info("Added Notes heading to blank last verso page")
            
            return book_content
            
        except Exception as e:
            logger.error(f"Error processing book for notes page: {e}")
            return book_content
    
    def create_standalone_notes_page(self) -> str:
        """Create a standalone Notes page that can be inserted anywhere"""
        try:
            return self.format_notes_page()
        except Exception as e:
            logger.error(f"Error creating standalone notes page: {e}")
            return "\\chapter*{Notes}"
    
    def detect_blank_pages(self, book_content: str) -> List[int]:
        """Detect all blank pages in the book"""
        try:
            pages = book_content.split('\\newpage')
            blank_pages = []
            
            for i, page in enumerate(pages):
                content_without_whitespace = re.sub(r'\s+', '', page.strip())
                if len(content_without_whitespace) < 50:  # Consider blank if < 50 chars
                    blank_pages.append(i)
            
            return blank_pages
            
        except Exception as e:
            logger.error(f"Error detecting blank pages: {e}")
            return []