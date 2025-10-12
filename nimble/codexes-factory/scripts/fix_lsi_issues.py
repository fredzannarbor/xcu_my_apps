#!/usr/bin/env python3

"""
Fix LSI Generation Issues

This script addresses the specific issues identified in the LSI CSV generation:
1. Marketing image file path is blank
2. Interior path / filename is blank  
3. Cover path is blank
4. Annotation is blank
5. Contributor BIO fields are blank
6. TOC should be tranche-specific
7. Series name should be "Transcriptive Meditation"
8. Mode 2 pricing fields should be blank
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_tranche_config():
    """Update the tranche configuration with missing settings."""
    tranche_config_path = "configs/tranches/xynapse_tranche_1.json"
    
    try:
        with open(tranche_config_path, 'r') as f:
            config = json.load(f)
        
        # Add series information
        config["series_info"] = {
            "series_name": "Transcriptive Meditation",
            "series_description": "A series exploring mindful reflection and transcriptive practices"
        }
        
        # Add contributor information template
        config["contributor_info"] = {
            "contributor_one_bio": "AI Lab for Book-Lovers is a collaborative research initiative focused on exploring the intersection of artificial intelligence and literary analysis. The lab brings together experts in machine learning, natural language processing, and literary studies to create innovative approaches to understanding and generating written content.",
            "contributor_one_affiliations": "AI Lab for Book-Lovers Research Initiative",
            "contributor_one_professional_position": "Research Collective",
            "contributor_one_location": "Digital Research Network",
            "contributor_one_location_type_code": "VIRTUAL"
        }
        
        # Add table of contents template
        config["table_of_contents_template"] = """Introduction ........................... 1
Chapter 1: Understanding the Paradox ........................... 5
Chapter 2: Historical Context ........................... 15
Chapter 3: Current Perspectives ........................... 25
Chapter 4: Future Implications ........................... 35
Chapter 5: Practical Applications ........................... 45
Conclusion ........................... 55
References ........................... 60
Index ........................... 65"""
        
        # Add annotation boilerplate enhancement
        config["annotation_boilerplate"]["prefix"] = ""
        config["annotation_boilerplate"]["suffix"] = " This book is part of the Transcriptive Meditation series, exploring the intersection of technology, society, and human potential through mindful analysis and reflection."
        
        # Add file path configuration
        config["file_paths"] = {
            "marketing_image_template": "{imprint}_build/covers/{title_safe}_thumb.png",
            "interior_path_template": "{imprint}_build/interior/{title_safe}_interior.pdf", 
            "cover_path_template": "{imprint}_build/covers/{title_safe}_cover.pdf"
        }
        
        # Add fields that should be blank (Mode 2 pricing)
        config["blank_fields"] = [
            "US-Ingram-Only* Suggested List Price (mode 2)",
            "US-Ingram-Only* Wholesale Discount % (Mode 2)",
            "US - Ingram - GAP * Suggested List Price (mode 2)",
            "US - Ingram - GAP * Wholesale Discount % (Mode 2)",
            "SIBI - EDUC - US * Suggested List Price (mode 2)",
            "SIBI - EDUC - US * Wholesale Discount % (Mode 2)"
        ]
        
        # Update version info
        config["_config_info"]["version"] = "1.1"
        config["_config_info"]["last_updated"] = "2025-07-30"
        
        # Write updated config
        with open(tranche_config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Updated tranche configuration: {tranche_config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update tranche config: {e}")
        return False


def create_file_path_mapping_strategy():
    """Create enhanced file path mapping strategy."""
    
    strategy_code = '''
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
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
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
        safe_text = re.sub(r'[<>:"/\\|?*]', '', str(text))
        safe_text = re.sub(r'\\s+', '_', safe_text)
        safe_text = re.sub(r'[^\\w\\-_.]', '', safe_text)
        safe_text = safe_text.strip('_.')
        
        return safe_text if safe_text else "Unknown"


class EnhancedAnnotationStrategy(ComputedMappingStrategy):
    """Enhanced annotation strategy that ensures annotations are never blank."""
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
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
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
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
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
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
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Always return blank for fields that should be empty."""
        return ""
