"""Global Configuration Validator

This module provides validation and documentation for global LSI configuration defaults.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class GlobalConfigValidator:
    """
    Validates and documents global LSI configuration defaults.
    """
    
    def __init__(self, config_path: str = "configs/default_lsi_config.json"):
        """
        Initialize global configuration validator.
        
        Args:
            config_path: Path to global configuration file
        """
        self.config_path = Path(config_path)
        self.config_data = None
        self.validation_rules = self._create_validation_rules()
        
        # Load configuration
        self._load_config()
    
    def _load_config(self) -> None:
        """Load global configuration from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
                logger.info(f"Loaded global configuration from {self.config_path}")
            else:
                logger.error(f"Global configuration file not found: {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading global configuration: {e}")
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the global configuration.
        
        Returns:
            Validation results dictionary
        """
        if not self.config_data:
            return {
                "valid": False,
                "errors": ["Configuration not loaded"],
                "warnings": [],
                "sections_validated": 0
            }
        
        errors = []
        warnings = []
        sections_validated = 0
        
        # Validate each section
        for section_name, section_data in self.config_data.items():
            if section_name.startswith("_"):
                continue  # Skip metadata sections
            
            if isinstance(section_data, dict):
                section_errors, section_warnings = self._validate_section(section_name, section_data)
                errors.extend(section_errors)
                warnings.extend(section_warnings)
                sections_validated += 1
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sections_validated": sections_validated,
            "total_fields": self._count_total_fields()
        }
    
    def _validate_section(self, section_name: str, section_data: Dict[str, Any]) -> tuple:
        """
        Validate a configuration section.
        
        Args:
            section_name: Name of the section
            section_data: Section data dictionary
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Get validation rules for this section
        section_rules = self.validation_rules.get(section_name, {})
        
        for field_name, field_value in section_data.items():
            field_key = f"{section_name}.{field_name}"
            
            # Check if field has validation rules
            if field_name in section_rules:
                rule = section_rules[field_name]
                
                # Validate field value
                if not rule["validator"](field_value):
                    errors.append(f"Invalid value for {field_key}: {field_value} ({rule['description']})")
            
            # Check for empty required fields
            if field_name in ["publisher", "lightning_source_account", "contact_email"]:
                if not field_value or str(field_value).strip() == "":
                    warnings.append(f"Empty value for important field: {field_key}")
        
        return errors, warnings
    
    def _create_validation_rules(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Create validation rules for configuration fields.
        
        Returns:
            Dictionary of validation rules
        """
        def validate_percentage(value):
            try:
                num_val = float(str(value).replace("%", ""))
                return 0 <= num_val <= 100
            except:
                return False
        
        def validate_positive_number(value):
            try:
                return float(value) > 0
            except:
                return False
        
        def validate_non_negative_number(value):
            try:
                return float(value) >= 0
            except:
                return False
        
        def validate_language_code(value):
            return isinstance(value, str) and len(value) == 3
        
        def validate_currency_code(value):
            return isinstance(value, str) and len(value) == 3
        
        def validate_choice(choices):
            def validator(value):
                return str(value) in choices
            return validator
        
        return {
            "pricing_defaults": {
                "us_wholesale_discount": {
                    "validator": validate_percentage,
                    "description": "Must be a percentage between 0-100"
                },
                "uk_wholesale_discount": {
                    "validator": validate_percentage,
                    "description": "Must be a percentage between 0-100"
                },
                "eu_wholesale_discount": {
                    "validator": validate_percentage,
                    "description": "Must be a percentage between 0-100"
                }
            },
            "physical_defaults": {
                "page_count": {
                    "validator": validate_positive_number,
                    "description": "Must be a positive number"
                },
                "weight_lbs": {
                    "validator": validate_positive_number,
                    "description": "Must be a positive number"
                },
                "custom_trim_width_inches": {
                    "validator": validate_positive_number,
                    "description": "Must be a positive number"
                },
                "custom_trim_height_inches": {
                    "validator": validate_positive_number,
                    "description": "Must be a positive number"
                }
            },
            "system_defaults": {
                "language_code": {
                    "validator": validate_language_code,
                    "description": "Must be a 3-letter language code"
                },
                "binding_type": {
                    "validator": validate_choice(["paperback", "hardcover", "spiral"]),
                    "description": "Must be paperback, hardcover, or spiral"
                },
                "interior_color": {
                    "validator": validate_choice(["BW", "Color"]),
                    "description": "Must be BW or Color"
                }
            },
            "publishing_defaults": {
                "carton_pack_quantity": {
                    "validator": validate_positive_number,
                    "description": "Must be a positive number"
                }
            }
        }
    
    def _count_total_fields(self) -> int:
        """Count total number of configuration fields."""
        if not self.config_data:
            return 0
        
        total = 0
        for section_name, section_data in self.config_data.items():
            if section_name.startswith("_"):
                continue
            if isinstance(section_data, dict):
                total += len(section_data)
        
        return total
    
    def get_field_documentation(self) -> Dict[str, Dict[str, str]]:
        """
        Get documentation for all configuration fields.
        
        Returns:
            Dictionary of field documentation
        """
        return {
            "system_defaults": {
                "language_code": "Default language code (ISO 639-2/T)",
                "country_of_origin": "Default country of origin",
                "territorial_rights": "Default territorial rights",
                "returnability": "Default return policy",
                "binding_type": "Default binding type",
                "interior_color": "Default interior color",
                "interior_paper": "Default interior paper type",
                "cover_type": "Default cover finish",
                "edition_number": "Default edition number",
                "edition_description": "Default edition description"
            },
            "publishing_defaults": {
                "publisher": "Default publisher name",
                "imprint": "Default imprint name",
                "lightning_source_account": "Default LSI account number",
                "cover_submission_method": "Default cover submission method",
                "text_block_submission_method": "Default text block submission method",
                "rendition_booktype": "Default rendition/book type",
                "carton_pack_quantity": "Default carton pack quantity",
                "order_type_eligibility": "Default order type eligibility"
            },
            "pricing_defaults": {
                "us_wholesale_discount": "Default US wholesale discount percentage",
                "uk_wholesale_discount": "Default UK wholesale discount percentage",
                "eu_wholesale_discount": "Default EU wholesale discount percentage",
                "ca_wholesale_discount": "Default Canada wholesale discount percentage",
                "au_wholesale_discount": "Default Australia wholesale discount percentage"
            },
            "physical_defaults": {
                "trim_size": "Default trim size",
                "page_count": "Default page count",
                "spine_width": "Default spine width",
                "weight_lbs": "Default weight in pounds",
                "custom_trim_width_inches": "Default custom trim width",
                "custom_trim_height_inches": "Default custom trim height"
            },
            "metadata_defaults": {
                "language": "Default language name",
                "audience": "Default target audience",
                "bisac_category": "Default primary BISAC category",
                "bisac_category_2": "Default secondary BISAC category",
                "bisac_category_3": "Default tertiary BISAC category"
            }
        }
    
    def generate_documentation_report(self) -> str:
        """
        Generate a comprehensive documentation report.
        
        Returns:
            Formatted documentation report
        """
        if not self.config_data:
            return "Configuration not loaded"
        
        report = []
        report.append("# Global LSI Configuration Documentation")
        report.append("")
        
        # Add configuration info
        if "_config_info" in self.config_data:
            info = self.config_data["_config_info"]
            report.append(f"**Version:** {info.get('version', 'Unknown')}")
            report.append(f"**Last Updated:** {info.get('last_updated', 'Unknown')}")
            report.append(f"**Description:** {info.get('description', 'No description')}")
            report.append("")
        
        # Add validation results
        validation = self.validate_configuration()
        report.append("## Validation Results")
        report.append(f"- **Status:** {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
        report.append(f"- **Sections Validated:** {validation['sections_validated']}")
        report.append(f"- **Total Fields:** {validation['total_fields']}")
        
        if validation['errors']:
            report.append(f"- **Errors:** {len(validation['errors'])}")
            for error in validation['errors']:
                report.append(f"  - {error}")
        
        if validation['warnings']:
            report.append(f"- **Warnings:** {len(validation['warnings'])}")
            for warning in validation['warnings']:
                report.append(f"  - {warning}")
        
        report.append("")
        
        # Add field documentation
        field_docs = self.get_field_documentation()
        
        for section_name, fields in field_docs.items():
            if section_name in self.config_data:
                report.append(f"## {section_name.replace('_', ' ').title()}")
                report.append("")
                
                section_data = self.config_data[section_name]
                for field_name, description in fields.items():
                    current_value = section_data.get(field_name, "Not set")
                    report.append(f"- **{field_name}**: {description}")
                    report.append(f"  - Current value: `{current_value}`")
                
                report.append("")
        
        return "\n".join(report)
    
    def export_field_list(self) -> List[Dict[str, Any]]:
        """
        Export a list of all configuration fields with their properties.
        
        Returns:
            List of field dictionaries
        """
        if not self.config_data:
            return []
        
        fields = []
        field_docs = self.get_field_documentation()
        
        for section_name, section_data in self.config_data.items():
            if section_name.startswith("_") or not isinstance(section_data, dict):
                continue
            
            section_docs = field_docs.get(section_name, {})
            
            for field_name, field_value in section_data.items():
                fields.append({
                    "section": section_name,
                    "field": field_name,
                    "value": field_value,
                    "description": section_docs.get(field_name, "No description available"),
                    "type": type(field_value).__name__
                })
        
        return fields


def validate_global_configuration(config_path: str = "configs/default_lsi_config.json") -> Dict[str, Any]:
    """
    Validate global LSI configuration.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Validation results
    """
    validator = GlobalConfigValidator(config_path)
    return validator.validate_configuration()


def generate_configuration_documentation(config_path: str = "configs/default_lsi_config.json",
                                       output_path: str = "GLOBAL_CONFIG_DOCUMENTATION.md") -> bool:
    """
    Generate configuration documentation file.
    
    Args:
        config_path: Path to configuration file
        output_path: Path to output documentation file
        
    Returns:
        True if successful
    """
    try:
        validator = GlobalConfigValidator(config_path)
        documentation = validator.generate_documentation_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(documentation)
        
        logger.info(f"Generated configuration documentation: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error generating documentation: {e}")
        return False