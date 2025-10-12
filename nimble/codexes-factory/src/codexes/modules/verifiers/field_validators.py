# src/codexes/modules/verifiers/field_validators.py

import re
import os
import subprocess
from datetime import datetime, date
from typing import Any, List, Set, Optional
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .validation_framework import FieldValidator, FieldValidationResult, ValidationSeverity
from ..metadata.metadata_models import CodexMetadata


class ISBNValidator(FieldValidator):
    """Validator for ISBN format and check-digit validation"""
    
    def __init__(self):
        super().__init__("ISBNValidator")
        # ISBN-13 pattern: 978 or 979 prefix, followed by 9 digits, then check digit
        self.isbn13_pattern = re.compile(r'^97[89]\d{10}$')
        # ISBN-10 pattern: 9 digits followed by check digit (which can be X)
        self.isbn10_pattern = re.compile(r'^\d{9}[\dX]$')
    
    def can_validate(self, field_name: str) -> bool:
        """Only validate ISBN fields"""
        return field_name in ['isbn13', 'isbn10', 'parent_isbn']
    
    def validate(self, field_name: str, value: Any, metadata: CodexMetadata) -> FieldValidationResult:
        """Validate ISBN format and check digit"""
        if not value or not isinstance(value, str):
            return self._create_result(
                field_name, 
                True,  # Empty ISBN is valid (not required for all fields)
                ValidationSeverity.INFO,
                "ISBN field is empty"
            )
        
        # Clean the ISBN (remove spaces, hyphens)
        clean_isbn = re.sub(r'[\s\-]', '', str(value).upper())
        
        if field_name == 'isbn13' or (field_name == 'parent_isbn' and len(clean_isbn) == 13):
            return self._validate_isbn13(field_name, clean_isbn)
        elif field_name == 'isbn10' or (field_name == 'parent_isbn' and len(clean_isbn) == 10):
            return self._validate_isbn10(field_name, clean_isbn)
        else:
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Invalid ISBN length: {len(clean_isbn)}. Expected 10 or 13 digits."
            )
    
    def _validate_isbn13(self, field_name: str, isbn: str) -> FieldValidationResult:
        """Validate ISBN-13 format and check digit"""
        if len(isbn) != 13:
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Invalid ISBN length: {len(isbn)}. Expected 13 digits."
            )
        
        if not self.isbn13_pattern.match(isbn):
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Invalid ISBN-13 format: {isbn}. Must start with 978 or 979 and be 13 digits."
            )
        
        # Calculate check digit
        if not self._verify_isbn13_check_digit(isbn):
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Invalid ISBN-13 check digit: {isbn}",
                suggested_value=self._calculate_isbn13_check_digit(isbn[:-1])
            )
        
        return self._create_result(field_name, True, ValidationSeverity.INFO, "Valid ISBN-13")
    
    def _validate_isbn10(self, field_name: str, isbn: str) -> FieldValidationResult:
        """Validate ISBN-10 format and check digit"""
        if not self.isbn10_pattern.match(isbn):
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Invalid ISBN-10 format: {isbn}. Must be 10 characters (digits and optional X)."
            )
        
        # Calculate check digit
        if not self._verify_isbn10_check_digit(isbn):
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Invalid ISBN-10 check digit: {isbn}",
                suggested_value=self._calculate_isbn10_check_digit(isbn[:-1])
            )
        
        return self._create_result(field_name, True, ValidationSeverity.INFO, "Valid ISBN-10")
    
    def _verify_isbn13_check_digit(self, isbn: str) -> bool:
        """Verify ISBN-13 check digit using modulo 10 algorithm"""
        try:
            total = 0
            for i, digit in enumerate(isbn[:-1]):
                weight = 1 if i % 2 == 0 else 3
                total += int(digit) * weight
            
            check_digit = (10 - (total % 10)) % 10
            return check_digit == int(isbn[-1])
        except (ValueError, IndexError):
            return False
    
    def _verify_isbn10_check_digit(self, isbn: str) -> bool:
        """Verify ISBN-10 check digit using modulo 11 algorithm"""
        try:
            total = 0
            for i, char in enumerate(isbn[:-1]):
                total += int(char) * (10 - i)
            
            remainder = total % 11
            check_digit = (11 - remainder) % 11
            
            if check_digit == 10:
                return isbn[-1] == 'X'
            else:
                return isbn[-1] == str(check_digit)
        except (ValueError, IndexError):
            return False
    
    def _calculate_isbn13_check_digit(self, isbn_base: str) -> str:
        """Calculate correct ISBN-13 check digit"""
        try:
            total = 0
            for i, digit in enumerate(isbn_base):
                weight = 1 if i % 2 == 0 else 3
                total += int(digit) * weight
            
            check_digit = (10 - (total % 10)) % 10
            return isbn_base + str(check_digit)
        except (ValueError, IndexError):
            return isbn_base + "?"
    
    def _calculate_isbn10_check_digit(self, isbn_base: str) -> str:
        """Calculate correct ISBN-10 check digit"""
        try:
            total = 0
            for i, char in enumerate(isbn_base):
                total += int(char) * (10 - i)
            
            remainder = total % 11
            check_digit = (11 - remainder) % 11
            check_char = 'X' if check_digit == 10 else str(check_digit)
            return isbn_base + check_char
        except (ValueError, IndexError):
            return isbn_base + "?"


