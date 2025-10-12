"""Configuration Reference Updater

This module provides functionality to update configuration file references in the codebase
after configuration directory unification.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
import ast
import tokenize
import io

logger = logging.getLogger(__name__)


@dataclass
class ReferenceUpdate:
    """Represents a configuration reference update."""
    file_path: Path
    line_number: int
    old_reference: str
    new_reference: str
    reference_type: str  # 'import', 'file_path', 'config_path', 'string_literal'
    context: str  # surrounding code context
    updated: bool = False
    error: Optional[str] = None


@dataclass
class FileAnalysis:
    """Analysis results for a single file."""
    file_path: Path
    references_found: List[ReferenceUpdate]
    syntax_valid: bool
    file_type: str  # 'python', 'json', 'markdown', 'other'
    encoding: str = 'utf-8'


class ConfigurationReferenceUpdater:
    """
    Updates configuration file references in the codebase after directory unification.
    
    This class searches for references to configs/ directory and updates them to
    point to the unified config/ directory structure.
    """
    
    def __init__(self, root_dir: str = "."):
        """
        Initialize the configuration reference updater.
        
        Args:
            root_dir: Root directory of the project
        """
        self.root_dir = Path(root_dir)
        self.backup_dir = self.root_dir / ".cleanup_backups" / "reference_updates"
        
        # Reference patterns to search for
        self.reference_patterns = {
            'configs_path': [
                r'configs/',
                r'"configs/',
                r"'configs/",
                r'Path\("configs/',
                r"Path\('configs/",
                r'os\.path\.join\([^)]*"configs"',
                r'os\.path\.join\([^)]*\'configs\'',
            ],
            'config_imports': [
                r'from\s+configs\.',
                r'import\s+configs\.',
            ],
            'config_files': [
                r'configs/[a-zA-Z0-9_/.-]+\.json',
                r'"configs/[a-zA-Z0-9_/.-]+\.json"',
                r"'configs/[a-zA-Z0-9_/.-]+\.json'",
            ]
        }
        
        # Path mappings for the unified structure
        self.path_mappings = {
            'configs/default_lsi_config.json': 'config/default_lsi_config.json',
            'configs/llm_monitoring_config.json': 'config/llm_monitoring_config.json',
            'configs/llm_prompt_config.json': 'config/llm_prompt_config.json',
            'configs/logging_config.json': 'config/logging_config.json',
            'configs/isbn_schedule.json': 'config/isbn_schedule.json',
            'configs/publishers/': 'config/publishers/',
            'configs/imprints/': 'config/imprints/',
            'configs/tranches/': 'config/tranches/',
            'configs/examples/': 'config/examples/',
        }
        
        # Analysis results
        self.file_analyses: List[FileAnalysis] = []
        self.all_updates: List[ReferenceUpdate] = []
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def search_and_replace_config_paths(self) -> Dict[str, List[str]]:
        """
        Search for configuration file paths in Python code and update them.
        
        Returns:
            Dictionary containing search and replace results
        """
        logger.info("Searching for configuration references in codebase...")
        
        results = {
            "files_scanned": [],
            "files_updated": [],
            "references_found": [],
            "references_updated": [],
            "errors": []
        }
        
        # Find all Python files to scan
        python_files = list(self.root_dir.rglob("*.py"))
        
        # Also scan some configuration and documentation files
        other_files = []
        for pattern in ["*.json", "*.md", "*.txt", "*.sh"]:
            other_files.extend(self.root_dir.rglob(pattern))
        
        all_files = python_files + other_files
        
        for file_path in all_files:
            # Skip files in certain directories
            if self._should_skip_file(file_path):
                continue
            
            try:
                analysis = self._analyze_file(file_path)
                self.file_analyses.append(analysis)
                results["files_scanned"].append(str(file_path))
                
                if analysis.references_found:
                    results["references_found"].extend([
                        {
                            "file": str(ref.file_path),
                            "line": ref.line_number,
                            "old": ref.old_reference,
                            "new": ref.new_reference,
                            "type": ref.reference_type
                        }
                        for ref in analysis.references_found
                    ])
                
            except Exception as e:
                error_msg = f"Error analyzing {file_path}: {e}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        # Collect all updates
        self.all_updates = []
        for analysis in self.file_analyses:
            self.all_updates.extend(analysis.references_found)
        
        logger.info(f"Found {len(self.all_updates)} configuration references "
                   f"in {len(self.file_analyses)} files")
        
        return results
    
    def update_import_statements(self) -> Dict[str, List[str]]:
        """
        Update import statements that reference configs module.
        
        Returns:
            Dictionary containing import update results
        """
        logger.info("Updating import statements...")
        
        results = {
            "imports_found": [],
            "imports_updated": [],
            "errors": []
        }
        
        # Find import-related updates
        import_updates = [
            update for update in self.all_updates 
            if update.reference_type == 'import'
        ]
        
        for update in import_updates:
            try:
                # Update the import statement
                success = self._update_import_reference(update)
                if success:
                    results["imports_updated"].append({
                        "file": str(update.file_path),
                        "old_import": update.old_reference,
                        "new_import": update.new_reference
                    })
                    update.updated = True
                else:
                    results["errors"].append(f"Failed to update import in {update.file_path}")
                
            except Exception as e:
                error_msg = f"Error updating import in {update.file_path}: {e}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        return results
    
    def validate_configuration_loading(self) -> Dict[str, bool]:
        """
        Validate that all configuration loading still works after updates.
        
        Returns:
            Dictionary containing validation results
        """
        logger.info("Validating configuration loading...")
        
        validation_results = {
            "syntax_valid": True,
            "imports_valid": True,
            "paths_exist": True,
            "config_loadable": True,
            "errors": [],
            "warnings": []
        }
        
        # 1. Check Python syntax validity
        for analysis in self.file_analyses:
            if analysis.file_type == 'python' and not analysis.syntax_valid:
                validation_results["syntax_valid"] = False
                validation_results["errors"].append(
                    f"Syntax error in {analysis.file_path}"
                )
        
        # 2. Validate that updated paths exist
        for update in self.all_updates:
            if update.updated and update.reference_type == 'file_path':
                # Extract the actual path from the reference
                path_match = re.search(r'config/[a-zA-Z0-9_/.-]+\.json', update.new_reference)
                if path_match:
                    config_path = self.root_dir / path_match.group()
                    if not config_path.exists():
                        validation_results["paths_exist"] = False
                        validation_results["errors"].append(
                            f"Updated path does not exist: {config_path}"
                        )
        
        # 3. Test configuration loading for key files
        key_config_files = [
            "config/default_lsi_config.json",
            "config/llm_monitoring_config.json",
            "config/logging_config.json"
        ]
        
        for config_file in key_config_files:
            config_path = self.root_dir / config_file
            if config_path.exists():
                try:
                    import json
                    with open(config_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                except Exception as e:
                    validation_results["config_loadable"] = False
                    validation_results["errors"].append(
                        f"Cannot load config {config_file}: {e}"
                    )
            else:
                validation_results["warnings"].append(
                    f"Config file not found: {config_file}"
                )
        
        # 4. Check for any remaining configs/ references
        remaining_refs = self._find_remaining_configs_references()
        if remaining_refs:
            validation_results["warnings"].extend([
                f"Remaining configs/ reference in {ref['file']}:{ref['line']}: {ref['text']}"
                for ref in remaining_refs
            ])
        
        # Overall validation status
        validation_results["all_valid"] = (
            validation_results["syntax_valid"] and
            validation_results["imports_valid"] and
            validation_results["paths_exist"] and
            validation_results["config_loadable"]
        )
        
        logger.info(f"Validation complete: {'PASSED' if validation_results['all_valid'] else 'FAILED'}")
        
        return validation_results
    
    def execute_updates(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Execute all configuration reference updates.
        
        Args:
            dry_run: If True, only simulate the updates without making changes
            
        Returns:
            Dictionary containing execution results
        """
        logger.info(f"Executing configuration reference updates (dry_run={dry_run})...")
        
        results = {
            "success": False,
            "files_updated": 0,
            "references_updated": 0,
            "errors": [],
            "backup_location": str(self.backup_dir) if not dry_run else None,
            "dry_run": dry_run
        }
        
        try:
            # Create backups if not dry run
            if not dry_run:
                backup_success = self._create_backups()
                if not backup_success:
                    results["errors"].append("Failed to create backups")
                    return results
            
            # Group updates by file
            updates_by_file = {}
            for update in self.all_updates:
                file_path = update.file_path
                if file_path not in updates_by_file:
                    updates_by_file[file_path] = []
                updates_by_file[file_path].append(update)
            
            # Process each file
            for file_path, file_updates in updates_by_file.items():
                try:
                    if dry_run:
                        logger.info(f"[DRY RUN] Would update {len(file_updates)} references in {file_path}")
                        for update in file_updates:
                            update.updated = True
                    else:
                        success = self._update_file_references(file_path, file_updates)
                        if success:
                            results["files_updated"] += 1
                            for update in file_updates:
                                if update.updated:
                                    results["references_updated"] += 1
                        else:
                            results["errors"].append(f"Failed to update {file_path}")
                
                except Exception as e:
                    error_msg = f"Error updating {file_path}: {e}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # Validate results if not dry run
            if not dry_run:
                validation = self.validate_configuration_loading()
                results["validation"] = validation
                results["success"] = validation["all_valid"] and len(results["errors"]) == 0
            else:
                results["success"] = len(results["errors"]) == 0
            
            logger.info(f"Reference updates {'simulation' if dry_run else 'execution'} complete: "
                       f"{results['files_updated']} files, {results['references_updated']} references")
            
        except Exception as e:
            results["errors"].append(f"Update execution failed: {e}")
            logger.error(f"Update execution failed: {e}")
        
        return results
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped during analysis."""
        skip_patterns = [
            ".git/", "__pycache__/", ".pytest_cache/", ".venv/", "node_modules/",
            ".cleanup_backups/", "logs/", "output/", ".DS_Store"
        ]
        
        file_str = str(file_path)
        return any(pattern in file_str for pattern in skip_patterns)
    
    def _analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a single file for configuration references."""
        references = []
        syntax_valid = True
        file_type = self._determine_file_type(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Check syntax for Python files
            if file_type == 'python':
                try:
                    ast.parse(content)
                except SyntaxError:
                    syntax_valid = False
            
            # Search for configuration references
            for line_num, line in enumerate(lines, 1):
                line_references = self._find_references_in_line(
                    line, line_num, file_path
                )
                references.extend(line_references)
        
        except Exception as e:
            logger.warning(f"Could not analyze {file_path}: {e}")
            syntax_valid = False
        
        return FileAnalysis(
            file_path=file_path,
            references_found=references,
            syntax_valid=syntax_valid,
            file_type=file_type
        )
    
    def _determine_file_type(self, file_path: Path) -> str:
        """Determine the type of file based on extension."""
        suffix = file_path.suffix.lower()
        
        type_mapping = {
            '.py': 'python',
            '.json': 'json',
            '.md': 'markdown',
            '.txt': 'text',
            '.sh': 'shell',
            '.yml': 'yaml',
            '.yaml': 'yaml'
        }
        
        return type_mapping.get(suffix, 'other')
    
    def _find_references_in_line(self, line: str, line_num: int, 
                                file_path: Path) -> List[ReferenceUpdate]:
        """Find configuration references in a single line."""
        references = []
        
        # Search for each pattern type
        for pattern_type, patterns in self.reference_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    old_ref = match.group()
                    new_ref = self._generate_new_reference(old_ref, pattern_type)
                    
                    if new_ref and new_ref != old_ref:
                        reference = ReferenceUpdate(
                            file_path=file_path,
                            line_number=line_num,
                            old_reference=old_ref,
                            new_reference=new_ref,
                            reference_type=pattern_type,
                            context=line.strip()
                        )
                        references.append(reference)
        
        return references
    
    def _generate_new_reference(self, old_ref: str, pattern_type: str) -> Optional[str]:
        """Generate the new reference path for an old reference."""
        # Simple string replacement for most cases
        if 'configs/' in old_ref:
            # Apply specific mappings first
            for old_path, new_path in self.path_mappings.items():
                if old_path in old_ref:
                    return old_ref.replace(old_path, new_path)
            
            # General replacement
            return old_ref.replace('configs/', 'config/')
        
        # Handle import statements
        if pattern_type == 'config_imports':
            return old_ref.replace('configs.', 'config.')
        
        return None
    
    def _update_import_reference(self, update: ReferenceUpdate) -> bool:
        """Update a single import reference in a file."""
        try:
            with open(update.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Update the specific line
            if 1 <= update.line_number <= len(lines):
                old_line = lines[update.line_number - 1]
                new_line = old_line.replace(update.old_reference, update.new_reference)
                lines[update.line_number - 1] = new_line
                
                # Write back to file
                with open(update.file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                return True
        
        except Exception as e:
            logger.error(f"Failed to update import in {update.file_path}: {e}")
        
        return False
    
    def _update_file_references(self, file_path: Path, 
                               updates: List[ReferenceUpdate]) -> bool:
        """Update all references in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply all updates to the content
            updated_content = content
            for update in updates:
                updated_content = updated_content.replace(
                    update.old_reference, update.new_reference
                )
                update.updated = True
            
            # Write updated content back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to update references in {file_path}: {e}")
            return False
    
    def _create_backups(self) -> bool:
        """Create backups of files that will be modified."""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Get unique files that will be updated
            files_to_backup = set(update.file_path for update in self.all_updates)
            
            for file_path in files_to_backup:
                backup_path = self.backup_dir / f"{file_path.name}_{timestamp}.backup"
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                
                import shutil
                shutil.copy2(file_path, backup_path)
            
            logger.info(f"Created backups for {len(files_to_backup)} files")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create backups: {e}")
            return False
    
    def _find_remaining_configs_references(self) -> List[Dict[str, Any]]:
        """Find any remaining references to configs/ after updates."""
        remaining_refs = []
        
        # Re-scan files for any remaining configs/ references
        for file_path in self.root_dir.rglob("*.py"):
            if self._should_skip_file(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    if 'configs/' in line and 'config/' not in line:
                        remaining_refs.append({
                            'file': str(file_path),
                            'line': line_num,
                            'text': line.strip()
                        })
            
            except Exception:
                continue
        
        return remaining_refs