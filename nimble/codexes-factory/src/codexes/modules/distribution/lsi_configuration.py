"""
LSI Configuration Management System

This module provides configuration management for LSI ACS generation,
supporting multiple publishers, imprints, and territorial configurations.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field

# Set up debug logging
DEBUG_LSI_CONFIG = True
logger = logging.getLogger(__name__)

def debug_log(message):
    """Print debug messages when DEBUG_LSI_CONFIG is True."""
    if DEBUG_LSI_CONFIG:
        print(f"[LSI_CONFIG_DEBUG] {message}")


@dataclass
class TerritorialConfig:
    """Configuration for a specific territory/region."""
    territory_code: str
    wholesale_discount_percent: str = ""
    returnability: str = ""
    currency: str = ""
    pricing_multiplier: float = 1.0
    exchange_rate: float = 1.0
    tax_rate: str = "0.0"
    shipping_class: str = ""
    market_type: str = ""
    additional_fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class ImprintConfig:
    """Configuration for a specific imprint."""
    imprint_name: str
    publisher: str = ""
    default_values: Dict[str, str] = field(default_factory=dict)
    territorial_configs: Dict[str, TerritorialConfig] = field(default_factory=dict)
    field_overrides: Dict[str, str] = field(default_factory=dict)


class LSIConfiguration:
    """
    Manages LSI configuration including defaults, overrides, and imprint-specific settings.
    
    Supports hierarchical configuration with the following precedence:
    1. Field overrides (highest priority)
    2. Imprint-specific configurations
    3. Default values (lowest priority)
    """
    
    def __init__(self, config_path: Optional[str] = None, config_dir: Optional[str] = None):
        """
        Initialize LSI configuration.
        
        Args:
            config_path: Path to a specific configuration file
            config_dir: Directory containing configuration files (defaults to configs/)
        """
        debug_log(f"Initializing LSI Configuration with config_path={config_path}, config_dir={config_dir}")
        self.config_dir = Path(config_dir) if config_dir else Path("configs")
        self.publishers_dir = self.config_dir / "publishers"
        self.imprints_dir = self.config_dir / "imprints"
        
        debug_log(f"Config directories: main={self.config_dir}, publishers={self.publishers_dir}, imprints={self.imprints_dir}")
        debug_log(f"Config directories exist: main={self.config_dir.exists()}, publishers={self.publishers_dir.exists()}, imprints={self.imprints_dir.exists()}")
        
        # Core configuration data
        self._defaults: Dict[str, str] = {}
        self._field_overrides: Dict[str, str] = {}
        self._imprint_configs: Dict[str, ImprintConfig] = {}
        self._territorial_configs: Dict[str, TerritorialConfig] = {}
        
        # Load configuration
        if config_path:
            debug_log(f"Loading configuration from specific path: {config_path}")
            self._load_config_file(config_path)
        else:
            debug_log("Loading default configurations")
            self._load_default_configs()
    
    def _load_config_file(self, config_path: str) -> None:
        """Load configuration from a specific file."""
        debug_log(f"Attempting to load config file: {config_path}")
        config_path_obj = Path(config_path)
        debug_log(f"Absolute path: {config_path_obj.absolute()}")
        debug_log(f"File exists: {config_path_obj.exists()}")
        
        try:
            debug_log(f"Opening file: {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            debug_log(f"Config loaded successfully. Keys: {list(config_data.keys())}")
            self._parse_config_data(config_data)
        except FileNotFoundError:
            debug_log(f"ERROR: Configuration file not found: {config_path}")
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError as e:
            debug_log(f"ERROR: Invalid JSON in configuration file {config_path}: {e}")
            raise ValueError(f"Invalid JSON in configuration file {config_path}: {e}")
        except Exception as e:
            debug_log(f"ERROR: Unexpected error loading config file: {e}")
            import traceback
            debug_log(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _load_default_configs(self) -> None:
        """Load default configurations from the configs directory structure."""
        # Load main default configuration if it exists
        default_config_path = self.config_dir / "default_lsi_config.json"
        if default_config_path.exists():
            self._load_config_file(str(default_config_path))
        
        # Load publisher configurations
        if self.publishers_dir.exists():
            for publisher_file in self.publishers_dir.glob("*.json"):
                self._load_publisher_config(publisher_file)
        
        # Load imprint configurations
        if self.imprints_dir.exists():
            for imprint_file in self.imprints_dir.glob("*.json"):
                self._load_imprint_config(imprint_file)
    
    def _load_publisher_config(self, config_path: Path) -> None:
        """Load publisher-specific configuration."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Merge publisher defaults into main defaults
            if "defaults" in config_data:
                self._defaults.update(config_data["defaults"])
            
            # Load territorial configs if present
            if "territorial_configs" in config_data:
                for territory, config in config_data["territorial_configs"].items():
                    self._territorial_configs[territory] = TerritorialConfig(
                        territory_code=territory,
                        **config
                    )
                    
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load publisher config {config_path}: {e}")
    
    def _load_imprint_config(self, config_path: Path) -> None:
        """Load imprint-specific configuration."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            imprint_name = config_path.stem
            
            # Create imprint config
            imprint_config = ImprintConfig(
                imprint_name=imprint_name,
                publisher=config_data.get("publisher", ""),
                default_values=config_data.get("defaults", {}),
                field_overrides=config_data.get("field_overrides", {})
            )
            
            # Load territorial configs for this imprint
            if "territorial_configs" in config_data:
                for territory, config in config_data["territorial_configs"].items():
                    imprint_config.territorial_configs[territory] = TerritorialConfig(
                        territory_code=territory,
                        **config
                    )
            
            self._imprint_configs[imprint_name] = imprint_config
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load imprint config {config_path}: {e}")
    
    def _parse_config_data(self, config_data: Dict[str, Any]) -> None:
        """Parse configuration data from a loaded JSON structure."""
        debug_log(f"Parsing config data with keys: {list(config_data.keys())}")
        
        # Load defaults
        if "defaults" in config_data:
            debug_log(f"Updating defaults with: {list(config_data['defaults'].keys())}")
            self._defaults.update(config_data["defaults"])
        else:
            debug_log("No 'defaults' section found in config")
        
        # Load field overrides
        if "field_overrides" in config_data:
            debug_log(f"Updating field_overrides with: {list(config_data['field_overrides'].keys())}")
            self._field_overrides.update(config_data["field_overrides"])
        else:
            debug_log("No 'field_overrides' section found in config")
        
        # Load imprint configurations
        if "imprint_configs" in config_data:
            debug_log(f"Found imprint_configs: {list(config_data['imprint_configs'].keys())}")
            for imprint_name, imprint_data in config_data["imprint_configs"].items():
                debug_log(f"Processing imprint config for: {imprint_name}")
                imprint_config = ImprintConfig(
                    imprint_name=imprint_name,
                    publisher=imprint_data.get("publisher", ""),
                    default_values=imprint_data.get("defaults", {}),
                    field_overrides=imprint_data.get("field_overrides", {})
                )
                
                # Load territorial configs for this imprint
                if "territorial_configs" in imprint_data:
                    debug_log(f"Found territorial_configs for imprint {imprint_name}: {list(imprint_data['territorial_configs'].keys())}")
                    for territory, config in imprint_data["territorial_configs"].items():
                        imprint_config.territorial_configs[territory] = TerritorialConfig(
                            territory_code=territory,
                            **config
                        )
                
                self._imprint_configs[imprint_name] = imprint_config
        else:
            debug_log("No 'imprint_configs' section found in config")
        
        # Load global territorial configurations
        if "territorial_configs" in config_data:
            debug_log(f"Found global territorial_configs: {list(config_data['territorial_configs'].keys())}")
            for territory, config in config_data["territorial_configs"].items():
                self._territorial_configs[territory] = TerritorialConfig(
                    territory_code=territory,
                    **config
                )
        else:
            debug_log("No global 'territorial_configs' section found in config")
            
        debug_log(f"Config parsing complete. Current state: defaults={len(self._defaults)} keys, field_overrides={len(self._field_overrides)} keys, imprints={len(self._imprint_configs)} configs, territories={len(self._territorial_configs)} configs")
    
    def get_default_value(self, field_name: str) -> str:
        """
        Get the default value for a field.
        
        Args:
            field_name: Name of the LSI field
            
        Returns:
            Default value for the field, or empty string if not found
        """
        value = self._defaults.get(field_name, "")
        debug_log(f"get_default_value('{field_name}'): {value}")
        return value
    
    def get_field_override(self, field_name: str) -> Optional[str]:
        """
        Get field override value if it exists.
        
        Args:
            field_name: Name of the LSI field
            
        Returns:
            Override value if exists, None otherwise
        """
        return self._field_overrides.get(field_name)
    
    def get_imprint_config(self, imprint: str) -> Optional[ImprintConfig]:
        """
        Get configuration for a specific imprint.
        
        Args:
            imprint: Name of the imprint
            
        Returns:
            ImprintConfig object if found, None otherwise
        """
        return self._imprint_configs.get(imprint)
    
    def get_territorial_config(self, territory: str) -> Optional[TerritorialConfig]:
        """
        Get configuration for a specific territory.
        
        Args:
            territory: Territory code (e.g., 'UK', 'EU', 'US')
            
        Returns:
            TerritorialConfig object if found, None otherwise
        """
        return self._territorial_configs.get(territory)
    
    def get_field_value(self, field_name: str, imprint: Optional[str] = None, 
                       territory: Optional[str] = None) -> str:
        """
        Get field value with full precedence hierarchy.
        
        Precedence order:
        1. Field overrides (global)
        2. Imprint-specific field overrides
        3. Territorial configuration values
        4. Imprint default values
        5. Global default values
        
        Args:
            field_name: Name of the LSI field
            imprint: Imprint name for imprint-specific values
            territory: Territory code for territorial values
            
        Returns:
            Field value based on precedence hierarchy
        """
        # 1. Check global field overrides first
        if field_name in self._field_overrides:
            return self._field_overrides[field_name]
        
        # 2. Check imprint-specific overrides
        if imprint and imprint in self._imprint_configs:
            imprint_config = self._imprint_configs[imprint]
            if field_name in imprint_config.field_overrides:
                return imprint_config.field_overrides[field_name]
            
            # 3. Check territorial configuration within imprint
            if territory and territory in imprint_config.territorial_configs:
                territorial_config = imprint_config.territorial_configs[territory]
                if field_name in territorial_config.additional_fields:
                    return territorial_config.additional_fields[field_name]
                
                # Check standard territorial fields
                territorial_value = self._get_territorial_field_value(territorial_config, field_name)
                if territorial_value:
                    return territorial_value
            
            # 4. Check imprint default values
            if field_name in imprint_config.default_values:
                return imprint_config.default_values[field_name]
        
        # 5. Check global territorial configuration
        if territory and territory in self._territorial_configs:
            territorial_config = self._territorial_configs[territory]
            if field_name in territorial_config.additional_fields:
                return territorial_config.additional_fields[field_name]
            
            territorial_value = self._get_territorial_field_value(territorial_config, field_name)
            if territorial_value:
                return territorial_value
        
        # 6. Fall back to global defaults
        return self.get_default_value(field_name)
    
    def _get_territorial_field_value(self, territorial_config: TerritorialConfig, 
                                   field_name: str) -> Optional[str]:
        """Get value from territorial config for standard territorial fields."""
        field_mapping = {
            "wholesale_discount_percent": territorial_config.wholesale_discount_percent,
            "returnability": territorial_config.returnability,
            "currency": territorial_config.currency,
            "exchange_rate": str(territorial_config.exchange_rate),
            "tax_rate": territorial_config.tax_rate,
            "shipping_class": territorial_config.shipping_class,
            "market_type": territorial_config.market_type,
        }
        
        return field_mapping.get(field_name)
    
    def get_available_imprints(self) -> List[str]:
        """Get list of available imprint names."""
        return list(self._imprint_configs.keys())
    
    def get_available_territories(self) -> List[str]:
        """Get list of available territory codes."""
        territories = set(self._territorial_configs.keys())
        
        # Add territories from imprint configs
        for imprint_config in self._imprint_configs.values():
            territories.update(imprint_config.territorial_configs.keys())
        
        return sorted(list(territories))
    
    def validate_configuration(self) -> List[str]:
        """
        Validate the loaded configuration for common issues.
        
        Returns:
            List of validation warnings/errors
        """
        warnings = []
        
        # Check for required default fields
        required_fields = [
            "publisher", "lightning_source_account", "cover_submission_method",
            "text_block_submission_method"
        ]
        
        for field in required_fields:
            if not self.get_default_value(field):
                warnings.append(f"Missing default value for required field: {field}")
        
        # Check imprint configurations
        for imprint_name, imprint_config in self._imprint_configs.items():
            if not imprint_config.publisher:
                warnings.append(f"Imprint '{imprint_name}' missing publisher information")
        
        # Check territorial configurations
        for territory, config in self._territorial_configs.items():
            if not config.wholesale_discount_percent:
                warnings.append(f"Territory '{territory}' missing wholesale discount percentage")
        
        return warnings
    
    def save_configuration(self, output_path: str) -> None:
        """
        Save current configuration to a JSON file.
        
        Args:
            output_path: Path where to save the configuration
        """
        config_data = {
            "defaults": self._defaults,
            "field_overrides": self._field_overrides,
            "imprint_configs": {},
            "territorial_configs": {}
        }
        
        # Serialize imprint configs
        for imprint_name, imprint_config in self._imprint_configs.items():
            config_data["imprint_configs"][imprint_name] = {
                "publisher": imprint_config.publisher,
                "defaults": imprint_config.default_values,
                "field_overrides": imprint_config.field_overrides,
                "territorial_configs": {}
            }
            
            # Add territorial configs for this imprint
            for territory, territorial_config in imprint_config.territorial_configs.items():
                config_data["imprint_configs"][imprint_name]["territorial_configs"][territory] = {
                    "wholesale_discount_percent": territorial_config.wholesale_discount_percent,
                    "returnability": territorial_config.returnability,
                    "currency": territorial_config.currency,
                    "pricing_multiplier": territorial_config.pricing_multiplier,
                    "exchange_rate": territorial_config.exchange_rate,
                    "tax_rate": territorial_config.tax_rate,
                    "shipping_class": territorial_config.shipping_class,
                    "market_type": territorial_config.market_type,
                    **territorial_config.additional_fields
                }
        
        # Serialize global territorial configs
        for territory, territorial_config in self._territorial_configs.items():
            config_data["territorial_configs"][territory] = {
                "wholesale_discount_percent": territorial_config.wholesale_discount_percent,
                "returnability": territorial_config.returnability,
                "currency": territorial_config.currency,
                "pricing_multiplier": territorial_config.pricing_multiplier,
                "exchange_rate": territorial_config.exchange_rate,
                "tax_rate": territorial_config.tax_rate,
                "shipping_class": territorial_config.shipping_class,
                "market_type": territorial_config.market_type,
                **territorial_config.additional_fields
            }
        
        # Write to file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)