class PricingValidator(FieldValidator):
    """Validator for currency and discount validation"""
    
    def __init__(self):
        super().__init__("PricingValidator")
        # Currency patterns
        self.currency_patterns = {
            'usd': re.compile(r'^\$?\d+\.?\d{0,2}$'),
            'gbp': re.compile(r'^£?\d+\.?\d{0,2}$'),
            'eur': re.compile(r'^€?\d+\.?\d{0,2}$'),
            'cad': re.compile(r'^C?\$?\d+\.?\d{0,2}$'),
            'aud': re.compile(r'^A?\$?\d+\.?\d{0,2}$'),
        }
        # Discount pattern (percentage)
        self.discount_pattern = re.compile(r'^\d{1,2}\.?\d{0,2}%?$')
        
        # Valid discount ranges
        self.min_discount = 0.0
        self.max_discount = 100.0
        
        # Minimum price thresholds
        self.min_price = 0.01
        self.max_reasonable_price = 999.99
    
    def can_validate(self, field_name: str) -> bool:
        """Only validate pricing and discount fields"""
        pricing_fields = [
            'list_price_usd', 'us_suggested_list_price',
            'uk_suggested_list_price', 'eu_suggested_list_price_mode2',
            'au_suggested_list_price_mode2', 'ca_suggested_list_price_mode2',
            'gc_suggested_list_price_mode2', 'usbr1_suggested_list_price_mode2',
            'usde1_suggested_list_price_mode2', 'usru1_suggested_list_price_mode2',
            'uspl1_suggested_list_price_mode2', 'uskr1_suggested_list_price_mode2',
            'uscn1_suggested_list_price_mode2', 'usin1_suggested_list_price_mode2',
            'usjp2_suggested_list_price_mode2', 'uaeusd_suggested_list_price_mode2',
            'us_ingram_only_suggested_list_price_mode2', 'us_ingram_gap_suggested_list_price_mode2',
            'sibi_educ_us_suggested_list_price_mode2'
        ]
        
        discount_fields = [
            'us_wholesale_discount', 'uk_wholesale_discount_percent',
            'eu_wholesale_discount_percent_mode2', 'au_wholesale_discount_percent_mode2',
            'ca_wholesale_discount_percent_mode2', 'gc_wholesale_discount_percent_mode2',
            'usbr1_wholesale_discount_percent_mode2', 'usde1_wholesale_discount_percent_mode2',
            'usru1_wholesale_discount_percent_mode2', 'uspl1_wholesale_discount_percent_mode2',
            'uskr1_wholesale_discount_percent_mode2', 'uscn1_wholesale_discount_percent_mode2',
            'usin1_wholesale_discount_percent_mode2', 'usjp2_wholesale_discount_percent_mode2',
            'uaeusd_wholesale_discount_percent_mode2', 'us_ingram_only_wholesale_discount_percent_mode2',
            'us_ingram_gap_wholesale_discount_percent_mode2', 'sibi_educ_us_wholesale_discount_percent_mode2'
        ]
        
        return field_name in pricing_fields or field_name in discount_fields
    
    def validate(self, field_name: str, value: Any, metadata: CodexMetadata) -> FieldValidationResult:
        """Validate pricing or discount field"""
        if value is None or value == "":
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.INFO,
                "Pricing field is empty"
            )
        
        value_str = str(value).strip()
        
        if 'discount' in field_name:
            return self._validate_discount(field_name, value_str)
        else:
            return self._validate_price(field_name, value_str)
    
    def _validate_price(self, field_name: str, price_str: str) -> FieldValidationResult:
        """Validate price format and range"""
        # Extract numeric value
        numeric_price = self._extract_numeric_value(price_str)
        
        if numeric_price is None:
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Invalid price format: {price_str}. Expected format like '$19.95' or '19.95'"
            )
        
        # Check minimum price
        if numeric_price < self.min_price:
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Price too low: ${numeric_price:.2f}. Minimum price is ${self.min_price:.2f}"
            )
        
        # Check maximum reasonable price (warning only)
        if numeric_price > self.max_reasonable_price:
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.WARNING,
                f"Price seems high: ${numeric_price:.2f}. Please verify this is correct."
            )
        
        # Check for proper price formatting (no currency symbols)
        if not self._has_proper_price_format(price_str):
            suggested_format = f"{numeric_price:.2f}"
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.WARNING,
                f"Price format should be a number without currency symbols: {price_str}",
                suggested_value=suggested_format
            )
        
        return self._create_result(field_name, True, ValidationSeverity.INFO, f"Valid price: {price_str}")
    
    def _validate_discount(self, field_name: str, discount_str: str) -> FieldValidationResult:
        """Validate discount percentage format and range"""
        # Extract numeric value
        numeric_discount = self._extract_numeric_value(discount_str.rstrip('%'))
        
        if numeric_discount is None:
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Invalid discount format: {discount_str}. Expected format like '40%' or '40'"
            )
        
        # Check discount range
        if numeric_discount < self.min_discount:
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Discount too low: {numeric_discount}%. Minimum discount is {self.min_discount}%"
            )
        
        if numeric_discount > self.max_discount:
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Discount too high: {numeric_discount}%. Maximum discount is {self.max_discount}%"
            )
        
        # Check for proper percentage formatting
        if not discount_str.endswith('%'):
            # Format as integer if it's a whole number, otherwise as float
            if numeric_discount == int(numeric_discount):
                suggested_format = f"{int(numeric_discount)}%"
            else:
                suggested_format = f"{numeric_discount}%"
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.WARNING,
                f"Discount format should include %: {discount_str}",
                suggested_value=suggested_format
            )
        
        return self._create_result(field_name, True, ValidationSeverity.INFO, f"Valid discount: {discount_str}")
    
    def _extract_numeric_value(self, value_str: str) -> float:
        """Extract numeric value from price or discount string"""
        try:
            # Remove currency symbols and whitespace
            clean_value = re.sub(r'[£€$CAD\s]', '', value_str)
            return float(clean_value)
        except (ValueError, TypeError):
            return None
    
    def _has_proper_price_format(self, price_str: str) -> bool:
        """Check if price has proper format (positive number with up to 2 decimals, no currency symbol)"""
        # Valid price format: positive number with 0-2 decimal places, no currency symbols
        return re.match(r'^\d+(\.\d{1,2})?$', price_str) is not None


