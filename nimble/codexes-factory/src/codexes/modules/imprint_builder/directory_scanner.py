"""
Directory Scanner component for batch processing of imprint concepts.

This module handles scanning directories for CSV files, filtering,
and creating processing plans for batch operations.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional, Set, Dict, Any
from dataclasses import dataclass

from .batch_models import ProcessingPlan, ValidationResult


@dataclass
class ScanResult:
    """Result of scanning a directory for CSV files."""
    directory: Path
    total_files: int
    csv_files: List[Path]
    ignored_files: List[Path]
    errors: List[str]
    warnings: List[str]
    
    def __post_init__(self):
        """Ensure directory is a Path object."""
        if isinstance(self.directory, str):
            self.directory = Path(self.directory)


class DirectoryScanner:
    """Handles scanning directories for CSV files and creating processing plans."""
    
    # File extensions to consider as CSV files
    CSV_EXTENSIONS = {'.csv', '.CSV'}
    
    # File patterns to ignore
    IGNORE_PATTERNS = {
        # Hidden files
        '.*',
        # Temporary files
        '~*',
        '*~',
        '*.tmp',
        '*.temp',
        # System files
        'Thumbs.db',
        '.DS_Store',
        # Backup files
        '*.bak',
        '*.backup'
    }
    
    def __init__(self, recursive: bool = True, follow_symlinks: bool = False):
        """
        Initialize DirectoryScanner.
        
        Args:
            recursive: Whether to scan subdirectories recursively
            follow_symlinks: Whether to follow symbolic links
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.recursive = recursive
        self.follow_symlinks = follow_symlinks
        
        self.logger.info(f"Initialized DirectoryScanner (recursive={recursive}, follow_symlinks={follow_symlinks})")
    
    def scan_directory(self, directory_path: Path) -> List[Path]:
        """
        Scan directory for all files.
        
        Args:
            directory_path: Path to directory to scan
            
        Returns:
            List of all file paths found
            
        Raises:
            FileNotFoundError: If directory doesn't exist
            PermissionError: If directory is not accessible
        """
        self.logger.info(f"Scanning directory: {directory_path}")
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        try:
            all_files = []
            
            if self.recursive:
                # Use rglob for recursive scanning
                for file_path in directory_path.rglob('*'):
                    if file_path.is_file():
                        # Check if we should follow symlinks
                        if not self.follow_symlinks and file_path.is_symlink():
                            self.logger.debug(f"Skipping symlink: {file_path}")
                            continue
                        all_files.append(file_path)
            else:
                # Use glob for non-recursive scanning
                for file_path in directory_path.glob('*'):
                    if file_path.is_file():
                        # Check if we should follow symlinks
                        if not self.follow_symlinks and file_path.is_symlink():
                            self.logger.debug(f"Skipping symlink: {file_path}")
                            continue
                        all_files.append(file_path)
            
            self.logger.info(f"Found {len(all_files)} files in {directory_path}")
            return sorted(all_files)
            
        except PermissionError as e:
            self.logger.error(f"Permission denied accessing directory {directory_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory_path}: {e}")
            raise
    
    def filter_csv_files(self, file_paths: List[Path]) -> List[Path]:
        """
        Filter list of files to include only CSV files.
        
        Args:
            file_paths: List of file paths to filter
            
        Returns:
            List of CSV file paths
        """
        csv_files = []
        
        for file_path in file_paths:
            # Check file extension
            if file_path.suffix in self.CSV_EXTENSIONS:
                # Check if file should be ignored
                if not self._should_ignore_file(file_path):
                    csv_files.append(file_path)
                else:
                    self.logger.debug(f"Ignoring CSV file due to pattern match: {file_path}")
            else:
                self.logger.debug(f"Skipping non-CSV file: {file_path}")
        
        self.logger.info(f"Filtered to {len(csv_files)} CSV files from {len(file_paths)} total files")
        return csv_files
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """
        Check if a file should be ignored based on patterns.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file should be ignored
        """
        filename = file_path.name
        
        # Check against ignore patterns
        for pattern in self.IGNORE_PATTERNS:
            if pattern.startswith('*') and pattern.endswith('*'):
                # Contains pattern
                if pattern[1:-1] in filename:
                    return True
            elif pattern.startswith('*'):
                # Ends with pattern
                if filename.endswith(pattern[1:]):
                    return True
            elif pattern.endswith('*'):
                # Starts with pattern
                if filename.startswith(pattern[:-1]):
                    return True
            else:
                # Exact match
                if filename == pattern:
                    return True
        
        return False
    
    def create_processing_plan(self, csv_files: List[Path]) -> ProcessingPlan:
        """
        Create a processing plan for CSV files.
        
        Args:
            csv_files: List of CSV file paths
            
        Returns:
            ProcessingPlan with ordered file list
        """
        if not csv_files:
            self.logger.warning("No CSV files provided for processing plan")
            return ProcessingPlan(csv_files=[], estimated_rows=0)
        
        # Sort files for consistent processing order
        sorted_files = sorted(csv_files)
        
        # Estimate total rows (basic estimation)
        estimated_rows = self._estimate_total_rows(sorted_files)
        
        plan = ProcessingPlan(
            csv_files=sorted_files,
            estimated_rows=estimated_rows,
            processing_order=sorted_files.copy()
        )
        
        self.logger.info(f"Created processing plan for {len(sorted_files)} files, estimated {estimated_rows} rows")
        return plan
    
    def _estimate_total_rows(self, csv_files: List[Path]) -> int:
        """
        Estimate total number of rows across all CSV files.
        
        Args:
            csv_files: List of CSV file paths
            
        Returns:
            Estimated total row count
        """
        total_estimated = 0
        
        for csv_file in csv_files:
            try:
                # Quick estimation by counting lines
                with open(csv_file, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                    # Subtract 1 for header row if present
                    estimated_rows = max(0, line_count - 1)
                    total_estimated += estimated_rows
                    
            except Exception as e:
                self.logger.warning(f"Could not estimate rows for {csv_file}: {e}")
                # Use default estimation
                total_estimated += 10
        
        return total_estimated
    
    def scan_for_csv_files(self, directory_path: Path) -> ScanResult:
        """
        Comprehensive scan for CSV files in directory.
        
        Args:
            directory_path: Path to directory to scan
            
        Returns:
            ScanResult with detailed information about the scan
        """
        errors = []
        warnings = []
        csv_files = []
        ignored_files = []
        total_files = 0
        
        try:
            # Scan directory for all files
            all_files = self.scan_directory(directory_path)
            total_files = len(all_files)
            
            # Separate CSV files from others
            for file_path in all_files:
                if file_path.suffix in self.CSV_EXTENSIONS:
                    if not self._should_ignore_file(file_path):
                        csv_files.append(file_path)
                    else:
                        ignored_files.append(file_path)
                        warnings.append(f"Ignored CSV file due to pattern: {file_path.name}")
                else:
                    ignored_files.append(file_path)
            
            # Validate CSV files
            valid_csv_files = []
            for csv_file in csv_files:
                if self._validate_csv_file(csv_file):
                    valid_csv_files.append(csv_file)
                else:
                    warnings.append(f"CSV file may be invalid: {csv_file.name}")
                    # Still include it, let CSVReader handle the error
                    valid_csv_files.append(csv_file)
            
            csv_files = valid_csv_files
            
        except FileNotFoundError as e:
            errors.append(f"Directory not found: {str(e)}")
        except PermissionError as e:
            errors.append(f"Permission denied: {str(e)}")
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
        
        result = ScanResult(
            directory=directory_path,
            total_files=total_files,
            csv_files=csv_files,
            ignored_files=ignored_files,
            errors=errors,
            warnings=warnings
        )
        
        self.logger.info(f"Scan complete: {len(csv_files)} CSV files, {len(ignored_files)} ignored, {len(errors)} errors")
        return result
    
    def _validate_csv_file(self, csv_file: Path) -> bool:
        """
        Basic validation of CSV file.
        
        Args:
            csv_file: Path to CSV file
            
        Returns:
            True if file appears to be a valid CSV
        """
        try:
            # Check if file is readable and not empty
            if csv_file.stat().st_size == 0:
                return False
            
            # Try to read first few lines
            with open(csv_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if not first_line:
                    return False
                
                # Check if it looks like CSV (has commas)
                if ',' not in first_line:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"CSV validation failed for {csv_file}: {e}")
            return False
    
    def get_directory_info(self, directory_path: Path) -> Dict[str, Any]:
        """
        Get information about a directory without full scanning.
        
        Args:
            directory_path: Path to directory
            
        Returns:
            Dictionary with directory information
        """
        try:
            if not directory_path.exists():
                return {
                    "exists": False,
                    "error": "Directory does not exist"
                }
            
            if not directory_path.is_dir():
                return {
                    "exists": True,
                    "is_directory": False,
                    "error": "Path is not a directory"
                }
            
            # Quick scan for file counts
            total_files = 0
            csv_count = 0
            
            try:
                for item in directory_path.iterdir():
                    if item.is_file():
                        total_files += 1
                        if item.suffix in self.CSV_EXTENSIONS:
                            csv_count += 1
            except PermissionError:
                return {
                    "exists": True,
                    "is_directory": True,
                    "error": "Permission denied"
                }
            
            return {
                "exists": True,
                "is_directory": True,
                "total_files": total_files,
                "csv_files": csv_count,
                "readable": True,
                "recursive_scan": self.recursive
            }
            
        except Exception as e:
            return {
                "exists": False,
                "error": str(e)
            }


def create_directory_scanner(recursive: bool = True, follow_symlinks: bool = False) -> DirectoryScanner:
    """
    Factory function to create a DirectoryScanner instance.
    
    Args:
        recursive: Whether to scan subdirectories recursively
        follow_symlinks: Whether to follow symbolic links
        
    Returns:
        Configured DirectoryScanner instance
    """
    return DirectoryScanner(recursive=recursive, follow_symlinks=follow_symlinks)