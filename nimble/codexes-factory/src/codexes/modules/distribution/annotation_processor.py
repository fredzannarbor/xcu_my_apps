"""
Annotation Processor Module

This module provides functionality for processing and enhancing annotations
with boilerplate text from tranche configurations.
"""

import logging
from typing import Dict, Optional

from ..metadata.metadata_models import CodexMetadata

logger = logging.getLogger(__name__)


class AnnotationProcessor:
    """
    Processes and enhances annotations with boilerplate text.
    """
    
    @staticmethod
    def apply_boilerplate(annotation: str, boilerplate: Dict[str, str]) -> str:
        """
        Apply boilerplate text to an annotation.
        
        Args:
            annotation: The original annotation text
            boilerplate: Dictionary with prefix and suffix text
            
        Returns:
            Enhanced annotation with boilerplate text
        """
        if not annotation:
            return ""
        
        prefix = boilerplate.get("prefix", "")
        suffix = boilerplate.get("suffix", "")
        
        # For HTML annotations, ensure proper tag handling
        if annotation.strip().startswith("<p>"):
            # HTML annotation - insert suffix before the last closing paragraph tag
            if suffix:
                last_p_index = annotation.rfind("</p>")
                if last_p_index >= 0:
                    # Insert suffix before the last </p> tag
                    enhanced = annotation[:last_p_index] + suffix + annotation[last_p_index:]
                else:
                    # No closing paragraph tag, append suffix with its own paragraph
                    enhanced = annotation + f"<p>{suffix}</p>"
            else:
                enhanced = annotation
                
            # Add prefix at the beginning if provided
            if prefix:
                if enhanced.strip().startswith("<p>"):
                    # Insert after the first <p> tag
                    first_p_end = enhanced.find(">", enhanced.find("<p>")) + 1
                    enhanced = enhanced[:first_p_end] + f" {prefix}" + enhanced[first_p_end:]
                else:
                    # Add prefix with its own paragraph
                    enhanced = f"<p>{prefix}</p>" + enhanced
        else:
            # Plain text annotation - simply concatenate
            enhanced = f"{prefix}{annotation}{suffix}"
        
        return enhanced
    
    @staticmethod
    def process_annotation(metadata: CodexMetadata, boilerplate: Optional[Dict[str, str]] = None) -> None:
        """
        Process annotation fields in metadata, applying boilerplate if provided.
        
        Args:
            metadata: The metadata object to process
            boilerplate: Optional dictionary with prefix and suffix text
        """
        if not boilerplate:
            return
        
        # Process annotation_summary field
        if hasattr(metadata, 'annotation_summary') and metadata.annotation_summary:
            metadata.annotation_summary = AnnotationProcessor.apply_boilerplate(
                metadata.annotation_summary, boilerplate
            )
            logger.info("Applied boilerplate to annotation_summary field")
        
        # Process summary_long field (used as fallback for annotation)
        if hasattr(metadata, 'summary_long') and metadata.summary_long:
            metadata.summary_long = AnnotationProcessor.apply_boilerplate(
                metadata.summary_long, boilerplate
            )
            logger.info("Applied boilerplate to summary_long field")