class DateValidator(FieldValidator):
    """Validator for publication and street dates with Tuesday preference"""
    
    def __init__(self):
        super().__init__("DateValidator")
        # Common date formats
        self.date_formats = [
            '%Y-%m-%d',      # 2024-03-15
            '%m/%d/%Y',      # 03/15/2024
            '%d/%m/%Y',      # 15/03/2024
            '%Y/%m/%d',      # 2024/03/15
            '%B %d, %Y',     # March 15, 2024
            '%b %d, %Y',     # Mar 15, 2024
            '%d %B %Y',      # 15 March 2024
            '%d %b %Y',      # 15 Mar 2024
        ]
    
    def can_validate(self, field_name: str) -> bool:
        """Only validate date fields"""
        date_fields = [
            'publication_date', 'street_date', 'copyright_year'
        ]
        return field_name in date_fields
    
    def validate(self, field_name: str, value: Any, metadata: CodexMetadata) -> FieldValidationResult:
        """Validate date format and check for Tuesday preference"""
        if not value:
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.INFO,
                "Date field is empty"
            )
        
        value_str = str(value).strip()
        
        # Special handling for copyright_year (just year)
        if field_name == 'copyright_year':
            return self._validate_year(field_name, value_str)
        
        # Parse the date
        parsed_date = self._parse_date(value_str)
        
        if parsed_date is None:
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Invalid date format: {value_str}. Expected formats: YYYY-MM-DD, MM/DD/YYYY, etc.",
                suggested_value="YYYY-MM-DD"
            )
        
        # Check if it's a Tuesday (US publishing standard) first
        is_tuesday = parsed_date.weekday() == 1  # Tuesday is weekday 1 (Monday is 0)
        
        # Check if date is in the future (for publication dates)
        today = date.today()
        is_future = parsed_date >= today
        
        if field_name in ['publication_date', 'street_date']:
            if not is_future and is_tuesday:
                return self._create_result(
                    field_name,
                    True,
                    ValidationSeverity.WARNING,
                    f"Date is in the past: {parsed_date}. Consider updating to a future date."
                )
            elif not is_future and not is_tuesday:
                return self._create_result(
                    field_name,
                    True,
                    ValidationSeverity.WARNING,
                    f"Date is in the past: {parsed_date}. Consider updating to a future date."
                )
            elif is_future and not is_tuesday:
                weekday_name = parsed_date.strftime('%A')
                # Find the next Tuesday
                days_until_tuesday = (1 - parsed_date.weekday()) % 7
                if days_until_tuesday == 0:
                    days_until_tuesday = 7
                
                from datetime import timedelta
                next_tuesday = parsed_date + timedelta(days=days_until_tuesday)
                
                return self._create_result(
                    field_name,
                    True,
                    ValidationSeverity.WARNING,
                    f"Publication date is {weekday_name}. Tuesday is the standard release day in US publishing.",
                    suggested_value=next_tuesday.strftime('%Y-%m-%d')
                )
        
        # If we get here, it's either a valid Tuesday or not a publication date field
        if is_tuesday:
            return self._create_result(
                field_name, 
                True, 
                ValidationSeverity.INFO, 
                f"Valid publication date: {parsed_date} (Tuesday)"
            )
        else:
            # For non-publication date fields, just warn about Tuesday preference
            weekday_name = parsed_date.strftime('%A')
            from datetime import timedelta
            days_until_tuesday = (1 - parsed_date.weekday()) % 7
            if days_until_tuesday == 0:
                days_until_tuesday = 7
            next_tuesday = parsed_date + timedelta(days=days_until_tuesday)
            
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.WARNING,
                f"Date is {weekday_name}. Tuesday is the standard release day in US publishing.",
                suggested_value=next_tuesday.strftime('%Y-%m-%d')
            )
    
    def _validate_year(self, field_name: str, year_str: str) -> FieldValidationResult:
        """Validate year format and range"""
        try:
            year = int(year_str)
            current_year = datetime.now().year
            
            if year < 1900:
                return self._create_result(
                    field_name,
                    False,
                    ValidationSeverity.ERROR,
                    f"Year too early: {year}. Expected year >= 1900"
                )
            
            if year > current_year + 10:
                return self._create_result(
                    field_name,
                    True,
                    ValidationSeverity.WARNING,
                    f"Year seems far in the future: {year}. Please verify."
                )
            
            return self._create_result(field_name, True, ValidationSeverity.INFO, f"Valid year: {year}")
            
        except ValueError:
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Invalid year format: {year_str}. Expected 4-digit year like 2024"
            )
    
    def _parse_date(self, date_str: str) -> date:
        """Parse date string using multiple formats"""
        for date_format in self.date_formats:
            try:
                parsed = datetime.strptime(date_str, date_format)
                return parsed.date()
            except ValueError:
                continue
        return None


