"""
Comprehensive File Inventory System for repository cleanup operations.

This module provides a unified interface for file analysis, safety validation,
and dependency mapping to support safe repository cleanup operations.
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

from .file_analysis_engine import FileAnalysisEngine, FileInfo
from .safety_validator import SafetyValidator, SafetyCheck, BackupInfo


@dataclass
class DependencyMap:
    """Maps file dependencies and references."""
    file_path: str
    imports: List[str] = field(default_factory=list)
    imported_by: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    referenced_by: List[str] = field(default_factory=list)


@dataclass
class InventoryReport:
    """Comprehensive inventory report."""
    timestamp: datetime
    total_files: int
    categorized_files: Dict[str, List[str]]
    temporary_files: List[str]
    misplaced_tests: List[str]
    misplaced_docs: List[str]
    config_files: Dict[str, List[str]]
    resource_files: Dict[str, List[str]]
    safety_issues: List[str]
    dependency_map: Dict[str, DependencyMap]
    recommendations: List[str]


class FileInventorySystem:
    """
    Comprehensive file inventory system that combines analysis and safety validation.
    
    Provides a unified interface for scanning, categorizing, and validating files
    for safe cleanup operations with full dependency tracking.
    """
    
    def __init__(self, root_path: str = "."):
        """
        Initialize the file inventory system.
        
        Args:
            root_path: Root directory to analyze (default: current directory)
        """
        self.root_path = Path(root_path).resolve()
        self.analysis_engine = FileAnalysisEngine(str(self.root_path))
        self.safety_validator = SafetyValidator(str(self.root_path))
        
        # Inventory data
        self.file_inventory: Dict[str, FileInfo] = {}
        self.dependency_map: Dict[str, DependencyMap] = {}
        self.safety_checks: Dict[str, SafetyCheck] = {}
        
        # Analysis results
        self.categorized_files: Dict[str, List[str]] = {}
        self.temporary_files: List[str] = []
        self.misplaced_tests: List[str] = []
        self.misplaced_docs: List[str] = []
        self.config_files: Dict[str, List[str]] = {}
        self.resource_files: Dict[str, List[str]] = {}
    
    def perform_full_analysis(self) -> InventoryReport:
        """
        Perform a comprehensive analysis of the repository.
        
        Returns:
            Complete inventory report with all analysis results
        """
        print("Starting comprehensive file analysis...")
        
        # Step 1: Scan and categorize all files
        print("Scanning directory structure...")
        self.categorized_files = self.analysis_engine.scan_directory_structure()
        self.file_inventory = self.analysis_engine.file_inventory
        
        # Step 2: Identify specific file types
        print("Identifying temporary files...")
        self.temporary_files = self.analysis_engine.identify_temporary_files()
        
        print("Finding misplaced test scripts...")
        self.misplaced_tests = self.analysis_engine.find_test_scripts()
        
        print("Locating scattered documentation...")
        self.misplaced_docs = self.analysis_engine.locate_documentation_files()
        
        print("Analyzing configuration files...")
        self.config_files = self.analysis_engine.find_configuration_files()
        
        print("Identifying resource files...")
        self.resource_files = self.analysis_engine.identify_resource_files()
        
        # Step 3: Build dependency map
        print("Building dependency map...")
        self._build_dependency_map()
        
        # Step 4: Perform safety validation
        print("Performing safety validation...")
        self._perform_safety_validation()
        
        # Step 5: Generate recommendations
        print("Generating recommendations...")
        recommendations = self._generate_recommendations()
        
        # Step 6: Create comprehensive report
        report = InventoryReport(
            timestamp=datetime.now(),
            total_files=len(self.file_inventory),
            categorized_files=self.categorized_files,
            temporary_files=self.temporary_files,
            misplaced_tests=self.misplaced_tests,
            misplaced_docs=self.misplaced_docs,
            config_files=self.config_files,
            resource_files=self.resource_files,
            safety_issues=self._get_safety_issues(),
            dependency_map=self.dependency_map,
            recommendations=recommendations
        )
        
        print("Analysis complete!")
        return report
    
    def get_file_info(self, file_path: str) -> Optional[FileInfo]:
        """Get detailed information about a specific file."""
        return self.file_inventory.get(file_path)
    
    def get_dependencies(self, file_path: str) -> Optional[DependencyMap]:
        """Get dependency information for a specific file."""
        return self.dependency_map.get(file_path)
    
    def get_safety_check(self, file_path: str) -> Optional[SafetyCheck]:
        """Get safety validation results for a specific file."""
        return self.safety_checks.get(file_path)
    
    def is_safe_to_move(self, file_path: str, destination: str) -> Tuple[bool, str]:
        """
        Check if it's safe to move a file to a new location.
        
        Args:
            file_path: Source file path
            destination: Destination file path
            
        Returns:
            Tuple of (is_safe, reason)
        """
        # Check basic safety
        safety_check = self.safety_checks.get(file_path)
        if not safety_check or not safety_check.is_safe:
            reason = safety_check.reason if safety_check else "File not analyzed"
            return False, reason
        
        # Check move-specific safety
        if not self.safety_validator.verify_move_safety(file_path, destination):
            return False, "Move operation failed safety validation"
        
        # Check dependencies
        deps = self.dependency_map.get(file_path)
        if deps and (deps.imported_by or deps.referenced_by):
            return False, f"File has dependencies: {len(deps.imported_by + deps.referenced_by)} files depend on it"
        
        return True, "File is safe to move"
    
    def is_safe_to_delete(self, file_path: str) -> Tuple[bool, str]:
        """
        Check if it's safe to delete a file.
        
        Args:
            file_path: File path to check
            
        Returns:
            Tuple of (is_safe, reason)
        """
        # Check if file is marked as temporary
        file_info = self.file_inventory.get(file_path)
        if not file_info or not file_info.is_safe_to_delete:
            return False, "File is not marked as safe to delete"
        
        # Check safety validation
        safety_check = self.safety_checks.get(file_path)
        if not safety_check or not safety_check.is_safe:
            reason = safety_check.reason if safety_check else "File not analyzed"
            return False, reason
        
        # Check dependencies
        deps = self.dependency_map.get(file_path)
        if deps and (deps.imported_by or deps.referenced_by):
            return False, f"File has dependencies: {len(deps.imported_by + deps.referenced_by)} files depend on it"
        
        return True, "File is safe to delete"
    
    def create_operation_backup(self, files: List[str], operation_type: str) -> str:
        """
        Create a backup before performing operations on files.
        
        Args:
            files: List of files to backup
            operation_type: Type of operation being performed
            
        Returns:
            Backup ID
        """
        return self.safety_validator.create_backup(files, operation_type)
    
    def save_inventory_report(self, report: InventoryReport, output_path: str) -> None:
        """
        Save the inventory report to a JSON file.
        
        Args:
            report: Inventory report to save
            output_path: Path to save the report
        """
        # Convert dataclasses to dictionaries for JSON serialization
        report_dict = asdict(report)
        
        # Convert datetime to string
        report_dict['timestamp'] = report.timestamp.isoformat()
        
        # Convert DependencyMap objects to dictionaries
        dependency_dict = {}
        for file_path, dep_map in report.dependency_map.items():
            dependency_dict[file_path] = asdict(dep_map)
        report_dict['dependency_map'] = dependency_dict
        
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
    
    def load_inventory_report(self, input_path: str) -> InventoryReport:
        """
        Load an inventory report from a JSON file.
        
        Args:
            input_path: Path to the report file
            
        Returns:
            Loaded inventory report
        """
        with open(input_path, 'r') as f:
            report_dict = json.load(f)
        
        # Convert timestamp back to datetime
        timestamp = datetime.fromisoformat(report_dict['timestamp'])
        
        # Convert dependency map back to DependencyMap objects
        dependency_map = {}
        for file_path, dep_dict in report_dict['dependency_map'].items():
            dependency_map[file_path] = DependencyMap(**dep_dict)
        
        return InventoryReport(
            timestamp=timestamp,
            total_files=report_dict['total_files'],
            categorized_files=report_dict['categorized_files'],
            temporary_files=report_dict['temporary_files'],
            misplaced_tests=report_dict['misplaced_tests'],
            misplaced_docs=report_dict['misplaced_docs'],
            config_files=report_dict['config_files'],
            resource_files=report_dict['resource_files'],
            safety_issues=report_dict['safety_issues'],
            dependency_map=dependency_map,
            recommendations=report_dict['recommendations']
        )
    
    def _build_dependency_map(self) -> None:
        """Build a comprehensive dependency map for all files."""
        # Initialize dependency map
        for file_path in self.file_inventory:
            self.dependency_map[file_path] = DependencyMap(file_path=file_path)
        
        # Analyze each file for references
        for file_path in self.file_inventory:
            references = self.analysis_engine.analyze_file_references(file_path)
            
            if file_path in self.dependency_map:
                self.dependency_map[file_path].references = references
            
            # Update reverse dependencies
            for ref in references:
                # Try to find the referenced file in our inventory
                matching_files = self._find_matching_files(ref)
                for matching_file in matching_files:
                    if matching_file in self.dependency_map:
                        self.dependency_map[matching_file].referenced_by.append(file_path)
        
        # Build import relationships for Python files
        self._build_import_relationships()
    
    def _build_import_relationships(self) -> None:
        """Build import relationships between Python files."""
        python_files = [f for f in self.file_inventory if f.endswith('.py')]
        
        for file_path in python_files:
            try:
                # Get module name
                module_name = self._get_module_name(file_path)
                if not module_name:
                    continue
                
                # Find files that import this module
                importing_files = self.safety_validator._find_python_dependencies(module_name)
                
                if file_path in self.dependency_map:
                    self.dependency_map[file_path].imported_by = importing_files
                
                # Update the importing files
                for importing_file in importing_files:
                    if importing_file in self.dependency_map:
                        if module_name not in self.dependency_map[importing_file].imports:
                            self.dependency_map[importing_file].imports.append(module_name)
            
            except Exception as e:
                print(f"Warning: Could not analyze imports for {file_path}: {e}")
    
    def _perform_safety_validation(self) -> None:
        """Perform safety validation on all files."""
        for file_path in self.file_inventory:
            safety_check = self.safety_validator.validate_file_safety(file_path)
            self.safety_checks[file_path] = safety_check
            
            # Update file info with safety status
            if file_path in self.file_inventory:
                file_info = self.file_inventory[file_path]
                file_info.is_safe_to_move = safety_check.is_safe
                
                # Mark temporary files as safe to delete if they pass safety checks
                if file_info.category == "temporary" and safety_check.is_safe:
                    file_info.is_safe_to_delete = True
    
    def _get_safety_issues(self) -> List[str]:
        """Get a list of safety issues found during validation."""
        issues = []
        
        for file_path, safety_check in self.safety_checks.items():
            if not safety_check.is_safe:
                issues.append(f"{file_path}: {safety_check.reason}")
            
            for warning in safety_check.warnings:
                issues.append(f"{file_path}: WARNING - {warning}")
        
        return issues
    
    def _generate_recommendations(self) -> List[str]:
        """Generate cleanup recommendations based on analysis."""
        recommendations = []
        
        # Temporary files
        if self.temporary_files:
            safe_temp_files = [f for f in self.temporary_files 
                             if self.safety_checks.get(f, SafetyCheck("", False, "")).is_safe]
            if safe_temp_files:
                recommendations.append(
                    f"Remove {len(safe_temp_files)} temporary files to clean up repository"
                )
        
        # Misplaced tests
        if self.misplaced_tests:
            safe_tests = [f for f in self.misplaced_tests 
                         if self.safety_checks.get(f, SafetyCheck("", False, "")).is_safe]
            if safe_tests:
                recommendations.append(
                    f"Move {len(safe_tests)} test files to tests/ directory for better organization"
                )
        
        # Misplaced documentation
        if self.misplaced_docs:
            safe_docs = [f for f in self.misplaced_docs 
                        if self.safety_checks.get(f, SafetyCheck("", False, "")).is_safe]
            if safe_docs:
                recommendations.append(
                    f"Move {len(safe_docs)} documentation files to docs/ directory"
                )
        
        # Configuration consolidation
        if len(self.config_files) > 1:
            recommendations.append(
                "Consolidate configuration files into a single config/ directory"
            )
        
        # Resource organization
        if self.resource_files.get("images"):
            recommendations.append(
                f"Move {len(self.resource_files['images'])} image files to resources/images/"
            )
        
        if self.resource_files.get("exports"):
            recommendations.append(
                f"Move {len(self.resource_files['exports'])} exported files to exports/ directory"
            )
        
        return recommendations
    
    def _find_matching_files(self, reference: str) -> List[str]:
        """Find files in inventory that match a reference."""
        matching_files = []
        
        # Direct match
        if reference in self.file_inventory:
            matching_files.append(reference)
        
        # Try with different extensions
        base_ref = Path(reference).with_suffix('')
        for file_path in self.file_inventory:
            if Path(file_path).with_suffix('') == base_ref:
                matching_files.append(file_path)
        
        # Try filename match
        ref_name = Path(reference).name
        for file_path in self.file_inventory:
            if Path(file_path).name == ref_name:
                matching_files.append(file_path)
        
        return matching_files
    
    def _get_module_name(self, file_path: str) -> str:
        """Get the Python module name for a file path."""
        path = Path(file_path)
        if path.suffix != '.py':
            return ""
        
        # Convert file path to module name
        parts = path.with_suffix('').parts
        if parts and parts[0] == 'src':
            parts = parts[1:]  # Remove 'src' prefix
        
        return '.'.join(parts)