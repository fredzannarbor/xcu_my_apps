#!/usr/bin/env python3
"""
Tests for the TestScriptOrganizer class.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.test_script_organizer import TestScriptOrganizer, TestType, TestFileInfo


class TestTestScriptOrganizer:
    """Test cases for TestScriptOrganizer."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.organizer = TestScriptOrganizer(self.temp_dir)
        
        # Create test directory structure
        self.tests_dir = Path(self.temp_dir) / "tests"
        self.tests_dir.mkdir(exist_ok=True)
        
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename: str, content: str, subdir: str = "") -> str:
        """Create a test file with given content."""
        if subdir:
            file_dir = Path(self.temp_dir) / subdir
            file_dir.mkdir(parents=True, exist_ok=True)
            file_path = file_dir / filename
        else:
            file_path = Path(self.temp_dir) / filename
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        return str(file_path)
    
    def test_find_misplaced_tests_in_root(self):
        """Test finding test files in root directory."""
        # Create a test file in root
        test_content = '''
import unittest

def test_something():
    pass

class TestExample(unittest.TestCase):
    def test_method(self):
        pass
'''
        self.create_test_file("test_example.py", test_content)
        
        misplaced = self.organizer.find_misplaced_tests()
        assert len(misplaced) == 1
        assert "test_example.py" in misplaced[0]
    
    def test_find_misplaced_tests_ignores_tests_dir(self):
        """Test that files in tests/ directory are ignored."""
        # Create test file in tests/ directory
        test_content = "def test_something(): pass"
        self.create_test_file("test_in_tests.py", test_content, "tests")
        
        # Create test file in root
        self.create_test_file("test_in_root.py", test_content)
        
        misplaced = self.organizer.find_misplaced_tests()
        assert len(misplaced) == 1
        assert "test_in_root.py" in misplaced[0]
        assert "test_in_tests.py" not in str(misplaced)
    
    def test_categorize_pipeline_test(self):
        """Test categorization of pipeline test."""
        pipeline_test_content = '''
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from run_book_pipeline import SuccessAwareTerseLogFilter

def test_pipeline_success_messages():
    """Test that success messages appear in the pipeline."""
    pass
'''
        test_file = self.create_test_file("test_pipeline_success_messages.py", pipeline_test_content)
        
        test_info = self.organizer.categorize_test_file(test_file)
        
        assert test_info.test_type == TestType.PIPELINE
        assert "tests/pipeline" in test_info.target_directory
        assert len(test_info.test_functions) == 1
        assert "test_pipeline_success_messages" in test_info.test_functions
    
    def test_categorize_integration_test(self):
        """Test categorization of integration test."""
        integration_test_content = '''
import pytest
from src.codexes.modules.distribution import field_mapping

def test_full_integration_workflow():
    """Test complete integration workflow."""
    pass

def test_end_to_end_flow():
    """Test end-to-end flow."""
    pass
'''
        test_file = self.create_test_file("test_integration_workflow.py", integration_test_content)
        
        test_info = self.organizer.categorize_test_file(test_file)
        
        assert test_info.test_type == TestType.INTEGRATION
        assert "tests/integration" in test_info.target_directory
        assert len(test_info.test_functions) == 2
    
    def test_categorize_unit_test(self):
        """Test categorization of unit test."""
        unit_test_content = '''
import unittest
from src.codexes.core.utils import some_function

class TestSomeFunction(unittest.TestCase):
    def test_basic_operation(self):
        """Test basic operation."""
        pass
    
    def test_edge_cases(self):
        """Test edge cases."""
        pass
'''
        test_file = self.create_test_file("test_some_function.py", unit_test_content)
        
        test_info = self.organizer.categorize_test_file(test_file)
        
        assert test_info.test_type == TestType.UNIT
        assert test_info.target_directory == "tests"
        assert len(test_info.test_functions) == 2
    
    def test_categorize_performance_test(self):
        """Test categorization of performance test."""
        performance_test_content = '''
import time
import pytest

def test_performance_benchmark():
    """Test performance benchmark."""
    pass

def test_load_testing():
    """Test load performance."""
    pass
'''
        test_file = self.create_test_file("test_performance_benchmark.py", performance_test_content)
        
        test_info = self.organizer.categorize_test_file(test_file)
        
        assert test_info.test_type == TestType.PERFORMANCE
        assert "tests/performance" in test_info.target_directory
    
    def test_create_test_mapping(self):
        """Test creating mapping of all misplaced tests."""
        # Create multiple test files
        self.create_test_file("test_unit.py", "def test_unit(): pass")
        self.create_test_file("test_integration_full.py", "def test_integration(): pass")
        self.create_test_file("test_pipeline_workflow.py", "def test_pipeline(): pass")
        
        mapping = self.organizer.create_test_mapping()
        
        assert len(mapping) == 3
        
        # Check that all files are mapped
        filenames = [Path(path).name for path in mapping.keys()]
        assert "test_unit.py" in filenames
        assert "test_integration_full.py" in filenames
        assert "test_pipeline_workflow.py" in filenames
    
    def test_validate_test_organization(self):
        """Test validation of test organization."""
        # Create a test file
        test_content = "def test_something(): pass"
        test_file = self.create_test_file("test_validation.py", test_content)
        
        # Create mapping
        mapping = self.organizer.create_test_mapping()
        
        # Validate
        validation_results = self.organizer.validate_test_organization(mapping)
        
        assert len(validation_results) == 1
        # Check if any key contains our test file name (handles path resolution differences)
        found_key = None
        for key in validation_results.keys():
            if "test_validation.py" in key:
                found_key = key
                break
        
        assert found_key is not None
        # Should be valid since it's a simple test file
        assert validation_results[found_key] is True
    
    def test_generate_organization_report(self):
        """Test generation of organization report."""
        # Create test files of different types
        self.create_test_file("test_unit.py", "def test_unit(): pass")
        self.create_test_file("test_integration_full.py", "def test_integration(): pass")
        
        report = self.organizer.generate_organization_report()
        
        assert "Test Script Organization Analysis Report" in report
        assert "Found 2 misplaced test files" in report
        assert "UNIT Tests" in report or "INTEGRATION Tests" in report
        assert "Summary:" in report
        assert "Total files: 2" in report
    
    def test_is_test_file_patterns(self):
        """Test test file pattern matching."""
        organizer = TestScriptOrganizer()
        
        # Should match
        assert organizer._is_test_file("test_example.py") is True
        assert organizer._is_test_file("test_something_else.py") is True
        assert organizer._is_test_file("example_test.py") is True
        
        # Should not match
        assert organizer._is_test_file("example.py") is False
        assert organizer._is_test_file("main.py") is False
        assert organizer._is_test_file("config.py") is False
    
    def test_extract_imports(self):
        """Test import extraction from Python files."""
        test_content = '''
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock
from src.codexes.core import utils

def test_something():
    pass
'''
        test_file = self.create_test_file("test_imports.py", test_content)
        
        imports = self.organizer._extract_imports(test_file)
        
        assert "import os" in imports
        assert "import sys" in imports
        assert "from pathlib import Path" in imports
        assert "from unittest.mock import MagicMock" in imports
        assert "from src.codexes.core import utils" in imports
    
    def test_extract_test_functions(self):
        """Test test function extraction."""
        test_content = '''
def test_function_one():
    pass

def helper_function():
    pass

def test_function_two():
    pass

class TestClass:
    def test_method(self):
        pass
    
    def helper_method(self):
        pass
'''
        test_file = self.create_test_file("test_functions.py", test_content)
        
        test_functions = self.organizer._extract_test_functions(test_file)
        
        assert "test_function_one" in test_functions
        assert "test_function_two" in test_functions
        assert "test_method" in test_functions
        assert "helper_function" not in test_functions
        assert "helper_method" not in test_functions


    def test_move_test_file(self):
        """Test moving a test file to target directory."""
        # Create a test file
        test_content = "def test_something(): pass"
        test_file = self.create_test_file("test_move_me.py", test_content)
        
        # Create target directory
        target_dir = "tests/unit"
        
        # Move the file
        success = self.organizer.move_test_file(test_file, target_dir)
        
        assert success is True
        
        # Check that file was moved
        moved_file = Path(self.temp_dir) / target_dir / "test_move_me.py"
        assert moved_file.exists()
        
        # Check that original file is gone
        assert not Path(test_file).exists()
    
    def test_move_test_file_creates_directory(self):
        """Test that move_test_file creates target directory if it doesn't exist."""
        # Create a test file
        test_content = "def test_something(): pass"
        test_file = self.create_test_file("test_create_dir.py", test_content)
        
        # Use a non-existent target directory
        target_dir = "tests/new_category"
        
        # Move the file
        success = self.organizer.move_test_file(test_file, target_dir)
        
        assert success is True
        
        # Check that directory was created
        target_path = Path(self.temp_dir) / target_dir
        assert target_path.exists()
        assert target_path.is_dir()
        
        # Check that file was moved
        moved_file = target_path / "test_create_dir.py"
        assert moved_file.exists()
    
    def test_update_test_imports_sys_path(self):
        """Test updating sys.path.insert statements when moving files."""
        # Create a test file with sys.path modification
        test_content = '''
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_something():
    pass
'''
        test_file = self.create_test_file("test_imports.py", test_content)
        
        # Move to a subdirectory (deeper)
        target_dir = Path(self.temp_dir) / "tests" / "unit"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "test_imports.py"
        
        # Copy file to target location
        shutil.copy2(test_file, target_file)
        
        # Update imports (moving from root to tests/unit - 2 levels deeper)
        old_path = test_file
        new_path = str(target_file)
        
        success = self.organizer.update_test_imports(new_path, old_path, new_path)
        
        assert success is True
        
        # Check that the import was updated
        with open(target_file, 'r') as f:
            updated_content = f.read()
        
        assert "sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'" in updated_content
    
    def test_validate_test_execution(self):
        """Test validation of test file execution."""
        # Create a valid test file
        valid_test_content = '''
def test_valid():
    assert True
'''
        valid_test_file = self.create_test_file("test_valid.py", valid_test_content)
        
        # Test validation
        is_valid = self.organizer.validate_test_execution(valid_test_file)
        assert is_valid is True
        
        # Create an invalid test file
        invalid_test_content = '''
def test_invalid(
    # Missing closing parenthesis - syntax error
    assert True
'''
        invalid_test_file = self.create_test_file("test_invalid.py", invalid_test_content)
        
        # Test validation
        is_valid = self.organizer.validate_test_execution(invalid_test_file)
        assert is_valid is False
    
    def test_move_all_tests_dry_run(self):
        """Test dry run of moving all tests."""
        # Create multiple test files
        self.create_test_file("test_unit.py", "def test_unit(): pass")
        self.create_test_file("test_integration_full.py", "def test_integration(): pass")
        
        # Run dry run
        results = self.organizer.move_all_tests(dry_run=True)
        
        # Check that files weren't actually moved
        assert Path(self.temp_dir, "test_unit.py").exists()
        assert Path(self.temp_dir, "test_integration_full.py").exists()
        
        # Check that results indicate success
        assert len(results) == 2
        assert all(results.values())
    
    def test_move_all_tests_actual(self):
        """Test actual moving of all tests."""
        # Create test files
        unit_content = "def test_unit(): pass"
        integration_content = "def test_integration(): pass"
        
        self.create_test_file("test_unit.py", unit_content)
        self.create_test_file("test_integration_full.py", integration_content)
        
        # Run actual move
        results = self.organizer.move_all_tests(dry_run=False)
        
        # Check that files were moved
        assert not Path(self.temp_dir, "test_unit.py").exists()
        assert not Path(self.temp_dir, "test_integration_full.py").exists()
        
        # Check that files exist in target locations
        assert Path(self.temp_dir, "tests", "test_unit.py").exists()
        assert Path(self.temp_dir, "tests", "integration", "test_integration_full.py").exists()
        
        # Check results
        assert len(results) == 2
        assert all(results.values())


if __name__ == "__main__":
    pytest.main([__file__])