class BISACValidator(FieldValidator):
    """Validator for BISAC code verification"""
    
    def __init__(self):
        super().__init__("BISACValidator")
        # Common BISAC code patterns and categories
        self.bisac_pattern = re.compile(r'^[A-Z]{3}\d{6}$')
        
        # Common BISAC prefixes (this is a subset - in production you'd want the full list)
        self.valid_prefixes = {
            'ANT': 'Antiques & Collectibles',
            'ARC': 'Architecture',
            'ART': 'Art',
            'BIO': 'Biography & Autobiography',
            'BUS': 'Business & Economics',
            'COM': 'Computers',
            'CRA': 'Crafts & Hobbies',
            'DRA': 'Drama',
            'EDU': 'Education',
            'FAM': 'Family & Relationships',
            'FIC': 'Fiction',
            'FOR': 'Foreign Language Study',
            'GAM': 'Games & Activities',
            'GAR': 'Gardening',
            'HEA': 'Health & Fitness',
            'HIS': 'History',
            'HOU': 'House & Home',
            'HUM': 'Humor',
            'JUV': 'Juvenile Fiction',
            'JNF': 'Juvenile Nonfiction',
            'LAN': 'Language Arts & Disciplines',
            'LAW': 'Law',
            'LIT': 'Literary Collections',
            'LCO': 'Literary Criticism',
            'MAT': 'Mathematics',
            'MED': 'Medical',
            'MUS': 'Music',
            'NAT': 'Nature',
            'OCC': 'Body, Mind & Spirit',
            'PER': 'Performing Arts',
            'PET': 'Pets',
            'PHI': 'Philosophy',
            'PHO': 'Photography',
            'POE': 'Poetry',
            'POL': 'Political Science',
            'PSY': 'Psychology',
            'REF': 'Reference',
            'REL': 'Religion',
            'SCI': 'Science',
            'SEL': 'Self-Help',
            'SOC': 'Social Science',
            'SPO': 'Sports & Recreation',
            'STU': 'Study Aids',
            'TEC': 'Technology & Engineering',
            'TRA': 'Transportation',
            'TRU': 'True Crime',
            'TRV': 'Travel',
            'YAF': 'Young Adult Fiction',
            'YAN': 'Young Adult Nonfiction'
        }
    
    def can_validate(self, field_name: str) -> bool:
        """Only validate BISAC-related fields"""
        bisac_fields = [
            'bisac_codes', 'bisac_text'
        ]
        return field_name in bisac_fields
    
    def validate(self, field_name: str, value: Any, metadata: CodexMetadata) -> FieldValidationResult:
        """Validate BISAC codes format and categories"""
        if not value:
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.WARNING,
                "BISAC field is empty. Consider adding BISAC codes for better discoverability."
            )
        
        value_str = str(value).strip()
        
        if field_name == 'bisac_codes':
            return self._validate_bisac_codes(field_name, value_str)
        elif field_name == 'bisac_text':
            return self._validate_bisac_text(field_name, value_str)
        
        return self._create_result(field_name, True, ValidationSeverity.INFO, "BISAC field validated")
    
    def _validate_bisac_codes(self, field_name: str, codes_str: str) -> FieldValidationResult:
        """Validate BISAC codes format"""
        # Split by semicolon or comma
        codes = [code.strip() for code in re.split(r'[;,]', codes_str) if code.strip()]
        
        if not codes:
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.WARNING,
                "No BISAC codes found. Consider adding codes for better categorization."
            )
        
        invalid_codes = []
        unknown_prefixes = []
        
        for code in codes:
            # Check format
            if not self.bisac_pattern.match(code):
                invalid_codes.append(code)
                continue
            
            # Check prefix
            prefix = code[:3]
            if prefix not in self.valid_prefixes:
                unknown_prefixes.append(code)
        
        # Report invalid formats
        if invalid_codes:
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Invalid BISAC code format: {', '.join(invalid_codes)}. Expected format: ABC123456"
            )
        
        # Report unknown prefixes (warning only)
        if unknown_prefixes:
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.WARNING,
                f"Unknown BISAC prefixes: {', '.join(unknown_prefixes)}. Please verify these codes."
            )
        
        # Check count (LSI typically allows up to 3 BISAC codes)
        if len(codes) > 3:
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.WARNING,
                f"Many BISAC codes ({len(codes)}). LSI typically uses 1-3 primary codes."
            )
        
        return self._create_result(
            field_name, 
            True, 
            ValidationSeverity.INFO, 
            f"Valid BISAC codes: {len(codes)} codes found"
        )
    
    def _validate_bisac_text(self, field_name: str, text: str) -> FieldValidationResult:
        """Validate BISAC text descriptions"""
        if len(text.strip()) < 10:
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.WARNING,
                "BISAC text is very short. Consider adding more descriptive category text."
            )
        
        # Check for common BISAC category terms
        common_terms = [
            'fiction', 'nonfiction', 'biography', 'history', 'science', 
            'business', 'self-help', 'reference', 'education', 'health',
            'art', 'music', 'travel', 'cooking', 'religion', 'philosophy'
        ]
        
        text_lower = text.lower()
        found_terms = [term for term in common_terms if term in text_lower]
        
        if not found_terms:
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.WARNING,
                "BISAC text doesn't contain common category terms. Verify it matches your BISAC codes."
            )
        
        return self._create_result(
            field_name, 
            True, 
            ValidationSeverity.INFO, 
            f"Valid BISAC text with category terms: {', '.join(found_terms)}"
        )