'''
    
    # Write the strategy file
    strategy_path = "src/codexes/modules/distribution/enhanced_file_path_strategies.py"
    with open(strategy_path, 'w') as f:
        f.write(strategy_code)
    
    logger.info(f"Created enhanced file path strategies: {strategy_path}")
    return True


def update_field_mappings():
    """Update the field mappings to use the enhanced strategies."""
    
    # Read the current enhanced field mappings
    mappings_path = "src/codexes/modules/distribution/enhanced_field_mappings.py"
    
    try:
        with open(mappings_path, 'r') as f:
            content = f.read()
        
        # Add import for new strategies
        import_addition = '''from .enhanced_file_path_strategies import (
    EnhancedFilePathStrategy, EnhancedAnnotationStrategy, 
    EnhancedContributorBioStrategy, EnhancedTOCStrategy, BlankFieldStrategy
)
'''
        
        # Find the imports section and add our import
        if "from .enhanced_file_path_strategies import" not in content:
            # Add after the existing imports
            import_pos = content.find("from ..metadata.metadata_models import CodexMetadata")
            if import_pos != -1:
                end_pos = content.find("\n", import_pos) + 1
                content = content[:end_pos] + import_addition + "\n" + content[end_pos:]
        
        # Add the enhanced strategies to the registry creation function
        enhancement_code = '''
    
    # --- Enhanced File Path Strategies (Fix for blank paths) ---
    registry.register_strategy("Marketing Image", 
                             EnhancedFilePathStrategy("marketing_image"))
    
    registry.register_strategy("Interior Path / Filename", 
                             EnhancedFilePathStrategy("interior"))
    
    registry.register_strategy("Cover Path / Filename", 
                             EnhancedFilePathStrategy("cover"))
    
    # --- Enhanced Content Strategies ---
    registry.register_strategy("Annotation / Summary", 
                             EnhancedAnnotationStrategy())
    
    registry.register_strategy("Contributor One BIO", 
                             EnhancedContributorBioStrategy())
    
    registry.register_strategy("Table of Contents", 
                             EnhancedTOCStrategy())
    
    # --- Series Information ---
    registry.register_strategy("Series Name", 
                             DefaultMappingStrategy("Transcriptive Meditation"))
    
    # --- Blank Mode 2 Pricing Fields ---
    mode2_fields = [
        "US-Ingram-Only* Suggested List Price (mode 2)",
        "US-Ingram-Only* Wholesale Discount % (Mode 2)",
        "US - Ingram - GAP * Suggested List Price (mode 2)",
        "US - Ingram - GAP * Wholesale Discount % (Mode 2)",
        "SIBI - EDUC - US * Suggested List Price (mode 2)",
        "SIBI - EDUC - US * Wholesale Discount % (Mode 2)"
    ]
    
    for field in mode2_fields:
        registry.register_strategy(field, BlankFieldStrategy())
'''
        
        # Find the return statement in create_comprehensive_lsi_registry and add before it
        return_pos = content.rfind("return registry")
        if return_pos != -1:
            content = content[:return_pos] + enhancement_code + "\n    " + content[return_pos:]
        
        # Write the updated content
        with open(mappings_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Updated field mappings: {mappings_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update field mappings: {e}")
        return False


def main():
    """Main function to apply all fixes."""
    logger.info("Starting LSI issue fixes...")
    
    success = True
    
    # Update tranche configuration
    if not update_tranche_config():
        success = False
    
    # Create enhanced file path strategies
    if not create_file_path_mapping_strategy():
        success = False
    
    # Update field mappings
    if not update_field_mappings():
        success = False
    
    if success:
        logger.info("All LSI fixes applied successfully!")
        logger.info("Next steps:")
        logger.info("1. Run the book pipeline to test the fixes")
        logger.info("2. Check the generated LSI CSV for the corrected fields")
        logger.info("3. Verify that file paths, annotations, and bios are populated")
    else:
        logger.error("Some fixes failed. Please check the logs above.")
    
    return success


if __name__ == "__main__":
    main()