"""
Error Recovery Manager Module

This module provides functionality for handling and recovering from field completion errors.
It implements fallback strategies for failed completions and provides error logging and reporting.
"""

import re
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from ..metadata.metadata_models import CodexMetadata
from ..verifiers.validation_framework import ValidationResult, FieldValidationResult, ValidationSeverity

logger = logging.getLogger(__name__)


class ErrorRecoveryManager:
    """
    Manager for handling and recovering from field completion errors.
    
    This class provides functionality for handling errors during field completion,
    implementing fallback strategies, and providing error logging and reporting.
    """
    
    def __init__(self):
        """Initialize the error recovery manager."""
        # Load common BISAC categories for fallback
        self.common_bisac_categories = {
            'fiction': ['FIC000000', 'FIC028000', 'FIC019000', 'FIC022000'],
            'business': ['BUS000000', 'BUS007000', 'BUS071000', 'BUS008000'],
            'science': ['SCI000000', 'SCI034000', 'SCI055000', 'SCI027000'],
            'technology': ['TEC000000', 'TEC007000', 'TEC008000', 'TEC061000'],
            'computers': ['COM000000', 'COM014000', 'COM051000', 'COM021000'],
            'biography': ['BIO026000', 'BIO000000', 'BIO003000', 'BIO007000']
        }
        
        # Load territorial pricing multipliers
        self.territorial_multipliers = {
            'UK': 0.79,  # GBP
            'EU': 0.85,  # EUR
            'CA': 1.25,  # CAD
            'AU': 1.35,  # AUD
            'USJP2': 110.0,  # JPY
            'USBR1': 5.0,  # BRL
            'USPL1': 3.8,  # PLN
            'USRU1': 75.0,  # RUB
            'USCN1': 7.0,  # CNY
            'USIN1': 75.0,  # INR
            'USKR1': 1200.0,  # KRW
            'UAEUSD': 3.67  # AED
        }
        
        # Load standard discount percentages
        self.standard_discounts = {
            'US': '40%',
            'UK': '40%',
            'EU': '40%',
            'CA': '40%',
            'AU': '40%',
            'USJP2': '40%',
            'USBR1': '55%',  # Brazil typically has higher discounts
            'USPL1': '45%',  # Poland
            'USRU1': '45%',  # Russia
            'USCN1': '50%',  # China
            'USIN1': '45%',  # India
            'USKR1': '45%',  # Korea
            'UAEUSD': '45%',  # UAE
            'SIBI-EDUC-US': '20%'  # Educational discount is typically lower
        }
        
        logger.info("Error Recovery Manager initialized")
    
    def attempt_isbn_correction(self, isbn: str) -> str:
        """
        Attempt to correct an invalid ISBN.
        
        Args:
            isbn: ISBN string to correct
            
        Returns:
            Corrected ISBN string or original if correction fails
        """
        if not isbn:
            return isbn
        
        try:
            # Remove hyphens and spaces
            clean_isbn = isbn.replace("-", "").replace(" ", "")
            
            # Check if it's a valid ISBN-13
            if len(clean_isbn) == 13 and clean_isbn.isdigit():
                if self._validate_isbn13_check_digit(clean_isbn):
                    return clean_isbn
                else:
                    # Fix check digit
                    return self._calculate_isbn13_with_check_digit(clean_isbn[:12])
            
            # Check if it's a valid ISBN-10
            elif len(clean_isbn) == 10 and (clean_isbn[:9].isdigit() and (clean_isbn[9].isdigit() or clean_isbn[9].upper() == 'X')):
                if self._validate_isbn10_check_digit(clean_isbn):
                    return clean_isbn
                else:
                    # Fix check digit
                    return self._calculate_isbn10_with_check_digit(clean_isbn[:9])
            
            # Check if it's an ISBN-13 missing check digit
            elif len(clean_isbn) == 12 and clean_isbn.isdigit():
                return self._calculate_isbn13_with_check_digit(clean_isbn)
            
            # Check if it's an ISBN-10 missing check digit
            elif len(clean_isbn) == 9 and clean_isbn.isdigit():
                return self._calculate_isbn10_with_check_digit(clean_isbn)
            
            # If we can't correct it, return the original
            return isbn
            
        except Exception as e:
            logger.error(f"Error correcting ISBN {isbn}: {e}")
            return isbn
    
    def _validate_isbn13_check_digit(self, isbn: str) -> bool:
        """
        Validate the check digit of an ISBN-13.
        
        Args:
            isbn: ISBN-13 string
            
        Returns:
            True if check digit is valid, False otherwise
        """
        try:
            # Calculate check digit
            check_digit = int(isbn[-1])
            digits = [int(d) for d in isbn[:-1]]
            weighted_sum = sum(d if i % 2 == 0 else d * 3 for i, d in enumerate(digits))
            calculated_check = (10 - (weighted_sum % 10)) % 10
            return check_digit == calculated_check
        except (ValueError, IndexError):
            return False
    
    def _calculate_isbn13_with_check_digit(self, isbn_prefix: str) -> str:
        """
        Calculate the check digit for an ISBN-13 prefix.
        
        Args:
            isbn_prefix: First 12 digits of ISBN-13
            
        Returns:
            Complete ISBN-13 with check digit
        """
        try:
            # Ensure we have exactly 12 digits
            if len(isbn_prefix) > 12:
                isbn_prefix = isbn_prefix[:12]
            elif len(isbn_prefix) < 12:
                # Pad with zeros if needed
                isbn_prefix = isbn_prefix.ljust(12, '0')
            
            # Calculate check digit
            digits = [int(d) for d in isbn_prefix]
            weighted_sum = sum(d if i % 2 == 0 else d * 3 for i, d in enumerate(digits))
            check_digit = (10 - (weighted_sum % 10)) % 10
            
            return isbn_prefix + str(check_digit)
        except Exception as e:
            logger.error(f"Error calculating ISBN-13 check digit: {e}")
            return isbn_prefix + "0"  # Fallback
    
    def _validate_isbn10_check_digit(self, isbn: str) -> bool:
        """
        Validate the check digit of an ISBN-10.
        
        Args:
            isbn: ISBN-10 string
            
        Returns:
            True if check digit is valid, False otherwise
        """
        try:
            # Calculate check digit
            check_char = isbn[-1].upper()
            check_digit = 10 if check_char == 'X' else int(check_char)
            
            digits = [int(d) for d in isbn[:9]]
            weighted_sum = sum((10 - i) * d for i, d in enumerate(digits))
            calculated_check = (11 - (weighted_sum % 11)) % 11
            calculated_char = 'X' if calculated_check == 10 else str(calculated_check)
            
            return check_char == calculated_char
        except (ValueError, IndexError):
            return False
    
    def _calculate_isbn10_with_check_digit(self, isbn_prefix: str) -> str:
        """
        Calculate the check digit for an ISBN-10 prefix.
        
        Args:
            isbn_prefix: First 9 digits of ISBN-10
            
        Returns:
            Complete ISBN-10 with check digit
        """
        try:
            # Ensure we have exactly 9 digits
            if len(isbn_prefix) > 9:
                isbn_prefix = isbn_prefix[:9]
            elif len(isbn_prefix) < 9:
                # Pad with zeros if needed
                isbn_prefix = isbn_prefix.ljust(9, '0')
            
            # Calculate check digit
            digits = [int(d) for d in isbn_prefix]
            weighted_sum = sum((10 - i) * d for i, d in enumerate(digits))
            check_digit = (11 - (weighted_sum % 11)) % 11
            check_char = 'X' if check_digit == 10 else str(check_digit)
            
            return isbn_prefix + check_char
        except Exception as e:
            logger.error(f"Error calculating ISBN-10 check digit: {e}")
            return isbn_prefix + "0"  # Fallback
    
    def suggest_bisac_codes(self, title: str, keywords: str = "", description: str = "") -> List[str]:
        """
        Suggest BISAC codes based on title, keywords, and description.
        
        Args:
            title: Book title
            keywords: Book keywords
            description: Book description
            
        Returns:
            List of suggested BISAC codes
        """
        if not title and not keywords and not description:
            return []
        
        try:
            # Combine all text for analysis
            all_text = f"{title} {keywords} {description}".lower()
            
            # Check for specific keywords
            suggestions = []
            
            # Fiction categories
            if any(word in all_text for word in ['fiction', 'novel', 'story', 'stories']):
                if 'science fiction' in all_text or 'sci-fi' in all_text:
                    suggestions.append('FIC028000')  # FICTION / Science Fiction / General
                elif 'fantasy' in all_text:
                    suggestions.append('FIC009000')  # FICTION / Fantasy / General
                elif 'mystery' in all_text or 'detective' in all_text:
                    suggestions.append('FIC022000')  # FICTION / Mystery & Detective / General
                elif 'thriller' in all_text or 'suspense' in all_text:
                    suggestions.append('FIC031000')  # FICTION / Thrillers / General
                else:
                    suggestions.append('FIC000000')  # FICTION / General
            
            # Business categories
            if any(word in all_text for word in ['business', 'management', 'leadership', 'entrepreneur']):
                if 'leadership' in all_text:
                    suggestions.append('BUS071000')  # BUSINESS & ECONOMICS / Leadership
                elif 'marketing' in all_text:
                    suggestions.append('BUS043000')  # BUSINESS & ECONOMICS / Marketing / General
                elif 'finance' in all_text:
                    suggestions.append('BUS027000')  # BUSINESS & ECONOMICS / Finance / General
                else:
                    suggestions.append('BUS000000')  # BUSINESS & ECONOMICS / General
            
            # Technology categories
            if any(word in all_text for word in ['technology', 'tech', 'engineering']):
                if 'software' in all_text or 'programming' in all_text:
                    suggestions.append('COM051000')  # COMPUTERS / Programming / General
                elif 'artificial intelligence' in all_text or 'ai' in all_text or 'machine learning' in all_text:
                    suggestions.append('COM004000')  # COMPUTERS / Intelligence (AI) & Semantics
                else:
                    suggestions.append('TEC000000')  # TECHNOLOGY & ENGINEERING / General
            
            # Science categories
            if any(word in all_text for word in ['science', 'scientific', 'physics', 'chemistry', 'biology']):
                if 'physics' in all_text:
                    suggestions.append('SCI055000')  # SCIENCE / Physics / General
                elif 'chemistry' in all_text:
                    suggestions.append('SCI013000')  # SCIENCE / Chemistry / General
                elif 'biology' in all_text:
                    suggestions.append('SCI008000')  # SCIENCE / Life Sciences / Biology / General
                else:
                    suggestions.append('SCI000000')  # SCIENCE / General
            
            # Self-help categories
            if any(word in all_text for word in ['self-help', 'self help', 'personal growth', 'motivation']):
                if 'motivation' in all_text:
                    suggestions.append('SEL021000')  # SELF-HELP / Motivational & Inspirational
                else:
                    suggestions.append('SEL000000')  # SELF-HELP / General
            
            # Philosophy categories
            if any(word in all_text for word in ['philosophy', 'philosophical', 'ethics']):
                suggestions.append('PHI000000')  # PHILOSOPHY / General
            
            # History categories
            if any(word in all_text for word in ['history', 'historical']):
                suggestions.append('HIS000000')  # HISTORY / General
            
            # Biography categories
            if any(word in all_text for word in ['biography', 'memoir', 'autobiography']):
                suggestions.append('BIO000000')  # BIOGRAPHY & AUTOBIOGRAPHY / General
            
            # If no suggestions were made, use a fallback
            if not suggestions:
                suggestions.append('BIO026000')  # BIOGRAPHY & AUTOBIOGRAPHY / Personal Memoirs
            
            return suggestions[:3]  # Return up to 3 suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting BISAC codes: {e}")
            return ['BIO026000']  # Fallback code
    
    def calculate_missing_pricing(self, base_price_usd: float, territory: str) -> str:
        """
        Calculate missing territorial pricing based on US price.
        
        Args:
            base_price_usd: Base price in USD
            territory: Territory code (UK, EU, CA, AU, etc.)
            
        Returns:
            Formatted price string with currency symbol
        """
        if not base_price_usd or base_price_usd <= 0:
            return ""
        
        try:
            # Get multiplier for territory
            multiplier = self.territorial_multipliers.get(territory, 1.0)
            
            # Calculate price
            price = base_price_usd * multiplier
            
            # Format with appropriate currency symbol
            if territory == 'UK':
                return f"£{price:.2f}"
            elif territory == 'EU':
                return f"€{price:.2f}"
            elif territory == 'CA':
                return f"C${price:.2f}"
            elif territory == 'AU':
                return f"A${price:.2f}"
            elif territory in ['USJP2']:
                # No decimals for Yen
                return f"¥{int(price)}"
            elif territory in ['USBR1']:
                return f"R${price:.2f}"
            elif territory in ['USPL1']:
                return f"zł{price:.2f}"
            elif territory in ['USRU1']:
                return f"₽{price:.2f}"
            elif territory in ['USCN1']:
                return f"¥{price:.2f}"
            elif territory in ['USIN1']:
                return f"₹{price:.2f}"
            elif territory in ['USKR1']:
                return f"₩{int(price)}"
            elif territory in ['UAEUSD']:
                return f"د.إ{price:.2f}"
            else:
                return f"${price:.2f}"
                
        except Exception as e:
            logger.error(f"Error calculating price for territory {territory}: {e}")
            return f"${base_price_usd:.2f}"  # Fallback to USD
    
    def get_standard_discount(self, territory: str) -> str:
        """
        Get standard wholesale discount percentage for a territory.
        
        Args:
            territory: Territory code
            
        Returns:
            Discount percentage string
        """
        return self.standard_discounts.get(territory, '40%')
    
    def generate_default_contributor_info(self, author_name: str, book_title: str = "") -> Dict[str, str]:
        """
        Generate default contributor information.
        
        Args:
            author_name: Name of the author
            book_title: Title of the book
            
        Returns:
            Dictionary with contributor information
        """
        if not author_name:
            return {}
        
        try:
            # Create a basic bio
            if book_title:
                bio = f"{author_name} is the author of {book_title}. They are an accomplished writer with expertise in their field."
            else:
                bio = f"{author_name} is an accomplished author with expertise in their field."
            
            # Add some generic information
            bio += " Their work has been recognized for its clarity and insight."
            
            return {
                "contributor_one_bio": bio,
                "contributor_one_role": "Author",
                "contributor_one_location": "United States",
                "contributor_one_professional_position": "Writer",
                "contributor_one_affiliations": ""
            }
            
        except Exception as e:
            logger.error(f"Error generating contributor info: {e}")
            return {}
    
    def recover_from_validation_errors(self, metadata: CodexMetadata, validation_result: ValidationResult) -> CodexMetadata:
        """
        Attempt to recover from validation errors.
        
        Args:
            metadata: CodexMetadata object to fix
            validation_result: ValidationResult with errors
            
        Returns:
            Updated CodexMetadata object with fixes applied
        """
        if validation_result.is_valid:
            return metadata
        
        try:
            # Apply suggested values from field validation results
            for field_result in validation_result.field_results:
                if not field_result.is_valid and field_result.suggested_value:
                    field_name = field_result.field_name
                    if hasattr(metadata, field_name):
                        setattr(metadata, field_name, field_result.suggested_value)
                        logger.info(f"Applied suggested value for {field_name}: {field_result.suggested_value}")
            
            # Check for specific error types and apply fixes
            
            # Fix ISBN errors
            if any("ISBN" in error for error in validation_result.errors):
                if hasattr(metadata, 'isbn13') and metadata.isbn13:
                    corrected_isbn = self.attempt_isbn_correction(metadata.isbn13)
                    if corrected_isbn != metadata.isbn13:
                        metadata.isbn13 = corrected_isbn
                        logger.info(f"Corrected ISBN-13: {corrected_isbn}")
            
            # Fix missing BISAC codes
            if any("BISAC" in error for error in validation_result.errors) or not metadata.bisac_codes:
                if not metadata.bisac_codes:
                    suggested_codes = self.suggest_bisac_codes(
                        metadata.title, 
                        getattr(metadata, 'keywords', ''),
                        getattr(metadata, 'summary_short', '')
                    )
                    if suggested_codes:
                        metadata.bisac_codes = suggested_codes[0]
                        if len(suggested_codes) > 1 and not getattr(metadata, 'bisac_category_2', ''):
                            metadata.bisac_category_2 = suggested_codes[1]
                        if len(suggested_codes) > 2 and not getattr(metadata, 'bisac_category_3', ''):
                            metadata.bisac_category_3 = suggested_codes[2]
                        logger.info(f"Added suggested BISAC codes: {suggested_codes}")
            
            # Fix missing territorial pricing
            if any("pricing" in error.lower() for error in validation_result.errors):
                if hasattr(metadata, 'list_price_usd') and metadata.list_price_usd:
                    # Fix UK pricing
                    if not getattr(metadata, 'uk_suggested_list_price', ''):
                        uk_price = self.calculate_missing_pricing(metadata.list_price_usd, 'UK')
                        if uk_price:
                            metadata.uk_suggested_list_price = uk_price
                            logger.info(f"Added UK price: {uk_price}")
                    
                    # Fix EU pricing
                    if not getattr(metadata, 'eu_suggested_list_price_mode2', ''):
                        eu_price = self.calculate_missing_pricing(metadata.list_price_usd, 'EU')
                        if eu_price:
                            metadata.eu_suggested_list_price_mode2 = eu_price
                            logger.info(f"Added EU price: {eu_price}")
                    
                    # Fix CA pricing
                    if not getattr(metadata, 'ca_suggested_list_price_mode2', ''):
                        ca_price = self.calculate_missing_pricing(metadata.list_price_usd, 'CA')
                        if ca_price:
                            metadata.ca_suggested_list_price_mode2 = ca_price
                            logger.info(f"Added CA price: {ca_price}")
                    
                    # Fix AU pricing
                    if not getattr(metadata, 'au_suggested_list_price_mode2', ''):
                        au_price = self.calculate_missing_pricing(metadata.list_price_usd, 'AU')
                        if au_price:
                            metadata.au_suggested_list_price_mode2 = au_price
                            logger.info(f"Added AU price: {au_price}")
            
            # Fix missing contributor information
            if any("contributor" in error.lower() for error in validation_result.errors):
                if not getattr(metadata, 'contributor_one_bio', '') and hasattr(metadata, 'author'):
                    contributor_info = self.generate_default_contributor_info(
                        metadata.author, 
                        getattr(metadata, 'title', '')
                    )
                    for field, value in contributor_info.items():
                        if hasattr(metadata, field) and not getattr(metadata, field, ''):
                            setattr(metadata, field, value)
                            logger.info(f"Added {field}: {value[:50]}...")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error recovering from validation errors: {e}")
            return metadata
    
    def get_recovery_suggestions(self, validation_result: ValidationResult) -> List[str]:
        """
        Get suggestions for recovering from validation errors.
        
        Args:
            validation_result: ValidationResult with errors
            
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        try:
            # Check if there are blocking errors
            if validation_result.has_blocking_errors():
                suggestions.append("This metadata has blocking errors that must be fixed before submission to LSI.")
            
            # Add suggestions based on field validation results
            for field_result in validation_result.field_results:
                if not field_result.is_valid:
                    field_name = field_result.field_name
                    error_message = field_result.error_message
                    
                    # ISBN errors
                    if "isbn" in field_name.lower():
                        suggestions.append(f"Fix the ISBN format: {error_message}")
                        suggestions.append("ISBNs should be 13 digits starting with 978 or 979.")
                    
                    # Price errors
                    elif "price" in field_name.lower():
                        suggestions.append(f"Fix the price format: {error_message}")
                        suggestions.append("Prices should be decimal numbers with currency symbols.")
                    
                    # Date errors
                    elif "date" in field_name.lower():
                        suggestions.append(f"Fix the date format: {error_message}")
                        suggestions.append("Dates should be in YYYY-MM-DD format.")
                        suggestions.append("For Tuesday publication dates, consider using the next available Tuesday.")
                    
                    # BISAC errors
                    elif "bisac" in field_name.lower():
                        suggestions.append(f"Fix the BISAC code format: {error_message}")
                        suggestions.append("BISAC codes should be in the format ABC123456.")
                    
                    # File errors
                    elif "path" in field_name.lower() or "file" in field_name.lower():
                        suggestions.append(f"Fix the file path: {error_message}")
                        suggestions.append("Ensure files are uploaded to LSI via FTP before submission.")
                    
                    # General suggestion
                    else:
                        suggestions.append(f"Fix field '{field_name}': {error_message}")
            
            # Add general suggestions
            if not suggestions:
                suggestions.append("No specific suggestions available. Please review the validation errors.")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting recovery suggestions: {e}")
            return ["An error occurred while generating recovery suggestions."]