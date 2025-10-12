"""
Enhanced Configuration Management Infrastructure for Streamlit UI
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib


@dataclass
class ValidationError:
    field_name: str
    error_message: str
    error_type: str
    suggested_values: List[str] = None


@dataclass
class ValidationWarning:
    field_name: str
    warning_message: str
    warning_type: str


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationWarning]
    parameter_status: Dict[str, str]  # parameter_name -> status


@dataclass
class ConfigurationState:
    publisher: str
    imprint: str
    tranche: str
    parameters: Dict[str, Any]
    validation_results: ValidationResult
    last_updated: datetime
    configuration_hash: str


class EnhancedConfigurationManager:
    """Central component for managing multi-level configurations and UI state"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Cache for loaded configurations
        self._config_cache = {}
        self._available_configs_cache = None
        
    def load_available_configs(self) -> Dict[str, List[str]]:
        """Load and cache available configuration files"""
        if self._available_configs_cache is not None:
            return self._available_configs_cache
            
        configs = {
            'publishers': [],
            'imprints': [],
            'tranches': []
        }
        
        # Load publishers
        publisher_dir = Path("configs/publishers")
        if publisher_dir.exists():
            for file_path in publisher_dir.glob("*.json"):
                configs['publishers'].append(file_path.stem)
                
        # Load imprints
        imprint_dir = Path("configs/imprints")
        if imprint_dir.exists():
            for file_path in imprint_dir.glob("*.json"):
                configs['imprints'].append(file_path.stem)
                
        # Load tranches
        tranche_dir = Path("configs/tranches")
        if tranche_dir.exists():
            for file_path in tranche_dir.glob("*.json"):
                configs['tranches'].append(file_path.stem)
                
        self._available_configs_cache = configs
        return configs
    
    def merge_configurations(self, publisher: str = None, imprint: str = None, tranche: str = None) -> Dict[str, Any]:
        """Merge configurations from all levels with proper inheritance"""
        cache_key = f"{publisher}|{imprint}|{tranche}"
        
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
            
        try:
            # Start with default configuration
            merged_config = self._load_default_config()
            
            # Apply publisher configuration
            if publisher:
                publisher_config = self._load_config_file('publisher', publisher)
                if publisher_config:
                    merged_config = self._deep_merge(merged_config, publisher_config)
                    
            # Apply imprint configuration
            if imprint:
                imprint_config = self._load_config_file('imprint', imprint)
                if imprint_config:
                    merged_config = self._deep_merge(merged_config, imprint_config)
                    
            # Apply tranche configuration
            if tranche:
                tranche_config = self._load_config_file('tranche', tranche)
                if tranche_config:
                    merged_config = self._deep_merge(merged_config, tranche_config)
                    
            # Cache the result
            self._config_cache[cache_key] = merged_config
            return merged_config
            
        except Exception as e:
            self.logger.error(f"Error merging configurations: {e}")
            return self._load_default_config()
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries with override taking precedence"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load the default configuration"""
        try:
            config_path = Path("configs/default_lsi_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading default config: {e}")
        
        # Return minimal default if file loading fails
        return {
            'publisher': 'Nimble Books LLC',
            'imprint': 'xynapse traces',
            'lightning_source_account': '6024045',
            'language_code': 'eng',
            'territorial_rights': 'World'
        }
    
    def _load_config_file(self, config_type: str, name: str) -> Optional[Dict[str, Any]]:
        """Load a configuration file by type and name"""
        try:
            config_dirs = {
                'publisher': 'configs/publishers',
                'imprint': 'configs/imprints',
                'tranche': 'configs/tranches'
            }
            
            if config_type not in config_dirs:
                return None
                
            config_path = Path(config_dirs[config_type]) / f"{name}.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading {config_type} config {name}: {e}")
        
        return None
    
    def validate_configuration(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate configuration parameters"""
        errors = []
        warnings = []
        parameter_status = {}
        
        # Basic validation rules
        required_fields = [
            'publisher', 'imprint', 'lightning_source_account',
            'language_code', 'territorial_rights'
        ]
        
        for field in required_fields:
            if not config.get(field):
                errors.append(ValidationError(
                    field_name=field,
                    error_message=f"{field} is required",
                    error_type="required_field"
                ))
                parameter_status[field] = "error"
            else:
                parameter_status[field] = "valid"
        
        # Validate Lightning Source Account format
        ls_account = config.get('lightning_source_account', '')
        if ls_account and not ls_account.isdigit():
            errors.append(ValidationError(
                field_name='lightning_source_account',
                error_message="Lightning Source Account must be numeric",
                error_type="format_error"
            ))
            parameter_status['lightning_source_account'] = "error"
        
        # Validate territorial pricing
        territorial_configs = config.get('territorial_configs', {})
        for territory, territory_config in territorial_configs.items():
            if not territory_config.get('currency'):
                warnings.append(ValidationWarning(
                    field_name=f'territorial_configs.{territory}.currency',
                    warning_message=f"Currency not specified for {territory}",
                    warning_type="missing_optional"
                ))
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            parameter_status=parameter_status
        )
    
    def get_parameter_groups(self) -> Dict[str, List[str]]:
        """Get parameter groups for UI organization"""
        return {
            'core_settings': [
                'publisher', 'imprint', 'lightning_source_account',
                'language_code', 'country_of_origin'
            ],
            'lsi_configuration': [
                'rendition_booktype', 'cover_submission_method',
                'text_block_submission_method', 'carton_pack_quantity'
            ],
            'territorial_pricing': [
                'territorial_configs', 'us_wholesale_discount',
                'uk_wholesale_discount', 'eu_wholesale_discount'
            ],
            'physical_specifications': [
                'trim_size', 'page_count', 'spine_width',
                'binding_type', 'interior_color', 'cover_type'
            ],
            'metadata_defaults': [
                'bisac_category', 'thema_subject_1', 'audience',
                'contributor_one_role', 'series_name'
            ],
            'distribution_settings': [
                'territorial_rights', 'returnability', 'availability',
                'order_type_eligibility'
            ]
        }
    
    def save_configuration_snapshot(self, config: Dict[str, Any]) -> str:
        """Save configuration snapshot for audit purposes"""
        timestamp = datetime.now().isoformat()
        config_hash = hashlib.md5(json.dumps(config, sort_keys=True).encode()).hexdigest()
        
        snapshot = {
            'timestamp': timestamp,
            'configuration_hash': config_hash,
            'configuration': config
        }
        
        # Save to logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        snapshot_file = logs_dir / f"config_snapshot_{timestamp.replace(':', '-')}.json"
        
        try:
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot, f, indent=2)
            
            self.logger.info(f"Configuration snapshot saved: {snapshot_file}")
            return str(snapshot_file)
            
        except Exception as e:
            self.logger.error(f"Error saving configuration snapshot: {e}")
            return ""
    
    def clear_cache(self):
        """Clear configuration cache"""
        self._config_cache.clear()
        self._available_configs_cache = None
    
    def get_configuration_inheritance_chain(self, publisher: str = None, imprint: str = None, tranche: str = None) -> List[Dict[str, Any]]:
        """Get the inheritance chain showing how configuration is built up"""
        chain = []
        
        # Default config
        default_config = self._load_default_config()
        chain.append({
            'level': 'default',
            'name': 'Default Configuration',
            'config': default_config
        })
        
        # Publisher config
        if publisher:
            publisher_config = self._load_config_file('publisher', publisher)
            if publisher_config:
                chain.append({
                    'level': 'publisher',
                    'name': f'Publisher: {publisher}',
                    'config': publisher_config
                })
        
        # Imprint config
        if imprint:
            imprint_config = self._load_config_file('imprint', imprint)
            if imprint_config:
                chain.append({
                    'level': 'imprint',
                    'name': f'Imprint: {imprint}',
                    'config': imprint_config
                })
        
        # Tranche config
        if tranche:
            tranche_config = self._load_config_file('tranche', tranche)
            if tranche_config:
                chain.append({
                    'level': 'tranche',
                    'name': f'Tranche: {tranche}',
                    'config': tranche_config
                })
        
        return chain