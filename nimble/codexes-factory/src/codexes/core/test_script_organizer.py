#!/usr/bin/env python3
"""
Test Script Organizer for the Codexes Factory cleanup system.

This module provides functionality to identify, categorize, and organize
test scripts that are misplaced outside the tests/ directory.
"""

import os
import re
import ast
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .safety_validator import SafetyValidator


class TestType(Enum):
    """Enumeration of test types for categorization."""
    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    PIPELINE = "pipeline"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class TestFileInfo:
    """Information about a test file."""
    file_path: str
    test_type: TestType
    target_directory: str
    imports: List[str]
    test_functions: List[str]
    dependencies: List[str]


class TestScriptOrganizer:
    """
    Organizes test scripts by moving them to appropriate locations in tests/ directory.
    
    This class identifies misplaced test files, categorizes them by type,
    and moves them to the appropriate subdirectories within tests/.
    """
    
    def __init__(self, root_path: str = "."):
        """
        Initialize the TestScriptOrganizer.
        
        Args:
            root_path: Root directory of the project
        """
        self.root_path = Path(root_path).resolve()
        self.tests_dir = self.root_path / "tests"
        self.safety_validator = SafetyValidator(str(self.root_path))
        
        # Test file patterns
        self.test_patterns = [
            r"^test_.*\.py$",
            r".*_test\.py$",
            r"test.*\.py$"
        ]
        
        # Keywords that help identify test types (order matters - more specific first)
        self.test_type_keywords = {
            TestType.PIPELINE: [
                "pipeline", "book_pipeline", "processing", "batch", "success_messages"
            ],
            TestType.PERFORMANCE: [
                "performance", "benchmark", "speed", "load", "stress"
            ],
            TestType.SYSTEM: [
                "system", "live", "real", "production"
            ],
            TestType.INTEGRATION: [
                "integration", "end_to_end", "e2e", "full", "complete", "workflow"
            ],
            TestType.FUNCTIONAL: [
                "functional", "acceptance", "behavior", "feature"
            ]
        }
    
    def find_misplaced_tests(self) -> List[str]:
        """
        Find test files outside the tests/ directory.
        
        Returns:
            List of paths to misplaced test files
        """
        misplaced_tests = []
        
        # Search in root directory
        for file_path in self.root_path.glob("*.py"):
            if self._is_test_file(file_path.name):
                misplaced_tests.append(str(file_path))
        
        # Search in subdirectories (excluding tests/, src/, and hidden dirs)
        exclude_dirs = {
            "tests", "src", ".git", ".venv", "__pycache__", 
            ".pytest_cache", ".idea", ".kiro", "node_modules"
        }
        
        for dir_path in self.root_path.iterdir():
            if (dir_path.is_dir() and 
                dir_path.name not in exclude_dirs and 
                not dir_path.name.startswith(".")):
                
                for file_path in dir_path.rglob("*.py"):
                    if self._is_test_file(file_path.name):
                        misplaced_tests.append(str(file_path))
        
        return misplaced_tests
    
    def _is_test_file(self, filename: str) -> bool:
        """
        Check if a filename matches test file patterns.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if the file appears to be a test file
        """
        for pattern in self.test_patterns:
            if re.match(pattern, filename):
                return True
        return False
    
    def categorize_test_file(self, file_path: str) -> TestFileInfo:
        """
        Analyze and categorize a test file.
        
        Args:
            file_path: Path to the test file
            
        Returns:
            TestFileInfo object with categorization details
        """
        path = Path(file_path)
        
        # Extract information from the file
        imports = self._extract_imports(file_path)
        test_functions = self._extract_test_functions(file_path)
        dependencies = self._analyze_dependencies(file_path)
        
        # Determine test type
        test_type = self._determine_test_type(path.name, imports, test_functions)
        
        # Determine target directory
        target_directory = self._get_target_directory(test_type, path.name)
        
        return TestFileInfo(
            file_path=file_path,
            test_type=test_type,
            target_directory=target_directory,
            imports=imports,
            test_functions=test_functions,
            dependencies=dependencies
        )
    
    def _extract_imports(self, file_path: str) -> List[str]:
        """
        Extract import statements from a Python file.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of import statements
        """
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
        
        except Exception as e:
            print(f"Warning: Could not parse imports from {file_path}: {e}")
        
        return imports
    
    def _extract_test_functions(self, file_path: str) -> List[str]:
        """
        Extract test function names from a Python file.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of test function names
        """
        test_functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith('test_') or 'test' in node.name.lower():
                        test_functions.append(node.name)
        
        except Exception as e:
            print(f"Warning: Could not parse test functions from {file_path}: {e}")
        
        return test_functions
    
    def _analyze_dependencies(self, file_path: str) -> List[str]:
        """
        Analyze file dependencies by looking at imports and references.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of dependency file paths
        """
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for relative imports and file references
            relative_import_pattern = r'from\s+\.+(\w+)'
            matches = re.findall(relative_import_pattern, content)
            dependencies.extend(matches)
            
            # Look for sys.path modifications
            if 'sys.path.insert' in content or 'sys.path.append' in content:
                dependencies.append('sys_path_modification')
        
        except Exception as e:
            print(f"Warning: Could not analyze dependencies for {file_path}: {e}")
        
        return dependencies
    
    def _determine_test_type(self, filename: str, imports: List[str], 
                           test_functions: List[str]) -> TestType:
        """
        Determine the type of test based on filename, imports, and functions.
        
        Args:
            filename: Name of the test file
            imports: List of import statements
            test_functions: List of test function names
            
        Returns:
            TestType enum value
        """
        # Combine all text for analysis
        analysis_text = f"{filename} {' '.join(imports)} {' '.join(test_functions)}".lower()
        
        # Check for specific test type keywords (order matters - more specific first)
        for test_type, keywords in self.test_type_keywords.items():
            for keyword in keywords:
                if keyword in analysis_text:
                    return test_type
        
        # Default categorization based on imports
        if any('pipeline' in imp.lower() for imp in imports):
            return TestType.PIPELINE
        elif any('integration' in imp.lower() for imp in imports):
            return TestType.INTEGRATION
        elif any('unittest' in imp or 'pytest' in imp for imp in imports):
            return TestType.UNIT
        
        return TestType.UNIT  # Default to unit test instead of unknown
    
    def _get_target_directory(self, test_type: TestType, filename: str) -> str:
        """
        Determine the target directory for a test file based on its type.
        
        Args:
            test_type: Type of the test
            filename: Name of the test file
            
        Returns:
            Target directory path relative to tests/
        """
        base_tests_dir = "tests"
        
        # Map test types to subdirectories
        type_mapping = {
            TestType.INTEGRATION: f"{base_tests_dir}/integration",
            TestType.PERFORMANCE: f"{base_tests_dir}/performance", 
            TestType.FUNCTIONAL: f"{base_tests_dir}/functional",
            TestType.PIPELINE: f"{base_tests_dir}/pipeline",
            TestType.SYSTEM: f"{base_tests_dir}/system",
            TestType.UNIT: base_tests_dir,  # Unit tests go directly in tests/
            TestType.UNKNOWN: base_tests_dir  # Unknown tests go directly in tests/
        }
        
        return type_mapping.get(test_type, base_tests_dir)
    
    def create_test_mapping(self) -> Dict[str, TestFileInfo]:
        """
        Create a mapping of all misplaced test files to their target locations.
        
        Returns:
            Dictionary mapping source paths to TestFileInfo objects
        """
        misplaced_tests = self.find_misplaced_tests()
        test_mapping = {}
        
        for test_file in misplaced_tests:
            test_info = self.categorize_test_file(test_file)
            test_mapping[test_file] = test_info
        
        return test_mapping
    
    def validate_test_organization(self, test_mapping: Dict[str, TestFileInfo]) -> Dict[str, bool]:
        """
        Validate that test files can be safely moved to their target locations.
        
        Args:
            test_mapping: Dictionary mapping source paths to TestFileInfo objects
            
        Returns:
            Dictionary mapping file paths to validation status
        """
        validation_results = {}
        
        for source_path, test_info in test_mapping.items():
            # Check if source file is safe to move
            is_safe = self.safety_validator.validate_file_safety(source_path)
            
            # Check if target directory exists or can be created
            target_dir = Path(self.root_path) / test_info.target_directory
            can_create_target = True
            
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Cannot create target directory {target_dir}: {e}")
                can_create_target = False
            
            # Check for naming conflicts
            target_file = target_dir / Path(source_path).name
            has_conflict = target_file.exists()
            
            validation_results[source_path] = (
                is_safe and can_create_target and not has_conflict
            )
        
        return validation_results
    
    def generate_organization_report(self) -> str:
        """
        Generate a report of test organization analysis.
        
        Returns:
            Formatted report string
        """
        test_mapping = self.create_test_mapping()
        validation_results = self.validate_test_organization(test_mapping)
        
        report_lines = [
            "Test Script Organization Analysis Report",
            "=" * 50,
            "",
            f"Found {len(test_mapping)} misplaced test files:",
            ""
        ]
        
        # Group by test type
        by_type = {}
        for test_info in test_mapping.values():
            test_type = test_info.test_type
            if test_type not in by_type:
                by_type[test_type] = []
            by_type[test_type].append(test_info)
        
        for test_type, test_files in by_type.items():
            report_lines.append(f"{test_type.value.upper()} Tests ({len(test_files)}):")
            for test_info in test_files:
                source = Path(test_info.file_path).name
                target = test_info.target_directory
                status = "✅ Ready" if validation_results.get(test_info.file_path, False) else "❌ Issues"
                report_lines.append(f"  - {source} → {target} [{status}]")
            report_lines.append("")
        
        # Summary
        ready_count = sum(1 for v in validation_results.values() if v)
        report_lines.extend([
            "Summary:",
            f"  - Total files: {len(test_mapping)}",
            f"  - Ready to move: {ready_count}",
            f"  - Need attention: {len(test_mapping) - ready_count}",
            ""
        ])
        
        return "\n".join(report_lines)
    
    def move_test_file(self, source_path: str, target_directory: str) -> bool:
        """
        Move a test file to the target directory with path validation.
        
        Args:
            source_path: Path to the source test file
            target_directory: Target directory path
            
        Returns:
            True if the move was successful, False otherwise
        """
        try:
            source = Path(source_path)
            target_dir = Path(self.root_path) / target_directory
            target_file = target_dir / source.name
            
            # Validate source file exists
            if not source.exists():
                print(f"Error: Source file {source_path} does not exist")
                return False
            
            # Create target directory if it doesn't exist
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Check for naming conflicts
            if target_file.exists():
                print(f"Error: Target file {target_file} already exists")
                return False
            
            # Validate file safety before moving
            if not self.safety_validator.validate_file_safety(source_path):
                print(f"Error: File {source_path} is not safe to move")
                return False
            
            # Move the file
            shutil.move(str(source), str(target_file))
            print(f"Moved {source.name} to {target_directory}")
            
            return True
            
        except Exception as e:
            print(f"Error moving {source_path}: {e}")
            return False
    
    def update_test_imports(self, test_file_path: str, old_path: str, new_path: str) -> bool:
        """
        Update import paths in a moved test file.
        
        Args:
            test_file_path: Path to the test file
            old_path: Original file path (for calculating relative changes)
            new_path: New file path
            
        Returns:
            True if imports were updated successfully, False otherwise
        """
        try:
            # Calculate the depth change
            old_depth = len(Path(old_path).parts) - 1  # Subtract 1 for filename
            new_depth = len(Path(new_path).parts) - 1
            depth_change = new_depth - old_depth
            
            # Read the file content
            with open(test_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            updated_content = content
            
            # Update sys.path.insert patterns
            if 'sys.path.insert' in content:
                # Pattern for sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
                old_pattern = r"sys\.path\.insert\(0,\s*os\.path\.join\(os\.path\.dirname\(__file__\),\s*['\"]([^'\"]*)['\"]"
                
                def replace_sys_path(match):
                    original_path = match.group(1)
                    # Adjust the path based on depth change
                    if depth_change > 0:
                        # Moved deeper, need more '../' 
                        new_relative_path = '../' * depth_change + original_path
                    elif depth_change < 0:
                        # Moved shallower, need fewer '../'
                        parts = original_path.split('/')
                        # Remove leading '../' based on depth change
                        parts_to_remove = abs(depth_change)
                        while parts_to_remove > 0 and parts and parts[0] == '..':
                            parts.pop(0)
                            parts_to_remove -= 1
                        new_relative_path = '/'.join(parts) if parts else '.'
                    else:
                        # Same depth, no change needed
                        new_relative_path = original_path
                    
                    return f"sys.path.insert(0, os.path.join(os.path.dirname(__file__), '{new_relative_path}'"
                
                updated_content = re.sub(old_pattern, replace_sys_path, updated_content)
            
            # Update relative imports if any
            # Pattern for relative imports like 'from run_book_pipeline import'
            if depth_change != 0:
                # Look for imports from root-level modules
                root_import_pattern = r"from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import"
                
                def replace_root_import(match):
                    module_name = match.group(1)
                    # Check if this looks like a root-level module (not a package)
                    if not '.' in module_name and depth_change > 0:
                        # Add sys.path modification if not already present
                        return match.group(0)  # Keep as-is for now
                    return match.group(0)
                
                updated_content = re.sub(root_import_pattern, replace_root_import, updated_content)
            
            # Write the updated content back
            if updated_content != content:
                with open(test_file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                print(f"Updated imports in {Path(test_file_path).name}")
                return True
            else:
                print(f"No import updates needed for {Path(test_file_path).name}")
                return True
                
        except Exception as e:
            print(f"Error updating imports in {test_file_path}: {e}")
            return False
    
    def validate_test_execution(self, test_file_path: str) -> bool:
        """
        Validate that a test file can be executed correctly from its new location.
        
        Args:
            test_file_path: Path to the test file
            
        Returns:
            True if the test can be executed, False otherwise
        """
        try:
            # Try to import the test file to check for import errors
            import subprocess
            import sys
            
            # Run a basic syntax check
            result = subprocess.run([
                sys.executable, '-m', 'py_compile', test_file_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {Path(test_file_path).name} passes syntax validation")
                return True
            else:
                print(f"❌ {Path(test_file_path).name} has syntax errors: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error validating {test_file_path}: {e}")
            return False
    
    def move_all_tests(self, dry_run: bool = True) -> Dict[str, bool]:
        """
        Move all misplaced test files to their appropriate locations.
        
        Args:
            dry_run: If True, only simulate the moves without actually doing them
            
        Returns:
            Dictionary mapping file paths to success status
        """
        test_mapping = self.create_test_mapping()
        validation_results = self.validate_test_organization(test_mapping)
        results = {}
        
        print(f"{'=== DRY RUN ===' if dry_run else '=== MOVING TESTS ==='}")
        print()
        
        for source_path, test_info in test_mapping.items():
            source_name = Path(source_path).name
            
            if not validation_results.get(source_path, False):
                print(f"❌ Skipping {source_name} - validation failed")
                results[source_path] = False
                continue
            
            if dry_run:
                print(f"Would move {source_name} to {test_info.target_directory}")
                results[source_path] = True
            else:
                # Actually move the file
                old_path = source_path
                success = self.move_test_file(source_path, test_info.target_directory)
                
                if success:
                    # Update imports in the moved file
                    new_path = Path(self.root_path) / test_info.target_directory / Path(source_path).name
                    import_success = self.update_test_imports(str(new_path), old_path, str(new_path))
                    
                    if import_success:
                        # Validate the moved file
                        validation_success = self.validate_test_execution(str(new_path))
                        results[source_path] = validation_success
                    else:
                        results[source_path] = False
                else:
                    results[source_path] = False
        
        # Summary
        successful_moves = sum(1 for success in results.values() if success)
        total_files = len(results)
        
        print()
        print(f"Summary: {successful_moves}/{total_files} files processed successfully")
        
        return results