#!/usr/bin/env python3
"""
Test script for the Cleanup Report Generator.

This script tests the cleanup report generation functionality and demonstrates
how to create comprehensive cleanup reports and documentation.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.cleanup_report_generator import (
    CleanupReportGenerator, CleanupOperation, DirectoryStructureChange,
    generate_cleanup_report
)


def test_cleanup_report_generator():
    """Test the cleanup report generator functionality."""
    print("=" * 60)
    print("TESTING CLEANUP REPORT GENERATOR")
    print("=" * 60)
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test directory structure
        create_test_directory_structure(temp_path)
        
        # Initialize report generator
        generator = CleanupReportGenerator(str(temp_path))
        
        # Start cleanup session
        session_id = generator.start_cleanup_session()
        print(f"Started cleanup session: {session_id}")
        
        # Create sample cleanup operations
        operations = create_sample_operations()
        
        # Record operations
        for operation in operations:
            generator.record_operation(operation)
            print(f"Recorded operation: {operation.operation_id}")
        
        # Create sample directory changes
        changes = create_sample_directory_changes()
        
        # Record directory changes
        for change in changes:
            generator.record_directory_change(change)
            print(f"Recorded directory change: {change.change_type} - {change.path}")
        
        # Create sample validation results
        validation_results = create_sample_validation_results()
        
        # Generate comprehensive report
        print("\nGenerating comprehensive report...")
        report_path = generator.generate_comprehensive_report(validation_results)
        print(f"Generated report: {report_path}")
        
        # Generate directory structure documentation
        print("\nGenerating directory structure documentation...")
        structure_doc_path = generator.generate_directory_structure_documentation()
        print(f"Generated structure documentation: {structure_doc_path}")
        
        # Generate validation summary
        print("\nGenerating validation summary...")
        validation_summary_path = generator.generate_validation_summary(validation_results)
        print(f"Generated validation summary: {validation_summary_path}")
        
        # Copy reports to current directory for inspection
        copy_reports_to_current_directory(generator.reports_dir)
        
        print("\n✅ Cleanup report generator test completed successfully!")
        print("Check the 'test_cleanup_reports' directory for generated reports.")
        
        return True


def create_test_directory_structure(temp_path: Path):
    """Create a test directory structure."""
    # Create directories
    directories = [
        "src/codexes/core",
        "src/codexes/modules",
        "tests",
        "docs",
        "configs",
        "data",
        "logs",
        "prompts"
    ]
    
    for dir_path in directories:
        (temp_path / dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create some test files
    test_files = [
        "src/codexes/core/test_module.py",
        "src/codexes/modules/test_feature.py",
        "tests/test_example.py",
        "docs/README.md",
        "configs/config.json",
        "data/sample.csv",
        "logs/app.log",
        "prompts/sample.json"
    ]
    
    for file_path in test_files:
        full_path = temp_path / file_path
        full_path.write_text(f"# Test file: {file_path}\n")


def create_sample_operations() -> list:
    """Create sample cleanup operations."""
    operations = []
    
    # File move operation
    operations.append(CleanupOperation(
        operation_id="move_001",
        operation_type="move",
        source_path="test_file.py",
        destination_path="tests/test_file.py",
        timestamp=datetime.now(),
        success=True,
        message="Moved test file to tests directory",
        files_affected=["test_file.py"],
        references_updated=["src/main.py", "docs/README.md"]
    ))
    
    # File deletion operation
    operations.append(CleanupOperation(
        operation_id="delete_001",
        operation_type="delete",
        source_path="exported_config_20240101_120000.json",
        destination_path=None,
        timestamp=datetime.now(),
        success=True,
        message="Deleted temporary exported config file",
        files_affected=["exported_config_20240101_120000.json"]
    ))
    
    # Directory merge operation
    operations.append(CleanupOperation(
        operation_id="merge_001",
        operation_type="merge",
        source_path="config",
        destination_path="configs",
        timestamp=datetime.now(),
        success=True,
        message="Merged config directory into configs",
        files_affected=["config/app.json", "config/db.json"],
        references_updated=["src/app.py", "src/database.py"]
    ))
    
    # Failed operation
    operations.append(CleanupOperation(
        operation_id="move_002",
        operation_type="move",
        source_path="locked_file.py",
        destination_path="src/locked_file.py",
        timestamp=datetime.now(),
        success=False,
        message="Failed to move file: Permission denied",
        files_affected=[]
    ))
    
    return operations


def create_sample_directory_changes() -> list:
    """Create sample directory structure changes."""
    changes = []
    
    changes.append(DirectoryStructureChange(
        change_type="created",
        path="tests/integration",
        reason="Created directory for integration tests",
        files_count=0
    ))
    
    changes.append(DirectoryStructureChange(
        change_type="removed",
        path="old_docs",
        reason="Removed obsolete documentation directory",
        files_count=5
    ))
    
    changes.append(DirectoryStructureChange(
        change_type="moved",
        path="docs/api",
        old_path="api_docs",
        new_path="docs/api",
        reason="Moved API documentation to docs directory",
        files_count=12
    ))
    
    changes.append(DirectoryStructureChange(
        change_type="merged",
        path="configs",
        old_path="config",
        new_path="configs",
        reason="Merged config directory into configs",
        files_count=8
    ))
    
    return changes


def create_sample_validation_results() -> dict:
    """Create sample validation results."""
    return {
        "timestamp": datetime.now().isoformat(),
        "total_tests": 6,
        "passed_tests": 5,
        "failed_tests": 1,
        "warnings": 3,
        "overall_success": False,
        "test_results": [
            {
                "test_name": "import_validation",
                "success": True,
                "message": "All critical imports working correctly",
                "warnings": ["Non-critical module import issue: optional_module"]
            },
            {
                "test_name": "configuration_validation",
                "success": True,
                "message": "All configuration files loaded successfully",
                "warnings": []
            },
            {
                "test_name": "file_reference_validation",
                "success": False,
                "message": "Found broken file references",
                "warnings": ["Reference to moved file in old_script.py"],
                "errors": ["Broken reference: old_path/missing_file.json"]
            },
            {
                "test_name": "script_validation",
                "success": True,
                "message": "All critical scripts validated successfully",
                "warnings": []
            },
            {
                "test_name": "directory_structure_validation",
                "success": True,
                "message": "Directory structure is correct",
                "warnings": ["Unexpected directory: temp_folder"]
            },
            {
                "test_name": "functionality_preservation",
                "success": True,
                "message": "All functionality preserved",
                "warnings": ["LLM integration warning: API key not configured"]
            }
        ]
    }


def copy_reports_to_current_directory(reports_dir: Path):
    """Copy generated reports to current directory for inspection."""
    current_dir = Path.cwd()
    test_reports_dir = current_dir / "test_cleanup_reports"
    
    if test_reports_dir.exists():
        shutil.rmtree(test_reports_dir)
    
    shutil.copytree(reports_dir, test_reports_dir)
    print(f"\nReports copied to: {test_reports_dir}")


def test_convenience_function():
    """Test the convenience function for generating reports."""
    print("\n" + "=" * 60)
    print("TESTING CONVENIENCE FUNCTION")
    print("=" * 60)
    
    # Create sample data
    operations = create_sample_operations()
    changes = create_sample_directory_changes()
    validation_results = create_sample_validation_results()
    
    # Generate report using convenience function
    with tempfile.TemporaryDirectory() as temp_dir:
        report_path = generate_cleanup_report(
            operations=operations,
            directory_changes=changes,
            validation_results=validation_results,
            root_path=temp_dir
        )
        
        print(f"Generated report using convenience function: {report_path}")
        
        # Copy to current directory
        current_dir = Path.cwd()
        convenience_report_path = current_dir / "convenience_cleanup_report.md"
        shutil.copy2(report_path, convenience_report_path)
        print(f"Report copied to: {convenience_report_path}")
    
    print("✅ Convenience function test completed successfully!")


def main():
    """Main function to run all tests."""
    print("🧪 CLEANUP REPORT GENERATOR TESTS")
    print("=" * 80)
    
    try:
        # Test main functionality
        test_cleanup_report_generator()
        
        # Test convenience function
        test_convenience_function()
        
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)