class PDFValidator(FieldValidator):
    """Validator for PDF X-1a format checking and file validation"""
    
    def __init__(self, ftp_staging_path: str = "/ftp2lsi"):
        super().__init__("PDFValidator")
        self.ftp_staging_path = ftp_staging_path
        # Standard trim sizes (width x height in inches)
        self.standard_trim_sizes = {
            "5 x 8": (5.0, 8.0),
            "5.25 x 8": (5.25, 8.0),
            "5.5 x 8.5": (5.5, 8.5),
            "6 x 9": (6.0, 9.0),
            "6.14 x 9.21": (6.14, 9.21),  # A5
            "7 x 10": (7.0, 10.0),
            "7.5 x 9.25": (7.5, 9.25),
            "8 x 10": (8.0, 10.0),
            "8.25 x 11": (8.25, 11.0),
            "8.5 x 11": (8.5, 11.0),
        }
    
    def can_validate(self, field_name: str) -> bool:
        """Only validate PDF and file-related fields"""
        pdf_fields = [
            'interior_path_filename', 'cover_path_filename', 'jacket_path_filename',
            'trim_size', 'page_count', 'isbn13'  # ISBN13 for file naming validation
        ]
        return field_name in pdf_fields
    
    def validate(self, field_name: str, value: Any, metadata: CodexMetadata) -> FieldValidationResult:
        """Validate PDF files and related specifications"""
        if field_name in ['interior_path_filename', 'cover_path_filename', 'jacket_path_filename']:
            return self._validate_pdf_file(field_name, value, metadata)
        elif field_name == 'trim_size':
            return self._validate_trim_size(field_name, value, metadata)
        elif field_name == 'page_count':
            return self._validate_page_count(field_name, value, metadata)
        elif field_name == 'isbn13':
            return self._validate_file_naming_convention(field_name, value, metadata)
        
        return self._create_result(field_name, True, ValidationSeverity.INFO, "Field validated")
    
    def _validate_pdf_file(self, field_name: str, file_path: str, metadata: CodexMetadata) -> FieldValidationResult:
        """Validate PDF file existence, format, and specifications"""
        if not file_path:
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.WARNING,
                f"No file path specified for {field_name}"
            )
        
        # Check if file exists in FTP staging area
        full_path = os.path.join(self.ftp_staging_path, file_path)
        if not os.path.exists(full_path):
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"File not found in FTP staging area: {full_path}",
                suggested_value=f"Upload file to {self.ftp_staging_path}"
            )
        
        # Check file extension
        if not file_path.lower().endswith('.pdf'):
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"File must be PDF format: {file_path}"
            )
        
        # Validate file naming convention
        naming_result = self._check_file_naming_convention(field_name, file_path, metadata)
        if not naming_result.is_valid:
            return naming_result
        
        # Check PDF format (PDF X-1a)
        pdf_format_result = self._check_pdf_format(full_path, field_name)
        if not pdf_format_result.is_valid:
            return pdf_format_result
        
        # For interior files, validate page count and trim size consistency
        if field_name == 'interior_path_filename':
            consistency_result = self._check_interior_consistency(full_path, metadata)
            if not consistency_result.is_valid:
                return consistency_result
        
        # If PDF format check returned a warning, propagate that
        if pdf_format_result.severity == ValidationSeverity.WARNING:
            return pdf_format_result
        
        return self._create_result(
            field_name,
            True,
            ValidationSeverity.INFO,
            f"Valid PDF file: {file_path}"
        )
    
    def _check_file_naming_convention(self, field_name: str, file_path: str, metadata: CodexMetadata) -> FieldValidationResult:
        """Check if file follows LSI naming convention: ISBN_interior.pdf or ISBN_cover.pdf"""
        if not metadata.isbn13:
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.WARNING,
                "Cannot validate file naming convention without ISBN13"
            )
        
        expected_patterns = {
            'interior_path_filename': f"{metadata.isbn13}_interior.pdf",
            'cover_path_filename': f"{metadata.isbn13}_cover.pdf",
            'jacket_path_filename': f"{metadata.isbn13}_jacket.pdf"
        }
        
        if field_name in expected_patterns:
            expected_name = expected_patterns[field_name]
            file_name = os.path.basename(file_path)
            
            if file_name != expected_name:
                return self._create_result(
                    field_name,
                    False,
                    ValidationSeverity.ERROR,
                    f"File naming convention error. Expected: {expected_name}, Got: {file_name}",
                    suggested_value=expected_name
                )
        
        return self._create_result(field_name, True, ValidationSeverity.INFO, "File naming convention is correct")
    
    def _check_pdf_format(self, file_path: str, field_name: str) -> FieldValidationResult:
        """Check if PDF is in PDF X-1a format using external tools"""
        try:
            # Try to use pdfinfo (from poppler-utils) to check PDF version and format
            result = subprocess.run(
                ['pdfinfo', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return self._create_result(
                    field_name,
                    False,
                    ValidationSeverity.ERROR,
                    f"Cannot read PDF file: {file_path}. Error: {result.stderr}"
                )
            
            pdf_info = result.stdout
            
            # Check for PDF/X-1a compliance indicators
            # Note: This is a basic check - full PDF/X-1a validation requires specialized tools
            if 'PDF/X-1a' in pdf_info or 'PDFX1a' in pdf_info:
                return self._create_result(
                    field_name,
                    True,
                    ValidationSeverity.INFO,
                    "PDF appears to be PDF/X-1a compliant"
                )
            else:
                return self._create_result(
                    field_name,
                    True,
                    ValidationSeverity.WARNING,
                    "PDF format compliance cannot be verified. Ensure PDF is PDF/X-1a compliant for LSI submission."
                )
        
        except subprocess.TimeoutExpired:
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"PDF validation timed out for: {file_path}"
            )
        except FileNotFoundError:
            # pdfinfo not available - fall back to basic file validation
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.WARNING,
                "PDF format validation tools not available. Please verify PDF/X-1a compliance manually."
            )
        except Exception as e:
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Error validating PDF format: {str(e)}"
            )
    
    def _check_interior_consistency(self, file_path: str, metadata: CodexMetadata) -> FieldValidationResult:
        """Check if interior PDF page count and trim size match metadata"""
        try:
            # Get PDF page count using pdfinfo
            result = subprocess.run(
                ['pdfinfo', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                pdf_info = result.stdout
                
                # Extract page count from pdfinfo output
                for line in pdf_info.split('\n'):
                    if line.startswith('Pages:'):
                        pdf_page_count = int(line.split(':')[1].strip())
                        
                        # Compare with metadata page count
                        if metadata.page_count > 0 and pdf_page_count != metadata.page_count:
                            return self._create_result(
                                'interior_path_filename',
                                False,
                                ValidationSeverity.ERROR,
                                f"Page count mismatch: PDF has {pdf_page_count} pages, metadata specifies {metadata.page_count} pages"
                            )
                        break
                
                # Extract page size information if available
                page_size_info = self._extract_page_size_from_pdfinfo(pdf_info)
                if page_size_info and metadata.trim_size:
                    trim_match_result = self._check_trim_size_match(page_size_info, metadata.trim_size)
                    if not trim_match_result.is_valid:
                        return trim_match_result
            
            return self._create_result(
                'interior_path_filename',
                True,
                ValidationSeverity.INFO,
                "Interior PDF specifications are consistent with metadata"
            )
        
        except subprocess.TimeoutExpired:
            return self._create_result(
                'interior_path_filename',
                True,
                ValidationSeverity.WARNING,
                "PDF consistency check timed out"
            )
        except Exception as e:
            return self._create_result(
                'interior_path_filename',
                True,
                ValidationSeverity.WARNING,
                f"Cannot verify PDF consistency: {str(e)}"
            )
    
    def _extract_page_size_from_pdfinfo(self, pdf_info: str) -> Optional[tuple]:
        """Extract page size from pdfinfo output"""
        try:
            for line in pdf_info.split('\n'):
                if line.startswith('Page size:'):
                    # Example: "Page size:      432 x 648 pts (6 x 9 inches)"
                    if 'inches' in line:
                        inches_part = line.split('(')[1].split('inches')[0].strip()
                        dimensions = inches_part.split(' x ')
                        if len(dimensions) == 2:
                            width = float(dimensions[0].strip())
                            height = float(dimensions[1].strip())
                            return (width, height)
            return None
        except (ValueError, IndexError):
            return None
    
    def _check_trim_size_match(self, pdf_size: tuple, metadata_trim_size: str) -> FieldValidationResult:
        """Check if PDF page size matches metadata trim size"""
        pdf_width, pdf_height = pdf_size
        
        # Parse metadata trim size
        if metadata_trim_size in self.standard_trim_sizes:
            expected_width, expected_height = self.standard_trim_sizes[metadata_trim_size]
        else:
            # Try to parse custom trim size like "6.5 x 9.25"
            try:
                parts = metadata_trim_size.lower().replace('x', ' x ').split(' x ')
                if len(parts) == 2:
                    expected_width = float(parts[0].strip())
                    expected_height = float(parts[1].strip())
                else:
                    return self._create_result(
                        'trim_size',
                        True,
                        ValidationSeverity.WARNING,
                        f"Cannot parse trim size format: {metadata_trim_size}"
                    )
            except ValueError:
                return self._create_result(
                    'trim_size',
                    True,
                    ValidationSeverity.WARNING,
                    f"Cannot parse trim size: {metadata_trim_size}"
                )
        
        # Allow small tolerance for rounding (0.1 inch)
        tolerance = 0.1
        width_match = abs(pdf_width - expected_width) <= tolerance
        height_match = abs(pdf_height - expected_height) <= tolerance
        
        if not (width_match and height_match):
            return self._create_result(
                'trim_size',
                False,
                ValidationSeverity.ERROR,
                f"Trim size mismatch: PDF is {pdf_width} x {pdf_height} inches, metadata specifies {metadata_trim_size}"
            )
        
        return self._create_result(
            'trim_size',
            True,
            ValidationSeverity.INFO,
            f"Trim size matches: {pdf_width} x {pdf_height} inches"
        )
    
    def _validate_trim_size(self, field_name: str, trim_size: str, metadata: CodexMetadata) -> FieldValidationResult:
        """Validate trim size format and check against standard sizes"""
        if not trim_size:
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.WARNING,
                "Trim size not specified"
            )
        
        # Check if it's a standard trim size
        if trim_size in self.standard_trim_sizes:
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.INFO,
                f"Standard trim size: {trim_size}"
            )
        
        # Try to parse custom trim size
        try:
            parts = trim_size.lower().replace('x', ' x ').split(' x ')
            if len(parts) == 2:
                width = float(parts[0].strip())
                height = float(parts[1].strip())
                
                # Check reasonable dimensions
                if width < 3.0 or width > 12.0 or height < 4.0 or height > 15.0:
                    return self._create_result(
                        field_name,
                        True,
                        ValidationSeverity.WARNING,
                        f"Unusual trim size: {trim_size}. Please verify dimensions."
                    )
                
                return self._create_result(
                    field_name,
                    True,
                    ValidationSeverity.INFO,
                    f"Custom trim size: {width} x {height} inches"
                )
            else:
                return self._create_result(
                    field_name,
                    False,
                    ValidationSeverity.ERROR,
                    f"Invalid trim size format: {trim_size}. Expected format: '6 x 9' or '6.5 x 9.25'"
                )
        except ValueError:
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Cannot parse trim size: {trim_size}. Expected format: '6 x 9'"
            )
    
    def _validate_page_count(self, field_name: str, page_count: Any, metadata: CodexMetadata) -> FieldValidationResult:
        """Validate page count is reasonable and consistent"""
        if not page_count or page_count == 0:
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.WARNING,
                "Page count not specified"
            )
        
        try:
            pages = int(page_count)
            
            if pages < 1:
                return self._create_result(
                    field_name,
                    False,
                    ValidationSeverity.ERROR,
                    f"Invalid page count: {pages}. Must be at least 1 page."
                )
            
            if pages < 24:
                return self._create_result(
                    field_name,
                    True,
                    ValidationSeverity.WARNING,
                    f"Very short book: {pages} pages. LSI minimum is typically 24 pages."
                )
            
            if pages > 1000:
                return self._create_result(
                    field_name,
                    True,
                    ValidationSeverity.WARNING,
                    f"Very long book: {pages} pages. Please verify page count."
                )
            
            # Check if page count is even (standard for perfect binding)
            if pages % 2 != 0:
                return self._create_result(
                    field_name,
                    True,
                    ValidationSeverity.WARNING,
                    f"Odd page count: {pages}. Perfect bound books typically have even page counts."
                )
            
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.INFO,
                f"Valid page count: {pages} pages"
            )
        
        except (ValueError, TypeError):
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Invalid page count format: {page_count}. Expected integer."
            )
    
    def _validate_file_naming_convention(self, field_name: str, isbn13: str, metadata: CodexMetadata) -> FieldValidationResult:
        """Validate that file naming follows LSI convention when ISBN is provided"""
        if not isbn13:
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.INFO,
                "No ISBN provided for file naming validation"
            )
        
        # Check if corresponding files follow naming convention
        issues = []
        
        if metadata.interior_path_filename:
            expected_interior = f"{isbn13}_interior.pdf"
            actual_interior = os.path.basename(metadata.interior_path_filename)
            if actual_interior != expected_interior:
                issues.append(f"Interior file should be named: {expected_interior}")
        
        if metadata.cover_path_filename:
            expected_cover = f"{isbn13}_cover.pdf"
            actual_cover = os.path.basename(metadata.cover_path_filename)
            if actual_cover != expected_cover:
                issues.append(f"Cover file should be named: {expected_cover}")
        
        if metadata.jacket_path_filename:
            expected_jacket = f"{isbn13}_jacket.pdf"
            actual_jacket = os.path.basename(metadata.jacket_path_filename)
            if actual_jacket != expected_jacket:
                issues.append(f"Jacket file should be named: {expected_jacket}")
        
        if issues:
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"File naming convention issues: {'; '.join(issues)}"
            )
        
        return self._create_result(
            field_name,
            True,
            ValidationSeverity.INFO,
            "File naming convention is correct"
        )


