"""
Temporary File Cleaner for repository cleanup operations.

This module provides safe identification, categorization, and removal of temporary
files to maintain a clean repository structure.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import logging
from datetime import datetime

from .file_analysis_engine import FileAnalysisEngine, FileInfo
from .safety_validator import SafetyValidator


@dataclass
class TemporaryFileCategory:
    """Information about a category of temporary files."""
    name: str
    description: str
    patterns: List[str]
    files: List[str] = field(default_factory=list)
    safe_to_delete: bool = True
    requires_confirmation: bool = False


class TemporaryFileCleaner:
    """
    Cleaner for safely removing temporary and unnecessary files.
    
    Provides methods to identify temporary files by pattern, categorize them
    by type, validate removal safety, and perform cleanup operations with
    proper logging and gitignore updates.
    """
    
    def __init__(self, root_path: str = ".", file_analysis_engine: Optional[FileAnalysisEngine] = None):
        """
        Initialize the temporary file cleaner.
        
        Args:
            root_path: Root directory to clean (default: current directory)
            file_analysis_engine: Optional existing file analysis engine
        """
        self.root_path = Path(root_path).resolve()
        self.file_analysis_engine = file_analysis_engine or FileAnalysisEngine(str(self.root_path))
        self.safety_validator = SafetyValidator(str(self.root_path))
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Define temporary file categories
        self.temp_categories = self._initialize_temp_categories()
    
    def identify_temp_patterns(self) -> List[str]:
        """
        Get all temporary file patterns used for identification.
        
        Returns:
            List of regex patterns for temporary files
        """
        patterns = []
        for category in self.temp_categories.values():
            patterns.extend(category.patterns)
        return patterns
    
    def categorize_temp_files(self) -> Dict[str, List[str]]:
        """
        Categorize all temporary files found in the repository.
        
        Returns:
            Dictionary mapping category names to lists of file paths
        """
        # Ensure file inventory is populated
        if not self.file_analysis_engine.file_inventory:
            self.file_analysis_engine.scan_directory_structure()
        
        categorized_files = defaultdict(list)
        
        # Scan all files and categorize temporary ones
        for file_path, file_info in self.file_analysis_engine.file_inventory.items():
            category = self._categorize_temp_file(file_path)
            if category:
                categorized_files[category].append(file_path)
                self.temp_categories[category].files.append(file_path)
        
        # Also scan for files that might not be in inventory yet
        self._scan_for_additional_temp_files(categorized_files)
        
        return dict(categorized_files)
    
    def validate_removal_safety(self, files: List[str]) -> Dict[str, bool]:
        """
        Validate that files are safe to remove.
        
        Args:
            files: List of file paths to validate
            
        Returns:
            Dictionary mapping file paths to safety status (True = safe to remove)
        """
        safety_results = {}
        
        for file_path in files:
            full_path = self.root_path / file_path
            
            # Basic safety checks
            is_safe = True
            
            # Check if file exists
            if not full_path.exists():
                safety_results[file_path] = False
                self.logger.warning(f"File does not exist: {file_path}")
                continue
            
            # Use safety validator for comprehensive checks
            try:
                is_safe = self.safety_validator.validate_file_safety(file_path)
                
                # Additional checks for temporary files
                if is_safe:
                    is_safe = self._additional_temp_file_safety_checks(file_path)
                
            except Exception as e:
                self.logger.error(f"Error validating safety for {file_path}: {e}")
                is_safe = False
            
            safety_results[file_path] = is_safe
            
            if not is_safe:
                self.logger.warning(f"File marked as unsafe to remove: {file_path}")
        
        return safety_results
    
    def clean_temporary_files(self, files: List[str], dry_run: bool = True) -> Dict[str, str]:
        """
        Clean temporary files with safety validation and logging.
        
        Args:
            files: List of file paths to clean
            dry_run: If True, only simulate the cleanup (default: True)
            
        Returns:
            Dictionary mapping file paths to operation results
        """
        results = {}
        
        # Validate safety first
        safety_results = self.validate_removal_safety(files)
        safe_files = [f for f, safe in safety_results.items() if safe]
        unsafe_files = [f for f, safe in safety_results.items() if not safe]
        
        # Log unsafe files
        if unsafe_files:
            self.logger.warning(f"Skipping {len(unsafe_files)} unsafe files: {unsafe_files}")
            for file_path in unsafe_files:
                results[file_path] = "SKIPPED - Unsafe to remove"
        
        # Process safe files
        if dry_run:
            self.logger.info(f"DRY RUN: Would remove {len(safe_files)} temporary files")
            for file_path in safe_files:
                results[file_path] = "DRY RUN - Would be removed"
        else:
            self.logger.info(f"Removing {len(safe_files)} temporary files")
            
            # Create backup before removal
            backup_path = self._create_cleanup_backup(safe_files)
            if backup_path:
                self.logger.info(f"Created backup at: {backup_path}")
            
            # Remove files
            for file_path in safe_files:
                try:
                    full_path = self.root_path / file_path
                    
                    if full_path.is_file():
                        full_path.unlink()
                        results[file_path] = "REMOVED - File deleted"
                        self.logger.info(f"Removed file: {file_path}")
                    elif full_path.is_dir():
                        shutil.rmtree(full_path)
                        results[file_path] = "REMOVED - Directory deleted"
                        self.logger.info(f"Removed directory: {file_path}")
                    else:
                        results[file_path] = "SKIPPED - Not a file or directory"
                        
                except Exception as e:
                    results[file_path] = f"ERROR - {str(e)}"
                    self.logger.error(f"Failed to remove {file_path}: {e}")
        
        return results
    
    def update_gitignore(self, patterns: List[str]) -> None:
        """
        Update .gitignore file to prevent future accumulation of temporary files.
        
        Args:
            patterns: List of patterns to add to .gitignore
        """
        gitignore_path = self.root_path / ".gitignore"
        
        # Read existing .gitignore
        existing_patterns = set()
        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    existing_patterns = set(line.strip() for line in f if line.strip() and not line.startswith('#'))
            except Exception as e:
                self.logger.error(f"Error reading .gitignore: {e}")
                return
        
        # Determine new patterns to add
        new_patterns = []
        for pattern in patterns:
            # Convert regex patterns to gitignore patterns
            gitignore_pattern = self._regex_to_gitignore_pattern(pattern)
            if gitignore_pattern and gitignore_pattern not in existing_patterns:
                new_patterns.append(gitignore_pattern)
        
        # Add new patterns if any
        if new_patterns:
            try:
                with open(gitignore_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n# Temporary files (added by cleanup on {datetime.now().strftime('%Y-%m-%d')})\n")
                    for pattern in new_patterns:
                        f.write(f"{pattern}\n")
                
                self.logger.info(f"Added {len(new_patterns)} patterns to .gitignore: {new_patterns}")
            except Exception as e:
                self.logger.error(f"Error updating .gitignore: {e}")
        else:
            self.logger.info("No new patterns to add to .gitignore")
    
    def _initialize_temp_categories(self) -> Dict[str, TemporaryFileCategory]:
        """Initialize temporary file categories with patterns."""
        categories = {}
        
        # Exported configuration files
        categories["exported_configs"] = TemporaryFileCategory(
            name="exported_configs",
            description="Exported configuration files with timestamps",
            patterns=[r"exported_config_\d{8}_\d{6}\.json$"],
            safe_to_delete=True,
            requires_confirmation=False
        )
        
        # Python cache files
        categories["python_cache"] = TemporaryFileCategory(
            name="python_cache",
            description="Python bytecode cache files and directories",
            patterns=[r"__pycache__", r"\.pyc$", r"\.pyo$"],
            safe_to_delete=True,
            requires_confirmation=False
        )
        
        # System files
        categories["system_files"] = TemporaryFileCategory(
            name="system_files",
            description="Operating system generated files",
            patterns=[r"\.DS_Store$", r"Thumbs\.db$", r"desktop\.ini$"],
            safe_to_delete=True,
            requires_confirmation=False
        )
        
        # LaTeX temporary files
        categories["latex_temp"] = TemporaryFileCategory(
            name="latex_temp",
            description="LaTeX compilation temporary files",
            patterns=[
                r"\.aux$", r"\.fdb_latexmk$", r"\.fls$", r"\.synctex\.gz$",
                r"\.toc$", r"\.out$", r"\.nav$", r"\.snm$", r"\.vrb$",
                r"texput\.log$"
            ],
            safe_to_delete=True,
            requires_confirmation=False
        )
        
        # Log files (with caution)
        categories["log_files"] = TemporaryFileCategory(
            name="log_files",
            description="Log files that may be safe to remove",
            patterns=[r"\.log$"],
            safe_to_delete=False,  # Requires manual review
            requires_confirmation=True
        )
        
        # Build artifacts
        categories["build_artifacts"] = TemporaryFileCategory(
            name="build_artifacts",
            description="Build and compilation artifacts",
            patterns=[r"\.egg-info/", r"build/", r"dist/"],
            safe_to_delete=True,
            requires_confirmation=True
        )
        
        return categories
    
    def _categorize_temp_file(self, file_path: str) -> Optional[str]:
        """Categorize a file as temporary based on patterns."""
        for category_name, category in self.temp_categories.items():
            for pattern in category.patterns:
                if re.search(pattern, file_path):
                    return category_name
        return None
    
    def _scan_for_additional_temp_files(self, categorized_files: Dict[str, List[str]]) -> None:
        """Scan for additional temporary files that might not be in inventory."""
        # Scan root directory for exported config files
        for file_path in self.root_path.glob("exported_config_*.json"):
            relative_path = str(file_path.relative_to(self.root_path))
            if relative_path not in categorized_files["exported_configs"]:
                categorized_files["exported_configs"].append(relative_path)
        
        # Scan for __pycache__ directories
        for pycache_dir in self.root_path.rglob("__pycache__"):
            relative_path = str(pycache_dir.relative_to(self.root_path))
            if relative_path not in categorized_files["python_cache"]:
                categorized_files["python_cache"].append(relative_path)
        
        # Scan for .DS_Store files
        for ds_store in self.root_path.rglob(".DS_Store"):
            relative_path = str(ds_store.relative_to(self.root_path))
            if relative_path not in categorized_files["system_files"]:
                categorized_files["system_files"].append(relative_path)
    
    def _additional_temp_file_safety_checks(self, file_path: str) -> bool:
        """Additional safety checks specific to temporary files."""
        full_path = self.root_path / file_path
        
        # Don't remove files that are very recent (less than 1 hour old)
        # This prevents removing files from active processes
        try:
            stat = full_path.stat()
            age_hours = (datetime.now().timestamp() - stat.st_mtime) / 3600
            if age_hours < 1:
                self.logger.info(f"File too recent to remove safely: {file_path} (age: {age_hours:.1f} hours)")
                return False
        except Exception:
            pass
        
        # Don't remove files in critical directories
        critical_dirs = {".git", ".kiro", "src", "tests"}
        path_parts = Path(file_path).parts
        if any(part in critical_dirs for part in path_parts):
            # Exception for __pycache__ and .DS_Store in these directories
            if not (file_path.endswith(("__pycache__", ".DS_Store")) or "__pycache__" in file_path):
                return False
        
        return True
    
    def _create_cleanup_backup(self, files: List[str]) -> Optional[str]:
        """Create a backup of files before cleanup."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.root_path / f".cleanup_backup_{timestamp}"
            backup_dir.mkdir(exist_ok=True)
            
            for file_path in files:
                source_path = self.root_path / file_path
                if source_path.exists():
                    # Create directory structure in backup
                    backup_file_path = backup_dir / file_path
                    backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if source_path.is_file():
                        shutil.copy2(source_path, backup_file_path)
                    elif source_path.is_dir():
                        shutil.copytree(source_path, backup_file_path, dirs_exist_ok=True)
            
            return str(backup_dir)
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
    
    def _regex_to_gitignore_pattern(self, regex_pattern: str) -> Optional[str]:
        """Convert regex pattern to gitignore pattern."""
        # Simple conversions for common patterns
        conversions = {
            r"exported_config_\d{8}_\d{6}\.json$": "exported_config_*.json",
            r"__pycache__": "__pycache__/",
            r"\.DS_Store$": ".DS_Store",
            r"\.pyc$": "*.pyc",
            r"\.pyo$": "*.pyo",
            r"\.log$": "*.log",
            r"\.aux$": "*.aux",
            r"\.fdb_latexmk$": "*.fdb_latexmk",
            r"\.fls$": "*.fls",
            r"\.synctex\.gz$": "*.synctex.gz",
            r"\.toc$": "*.toc",
            r"\.out$": "*.out",
            r"\.nav$": "*.nav",
            r"\.snm$": "*.snm",
            r"\.vrb$": "*.vrb",
            r"texput\.log$": "texput.log",
        }
        
        return conversions.get(regex_pattern)