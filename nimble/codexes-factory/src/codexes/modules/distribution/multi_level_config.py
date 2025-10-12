"""Multi-Level Configuration System

This module provides a hierarchical configuration system that supports
multiple levels of configuration with priority-based resolution.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class ConfigurationLevel(Enum):
    """Configuration levels in priority order (highest to lowest)."""
    FIELD_OVERRIDE = "field_override"      # Highest priority
    BOOK_SPECIFIC = "book_specific"        # Book-specific overrides
    TRANCHE_SPECIFIC = "tranche_specific"  # Tranche-level configuration
    IMPRINT_SPECIFIC = "imprint_specific"  # Imprint-level configuration
    PUBLISHER_SPECIFIC = "publisher_specific"  # Publisher-level configuration
    GLOBAL_DEFAULT = "global_default"      # Lowest priority


@dataclass
class ConfigurationEntry:
    """Represents a single configuration entry with metadata."""
    value: Any
    level: ConfigurationLevel
    source: str = ""
    description: str = ""
    last_modified: str = ""
    
    def __post_init__(self):
        if not self.last_modified:
            from datetime import datetime
            self.last_modified = datetime.now().isoformat()


@dataclass
class ConfigurationContext:
    """Context information for configuration resolution."""
    book_isbn: Optional[str] = None
    tranche_name: Optional[str] = None
    imprint_name: Optional[str] = None
    publisher_name: Optional[str] = None
    field_overrides: Dict[str, Any] = field(default_factory=dict)


class MultiLevelConfiguration:
    """
    Multi-level configuration system with priority-based resolution.
    
    This system supports hierarchical configuration with the following priority order:
    1. Field Overrides (highest priority)
    2. Book-specific configuration
    3. Imprint-specific configuration
    4. Publisher-specific configuration
    5. Global defaults (lowest priority)
    """
    
    def __init__(self, config_dir: str = "configs"):
        """
        Initialize multi-level configuration system.
        
        Args:
            config_dir: Base directory for configuration files
        """
        self.config_dir = Path(config_dir)
        self.configurations: Dict[ConfigurationLevel, Dict[str, ConfigurationEntry]] = {
            level: {} for level in ConfigurationLevel
        }
        self.validation_rules: Dict[str, callable] = {}
        self._loaded_contexts: set = set()  # Track loaded context-specific configs
        
        # Load configurations
        self._load_all_configurations()
    
    def get_value(self, key: str, context: ConfigurationContext = None, 
                  default: Any = None) -> Any:
        """
        Get configuration value with priority-based resolution.
        
        Args:
            key: Configuration key
            context: Configuration context for resolution
            default: Default value if not found
            
        Returns:
            Configuration value from highest priority source
        """
        if context is None:
            context = ConfigurationContext()
        
        # Check field overrides first
        if key in context.field_overrides:
            return context.field_overrides[key]
        
        # Check each configuration level in priority order
        for level in ConfigurationLevel:
            config_dict = self._get_level_config(level, context)
            if key in config_dict:
                entry = config_dict[key]
                logger.debug(f"Found {key} in {level.value}: {entry.value}")
                return entry.value
        
        # Return default if not found
        logger.debug(f"Using default value for {key}: {default}")
        return default
    
    def set_value(self, key: str, value: Any, level: ConfigurationLevel,
                  context: ConfigurationContext = None, 
                  description: str = "", source: str = "") -> bool:
        """
        Set configuration value at specified level.
        
        Args:
            key: Configuration key
            value: Configuration value
            level: Configuration level
            context: Configuration context
            description: Description of the configuration
            source: Source of the configuration
            
        Returns:
            True if value was set successfully
        """
        try:
            # Validate the value if validation rule exists
            if key in self.validation_rules:
                if not self.validation_rules[key](value):
                    logger.error(f"Validation failed for {key}: {value}")
                    return False
            
            # Create configuration entry
            entry = ConfigurationEntry(
                value=value,
                level=level,
                source=source or f"{level.value}_config",
                description=description
            )
            
            # Store in appropriate level
            if level == ConfigurationLevel.FIELD_OVERRIDE:
                if context and hasattr(context, 'field_overrides'):
                    context.field_overrides[key] = value
                else:
                    self.configurations[level][key] = entry
            else:
                self.configurations[level][key] = entry
            
            logger.info(f"Set {key} = {value} at level {level.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            return False
    
    def get_configuration_info(self, key: str, context: ConfigurationContext = None) -> Dict[str, Any]:
        """
        Get detailed information about a configuration key.
        
        Args:
            key: Configuration key
            context: Configuration context
            
        Returns:
            Dictionary with configuration information
        """
        if context is None:
            context = ConfigurationContext()
        
        info = {
            "key": key,
            "value": None,
            "level": None,
            "source": None,
            "description": None,
            "last_modified": None,
            "available_levels": []
        }
        
        # Find the active configuration
        for level in ConfigurationLevel:
            config_dict = self._get_level_config(level, context)
            if key in config_dict:
                entry = config_dict[key]
                if info["value"] is None:  # First (highest priority) match
                    info.update({
                        "value": entry.value,
                        "level": level.value,
                        "source": entry.source,
                        "description": entry.description,
                        "last_modified": entry.last_modified
                    })
                
                # Add to available levels
                info["available_levels"].append({
                    "level": level.value,
                    "value": entry.value,
                    "source": entry.source
                })
        
        return info
    
    def list_all_configurations(self, context: ConfigurationContext = None) -> Dict[str, Any]:
        """
        List all available configurations with their sources.
        
        Args:
            context: Configuration context
            
        Returns:
            Dictionary of all configurations
        """
        if context is None:
            context = ConfigurationContext()
        
        all_configs = {}
        all_keys = set()
        
        # Collect all keys from all levels
        for level in ConfigurationLevel:
            config_dict = self._get_level_config(level, context)
            all_keys.update(config_dict.keys())
        
        # Get information for each key
        for key in sorted(all_keys):
            all_configs[key] = self.get_configuration_info(key, context)
        
        return all_configs
    
    def add_validation_rule(self, key: str, validator: callable) -> None:
        """
        Add validation rule for a configuration key.
        
        Args:
            key: Configuration key
            validator: Validation function that returns True if valid
        """
        self.validation_rules[key] = validator
        logger.info(f"Added validation rule for {key}")
    
    def load_configuration_file(self, file_path: str, level: ConfigurationLevel) -> bool:
        """
        Load configuration from a JSON file.
        
        Args:
            file_path: Path to configuration file
            level: Configuration level to load into
            
        Returns:
            True if loaded successfully
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"Configuration file not found: {file_path}")
                return False
            
            with open(path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Load each configuration entry
            for key, value in config_data.items():
                if isinstance(value, dict) and "value" in value:
                    # Structured configuration entry
                    entry = ConfigurationEntry(
                        value=value["value"],
                        level=level,
                        source=str(path),
                        description=value.get("description", ""),
                        last_modified=value.get("last_modified", "")
                    )
                else:
                    # Simple value
                    entry = ConfigurationEntry(
                        value=value,
                        level=level,
                        source=str(path)
                    )
                
                self.configurations[level][key] = entry
            
            logger.info(f"Loaded {len(config_data)} configurations from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration file {file_path}: {e}")
            return False
    
    def save_configuration_file(self, file_path: str, level: ConfigurationLevel) -> bool:
        """
        Save configuration level to a JSON file.
        
        Args:
            file_path: Path to save configuration file
            level: Configuration level to save
            
        Returns:
            True if saved successfully
        """
        try:
            config_data = {}
            
            for key, entry in self.configurations[level].items():
                config_data[key] = {
                    "value": entry.value,
                    "description": entry.description,
                    "last_modified": entry.last_modified
                }
            
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            logger.info(f"Saved {len(config_data)} configurations to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration file {file_path}: {e}")
            return False
    
    def _get_level_config(self, level: ConfigurationLevel, 
                         context: ConfigurationContext) -> Dict[str, ConfigurationEntry]:
        """
        Get configuration dictionary for a specific level and context.
        
        Args:
            level: Configuration level
            context: Configuration context
            
        Returns:
            Configuration dictionary for the level
        """
        if level == ConfigurationLevel.FIELD_OVERRIDE:
            # Convert field overrides to ConfigurationEntry format
            if context and context.field_overrides:
                return {
                    key: ConfigurationEntry(value, level, "field_override")
                    for key, value in context.field_overrides.items()
                }
            return {}
        
        elif level == ConfigurationLevel.BOOK_SPECIFIC:
            # Book-specific configurations (could be loaded dynamically)
            if context and context.book_isbn:
                book_config_path = self.config_dir / "books" / f"{context.book_isbn}.json"
                if book_config_path.exists() and level not in self._loaded_contexts:
                    # Load book-specific config if not already loaded
                    self.load_configuration_file(str(book_config_path), level)
                    self._loaded_contexts.add((level, context.book_isbn))
            return self.configurations[level]
        
        elif level == ConfigurationLevel.TRANCHE_SPECIFIC:
            # Tranche-specific configurations - Fixed loading logic
            if context and context.tranche_name:
                context_key = (level, context.tranche_name)
                if context_key not in self._loaded_contexts:
                    tranche_config_path = self.config_dir / "tranches" / f"{context.tranche_name}.json"
                    if tranche_config_path.exists():
                        logger.info(f"Loading tranche config: {tranche_config_path}")
                        success = self.load_configuration_file(str(tranche_config_path), level)
                        if success:
                            self._loaded_contexts.add(context_key)
                            logger.info(f"Successfully loaded tranche config for {context.tranche_name}")
                        else:
                            logger.error(f"Failed to load tranche config for {context.tranche_name}")
                    else:
                        logger.warning(f"Tranche config file not found: {tranche_config_path}")
                        self._loaded_contexts.add(context_key)  # Mark as attempted
            return self.configurations[level]
        
        elif level == ConfigurationLevel.IMPRINT_SPECIFIC:
            # Imprint-specific configurations - Fixed loading logic
            if context and context.imprint_name:
                context_key = (level, context.imprint_name)
                if context_key not in self._loaded_contexts:
                    imprint_config_path = self.config_dir / "imprints" / f"{context.imprint_name}.json"
                    if imprint_config_path.exists():
                        logger.info(f"Loading imprint config: {imprint_config_path}")
                        success = self.load_configuration_file(str(imprint_config_path), level)
                        if success:
                            self._loaded_contexts.add(context_key)
                            logger.info(f"Successfully loaded imprint config for {context.imprint_name}")
                        else:
                            logger.error(f"Failed to load imprint config for {context.imprint_name}")
                    else:
                        logger.warning(f"Imprint config file not found: {imprint_config_path}")
                        self._loaded_contexts.add(context_key)  # Mark as attempted
            return self.configurations[level]
        
        elif level == ConfigurationLevel.PUBLISHER_SPECIFIC:
            # Publisher-specific configurations - Fixed loading logic
            if context and context.publisher_name:
                context_key = (level, context.publisher_name)
                if context_key not in self._loaded_contexts:
                    publisher_config_path = self.config_dir / "publishers" / f"{context.publisher_name}.json"
                    if publisher_config_path.exists():
                        logger.info(f"Loading publisher config: {publisher_config_path}")
                        success = self.load_configuration_file(str(publisher_config_path), level)
                        if success:
                            self._loaded_contexts.add(context_key)
                            logger.info(f"Successfully loaded publisher config for {context.publisher_name}")
                        else:
                            logger.error(f"Failed to load publisher config for {context.publisher_name}")
                    else:
                        logger.warning(f"Publisher config file not found: {publisher_config_path}")
                        self._loaded_contexts.add(context_key)  # Mark as attempted
            return self.configurations[level]
        
        else:
            # Global defaults
            return self.configurations[level]
    
    def _load_all_configurations(self) -> None:
        """Load all available configuration files."""
        try:
            # Load global defaults
            global_config_path = self.config_dir / "default_lsi_config.json"
            if global_config_path.exists():
                self.load_configuration_file(str(global_config_path), ConfigurationLevel.GLOBAL_DEFAULT)
            
            # Load publisher configurations
            publishers_dir = self.config_dir / "publishers"
            if publishers_dir.exists():
                for config_file in publishers_dir.glob("*.json"):
                    self.load_configuration_file(str(config_file), ConfigurationLevel.PUBLISHER_SPECIFIC)
            
            # Load imprint configurations
            imprints_dir = self.config_dir / "imprints"
            if imprints_dir.exists():
                for config_file in imprints_dir.glob("*.json"):
                    self.load_configuration_file(str(config_file), ConfigurationLevel.IMPRINT_SPECIFIC)
            
            # Load tranche configurations
            tranches_dir = self.config_dir / "tranches"
            if tranches_dir.exists():
                for config_file in tranches_dir.glob("*.json"):
                    self.load_configuration_file(str(config_file), ConfigurationLevel.TRANCHE_SPECIFIC)
            
            # Load book-specific configurations
            books_dir = self.config_dir / "books"
            if books_dir.exists():
                for config_file in books_dir.glob("*.json"):
                    self.load_configuration_file(str(config_file), ConfigurationLevel.BOOK_SPECIFIC)
            
            logger.info("Loaded all available configuration files")
            
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")


class ConfigurationValidator:
    """Provides common validation functions for configuration values."""
    
    @staticmethod
    def validate_percentage(value: Any) -> bool:
        """Validate percentage value (0-100)."""
        try:
            num_value = float(str(value).replace('%', ''))
            return 0 <= num_value <= 100
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_positive_number(value: Any) -> bool:
        """Validate positive number."""
        try:
            return float(value) > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_non_empty_string(value: Any) -> bool:
        """Validate non-empty string."""
        return isinstance(value, str) and len(value.strip()) > 0
    
    @staticmethod
    def validate_email(value: Any) -> bool:
        """Validate email address format."""
        import re
        if not isinstance(value, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, value) is not None
    
    @staticmethod
    def validate_isbn(value: Any) -> bool:
        """Validate ISBN format."""
        if not isinstance(value, str):
            return False
        isbn_clean = value.replace('-', '').replace(' ', '')
        return len(isbn_clean) in [10, 13] and isbn_clean.isdigit()
    
    @staticmethod
    def validate_date_format(value: Any) -> bool:
        """Validate date format (YYYY-MM-DD)."""
        import re
        if not isinstance(value, str):
            return False
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        return re.match(pattern, value) is not None
    
    @staticmethod
    def validate_choice(choices: List[str]) -> callable:
        """Create validator for choice from list."""
        def validator(value: Any) -> bool:
            return str(value) in choices
        return validator


def create_default_multi_level_config(config_dir: str = "configs") -> MultiLevelConfiguration:
    """
    Create a multi-level configuration with default validation rules.
    
    Args:
        config_dir: Configuration directory
        
    Returns:
        Configured MultiLevelConfiguration instance
    """
    config = MultiLevelConfiguration(config_dir)
    
    # Add common validation rules
    validator = ConfigurationValidator()
    
    # Percentage fields
    percentage_fields = [
        "us_wholesale_discount", "uk_wholesale_discount", "eu_wholesale_discount",
        "ca_wholesale_discount", "au_wholesale_discount", "wholesale_discount_percent"
    ]
    for field in percentage_fields:
        config.add_validation_rule(field, validator.validate_percentage)
    
    # Positive number fields
    positive_number_fields = [
        "carton_pack_quantity", "edition_number", "min_age", "max_age",
        "illustration_count", "page_count"
    ]
    for field in positive_number_fields:
        config.add_validation_rule(field, validator.validate_positive_number)
    
    # Non-empty string fields
    string_fields = [
        "lightning_source_account", "publisher", "imprint", "title",
        "author", "language_code"
    ]
    for field in string_fields:
        config.add_validation_rule(field, validator.validate_non_empty_string)
    
    # Email fields
    config.add_validation_rule("contact_email", validator.validate_email)
    
    # ISBN fields
    isbn_fields = ["isbn13", "isbn10", "isbn"]
    for field in isbn_fields:
        config.add_validation_rule(field, validator.validate_isbn)
    
    # Date fields
    date_fields = ["publication_date", "street_date", "copyright_date"]
    for field in date_fields:
        config.add_validation_rule(field, validator.validate_date_format)
    
    # Choice fields
    config.add_validation_rule("language_code", validator.validate_choice(["eng", "spa", "fre", "ger", "ita"]))
    config.add_validation_rule("binding_type", validator.validate_choice(["paperback", "hardcover", "spiral"]))
    config.add_validation_rule("interior_color", validator.validate_choice(["BW", "Color"]))
    
    return config