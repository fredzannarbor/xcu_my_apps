"""
Tests for the Error Recovery Manager module.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

import sys
sys.path.append(os.path.abspath('src'))

from codexes.modules.metadata.metadata_models import CodexMetadata
from codexes.modules.distribution.error_recovery_manager import ErrorRecoveryManager
from codexes.modules.verifiers.validation_framework import (
    ValidationResult, FieldValidationResult, ValidationSeverity
)


class TestErrorRecoveryManager(unittest.TestCase):
    """Test cases for the ErrorRecoveryManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.recovery_manager = ErrorRecoveryManager()
        
        # Create a test metadata object
        self.metadata = CodexMetadata(
            title="Test Book",
            isbn13="9781234567890",  # Invalid check digit
            author="Test Author",
            publisher="Test Publisher",
            list_price_usd=19.99,
            keywords="artificial intelligence, machine learning",
            summary_short="A book about AI and ML technologies"
        )
    
    def test_init(self):
        """Test initialization."""
        self.assertIsNotNone(self.recovery_manager)
        self.assertIsNotNone(self.recovery_manager.common_bisac_categories)
        self.assertIsNotNone(self.recovery_manager.territorial_multipliers)
        self.assertIsNotNone(self.recovery_manager.standard_discounts)
    
    def test_isbn_correction_valid_isbn13(self):
        """Test ISBN correction with valid ISBN-13."""
        valid_isbn = "9781234567897"  # Valid check digit
        result = self.recovery_manager.attempt_isbn_correction(valid_isbn)
        self.assertEqual(result, valid_isbn)
    
    def test_isbn_correction_invalid_isbn13(self):
        """Test ISBN correction with invalid ISBN-13 check digit."""
        invalid_isbn = "9781234567890"  # Invalid check digit
        result = self.recovery_manager.attempt_isbn_correction(invalid_isbn)
        self.assertNotEqual(result, invalid_isbn)
        self.assertEqual(len(result), 13)
    
    def test_isbn_correction_valid_isbn10(self):
        """Test ISBN correction with valid ISBN-10."""
        valid_isbn = "123456789X"  # Valid check digit
        result = self.recovery_manager.attempt_isbn_correction(valid_isbn)
        self.assertEqual(result, valid_isbn)
    
    def test_isbn_correction_invalid_isbn10(self):
        """Test ISBN correction with invalid ISBN-10 check digit."""
        invalid_isbn = "1234567890"  # Invalid check digit
        result = self.recovery_manager.attempt_isbn_correction(invalid_isbn)
        self.assertNotEqual(result, invalid_isbn)
        self.assertEqual(len(result), 10)
    
    def test_isbn_correction_with_formatting(self):
        """Test ISBN correction with hyphens and spaces."""
        formatted_isbn = "978-1-234-56789-0"  # Invalid check digit with formatting
        result = self.recovery_manager.attempt_isbn_correction(formatted_isbn)
        self.assertNotIn("-", result)
        self.assertNotIn(" ", result)
        self.assertEqual(len(result), 13)
    
    def test_suggest_bisac_codes_fiction(self):
        """Test BISAC code suggestion for fiction."""
        suggestions = self.recovery_manager.suggest_bisac_codes(
            "The Great Adventure", 
            "fiction, adventure, novel",
            "An exciting fictional story"
        )
        self.assertGreater(len(suggestions), 0)
        self.assertTrue(any('FIC' in code for code in suggestions))
    
    def test_suggest_bisac_codes_business(self):
        """Test BISAC code suggestion for business."""
        suggestions = self.recovery_manager.suggest_bisac_codes(
            "Leadership in the Digital Age",
            "business, leadership, management",
            "A guide to modern business leadership"
        )
        self.assertGreater(len(suggestions), 0)
        self.assertTrue(any('BUS' in code for code in suggestions))
    
    def test_calculate_missing_pricing_uk(self):
        """Test pricing calculation for UK."""
        result = self.recovery_manager.calculate_missing_pricing(20.0, 'UK')
        self.assertTrue(result.startswith('£'))
        self.assertIn('15.80', result)  # 20.0 * 0.79
    
    def test_calculate_missing_pricing_eu(self):
        """Test pricing calculation for EU."""
        result = self.recovery_manager.calculate_missing_pricing(20.0, 'EU')
        self.assertTrue(result.startswith('€'))
        self.assertIn('17.00', result)  # 20.0 * 0.85
    
    def test_get_standard_discount(self):
        """Test getting standard discount percentages."""
        self.assertEqual(self.recovery_manager.get_standard_discount('US'), '40%')
        self.assertEqual(self.recovery_manager.get_standard_discount('UK'), '40%')
        self.assertEqual(self.recovery_manager.get_standard_discount('USBR1'), '55%')  # Brazil
        self.assertEqual(self.recovery_manager.get_standard_discount('SIBI-EDUC-US'), '20%')  # Educational
        self.assertEqual(self.recovery_manager.get_standard_discount('UNKNOWN'), '40%')  # Default
    
    def test_generate_default_contributor_info(self):
        """Test generating default contributor information."""
        result = self.recovery_manager.generate_default_contributor_info("John Doe", "Test Book")
        
        self.assertIsInstance(result, dict)
        self.assertIn('contributor_one_bio', result)
        self.assertIn('contributor_one_role', result)
        self.assertIn('contributor_one_location', result)
        
        self.assertIn("John Doe", result['contributor_one_bio'])
        self.assertIn("Test Book", result['contributor_one_bio'])
        self.assertEqual(result['contributor_one_role'], 'Author')
        self.assertEqual(result['contributor_one_location'], 'United States')
    
    def test_recover_from_validation_errors_no_errors(self):
        """Test recovery when there are no blocking errors."""
        validation_result = ValidationResult(
            is_valid=True,
            field_results=[],
            errors=[],
            warnings=[]
        )
        
        result = self.recovery_manager.recover_from_validation_errors(self.metadata, validation_result)
        self.assertEqual(result, self.metadata)
    
    def test_recover_from_validation_errors_with_suggestions(self):
        """Test recovery with field suggestions."""
        field_result = FieldValidationResult(
            field_name="isbn13",
            is_valid=False,
            severity=ValidationSeverity.ERROR,
            error_message="Invalid check digit",
            suggested_value="9781234567897"
        )
        
        validation_result = ValidationResult(
            is_valid=False,
            field_results=[field_result],
            errors=["Invalid ISBN"],
            warnings=[]
        )
        
        result = self.recovery_manager.recover_from_validation_errors(self.metadata, validation_result)
        self.assertEqual(result.isbn13, "9781234567897")
    
    def test_recover_from_validation_errors_isbn_correction(self):
        """Test recovery with ISBN correction."""
        # Store original ISBN for comparison
        original_isbn = self.metadata.isbn13
        
        validation_result = ValidationResult(
            is_valid=False,
            field_results=[],
            errors=["Invalid ISBN"],
            warnings=[]
        )
        
        result = self.recovery_manager.recover_from_validation_errors(self.metadata, validation_result)
        # ISBN should be corrected
        self.assertNotEqual(result.isbn13, original_isbn)
        self.assertEqual(len(result.isbn13), 13)
    
    def test_recover_from_validation_errors_bisac_suggestion(self):
        """Test recovery with BISAC code suggestion."""
        metadata = CodexMetadata(
            title="Artificial Intelligence Guide",
            author="AI Expert",
            keywords="AI, machine learning",
            bisac_codes=""  # Empty BISAC codes
        )
        
        validation_result = ValidationResult(
            is_valid=False,
            field_results=[],
            errors=["Missing BISAC codes"],
            warnings=[]
        )
        
        result = self.recovery_manager.recover_from_validation_errors(metadata, validation_result)
        self.assertNotEqual(result.bisac_codes, "")
        self.assertGreater(len(result.bisac_codes), 0)
    
    def test_recover_from_validation_errors_pricing_calculation(self):
        """Test recovery with pricing calculation."""
        metadata = CodexMetadata(
            title="Test Book",
            author="Test Author",
            list_price_usd=25.00,
            uk_suggested_list_price="",  # Empty UK price
            eu_suggested_list_price_mode2=""  # Empty EU price
        )
        
        validation_result = ValidationResult(
            is_valid=False,
            field_results=[],
            errors=["Missing territorial pricing"],
            warnings=[]
        )
        
        result = self.recovery_manager.recover_from_validation_errors(metadata, validation_result)
        self.assertNotEqual(result.uk_suggested_list_price, "")
        self.assertIn("£", result.uk_suggested_list_price)
        self.assertNotEqual(result.eu_suggested_list_price_mode2, "")
        self.assertIn("€", result.eu_suggested_list_price_mode2)
    
    def test_get_recovery_suggestions(self):
        """Test getting recovery suggestions."""
        field_result = FieldValidationResult(
            field_name="isbn13",
            is_valid=False,
            severity=ValidationSeverity.ERROR,
            error_message="Invalid ISBN format"
        )
        
        validation_result = ValidationResult(
            is_valid=False,
            field_results=[field_result],
            errors=["Invalid ISBN"],
            warnings=[]
        )
        
        suggestions = self.recovery_manager.get_recovery_suggestions(validation_result)
        self.assertGreater(len(suggestions), 0)
        self.assertTrue(any("ISBN" in suggestion for suggestion in suggestions))


if __name__ == '__main__':
    unittest.main()