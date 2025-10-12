"""
Tests for the LSI Field Completion Reporter module.
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
from codexes.modules.distribution.lsi_field_completion_reporter import (
    LSIFieldCompletionReporter, FieldCompletionData, ReportStatistics
)


class TestLSIFieldCompletionReporter(unittest.TestCase):
    """Test cases for the LSIFieldCompletionReporter class."""
    
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
        
        # Add llm_completions manually
        self.metadata.llm_completions = {
            "generate_keywords": {
                "keywords": "test; keywords; book",
                "_completion_metadata": {
                    "timestamp": "2025-07-17T12:00:00",
                    "model": "gemini/gemini-2.5-flash",
                    "prompt_key": "generate_keywords"
                }
            }
        }
        
        # Create test LSI headers
        self.lsi_headers = [
            "Title", 
            "ISBN or SKU", 
            "Publisher", 
            "Rendition /Booktype",
            "Keywords"
        ]
        
        # Create the reporter
        self.reporter = LSIFieldCompletionReporter(self.registry)
    
    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.reporter.registry, self.registry)
    
    def test_generate_report_data(self):
        """Test generating report data."""
        report_data = self.reporter._generate_report_data(self.metadata, self.lsi_headers)
        
        # Check that we have the right number of items
        self.assertEqual(len(report_data), len(self.lsi_headers))
        
        # Check that the data is correct
        title_data = next(item for item in report_data if item.field_name == "Title")
        self.assertEqual(title_data.value, "Test Book")
        self.assertEqual(title_data.strategy_type, "DirectMappingStrategy")
        self.assertEqual(title_data.source, "Direct (title)")
        self.assertFalse(title_data.is_empty)
        
        # Check default value
        publisher_data = next(item for item in report_data if item.field_name == "Publisher")
        self.assertEqual(publisher_data.value, "Nimble Books LLC")
        self.assertEqual(publisher_data.strategy_type, "DefaultMappingStrategy")
        self.assertEqual(publisher_data.source, "Default")
        self.assertFalse(publisher_data.is_empty)
        
        # Check missing field
        keywords_data = next(item for item in report_data if item.field_name == "Keywords")
        self.assertEqual(keywords_data.strategy_type, "None")
        self.assertEqual(keywords_data.source, "Empty")
        self.assertTrue(keywords_data.is_empty)
    
    def test_determine_field_source(self):
        """Test determining field source."""
        # Test direct mapping
        strategy = DirectMappingStrategy("title")
        source = self.reporter._determine_field_source(self.metadata, "Title", strategy, "Test Book")
        self.assertEqual(source, "Direct (title)")
        
        # Test default mapping
        strategy = DefaultMappingStrategy("Default Value")
        source = self.reporter._determine_field_source(self.metadata, "Field", strategy, "Default Value")
        self.assertEqual(source, "Default")
        
        # Test empty value
        source = self.reporter._determine_field_source(self.metadata, "Field", strategy, "")
        self.assertEqual(source, "Empty")
    
    def test_calculate_statistics(self):
        """Test calculating statistics."""
        # Create some test data
        report_data = [
            FieldCompletionData("Field1", "DirectMappingStrategy", "Value1", "Direct", False),
            FieldCompletionData("Field2", "DefaultMappingStrategy", "Value2", "Default", False),
            FieldCompletionData("Field3", "DirectMappingStrategy", "", "Empty", True),
            FieldCompletionData("Field4", "ComputedMappingStrategy", "Value4", "Computed", False),
            FieldCompletionData("Field5", "None", "", "None", True)
        ]
        
        # Calculate statistics
        stats = self.reporter._calculate_statistics(report_data)
        
        # Check statistics
        self.assertEqual(stats.total_fields, 5)
        self.assertEqual(stats.populated_fields, 3)
        self.assertEqual(stats.empty_fields, 2)
        self.assertEqual(stats.completion_percentage, 60.0)
        
        # Check strategy counts
        self.assertEqual(stats.strategy_counts["DirectMappingStrategy"], 1)
        self.assertEqual(stats.strategy_counts["DefaultMappingStrategy"], 1)
        self.assertEqual(stats.strategy_counts["ComputedMappingStrategy"], 1)
        self.assertNotIn("None", stats.strategy_counts)
        
        # Check source counts
        self.assertEqual(stats.source_counts["Direct"], 1)
        self.assertEqual(stats.source_counts["Default"], 1)
        self.assertEqual(stats.source_counts["Computed"], 1)
        self.assertNotIn("Empty", stats.source_counts)
        self.assertNotIn("None", stats.source_counts)
    
    def test_generate_csv_report(self):
        """Test generating CSV report."""
        # Create some test data
        report_data = [
            FieldCompletionData("Field1", "DirectMappingStrategy", "Value1", "Direct", False),
            FieldCompletionData("Field2", "DefaultMappingStrategy", "Value2", "Default", False),
            FieldCompletionData("Field3", "DirectMappingStrategy", "", "Empty", True)
        ]
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Generate CSV report
            self.reporter._generate_csv_report(report_data, temp_path)
            
            # Check that the file exists
            self.assertTrue(os.path.exists(temp_path))
            
            # Check file content
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("Field1", content)
                self.assertIn("DirectMappingStrategy", content)
                self.assertIn("Value1", content)
                self.assertIn("Direct", content)
                self.assertIn("No", content)  # Not empty
                self.assertIn("Field3", content)
                self.assertIn("Empty", content)
                self.assertIn("Yes", content)  # Empty
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_generate_json_report(self):
        """Test generating JSON report."""
        # Create some test data
        report_data = [
            FieldCompletionData("Field1", "DirectMappingStrategy", "Value1", "Direct", False),
            FieldCompletionData("Field2", "DefaultMappingStrategy", "Value2", "Default", False)
        ]
        
        # Create statistics
        stats = ReportStatistics(
            total_fields=2,
            populated_fields=2,
            empty_fields=0,
            completion_percentage=100.0,
            strategy_counts={"DirectMappingStrategy": 1, "DefaultMappingStrategy": 1},
            source_counts={"Direct": 1, "Default": 1}
        )
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Generate JSON report
            self.reporter._generate_json_report(report_data, self.metadata, stats, temp_path)
            
            # Check that the file exists
            self.assertTrue(os.path.exists(temp_path))
            
            # Check file content
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.assertEqual(data["metadata"]["title"], "Test Book")
                self.assertEqual(data["metadata"]["isbn13"], "9781234567890")
                self.assertEqual(data["statistics"]["total_fields"], 2)
                self.assertEqual(data["statistics"]["populated_fields"], 2)
                self.assertEqual(len(data["field_data"]), 2)
                self.assertEqual(data["field_data"][0]["field_name"], "Field1")
                self.assertEqual(data["field_data"][0]["value"], "Value1")
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('os.makedirs')
    def test_generate_field_strategy_report(self, mock_makedirs):
        """Test generating field strategy report."""
        # Mock the report generation methods
        self.reporter._generate_report_data = MagicMock(return_value=[])
        self.reporter._calculate_statistics = MagicMock(return_value=ReportStatistics(
            total_fields=5,
            populated_fields=3,
            empty_fields=2,
            completion_percentage=60.0,
            strategy_counts={},
            source_counts={}
        ))
        self.reporter._generate_csv_report = MagicMock()
        self.reporter._generate_html_report = MagicMock()
        self.reporter._generate_json_report = MagicMock()
        
        # Call the method
        output_files = self.reporter.generate_field_strategy_report(
            metadata=self.metadata,
            lsi_headers=self.lsi_headers,
            output_dir="test_output",
            formats=["csv", "html", "json"]
        )
        
        # Check that the directory was created
        mock_makedirs.assert_called_once_with("test_output", exist_ok=True)
        
        # Check that the report generation methods were called
        self.reporter._generate_report_data.assert_called_once()
        self.reporter._calculate_statistics.assert_called_once()
        self.reporter._generate_csv_report.assert_called_once()
        self.reporter._generate_html_report.assert_called_once()
        self.reporter._generate_json_report.assert_called_once()
        
        # Check that the output files dictionary is correct
        self.assertIn("csv", output_files)
        self.assertIn("html", output_files)
        self.assertIn("json", output_files)
        self.assertTrue(output_files["csv"].startswith("test_output/"))
        self.assertTrue(output_files["html"].startswith("test_output/"))
        self.assertTrue(output_files["json"].startswith("test_output/"))


if __name__ == '__main__':
    unittest.main()