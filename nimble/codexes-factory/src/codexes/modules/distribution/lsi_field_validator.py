#!/usr/bin/env python3

"""
Comprehensive LSI Field Validator

This module provides comprehensive validation for all LSI CSV fields according to
IngramSpark's Lightning Source Inc. (LSI) specifications and requirements.
"""

import re
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    field_name: str
    severity: ValidationSeverity
    message: str
    current_value: Any
    suggested_value: Optional[Any] = None
    rule_violated: Optional[str] = None


@dataclass
class FieldValidationResult:
    """Result of validating a single field."""
    field_name: str
    is_valid: bool
    value: Any
    issues: List[ValidationIssue]
    
    def add_issue(self, severity: ValidationSeverity, message: str, 
                 suggested_value: Any = None, rule_violated: str = None):
        """Add a validation issue."""
        issue = ValidationIssue(
            field_name=self.field_name,
            severity=severity,
            message=message,
            current_value=self.value,
            suggested_value=suggested_value,
            rule_violated=rule_violated
        )
        self.issues.append(issue)
        
        if severity == ValidationSeverity.ERROR:
            self.is_valid = False


@dataclass
class LSIValidationResult:
    """Complete LSI validation result."""
    is_valid: bool
    field_results: Dict[str, FieldValidationResult]
    error_count: int
    warning_count: int
    info_count: int
    
    def __post_init__(self):
        self.error_count = sum(1 for result in self.field_results.values() 
                              for issue in result.issues 
                              if issue.severity == ValidationSeverity.ERROR)
        self.warning_count = sum(1 for result in self.field_results.values() 
                                for issue in result.issues 
                                if issue.severity == ValidationSeverity.WARNING)
        self.info_count = sum(1 for result in self.field_results.values() 
                             for issue in result.issues 
                             if issue.severity == ValidationSeverity.INFO)
    
    def get_all_issues(self) -> List[ValidationIssue]:
        """Get all validation issues across all fields."""
        issues = []
        for result in self.field_results.values():
            issues.extend(result.issues)
        return issues
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get all issues of a specific severity."""
        return [issue for issue in self.get_all_issues() if issue.severity == severity]
    
    def get_failed_fields(self) -> List[str]:
        """Get list of field names that failed validation."""
        return [name for name, result in self.field_results.items() if not result.is_valid]


class LSIFieldValidator:
    """Comprehensive validator for LSI CSV fields."""
    
    def __init__(self):
        """Initialize the validator with LSI field rules."""
        self.field_rules = self._initialize_field_rules()
        self.bisac_codes = self._load_bisac_codes()
        self.country_codes = self._load_country_codes()
        self.currency_codes = self._load_currency_codes()
        self.language_codes = self._load_language_codes()
    
    def validate_all_fields(self, metadata: Dict[str, Any]) -> LSIValidationResult:
        """Validate all LSI fields in the metadata."""
        field_results = {}
        
        for field_name, value in metadata.items():
            if field_name in self.field_rules:
                field_results[field_name] = self.validate_field(field_name, value)
            else:
                # Unknown field - create warning
                result = FieldValidationResult(field_name, True, value, [])
                result.add_issue(
                    ValidationSeverity.WARNING,
                    f"Unknown LSI field: {field_name}",
                    rule_violated="UNKNOWN_FIELD"
                )
                field_results[field_name] = result
        
        # Check for missing required fields
        for field_name, rules in self.field_rules.items():
            if rules.get('required', False) and field_name not in metadata:
                result = FieldValidationResult(field_name, False, None, [])
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"Required field missing: {field_name}",
                    rule_violated="REQUIRED_FIELD_MISSING"
                )
                field_results[field_name] = result
        
        # Determine overall validation result
        is_valid = all(result.is_valid for result in field_results.values())
        
        return LSIValidationResult(is_valid, field_results, 0, 0, 0)
    
    def validate_field(self, field_name: str, value: Any) -> FieldValidationResult:
        """Validate a single field."""
        result = FieldValidationResult(field_name, True, value, [])
        
        if field_name not in self.field_rules:
            result.add_issue(
                ValidationSeverity.WARNING,
                f"Unknown field: {field_name}",
                rule_violated="UNKNOWN_FIELD"
            )
            return result
        
        rules = self.field_rules[field_name]
        
        # Check if field is required
        if rules.get('required', False) and (value is None or value == ''):
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Required field is empty",
                rule_violated="REQUIRED_FIELD_EMPTY"
            )
            return result
        
        # Skip validation for empty optional fields
        if value is None or value == '':
            return result
        
        # Convert value to string for validation
        str_value = str(value).strip()
        
        # Validate data type
        expected_type = rules.get('type', 'string')
        if not self._validate_type(str_value, expected_type):
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Invalid data type. Expected {expected_type}, got {type(value).__name__}",
                rule_violated="INVALID_TYPE"
            )
        
        # Validate length constraints
        min_length = rules.get('min_length')
        max_length = rules.get('max_length')
        
        if min_length and len(str_value) < min_length:
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Value too short. Minimum length: {min_length}, actual: {len(str_value)}",
                rule_violated="MIN_LENGTH_VIOLATION"
            )
        
        if max_length and len(str_value) > max_length:
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Value too long. Maximum length: {max_length}, actual: {len(str_value)}",
                suggested_value=str_value[:max_length],
                rule_violated="MAX_LENGTH_VIOLATION"
            )
        
        # Validate format patterns
        pattern = rules.get('pattern')
        if pattern and not re.match(pattern, str_value):
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Value does not match required pattern: {pattern}",
                rule_violated="PATTERN_MISMATCH"
            )
        
        # Validate allowed values
        allowed_values = rules.get('allowed_values')
        if allowed_values and str_value not in allowed_values:
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Value not in allowed list: {allowed_values}",
                suggested_value=self._suggest_closest_value(str_value, allowed_values),
                rule_violated="INVALID_VALUE"
            )
        
        # Field-specific validations
        self._validate_field_specific(field_name, str_value, result)
        
        return result
    
    def _validate_type(self, value: str, expected_type: str) -> bool:
        """Validate data type."""
        try:
            if expected_type == 'integer':
                int(value)
            elif expected_type == 'decimal':
                Decimal(value)
            elif expected_type == 'date':
                datetime.strptime(value, '%Y-%m-%d')
            elif expected_type == 'boolean':
                value.lower() in ['true', 'false', '1', '0', 'yes', 'no']
            # string type always passes
            return True
        except (ValueError, InvalidOperation):
            return False
    
    def _validate_field_specific(self, field_name: str, value: str, result: FieldValidationResult):
        """Perform field-specific validations."""
        
        # ISBN validation
        if 'isbn' in field_name.lower():
            self._validate_isbn(value, result)
        
        # BISAC code validation
        elif 'bisac' in field_name.lower():
            self._validate_bisac_code(value, result)
        
        # Price validation
        elif 'price' in field_name.lower():
            self._validate_price(value, result)
        
        # Date validation
        elif 'date' in field_name.lower():
            self._validate_date(value, result)
        
        # Country code validation
        elif 'country' in field_name.lower():
            self._validate_country_code(value, result)
        
        # Language code validation
        elif 'language' in field_name.lower():
            self._validate_language_code(value, result)
        
        # Age range validation
        elif 'age' in field_name.lower():
            self._validate_age_range(value, result)
        
        # Dimensions validation
        elif any(dim in field_name.lower() for dim in ['width', 'height', 'spine']):
            self._validate_dimension(value, result)
    
    def _validate_isbn(self, value: str, result: FieldValidationResult):
        """Validate ISBN format."""
        # Remove hyphens and spaces
        clean_isbn = re.sub(r'[-\s]', '', value)
        
        if len(clean_isbn) == 10:
            # ISBN-10 validation
            if not re.match(r'^\d{9}[\dX]$', clean_isbn):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "Invalid ISBN-10 format",
                    rule_violated="INVALID_ISBN_FORMAT"
                )
        elif len(clean_isbn) == 13:
            # ISBN-13 validation
            if not re.match(r'^\d{13}$', clean_isbn):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "Invalid ISBN-13 format",
                    rule_violated="INVALID_ISBN_FORMAT"
                )
            elif not clean_isbn.startswith(('978', '979')):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "ISBN-13 must start with 978 or 979",
                    rule_violated="INVALID_ISBN_PREFIX"
                )
        else:
            result.add_issue(
                ValidationSeverity.ERROR,
                "ISBN must be 10 or 13 digits",
                rule_violated="INVALID_ISBN_LENGTH"
            )
    
    def _validate_bisac_code(self, value: str, result: FieldValidationResult):
        """Validate BISAC code."""
        if not re.match(r'^[A-Z]{3}\d{6}$', value):
            result.add_issue(
                ValidationSeverity.ERROR,
                "BISAC code must be 3 letters followed by 6 digits (e.g., FIC014000)",
                rule_violated="INVALID_BISAC_FORMAT"
            )
        elif value not in self.bisac_codes:
            result.add_issue(
                ValidationSeverity.WARNING,
                f"BISAC code not found in current database: {value}",
                rule_violated="UNKNOWN_BISAC_CODE"
            )
    
    def _validate_price(self, value: str, result: FieldValidationResult):
        """Validate price format."""
        try:
            price = Decimal(value)
            if price < 0:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "Price cannot be negative",
                    rule_violated="NEGATIVE_PRICE"
                )
            elif price == 0:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "Price is zero - confirm this is intentional",
                    rule_violated="ZERO_PRICE"
                )
            elif price > 9999.99:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "Price seems unusually high",
                    rule_violated="HIGH_PRICE"
                )
            
            # Check decimal places
            if price.as_tuple().exponent < -2:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "Price must have at most 2 decimal places",
                    suggested_value=f"{price:.2f}",
                    rule_violated="EXCESSIVE_DECIMAL_PLACES"
                )
        except (ValueError, InvalidOperation):
            result.add_issue(
                ValidationSeverity.ERROR,
                "Invalid price format - must be a valid decimal number",
                rule_violated="INVALID_PRICE_FORMAT"
            )
    
    def _validate_date(self, value: str, result: FieldValidationResult):
        """Validate date format."""
        try:
            parsed_date = datetime.strptime(value, '%Y-%m-%d')
            
            # Check if date is reasonable
            current_year = datetime.now().year
            if parsed_date.year < 1900:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "Date seems too old - confirm accuracy",
                    rule_violated="OLD_DATE"
                )
            elif parsed_date.year > current_year + 2:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "Date is more than 2 years in the future",
                    rule_violated="FUTURE_DATE"
                )
        except ValueError:
            result.add_issue(
                ValidationSeverity.ERROR,
                "Invalid date format - must be YYYY-MM-DD",
                rule_violated="INVALID_DATE_FORMAT"
            )
    
    def _validate_country_code(self, value: str, result: FieldValidationResult):
        """Validate country code."""
        if len(value) != 2:
            result.add_issue(
                ValidationSeverity.ERROR,
                "Country code must be 2 characters (ISO 3166-1 alpha-2)",
                rule_violated="INVALID_COUNTRY_CODE_LENGTH"
            )
        elif value.upper() not in self.country_codes:
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Invalid country code: {value}",
                suggested_value=self._suggest_closest_value(value.upper(), self.country_codes),
                rule_violated="INVALID_COUNTRY_CODE"
            )
    
    def _validate_language_code(self, value: str, result: FieldValidationResult):
        """Validate language code."""
        if len(value) not in [2, 3]:
            result.add_issue(
                ValidationSeverity.ERROR,
                "Language code must be 2 or 3 characters (ISO 639)",
                rule_violated="INVALID_LANGUAGE_CODE_LENGTH"
            )
        elif value.lower() not in self.language_codes:
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Invalid language code: {value}",
                suggested_value=self._suggest_closest_value(value.lower(), self.language_codes),
                rule_violated="INVALID_LANGUAGE_CODE"
            )
    
    def _validate_age_range(self, value: str, result: FieldValidationResult):
        """Validate age range format."""
        # Expected formats: "8-12", "12+", "Adult"
        if value.lower() in ['adult', 'all ages']:
            return
        
        if '+' in value:
            # Format like "12+"
            try:
                age = int(value.replace('+', ''))
                if age < 0 or age > 18:
                    result.add_issue(
                        ValidationSeverity.WARNING,
                        "Age seems outside typical range (0-18)",
                        rule_violated="UNUSUAL_AGE_RANGE"
                    )
            except ValueError:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "Invalid age format for '+' notation",
                    rule_violated="INVALID_AGE_FORMAT"
                )
        elif '-' in value:
            # Format like "8-12"
            try:
                min_age, max_age = map(int, value.split('-'))
                if min_age >= max_age:
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        "Minimum age must be less than maximum age",
                        rule_violated="INVALID_AGE_RANGE_ORDER"
                    )
                if min_age < 0 or max_age > 18:
                    result.add_issue(
                        ValidationSeverity.WARNING,
                        "Age range seems outside typical range (0-18)",
                        rule_violated="UNUSUAL_AGE_RANGE"
                    )
            except ValueError:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "Invalid age range format - use 'min-max' format",
                    rule_violated="INVALID_AGE_FORMAT"
                )
        else:
            result.add_issue(
                ValidationSeverity.ERROR,
                "Age range must be in format 'min-max', 'age+', or 'Adult'",
                rule_violated="INVALID_AGE_FORMAT"
            )
    
    def _validate_dimension(self, value: str, result: FieldValidationResult):
        """Validate dimension format."""
        try:
            dimension = float(value)
            if dimension <= 0:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "Dimension must be positive",
                    rule_violated="NEGATIVE_DIMENSION"
                )
            elif dimension > 50:  # Reasonable upper limit in inches
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "Dimension seems unusually large - confirm units",
                    rule_violated="LARGE_DIMENSION"
                )
        except ValueError:
            result.add_issue(
                ValidationSeverity.ERROR,
                "Dimension must be a valid number",
                rule_violated="INVALID_DIMENSION_FORMAT"
            )
    
    def _suggest_closest_value(self, value: str, allowed_values: List[str]) -> Optional[str]:
        """Suggest the closest matching value from allowed values."""
        if not allowed_values:
            return None
        
        value_lower = value.lower()
        
        # Exact match (case insensitive)
        for allowed in allowed_values:
            if allowed.lower() == value_lower:
                return allowed
        
        # Partial match
        for allowed in allowed_values:
            if value_lower in allowed.lower() or allowed.lower() in value_lower:
                return allowed
        
        # Return first option as fallback
        return allowed_values[0]
    
    def _initialize_field_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize LSI field validation rules."""
        return {
            # Required fields
            'Title': {
                'required': True,
                'type': 'string',
                'min_length': 1,
                'max_length': 255
            },
            'ISBN': {
                'required': True,
                'type': 'string',
                'pattern': r'^\d{10}(\d{3})?$'
            },
            'List Price': {
                'required': True,
                'type': 'decimal',
                'min_value': 0
            },
            'Binding Type': {
                'required': True,
                'type': 'string',
                'allowed_values': ['Paperback', 'Hardcover', 'Spiral Bound']
            },
            'Trim Size': {
                'required': True,
                'type': 'string',
                'pattern': r'^\d+(\.\d+)?\s*x\s*\d+(\.\d+)?$'
            },
            'Page Count': {
                'required': True,
                'type': 'integer',
                'min_value': 1
            },
            'Interior Color': {
                'required': True,
                'type': 'string',
                'allowed_values': ['BW', 'Color']
            },
            'Paper Color': {
                'required': True,
                'type': 'string',
                'allowed_values': ['White', 'Cream']
            },
            
            # Optional but important fields
            'Subtitle': {
                'required': False,
                'type': 'string',
                'max_length': 255
            },
            'Series Title': {
                'required': False,
                'type': 'string',
                'max_length': 255
            },
            'Volume Number': {
                'required': False,
                'type': 'integer',
                'min_value': 1
            },
            'Author': {
                'required': False,
                'type': 'string',
                'max_length': 255
            },
            'Author Role': {
                'required': False,
                'type': 'string',
                'allowed_values': ['Author', 'Editor', 'Translator', 'Illustrator']
            },
            'Publisher': {
                'required': False,
                'type': 'string',
                'max_length': 255
            },
            'Imprint': {
                'required': False,
                'type': 'string',
                'max_length': 255
            },
            'Publication Date': {
                'required': False,
                'type': 'date'
            },
            'Copyright Year': {
                'required': False,
                'type': 'integer',
                'min_value': 1900,
                'max_value': datetime.now().year + 1
            },
            'Language': {
                'required': False,
                'type': 'string',
                'max_length': 3
            },
            'Country of Publication': {
                'required': False,
                'type': 'string',
                'max_length': 2
            },
            'Short Description': {
                'required': False,
                'type': 'string',
                'max_length': 350
            },
            'Long Description': {
                'required': False,
                'type': 'string',
                'max_length': 4000
            },
            'BISAC Category': {
                'required': False,
                'type': 'string',
                'pattern': r'^[A-Z]{3}\d{6}$'
            },
            'BISAC Category 2': {
                'required': False,
                'type': 'string',
                'pattern': r'^[A-Z]{3}\d{6}$'
            },
            'BISAC Category 3': {
                'required': False,
                'type': 'string',
                'pattern': r'^[A-Z]{3}\d{6}$'
            },
            'Age Range From': {
                'required': False,
                'type': 'integer',
                'min_value': 0,
                'max_value': 18
            },
            'Age Range To': {
                'required': False,
                'type': 'integer',
                'min_value': 0,
                'max_value': 18
            },
            'US List Price': {
                'required': False,
                'type': 'decimal',
                'min_value': 0
            },
            'CA List Price': {
                'required': False,
                'type': 'decimal',
                'min_value': 0
            },
            'EU List Price': {
                'required': False,
                'type': 'decimal',
                'min_value': 0
            },
            'AU List Price': {
                'required': False,
                'type': 'decimal',
                'min_value': 0
            },
            'UK List Price': {
                'required': False,
                'type': 'decimal',
                'min_value': 0
            }
        }
    
    def _load_bisac_codes(self) -> List[str]:
        """Load valid BISAC codes."""
        # This would typically load from a file or database
        # For now, return a sample of common BISAC codes
        return [
            'FIC014000',  # Fiction / Historical
            'FIC019000',  # Fiction / Literary
            'FIC028000',  # Fiction / Science Fiction
            'FIC009000',  # Fiction / Fantasy
            'FIC022000',  # Fiction / Mystery & Detective
            'BIO001000',  # Biography & Autobiography / General
            'HIS036000',  # History / United States
            'SCI075000',  # Science / Physics
            'BUS071000',  # Business & Economics / Leadership
            'SEL027000',  # Self-Help / Personal Growth
            'REL006000',  # Religion / Christianity
            'POL000000',  # Political Science / General
            'PSY000000',  # Psychology / General
            'EDU000000',  # Education / General
            'MED000000',  # Medical / General
        ]
    
    def _load_country_codes(self) -> List[str]:
        """Load valid ISO country codes."""
        return [
            'US', 'CA', 'GB', 'AU', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE',
            'CH', 'AT', 'SE', 'NO', 'DK', 'FI', 'IE', 'PT', 'GR', 'PL',
            'CZ', 'HU', 'SK', 'SI', 'HR', 'BG', 'RO', 'LT', 'LV', 'EE',
            'JP', 'KR', 'CN', 'IN', 'BR', 'MX', 'AR', 'CL', 'CO', 'PE'
        ]
    
    def _load_currency_codes(self) -> List[str]:
        """Load valid ISO currency codes."""
        return [
            'USD', 'CAD', 'GBP', 'EUR', 'AUD', 'JPY', 'CHF', 'SEK',
            'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'BGN', 'RON', 'HRK'
        ]
    
    def _load_language_codes(self) -> List[str]:
        """Load valid ISO language codes."""
        return [
            'en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'sv', 'no', 'da',
            'fi', 'pl', 'cs', 'hu', 'sk', 'sl', 'hr', 'bg', 'ro', 'lt',
            'lv', 'et', 'el', 'tr', 'ru', 'uk', 'be', 'mk', 'sq', 'sr',
            'bs', 'mt', 'is', 'ga', 'cy', 'eu', 'ca', 'gl', 'oc', 'co',
            'zh', 'ja', 'ko', 'th', 'vi', 'id', 'ms', 'tl', 'hi', 'ur',
            'bn', 'ta', 'te', 'ml', 'kn', 'gu', 'pa', 'or', 'as', 'ne',
            'si', 'my', 'km', 'lo', 'ka', 'hy', 'az', 'kk', 'ky', 'uz',
            'tk', 'mn', 'bo', 'dz', 'ar', 'he', 'yi', 'fa', 'ps', 'sd',
            'am', 'ti', 'om', 'so', 'sw', 'rw', 'rn', 'ny', 'mg', 'st',
            'tn', 'ts', 've', 'xh', 'zu', 'af', 'nso', 'ss', 'nr', 'ng'
        ]