class FileExistenceValidator(FieldValidator):
    """Validator for checking file existence in FTP staging area"""
    
    def __init__(self, ftp_staging_path: str = "/ftp2lsi"):
        super().__init__("FileExistenceValidator")
        self.ftp_staging_path = ftp_staging_path
    
    def can_validate(self, field_name: str) -> bool:
        """Only validate file path fields"""
        file_fields = [
            'interior_path_filename', 'cover_path_filename', 'jacket_path_filename',
            'cover_image_path', 'cover_thumbnail_path', 'marketing_image'
        ]
        return field_name in file_fields
    
    def validate(self, field_name: str, value: Any, metadata: CodexMetadata) -> FieldValidationResult:
        """Validate file existence in staging area"""
        if not value:
            return self._create_result(
                field_name,
                True,
                ValidationSeverity.INFO,
                f"No file path specified for {field_name}"
            )
        
        file_path = str(value).strip()
        
        # For FTP staging files, check in staging directory
        if field_name in ['interior_path_filename', 'cover_path_filename', 'jacket_path_filename']:
            full_path = os.path.join(self.ftp_staging_path, file_path)
        else:
            # For other files, use path as-is (might be relative to project root)
            full_path = file_path
        
        if not os.path.exists(full_path):
            severity = ValidationSeverity.ERROR if field_name.endswith('_filename') else ValidationSeverity.WARNING
            return self._create_result(
                field_name,
                False if severity == ValidationSeverity.ERROR else True,
                severity,
                f"File not found: {full_path}"
            )
        
        # Check if it's a file (not directory)
        if not os.path.isfile(full_path):
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Path exists but is not a file: {full_path}"
            )
        
        # Check file size (warn if very large or very small)
        try:
            file_size = os.path.getsize(full_path)
            
            if file_size == 0:
                return self._create_result(
                    field_name,
                    False,
                    ValidationSeverity.ERROR,
                    f"File is empty: {full_path}"
                )
            
            # Warn about very large files (>100MB)
            if file_size > 100 * 1024 * 1024:
                return self._create_result(
                    field_name,
                    True,
                    ValidationSeverity.WARNING,
                    f"Large file size: {file_size / (1024*1024):.1f}MB. Consider optimizing for upload."
                )
            
            # Warn about very small PDF files (<100KB)
            if field_name.endswith('_filename') and file_path.lower().endswith('.pdf') and file_size < 100 * 1024:
                return self._create_result(
                    field_name,
                    True,
                    ValidationSeverity.WARNING,
                    f"Small PDF file: {file_size / 1024:.1f}KB. Verify file integrity."
                )
        
        except OSError as e:
            return self._create_result(
                field_name,
                False,
                ValidationSeverity.ERROR,
                f"Cannot access file: {full_path}. Error: {str(e)}"
            )
        
        return self._create_result(
            field_name,
            True,
            ValidationSeverity.INFO,
            f"File exists: {full_path} ({file_size / 1024:.1f}KB)"
        )