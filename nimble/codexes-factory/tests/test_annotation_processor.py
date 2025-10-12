"""
Tests for annotation processor.
"""

import os
import sys
import unittest

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.distribution.annotation_processor import AnnotationProcessor
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestAnnotationProcessor(unittest.TestCase):
    """Test cases for annotation processor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.metadata = CodexMetadata()
        self.metadata.annotation_summary = "<p>This is a test annotation.</p>"
        self.metadata.summary_long = "This is a test summary."
        
        self.boilerplate = {
            "prefix": "PREFIX: ",
            "suffix": " SUFFIX"
        }
    
    def test_apply_boilerplate_html(self):
        """Test applying boilerplate to HTML annotation."""
        annotation = "<p>This is a test annotation.</p>"
        result = AnnotationProcessor.apply_boilerplate(annotation, self.boilerplate)
        self.assertEqual(result, "<p> PREFIX: This is a test annotation. SUFFIX</p>")
    
    def test_apply_boilerplate_plain(self):
        """Test applying boilerplate to plain text annotation."""
        annotation = "This is a test annotation."
        result = AnnotationProcessor.apply_boilerplate(annotation, self.boilerplate)
        self.assertEqual(result, "PREFIX: This is a test annotation. SUFFIX")
    
    def test_apply_boilerplate_multiple_paragraphs(self):
        """Test applying boilerplate to annotation with multiple paragraphs."""
        annotation = "<p>First paragraph.</p><p>Second paragraph.</p>"
        result = AnnotationProcessor.apply_boilerplate(annotation, self.boilerplate)
        self.assertEqual(result, "<p> PREFIX: First paragraph.</p><p>Second paragraph. SUFFIX</p>")
    
    def test_process_annotation(self):
        """Test processing annotation fields in metadata."""
        AnnotationProcessor.process_annotation(self.metadata, self.boilerplate)
        self.assertEqual(self.metadata.annotation_summary, "<p> PREFIX: This is a test annotation. SUFFIX</p>")
        self.assertEqual(self.metadata.summary_long, "PREFIX: This is a test summary. SUFFIX")
    
    def test_process_annotation_no_boilerplate(self):
        """Test processing annotation with no boilerplate."""
        original_annotation = self.metadata.annotation_summary
        original_summary = self.metadata.summary_long
        
        AnnotationProcessor.process_annotation(self.metadata, None)
        
        # Should not change when no boilerplate is provided
        self.assertEqual(self.metadata.annotation_summary, original_annotation)
        self.assertEqual(self.metadata.summary_long, original_summary)
    
    def test_apply_boilerplate_empty_annotation(self):
        """Test applying boilerplate to empty annotation."""
        result = AnnotationProcessor.apply_boilerplate("", self.boilerplate)
        self.assertEqual(result, "")


if __name__ == '__main__':
    unittest.main()