"""Imprint Configuration Loader

This module provides functionality to load and manage imprint-specific configurations
for the LSI field enhancement system.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .multi_level_config import (
    MultiLevelConfiguration, ConfigurationLevel, ConfigurationContext,
    ConfigurationEntry
)

logger = logging.getLogger(__name__)


class ImprintConfigurationManager:
    """
    Manages imprint-specific configurations and integrates with the multi-level
    configuration system.
    """
    
    def __init__(self, config_dir: str = "configs"):
        """
        Initialize imprint configuration manager.
        
        Args:
            config_dir: Base configuration directory
        """
        self.config_dir = Path(config_dir)
        self.imprints_dir = self.config_dir / "imprints"
        self.loaded_imprints: Dict[str, Dict[str, Any]] = {}
        
        # Ensure imprints directory exists
        self.imprints_dir.mkdir(parents=True, exist_ok=True)
        
        # Load all available imprint configurations
        self._load_all_imprints()
    
    def get_imprint_names(self) -> List[str]:
        """
        Get list of all available imprint names.
        
        Returns:
            List of imprint names
        """
        return list(self.loaded_imprints.keys())
    
    def get_imprint_config(self, imprint_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific imprint.
        
        Args:
            imprint_name: Name of the imprint
            
        Returns:
            Imprint configuration dictionary or None if not found
        """
        return self.loaded_imprints.get(imprint_name)
    
    def create_imprint_context(self, imprint_name: str, 
                              publisher_name: str = None,
                              book_isbn: str = None) -> ConfigurationContext:
        """
        Create configuration context for an imprint.
        
        Args:
            imprint_name: Name of the imprint
            publisher_name: Name of the publisher (optional)
            book_isbn: ISBN of the book (optional)
            
        Returns:
            ConfigurationContext for the imprint
        """
        # Get publisher name from imprint config if not provided
        if not publisher_name:
            imprint_config = self.get_imprint_config(imprint_name)
            if imprint_config:
                publisher_name = imprint_config.get("publisher")
        
        return ConfigurationContext(
            book_isbn=book_isbn,
            imprint_name=imprint_name,
            publisher_name=publisher_name
        )
    
    def get_imprint_defaults(self, imprint_name: str) -> Dict[str, Any]:
        """
        Get default values for an imprint.
        
        Args:
            imprint_name: Name of the imprint
            
        Returns:
            Dictionary of default values
        """
        imprint_config = self.get_imprint_config(imprint_name)
        if not imprint_config:
            return {}
        
        defaults = {}
        
        # Extract defaults from various sections
        sections_to_extract = [
            "default_book_settings",
            "pricing_defaults", 
            "distribution_settings",
            "metadata_defaults",
            "lsi_specific_settings"
        ]
        
        for section in sections_to_extract:
            if section in imprint_config:
                defaults.update(imprint_config[section])
        
        # Handle nested configurations
        if "territorial_configs" in imprint_config:
            territorial = imprint_config["territorial_configs"]
            for territory, config in territorial.items():
                for key, value in config.items():
                    defaults[f"{territory.lower()}_{key}"] = value
        
        # Handle legacy compatibility
        if "legacy_compatibility" in imprint_config:
            legacy = imprint_config["legacy_compatibility"]
            if "defaults" in legacy:
                defaults.update(legacy["defaults"])
            if "field_overrides" in legacy:
                defaults.update(legacy["field_overrides"])
        
        return defaults
    
    def get_imprint_field_mappings(self, imprint_name: str) -> Dict[str, Any]:
        """
        Get field mappings specific to an imprint.
        
        Args:
            imprint_name: Name of the imprint
            
        Returns:
            Dictionary of field mappings
        """
        imprint_config = self.get_imprint_config(imprint_name)
        if not imprint_config:
            return {}
        
        mappings = {}
        
        # Extract LSI-specific settings
        if "lsi_specific_settings" in imprint_config:
            lsi_settings = imprint_config["lsi_specific_settings"]
            
            # Map LSI fields
            lsi_field_mappings = {
                "Stamped Text LEFT": lsi_settings.get("stamped_text_left", ""),
                "Stamped Text CENTER": lsi_settings.get("stamped_text_center", ""),
                "Stamped Text RIGHT": lsi_settings.get("stamped_text_right", ""),
                "LSI Special Category": lsi_settings.get("lsi_special_category", ""),
                "Metadata Contact Dictionary": lsi_settings.get("metadata_contact_dictionary", ""),
                "Publisher Reference ID": lsi_settings.get("publisher_reference_id", "")
            }
            
            # Add flex fields
            if "flex_fields" in lsi_settings:
                flex_fields = lsi_settings["flex_fields"]
                for i in range(1, 6):
                    field_key = f"lsi_flexfield{i}"
                    if field_key in flex_fields:
                        mappings[f"LSI FlexField{i}"] = flex_fields[field_key]
            
            mappings.update(lsi_field_mappings)
        
        # Extract distribution settings
        if "distribution_settings" in imprint_config:
            dist_settings = imprint_config["distribution_settings"]
            
            dist_mappings = {
                "Lightning Source Account": dist_settings.get("lightning_source_account", ""),
                "Cover Submission Method": dist_settings.get("cover_submission_method", "FTP"),
                "Text Block Submission Method": dist_settings.get("text_block_submission_method", "FTP"),
                "Rendition /Booktype": dist_settings.get("rendition_booktype", "paperback"),
                "Carton Pack Quantity": dist_settings.get("carton_pack_quantity", "24"),
                "Order Type Eligibility": dist_settings.get("order_type_eligibility", "POD")
            }
            
            mappings.update(dist_mappings)
        
        return mappings
    
    def get_territorial_pricing_config(self, imprint_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Get territorial pricing configuration for an imprint.
        
        Args:
            imprint_name: Name of the imprint
            
        Returns:
            Dictionary of territorial pricing configurations
        """
        imprint_config = self.get_imprint_config(imprint_name)
        if not imprint_config:
            return {}
        
        return imprint_config.get("territorial_configs", {})
    
    def integrate_with_multi_level_config(self, multi_config: MultiLevelConfiguration) -> None:
        """
        Integrate imprint configurations with multi-level configuration system.
        
        Args:
            multi_config: MultiLevelConfiguration instance to integrate with
        """
        for imprint_name, imprint_config in self.loaded_imprints.items():
            logger.info(f"Integrating imprint configuration: {imprint_name}")
            
            # Get default values for this imprint
            defaults = self.get_imprint_defaults(imprint_name)
            
            # Set each default value in the multi-level configuration
            for key, value in defaults.items():
                multi_config.set_value(
                    key=key,
                    value=value,
                    level=ConfigurationLevel.IMPRINT_SPECIFIC,
                    description=f"Imprint default for {imprint_name}",
                    source=f"imprint:{imprint_name}"
                )
    
    def validate_imprint_config(self, imprint_name: str) -> Dict[str, Any]:
        """
        Validate an imprint configuration.
        
        Args:
            imprint_name: Name of the imprint to validate
            
        Returns:
            Validation results dictionary
        """
        imprint_config = self.get_imprint_config(imprint_name)
        if not imprint_config:
            return {"valid": False, "errors": ["Imprint configuration not found"]}
        
        errors = []
        warnings = []
        
        # Required fields
        required_fields = ["imprint", "publisher", "contact_email"]
        for field in required_fields:
            if field not in imprint_config or not imprint_config[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate email format
        if "contact_email" in imprint_config:
            email = imprint_config["contact_email"]
            if "@" not in email or "." not in email:
                errors.append(f"Invalid email format: {email}")
        
        # Validate pricing defaults
        if "pricing_defaults" in imprint_config:
            pricing = imprint_config["pricing_defaults"]
            for key, value in pricing.items():
                if "discount" in key:
                    try:
                        discount_val = float(str(value).replace("%", ""))
                        if not (0 <= discount_val <= 100):
                            errors.append(f"Invalid discount percentage: {key} = {value}")
                    except ValueError:
                        errors.append(f"Invalid discount value: {key} = {value}")
        
        # Validate territorial configs
        if "territorial_configs" in imprint_config:
            territorial = imprint_config["territorial_configs"]
            for territory, config in territorial.items():
                if "exchange_rate" in config:
                    try:
                        rate = float(config["exchange_rate"])
                        if rate <= 0:
                            errors.append(f"Invalid exchange rate for {territory}: {rate}")
                    except ValueError:
                        errors.append(f"Invalid exchange rate format for {territory}")
        
        # Check for deprecated fields
        deprecated_fields = ["defaults", "field_overrides"]
        for field in deprecated_fields:
            if field in imprint_config and field not in ["legacy_compatibility"]:
                warnings.append(f"Deprecated field found: {field}. Consider moving to appropriate section.")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "imprint_name": imprint_name
        }
    
    def create_imprint_from_template(self, imprint_name: str, 
                                   publisher_name: str,
                                   contact_email: str,
                                   template_path: str = None) -> bool:
        """
        Create a new imprint configuration from template.
        
        Args:
            imprint_name: Name of the new imprint
            publisher_name: Name of the publisher
            contact_email: Contact email for the imprint
            template_path: Path to template file (optional)
            
        Returns:
            True if created successfully
        """
        try:
            # Use default template if none specified
            if not template_path:
                template_path = self.imprints_dir / "imprint_template.json"
            
            # Load template
            with open(template_path, 'r', encoding='utf-8') as f:
                template_config = json.load(f)
            
            # Customize template
            template_config["imprint"] = imprint_name
            template_config["publisher"] = publisher_name
            template_config["contact_email"] = contact_email
            
            # Update config info
            template_config["_config_info"]["description"] = f"{imprint_name} imprint configuration"
            template_config["_config_info"]["parent_publisher"] = publisher_name
            
            # Clean template-specific fields
            if "_template_info" in template_config:
                del template_config["_template_info"]
            if "_required_fields" in template_config:
                del template_config["_required_fields"]
            if "_optional_fields" in template_config:
                del template_config["_optional_fields"]
            
            # Replace template placeholders
            config_str = json.dumps(template_config, indent=2)
            config_str = config_str.replace("TEMPLATE_IMPRINT_NAME", imprint_name)
            config_str = config_str.replace("TEMPLATE_PUBLISHER_NAME", publisher_name)
            config_str = config_str.replace("template-imprint.com", 
                                          imprint_name.lower().replace(" ", "-") + ".com")
            
            # Save new configuration
            new_config_path = self.imprints_dir / f"{imprint_name.lower().replace(' ', '_')}.json"
            with open(new_config_path, 'w', encoding='utf-8') as f:
                f.write(config_str)
            
            # Reload configurations
            self._load_all_imprints()
            
            logger.info(f"Created new imprint configuration: {imprint_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating imprint configuration: {e}")
            return False
    
    def _load_all_imprints(self) -> None:
        """Load all imprint configurations from the imprints directory."""
        self.loaded_imprints.clear()
        
        # Support both new and legacy locations. Prefer 'imprints/'.
        primary_dir = self.imprints_dir if self.imprints_dir else Path("imprints")
        fallback_dir = Path("configs/imprints")

        dirs_to_scan = []
        if primary_dir.exists():
            dirs_to_scan.append(primary_dir)
        if fallback_dir.exists() and fallback_dir != primary_dir:
            dirs_to_scan.append(fallback_dir)

        if not dirs_to_scan:
            logger.warning(f"Imprints directory not found: {primary_dir} (also checked {fallback_dir})")
            return
        
        total_loaded = 0
        for dir_path in dirs_to_scan:
            for config_file in dir_path.glob("*.json"):
                # Skip template files
                if "template" in config_file.name.lower():
                    continue
                
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    # Get imprint name from config or filename
                    imprint_name = config_data.get("imprint", config_file.stem)
                    
                    # Only overwrite if not already loaded from the preferred directory
                    if imprint_name not in self.loaded_imprints:
                        self.loaded_imprints[imprint_name] = config_data
                        logger.debug(f"Loaded imprint configuration: {imprint_name} ({config_file})")
                        total_loaded += 1
                except Exception as e:
                    logger.error(f"Error loading imprint configuration {config_file}: {e}")
        
        logger.info(f"Loaded {total_loaded} imprint configurations")


def create_enhanced_lsi_registry_with_imprints(imprint_name: str = None,
                                             config_dir: str = "configs") -> 'FieldMappingRegistry':
    """
    Create an enhanced LSI field mapping registry with imprint-specific configurations.
    
    Args:
        imprint_name: Name of the imprint to use for configuration
        config_dir: Configuration directory
        
    Returns:
        Enhanced FieldMappingRegistry with imprint-specific settings
    """
    from .enhanced_field_mappings import create_enhanced_field_mapping_registry
    from .field_mapping import DefaultMappingStrategy
    
    # Create base registry
    registry = create_enhanced_field_mapping_registry()
    
    if imprint_name:
        # Load imprint configuration
        imprint_manager = ImprintConfigurationManager(config_dir)
        imprint_config = imprint_manager.get_imprint_config(imprint_name)
        
        if imprint_config:
            # Get field mappings from imprint configuration
            field_mappings = imprint_manager.get_imprint_field_mappings(imprint_name)
            
            # Register imprint-specific field mappings
            for field_name, field_value in field_mappings.items():
                if field_value:  # Only register non-empty values
                    registry.register_strategy(field_name, DefaultMappingStrategy(field_value))
            
            logger.info(f"Applied {len(field_mappings)} imprint-specific field mappings for {imprint_name}")
    
    return registry