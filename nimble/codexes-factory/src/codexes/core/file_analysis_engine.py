"""
File Analysis Engine for repository cleanup operations.

This module provides comprehensive file scanning, categorization, and dependency
analysis capabilities for safe repository cleanup operations.
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class FileInfo:
    """Information about a file in the repository."""
    path: str
    size: int
    modified_time: float
    file_type: str
    category: str
    dependencies: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    is_safe_to_move: bool = True
    is_safe_to_delete: bool = False


class FileAnalysisEngine:
    """
    Engine for analyzing repository file structure and categorizing files.
    
    Provides methods to scan directory structure, identify file types,
    categorize files for cleanup operations, and analyze dependencies.
    """
    
    def __init__(self, root_path: str = "."):
        """
        Initialize the file analysis engine.
        
        Args:
            root_path: Root directory to analyze (default: current directory)
        """
        self.root_path = Path(root_path).resolve()
        self.file_inventory: Dict[str, FileInfo] = {}
        self.temp_file_patterns = [
            r"exported_config_\d{8}_\d{6}\.json$",
            r"__pycache__",
            r"\.DS_Store$",
            r"\.pyc$",
            r"\.pyo$",
            r"\.log$",
            r"texput\.log$",
            r"\.aux$",
            r"\.fdb_latexmk$",
            r"\.fls$",
            r"\.synctex\.gz$",
            r"\.toc$",
            r"\.out$",
            r"\.nav$",
            r"\.snm$",
            r"\.vrb$",
        ]
        self.critical_patterns = [
            r"\.py$",
            r"\.json$",
            r"\.md$",
            r"\.txt$",
            r"\.csv$",
            r"requirements.*\.txt$",
            r"\.env",
            r"\.gitignore$",
            r"\.git/",
        ]
    
    def scan_directory_structure(self, root_path: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Recursively scan directory structure and categorize all files.
        
        Args:
            root_path: Optional override for root path
            
        Returns:
            Dictionary mapping categories to lists of file paths
        """
        if root_path:
            scan_root = Path(root_path).resolve()
        else:
            scan_root = self.root_path
            
        categorized_files = defaultdict(list)
        
        for root, dirs, files in os.walk(scan_root):
            # Skip certain directories
            dirs[:] = [d for d in dirs if not self._should_skip_directory(d)]
            
            for file in files:
                file_path = Path(root) / file
                relative_path = str(file_path.relative_to(scan_root))
                
                # Create FileInfo object
                file_info = self._create_file_info(file_path, relative_path)
                self.file_inventory[relative_path] = file_info
                
                # Categorize the file
                category = self._categorize_file(file_path)
                categorized_files[category].append(relative_path)
        
        return dict(categorized_files)
    
    def identify_temporary_files(self) -> List[str]:
        """
        Identify temporary files that can be safely removed.
        
        Returns:
            List of temporary file paths
        """
        temp_files = []
        
        for file_path, file_info in self.file_inventory.items():
            if self._is_temporary_file(file_path):
                file_info.is_safe_to_delete = True
                file_info.category = "temporary"
                temp_files.append(file_path)
        
        return temp_files
    
    def find_test_scripts(self) -> List[str]:
        """
        Find test scripts that should be moved to tests/ directory.
        
        Returns:
            List of test script paths outside tests/ directory
        """
        test_scripts = []
        
        for file_path, file_info in self.file_inventory.items():
            if self._is_misplaced_test_file(file_path):
                file_info.category = "misplaced_test"
                test_scripts.append(file_path)
        
        return test_scripts
    
    def locate_documentation_files(self) -> List[str]:
        """
        Locate documentation files that should be in docs/ directory.
        
        Returns:
            List of documentation file paths outside docs/ directory
        """
        doc_files = []
        
        for file_path, file_info in self.file_inventory.items():
            if self._is_misplaced_documentation(file_path):
                file_info.category = "misplaced_documentation"
                doc_files.append(file_path)
        
        return doc_files
    
    def find_configuration_files(self) -> Dict[str, List[str]]:
        """
        Find configuration files and categorize by directory.
        
        Returns:
            Dictionary mapping config directories to file lists
        """
        config_files = defaultdict(list)
        
        for file_path, file_info in self.file_inventory.items():
            if self._is_configuration_file(file_path):
                file_info.category = "configuration"
                
                # Determine which config directory it belongs to
                if file_path.startswith("config/"):
                    config_files["config"].append(file_path)
                elif file_path.startswith("configs/"):
                    config_files["configs"].append(file_path)
                else:
                    config_files["other"].append(file_path)
        
        return dict(config_files)
    
    def identify_resource_files(self) -> Dict[str, List[str]]:
        """
        Identify resource files that need organization.
        
        Returns:
            Dictionary mapping resource types to file lists
        """
        resource_files = defaultdict(list)
        
        for file_path, file_info in self.file_inventory.items():
            resource_type = self._get_resource_type(file_path)
            if resource_type:
                file_info.category = f"resource_{resource_type}"
                resource_files[resource_type].append(file_path)
        
        return dict(resource_files)
    
    def analyze_file_references(self, file_path: str) -> List[str]:
        """
        Analyze a file to find references to other files.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            List of referenced file paths
        """
        references = []
        full_path = self.root_path / file_path
        
        if not full_path.exists():
            return references
        
        try:
            if file_path.endswith('.py'):
                references.extend(self._analyze_python_references(full_path))
            elif file_path.endswith('.md'):
                references.extend(self._analyze_markdown_references(full_path))
            elif file_path.endswith('.json'):
                references.extend(self._analyze_json_references(full_path))
        except Exception as e:
            print(f"Warning: Could not analyze references in {file_path}: {e}")
        
        return references
    
    def _should_skip_directory(self, dirname: str) -> bool:
        """Check if a directory should be skipped during scanning."""
        skip_dirs = {'.git', '.venv', '__pycache__', '.pytest_cache', 
                    'node_modules', '.idea', '.vscode'}
        return dirname in skip_dirs
    
    def _create_file_info(self, file_path: Path, relative_path: str) -> FileInfo:
        """Create a FileInfo object for a file."""
        stat = file_path.stat()
        file_type = self._get_file_type(file_path)
        
        return FileInfo(
            path=relative_path,
            size=stat.st_size,
            modified_time=stat.st_mtime,
            file_type=file_type,
            category="unknown"
        )
    
    def _get_file_type(self, file_path: Path) -> str:
        """Determine the type of a file based on its extension."""
        suffix = file_path.suffix.lower()
        type_mapping = {
            '.py': 'python',
            '.json': 'json',
            '.md': 'markdown',
            '.txt': 'text',
            '.csv': 'csv',
            '.log': 'log',
            '.tex': 'latex',
            '.pdf': 'pdf',
            '.png': 'image',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.gif': 'image',
            '.svg': 'image',
        }
        return type_mapping.get(suffix, 'unknown')
    
    def _categorize_file(self, file_path: Path) -> str:
        """Categorize a file based on its path and name."""
        relative_path = str(file_path.relative_to(self.root_path))
        
        if self._is_temporary_file(relative_path):
            return "temporary"
        elif self._is_misplaced_test_file(relative_path):
            return "misplaced_test"
        elif self._is_misplaced_documentation(relative_path):
            return "misplaced_documentation"
        elif self._is_configuration_file(relative_path):
            return "configuration"
        elif self._get_resource_type(relative_path):
            return f"resource_{self._get_resource_type(relative_path)}"
        else:
            return "regular"
    
    def _is_temporary_file(self, file_path: str) -> bool:
        """Check if a file matches temporary file patterns."""
        for pattern in self.temp_file_patterns:
            if re.search(pattern, file_path):
                return True
        return False
    
    def _is_misplaced_test_file(self, file_path: str) -> bool:
        """Check if a file is a test file outside the tests/ directory."""
        if file_path.startswith("tests/"):
            return False
        
        filename = Path(file_path).name
        return (filename.startswith("test_") and filename.endswith(".py")) or \
               filename == "conftest.py"
    
    def _is_misplaced_documentation(self, file_path: str) -> bool:
        """Check if a file is documentation outside the docs/ directory."""
        if file_path.startswith("docs/"):
            return False
        
        filename = Path(file_path).name.lower()
        path_parts = Path(file_path).parts
        
        # Check for README files or .md files in root or inappropriate locations
        if filename.startswith("readme") or \
           (filename.endswith(".md") and len(path_parts) <= 2 and 
            not any(part in ["tests", "src", ".kiro"] for part in path_parts)):
            return True
        
        return False
    
    def _is_configuration_file(self, file_path: str) -> bool:
        """Check if a file is a configuration file."""
        if file_path.startswith(("config/", "configs/")):
            return True
        
        filename = Path(file_path).name.lower()
        config_patterns = [
            r".*config.*\.json$",
            r".*settings.*\.json$",
            r"\.env.*",
            r"requirements.*\.txt$",
        ]
        
        for pattern in config_patterns:
            if re.match(pattern, filename):
                return True
        
        return False
    
    def _get_resource_type(self, file_path: str) -> Optional[str]:
        """Determine the resource type of a file."""
        if file_path.startswith("images/"):
            return "images"
        elif file_path.startswith("resources/"):
            return None  # Already in resources
        elif re.match(r"exported_config_\d{8}_\d{6}\.json$", Path(file_path).name):
            return "exports"
        
        return None
    
    def _analyze_python_references(self, file_path: Path) -> List[str]:
        """Analyze Python file for import statements and file references."""
        references = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST to find imports
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        references.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        references.append(node.module)
            
            # Look for file path references
            file_patterns = [
                r'["\']([^"\']+\.(json|csv|txt|md|py))["\']',
                r'Path\(["\']([^"\']+)["\']',
                r'open\(["\']([^"\']+)["\']',
            ]
            
            for pattern in file_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, tuple):
                        references.append(match[0])
                    else:
                        references.append(match)
        
        except Exception as e:
            print(f"Warning: Could not parse Python file {file_path}: {e}")
        
        return references
    
    def _analyze_markdown_references(self, file_path: Path) -> List[str]:
        """Analyze Markdown file for links and references."""
        references = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find markdown links and references
            link_patterns = [
                r'\[([^\]]+)\]\(([^)]+)\)',  # [text](link)
                r'!\[([^\]]*)\]\(([^)]+)\)',  # ![alt](image)
                r'<([^>]+\.(md|json|csv|txt|py))>',  # <file.ext>
            ]
            
            for pattern in link_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, tuple):
                        # Take the link part (second element for most patterns)
                        link = match[1] if len(match) > 1 else match[0]
                        if not link.startswith(('http://', 'https://', 'mailto:')):
                            references.append(link)
                    else:
                        references.append(match)
        
        except Exception as e:
            print(f"Warning: Could not parse Markdown file {file_path}: {e}")
        
        return references
    
    def _analyze_json_references(self, file_path: Path) -> List[str]:
        """Analyze JSON file for file path references."""
        references = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for file paths in JSON values
            file_patterns = [
                r'"([^"]+\.(json|csv|txt|md|py|tex))"',
                r'"([^"]+/[^"]+\.[a-zA-Z0-9]+)"',
            ]
            
            for pattern in file_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, tuple):
                        references.append(match[0])
                    else:
                        references.append(match)
        
        except Exception as e:
            print(f"Warning: Could not parse JSON file {file_path}: {e}")
        
        return references