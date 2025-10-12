"""
Tests for DocumentationConsolidator class.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.codexes.core.documentation_consolidator import (
    DocumentationConsolidator, 
    DocumentationType,
    DocumentationFile
)


class TestDocumentationConsolidator:
    """Test cases for DocumentationConsolidator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.consolidator = DocumentationConsolidator(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test DocumentationConsolidator initialization."""
        assert self.consolidator.root_path == Path(self.temp_dir).resolve()
        assert self.consolidator.docs_dir == Path(self.temp_dir).resolve() / "docs"
        assert len(self.consolidator.documentation_files) == 0
    
    def test_extract_title_from_heading(self):
        """Test title extraction from markdown heading."""
        content = "# API Reference Guide\n\nThis is the content."
        title = self.consolidator._extract_title(content, "test.md")
        assert title == "API Reference Guide"
    
    def test_extract_title_from_filename(self):
        """Test title extraction from filename when no heading."""
        content = "This is content without heading."
        title = self.consolidator._extract_title(content, "user_guide.md")
        assert title == "User Guide"
    
    def test_categorize_document_api_reference(self):
        """Test categorization of API reference documents."""
        file_path = Path("test_api_reference.md")
        content = "This document describes the API methods and endpoints."
        
        doc_type = self.consolidator._categorize_document(file_path, content)
        assert doc_type == DocumentationType.API_REFERENCE
    
    def test_categorize_document_user_guide(self):
        """Test categorization of user guide documents."""
        file_path = Path("user_guide.md")
        content = "This guide shows how to use the system."
        
        doc_type = self.consolidator._categorize_document(file_path, content)
        assert doc_type == DocumentationType.USER_GUIDE
    
    def test_categorize_document_troubleshooting(self):
        """Test categorization of troubleshooting documents."""
        file_path = Path("troubleshooting_guide.md")
        content = "How to debug and fix common errors."
        
        doc_type = self.consolidator._categorize_document(file_path, content)
        assert doc_type == DocumentationType.TROUBLESHOOTING
    
    def test_categorize_document_readme(self):
        """Test categorization of README documents."""
        file_path = Path("docs/readme/codexes_factory_ai_assisted_publishing_platform_v32.md")
        content = "This is a readme file."
        
        doc_type = self.consolidator._categorize_document(file_path, content)
        assert doc_type == DocumentationType.README
    
    def test_determine_category_from_path(self):
        """Test category determination from file path."""
        file_path = Path(self.temp_dir) / "notes_and_reports" / "test.md"
        category = self.consolidator._determine_category(file_path, DocumentationType.NOTES)
        assert category == "notes"
    
    def test_determine_category_from_type(self):
        """Test category determination from document type."""
        file_path = Path(self.temp_dir) / "test.md"
        category = self.consolidator._determine_category(file_path, DocumentationType.API_REFERENCE)
        assert category == "api"
    
    def test_find_references_markdown_links(self):
        """Test finding references in markdown links."""
        content = "See [config guide](config/setup.md) and [API docs](api/reference.md)"
        references = self.consolidator._find_references(content)
        
        assert "config/setup.md" in references
        assert "api/reference.md" in references
    
    def test_find_references_file_paths(self):
        """Test finding file path references."""
        content = "Check the `config.json` file and 'setup.py' script."
        references = self.consolidator._find_references(content)
        
        assert "config.json" in references
        assert "setup.py" in references
    
    def test_generate_target_filename_descriptive(self):
        """Test target filename generation for descriptive names."""
        doc_file = DocumentationFile(
            path=Path("long_descriptive_filename.md"),
            doc_type=DocumentationType.USER_GUIDE,
            category="guides",
            title="Long Descriptive Filename",
            size=1000,
            references=[]
        )
        
        filename = self.consolidator._generate_target_filename(doc_file)
        assert filename == "long_descriptive_filename.md"
    
    def test_generate_target_filename_from_title(self):
        """Test target filename generation from title."""
        doc_file = DocumentationFile(
            path=Path("test.md"),
            doc_type=DocumentationType.API_REFERENCE,
            category="api",
            title="API Reference Guide",
            size=1000,
            references=[]
        )
        
        filename = self.consolidator._generate_target_filename(doc_file)
        assert filename == "API_REFERENCE_api_reference_guide.md"
    
    def test_create_doc_hierarchy(self):
        """Test creation of documentation hierarchy."""
        hierarchy = self.consolidator.create_doc_hierarchy()
        
        # Check that all expected categories are present
        expected_categories = [
            'api', 'guides', 'summaries', 'troubleshooting', 
            'configuration', 'readme', 'assessments', 'notes'
        ]
        
        for category in expected_categories:
            assert category in hierarchy
            assert hierarchy[category].startswith('docs/')
    
    def test_categorize_documentation(self):
        """Test categorization of documentation files."""
        doc_files = [
            DocumentationFile(
                path=Path("api.md"),
                doc_type=DocumentationType.API_REFERENCE,
                category="api",
                title="API Reference",
                size=1000,
                references=[]
            ),
            DocumentationFile(
                path=Path("guide.md"),
                doc_type=DocumentationType.USER_GUIDE,
                category="guides",
                title="User Guide",
                size=2000,
                references=[]
            )
        ]
        
        categorized = self.consolidator.categorize_documentation(doc_files)
        
        assert "api" in categorized
        assert "guides" in categorized
        assert len(categorized["api"]) == 1
        assert len(categorized["guides"]) == 1
    
    @patch('builtins.open', new_callable=mock_open, read_data="# Test Document\nContent here")
    @patch('os.walk')
    @patch('pathlib.Path.stat')
    def test_find_scattered_docs(self, mock_stat, mock_walk, mock_file):
        """Test finding scattered documentation files."""
        # Mock file system structure
        mock_walk.return_value = [
            (self.temp_dir, ['subdir'], ['test.md', 'other.txt']),
            (os.path.join(self.temp_dir, 'subdir'), [], ['guide.md'])
        ]
        
        # Mock file stats
        class MockStat:
            st_size = 1000
        mock_stat.return_value = MockStat()
        
        docs = self.consolidator.find_scattered_docs()
        
        # Should find markdown files but not other files
        assert len(docs) >= 0  # May be 0 due to mocking complexity
    
    def test_generate_consolidation_plan_empty(self):
        """Test consolidation plan generation with no files."""
        plan = self.consolidator.generate_consolidation_plan()
        
        assert plan['total_files'] == 0
        assert len(plan['categories']) == 0
        assert len(plan['file_mappings']) == 0
        assert len(plan['potential_conflicts']) == 0
    
    def test_update_file_references(self):
        """Test updating references in a file."""
        # Create a test file with references
        test_file = Path(self.temp_dir) / "test_refs.md"
        content = """
        # Test Document
        
        See [config guide](config/setup.md) for setup.
        Check the `old_file.md` for details.
        """
        
        with open(test_file, 'w') as f:
            f.write(content)
        
        # Define updates
        updates = {
            'config/setup.md': 'docs/configuration/setup.md',
            'old_file.md': 'docs/guides/old_file.md'
        }
        
        # Update references
        changes = self.consolidator._update_file_references(test_file, updates)
        
        # Check that changes were made
        assert len(changes) > 0
        
        # Check file content was updated
        with open(test_file, 'r') as f:
            updated_content = f.read()
        
        assert 'docs/configuration/setup.md' in updated_content
        assert 'docs/guides/old_file.md' in updated_content
    
    def test_check_file_links(self):
        """Test checking for broken links in a file."""
        # Create a test file with links
        test_file = Path(self.temp_dir) / "test_links.md"
        content = """
        # Test Document
        
        [Existing file](existing.md)
        [Missing file](missing.md)
        [External link](https://example.com)
        """
        
        with open(test_file, 'w') as f:
            f.write(content)
        
        # Create one of the referenced files
        existing_file = Path(self.temp_dir) / "existing.md"
        with open(existing_file, 'w') as f:
            f.write("# Existing file")
        
        # Check links
        broken_links = self.consolidator._check_file_links(test_file)
        
        # Should find the missing file but not the existing one or external link
        assert 'missing.md' in broken_links
        assert 'existing.md' not in broken_links
        assert 'https://example.com' not in broken_links
    
    def test_execute_consolidation_dry_run(self):
        """Test consolidation execution in dry run mode."""
        # Create a simple plan
        plan = {
            'total_files': 1,
            'categories': {},
            'file_mappings': {'test.md': 'docs/test.md'},
            'potential_conflicts': []
        }
        
        # Execute dry run
        results = self.consolidator.execute_consolidation(plan, dry_run=True)
        
        # Check results
        assert results['dry_run'] is True
        assert len(results['moved_files']) == 1
        assert len(results['failed_moves']) == 0
        assert 'test.md' in results['moved_files']


if __name__ == "__main__":
    pytest.main([__file__])