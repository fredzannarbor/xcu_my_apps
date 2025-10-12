"""Configuration Directory Unification System

This module provides functionality to analyze and merge the config/ and configs/
directories into a single unified configuration structure.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import shutil
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class ConfigFile:
    """Represents a configuration file with metadata."""
    path: Path
    name: str
    content: Dict[str, Any]
    size: int
    modified_time: datetime
    content_hash: str


@dataclass
class ConflictResolution:
    """Represents a conflict resolution strategy."""
    source_file: Path
    target_file: Path
    resolution_type: str  # 'merge', 'replace', 'rename', 'skip'
    backup_path: Optional[Path] = None
    merge_strategy: Optional[str] = None


@dataclass
class MergeOperation:
    """Represents a file merge operation."""
    operation_type: str  # 'move', 'merge', 'copy', 'create_directory'
    source_path: Path
    target_path: Path
    backup_path: Optional[Path] = None
    completed: bool = False
    error: Optional[str] = None


class ConfigurationUnifier:
    """
    Unifies config/ and configs/ directories into a single config/ structure.
    
    This class analyzes both directories, detects conflicts, and provides
    strategies for merging them while preserving all necessary configurations.
    """
    
    def __init__(self, root_dir: str = "."):
        """
        Initialize the configuration unifier.
        
        Args:
            root_dir: Root directory of the project
        """
        self.root_dir = Path(root_dir)
        self.config_dir = self.root_dir / "config"
        self.configs_dir = self.root_dir / "configs"
        self.backup_dir = self.root_dir / ".cleanup_backups" / "config_unification"
        
        # Analysis results
        self.config_files: Dict[str, ConfigFile] = {}
        self.configs_files: Dict[str, ConfigFile] = {}
        self.conflicts: List[ConflictResolution] = []
        self.merge_operations: List[MergeOperation] = []
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_configuration_directories(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze both config/ and configs/ directory structures.
        
        Returns:
            Dictionary containing analysis results for both directories
        """
        logger.info("Analyzing configuration directories...")
        
        analysis = {
            "config_dir": self._analyze_directory(self.config_dir),
            "configs_dir": self._analyze_directory(self.configs_dir),
            "conflicts": [],
            "merge_strategy": {},
            "statistics": {}
        }
        
        # Load file contents and metadata
        self.config_files = self._load_config_files(self.config_dir)
        self.configs_files = self._load_config_files(self.configs_dir)
        
        # Detect conflicts
        self.conflicts = self._detect_conflicts()
        analysis["conflicts"] = [
            {
                "source": str(conflict.source_file),
                "target": str(conflict.target_file),
                "resolution_type": conflict.resolution_type,
                "merge_strategy": conflict.merge_strategy
            }
            for conflict in self.conflicts
        ]
        
        # Generate merge strategy
        analysis["merge_strategy"] = self._generate_merge_strategy()
        
        # Calculate statistics
        analysis["statistics"] = {
            "config_files_count": len(self.config_files),
            "configs_files_count": len(self.configs_files),
            "conflicts_count": len(self.conflicts),
            "total_size_config": sum(f.size for f in self.config_files.values()),
            "total_size_configs": sum(f.size for f in self.configs_files.values())
        }
        
        logger.info(f"Analysis complete: {len(self.config_files)} config files, "
                   f"{len(self.configs_files)} configs files, {len(self.conflicts)} conflicts")
        
        return analysis
    
    def identify_config_conflicts(self) -> List[Dict[str, str]]:
        """
        Identify conflicts between config/ and configs/ directories.
        
        Returns:
            List of conflict descriptions
        """
        conflicts = []
        
        for conflict in self.conflicts:
            conflict_info = {
                "type": "file_conflict",
                "source_file": str(conflict.source_file),
                "target_file": str(conflict.target_file),
                "resolution": conflict.resolution_type,
                "description": self._describe_conflict(conflict)
            }
            conflicts.append(conflict_info)
        
        return conflicts
    
    def create_merge_strategy(self) -> Dict[str, str]:
        """
        Create a comprehensive merge strategy that preserves all necessary configurations.
        
        Returns:
            Dictionary describing the merge strategy
        """
        strategy = {
            "approach": "preserve_existing_config_structure",
            "conflict_resolution": "intelligent_merge",
            "backup_strategy": "full_backup_before_merge",
            "validation_strategy": "content_validation_and_testing"
        }
        
        # Detailed merge plan
        merge_plan = []
        
        # 1. Create directory structure in config/
        target_structure = self._design_target_structure()
        for dir_path in target_structure["directories"]:
            merge_plan.append({
                "operation": "create_directory",
                "target": str(self.config_dir / dir_path),
                "description": f"Create directory structure: {dir_path}"
            })
        
        # 2. Move configs/ files to config/
        for relative_path, config_file in self.configs_files.items():
            target_path = self._determine_target_path(relative_path, config_file)
            
            # Check for conflicts
            conflict = self._find_conflict_for_file(relative_path)
            if conflict:
                merge_plan.append({
                    "operation": "merge_files",
                    "source": str(config_file.path),
                    "target": str(target_path),
                    "conflict_resolution": conflict.resolution_type,
                    "description": f"Merge {relative_path} with conflict resolution"
                })
            else:
                merge_plan.append({
                    "operation": "move_file",
                    "source": str(config_file.path),
                    "target": str(target_path),
                    "description": f"Move {relative_path} to unified structure"
                })
        
        # 3. Handle existing config/ files
        for relative_path, config_file in self.config_files.items():
            merge_plan.append({
                "operation": "preserve_file",
                "file": str(config_file.path),
                "description": f"Preserve existing config file: {relative_path}"
            })
        
        strategy["merge_plan"] = merge_plan
        strategy["operations_count"] = len(merge_plan)
        
        return strategy
    
    def execute_merge(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Execute the configuration merge operation.
        
        Args:
            dry_run: If True, only simulate the merge without making changes
            
        Returns:
            Dictionary containing merge results
        """
        logger.info(f"Executing configuration merge (dry_run={dry_run})...")
        
        results = {
            "success": False,
            "operations_completed": 0,
            "operations_failed": 0,
            "errors": [],
            "backup_location": str(self.backup_dir) if not dry_run else None,
            "dry_run": dry_run
        }
        
        try:
            # Create backup if not dry run
            if not dry_run:
                backup_success = self._create_full_backup()
                if not backup_success:
                    results["errors"].append("Failed to create backup")
                    return results
            
            # Execute merge operations
            for operation in self.merge_operations:
                try:
                    if dry_run:
                        logger.info(f"[DRY RUN] Would execute: {operation.operation_type} "
                                  f"{operation.source_path} -> {operation.target_path}")
                        operation.completed = True
                    else:
                        self._execute_operation(operation)
                    
                    results["operations_completed"] += 1
                    
                except Exception as e:
                    operation.error = str(e)
                    results["operations_failed"] += 1
                    results["errors"].append(f"Operation failed: {operation.operation_type} - {e}")
                    logger.error(f"Operation failed: {e}")
            
            # Validate merge results if not dry run
            if not dry_run:
                validation_results = self._validate_merge_results()
                results["validation"] = validation_results
                results["success"] = validation_results["all_valid"]
            else:
                results["success"] = results["operations_failed"] == 0
            
            logger.info(f"Merge {'simulation' if dry_run else 'execution'} complete: "
                       f"{results['operations_completed']} successful, "
                       f"{results['operations_failed']} failed")
            
        except Exception as e:
            results["errors"].append(f"Merge execution failed: {e}")
            logger.error(f"Merge execution failed: {e}")
        
        return results
    
    def _analyze_directory(self, directory: Path) -> Dict[str, Any]:
        """Analyze a single directory structure."""
        if not directory.exists():
            return {
                "exists": False,
                "files": [],
                "subdirectories": [],
                "total_files": 0,
                "total_size": 0
            }
        
        files = []
        subdirectories = []
        total_size = 0
        
        for item in directory.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(directory)
                file_info = {
                    "path": str(relative_path),
                    "name": item.name,
                    "size": item.stat().st_size,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                }
                files.append(file_info)
                total_size += file_info["size"]
            elif item.is_dir() and item != directory:
                relative_path = item.relative_to(directory)
                subdirectories.append(str(relative_path))
        
        return {
            "exists": True,
            "files": files,
            "subdirectories": sorted(subdirectories),
            "total_files": len(files),
            "total_size": total_size
        }
    
    def _load_config_files(self, directory: Path) -> Dict[str, ConfigFile]:
        """Load configuration files from a directory."""
        config_files = {}
        
        if not directory.exists():
            return config_files
        
        for file_path in directory.rglob("*.json"):
            try:
                relative_path = file_path.relative_to(directory)
                
                # Load content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                
                # Calculate hash
                content_str = json.dumps(content, sort_keys=True)
                content_hash = hashlib.md5(content_str.encode()).hexdigest()
                
                config_file = ConfigFile(
                    path=file_path,
                    name=file_path.name,
                    content=content,
                    size=file_path.stat().st_size,
                    modified_time=datetime.fromtimestamp(file_path.stat().st_mtime),
                    content_hash=content_hash
                )
                
                config_files[str(relative_path)] = config_file
                
            except Exception as e:
                logger.warning(f"Failed to load config file {file_path}: {e}")
        
        return config_files
    
    def _detect_conflicts(self) -> List[ConflictResolution]:
        """Detect conflicts between config/ and configs/ files."""
        conflicts = []
        
        for configs_path, configs_file in self.configs_files.items():
            # Determine target path in config/
            target_path = self._determine_target_path(configs_path, configs_file)
            target_relative = target_path.relative_to(self.config_dir)
            
            # Check if target already exists in config/
            if str(target_relative) in self.config_files:
                config_file = self.config_files[str(target_relative)]
                
                # Determine conflict resolution strategy
                resolution = self._determine_conflict_resolution(configs_file, config_file)
                
                conflicts.append(ConflictResolution(
                    source_file=configs_file.path,
                    target_file=target_path,
                    resolution_type=resolution["type"],
                    merge_strategy=resolution.get("strategy")
                ))
        
        return conflicts
    
    def _determine_target_path(self, relative_path: str, config_file: ConfigFile) -> Path:
        """Determine the target path for a configs/ file in the config/ structure."""
        path_parts = Path(relative_path).parts
        
        # Map configs/ subdirectories to config/ structure
        if len(path_parts) > 1:
            subdir = path_parts[0]
            filename = path_parts[-1]
            
            # Map subdirectories
            subdir_mapping = {
                "publishers": "publishers",
                "imprints": "imprints", 
                "tranches": "tranches",
                "examples": "examples"
            }
            
            target_subdir = subdir_mapping.get(subdir, subdir)
            return self.config_dir / target_subdir / filename
        else:
            # Root level file
            return self.config_dir / relative_path
    
    def _determine_conflict_resolution(self, configs_file: ConfigFile, 
                                     config_file: ConfigFile) -> Dict[str, str]:
        """Determine how to resolve a conflict between two config files."""
        # Compare content hashes
        if configs_file.content_hash == config_file.content_hash:
            return {"type": "skip", "reason": "identical_content"}
        
        # Compare modification times
        if configs_file.modified_time > config_file.modified_time:
            return {"type": "replace", "reason": "configs_newer"}
        elif config_file.modified_time > configs_file.modified_time:
            return {"type": "merge", "strategy": "preserve_config_with_configs_additions"}
        else:
            # Same modification time, different content - merge intelligently
            return {"type": "merge", "strategy": "intelligent_merge"}
    
    def _generate_merge_strategy(self) -> Dict[str, Any]:
        """Generate the complete merge strategy."""
        # Create merge operations
        self.merge_operations = []
        
        # 1. Create target directory structure
        target_dirs = {"publishers", "imprints", "tranches", "examples"}
        for dir_name in target_dirs:
            target_dir = self.config_dir / dir_name
            if not target_dir.exists():
                self.merge_operations.append(MergeOperation(
                    operation_type="create_directory",
                    source_path=self.configs_dir / dir_name,
                    target_path=target_dir
                ))
        
        # 2. Handle file moves and merges
        for configs_path, configs_file in self.configs_files.items():
            target_path = self._determine_target_path(configs_path, configs_file)
            
            # Find if there's a conflict
            conflict = self._find_conflict_for_file(configs_path)
            
            if conflict:
                if conflict.resolution_type == "merge":
                    self.merge_operations.append(MergeOperation(
                        operation_type="merge_files",
                        source_path=configs_file.path,
                        target_path=target_path,
                        backup_path=self.backup_dir / f"backup_{target_path.name}"
                    ))
                elif conflict.resolution_type == "replace":
                    self.merge_operations.append(MergeOperation(
                        operation_type="replace_file",
                        source_path=configs_file.path,
                        target_path=target_path,
                        backup_path=self.backup_dir / f"backup_{target_path.name}"
                    ))
                # Skip operation for "skip" resolution type
            else:
                self.merge_operations.append(MergeOperation(
                    operation_type="move_file",
                    source_path=configs_file.path,
                    target_path=target_path
                ))
        
        return {
            "total_operations": len(self.merge_operations),
            "operation_types": {
                op.operation_type: sum(1 for o in self.merge_operations if o.operation_type == op.operation_type)
                for op in self.merge_operations
            },
            "estimated_duration": "5-10 minutes",
            "risk_level": "low"
        }
    
    def _find_conflict_for_file(self, relative_path: str) -> Optional[ConflictResolution]:
        """Find conflict resolution for a specific file."""
        for conflict in self.conflicts:
            if str(conflict.source_file).endswith(relative_path):
                return conflict
        return None
    
    def _design_target_structure(self) -> Dict[str, List[str]]:
        """Design the target directory structure."""
        return {
            "directories": [
                "publishers",
                "imprints", 
                "tranches",
                "examples"
            ]
        }
    
    def _describe_conflict(self, conflict: ConflictResolution) -> str:
        """Generate a human-readable description of a conflict."""
        source_name = conflict.source_file.name
        target_name = conflict.target_file.name
        
        descriptions = {
            "merge": f"Files {source_name} and {target_name} will be merged intelligently",
            "replace": f"File {target_name} will be replaced with {source_name}",
            "skip": f"File {source_name} will be skipped (identical to {target_name})",
            "rename": f"File {source_name} will be renamed to avoid conflict"
        }
        
        return descriptions.get(conflict.resolution_type, 
                              f"Unknown resolution for {source_name} -> {target_name}")
    
    def _create_full_backup(self) -> bool:
        """Create a full backup of both directories before merge."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup config/ directory
            if self.config_dir.exists():
                config_backup = self.backup_dir / f"config_backup_{timestamp}"
                shutil.copytree(self.config_dir, config_backup)
                logger.info(f"Created config/ backup: {config_backup}")
            
            # Backup configs/ directory
            if self.configs_dir.exists():
                configs_backup = self.backup_dir / f"configs_backup_{timestamp}"
                shutil.copytree(self.configs_dir, configs_backup)
                logger.info(f"Created configs/ backup: {configs_backup}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def _execute_operation(self, operation: MergeOperation) -> None:
        """Execute a single merge operation."""
        if operation.operation_type == "create_directory":
            operation.target_path.mkdir(parents=True, exist_ok=True)
            
        elif operation.operation_type == "move_file":
            operation.target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(operation.source_path), str(operation.target_path))
            
        elif operation.operation_type == "replace_file":
            if operation.backup_path:
                shutil.copy2(str(operation.target_path), str(operation.backup_path))
            shutil.copy2(str(operation.source_path), str(operation.target_path))
            
        elif operation.operation_type == "merge_files":
            self._merge_config_files(operation.source_path, operation.target_path, 
                                   operation.backup_path)
        
        operation.completed = True
    
    def _merge_config_files(self, source_path: Path, target_path: Path, 
                           backup_path: Optional[Path]) -> None:
        """Merge two configuration files intelligently."""
        # Create backup if specified
        if backup_path and target_path.exists():
            shutil.copy2(str(target_path), str(backup_path))
        
        # Load both files
        with open(source_path, 'r', encoding='utf-8') as f:
            source_config = json.load(f)
        
        if target_path.exists():
            with open(target_path, 'r', encoding='utf-8') as f:
                target_config = json.load(f)
        else:
            target_config = {}
        
        # Merge configurations (source takes precedence for conflicts)
        merged_config = self._deep_merge_configs(target_config, source_config)
        
        # Write merged configuration
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(merged_config, f, indent=2, ensure_ascii=False)
    
    def _deep_merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_merge_results(self) -> Dict[str, Any]:
        """Validate the results of the merge operation."""
        validation = {
            "all_valid": True,
            "config_files_valid": True,
            "json_syntax_valid": True,
            "required_files_present": True,
            "errors": [],
            "warnings": []
        }
        
        # Check that all expected files are present
        required_files = ["default_lsi_config.json"]
        for required_file in required_files:
            file_path = self.config_dir / required_file
            if not file_path.exists():
                validation["required_files_present"] = False
                validation["errors"].append(f"Required file missing: {required_file}")
        
        # Validate JSON syntax for all config files
        for config_file in self.config_dir.rglob("*.json"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                validation["json_syntax_valid"] = False
                validation["errors"].append(f"Invalid JSON in {config_file}: {e}")
        
        # Check if configs/ directory can be safely removed
        if self.configs_dir.exists():
            remaining_files = list(self.configs_dir.rglob("*.json"))
            if remaining_files:
                validation["warnings"].append(
                    f"configs/ directory still contains {len(remaining_files)} files"
                )
        
        validation["all_valid"] = (validation["config_files_valid"] and 
                                 validation["json_syntax_valid"] and 
                                 validation["required_files_present"])
        
        return validation