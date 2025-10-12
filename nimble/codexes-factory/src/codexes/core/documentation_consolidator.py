"""
Documentation Consolidator for organizing scattered documentation files.

This module provides functionality to identify, categorize, and organize
documentation files scattered throughout the repository into a logical
hierarchy within the docs/ directory.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DocumentationType(Enum):
    """Types of documentation files."""
    API_REFERENCE = "api_reference"
    USER_GUIDE = "user_guide"
    IMPLEMENTATION_SUMMARY = "implementation_summary"
    TROUBLESHOOTING = "troubleshooting"
    CONFIGURATION = "configuration"
    README = "readme"
    ASSESSMENT = "assessment"
    NOTES = "notes"
    SPECIFICATION = "specification"
    CHANGELOG = "changelog"
    TUTORIAL = "tutorial"
    UNKNOWN = "unknown"


@dataclass
class DocumentationFile:
    """Represents a documentation file with metadata."""
    path: Path
    doc_type: DocumentationType
    category: str
    title: str
    size: int
    references: List[str]
    target_path: Optional[Path] = None


class DocumentationConsolidator:
    """
    Consolidates scattered documentation into organized docs/ structure.
    
    This class identifies documentation files throughout the repository,
    categorizes them by type and content, and provides functionality to
    move them to appropriate locations within the docs/ directory.
    """
    
    def __init__(self, root_path: str = "."):
        """
        Initialize the DocumentationConsolidator.
        
        Args:
            root_path: Root directory to scan for documentation
        """
        self.root_path = Path(root_path).resolve()
        self.docs_dir = self.root_path / "docs"
        self.excluded_paths = {
            ".venv", ".git", "__pycache__", ".pytest_cache", 
            "node_modules", ".kiro", "output"
        }
        self.documentation_files: List[DocumentationFile] = []
        
        # Patterns for categorizing documentation
        self.type_patterns = {
            DocumentationType.API_REFERENCE: [
                r"api.*reference", r".*_api\.md$", r"reference.*guide"
            ],
            DocumentationType.USER_GUIDE: [
                r".*guide\.md$", r"usage.*guide", r"user.*guide", 
                r".*_guide\.md$", r"how.*to"
            ],
            DocumentationType.IMPLEMENTATION_SUMMARY: [
                r".*summary\.md$", r"implementation.*summary", 
                r".*_summary\.md$", r"complete.*summary"
            ],
            DocumentationType.TROUBLESHOOTING: [
                r"troubleshooting", r".*troubleshoot.*", r"debug.*guide",
                r".*_troubleshooting\.md$"
            ],
            DocumentationType.CONFIGURATION: [
                r"config.*", r".*config.*\.md$", r"setup.*guide",
                r"installation.*guide"
            ],
            DocumentationType.README: [
                r"readme\.md$", r"^readme$"
            ],
            DocumentationType.ASSESSMENT: [
                r"assessment.*", r".*assessment.*\.md$", r"evaluation.*"
            ],
            DocumentationType.NOTES: [
                r"notes.*\.md$", r".*notes\.md$", r"todo.*\.md$"
            ],
            DocumentationType.SPECIFICATION: [
                r"spec.*\.md$", r".*spec\.md$", r"specification.*"
            ],
            DocumentationType.CHANGELOG: [
                r"changelog.*", r".*changelog.*", r"changes.*\.md$"
            ],
            DocumentationType.TUTORIAL: [
                r"tutorial.*", r".*tutorial.*", r"walkthrough.*"
            ]
        }
        
    def find_scattered_docs(self) -> List[DocumentationFile]:
        """
        Find all documentation files outside the docs/ directory.
        
        Returns:
            List of DocumentationFile objects representing scattered docs
        """
        logger.info(f"Scanning for documentation files in {self.root_path}")
        
        markdown_files = []
        
        # Find all .md files excluding certain directories
        for root, dirs, files in os.walk(self.root_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_paths]
            
            # Skip if we're already in docs directory
            try:
                rel_parts = Path(root).relative_to(self.root_path).parts
                if rel_parts and rel_parts[0] == "docs":
                    continue
            except ValueError:
                # Handle case where paths don't have common root
                pass
                
            for file in files:
                if file.lower().endswith('.md'):
                    file_path = Path(root) / file
                    markdown_files.append(file_path)
        
        # Process each markdown file
        for file_path in markdown_files:
            try:
                doc_file = self._analyze_documentation_file(file_path)
                if doc_file:
                    self.documentation_files.append(doc_file)
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")
                
        logger.info(f"Found {len(self.documentation_files)} documentation files")
        return self.documentation_files
    
    def _analyze_documentation_file(self, file_path: Path) -> Optional[DocumentationFile]:
        """
        Analyze a documentation file to determine its type and metadata.
        
        Args:
            file_path: Path to the documentation file
            
        Returns:
            DocumentationFile object or None if not a valid doc file
        """
        try:
            # Get file stats
            stat = file_path.stat()
            
            # Read file content to analyze
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract title (first heading or filename)
            title = self._extract_title(content, file_path.name)
            
            # Determine document type
            doc_type = self._categorize_document(file_path, content)
            
            # Determine category based on location and type
            category = self._determine_category(file_path, doc_type)
            
            # Find references to other files
            references = self._find_references(content)
            
            return DocumentationFile(
                path=file_path,
                doc_type=doc_type,
                category=category,
                title=title,
                size=stat.st_size,
                references=references
            )
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return None
    
    def _extract_title(self, content: str, filename: str) -> str:
        """Extract title from document content or filename."""
        # Look for first heading
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            elif line.startswith('## '):
                return line[3:].strip()
        
        # Fallback to filename without extension
        return filename.replace('.md', '').replace('_', ' ').title()
    
    def _categorize_document(self, file_path: Path, content: str) -> DocumentationType:
        """
        Categorize document based on filename and content patterns.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            DocumentationType enum value
        """
        filename = file_path.name.lower()
        content_lower = content.lower()
        
        # Check patterns for each document type
        for doc_type, patterns in self.type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename, re.IGNORECASE):
                    return doc_type
                # Also check content for some patterns
                if doc_type in [DocumentationType.API_REFERENCE, 
                               DocumentationType.TROUBLESHOOTING]:
                    if re.search(pattern, content_lower):
                        return doc_type
        
        # Additional content-based categorization
        if any(word in content_lower for word in ['api', 'endpoint', 'method', 'class']):
            return DocumentationType.API_REFERENCE
        elif any(word in content_lower for word in ['error', 'troubleshoot', 'debug', 'fix']):
            return DocumentationType.TROUBLESHOOTING
        elif any(word in content_lower for word in ['config', 'setup', 'install', 'configure']):
            return DocumentationType.CONFIGURATION
        elif any(word in content_lower for word in ['guide', 'how to', 'tutorial', 'walkthrough']):
            return DocumentationType.USER_GUIDE
        
        return DocumentationType.UNKNOWN
    
    def _determine_category(self, file_path: Path, doc_type: DocumentationType) -> str:
        """
        Determine the category/subdirectory for the document.
        
        Args:
            file_path: Path to the file
            doc_type: Type of document
            
        Returns:
            Category string for organizing into subdirectories
        """
        try:
            path_parts = file_path.relative_to(self.root_path).parts
        except ValueError:
            # Handle case where paths don't have common root (e.g., in tests)
            path_parts = file_path.parts
        
        # Use directory structure to inform category
        if len(path_parts) > 1:
            parent_dir = path_parts[0]
            
            # Map common directory names to categories
            if parent_dir in ['notes_and_reports', 'notes']:
                return 'notes'
            elif parent_dir in ['resources']:
                return 'resources'
            elif parent_dir in ['src', 'modules']:
                return 'development'
            elif parent_dir in ['tests']:
                return 'testing'
            elif parent_dir in ['configs', 'config']:
                return 'configuration'
        
        # Use document type to determine category
        type_to_category = {
            DocumentationType.API_REFERENCE: 'api',
            DocumentationType.USER_GUIDE: 'guides',
            DocumentationType.IMPLEMENTATION_SUMMARY: 'summaries',
            DocumentationType.TROUBLESHOOTING: 'troubleshooting',
            DocumentationType.CONFIGURATION: 'configuration',
            DocumentationType.README: 'readme',
            DocumentationType.ASSESSMENT: 'assessments',
            DocumentationType.NOTES: 'notes',
            DocumentationType.SPECIFICATION: 'specifications',
            DocumentationType.CHANGELOG: 'changelog',
            DocumentationType.TUTORIAL: 'tutorials'
        }
        
        return type_to_category.get(doc_type, 'misc')
    
    def _find_references(self, content: str) -> List[str]:
        """
        Find references to other files in the document content.
        
        Args:
            content: Document content
            
        Returns:
            List of file references found in the document
        """
        references = []
        
        # Markdown link patterns
        md_links = re.findall(r'\[.*?\]\((.*?)\)', content)
        references.extend(md_links)
        
        # File path patterns
        file_patterns = [
            r'`([^`]*\.[a-zA-Z]{2,4})`',  # Files in backticks
            r'"([^"]*\.[a-zA-Z]{2,4})"',  # Files in quotes
            r"'([^']*\.[a-zA-Z]{2,4})'",  # Files in single quotes
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, content)
            references.extend(matches)
        
        # Clean and filter references
        cleaned_refs = []
        for ref in references:
            ref = ref.strip()
            if ref and not ref.startswith('http') and not ref.startswith('#'):
                cleaned_refs.append(ref)
        
        return list(set(cleaned_refs))  # Remove duplicates
    
    def categorize_documentation(self, doc_files: List[DocumentationFile]) -> Dict[str, List[DocumentationFile]]:
        """
        Categorize documentation files by type and category.
        
        Args:
            doc_files: List of DocumentationFile objects
            
        Returns:
            Dictionary mapping categories to lists of documentation files
        """
        categorized = {}
        
        for doc_file in doc_files:
            category = doc_file.category
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(doc_file)
        
        # Sort files within each category by title
        for category in categorized:
            categorized[category].sort(key=lambda x: x.title)
        
        logger.info(f"Categorized documentation into {len(categorized)} categories")
        return categorized
    
    def create_doc_hierarchy(self) -> Dict[str, str]:
        """
        Create logical hierarchy structure for docs/ organization.
        
        Returns:
            Dictionary mapping categories to target directory paths
        """
        hierarchy = {
            'api': 'docs/api',
            'guides': 'docs/guides',
            'summaries': 'docs/summaries',
            'troubleshooting': 'docs/troubleshooting',
            'configuration': 'docs/configuration',
            'readme': 'docs/readme',
            'assessments': 'docs/assessments',
            'notes': 'docs/notes',
            'specifications': 'docs/specifications',
            'changelog': 'docs/changelog',
            'tutorials': 'docs/tutorials',
            'development': 'docs/development',
            'testing': 'docs/testing',
            'resources': 'docs/resources',
            'misc': 'docs/misc'
        }
        
        # Create directories if they don't exist
        for target_dir in hierarchy.values():
            Path(target_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created documentation hierarchy with {len(hierarchy)} categories")
        return hierarchy
    
    def generate_consolidation_plan(self) -> Dict[str, Dict]:
        """
        Generate a plan for consolidating documentation.
        
        Returns:
            Dictionary containing consolidation plan with file mappings
        """
        if not self.documentation_files:
            self.find_scattered_docs()
        
        categorized = self.categorize_documentation(self.documentation_files)
        hierarchy = self.create_doc_hierarchy()
        
        plan = {
            'total_files': len(self.documentation_files),
            'categories': {},
            'file_mappings': {},
            'potential_conflicts': []
        }
        
        for category, files in categorized.items():
            target_dir = hierarchy.get(category, 'docs/misc')
            
            plan['categories'][category] = {
                'count': len(files),
                'target_directory': target_dir,
                'files': []
            }
            
            for doc_file in files:
                # Generate target filename
                target_filename = self._generate_target_filename(doc_file)
                target_path = Path(target_dir) / target_filename
                
                # Check for conflicts
                if target_path.exists():
                    plan['potential_conflicts'].append({
                        'source': str(doc_file.path),
                        'target': str(target_path),
                        'reason': 'File already exists'
                    })
                
                file_info = {
                    'source': str(doc_file.path),
                    'target': str(target_path),
                    'title': doc_file.title,
                    'type': doc_file.doc_type.value,
                    'size': doc_file.size,
                    'references': doc_file.references
                }
                
                plan['categories'][category]['files'].append(file_info)
                plan['file_mappings'][str(doc_file.path)] = str(target_path)
                
                # Update the doc_file with target path
                doc_file.target_path = target_path
        
        logger.info(f"Generated consolidation plan for {plan['total_files']} files")
        return plan
    
    def _generate_target_filename(self, doc_file: DocumentationFile) -> str:
        """
        Generate appropriate target filename for a documentation file.
        
        Args:
            doc_file: DocumentationFile object
            
        Returns:
            Target filename string
        """
        original_name = doc_file.path.name
        
        # Keep original name if it's already descriptive
        if len(original_name) > 10 and not original_name.startswith('README'):
            return original_name
        
        # Generate name based on title and type
        title_slug = re.sub(r'[^\w\s-]', '', doc_file.title.lower())
        title_slug = re.sub(r'[-\s]+', '_', title_slug)
        
        # Don't add type prefix for cleaner filenames
        # if doc_file.doc_type != DocumentationType.UNKNOWN:
        #     type_prefix = doc_file.doc_type.value.upper()
        #     if not title_slug.startswith(type_prefix.lower()):
        #         return f"{type_prefix}_{title_slug}.md"
        
        return f"{title_slug}.md"
    
    def move_documentation(self, source: str, destination: str) -> bool:
        """
        Move a documentation file to its target location.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if move was successful, False otherwise
        """
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            # Create destination directory if it doesn't exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle conflicts by creating backup
            if dest_path.exists():
                backup_path = dest_path.with_suffix(f'.backup{dest_path.suffix}')
                logger.warning(f"Destination exists, creating backup: {backup_path}")
                shutil.move(str(dest_path), str(backup_path))
            
            # Move the file
            shutil.move(str(source_path), str(dest_path))
            logger.info(f"Moved documentation: {source} -> {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Error moving {source} to {destination}: {e}")
            return False
    
    def update_doc_references(self, updates: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Update references to moved documentation files.
        
        Args:
            updates: Dictionary mapping old paths to new paths
            
        Returns:
            Dictionary of files that were updated with their changes
        """
        updated_files = {}
        
        # Find all files that might contain references
        reference_files = []
        for root, dirs, files in os.walk(self.root_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_paths]
            
            for file in files:
                if file.endswith(('.md', '.py', '.txt', '.rst', '.html')):
                    reference_files.append(Path(root) / file)
        
        # Process each file for reference updates
        for file_path in reference_files:
            try:
                changes = self._update_file_references(file_path, updates)
                if changes:
                    updated_files[str(file_path)] = changes
            except Exception as e:
                logger.warning(f"Error updating references in {file_path}: {e}")
        
        logger.info(f"Updated references in {len(updated_files)} files")
        return updated_files
    
    def _update_file_references(self, file_path: Path, updates: Dict[str, str]) -> List[str]:
        """
        Update references in a single file.
        
        Args:
            file_path: Path to file to update
            updates: Dictionary mapping old paths to new paths
            
        Returns:
            List of changes made to the file
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original_content = content
            changes = []
            
            # Update each reference mapping
            for old_path, new_path in updates.items():
                old_path_obj = Path(old_path)
                new_path_obj = Path(new_path)
                
                # Try different reference formats
                patterns_to_update = [
                    # Exact path matches
                    old_path,
                    str(old_path_obj.relative_to(self.root_path)) if old_path_obj.is_absolute() else old_path,
                    old_path_obj.name,
                    
                    # Markdown link formats
                    f"({old_path})",
                    f"({old_path_obj.name})",
                    
                    # Quoted formats
                    f'"{old_path}"',
                    f"'{old_path}'",
                    f'`{old_path}`',
                ]
                
                replacements = [
                    # Corresponding replacements
                    new_path,
                    str(new_path_obj.relative_to(self.root_path)) if new_path_obj.is_absolute() else new_path,
                    new_path_obj.name,
                    
                    # Markdown link formats
                    f"({new_path})",
                    f"({new_path_obj.name})",
                    
                    # Quoted formats
                    f'"{new_path}"',
                    f"'{new_path}'",
                    f'`{new_path}`',
                ]
                
                for pattern, replacement in zip(patterns_to_update, replacements):
                    if pattern in content:
                        content = content.replace(pattern, replacement)
                        changes.append(f"Updated reference: {pattern} -> {replacement}")
            
            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.debug(f"Updated references in {file_path}")
            
            return changes
            
        except Exception as e:
            logger.error(f"Error updating file {file_path}: {e}")
            return []
    
    def validate_documentation_links(self, moved_files: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Validate that all documentation links are still functional after moves.
        
        Args:
            moved_files: Dictionary mapping old paths to new paths
            
        Returns:
            Dictionary of validation results with any broken links found
        """
        validation_results = {}
        
        # Check all markdown files for broken links
        for root, dirs, files in os.walk(self.docs_dir):
            for file in files:
                if file.endswith('.md'):
                    file_path = Path(root) / file
                    broken_links = self._check_file_links(file_path)
                    if broken_links:
                        validation_results[str(file_path)] = broken_links
        
        logger.info(f"Validated links in docs directory, found {len(validation_results)} files with issues")
        return validation_results
    
    def _check_file_links(self, file_path: Path) -> List[str]:
        """
        Check for broken links in a single file.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            List of broken links found
        """
        broken_links = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find markdown links
            import re
            links = re.findall(r'\[.*?\]\((.*?)\)', content)
            
            for link in links:
                # Skip external links
                if link.startswith(('http://', 'https://', '#')):
                    continue
                
                # Check if file exists
                if link.startswith('/'):
                    # Absolute path from root
                    target_path = self.root_path / link[1:]
                else:
                    # Relative path from current file
                    target_path = file_path.parent / link
                
                if not target_path.exists():
                    broken_links.append(link)
        
        except Exception as e:
            logger.warning(f"Error checking links in {file_path}: {e}")
        
        return broken_links
    
    def execute_consolidation(self, plan: Dict, dry_run: bool = True) -> Dict[str, any]:
        """
        Execute the documentation consolidation plan.
        
        Args:
            plan: Consolidation plan from generate_consolidation_plan()
            dry_run: If True, only simulate the moves without actually doing them
            
        Returns:
            Dictionary with execution results
        """
        results = {
            'moved_files': {},
            'failed_moves': [],
            'updated_references': {},
            'validation_results': {},
            'dry_run': dry_run
        }
        
        if dry_run:
            logger.info("Executing consolidation in DRY RUN mode")
        else:
            logger.info("Executing consolidation with actual file moves")
        
        # Move files
        for source, target in plan['file_mappings'].items():
            if dry_run:
                logger.info(f"DRY RUN: Would move {source} -> {target}")
                results['moved_files'][source] = target
            else:
                if self.move_documentation(source, target):
                    results['moved_files'][source] = target
                else:
                    results['failed_moves'].append({'source': source, 'target': target})
        
        # Update references
        if not dry_run and results['moved_files']:
            results['updated_references'] = self.update_doc_references(results['moved_files'])
        
        # Validate links
        if not dry_run:
            results['validation_results'] = self.validate_documentation_links(results['moved_files'])
        
        logger.info(f"Consolidation complete. Moved: {len(results['moved_files'])}, Failed: {len(results['failed_moves'])}")
        return results
    
    def print_consolidation_summary(self, plan: Dict) -> None:
        """
        Print a summary of the consolidation plan.
        
        Args:
            plan: Consolidation plan dictionary
        """
        print(f"\n=== Documentation Consolidation Plan ===")
        print(f"Total files to organize: {plan['total_files']}")
        print(f"Categories: {len(plan['categories'])}")
        
        if plan['potential_conflicts']:
            print(f"\n⚠️  Potential conflicts: {len(plan['potential_conflicts'])}")
            for conflict in plan['potential_conflicts']:
                print(f"  - {conflict['source']} -> {conflict['target']}")
        
        print(f"\n📁 Categories:")
        for category, info in plan['categories'].items():
            print(f"  {category}: {info['count']} files -> {info['target_directory']}")
        
        print(f"\n📄 Sample file mappings:")
        for i, (source, target) in enumerate(plan['file_mappings'].items()):
            if i >= 5:  # Show first 5 mappings
                print(f"  ... and {len(plan['file_mappings']) - 5} more")
                break
            print(f"  {source} -> {target}")
    
    def print_execution_results(self, results: Dict) -> None:
        """
        Print the results of consolidation execution.
        
        Args:
            results: Results dictionary from execute_consolidation()
        """
        print(f"\n=== Consolidation Execution Results ===")
        print(f"Mode: {'DRY RUN' if results['dry_run'] else 'ACTUAL EXECUTION'}")
        print(f"Files moved: {len(results['moved_files'])}")
        print(f"Failed moves: {len(results['failed_moves'])}")
        
        if results['failed_moves']:
            print(f"\n❌ Failed moves:")
            for failure in results['failed_moves']:
                print(f"  - {failure['source']} -> {failure['target']}")
        
        if results['updated_references']:
            print(f"\n🔗 Reference updates: {len(results['updated_references'])} files")
            for file_path, changes in list(results['updated_references'].items())[:3]:
                print(f"  - {file_path}: {len(changes)} changes")
        
        if results['validation_results']:
            print(f"\n⚠️  Link validation issues: {len(results['validation_results'])} files")
            for file_path, broken_links in list(results['validation_results'].items())[:3]:
                print(f"  - {file_path}: {len(broken_links)} broken links")


if __name__ == "__main__":
    # Example usage
    consolidator = DocumentationConsolidator()
    plan = consolidator.generate_consolidation_plan()
    consolidator.print_consolidation_summary(plan)