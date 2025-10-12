#!/usr/bin/env python3

"""
File Path Generator

This module generates correct interior and cover file paths for LSI submissions,
ensuring they match actual deliverable artifact names and follow naming conventions.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FilePathResult:
    """Result of file path generation."""
    interior_path: str
    cover_path: str
    base_filename: str
    validation_issues: List[str]
    notes: Optional[str] = None


class FilePathGenerator:
    """Generates file paths for book deliverables."""
    
    def __init__(self):
        """Initialize file path generator."""
        # File naming conventions
        self.max_filename_length = 100  # Maximum filename length
        self.reserved_names = {
            'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4',
            'com5', 'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3',
            'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
        }
        
        # File extensions
        self.interior_extensions = ['.pdf']
        self.cover_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif']
        
        # Default file suffixes
        self.interior_suffixes = ['_interior', '_text', '_pages', '_content']
        self.cover_suffixes = ['_cover', '_jacket', '_front']
    
    def generate_file_paths(self, metadata: Dict[str, Any], 
                          output_dir: str = None) -> FilePathResult:
        """
        Generate interior and cover file paths from metadata.
        
        Args:
            metadata: Dictionary containing book metadata
            output_dir: Optional output directory path
            
        Returns:
            FilePathResult with generated paths and validation info
        """
        validation_issues = []
        
        # Generate base filename from metadata
        base_filename = self._generate_base_filename(metadata)
        
        # Validate base filename
        filename_issues = self._validate_filename(base_filename)
        validation_issues.extend(filename_issues)
        
        # Clean filename if needed
        if filename_issues:
            base_filename = self._clean_filename(base_filename)
            logger.info(f"Cleaned filename: {base_filename}")
        
        # Generate interior and cover paths
        interior_filename = f"{base_filename}_interior.pdf"
        cover_filename = f"{base_filename}_cover.pdf"
        
        # Add output directory if specified
        if output_dir:
            output_path = Path(output_dir)
            interior_path = str(output_path / interior_filename)
            cover_path = str(output_path / cover_filename)
        else:
            interior_path = interior_filename
            cover_path = cover_filename
        
        # Validate generated paths
        path_issues = self._validate_file_paths(interior_path, cover_path)
        validation_issues.extend(path_issues)
        
        return FilePathResult(
            interior_path=interior_path,
            cover_path=cover_path,
            base_filename=base_filename,
            validation_issues=validation_issues,
            notes=f"Generated from title: {metadata.get('title', 'Unknown')}"
        )
    
    def _generate_base_filename(self, metadata: Dict[str, Any]) -> str:
        """Generate base filename from metadata."""
        # Priority order for filename components
        title = metadata.get('title', metadata.get('Title', ''))
        author = metadata.get('author', metadata.get('Author', ''))
        isbn = metadata.get('isbn', metadata.get('ISBN', ''))
        
        # Start with title
        if title:
            base_name = self._sanitize_for_filename(title)
        elif author:
            base_name = f"Book_by_{self._sanitize_for_filename(author)}"
        elif isbn:
            base_name = f"Book_{self._sanitize_for_filename(isbn)}"
        else:
            base_name = "Unknown_Book"
        
        # Add author if available and different from title
        if author and title and author.lower() not in title.lower():
            author_part = self._sanitize_for_filename(author)
            # Limit author part to avoid overly long filenames
            if len(author_part) > 20:
                author_part = author_part[:20]
            base_name = f"{base_name}_by_{author_part}"
        
        # Ensure filename isn't too long
        if len(base_name) > self.max_filename_length - 20:  # Reserve space for suffixes
            base_name = base_name[:self.max_filename_length - 20]
            # Try to cut at word boundary
            if '_' in base_name:
                parts = base_name.split('_')
                base_name = '_'.join(parts[:-1])  # Remove last part
        
        return base_name
    
    def _sanitize_for_filename(self, text: str) -> str:
        """Sanitize text for use in filenames."""
        if not text:
            return ""
        
        # Convert to string and strip
        text = str(text).strip()
        
        # Replace problematic characters
        # Replace spaces and common punctuation with underscores
        text = re.sub(r'[\\/:*?"<>|]', '', text)  # Remove invalid filename chars
        text = re.sub(r'[\\s\\-]+', '_', text)     # Replace spaces and hyphens with underscores
        text = re.sub(r'[^\\w\\-_.]', '', text)    # Keep only alphanumeric, underscore, hyphen, dot
        text = re.sub(r'_+', '_', text)           # Collapse multiple underscores
        text = text.strip('_.')                   # Remove leading/trailing underscores and dots
        
        # Handle special cases
        if not text or text.lower() in self.reserved_names:
            text = f"Book_{text}" if text else "Book"
        
        return text
    
    def _validate_filename(self, filename: str) -> List[str]:
        """Validate filename for common issues."""
        issues = []
        
        if not filename:
            issues.append("Filename is empty")
            return issues
        
        # Check length
        if len(filename) > self.max_filename_length:
            issues.append(f"Filename too long ({len(filename)} > {self.max_filename_length})")
        
        # Check for reserved names
        if filename.lower() in self.reserved_names:
            issues.append(f"Filename uses reserved name: {filename}")
        
        # Check for invalid characters
        invalid_chars = re.findall(r'[\\/:*?"<>|]', filename)
        if invalid_chars:
            issues.append(f"Filename contains invalid characters: {set(invalid_chars)}")
        
        # Check for leading/trailing dots or spaces
        if filename.startswith('.') or filename.endswith('.'):
            issues.append("Filename starts or ends with dot")
        
        if filename.startswith(' ') or filename.endswith(' '):
            issues.append("Filename starts or ends with space")
        
        # Check for consecutive dots
        if '..' in filename:
            issues.append("Filename contains consecutive dots")
        
        return issues
    
    def _clean_filename(self, filename: str) -> str:
        """Clean filename to resolve validation issues."""
        if not filename:
            return "Book"
        
        # Remove invalid characters
        cleaned = re.sub(r'[\\/:*?"<>|]', '', filename)
        
        # Remove leading/trailing dots and spaces
        cleaned = cleaned.strip('. ')
        
        # Replace consecutive dots
        cleaned = re.sub(r'\\.+', '.', cleaned)
        
        # Ensure it's not a reserved name
        if cleaned.lower() in self.reserved_names:
            cleaned = f"Book_{cleaned}"
        
        # Ensure it's not empty
        if not cleaned:
            cleaned = "Book"
        
        # Truncate if too long
        if len(cleaned) > self.max_filename_length:
            cleaned = cleaned[:self.max_filename_length].rstrip('_.')
        
        return cleaned
    
    def _validate_file_paths(self, interior_path: str, cover_path: str) -> List[str]:
        """Validate generated file paths."""
        issues = []
        
        # Check if paths are different
        if interior_path == cover_path:
            issues.append("Interior and cover paths are identical")
        
        # Check path lengths
        if len(interior_path) > 260:  # Windows path limit
            issues.append(f"Interior path too long ({len(interior_path)} > 260)")
        
        if len(cover_path) > 260:
            issues.append(f"Cover path too long ({len(cover_path)} > 260)")
        
        # Check for valid extensions
        interior_ext = Path(interior_path).suffix.lower()
        if interior_ext not in self.interior_extensions:
            issues.append(f"Interior file has invalid extension: {interior_ext}")
        
        cover_ext = Path(cover_path).suffix.lower()
        if cover_ext not in self.cover_extensions:
            issues.append(f"Cover file has invalid extension: {cover_ext}")
        
        return issues
    
    def update_metadata_with_file_paths(self, metadata: Dict[str, Any], 
                                      output_dir: str = None) -> Dict[str, Any]:
        """
        Update metadata with generated file paths.
        
        Args:
            metadata: Dictionary containing book metadata
            output_dir: Optional output directory
            
        Returns:
            Updated metadata with file path fields
        """
        # Generate file paths
        result = self.generate_file_paths(metadata, output_dir)
        
        # Update metadata with file paths
        file_path_fields = {
            # Interior file path fields
            'interior_file_path': result.interior_path,
            'Interior File Path': result.interior_path,
            'interior_pdf_path': result.interior_path,
            'Interior PDF Path': result.interior_path,
            'text_file_path': result.interior_path,
            'Text File Path': result.interior_path,
            
            # Cover file path fields
            'cover_file_path': result.cover_path,
            'Cover File Path': result.cover_path,
            'cover_pdf_path': result.cover_path,
            'Cover PDF Path': result.cover_path,
            'jacket_file_path': result.cover_path,
            'Jacket File Path': result.cover_path,
        }
        
        # Update existing fields or add new ones
        for field_name, file_path in file_path_fields.items():
            if field_name in metadata:
                original_path = metadata[field_name]
                metadata[field_name] = file_path
                
                if original_path != file_path:
                    logger.info(f"Updated file path {field_name}: {original_path} -> {file_path}")
            else:
                # Add common field names
                if field_name in ['Interior File Path', 'Cover File Path']:
                    metadata[field_name] = file_path
                    logger.info(f"Added file path {field_name}: {file_path}")
        
        # Log validation issues
        if result.validation_issues:
            logger.warning(f"File path validation issues: {result.validation_issues}")
        
        return metadata
    
    def validate_existing_file_paths(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate existing file paths in metadata.
        
        Args:
            metadata: Dictionary containing book metadata
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'interior_paths': [],
            'cover_paths': [],
            'issues': [],
            'recommendations': []
        }
        
        # Find file path fields
        interior_fields = [
            'interior_file_path', 'Interior File Path', 'interior_pdf_path',
            'Interior PDF Path', 'text_file_path', 'Text File Path'
        ]
        
        cover_fields = [
            'cover_file_path', 'Cover File Path', 'cover_pdf_path',
            'Cover PDF Path', 'jacket_file_path', 'Jacket File Path'
        ]
        
        # Validate interior paths
        for field in interior_fields:
            if field in metadata and metadata[field]:
                path = metadata[field]
                validation_results['interior_paths'].append(path)
                
                # Validate path
                path_issues = self._validate_single_file_path(path, 'interior')
                validation_results['issues'].extend(path_issues)
        
        # Validate cover paths
        for field in cover_fields:
            if field in metadata and metadata[field]:
                path = metadata[field]
                validation_results['cover_paths'].append(path)
                
                # Validate path
                path_issues = self._validate_single_file_path(path, 'cover')
                validation_results['issues'].extend(path_issues)
        
        # Generate recommendations
        if not validation_results['interior_paths']:
            validation_results['recommendations'].append("No interior file path found - consider generating one")
        
        if not validation_results['cover_paths']:
            validation_results['recommendations'].append("No cover file path found - consider generating one")
        
        if len(validation_results['interior_paths']) > 1:
            validation_results['recommendations'].append("Multiple interior file paths found - consolidate to one")
        
        if len(validation_results['cover_paths']) > 1:
            validation_results['recommendations'].append("Multiple cover file paths found - consolidate to one")
        
        return validation_results
    
    def _validate_single_file_path(self, file_path: str, file_type: str) -> List[str]:
        """Validate a single file path."""
        issues = []
        
        if not file_path:
            issues.append(f"{file_type.title()} file path is empty")
            return issues
        
        # Check path length
        if len(file_path) > 260:
            issues.append(f"{file_type.title()} file path too long ({len(file_path)} > 260)")
        
        # Check file extension
        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()
        
        if file_type == 'interior':
            if extension not in self.interior_extensions:
                issues.append(f"Interior file has invalid extension: {extension}")
        elif file_type == 'cover':
            if extension not in self.cover_extensions:
                issues.append(f"Cover file has invalid extension: {extension}")
        
        # Check filename
        filename = path_obj.name
        filename_issues = self._validate_filename(filename)
        issues.extend([f"{file_type.title()} {issue}" for issue in filename_issues])
        
        return issues
    
    def suggest_file_paths(self, metadata: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Suggest alternative file paths based on metadata.
        
        Args:
            metadata: Dictionary containing book metadata
            
        Returns:
            Dictionary with suggested file paths
        """
        suggestions = {
            'interior_paths': [],
            'cover_paths': []
        }
        
        # Generate base suggestions
        result = self.generate_file_paths(metadata)
        base_filename = result.base_filename
        
        # Interior path suggestions
        for suffix in self.interior_suffixes:
            for ext in self.interior_extensions:
                suggestions['interior_paths'].append(f"{base_filename}{suffix}{ext}")
        
        # Cover path suggestions
        for suffix in self.cover_suffixes:
            for ext in self.cover_extensions:
                suggestions['cover_paths'].append(f"{base_filename}{suffix}{ext}")
        
        # Add ISBN-based suggestions if available
        isbn = metadata.get('isbn', metadata.get('ISBN', ''))
        if isbn:
            clean_isbn = re.sub(r'[^0-9X]', '', str(isbn))
            suggestions['interior_paths'].append(f"{clean_isbn}_interior.pdf")
            suggestions['cover_paths'].append(f"{clean_isbn}_cover.pdf")
        
        return suggestions


def generate_file_paths_for_metadata(metadata: Dict[str, Any], 
                                   output_dir: str = None) -> FilePathResult:
    """
    Convenience function to generate file paths for metadata.
    
    Args:
        metadata: Dictionary containing book metadata
        output_dir: Optional output directory
        
    Returns:
        FilePathResult with generated paths
    """
    generator = FilePathGenerator()
    return generator.generate_file_paths(metadata, output_dir)


def update_metadata_with_file_paths(metadata: Dict[str, Any], 
                                  output_dir: str = None) -> Dict[str, Any]:
    """
    Convenience function to update metadata with file paths.
    
    Args:
        metadata: Dictionary containing book metadata
        output_dir: Optional output directory
        
    Returns:
        Updated metadata with file path fields
    """
    generator = FilePathGenerator()
    return generator.update_metadata_with_file_paths(metadata, output_dir)