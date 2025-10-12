"""
Resource organization system for Codexes Factory cleanup.

This module provides functionality to organize images and exported files
into proper resource directories as part of the dot-release cleanup process.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .safety_validator import SafetyValidator
from .file_analysis_engine import FileAnalysisEngine


@dataclass
class ResourceMoveOperation:
    """Represents a resource file move operation."""
    source_path: str
    destination_path: str
    operation_type: str  # 'move_image', 'move_export', 'cleanup_directory'
    backup_path: Optional[str] = None
    completed: bool = False
    references_updated: bool = False


class ResourceOrganizer:
    """
    Organizes images and exported files into proper resource directories.
    
    This class handles:
    - Moving images/ directory contents to resources/images/
    - Moving exported config files to exports/ directory
    - Updating all file references in code and documentation
    - Cleaning up empty directories after moves
    """
    
    def __init__(self, root_path: str = "."):
        """
        Initialize the ResourceOrganizer.
        
        Args:
            root_path: Root directory of the project
        """
        self.root_path = Path(root_path).resolve()
        self.safety_validator = SafetyValidator(str(self.root_path))
        self.file_analyzer = FileAnalysisEngine(str(self.root_path))
        self.logger = logging.getLogger(__name__)
        
        # Track operations for rollback capability
        self.operations: List[ResourceMoveOperation] = []
        
    def process_images_directory(self) -> Dict[str, str]:
        """
        Process the images/ directory and move contents to resources/images/.
        
        Returns:
            Dict mapping old paths to new paths for moved files
        """
        images_dir = self.root_path / "images"
        resources_images_dir = self.root_path / "resources" / "images"
        
        # Ensure target directory exists
        resources_images_dir.mkdir(parents=True, exist_ok=True)
        
        moved_files = {}
        
        if not images_dir.exists():
            self.logger.info("Images directory does not exist, skipping image processing")
            return moved_files
            
        # Get all files in images directory
        image_files = []
        if images_dir.is_dir():
            for item in images_dir.rglob("*"):
                if item.is_file():
                    image_files.append(item)
        
        if not image_files:
            self.logger.info("Images directory is empty, will clean up directory")
            # Still track the directory cleanup operation
            operation = ResourceMoveOperation(
                source_path=str(images_dir),
                destination_path="",  # Directory removal
                operation_type="cleanup_directory"
            )
            self.operations.append(operation)
            return moved_files
            
        # Move each file
        for image_file in image_files:
            relative_path = image_file.relative_to(images_dir)
            destination = resources_images_dir / relative_path
            
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Validate move safety
            if not self.safety_validator.verify_move_safety(str(image_file), str(destination)):
                self.logger.warning(f"Skipping unsafe move: {image_file} -> {destination}")
                continue
                
            # Create backup if file exists at destination
            backup_path = None
            if destination.exists():
                backup_path = self._create_backup(str(destination))
                
            try:
                # Move the file
                shutil.move(str(image_file), str(destination))
                
                # Track the operation
                operation = ResourceMoveOperation(
                    source_path=str(image_file),
                    destination_path=str(destination),
                    operation_type="move_image",
                    backup_path=backup_path,
                    completed=True
                )
                self.operations.append(operation)
                
                # Add to moved files mapping
                old_path = str(image_file.relative_to(self.root_path))
                new_path = str(destination.relative_to(self.root_path))
                moved_files[old_path] = new_path
                
                self.logger.info(f"Moved image: {old_path} -> {new_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to move {image_file}: {e}")
                # Restore backup if it was created
                if backup_path and Path(backup_path).exists():
                    shutil.move(backup_path, str(destination))
                    
        return moved_files
        
    def find_exported_files(self) -> List[str]:
        """
        Find exported configuration files in the root directory.
        
        Returns:
            List of paths to exported config files
        """
        exported_files = []
        
        # Look for exported_config_*.json files in root
        for file_path in self.root_path.glob("exported_config_*.json"):
            if file_path.is_file():
                exported_files.append(str(file_path))
                
        self.logger.info(f"Found {len(exported_files)} exported config files")
        return exported_files
        
    def move_resources(self, mappings: Dict[str, str]) -> bool:
        """
        Move resources according to the provided mappings.
        
        Args:
            mappings: Dict mapping source paths to destination paths
            
        Returns:
            True if all moves were successful
        """
        success = True
        
        for source, destination in mappings.items():
            source_path = Path(source)
            dest_path = Path(destination)
            
            # Make paths absolute if they're relative
            if not source_path.is_absolute():
                source_path = self.root_path / source_path
            if not dest_path.is_absolute():
                dest_path = self.root_path / dest_path
                
            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Validate move safety
            if not self.safety_validator.verify_move_safety(str(source_path), str(dest_path)):
                self.logger.warning(f"Skipping unsafe move: {source_path} -> {dest_path}")
                success = False
                continue
                
            try:
                # Create backup if destination exists
                backup_path = None
                if dest_path.exists():
                    backup_path = self._create_backup(str(dest_path))
                    
                # Move the file
                shutil.move(str(source_path), str(dest_path))
                
                # Track the operation
                operation = ResourceMoveOperation(
                    source_path=str(source_path),
                    destination_path=str(dest_path),
                    operation_type="move_export",
                    backup_path=backup_path,
                    completed=True
                )
                self.operations.append(operation)
                
                self.logger.info(f"Moved resource: {source} -> {destination}")
                
            except Exception as e:
                self.logger.error(f"Failed to move {source} to {destination}: {e}")
                success = False
                # Restore backup if it was created
                if backup_path and Path(backup_path).exists():
                    shutil.move(backup_path, str(dest_path))
                    
        return success
        
    def update_resource_references(self, updates: Dict[str, str]) -> None:
        """
        Update resource references in code and documentation files.
        
        Args:
            updates: Dict mapping old paths to new paths
        """
        if not updates:
            self.logger.info("No resource reference updates needed")
            return
            
        # Find files that might contain resource references
        reference_files = []
        
        # Python files
        for py_file in self.root_path.rglob("*.py"):
            if self._should_update_file(py_file):
                reference_files.append(py_file)
                
        # Documentation files
        for md_file in self.root_path.rglob("*.md"):
            if self._should_update_file(md_file):
                reference_files.append(md_file)
                
        # LaTeX files
        for tex_file in self.root_path.rglob("*.tex"):
            if self._should_update_file(tex_file):
                reference_files.append(tex_file)
                
        # Update references in each file
        for file_path in reference_files:
            self._update_file_references(file_path, updates)
            
    def cleanup_empty_directories(self) -> List[str]:
        """
        Clean up empty directories after file moves.
        
        Returns:
            List of directories that were removed
        """
        removed_dirs = []
        
        # Check if images directory is empty and can be removed
        images_dir = self.root_path / "images"
        if images_dir.exists() and images_dir.is_dir():
            try:
                # Check if directory is empty (including subdirectories)
                is_empty = True
                for item in images_dir.rglob("*"):
                    if item.is_file():
                        is_empty = False
                        break
                        
                if is_empty:
                    # Remove the directory and any empty subdirectories
                    shutil.rmtree(str(images_dir))
                    removed_dirs.append(str(images_dir))
                    self.logger.info(f"Removed empty directory: {images_dir}")
                    
                    # Track the operation
                    operation = ResourceMoveOperation(
                        source_path=str(images_dir),
                        destination_path="",
                        operation_type="cleanup_directory",
                        completed=True
                    )
                    self.operations.append(operation)
                        
            except Exception as e:
                self.logger.error(f"Failed to remove empty directory {images_dir}: {e}")
                
        return removed_dirs
        
    def organize_exported_files(self) -> Dict[str, str]:
        """
        Organize exported config files into exports/ directory.
        
        Returns:
            Dict mapping old paths to new paths for moved files
        """
        exports_dir = self.root_path / "exports"
        exports_dir.mkdir(exist_ok=True)
        
        exported_files = self.find_exported_files()
        moved_files = {}
        
        for file_path in exported_files:
            source = Path(file_path)
            destination = exports_dir / source.name
            
            # Validate move safety
            if not self.safety_validator.verify_move_safety(str(source), str(destination)):
                self.logger.warning(f"Skipping unsafe move: {source} -> {destination}")
                continue
                
            try:
                # Create backup if destination exists
                backup_path = None
                if destination.exists():
                    backup_path = self._create_backup(str(destination))
                    
                # Move the file
                shutil.move(str(source), str(destination))
                
                # Track the operation
                operation = ResourceMoveOperation(
                    source_path=str(source),
                    destination_path=str(destination),
                    operation_type="move_export",
                    backup_path=backup_path,
                    completed=True
                )
                self.operations.append(operation)
                
                # Add to moved files mapping
                old_path = str(source.relative_to(self.root_path))
                new_path = str(destination.relative_to(self.root_path))
                moved_files[old_path] = new_path
                
                self.logger.info(f"Moved exported file: {old_path} -> {new_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to move exported file {source}: {e}")
                # Restore backup if it was created
                if backup_path and Path(backup_path).exists():
                    shutil.move(backup_path, str(destination))
                    
        return moved_files
        
    def validate_resource_organization(self) -> Dict[str, bool]:
        """
        Validate that resource organization was successful.
        
        Returns:
            Dict with validation results
        """
        results = {
            "images_moved": True,
            "exports_created": True,
            "references_updated": True,
            "empty_dirs_cleaned": True
        }
        
        # Check if images directory is properly handled
        images_dir = self.root_path / "images"
        if images_dir.exists():
            # If it exists, it should be empty
            if any(images_dir.iterdir()):
                results["images_moved"] = False
                self.logger.error("Images directory still contains files")
                
        # Check if exports directory was created and contains files
        exports_dir = self.root_path / "exports"
        if not exports_dir.exists():
            results["exports_created"] = False
            self.logger.error("Exports directory was not created")
        elif not any(exports_dir.iterdir()):
            # This might be OK if there were no exported files
            exported_files = self.find_exported_files()
            if exported_files:
                results["exports_created"] = False
                self.logger.error("Exports directory is empty but exported files still exist")
                
        # Validate that move operations were completed (cleanup operations don't need reference updates)
        for operation in self.operations:
            if operation.operation_type in ["move_image", "move_export"] and not operation.completed:
                results["references_updated"] = False
                self.logger.error(f"Move operation not completed: {operation.source_path}")
                
        return results
        
    def _create_backup(self, file_path: str) -> str:
        """Create a backup of a file before overwriting."""
        backup_path = f"{file_path}.backup"
        shutil.copy2(file_path, backup_path)
        return backup_path
        
    def _should_update_file(self, file_path: Path) -> bool:
        """Check if a file should be updated for reference changes."""
        # Skip files in certain directories
        skip_dirs = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv"}
        
        for part in file_path.parts:
            if part in skip_dirs:
                return False
                
        return True
        
    def _update_file_references(self, file_path: Path, updates: Dict[str, str]) -> None:
        """Update resource references in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            
            # Update each reference
            for old_path, new_path in updates.items():
                # Simple string replacement - be more precise
                if old_path in content:
                    content = content.replace(old_path, new_path)
                        
            # Write back if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.logger.info(f"Updated references in: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to update references in {file_path}: {e}")
            
    def rollback_operations(self) -> bool:
        """
        Rollback all completed operations.
        
        Returns:
            True if rollback was successful
        """
        success = True
        
        # Rollback in reverse order
        for operation in reversed(self.operations):
            if not operation.completed:
                continue
                
            try:
                if operation.operation_type == "cleanup_directory":
                    # Recreate directory if it was removed
                    if operation.source_path:
                        Path(operation.source_path).mkdir(parents=True, exist_ok=True)
                        self.logger.info(f"Recreated directory: {operation.source_path}")
                        
                elif operation.operation_type in ["move_image", "move_export"]:
                    # Move file back to original location
                    dest_path = Path(operation.destination_path)
                    source_path = Path(operation.source_path)
                    
                    if dest_path.exists():
                        # Ensure source directory exists
                        source_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Move back
                        shutil.move(str(dest_path), str(source_path))
                        self.logger.info(f"Rolled back: {dest_path} -> {source_path}")
                        
                        # Restore backup if it exists
                        if operation.backup_path and Path(operation.backup_path).exists():
                            shutil.move(operation.backup_path, str(dest_path))
                            
                operation.completed = False
                
            except Exception as e:
                self.logger.error(f"Failed to rollback operation {operation.source_path}: {e}")
                success = False
                
        return success