def validate_lsi_csv_data(csv_data: List[Dict[str, Any]]) -> List[LSIValidationResult]:
    """Validate a list of LSI CSV records."""
    validator = LSIFieldValidator()
    results = []
    
    for i, record in enumerate(csv_data):
        try:
            result = validator.validate_all_fields(record)
            results.append(result)
        except Exception as e:
            logger.error(f"Error validating record {i}: {e}")
            # Create error result
            error_result = LSIValidationResult(
                is_valid=False,
                field_results={},
                error_count=1,
                warning_count=0,
                info_count=0
            )
            results.append(error_result)
    
    return results


def generate_validation_report(validation_results: List[LSIValidationResult]) -> str:
    """Generate a comprehensive validation report."""
    lines = []
    lines.append("LSI CSV VALIDATION REPORT")
    lines.append("=" * 50)
    
    total_records = len(validation_results)
    valid_records = sum(1 for result in validation_results if result.is_valid)
    invalid_records = total_records - valid_records
    
    lines.append(f"Total Records: {total_records}")
    lines.append(f"Valid Records: {valid_records} ({valid_records/total_records:.1%})")
    lines.append(f"Invalid Records: {invalid_records} ({invalid_records/total_records:.1%})")
    lines.append("")
    
    # Summary statistics
    total_errors = sum(result.error_count for result in validation_results)
    total_warnings = sum(result.warning_count for result in validation_results)
    total_info = sum(result.info_count for result in validation_results)
    
    lines.append("ISSUE SUMMARY")
    lines.append("-" * 20)
    lines.append(f"Errors: {total_errors}")
    lines.append(f"Warnings: {total_warnings}")
    lines.append(f"Info: {total_info}")
    lines.append("")
    
    # Field-specific issues
    field_issues = {}
    for result in validation_results:
        for field_name, field_result in result.field_results.items():
            if not field_result.is_valid:
                if field_name not in field_issues:
                    field_issues[field_name] = 0
                field_issues[field_name] += 1
    
    if field_issues:
        lines.append("FIELDS WITH MOST ISSUES")
        lines.append("-" * 30)
        sorted_issues = sorted(field_issues.items(), key=lambda x: x[1], reverse=True)
        for field_name, count in sorted_issues[:10]:
            lines.append(f"{field_name}: {count} records")
        lines.append("")
    
    # Detailed issues for invalid records
    if invalid_records > 0:
        lines.append("DETAILED ISSUES")
        lines.append("-" * 20)
        for i, result in enumerate(validation_results):
            if not result.is_valid:
                lines.append(f"Record {i+1}:")
                for issue in result.get_all_issues():
                    if issue.severity == ValidationSeverity.ERROR:
                        lines.append(f"  ERROR: {issue.field_name} - {issue.message}")
                    elif issue.severity == ValidationSeverity.WARNING:
                        lines.append(f"  WARNING: {issue.field_name} - {issue.message}")
                lines.append("")
    
    return "\n".join(lines)