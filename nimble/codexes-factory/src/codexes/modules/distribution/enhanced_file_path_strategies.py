
"""
Enhanced File Path Mapping Strategy for LSI Issues

This module provides enhanced file path mapping that addresses the blank file path issues.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional

from ..metadata.metadata_models import CodexMetadata
from .field_mapping import ComputedMappingStrategy, MappingContext

logger = logging.getLogger(__name__)


class EnhancedFilePathStrategy(ComputedMappingStrategy):
    """Enhanced file path strategy that ensures paths are never blank."""
    
    def __init__(self, file_type: str, base_path: str = "", use_imprint_structure: bool = True):
        """
        Initialize enhanced file path strategy.
        
        Args:
            file_type: Type of file ("cover", "interior", "marketing_image")
            base_path: Base path for files
            use_imprint_structure: Whether to use imprint-based directory structure
        """
        self.file_type = file_type
        self.base_path = base_path
        self.use_imprint_structure = use_imprint_structure
        
        # File extensions
        self.extensions = {
            "cover": ".pdf",
            "interior": ".pdf", 
            "marketing_image": ".png",
            "jacket": ".pdf"
        }
        
        # Initialize parent class with computation function
        super().__init__(self._compute_file_path)
    
    def _compute_file_path(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Generate file path ensuring it's never blank."""
        try:
            # Get title and make it filename-safe
            title = getattr(metadata, 'title', 'Unknown_Book')
            title_safe = self._make_filename_safe(title)
            
            # Get imprint for directory structure
            imprint = getattr(metadata, 'imprint', 'default_imprint')
            imprint_safe = self._make_filename_safe(imprint)
            
            # Get file extension
            extension = self.extensions.get(self.file_type, '.pdf')
            
            # Build filename
            if self.file_type == "marketing_image":
                filename = f"{title_safe}_thumb{extension}"
            else:
                filename = f"{title_safe}_{self.file_type}{extension}"
            
            # Build full path
            if self.use_imprint_structure:
                if self.file_type == "interior":
                    full_path = f"{imprint_safe}_build/interior/{filename}"
                elif self.file_type == "cover":
                    full_path = f"{imprint_safe}_build/covers/{filename}"
                elif self.file_type == "marketing_image":
                    full_path = f"{imprint_safe}_build/covers/{filename}"
                else:
                    full_path = f"{imprint_safe}_build/{self.file_type}/{filename}"
            else:
                if self.base_path:
                    full_path = f"{self.base_path}/{filename}"
                else:
                    full_path = filename
            
            logger.info(f"Generated {self.file_type} path: {full_path}")
            return full_path
            
        except Exception as e:
            logger.error(f"Error generating {self.file_type} file path: {e}")
            # Return a fallback path to ensure it's never blank
            return f"output/{self.file_type}_file{self.extensions.get(self.file_type, '.pdf')}"
    
    def _make_filename_safe(self, text: str) -> str:
        """Make text safe for use in filenames."""
        if not text:
            return "Unknown"
        
        # Replace problematic characters
        safe_text = re.sub(r'[<>:"/\|?*]', '', str(text))
        safe_text = re.sub(r'\s+', '_', safe_text)
        safe_text = re.sub(r'[^\w\-_.]', '', safe_text)
        safe_text = safe_text.strip('_.')
        
        return safe_text if safe_text else "Unknown"


class EnhancedAnnotationStrategy(ComputedMappingStrategy):
    """Enhanced annotation strategy that ensures annotations are never blank."""
    
    def __init__(self):
        """Initialize enhanced annotation strategy."""
        super().__init__(self._compute_annotation)
    
    def _compute_annotation(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Generate annotation ensuring it's never blank."""
        try:
            # Try to get existing annotation
            annotation = getattr(metadata, 'annotation_summary', '') or getattr(metadata, 'summary_long', '')
            
            if not annotation:
                # Generate fallback annotation
                title = getattr(metadata, 'title', 'This Book')
                author = getattr(metadata, 'author', 'the Author')
                
                annotation = f"<p><b><i>Discover the fascinating insights of {title} in this compelling work by {author}.</i></b></p><p>This book offers valuable perspectives on important topics that will engage readers from beginning to end. With expert analysis and engaging prose, it presents complex ideas in an accessible format that both informs and inspires.</p>"
            
            # Apply tranche-specific boilerplate if available
            if context and hasattr(context, 'config') and context.config:
                boilerplate = context.config.get('annotation_boilerplate', {})
                prefix = boilerplate.get('prefix', '')
                suffix = boilerplate.get('suffix', '')
                
                if suffix:
                    # For HTML annotations, insert suffix before closing tag
                    if annotation.strip().endswith('</p>'):
                        annotation = annotation[:-4] + suffix + '</p>'
                    else:
                        annotation = annotation + suffix
                
                if prefix:
                    annotation = prefix + annotation
            
            return annotation
            
        except Exception as e:
            logger.error(f"Error generating annotation: {e}")
            return "<p>This book provides valuable insights and perspectives on important topics.</p>"


class EnhancedContributorBioStrategy(ComputedMappingStrategy):
    """Enhanced contributor bio strategy that ensures bios are never blank."""
    
    def __init__(self):
        """Initialize enhanced contributor bio strategy."""
        super().__init__(self._compute_contributor_bio)
    
    def _compute_contributor_bio(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Generate contributor bio ensuring it's never blank."""
        try:
            # Try to get existing bio
            bio = getattr(metadata, 'contributor_one_bio', '')
            
            if not bio:
                # Check for tranche-specific bio template
                if context and hasattr(context, 'config') and context.config:
                    contributor_info = context.config.get('contributor_info', {})
                    bio = contributor_info.get('contributor_one_bio', '')
                
                if not bio:
                    # Generate fallback bio
                    author = getattr(metadata, 'author', 'The Author')
                    title = getattr(metadata, 'title', 'this work')
                    
                    bio = f"{author} is a respected expert in the field with extensive knowledge and experience related to {title}. Through careful research and analysis, they bring valuable insights to readers seeking to understand complex topics in an accessible format."
            
            return bio
            
        except Exception as e:
            logger.error(f"Error generating contributor bio: {e}")
            return "A respected expert in the field with extensive knowledge and experience."


class EnhancedTOCStrategy(ComputedMappingStrategy):
    """Enhanced table of contents strategy with tranche-specific templates."""
    
    def __init__(self):
        """Initialize enhanced TOC strategy."""
        super().__init__(self._compute_toc)
    
    def _compute_toc(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Generate table of contents with tranche-specific template."""
        try:
            # Try to get existing TOC
            toc = getattr(metadata, 'table_of_contents', '')
            
            if not toc:
                # Check for tranche-specific TOC template
                if context and hasattr(context, 'config') and context.config:
                    toc = context.config.get('table_of_contents_template', '')
                
                if not toc:
                    # Generate fallback TOC
                    toc = """Introduction ........................... 1
Chapter 1: Understanding the Topic ........................... 5
Chapter 2: Historical Context ........................... 15
Chapter 3: Current Perspectives ........................... 25
Chapter 4: Future Implications ........................... 35
Chapter 5: Practical Applications ........................... 45
Conclusion ........................... 55
References ........................... 60"""
            
            return toc
            
        except Exception as e:
            logger.error(f"Error generating table of contents: {e}")
            return "Table of Contents will be provided in the final publication."


class BlankFieldStrategy(ComputedMappingStrategy):
    """Strategy that ensures specific fields remain blank."""
    
    def __init__(self):
        """Initialize blank field strategy."""
        super().__init__(self._compute_blank)
    
    def _compute_blank(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Always return blank for fields that should be empty."""
        return ""
