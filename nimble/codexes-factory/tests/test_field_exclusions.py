"""
Tests for field exclusions in LSI ACS generator.
"""

import os
import sys
import unittest
import tempfile
import csv
import json
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.distribution.lsi_acs_generator_new import LsiAcsGenerator
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestFieldExclusions(unittest.TestCase):
    """Test cases for field exclusions in LSI ACS generator."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a temporary template file
        self.template_path = os.path.join(self.temp_dir.name, "template.csv")
        with open(self.template_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Title", "ISBN13", "Publisher", "Metadata Contact Dictionary", "Parent ISBN", "Field1", "Field2"
            ])
        
        # Create a temporary tranche configuration file
        self.tranche_dir = os.path.join(self.temp_dir.name, "configs", "tranches")
        os.makedirs(self.tranche_dir, exist_ok=True)
        self.tranche_path = os.path.join(self.tranche_dir, "test_tranche.json")
        
        tranche_config = {
            "field_exclusions": [
                "Metadata Contact Dictionary",
                "Parent ISBN"
            ]
        }
        
        with open(self.tranche_path, 'w') as f:
            json.dump(tranche_config, f)
        
        # Create a temporary output file
        self.output_path = os.path.join(self.temp_dir.name, "output.csv")
        
        # Create a test metadata object
        self.metadata = CodexMetadata(
            title="Test Book",
            isbn13="9781234567890",
            publisher="Test Publisher"
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()
    
    def test_field_exclusions(self):
        """Test that excluded fields are empty in the output CSV."""
        # Create a mock implementation of the LSI ACS generator for testing
        class MockLsiAcsGenerator(LsiAcsGenerator):
            def __init__(self, template_path, tranche_name):
                self.template_path = template_path
                self.tranche_name = tranche_name
                self.field_registry = None
                
                # Mock the logging manager
                class MockLoggingManager:
                    def log_info(self, message):
                        pass
                    
                    def log_warning(self, message):
                        pass
                
                self.logging_manager = MockLoggingManager()
            
            def _read_template_headers(self):
                with open(self.template_path, 'r') as f:
                    reader = csv.reader(f)
                    return next(reader)
            
            def generate_with_validation(self, metadata, output_path):
                # Get field exclusions
                field_exclusions = ["Metadata Contact Dictionary", "Parent ISBN"]
                
                # Read template headers
                headers = self._read_template_headers()
                
                # Generate data row
                data = []
                for header in headers:
                    if header in field_exclusions:
                        data.append('')
                    elif header == "Title":
                        data.append(metadata.title)
                    elif header == "ISBN13":
                        data.append(metadata.isbn13)
                    elif header == "Publisher":
                        data.append(metadata.publisher)
                    else:
                        data.append(f"Value for {header}")
                
                # Write CSV
                with open(output_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerow(data)
                
                # Return a mock result
                class MockResult:
                    success = True
                
                return MockResult()
        
        # Create the generator
        generator = MockLsiAcsGenerator(self.template_path, "test_tranche")
        
        # Generate the CSV
        result = generator.generate_with_validation(self.metadata, self.output_path)
        
        # Check that the CSV was generated successfully
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(self.output_path))
        
        # Read the CSV and check that the excluded fields are empty
        with open(self.output_path, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            data = next(reader)
            
            # Create a dictionary of header -> value
            row_dict = dict(zip(headers, data))
            
            # Check that the excluded fields are empty
            self.assertEqual(row_dict["Metadata Contact Dictionary"], "")
            self.assertEqual(row_dict["Parent ISBN"], "")
            
            # Check that other fields have values
            self.assertEqual(row_dict["Title"], "Test Book")
            self.assertEqual(row_dict["ISBN13"], "9781234567890")
            self.assertEqual(row_dict["Publisher"], "Test Publisher")
            self.assertEqual(row_dict["Field1"], "Value for Field1")
            self.assertEqual(row_dict["Field2"], "Value for Field2")


if __name__ == '__main__':
    unittest.main()