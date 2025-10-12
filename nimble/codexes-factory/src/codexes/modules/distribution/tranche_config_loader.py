"""
Tranche Configuration Loader

This module provides functionality for loading and managing tranche-specific configurations.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .multi_level_config import MultiLevelConfiguration, ConfigurationContext, ConfigurationLevel

logger = logging.getLogger(__name__)


class TrancheConfigLoader:
    """
    Loader for tranche-specific configurations.
    
    This class provides methods for loading and accessing tranche-specific
    configurations for batch processing of books.
    """
    
    def __init__(self, config_dir: str = "configs"):
        """
        Initialize tranche configuration loader.
        
        Args:
            config_dir: Base directory for configuration files
        """
        self.config_dir = Path(config_dir)
        self.tranches_dir = self.config_dir / "tranches"
        self.config = MultiLevelConfiguration(config_dir)
    
    def list_available_tranches(self) -> List[str]:
        """
        List all available tranche configurations.
        
        Returns:
            List of tranche names
        """
        if not self.tranches_dir.exists():
            return []
        
        return [
            config_file.stem
            for config_file in self.tranches_dir.glob("*.json")
        ]
    
    def load_tranche_config(self, tranche_name: str) -> Dict[str, Any]:
        """
        Load configuration for a specific tranche.
        
        Args:
            tranche_name: Name of the tranche
            
        Returns:
            Dictionary with tranche configuration
        """
        tranche_config_path = self.tranches_dir / f"{tranche_name}.json"
        
        if not tranche_config_path.exists():
            logger.error(f"Tranche configuration not found: {tranche_name}")
            return {}
        
        try:
            with open(tranche_config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            logger.info(f"Loaded tranche configuration: {tranche_name}")
            return config_data
            
        except Exception as e:
            logger.error(f"Error loading tranche configuration {tranche_name}: {e}")
            return {}
    
    def get_tranche_context(self, tranche_name: str, 
                           publisher_name: Optional[str] = None,
                           imprint_name: Optional[str] = None) -> ConfigurationContext:
        """
        Create configuration context for a tranche.
        
        Args:
            tranche_name: Name of the tranche
            publisher_name: Optional publisher name override
            imprint_name: Optional imprint name override
            
        Returns:
            Configuration context for the tranche
        """
        # Load tranche config to get publisher and imprint if not provided
        tranche_config = self.load_tranche_config(tranche_name)
        
        # Get publisher and imprint from tranche config if not provided
        if not publisher_name and "publishing_defaults" in tranche_config:
            publisher_name = tranche_config["publishing_defaults"].get("publisher")
        
        if not imprint_name and "publishing_defaults" in tranche_config:
            imprint_name = tranche_config["publishing_defaults"].get("imprint")
        
        # Create context
        context = ConfigurationContext(
            tranche_name=tranche_name,
            publisher_name=publisher_name,
            imprint_name=imprint_name
        )
        
        return context
    
    def get_tranche_value(self, tranche_name: str, key: str, default: Any = None) -> Any:
        """
        Get configuration value for a tranche.
        
        Args:
            tranche_name: Name of the tranche
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        context = self.get_tranche_context(tranche_name)
        return self.config.get_value(key, context, default)
    
    def get_tranche_field_exclusions(self, tranche_name: str) -> List[str]:
        """
        Get list of fields to exclude from CSV output for a tranche.
        
        Args:
            tranche_name: Name of the tranche
            
        Returns:
            List of field names to exclude
        """
        tranche_config = self.load_tranche_config(tranche_name)
        return tranche_config.get("field_exclusions", [])
    
    def get_tranche_annotation_boilerplate(self, tranche_name: str) -> Dict[str, str]:
        """
        Get annotation boilerplate text for a tranche.
        
        Args:
            tranche_name: Name of the tranche
            
        Returns:
            Dictionary with prefix and suffix text
        """
        tranche_config = self.load_tranche_config(tranche_name)
        return tranche_config.get("annotation_boilerplate", {"prefix": "", "suffix": ""})
    
    def get_tranche_bisac_subject(self, tranche_name: str) -> Optional[str]:
        """
        Get required BISAC subject for a tranche.
        
        Args:
            tranche_name: Name of the tranche
            
        Returns:
            Required BISAC subject or None if not specified
        """
        tranche_config = self.load_tranche_config(tranche_name)
        return tranche_config.get("required_bisac_subject")
    
    def get_tranche_info(self, tranche_name: str) -> Dict[str, Any]:
        """
        Get tranche information.
        
        Args:
            tranche_name: Name of the tranche
            
        Returns:
            Dictionary with tranche information
        """
        tranche_config = self.load_tranche_config(tranche_name)
        return tranche_config.get("tranche_info", {})
    
    def get_book_index_in_tranche(self, tranche_name: str, book_id: str) -> Optional[int]:
        """
        Get the index of a book in a tranche.
        
        Args:
            tranche_name: Name of the tranche
            book_id: Book ID (UUID)
            
        Returns:
            Index of the book in the tranche or None if not found
        """
        tranche_config = self.load_tranche_config(tranche_name)
        
        # Check if the tranche has a book_list
        if "book_list" in tranche_config:
            book_list = tranche_config["book_list"]
            for i, book in enumerate(book_list):
                if book.get("uuid") == book_id:
                    return i
        
        # If no book_list or book not found, return None
        return None
    
    def get_field_overrides(self, tranche_name: str) -> Dict[str, Any]:
        """
        Get field overrides for a tranche.
        
        Args:
            tranche_name: Name of the tranche
            
        Returns:
            Dictionary with field override values
        """
        tranche_config = self.load_tranche_config(tranche_name)
        return tranche_config.get("field_overrides", {})
    
    def get_append_fields(self, tranche_name: str) -> List[str]:
        """
        Get list of fields that should append rather than replace.
        
        Args:
            tranche_name: Name of the tranche
            
        Returns:
            List of field names that should use append behavior
        """
        tranche_config = self.load_tranche_config(tranche_name)
        return tranche_config.get("append_fields", [])
    
    def get_file_path_templates(self, tranche_name: str) -> Dict[str, str]:
        """
        Get file path templates for a tranche.
        
        Args:
            tranche_name: Name of the tranche
            
        Returns:
            Dictionary with file path templates
        """
        tranche_config = self.load_tranche_config(tranche_name)
        return tranche_config.get("file_path_templates", {})
    
    def get_blank_fields(self, tranche_name: str) -> List[str]:
        """
        Get list of fields that should be forced to blank.
        
        Args:
            tranche_name: Name of the tranche
            
        Returns:
            List of field names that should be blank
        """
        tranche_config = self.load_tranche_config(tranche_name)
        return tranche_config.get("blank_fields", [])
    
    def get_tranche_override_config(self, tranche_name: str) -> Dict[str, Any]:
        """
        Get complete tranche override configuration.
        
        Args:
            tranche_name: Name of the tranche
            
        Returns:
            Dictionary with all override configuration
        """
        tranche_config = self.load_tranche_config(tranche_name)
        
        return {
            "field_overrides": tranche_config.get("field_overrides", {}),
            "append_fields": tranche_config.get("append_fields", []),
            "file_path_templates": tranche_config.get("file_path_templates", {}),
            "blank_fields": tranche_config.get("blank_fields", [])
        }
    
    def validate_tranche_config(self, tranche_name: str) -> Dict[str, List[str]]:
        """
        Validate tranche configuration schema.
        
        Args:
            tranche_name: Name of the tranche
            
        Returns:
            Dictionary with validation results (errors and warnings)
        """
        tranche_config = self.load_tranche_config(tranche_name)
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["tranche_info", "publisher", "imprint"]
        for field in required_fields:
            if field not in tranche_config:
                errors.append(f"Missing required field: {field}")
        
        # Validate field_overrides structure
        if "field_overrides" in tranche_config:
            field_overrides = tranche_config["field_overrides"]
            if not isinstance(field_overrides, dict):
                errors.append("field_overrides must be a dictionary")
        
        # Validate append_fields structure
        if "append_fields" in tranche_config:
            append_fields = tranche_config["append_fields"]
            if not isinstance(append_fields, list):
                errors.append("append_fields must be a list")
        
        # Validate file_path_templates structure
        if "file_path_templates" in tranche_config:
            templates = tranche_config["file_path_templates"]
            if not isinstance(templates, dict):
                errors.append("file_path_templates must be a dictionary")
            else:
                # Check for required template variables
                for template_name, template in templates.items():
                    if not isinstance(template, str):
                        errors.append(f"Template {template_name} must be a string")
        
        # Validate blank_fields structure
        if "blank_fields" in tranche_config:
            blank_fields = tranche_config["blank_fields"]
            if not isinstance(blank_fields, list):
                errors.append("blank_fields must be a list")
        
        # Check for deprecated fields
        deprecated_fields = ["annotation_boilerplate"]
        for field in deprecated_fields:
            if field in tranche_config and not isinstance(tranche_config[field], str):
                warnings.append(f"Field {field} should be moved to field_overrides")
        
        return {
            "errors": errors,
            "warnings": warnings
        }


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create tranche config loader
    loader = TrancheConfigLoader()
    
    # List available tranches
    tranches = loader.list_available_tranches()
    print(f"Available tranches: {tranches}")
    
    # Load tranche config
    if tranches:
        tranche_name = tranches[0]
        tranche_config = loader.load_tranche_config(tranche_name)
        print(f"Tranche config: {tranche_config}")
        
        # Get tranche value
        rendition_booktype = loader.get_tranche_value(tranche_name, "rendition_booktype", "Perfect Bound")
        print(f"Rendition booktype: {rendition_booktype}")
        
        # Get field exclusions
        exclusions = loader.get_tranche_field_exclusions(tranche_name)
        print(f"Field exclusions: {exclusions}")
        
        # Get annotation boilerplate
        boilerplate = loader.get_tranche_annotation_boilerplate(tranche_name)
        print(f"Annotation boilerplate: {boilerplate}")