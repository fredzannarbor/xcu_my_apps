"""
ISBN formatter for proper hyphenation and validation on copyright pages.
"""

import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

try:
    from ..fixes.validation_system import ValidationSystem
except ImportError:
    logger.warning("ValidationSystem not available, using basic validation")


class ISBNFormatter:
    """Format ISBN-13 with proper hyphenation and check digit validation"""
    
    def __init__(self):
        """Initialize ISBN formatter with hyphenation rules"""
        try:
            self.validator = ValidationSystem()
        except NameError:
            self.validator = None
        # ISBN-13 hyphenation patterns for common prefixes
        # Format: prefix -> (group_length, publisher_length_ranges)
        self.hyphenation_rules = {
            '978': {
                '0': [(1, [(0, 19999), (20000, 69999), (70000, 84999), (85000, 89999), (90000, 94999), (95000, 99999)]),
                      (2, [(200000, 699999)]),
                      (3, [(7000000, 7999999)]),
                      (4, [(80000000, 94999999)]),
                      (5, [(950000000, 999999999)])],
                '1': [(1, [(0, 9999), (10000, 39999), (40000, 54999), (55000, 86999), (87000, 99999)]),
                      (2, [(100000, 399999)]),
                      (3, [(4000000, 5499999)]),
                      (4, [(55000000, 86999999)]),
                      (5, [(870000000, 998999999)])],
            },
            '979': {
                '10': [(2, [(0, 19999), (20000, 69999)]),
                       (3, [(700000, 899999)]),
                       (4, [(90000000, 94999999)]),
                       (5, [(950000000, 999999999)])],
            }
        }
    
    def validate_isbn_format(self, isbn: str) -> bool:
        """Validate ISBN format and check digit with comprehensive validation"""
        try:
            # Use comprehensive validation system if available
            if self.validator:
                validation_result = self.validator.validate_isbn_input(isbn)
                if not validation_result.is_valid:
                    logger.warning(f"ISBN validation failed: {validation_result.error_message}")
                    return False
                
                # Log any warnings
                for warning in validation_result.warnings:
                    logger.warning(f"ISBN validation warning: {warning}")
                
                return True
            
            # Fallback to basic validation
            return self._basic_isbn_validation(isbn)
            
        except Exception as e:
            logger.error(f"Error validating ISBN format: {e}")
            return False
    
    def _basic_isbn_validation(self, isbn: str) -> bool:
        """Basic ISBN validation when ValidationSystem is not available"""
        try:
            # Clean ISBN (remove hyphens and spaces)
            clean_isbn = re.sub(r'[-\s]', '', isbn)
            
            # Check length
            if len(clean_isbn) != 13:
                logger.warning(f"Invalid ISBN length: {len(clean_isbn)} (expected 13)")
                return False
            
            # Check if all digits
            if not clean_isbn.isdigit():
                logger.warning(f"ISBN contains non-digit characters: {isbn}")
                return False
            
            # Check prefix (must start with 978 or 979)
            if not (clean_isbn.startswith('978') or clean_isbn.startswith('979')):
                logger.warning(f"Invalid ISBN prefix: {clean_isbn[:3]} (expected 978 or 979)")
                return False
            
            # Validate check digit
            if not self._validate_check_digit(clean_isbn):
                logger.warning(f"Invalid ISBN check digit: {isbn}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in basic ISBN validation: {e}")
            return False
    
    def _validate_check_digit(self, isbn13: str) -> bool:
        """Validate ISBN-13 check digit using modulo 10 algorithm"""
        try:
            if len(isbn13) != 13:
                return False
            
            # Calculate check digit
            check_sum = 0
            for i, digit in enumerate(isbn13[:-1]):
                weight = 1 if i % 2 == 0 else 3
                check_sum += int(digit) * weight
            
            calculated_check_digit = (10 - (check_sum % 10)) % 10
            actual_check_digit = int(isbn13[-1])
            
            return calculated_check_digit == actual_check_digit
            
        except Exception as e:
            logger.error(f"Error validating check digit: {e}")
            return False
    
    def format_isbn_13_hyphenated(self, isbn13: str) -> str:
        """Format ISBN-13 with proper hyphenation rules"""
        try:
            # Clean ISBN
            clean_isbn = re.sub(r'[-\s]', '', isbn13)
            
            # Validate first
            if not self.validate_isbn_format(clean_isbn):
                logger.warning(f"Invalid ISBN format, returning as-is: {isbn13}")
                return isbn13
            
            # Extract components
            prefix = clean_isbn[:3]  # 978 or 979
            group = clean_isbn[3:4]  # Registration group (country/language)
            
            # Handle special case for 979-10 (France)
            if prefix == '979' and clean_isbn[3:5] == '10':
                group = clean_isbn[3:5]
                remaining = clean_isbn[5:-1]  # Publisher and title, excluding check digit
            else:
                remaining = clean_isbn[4:-1]  # Publisher and title, excluding check digit
            
            check_digit = clean_isbn[-1]
            
            # Apply hyphenation rules
            formatted = self._apply_hyphenation_rules(prefix, group, remaining, check_digit)
            
            if formatted:
                logger.info(f"Formatted ISBN: {isbn13} -> {formatted}")
                return formatted
            else:
                # Fallback to basic hyphenation
                return self._basic_hyphenation(clean_isbn)
                
        except Exception as e:
            logger.error(f"Error formatting ISBN: {e}")
            return isbn13  # Return original on error
    
    def _apply_hyphenation_rules(self, prefix: str, group: str, remaining: str, check_digit: str) -> Optional[str]:
        """Apply specific hyphenation rules based on prefix and group"""
        try:
            if prefix not in self.hyphenation_rules:
                return None
            
            if group not in self.hyphenation_rules[prefix]:
                return None
            
            rules = self.hyphenation_rules[prefix][group]
            remaining_int = int(remaining)
            
            # Find matching rule
            for publisher_length, ranges in rules:
                for range_start, range_end in ranges:
                    if range_start <= remaining_int <= range_end:
                        # Split remaining into publisher and title
                        publisher = remaining[:publisher_length]
                        title = remaining[publisher_length:]
                        
                        # Format with hyphens
                        return f"{prefix}-{group}-{publisher}-{title}-{check_digit}"
            
            return None
            
        except Exception as e:
            logger.error(f"Error applying hyphenation rules: {e}")
            return None
    
    def _basic_hyphenation(self, clean_isbn: str) -> str:
        """Apply basic hyphenation when specific rules are not available"""
        try:
            # Basic pattern: 978-X-XXXXXX-XX-X or 979-XX-XXXXX-XX-X
            if clean_isbn.startswith('978'):
                return f"{clean_isbn[:3]}-{clean_isbn[3]}-{clean_isbn[4:10]}-{clean_isbn[10:12]}-{clean_isbn[12]}"
            elif clean_isbn.startswith('979'):
                if clean_isbn[3:5] == '10':
                    return f"{clean_isbn[:3]}-{clean_isbn[3:5]}-{clean_isbn[5:10]}-{clean_isbn[10:12]}-{clean_isbn[12]}"
                else:
                    return f"{clean_isbn[:3]}-{clean_isbn[3]}-{clean_isbn[4:10]}-{clean_isbn[10:12]}-{clean_isbn[12]}"
            
            return clean_isbn
            
        except Exception as e:
            logger.error(f"Error in basic hyphenation: {e}")
            return clean_isbn
    
    def generate_copyright_page_isbn(self, isbn13: str) -> str:
        """Generate properly formatted ISBN for copyright page display"""
        try:
            formatted_isbn = self.format_isbn_13_hyphenated(isbn13)
            
            # Add "ISBN" prefix for copyright page display
            copyright_isbn = f"ISBN {formatted_isbn}"
            
            logger.info(f"Generated copyright page ISBN: {copyright_isbn}")
            return copyright_isbn
            
        except Exception as e:
            logger.error(f"Error generating copyright page ISBN: {e}")
            # Use comprehensive error handler
            try:
                from ..fixes.error_handler import handle_fix_error, FixComponentType, ErrorSeverity
                
                context = {'isbn': isbn13}
                return handle_fix_error(
                    FixComponentType.ISBN_FORMATTER, 
                    e, 
                    context, 
                    ErrorSeverity.MEDIUM
                )
            except ImportError:
                # Fallback if error handler not available
                return f"ISBN {isbn13}"
    
    def extract_isbn_components(self, isbn13: str) -> Dict[str, str]:
        """Extract ISBN components for analysis"""
        try:
            clean_isbn = re.sub(r'[-\s]', '', isbn13)
            
            if not self.validate_isbn_format(clean_isbn):
                return {}
            
            components = {
                'prefix': clean_isbn[:3],
                'full_isbn': clean_isbn,
                'check_digit': clean_isbn[-1]
            }
            
            # Handle group identification
            if clean_isbn.startswith('979') and clean_isbn[3:5] == '10':
                components['group'] = clean_isbn[3:5]
                components['publisher_title'] = clean_isbn[5:-1]
            else:
                components['group'] = clean_isbn[3:4]
                components['publisher_title'] = clean_isbn[4:-1]
            
            return components
            
        except Exception as e:
            logger.error(f"Error extracting ISBN components: {e}")
            return {}
    
    def batch_format_isbns(self, isbn_list: list) -> Dict[str, str]:
        """Format multiple ISBNs in batch"""
        try:
            results = {}
            
            for isbn in isbn_list:
                if isinstance(isbn, str) and isbn.strip():
                    formatted = self.format_isbn_13_hyphenated(isbn.strip())
                    results[isbn] = formatted
                else:
                    logger.warning(f"Skipping invalid ISBN: {isbn}")
            
            logger.info(f"Batch formatted {len(results)} ISBNs")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch ISBN formatting: {e}")
            return {}