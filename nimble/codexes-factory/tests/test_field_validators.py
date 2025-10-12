# tests/test_field_validators.py

import pytest
from datetime import date, datetime
from unittest.mock import patch

from codexes.modules.verifiers.field_validators import (
    ISBNValidator,
    PricingValidator,
    DateValidator,
    BISACValidator
)
from codexes.modules.verifiers.validation_framework import ValidationSeverity
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestISBNValidator:
    """Test ISBNValidator class"""
    
    def setup_method(self):
        self.validator = ISBNValidator()
        self.metadata = CodexMetadata()
    
    def test_can_validate(self):
        assert self.validator.can_validate("isbn13") is True
        assert self.validator.can_validate("isbn10") is True
        assert self.validator.can_validate("parent_isbn") is True
        assert self.validator.can_validate("title") is False
    
    def test_empty_isbn(self):
        result = self.validator.validate("isbn13", "", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "empty" in result.message.lower()
    
    def test_valid_isbn13(self):
        # Valid ISBN-13: 978-0-13-235088-4
        result = self.validator.validate("isbn13", "9780132350884", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Valid ISBN-13" in result.message
    
    def test_valid_isbn13_with_formatting(self):
        # Test with hyphens and spaces
        result = self.validator.validate("isbn13", "978-0-13-235088-4", self.metadata)
        assert result.is_valid is True
    
    def test_invalid_isbn13_format(self):
        result = self.validator.validate("isbn13", "123456789", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Invalid ISBN length" in result.error_message
    
    def test_invalid_isbn13_check_digit(self):
        # Wrong check digit (should be 4, not 5)
        result = self.validator.validate("isbn13", "9780132350885", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Invalid ISBN-13 check digit" in result.error_message
        assert result.suggested_value == "9780132350884"
    
    def test_valid_isbn10(self):
        # Valid ISBN-10: 0-13-235088-2
        result = self.validator.validate("isbn10", "0132350882", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Valid ISBN-10" in result.message
    
    def test_valid_isbn10_with_x(self):
        # ISBN-10 with X check digit
        result = self.validator.validate("isbn10", "043942089X", self.metadata)
        assert result.is_valid is True
    
    def test_invalid_isbn10_format(self):
        result = self.validator.validate("isbn10", "12345", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Invalid ISBN-10 format" in result.error_message
    
    def test_invalid_isbn10_check_digit(self):
        # Wrong check digit (should be 2, not 3)
        result = self.validator.validate("isbn10", "0132350883", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Invalid ISBN-10 check digit" in result.error_message
        assert result.suggested_value == "0132350882"
    
    def test_parent_isbn_auto_detection(self):
        # Test that parent_isbn detects format automatically
        result13 = self.validator.validate("parent_isbn", "9780132350884", self.metadata)
        assert result13.is_valid is True
        
        result10 = self.validator.validate("parent_isbn", "0132350882", self.metadata)
        assert result10.is_valid is True
    
    def test_invalid_length(self):
        result = self.validator.validate("isbn13", "12345678", self.metadata)
        assert result.is_valid is False
        assert "Invalid ISBN length" in result.error_message


class TestPricingValidator:
    """Test PricingValidator class"""
    
    def setup_method(self):
        self.validator = PricingValidator()
        self.metadata = CodexMetadata()
    
    def test_can_validate(self):
        assert self.validator.can_validate("list_price_usd") is True
        assert self.validator.can_validate("us_suggested_list_price") is True
        assert self.validator.can_validate("us_wholesale_discount") is True
        assert self.validator.can_validate("uk_wholesale_discount_percent") is True
        assert self.validator.can_validate("title") is False
    
    def test_empty_price(self):
        result = self.validator.validate("list_price_usd", "", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "empty" in result.message.lower()
    
    def test_valid_numeric_price(self):
        result = self.validator.validate("list_price_usd", 19.95, self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Valid price" in result.message
    
    def test_valid_string_price(self):
        result = self.validator.validate("us_suggested_list_price", "$19.95", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "should be a number without currency symbols" in result.warning_message
        assert result.suggested_value == "19.95"
    
    def test_price_without_currency_symbol(self):
        result = self.validator.validate("us_suggested_list_price", "19.95", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Valid price" in result.info_message
    
    def test_invalid_price_format(self):
        result = self.validator.validate("list_price_usd", "invalid", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Invalid price format" in result.error_message
    
    def test_price_too_low(self):
        result = self.validator.validate("list_price_usd", 0.0, self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Price too low" in result.error_message
    
    def test_price_very_high(self):
        result = self.validator.validate("list_price_usd", 1500.0, self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "Price seems high" in result.warning_message
    
    def test_valid_discount_percentage(self):
        result = self.validator.validate("us_wholesale_discount", "40%", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Valid discount" in result.message
    
    def test_discount_without_percent_sign(self):
        result = self.validator.validate("us_wholesale_discount", "40", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "should include %" in result.warning_message
        assert result.suggested_value == "40%"
    
    def test_invalid_discount_format(self):
        result = self.validator.validate("us_wholesale_discount", "invalid", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Invalid discount format" in result.error_message
    
    def test_discount_too_low(self):
        result = self.validator.validate("us_wholesale_discount", "-5%", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Discount too low" in result.error_message
    
    def test_discount_too_high(self):
        result = self.validator.validate("us_wholesale_discount", "150%", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Discount too high" in result.error_message
    
    def test_international_currency_formats(self):
        # Test various currency formats - these should trigger warnings since prices should be numbers without symbols
        result_gbp = self.validator.validate("uk_suggested_list_price", "£15.99", self.metadata)
        assert result_gbp.is_valid is True
        assert result_gbp.severity == ValidationSeverity.WARNING
        assert "should be a number without currency symbols" in result_gbp.warning_message
        
        result_eur = self.validator.validate("eu_suggested_list_price_mode2", "€18.50", self.metadata)
        assert result_eur.is_valid is True
        assert result_eur.severity == ValidationSeverity.WARNING
        
        result_cad = self.validator.validate("ca_suggested_list_price_mode2", "C$25.00", self.metadata)
        assert result_cad.is_valid is True
        assert result_cad.severity == ValidationSeverity.WARNING


class TestDateValidator:
    """Test DateValidator class"""
    
    def setup_method(self):
        self.validator = DateValidator()
        self.metadata = CodexMetadata()
    
    def test_can_validate(self):
        assert self.validator.can_validate("publication_date") is True
        assert self.validator.can_validate("street_date") is True
        assert self.validator.can_validate("copyright_year") is True
        assert self.validator.can_validate("title") is False
    
    def test_empty_date(self):
        result = self.validator.validate("publication_date", "", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "empty" in result.message.lower()
    
    def test_valid_date_formats(self):
        # Test various date formats
        formats_to_test = [
            "2024-03-15",      # ISO format
            "03/15/2024",      # US format
            "15/03/2024",      # European format
            "March 15, 2024",  # Long format
            "Mar 15, 2024",    # Short format
        ]
        
        for date_str in formats_to_test:
            result = self.validator.validate("publication_date", date_str, self.metadata)
            # Note: Some might be Tuesday, some might not
            assert result.is_valid is True
    
    def test_invalid_date_format(self):
        result = self.validator.validate("publication_date", "invalid-date", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Invalid date format" in result.error_message
        assert result.suggested_value == "YYYY-MM-DD"
    
    @patch('src.codexes.modules.verifiers.field_validators.date')
    def test_past_date_warning(self, mock_date):
        # Mock today's date
        mock_date.today.return_value = date(2024, 6, 1)
        
        result = self.validator.validate("publication_date", "2024-01-01", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "Date is in the past" in result.warning_message
    
    def test_tuesday_publication_date(self):
        # August 5, 2025 is a Tuesday (future date)
        result = self.validator.validate("publication_date", "2025-08-05", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Tuesday" in result.message
    
    def test_non_tuesday_publication_date(self):
        # August 6, 2025 is a Wednesday (future date)
        result = self.validator.validate("publication_date", "2025-08-06", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "Wednesday" in result.warning_message
        assert "Tuesday is the standard release day" in result.warning_message
        assert result.suggested_value == "2025-08-12"  # Next Tuesday
    
    def test_valid_copyright_year(self):
        current_year = datetime.now().year
        result = self.validator.validate("copyright_year", str(current_year), self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert f"Valid year: {current_year}" in result.message
    
    def test_copyright_year_too_early(self):
        result = self.validator.validate("copyright_year", "1800", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Year too early" in result.error_message
    
    def test_copyright_year_far_future(self):
        far_future = datetime.now().year + 20
        result = self.validator.validate("copyright_year", str(far_future), self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "far in the future" in result.warning_message
    
    def test_invalid_copyright_year(self):
        result = self.validator.validate("copyright_year", "not-a-year", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Invalid year format" in result.error_message


class TestBISACValidator:
    """Test BISACValidator class"""
    
    def setup_method(self):
        self.validator = BISACValidator()
        self.metadata = CodexMetadata()
    
    def test_can_validate(self):
        assert self.validator.can_validate("bisac_codes") is True
        assert self.validator.can_validate("bisac_text") is True
        assert self.validator.can_validate("title") is False
    
    def test_empty_bisac_codes(self):
        result = self.validator.validate("bisac_codes", "", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "empty" in result.warning_message
        assert "discoverability" in result.warning_message
    
    def test_valid_bisac_codes(self):
        result = self.validator.validate("bisac_codes", "FIC000000;FIC019000", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "Valid BISAC codes" in result.message
    
    def test_invalid_bisac_code_format(self):
        result = self.validator.validate("bisac_codes", "INVALID;FIC000000", self.metadata)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.ERROR
        assert "Invalid BISAC code format" in result.error_message
        assert "INVALID" in result.error_message
    
    def test_unknown_bisac_prefix(self):
        result = self.validator.validate("bisac_codes", "XYZ123456", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "Unknown BISAC prefixes" in result.warning_message
        assert "XYZ123456" in result.warning_message
    
    def test_too_many_bisac_codes(self):
        codes = ";".join([f"FIC{i:06d}" for i in range(5)])  # 5 codes
        result = self.validator.validate("bisac_codes", codes, self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "Many BISAC codes" in result.warning_message
        assert "typically uses 1-3" in result.warning_message
    
    def test_bisac_codes_comma_separated(self):
        # Test comma separation instead of semicolon
        result = self.validator.validate("bisac_codes", "FIC000000,FIC019000", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
    
    def test_valid_bisac_text(self):
        text = "Fiction / General / Contemporary Fiction"
        result = self.validator.validate("bisac_text", text, self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "fiction" in result.message.lower()
    
    def test_short_bisac_text(self):
        result = self.validator.validate("bisac_text", "Fiction", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "very short" in result.warning_message
    
    def test_bisac_text_no_common_terms(self):
        result = self.validator.validate("bisac_text", "Unusual category description", self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.WARNING
        assert "doesn't contain common category terms" in result.warning_message
    
    def test_bisac_text_with_common_terms(self):
        text = "This is a science fiction novel about space travel and adventure"
        result = self.validator.validate("bisac_text", text, self.metadata)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.INFO
        assert "science" in result.message.lower()


class TestValidatorIntegration:
    """Test validators working together"""
    
    def test_all_validators_with_complete_metadata(self):
        """Test all validators with a complete metadata object"""
        metadata = CodexMetadata(
            title="Test Book",
            isbn13="9780132350884",
            isbn10="0132350882",
            publication_date="2024-03-12",  # Tuesday
            copyright_year="2024",
            list_price_usd=19.95,
            us_suggested_list_price="$19.95",
            us_wholesale_discount="40%",
            bisac_codes="FIC000000;FIC019000",
            bisac_text="Fiction / General / Contemporary Fiction"
        )
        
        validators = [
            ISBNValidator(),
            PricingValidator(),
            DateValidator(),
            BISACValidator()
        ]
        
        all_results = []
        for validator in validators:
            # Get all fields from metadata
            for field_name in dir(metadata):
                if not field_name.startswith('_') and validator.can_validate(field_name):
                    field_value = getattr(metadata, field_name)
                    result = validator.validate(field_name, field_value, metadata)
                    all_results.append(result)
        
        # Should have some results
        assert len(all_results) > 0
        
        # Count errors and warnings
        errors = [r for r in all_results if r.has_error]
        warnings = [r for r in all_results if r.has_warning]
        
        # With good data, should have no errors
        assert len(errors) == 0
        
        # Might have some warnings (that's OK)
        print(f"Found {len(warnings)} warnings in complete metadata test")
    
    def test_all_validators_with_problematic_metadata(self):
        """Test all validators with problematic metadata"""
        metadata = CodexMetadata(
            title="Test Book",
            isbn13="9780132350885",  # Wrong check digit
            publication_date="2024-03-13",  # Wednesday (not Tuesday)
            list_price_usd=0.0,  # Too low
            us_wholesale_discount="150%",  # Too high
            bisac_codes="INVALID123"  # Invalid format
        )
        
        validators = [
            ISBNValidator(),
            PricingValidator(),
            DateValidator(),
            BISACValidator()
        ]
        
        all_results = []
        for validator in validators:
            for field_name in dir(metadata):
                if not field_name.startswith('_') and validator.can_validate(field_name):
                    field_value = getattr(metadata, field_name)
                    result = validator.validate(field_name, field_value, metadata)
                    all_results.append(result)
        
        # Should have some results
        assert len(all_results) > 0
        
        # Count errors and warnings
        errors = [r for r in all_results if r.has_error]
        warnings = [r for r in all_results if r.has_warning]
        
        # With bad data, should have some errors
        assert len(errors) > 0
        
        print(f"Found {len(errors)} errors and {len(warnings)} warnings in problematic metadata test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])