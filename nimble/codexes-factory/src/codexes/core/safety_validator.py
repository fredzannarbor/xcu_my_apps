"""
Safety Validator for repository cleanup operations.

This module provides comprehensive safety validation, backup creation,
and rollback mechanisms for safe file operations during cleanup.
"""

import os
import shutil
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import tempfile
import subprocess
import psutil


@dataclass
class BackupInfo:
    """Information about a backup operation."""
    backup_id: str
    timestamp: datetime
    backup_path: str
    original_files: List[str]
    backup_manifest: Dict[str, str]
    operation_type: str
    completed: bool = False


@dataclass
class SafetyCheck:
    """Result of a safety validation check."""
    file_path: str
    is_safe: bool
    reason: str
    warnings: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


class SafetyValidator:
    """
    Validator for ensuring file operations are safe and reversible.
    
    Provides methods to validate file safety, create backups, and
    implement rollback mechanisms for failed operations.
    """
    
    def __init__(self, root_path: str = ".", backup_dir: str = ".cleanup_backups"):
        """
        Initialize the safety validator.
        
        Args:
            root_path: Root directory for operations (default: current directory)
            backup_dir: Directory to store backups (default: .cleanup_backups)
        """
        self.root_path = Path(root_path).resolve()
        self.backup_dir = self.root_path / backup_dir
        self.backup_dir.mkdir(exist_ok=True)
        
        # Critical files that should never be deleted
        self.critical_files = {
            ".git",
            ".gitignore",
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            ".env",
            "docs/readme/codexes_factory_ai_assisted_publishing_platform_v32.md",
            "LICENSE",
        }
        
        # Critical directories that should never be removed
        self.critical_directories = {
            ".git",
            "src",
            "tests",
            ".venv",
        }
        
        # Files currently in use (will be populated by process checking)
        self.files_in_use: Set[str] = set()
        
        # Backup registry
        self.backup_registry: Dict[str, BackupInfo] = {}
        self._load_backup_registry()
    
    def validate_file_safety(self, file_path: str) -> SafetyCheck:
        """
        Validate if a file is safe to move or delete.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            SafetyCheck object with validation results
        """
        path = Path(file_path)
        warnings = []
        
        # Check if file exists
        if not (self.root_path / path).exists():
            return SafetyCheck(
                file_path=file_path,
                is_safe=False,
                reason="File does not exist",
                warnings=warnings
            )
        
        # Check if it's a critical file
        if path.name in self.critical_files or str(path) in self.critical_files:
            return SafetyCheck(
                file_path=file_path,
                is_safe=False,
                reason="File is marked as critical",
                warnings=warnings
            )
        
        # Check if it's in a critical directory
        for critical_dir in self.critical_directories:
            if str(path).startswith(critical_dir + "/") or str(path) == critical_dir:
                if not self._is_safe_within_critical_dir(path, critical_dir):
                    return SafetyCheck(
                        file_path=file_path,
                        is_safe=False,
                        reason=f"File is in critical directory: {critical_dir}",
                        warnings=warnings
                    )
        
        # Check if file is currently in use
        if self._is_file_in_use(file_path):
            return SafetyCheck(
                file_path=file_path,
                is_safe=False,
                reason="File is currently in use by a running process",
                warnings=warnings
            )
        
        # Check file permissions
        full_path = self.root_path / path
        if not os.access(full_path, os.R_OK | os.W_OK):
            return SafetyCheck(
                file_path=file_path,
                is_safe=False,
                reason="Insufficient permissions to modify file",
                warnings=warnings
            )
        
        # Check if it's a large file (warn but don't block)
        if full_path.is_file() and full_path.stat().st_size > 100 * 1024 * 1024:  # 100MB
            warnings.append("File is larger than 100MB")
        
        # Check if it's recently modified (warn but don't block)
        if full_path.is_file():
            mod_time = full_path.stat().st_mtime
            if time.time() - mod_time < 3600:  # Modified in last hour
                warnings.append("File was modified within the last hour")
        
        return SafetyCheck(
            file_path=file_path,
            is_safe=True,
            reason="File passed all safety checks",
            warnings=warnings
        )
    
    def check_dependencies(self, file_path: str) -> List[str]:
        """
        Check what other files depend on the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            List of files that depend on the given file
        """
        dependencies = []
        path = Path(file_path)
        
        # For Python files, check for imports
        if path.suffix == '.py':
            module_name = self._get_module_name(file_path)
            dependencies.extend(self._find_python_dependencies(module_name))
        
        # For config files, check for references
        elif path.suffix == '.json':
            dependencies.extend(self._find_config_dependencies(file_path))
        
        # For any file, do a text search for references
        dependencies.extend(self._find_text_references(file_path))
        
        return list(set(dependencies))  # Remove duplicates
    
    def create_backup(self, files: List[str], operation_type: str = "cleanup") -> str:
        """
        Create a backup of the specified files.
        
        Args:
            files: List of file paths to backup
            operation_type: Type of operation being performed
            
        Returns:
            Backup ID for the created backup
        """
        backup_id = self._generate_backup_id()
        timestamp = datetime.now()
        backup_path = self.backup_dir / f"backup_{backup_id}"
        backup_path.mkdir(exist_ok=True)
        
        backup_manifest = {}
        
        for file_path in files:
            source_path = self.root_path / file_path
            if not source_path.exists():
                continue
            
            # Create backup directory structure
            relative_path = Path(file_path)
            backup_file_path = backup_path / relative_path
            backup_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file to backup
            if source_path.is_file():
                shutil.copy2(source_path, backup_file_path)
                # Calculate checksum for verification
                checksum = self._calculate_checksum(source_path)
                backup_manifest[file_path] = checksum
            elif source_path.is_dir():
                shutil.copytree(source_path, backup_file_path, dirs_exist_ok=True)
                backup_manifest[file_path] = "directory"
        
        # Save backup info
        backup_info = BackupInfo(
            backup_id=backup_id,
            timestamp=timestamp,
            backup_path=str(backup_path),
            original_files=files,
            backup_manifest=backup_manifest,
            operation_type=operation_type,
            completed=True
        )
        
        self.backup_registry[backup_id] = backup_info
        self._save_backup_registry()
        
        # Save manifest file
        manifest_path = backup_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump({
                'backup_id': backup_id,
                'timestamp': timestamp.isoformat(),
                'operation_type': operation_type,
                'files': backup_manifest
            }, f, indent=2)
        
        return backup_id
    
    def verify_move_safety(self, source: str, destination: str) -> bool:
        """
        Verify that moving a file from source to destination is safe.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if the move is safe, False otherwise
        """
        source_path = self.root_path / source
        dest_path = self.root_path / destination
        
        # Check if source exists
        if not source_path.exists():
            return False
        
        # Check if destination already exists
        if dest_path.exists():
            return False
        
        # Check if destination directory exists or can be created
        dest_dir = dest_path.parent
        if not dest_dir.exists():
            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                return False
        
        # Check permissions
        if not os.access(source_path, os.R_OK | os.W_OK):
            return False
        
        if not os.access(dest_dir, os.W_OK):
            return False
        
        # Check if source file is safe to move
        safety_check = self.validate_file_safety(source)
        return safety_check.is_safe
    
    def validate_reference_updates(self, updates: Dict[str, str]) -> bool:
        """
        Validate that reference updates are safe and correct.
        
        Args:
            updates: Dictionary mapping old paths to new paths
            
        Returns:
            True if all updates are valid, False otherwise
        """
        for old_path, new_path in updates.items():
            # Check if old path exists
            if not (self.root_path / old_path).exists():
                return False
            
            # Check if new path is valid
            new_full_path = self.root_path / new_path
            if not new_full_path.parent.exists():
                return False
        
        return True
    
    def rollback_operation(self, backup_id: str) -> bool:
        """
        Rollback an operation using the specified backup.
        
        Args:
            backup_id: ID of the backup to restore
            
        Returns:
            True if rollback was successful, False otherwise
        """
        if backup_id not in self.backup_registry:
            return False
        
        backup_info = self.backup_registry[backup_id]
        backup_path = Path(backup_info.backup_path)
        
        if not backup_path.exists():
            return False
        
        try:
            # Restore each file from backup
            for file_path in backup_info.original_files:
                backup_file_path = backup_path / file_path
                original_path = self.root_path / file_path
                
                if backup_file_path.exists():
                    # Remove current file if it exists
                    if original_path.exists():
                        if original_path.is_file():
                            original_path.unlink()
                        elif original_path.is_dir():
                            shutil.rmtree(original_path)
                    
                    # Restore from backup
                    original_path.parent.mkdir(parents=True, exist_ok=True)
                    if backup_file_path.is_file():
                        shutil.copy2(backup_file_path, original_path)
                    elif backup_file_path.is_dir():
                        shutil.copytree(backup_file_path, original_path)
            
            return True
        
        except Exception as e:
            print(f"Error during rollback: {e}")
            return False
    
    def cleanup_old_backups(self, keep_days: int = 7) -> List[str]:
        """
        Clean up old backup directories.
        
        Args:
            keep_days: Number of days to keep backups
            
        Returns:
            List of removed backup IDs
        """
        removed_backups = []
        cutoff_time = time.time() - (keep_days * 24 * 3600)
        
        for backup_id, backup_info in list(self.backup_registry.items()):
            if backup_info.timestamp.timestamp() < cutoff_time:
                backup_path = Path(backup_info.backup_path)
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                
                del self.backup_registry[backup_id]
                removed_backups.append(backup_id)
        
        self._save_backup_registry()
        return removed_backups
    
    def _is_safe_within_critical_dir(self, path: Path, critical_dir: str) -> bool:
        """Check if a file within a critical directory is safe to modify."""
        # Allow certain operations within critical directories
        if critical_dir == "src":
            # Allow moving test files out of src
            return path.name.startswith("test_")
        elif critical_dir == "tests":
            # Generally safe to reorganize within tests
            return True
        
        return False
    
    def _is_file_in_use(self, file_path: str) -> bool:
        """Check if a file is currently in use by any process."""
        full_path = self.root_path / file_path
        
        try:
            # Try to get processes that have the file open
            for proc in psutil.process_iter(['pid', 'name', 'open_files']):
                try:
                    if proc.info['open_files']:
                        for open_file in proc.info['open_files']:
                            if Path(open_file.path) == full_path:
                                return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            # If we can't check, err on the side of caution for critical files
            if full_path.suffix == '.py':
                return True
        
        return False
    
    def _get_module_name(self, file_path: str) -> str:
        """Get the Python module name for a file path."""
        path = Path(file_path)
        if path.suffix != '.py':
            return ""
        
        # Convert file path to module name
        parts = path.with_suffix('').parts
        if parts[0] == 'src':
            parts = parts[1:]  # Remove 'src' prefix
        
        return '.'.join(parts)
    
    def _find_python_dependencies(self, module_name: str) -> List[str]:
        """Find Python files that import the given module."""
        dependencies = []
        
        # Search for import statements
        for root, dirs, files in os.walk(self.root_path):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in {'.git', '.venv', '__pycache__'}]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Look for import statements
                        import_patterns = [
                            f"import {module_name}",
                            f"from {module_name}",
                            f"import {module_name.split('.')[-1]}",
                        ]
                        
                        for pattern in import_patterns:
                            if pattern in content:
                                rel_path = str(file_path.relative_to(self.root_path))
                                dependencies.append(rel_path)
                                break
                    
                    except Exception:
                        continue
        
        return dependencies
    
    def _find_config_dependencies(self, file_path: str) -> List[str]:
        """Find files that reference the given config file."""
        dependencies = []
        config_name = Path(file_path).name
        
        # Search for references to the config file
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in {'.git', '.venv', '__pycache__'}]
            
            for file in files:
                if file.endswith(('.py', '.json', '.md')):
                    file_path_full = Path(root) / file
                    try:
                        with open(file_path_full, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if config_name in content or file_path in content:
                            rel_path = str(file_path_full.relative_to(self.root_path))
                            dependencies.append(rel_path)
                    
                    except Exception:
                        continue
        
        return dependencies
    
    def _find_text_references(self, file_path: str) -> List[str]:
        """Find text references to the given file."""
        dependencies = []
        file_name = Path(file_path).name
        
        # Search for text references
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in {'.git', '.venv', '__pycache__'}]
            
            for file in files:
                if file.endswith(('.py', '.md', '.txt', '.json')):
                    file_path_full = Path(root) / file
                    try:
                        with open(file_path_full, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Look for various reference patterns
                        if (file_name in content or 
                            file_path in content or 
                            str(Path(file_path)) in content):
                            rel_path = str(file_path_full.relative_to(self.root_path))
                            dependencies.append(rel_path)
                    
                    except Exception:
                        continue
        
        return dependencies
    
    def _generate_backup_id(self) -> str:
        """Generate a unique backup ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        return f"{timestamp}_{random_suffix}"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _load_backup_registry(self) -> None:
        """Load the backup registry from disk."""
        registry_path = self.backup_dir / "registry.json"
        if registry_path.exists():
            try:
                with open(registry_path, 'r') as f:
                    data = json.load(f)
                
                for backup_id, backup_data in data.items():
                    self.backup_registry[backup_id] = BackupInfo(
                        backup_id=backup_data['backup_id'],
                        timestamp=datetime.fromisoformat(backup_data['timestamp']),
                        backup_path=backup_data['backup_path'],
                        original_files=backup_data['original_files'],
                        backup_manifest=backup_data['backup_manifest'],
                        operation_type=backup_data['operation_type'],
                        completed=backup_data.get('completed', True)
                    )
            except Exception as e:
                print(f"Warning: Could not load backup registry: {e}")
    
    def _save_backup_registry(self) -> None:
        """Save the backup registry to disk."""
        registry_path = self.backup_dir / "registry.json"
        
        data = {}
        for backup_id, backup_info in self.backup_registry.items():
            data[backup_id] = {
                'backup_id': backup_info.backup_id,
                'timestamp': backup_info.timestamp.isoformat(),
                'backup_path': backup_info.backup_path,
                'original_files': backup_info.original_files,
                'backup_manifest': backup_info.backup_manifest,
                'operation_type': backup_info.operation_type,
                'completed': backup_info.completed
            }
        
        with open(registry_path, 'w') as f:
            json.dump(data, f, indent=2)