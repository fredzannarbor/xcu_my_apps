"""
Tests for the LSI Field Completion Integration module.
"""

import os
import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

import sys
sys.path.append(os.path.abspath('src'))

from codexes.modules.metadata.metadata_models import CodexMetadata
from codexes.modules.distribution.field_mapping import (
    FieldMappingRegistry, DirectMappingStrategy, DefaultMappingStrategy, 
    ComputedMappingStrategy, MappingContext
)
from codexes.modules.distribution.lsi_field_completion_integration import (
    LSIFieldCompletionIntegrator, integrate_field_completion_with_lsi_generator
)
from codexes.modules.verifiers.validation_framework import (
    ValidationResult, FieldValidationResult, ValidationSeverity
)


class TestLSIFieldCompletionIntegration(unittest.TestCase):
    """Test cases for the LSIFieldCompletionIntegration class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test registry
        self.registry = FieldMappingRegistry()
        
        # Register some test strategies
        self.registry.register_strategy("Title", DirectMappingStrategy("title"))
        self.registry.register_strategy("ISBN or SKU", DirectMappingStrategy("isbn13"))
        self.registry.register_strategy("Publisher", DefaultMappingStrategy("Nimble Books LLC"))
        self.registry.register_strategy("Rendition /Booktype", DefaultMappingStrategy("Perfect Bound"))
        
        # Create a test metadata object
        self.metadata = CodexMetadata(
            title="Test Book",
            isbn13="9781234567890",
            author="Test Author",
            publisher="Test Publisher",
            summary_short="A short summary",
            summary_long="A longer summary with more details about the book"
        )
        
        # Mock the LLMFieldCompleter
        self.patcher = patch('src.codexes.modules.distribution.lsi_field_completion_integration.LLMFieldCompleter')
        self.mock_completer_class = self.patcher.start()
        self.mock_completer = MagicMock()
        self.mock_completer_class.return_value = self.mock_completer
        
        # Set up the mock completer to return the metadata unchanged
        self.mock_completer.complete_missing_fields.return_value = self.metadata
        
        # Create the integrator
        self.integrator = LSIFieldCompletionIntegrator()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.patcher.stop()
    
    def test_init(self):
        """Test initialization."""
        self.assertIsNotNone(self.integrator.field_completer)
        self.assertIsNotNone(self.integrator.error_recovery_manager)
    
    def test_complete_and_validate_metadata_success(self):
        """Test completing and validating metadata with success."""
        # Create a mock validation function that returns success
        mock_validation_func = MagicMock()
        mock_validation_func.return_value = ValidationResult(
            is_valid=True,
            field_results=[],
            errors=[],
            warnings=[]
        )
        
        # Call the method
        result = self.integrator.complete_and_validate_metadata(
            self.metadata, "Sample book content", mock_validation_func
        )
        
        # Check that the field completer was called
        self.mock_completer.complete_missing_fields.assert_called_once()
        
        # Check that validation was called
        mock_validation_func.assert_called_once()
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual(result["metadata"], self.metadata)
        self.assertIsNotNone(result["validation_result"])
    
    def test_complete_and_validate_metadata_failure(self):
        """Test completing and validating metadata with failure."""
        # Create a mock validation function that returns failure
        mock_validation_func = MagicMock()
        mock_validation_func.return_value = ValidationResult(
            is_valid=False,
            field_results=[
                FieldValidationResult(
                    field_name="isbn13",
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    error_message="Invalid ISBN",
                    suggested_value="9781234567897"
                )
            ],
            errors=["Invalid ISBN"],
            warnings=[]
        )
        
        # Mock the error recovery manager
        with patch.object(self.integrator.error_recovery_manager, 'recover_from_validation_errors') as mock_recover:
            # Set up the mock to return a fixed metadata
            fixed_metadata = CodexMetadata(
                title="Test Book",
                isbn13="9781234567897",  # Fixed ISBN
                author="Test Author",
                publisher="Test Publisher"
            )
            mock_recover.return_value = fixed_metadata
            
            # Set up the mock to return success on second validation
            mock_validation_func.side_effect = [
                ValidationResult(is_valid=False, field_results=[], errors=["Invalid ISBN"], warnings=[]),
                ValidationResult(is_valid=True, field_results=[], errors=[], warnings=[])
            ]
            
            # Call the method
            result = self.integrator.complete_and_validate_metadata(
                self.metadata, "Sample book content", mock_validation_func
            )
            
            # Check that recovery was attempted
            mock_recover.assert_called_once()
            
            # Check that validation was called twice
            self.assertEqual(mock_validation_func.call_count, 2)
            
            # Check the result
            self.assertTrue(result["success"])
            self.assertEqual(result["metadata"], fixed_metadata)
    
    def test_generate_field_completion_report(self):
        """Test generating field completion report."""
        # Mock the LSIFieldCompletionReporter
        with patch('src.codexes.modules.distribution.lsi_field_completion_integration.LSIFieldCompletionReporter') as mock_reporter_class:
            mock_reporter = MagicMock()
            mock_reporter_class.return_value = mock_reporter
            
            # Set up the mock to return some output files
            mock_reporter.generate_field_strategy_report.return_value = {
                "csv": "output/reports/test.csv",
                "html": "output/reports/test.html",
                "json": "output/reports/test.json"
            }
            
            # Call the method
            result = self.integrator.generate_field_completion_report(
                self.metadata, ["Title", "ISBN or SKU"], self.registry
            )
            
            # Check that the reporter was created
            mock_reporter_class.assert_called_once_with(self.registry)
            
            # Check that the report was generated
            mock_reporter.generate_field_strategy_report.assert_called_once()
            
            # Check the result
            self.assertEqual(len(result), 3)
            self.assertIn("csv", result)
            self.assertIn("html", result)
            self.assertIn("json", result)
    
    def test_integrate_field_completion_with_lsi_generator(self):
        """Test integrating field completion with LSI generator."""
        # Create a mock generator
        mock_generator = MagicMock()
        mock_generator.validate_metadata = MagicMock()
        mock_generator.get_lsi_headers = MagicMock(return_value=["Title", "ISBN or SKU"])
        mock_generator.field_registry = self.registry
        
        # Store the original generate_with_validation method
        original_generate = mock_generator.generate_with_validation
        
        # Call the integration function
        integrate_field_completion_with_lsi_generator(mock_generator)
        
        # Check that the integrator was stored in the generator
        self.assertTrue(hasattr(mock_generator, 'field_completion_integrator'))
        
        # Check that the generate_with_validation method was replaced
        self.assertNotEqual(mock_generator.generate_with_validation, original_generate)
        
        # Call the new generate_with_validation method
        mock_generator.generate_with_validation(self.metadata, "output/test.csv")
        
        # Check that the original method was called
        original_generate.assert_called_once()


if __name__ == '__main__':
    unittest.main()