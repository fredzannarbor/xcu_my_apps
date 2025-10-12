"""Publisher Configuration Loader

This module provides functionality to load and manage publisher-specific configurations
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


class PublisherConfigurationManager:
    """
    Manages publisher-specific configurations and integrates with the multi-level
    configuration system.
    """
    
    def __init__(self, config_dir: str = "configs"):
        """
        Initialize publisher configuration manager.
        
        Args:
            config_dir: Base configuration directory
        """
        self.config_dir = Path(config_dir)
        self.publishers_dir = self.config_dir / "publishers"
        self.loaded_publishers: Dict[str, Dict[str, Any]] = {}
        
        # Ensure publishers directory exists
        self.publishers_dir.mkdir(parents=True, exist_ok=True)
        
        # Load all available publisher configurations
        self._load_all_publishers()
    
    def get_publisher_names(self) -> List[str]:
        """
        Get list of all available publisher names.
        
        Returns:
            List of publisher names
        """
        return list(self.loaded_publishers.keys())
    
    def get_publisher_config(self, publisher_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific publisher.
        
        Args:
            publisher_name: Name of the publisher
            
        Returns:
            Publisher configuration dictionary or None if not found
        """
        return self.loaded_publishers.get(publisher_name)
    
    def create_publisher_context(self, publisher_name: str, 
                                imprint_name: str = None,
                                book_isbn: str = None) -> ConfigurationContext:
        """
        Create configuration context for a publisher.
        
        Args:
            publisher_name: Name of the publisher
            imprint_name: Name of the imprint (optional)
            book_isbn: ISBN of the book (optional)
            
        Returns:
            ConfigurationContext for the publisher
        """
        return ConfigurationContext(
            book_isbn=book_isbn,
            imprint_name=imprint_name,
            publisher_name=publisher_name
        )
    
    def get_publisher_defaults(self, publisher_name: str) -> Dict[str, Any]:
        """
        Get default values for a publisher.
        
        Args:
            publisher_name: Name of the publisher
            
        Returns:
            Dictionary of default values
        """
        publisher_config = self.get_publisher_config(publisher_name)
        if not publisher_config:
            return {}
        
        defaults = {}
        
        # Extract defaults from various sections
        sections_to_extract = [
            "default_settings",
            "pricing_strategy", 
            "distribution_settings",
            "metadata_standards",
            "lsi_account_settings"
        ]
        
        for section in sections_to_extract:
            if section in publisher_config:
                section_data = publisher_config[section]
                if isinstance(section_data, dict):
                    defaults.update(section_data)
        
        # Handle territorial configurations
        if "territorial_configs" in publisher_config:
            territorial = publisher_config["territorial_configs"]
            for territory, config in territorial.items():
                for key, value in config.items():
                    defaults[f"{territory.lower()}_{key}"] = value
        
        # Handle legacy compatibility
        if "legacy_compatibility" in publisher_config:
            legacy = publisher_config["legacy_compatibility"]
            if "defaults" in legacy:
                defaults.update(legacy["defaults"])
            if "field_overrides" in legacy:
                defaults.update(legacy["field_overrides"])
        
        # Add publisher-specific fields
        if "publisher" in publisher_config:
            defaults["publisher"] = publisher_config["publisher"]
        if "contact_email" in publisher_config:
            defaults["contact_email"] = publisher_config["contact_email"]
        if "lightning_source_account" in publisher_config:
            defaults["lightning_source_account"] = publisher_config["lightning_source_account"]
        
        return defaults
    
    def get_publisher_field_mappings(self, publisher_name: str) -> Dict[str, Any]:
        """
        Get field mappings specific to a publisher.
        
        Args:
            publisher_name: Name of the publisher
            
        Returns:
            Dictionary of field mappings
        """
        publisher_config = self.get_publisher_config(publisher_name)
        if not publisher_config:
            return {}
        
        mappings = {}
        
        # Extract LSI account settings
        if "lsi_account_settings" in publisher_config:
            lsi_settings = publisher_config["lsi_account_settings"]
            
            lsi_mappings = {
                "Lightning Source Account": lsi_settings.get("account_number", ""),
                "LSI Account": lsi_settings.get("account_number", ""),
                "Account Number": lsi_settings.get("account_number", "")
            }
            
            mappings.update(lsi_mappings)
        
        # Extract distribution settings
        if "distribution_settings" in publisher_config:
            dist_settings = publisher_config["distribution_settings"]
            
            dist_mappings = {
                "Cover Submission Method": dist_settings.get("cover_submission_method", "FTP"),
                "Text Block Submission Method": dist_settings.get("text_block_submission_method", "FTP"),
                "Rendition /Booktype": dist_settings.get("rendition_booktype", "paperback"),
                "Carton Pack Quantity": dist_settings.get("carton_pack_quantity", "24"),
                "Order Type Eligibility": dist_settings.get("order_type_eligibility", "POD")
            }
            
            mappings.update(dist_mappings)
        
        # Extract company info
        if "company_info" in publisher_config:
            company_info = publisher_config["company_info"]
            
            company_mappings = {
                "Publisher": company_info.get("legal_name", publisher_config.get("publisher", "")),
                "Country of Origin": publisher_config.get("default_settings", {}).get("country_of_origin", "US")
            }
            
            mappings.update(company_mappings)
        
        return mappings
    
    def get_territorial_pricing_config(self, publisher_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Get territorial pricing configuration for a publisher.
        
        Args:
            publisher_name: Name of the publisher
            
        Returns:
            Dictionary of territorial pricing configurations
        """
        publisher_config = self.get_publisher_config(publisher_name)
        if not publisher_config:
            return {}
        
        return publisher_config.get("territorial_configs", {})
    
    def get_quality_standards(self, publisher_name: str) -> Dict[str, Any]:
        """
        Get quality standards for a publisher.
        
        Args:
            publisher_name: Name of the publisher
            
        Returns:
            Dictionary of quality standards
        """
        publisher_config = self.get_publisher_config(publisher_name)
        if not publisher_config:
            return {}
        
        return publisher_config.get("quality_standards", {})
    
    def get_metadata_standards(self, publisher_name: str) -> Dict[str, Any]:
        """
        Get metadata standards for a publisher.
        
        Args:
            publisher_name: Name of the publisher
            
        Returns:
            Dictionary of metadata standards
        """
        publisher_config = self.get_publisher_config(publisher_name)
        if not publisher_config:
            return {}
        
        return publisher_config.get("metadata_standards", {})
    
    def integrate_with_multi_level_config(self, multi_config: MultiLevelConfiguration) -> None:
        """
        Integrate publisher configurations with multi-level configuration system.
        
        Args:
            multi_config: MultiLevelConfiguration instance to integrate with
        """
        for publisher_name, publisher_config in self.loaded_publishers.items():
            logger.info(f"Integrating publisher configuration: {publisher_name}")
            
            # Get default values for this publisher
            defaults = self.get_publisher_defaults(publisher_name)
            
            # Set each default value in the multi-level configuration
            for key, value in defaults.items():
                multi_config.set_value(
                    key=key,
                    value=value,
                    level=ConfigurationLevel.PUBLISHER_SPECIFIC,
                    description=f"Publisher default for {publisher_name}",
                    source=f"publisher:{publisher_name}"
                )
    
    def validate_publisher_config(self, publisher_name: str) -> Dict[str, Any]:
        """
        Validate a publisher configuration.
        
        Args:
            publisher_name: Name of the publisher to validate
            
        Returns:
            Validation results dictionary
        """
        publisher_config = self.get_publisher_config(publisher_name)
        if not publisher_config:
            return {"valid": False, "errors": ["Publisher configuration not found"]}
        
        errors = []
        warnings = []
        
        # Required fields
        required_fields = ["publisher", "contact_email", "lightning_source_account"]
        for field in required_fields:
            if field not in publisher_config or not publisher_config[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate email format
        if "contact_email" in publisher_config:
            email = publisher_config["contact_email"]
            if "@" not in email or "." not in email:
                errors.append(f"Invalid email format: {email}")
        
        # Validate LSI account
        if "lightning_source_account" in publisher_config:
            account = publisher_config["lightning_source_account"]
            if not str(account).isdigit() and not str(account).startswith("LSI"):
                warnings.append(f"Unusual LSI account format: {account}")
        
        # Validate pricing strategy
        if "pricing_strategy" in publisher_config:
            pricing = publisher_config["pricing_strategy"]
            for key, value in pricing.items():
                if "discount" in key:
                    try:
                        discount_val = float(str(value).replace("%", ""))
                        if not (0 <= discount_val <= 100):
                            errors.append(f"Invalid discount percentage: {key} = {value}")
                    except ValueError:
                        errors.append(f"Invalid discount value: {key} = {value}")
        
        # Validate territorial configs
        if "territorial_configs" in publisher_config:
            territorial = publisher_config["territorial_configs"]
            for territory, config in territorial.items():
                if "exchange_rate" in config:
                    try:
                        rate = float(config["exchange_rate"])
                        if rate <= 0:
                            errors.append(f"Invalid exchange rate for {territory}: {rate}")
                    except ValueError:
                        errors.append(f"Invalid exchange rate format for {territory}")
        
        # Check for required sections
        required_sections = ["company_info", "distribution_settings"]
        for section in required_sections:
            if section not in publisher_config:
                warnings.append(f"Missing recommended section: {section}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "publisher_name": publisher_name
        }
    
    def create_publisher_from_template(self, publisher_name: str, 
                                     contact_email: str,
                                     lsi_account: str,
                                     template_path: str = None) -> bool:
        """
        Create a new publisher configuration from template.
        
        Args:
            publisher_name: Name of the new publisher
            contact_email: Contact email for the publisher
            lsi_account: LSI account number
            template_path: Path to template file (optional)
            
        Returns:
            True if created successfully
        """
        try:
            # Use default template if none specified
            if not template_path:
                template_path = self.publishers_dir / "publisher_template.json"
            
            # Load template
            with open(template_path, 'r', encoding='utf-8') as f:
                template_config = json.load(f)
            
            # Customize template
            template_config["publisher"] = publisher_name
            template_config["contact_email"] = contact_email
            template_config["lightning_source_account"] = lsi_account
            
            # Update config info
            template_config["_config_info"]["description"] = f"{publisher_name} publisher configuration"
            
            # Update company info
            if "company_info" in template_config:
                template_config["company_info"]["legal_name"] = publisher_name
            
            # Update LSI account settings
            if "lsi_account_settings" in template_config:
                template_config["lsi_account_settings"]["account_number"] = lsi_account
            
            # Clean template-specific fields
            if "_template_info" in template_config:
                del template_config["_template_info"]
            if "_required_fields" in template_config:
                del template_config["_required_fields"]
            if "_optional_fields" in template_config:
                del template_config["_optional_fields"]
            
            # Replace template placeholders
            config_str = json.dumps(template_config, indent=2)
            config_str = config_str.replace("TEMPLATE_PUBLISHER_NAME", publisher_name)
            config_str = config_str.replace("template-publisher.com", 
                                          publisher_name.lower().replace(" ", "-") + ".com")
            config_str = config_str.replace("LSI000000", lsi_account)
            
            # Save new configuration
            new_config_path = self.publishers_dir / f"{publisher_name.lower().replace(' ', '_')}.json"
            with open(new_config_path, 'w', encoding='utf-8') as f:
                f.write(config_str)
            
            # Reload configurations
            self._load_all_publishers()
            
            logger.info(f"Created new publisher configuration: {publisher_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating publisher configuration: {e}")
            return False
    
    def _load_all_publishers(self) -> None:
        """Load all publisher configurations from the publishers directory."""
        self.loaded_publishers.clear()
        
        if not self.publishers_dir.exists():
            logger.warning(f"Publishers directory not found: {self.publishers_dir}")
            return
        
        for config_file in self.publishers_dir.glob("*.json"):
            # Skip template files
            if "template" in config_file.name.lower():
                continue
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Get publisher name from config or filename
                publisher_name = config_data.get("publisher", 
                                config_data.get("publisher_name", config_file.stem))
                
                self.loaded_publishers[publisher_name] = config_data
                logger.debug(f"Loaded publisher configuration: {publisher_name}")
                
            except Exception as e:
                logger.error(f"Error loading publisher configuration {config_file}: {e}")
        
        logger.info(f"Loaded {len(self.loaded_publishers)} publisher configurations")


def create_enhanced_lsi_registry_with_publisher(publisher_name: str = None,
                                              config_dir: str = "configs") -> 'FieldMappingRegistry':
    """
    Create an enhanced LSI field mapping registry with publisher-specific configurations.
    
    Args:
        publisher_name: Name of the publisher to use for configuration
        config_dir: Configuration directory
        
    Returns:
        Enhanced FieldMappingRegistry with publisher-specific settings
    """
    from .enhanced_field_mappings import create_enhanced_field_mapping_registry
    from .field_mapping import DefaultMappingStrategy
    
    # Create base registry
    registry = create_enhanced_field_mapping_registry()
    
    if publisher_name:
        # Load publisher configuration
        publisher_manager = PublisherConfigurationManager(config_dir)
        publisher_config = publisher_manager.get_publisher_config(publisher_name)
        
        if publisher_config:
            # Get field mappings from publisher configuration
            field_mappings = publisher_manager.get_publisher_field_mappings(publisher_name)
            
            # Register publisher-specific field mappings
            for field_name, field_value in field_mappings.items():
                if field_value:  # Only register non-empty values
                    registry.register_strategy(field_name, DefaultMappingStrategy(field_value))
            
            logger.info(f"Applied {len(field_mappings)} publisher-specific field mappings for {publisher_name}")
    
    return registry