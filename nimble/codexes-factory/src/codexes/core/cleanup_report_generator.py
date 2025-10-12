"""
Cleanup Report Generator for repository cleanup operations.

This module generates comprehensive reports and documentation for cleanup
operations, including file movements, operations performed, and validation results.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import shutil
from collections import defaultdict

from .file_analysis_engine import FileAnalysisEngine, FileInfo
from .safety_validator import SafetyValidator, BackupInfo


@dataclass
class CleanupOperation:
    """Information about a cleanup operation performed."""
    operation_id: str
    operation_type: str  # 'move', 'delete', 'merge', 'create'
    source_path: Optional[str]
    destination_path: Optional[str]
    timestamp: datetime
    success: bool
    message: str
    backup_id: Optional[str] = None
    files_affected: List[str] = field(default_factory=list)
    references_updated: List[str] = field(default_factory=list)


@dataclass
class DirectoryStructureChange:
    """Information about directory structure changes."""
    change_type: str  # 'created', 'removed', 'moved', 'merged'
    path: str
    old_path: Optional[str] = None
    new_path: Optional[str] = None
    reason: str = ""
    files_count: int = 0


@dataclass
class CleanupSummary:
    """Summary of all cleanup operations."""
    cleanup_session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    total_operations: int
    successful_operations: int
    failed_operations: int
    files_moved: int
    files_deleted: int
    directories_created: int
    directories_removed: int
    backup_ids: List[str]
    validation_results: Dict[str, Any]


class CleanupReportGenerator:
    """
    Generator for comprehensive cleanup reports and documentation.
    
    Creates detailed reports of cleanup operations, directory structure changes,
    and validation results with proper documentation of the new organization.
    """
    
    def __init__(self, root_path: str = ".", reports_dir: str = "cleanup_reports"):
        """
        Initialize the cleanup report generator.
        
        Args:
            root_path: Root directory of the project
            reports_dir: Directory to store cleanup reports
        """
        self.root_path = Path(root_path).resolve()
        self.reports_dir = self.root_path / reports_dir
        self.reports_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.file_analysis_engine = FileAnalysisEngine(str(self.root_path))
        self.safety_validator = SafetyValidator(str(self.root_path))
        
        # Tracking data
        self.cleanup_operations: List[CleanupOperation] = []
        self.directory_changes: List[DirectoryStructureChange] = []
        self.cleanup_summary: Optional[CleanupSummary] = None
        
        # Session tracking
        self.session_id = self._generate_session_id()
        self.session_start_time = datetime.now()
    
    def start_cleanup_session(self) -> str:
        """
        Start a new cleanup session.
        
        Returns:
            Session ID for the cleanup session
        """
        self.session_id = self._generate_session_id()
        self.session_start_time = datetime.now()
        self.cleanup_operations.clear()
        self.directory_changes.clear()
        
        # Create initial directory structure snapshot
        self._create_initial_snapshot()
        
        return self.session_id
    
    def record_operation(self, operation: CleanupOperation) -> None:
        """
        Record a cleanup operation.
        
        Args:
            operation: CleanupOperation to record
        """
        self.cleanup_operations.append(operation)
    
    def record_directory_change(self, change: DirectoryStructureChange) -> None:
        """
        Record a directory structure change.
        
        Args:
            change: DirectoryStructureChange to record
        """
        self.directory_changes.append(change)
    
    def generate_comprehensive_report(self, validation_results: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a comprehensive cleanup report.
        
        Args:
            validation_results: Optional validation results to include
            
        Returns:
            Path to the generated report file
        """
        # Finalize cleanup summary
        self._finalize_cleanup_summary(validation_results)
        
        # Generate report timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate different report formats
        json_report_path = self._generate_json_report(timestamp)
        markdown_report_path = self._generate_markdown_report(timestamp)
        html_report_path = self._generate_html_report(timestamp)
        
        # Generate directory structure documentation
        structure_doc_path = self._generate_directory_structure_documentation(timestamp)
        
        # Generate validation summary
        validation_summary_path = self._generate_validation_summary(timestamp, validation_results)
        
        return markdown_report_path
    
    def generate_directory_structure_documentation(self) -> str:
        """
        Generate documentation of the new directory structure.
        
        Returns:
            Path to the generated documentation file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self._generate_directory_structure_documentation(timestamp)
    
    def generate_validation_summary(self, validation_results: Dict[str, Any]) -> str:
        """
        Generate a validation summary report.
        
        Args:
            validation_results: Validation results to summarize
            
        Returns:
            Path to the generated validation summary file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self._generate_validation_summary(timestamp, validation_results)
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _create_initial_snapshot(self) -> None:
        """Create an initial snapshot of the directory structure."""
        snapshot_path = self.reports_dir / f"{self.session_id}_initial_snapshot.json"
        
        # Scan current directory structure
        categorized_files = self.file_analysis_engine.scan_directory_structure()
        
        snapshot_data = {
            "session_id": self.session_id,
            "timestamp": self.session_start_time.isoformat(),
            "directory_structure": self._get_directory_tree(),
            "file_categories": categorized_files,
            "total_files": len(self.file_analysis_engine.file_inventory),
            "total_directories": len([d for d in self.root_path.rglob("*") if d.is_dir()])
        }
        
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2, default=str)
    
    def _finalize_cleanup_summary(self, validation_results: Optional[Dict[str, Any]]) -> None:
        """Finalize the cleanup summary with statistics."""
        end_time = datetime.now()
        
        # Calculate statistics
        total_ops = len(self.cleanup_operations)
        successful_ops = sum(1 for op in self.cleanup_operations if op.success)
        failed_ops = total_ops - successful_ops
        
        files_moved = sum(1 for op in self.cleanup_operations 
                         if op.operation_type == 'move' and op.success)
        files_deleted = sum(1 for op in self.cleanup_operations 
                           if op.operation_type == 'delete' and op.success)
        
        dirs_created = sum(1 for change in self.directory_changes 
                          if change.change_type == 'created')
        dirs_removed = sum(1 for change in self.directory_changes 
                          if change.change_type == 'removed')
        
        backup_ids = list(set(op.backup_id for op in self.cleanup_operations 
                             if op.backup_id))
        
        self.cleanup_summary = CleanupSummary(
            cleanup_session_id=self.session_id,
            start_time=self.session_start_time,
            end_time=end_time,
            total_operations=total_ops,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            files_moved=files_moved,
            files_deleted=files_deleted,
            directories_created=dirs_created,
            directories_removed=dirs_removed,
            backup_ids=backup_ids,
            validation_results=validation_results or {}
        )
    
    def _generate_json_report(self, timestamp: str) -> str:
        """Generate a JSON format report."""
        report_path = self.reports_dir / f"cleanup_report_{timestamp}.json"
        
        report_data = {
            "session_info": asdict(self.cleanup_summary) if self.cleanup_summary else {},
            "operations": [asdict(op) for op in self.cleanup_operations],
            "directory_changes": [asdict(change) for change in self.directory_changes],
            "final_structure": self._get_directory_tree()
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return str(report_path)
    
    def _generate_markdown_report(self, timestamp: str) -> str:
        """Generate a Markdown format report."""
        report_path = self.reports_dir / f"cleanup_report_{timestamp}.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self._create_markdown_content())
        
        return str(report_path)
    
    def _generate_html_report(self, timestamp: str) -> str:
        """Generate an HTML format report."""
        report_path = self.reports_dir / f"cleanup_report_{timestamp}.html"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self._create_html_content())
        
        return str(report_path)
    
    def _generate_directory_structure_documentation(self, timestamp: str) -> str:
        """Generate directory structure documentation."""
        doc_path = self.reports_dir / f"directory_structure_{timestamp}.md"
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(self._create_directory_structure_content())
        
        return str(doc_path)
    
    def _generate_validation_summary(self, timestamp: str, validation_results: Optional[Dict[str, Any]]) -> str:
        """Generate validation summary documentation."""
        summary_path = self.reports_dir / f"validation_summary_{timestamp}.md"
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(self._create_validation_summary_content(validation_results))
        
        return str(summary_path)
    
    def _get_directory_tree(self) -> Dict[str, Any]:
        """Get the current directory tree structure."""
        def build_tree(path: Path) -> Dict[str, Any]:
            tree = {"type": "directory", "children": {}}
            
            try:
                for item in sorted(path.iterdir()):
                    if item.name.startswith('.') and item.name not in {'.gitignore', '.env'}:
                        continue
                    
                    if item.is_dir():
                        tree["children"][item.name] = build_tree(item)
                    else:
                        tree["children"][item.name] = {
                            "type": "file",
                            "size": item.stat().st_size if item.exists() else 0
                        }
            except PermissionError:
                tree["error"] = "Permission denied"
            
            return tree
        
        return build_tree(self.root_path)
    
    def _create_markdown_content(self) -> str:
        """Create the main markdown report content."""
        content = []
        
        # Header
        content.append("# Repository Cleanup Report")
        content.append("")
        content.append(f"**Session ID:** {self.session_id}")
        content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("")
        
        # Executive Summary
        if self.cleanup_summary:
            content.append("## Executive Summary")
            content.append("")
            content.append(f"- **Duration:** {self.cleanup_summary.start_time.strftime('%Y-%m-%d %H:%M:%S')} to {self.cleanup_summary.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.cleanup_summary.end_time else 'In Progress'}")
            content.append(f"- **Total Operations:** {self.cleanup_summary.total_operations}")
            content.append(f"- **Successful Operations:** {self.cleanup_summary.successful_operations}")
            content.append(f"- **Failed Operations:** {self.cleanup_summary.failed_operations}")
            content.append(f"- **Files Moved:** {self.cleanup_summary.files_moved}")
            content.append(f"- **Files Deleted:** {self.cleanup_summary.files_deleted}")
            content.append(f"- **Directories Created:** {self.cleanup_summary.directories_created}")
            content.append(f"- **Directories Removed:** {self.cleanup_summary.directories_removed}")
            content.append("")
        
        # Operations Performed
        content.append("## Operations Performed")
        content.append("")
        
        if self.cleanup_operations:
            # Group operations by type
            ops_by_type = defaultdict(list)
            for op in self.cleanup_operations:
                ops_by_type[op.operation_type].append(op)
            
            for op_type, ops in ops_by_type.items():
                content.append(f"### {op_type.title()} Operations")
                content.append("")
                
                for op in ops:
                    status = "✅" if op.success else "❌"
                    content.append(f"- {status} **{op.operation_id}**")
                    if op.source_path:
                        content.append(f"  - Source: `{op.source_path}`")
                    if op.destination_path:
                        content.append(f"  - Destination: `{op.destination_path}`")
                    content.append(f"  - Message: {op.message}")
                    if op.files_affected:
                        content.append(f"  - Files Affected: {len(op.files_affected)}")
                    content.append("")
        else:
            content.append("No operations were performed.")
            content.append("")
        
        # Directory Structure Changes
        content.append("## Directory Structure Changes")
        content.append("")
        
        if self.directory_changes:
            for change in self.directory_changes:
                content.append(f"- **{change.change_type.title()}:** `{change.path}`")
                if change.old_path and change.new_path:
                    content.append(f"  - Moved from: `{change.old_path}` to `{change.new_path}`")
                if change.reason:
                    content.append(f"  - Reason: {change.reason}")
                if change.files_count > 0:
                    content.append(f"  - Files: {change.files_count}")
                content.append("")
        else:
            content.append("No directory structure changes were made.")
            content.append("")
        
        # Validation Results
        if self.cleanup_summary and self.cleanup_summary.validation_results:
            content.append("## Validation Results")
            content.append("")
            
            validation = self.cleanup_summary.validation_results
            if "overall_success" in validation:
                status = "✅ PASSED" if validation["overall_success"] else "❌ FAILED"
                content.append(f"**Overall Validation:** {status}")
                content.append("")
            
            if "test_results" in validation:
                for test in validation["test_results"]:
                    # Handle both dict and ValidationResult objects
                    if hasattr(test, 'success'):
                        # ValidationResult object
                        status = "✅" if test.success else "❌"
                        test_name = getattr(test, 'test_name', 'Unknown Test')
                        message = getattr(test, 'message', 'No message')
                        warnings = getattr(test, 'warnings', [])
                        errors = getattr(test, 'errors', [])
                    else:
                        # Dictionary
                        status = "✅" if test.get("success", False) else "❌"
                        test_name = test.get('test_name', 'Unknown Test')
                        message = test.get('message', 'No message')
                        warnings = test.get('warnings', [])
                        errors = test.get('errors', [])
                    
                    content.append(f"- {status} **{test_name}**")
                    content.append(f"  - {message}")
                    
                    if warnings:
                        content.append(f"  - Warnings: {len(warnings)}")
                    
                    if errors:
                        content.append(f"  - Errors: {len(errors)}")
                    
                    content.append("")
        
        # Backup Information
        if self.cleanup_summary and self.cleanup_summary.backup_ids:
            content.append("## Backup Information")
            content.append("")
            content.append("The following backups were created during cleanup:")
            content.append("")
            
            for backup_id in self.cleanup_summary.backup_ids:
                content.append(f"- `{backup_id}`")
            
            content.append("")
            content.append("These backups can be used to rollback changes if needed.")
            content.append("")
        
        # Recommendations
        content.append("## Recommendations")
        content.append("")
        
        if self.cleanup_summary:
            if self.cleanup_summary.failed_operations > 0:
                content.append("- ⚠️ Some operations failed. Review the failed operations above and consider manual intervention.")
            
            if self.cleanup_summary.validation_results.get("failed_tests", 0) > 0:
                content.append("- ⚠️ Some validation tests failed. Review the validation results and fix any issues.")
            
            if self.cleanup_summary.successful_operations > 0:
                content.append("- ✅ Cleanup operations completed successfully. The repository structure has been improved.")
            
            content.append("- 📝 Update any documentation that references the old file locations.")
            content.append("- 🧪 Run the full test suite to ensure all functionality still works.")
            content.append("- 🔄 Consider updating CI/CD pipelines if they reference moved files.")
        
        content.append("")
        
        return "\n".join(content)
    
    def _create_html_content(self) -> str:
        """Create HTML report content."""
        # Convert markdown to basic HTML
        markdown_content = self._create_markdown_content()
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Repository Cleanup Report - {self.session_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1, h2, h3 {{ color: #333; }}
        code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        .success {{ color: #28a745; }}
        .failure {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
    </style>
</head>
<body>
    <pre>{markdown_content}</pre>
</body>
</html>
"""
        return html_content
    
    def _create_directory_structure_content(self) -> str:
        """Create directory structure documentation content."""
        content = []
        
        content.append("# Repository Directory Structure")
        content.append("")
        content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"**Session:** {self.session_id}")
        content.append("")
        
        content.append("## Overview")
        content.append("")
        content.append("This document describes the current directory structure of the repository")
        content.append("after cleanup operations have been performed.")
        content.append("")
        
        content.append("## Directory Structure")
        content.append("")
        content.append("```")
        content.append(self._format_directory_tree(self._get_directory_tree()))
        content.append("```")
        content.append("")
        
        content.append("## Directory Descriptions")
        content.append("")
        
        # Standard directory descriptions
        directory_descriptions = {
            "src/": "Source code directory containing the main application code",
            "src/codexes/": "Main application package",
            "src/codexes/core/": "Core functionality and utilities",
            "src/codexes/modules/": "Feature modules organized by functionality",
            "tests/": "Test suite including unit and integration tests",
            "docs/": "Documentation including guides, API docs, and summaries",
            "configs/": "Configuration files for different environments and components",
            "data/": "Data files including catalogs and processed content",
            "logs/": "Log files from application execution",
            "prompts/": "LLM prompt templates and configurations",
            "resources/": "Static resources including images and templates",
            "templates/": "Template files for document generation",
            "examples/": "Example scripts and usage demonstrations",
            "imprints/": "Imprint-specific configurations and templates",
            "output/": "Generated output files and build artifacts"
        }
        
        for dir_path, description in directory_descriptions.items():
            if (self.root_path / dir_path.rstrip('/')).exists():
                content.append(f"- **{dir_path}** - {description}")
        
        content.append("")
        
        content.append("## File Organization Principles")
        content.append("")
        content.append("The repository follows these organization principles:")
        content.append("")
        content.append("1. **Source Code Separation** - All source code is in `src/`")
        content.append("2. **Test Isolation** - All tests are in `tests/`")
        content.append("3. **Documentation Centralization** - All docs are in `docs/`")
        content.append("4. **Configuration Hierarchy** - Configs follow inheritance patterns")
        content.append("5. **Resource Organization** - Static resources are properly categorized")
        content.append("6. **Clean Root Directory** - Minimal files in the root directory")
        content.append("")
        
        return "\n".join(content)
    
    def _create_validation_summary_content(self, validation_results: Optional[Dict[str, Any]]) -> str:
        """Create validation summary content."""
        content = []
        
        content.append("# Cleanup Validation Summary")
        content.append("")
        content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"**Session:** {self.session_id}")
        content.append("")
        
        if not validation_results:
            content.append("No validation results available.")
            return "\n".join(content)
        
        content.append("## Validation Overview")
        content.append("")
        
        overall_success = validation_results.get("overall_success", False)
        status = "✅ PASSED" if overall_success else "❌ FAILED"
        content.append(f"**Overall Status:** {status}")
        content.append("")
        
        if "total_tests" in validation_results:
            content.append(f"- **Total Tests:** {validation_results['total_tests']}")
            content.append(f"- **Passed:** {validation_results.get('passed_tests', 0)}")
            content.append(f"- **Failed:** {validation_results.get('failed_tests', 0)}")
            content.append(f"- **Warnings:** {validation_results.get('warnings', 0)}")
            content.append("")
        
        content.append("## Test Results")
        content.append("")
        
        if "test_results" in validation_results:
            for test in validation_results["test_results"]:
                # Handle both dict and ValidationResult objects
                if hasattr(test, 'success'):
                    # ValidationResult object
                    status = "✅ PASS" if test.success else "❌ FAIL"
                    test_name = getattr(test, 'test_name', 'Unknown Test').replace("_", " ").title()
                    message = getattr(test, 'message', 'No message')
                    warnings = getattr(test, 'warnings', [])
                    errors = getattr(test, 'errors', [])
                else:
                    # Dictionary
                    status = "✅ PASS" if test.get("success", False) else "❌ FAIL"
                    test_name = test.get("test_name", "Unknown Test").replace("_", " ").title()
                    message = test.get('message', 'No message')
                    warnings = test.get('warnings', [])
                    errors = test.get('errors', [])
                
                content.append(f"### {test_name}")
                content.append("")
                content.append(f"**Status:** {status}")
                content.append(f"**Message:** {message}")
                content.append("")
                
                if warnings:
                    content.append("**Warnings:**")
                    for warning in warnings:
                        content.append(f"- ⚠️ {warning}")
                    content.append("")
                
                if errors:
                    content.append("**Errors:**")
                    for error in errors:
                        content.append(f"- ❌ {error}")
                    content.append("")
        
        content.append("## Recommendations")
        content.append("")
        
        if overall_success:
            content.append("✅ **All validation tests passed successfully!**")
            content.append("")
            content.append("The cleanup operations have been completed without breaking")
            content.append("any critical functionality. The repository is ready for use.")
        else:
            content.append("❌ **Some validation tests failed.**")
            content.append("")
            content.append("Please review the failed tests above and take appropriate action:")
            content.append("")
            content.append("1. Fix any broken imports or references")
            content.append("2. Update configuration files if needed")
            content.append("3. Verify that all critical scripts still work")
            content.append("4. Run the full test suite to ensure functionality")
            content.append("5. Consider rolling back changes if issues persist")
        
        content.append("")
        
        return "\n".join(content)
    
    def _format_directory_tree(self, tree: Dict[str, Any], prefix: str = "", is_last: bool = True) -> str:
        """Format directory tree for display."""
        lines = []
        
        if "children" in tree:
            items = list(tree["children"].items())
            for i, (name, subtree) in enumerate(items):
                is_last_item = i == len(items) - 1
                
                # Choose the appropriate prefix
                current_prefix = "└── " if is_last_item else "├── "
                lines.append(f"{prefix}{current_prefix}{name}")
                
                # Recurse for directories
                if isinstance(subtree, dict) and "children" in subtree:
                    next_prefix = prefix + ("    " if is_last_item else "│   ")
                    lines.append(self._format_directory_tree(subtree, next_prefix, is_last_item))
        
        return "\n".join(lines)


def generate_cleanup_report(operations: List[CleanupOperation], 
                          directory_changes: List[DirectoryStructureChange],
                          validation_results: Optional[Dict[str, Any]] = None,
                          root_path: str = ".") -> str:
    """
    Convenience function to generate a cleanup report.
    
    Args:
        operations: List of cleanup operations performed
        directory_changes: List of directory structure changes
        validation_results: Optional validation results
        root_path: Root path of the project
        
    Returns:
        Path to the generated report file
    """
    generator = CleanupReportGenerator(root_path)
    
    # Record operations and changes
    for operation in operations:
        generator.record_operation(operation)
    
    for change in directory_changes:
        generator.record_directory_change(change)
    
    # Generate comprehensive report
    return generator.generate_comprehensive_report(validation_results)