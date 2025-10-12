"""Configuration management for TrillionsOfPeople package."""

import os
import sys
import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from .models import Config
from .exceptions import ConfigurationError

# Handle TOML imports for different Python versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


class ConfigManager:
    """Manages configuration loading from multiple sources with security validation."""
    
    # Valid API key patterns for validation
    API_KEY_PATTERNS = {
        'openai': re.compile(r'^sk-[A-Za-z0-9_-]{20,}$'),
        'anthropic': re.compile(r'^sk-ant-[A-Za-z0-9\-_]{10,}$'),
        'replicate': re.compile(r'^r8_[A-Za-z0-9]{10,}$'),
    }
    
    # Sensitive field names that should not be logged
    SENSITIVE_FIELDS = {'openai_api_key', 'anthropic_api_key', 'replicate_api_key', 'stripe_secret_key'}
    
    def __init__(self, env_prefix: str = "TRILLIONS_"):
        """Initialize configuration manager."""
        self.env_prefix = env_prefix
        self.logger = logging.getLogger(__name__)
    
    def load_config(
        self, 
        config_file: Optional[str] = None,
        cli_overrides: Optional[Dict[str, Any]] = None
    ) -> Config:
        """
        Load configuration from multiple sources in order of precedence:
        1. CLI arguments (highest priority)
        2. Environment variables
        3. Configuration file
        4. Default values (lowest priority)
        """
        config = Config()
        
        # Load from config file first (lowest precedence)
        if config_file:
            self._load_from_file(config, config_file)
        
        # Load from environment variables (medium precedence)
        self._load_from_env(config)
        
        # Apply CLI overrides (highest precedence)
        if cli_overrides:
            self._apply_cli_overrides(config, cli_overrides)
            
        # Validate configuration
        self.validate_config(config)
        
        # Log configuration (without sensitive data)
        self._log_config(config)
        
        return config
    
    def _load_from_env(self, config: Config) -> None:
        """Load configuration from environment variables with TRILLIONS_ prefix."""
        env_mappings = {
            'OPENAI_API_KEY': 'openai_api_key',
            'ANTHROPIC_API_KEY': 'anthropic_api_key',
            'REPLICATE_API_KEY': 'replicate_api_key',
            'DEFAULT_COUNTRY': 'default_country',
            'DEFAULT_YEAR': ('default_year', int),
            'MAX_PEOPLE_PER_REQUEST': ('max_people_per_request', int),
            'ENABLE_IMAGE_GENERATION': ('enable_image_generation', self._parse_bool),
            'DATA_DIRECTORY': 'data_directory',
            'LOG_LEVEL': 'log_level',
            'CACHE_TTL': ('cache_ttl', int),
            'REQUEST_TIMEOUT': ('request_timeout', int),
            'MAX_RETRIES': ('max_retries', int),
            'ENABLE_TELEMETRY': ('enable_telemetry', self._parse_bool),
        }
        
        for env_key, config_attr in env_mappings.items():
            env_value = os.getenv(f"{self.env_prefix}{env_key}")
            if env_value is not None:
                try:
                    if isinstance(config_attr, tuple):
                        attr_name, converter = config_attr
                        setattr(config, attr_name, converter(env_value))
                    else:
                        setattr(config, config_attr, env_value)
                except (ValueError, TypeError) as e:
                    raise ConfigurationError(
                        f"Invalid value for {self.env_prefix}{env_key}: {env_value}. Error: {e}"
                    )
    
    def _load_from_file(self, config: Config, config_file: str) -> None:
        """Load configuration from TOML file."""
        if tomllib is None:
            raise ConfigurationError(
                "TOML support not available. Install tomli for Python < 3.11"
            )
        
        config_path = Path(config_file)
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_file}")
        
        if not config_path.is_file():
            raise ConfigurationError(f"Configuration path is not a file: {config_file}")
        
        # Validate file permissions for security
        if config_path.stat().st_mode & 0o077:
            self.logger.warning(
                f"Configuration file {config_file} has overly permissive permissions. "
                "Consider setting permissions to 600 for security."
            )
        
        try:
            with open(config_path, 'rb') as f:
                toml_data = tomllib.load(f)
            
            # Extract configuration section
            config_section = toml_data.get('trillions_of_people', toml_data)
            
            # Map TOML keys to config attributes
            self._apply_toml_config(config, config_section)
            
        except tomllib.TOMLDecodeError as e:
            raise ConfigurationError(f"Invalid TOML in configuration file: {e}")
        except (OSError, IOError) as e:
            raise ConfigurationError(f"Error reading configuration file: {e}")
    
    def _apply_toml_config(self, config: Config, toml_data: Dict[str, Any]) -> None:
        """Apply TOML configuration data to config object."""
        toml_mappings = {
            'openai_api_key': 'openai_api_key',
            'anthropic_api_key': 'anthropic_api_key',
            'replicate_api_key': 'replicate_api_key',
            'default_country': 'default_country',
            'default_year': 'default_year',
            'max_people_per_request': 'max_people_per_request',
            'enable_image_generation': 'enable_image_generation',
            'data_directory': 'data_directory',
            'log_level': 'log_level',
            'cache_ttl': 'cache_ttl',
            'request_timeout': 'request_timeout',
            'max_retries': 'max_retries',
            'enable_telemetry': 'enable_telemetry',
        }
        
        for toml_key, config_attr in toml_mappings.items():
            if toml_key in toml_data:
                try:
                    setattr(config, config_attr, toml_data[toml_key])
                except (ValueError, TypeError) as e:
                    raise ConfigurationError(
                        f"Invalid value for {toml_key} in configuration file: {toml_data[toml_key]}. Error: {e}"
                    )
    
    def _apply_cli_overrides(self, config: Config, overrides: Dict[str, Any]) -> None:
        """Apply CLI argument overrides to configuration."""
        for key, value in overrides.items():
            if hasattr(config, key) and value is not None:
                setattr(config, key, value)
    
    def validate_config(self, config: Config) -> None:
        """Comprehensive configuration validation with security checks."""
        errors = []
        
        # Validate numeric ranges
        if config.max_people_per_request <= 0:
            errors.append("max_people_per_request must be positive")
        if config.max_people_per_request > 1000:
            errors.append("max_people_per_request cannot exceed 1000 for safety")
        
        if config.default_year < -233000 or config.default_year > 100000:
            errors.append("default_year must be between -233000 and 100000")
        
        if config.cache_ttl < 0:
            errors.append("cache_ttl must be non-negative")
        
        if config.request_timeout <= 0:
            errors.append("request_timeout must be positive")
        
        if config.max_retries < 0:
            errors.append("max_retries must be non-negative")
        if config.max_retries > 10:
            errors.append("max_retries cannot exceed 10 for safety")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if config.log_level.upper() not in valid_log_levels:
            errors.append(f"log_level must be one of: {', '.join(valid_log_levels)}")
        
        # Validate data directory
        if config.data_directory:
            data_path = Path(config.data_directory)
            # Check for directory traversal attempts
            if '..' in str(data_path) or str(data_path).startswith('/'):
                errors.append("data_directory contains invalid path components")
        
        # Validate API keys format (without logging the actual keys)
        self._validate_api_keys(config, errors)
        
        # Validate country code if not "Random"
        if config.default_country and config.default_country != "Random":
            if not self._is_valid_country_code(config.default_country):
                errors.append(f"Invalid country code: {config.default_country}")
        
        if errors:
            raise ConfigurationError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    
    def _validate_api_keys(self, config: Config, errors: List[str]) -> None:
        """Validate API key formats without logging sensitive data."""
        api_keys = {
            'openai_api_key': config.openai_api_key,
            'anthropic_api_key': getattr(config, 'anthropic_api_key', None),
            'replicate_api_key': getattr(config, 'replicate_api_key', None),
        }
        
        for key_name, key_value in api_keys.items():
            if key_value:
                provider = key_name.split('_')[0]
                if provider in self.API_KEY_PATTERNS:
                    if not self.API_KEY_PATTERNS[provider].match(key_value):
                        errors.append(f"Invalid {provider} API key format")
                
                # Check for common security issues
                if len(key_value) < 20:
                    errors.append(f"{key_name} appears to be too short")
                if key_value.lower() in ['test', 'demo', 'example', 'placeholder']:
                    errors.append(f"{key_name} appears to be a placeholder value")
    
    def _is_valid_country_code(self, country: str) -> bool:
        """Validate country code format."""
        # Accept full country names or ISO codes
        if len(country) == 2:
            return country.isupper() and country.isalpha()
        elif len(country) == 3:
            return country.isupper() and country.isalpha()
        elif len(country) == 4 and country.isupper() and country.isalpha():
            # Reject 4+ character codes that look like invalid ISO codes
            return False
        else:
            # Accept full country names (basic validation)
            return len(country) > 2 and all(c.isalpha() or c.isspace() or c == '-' for c in country)
    
    def _parse_bool(self, value: str) -> bool:
        """Parse boolean values from string."""
        if isinstance(value, bool):
            return value
        return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
    
    def _log_config(self, config: Config) -> None:
        """Log configuration without sensitive data."""
        safe_config = {}
        for key, value in config.__dict__.items():
            if key in self.SENSITIVE_FIELDS:
                safe_config[key] = "***REDACTED***" if value else None
            else:
                safe_config[key] = value
        
        self.logger.info(f"Configuration loaded: {safe_config}")
    
    def setup_logging(self, config: Config) -> None:
        """Set up logging configuration with security considerations."""
        # Ensure log level is uppercase
        log_level = config.log_level.upper()
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            force=True  # Override any existing configuration
        )
        
        # Set specific loggers to appropriate levels to reduce noise
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        
        # Create custom filter to prevent API key logging
        class SensitiveDataFilter(logging.Filter):
            def __init__(self, api_key_patterns):
                super().__init__()
                self.api_key_patterns = api_key_patterns
            
            def filter(self, record):
                # Redact potential API keys from log messages
                if hasattr(record, 'msg') and isinstance(record.msg, str):
                    for pattern in self.api_key_patterns.values():
                        record.msg = pattern.sub('***REDACTED***', record.msg)
                return True
        
        # Apply filter to all handlers
        sensitive_filter = SensitiveDataFilter(self.API_KEY_PATTERNS)
        for handler in logging.root.handlers:
            handler.addFilter(sensitive_filter)
        
        logger = logging.getLogger(__name__)
        logger.info(f"Logging configured at {log_level} level")
    
    def create_sample_config(self, output_path: str) -> None:
        """Create a sample configuration file with documentation."""
        sample_config = '''# TrillionsOfPeople Configuration File
# This file uses TOML format: https://toml.io/

[trillions_of_people]

# API Keys (can also be set via environment variables)
# openai_api_key = "sk-your-openai-key-here"
# anthropic_api_key = "sk-ant-your-anthropic-key-here"
# replicate_api_key = "r8_your-replicate-key-here"

# Default settings
default_country = "Random"
default_year = 2100
max_people_per_request = 5

# Feature toggles
enable_image_generation = true
enable_telemetry = false

# Directories and paths
data_directory = "data"

# Logging
log_level = "INFO"

# Performance settings
cache_ttl = 3600  # Cache time-to-live in seconds
request_timeout = 30  # Request timeout in seconds
max_retries = 3  # Maximum number of retries for failed requests
'''
        
        try:
            with open(output_path, 'w') as f:
                f.write(sample_config)
            
            # Set secure file permissions
            os.chmod(output_path, 0o600)
            
            self.logger.info(f"Sample configuration file created at: {output_path}")
        except (OSError, IOError) as e:
            raise ConfigurationError(f"Failed to create sample config file: {e}")
    
    def validate_api_key_security(self, api_key: str, provider: str) -> List[str]:
        """Validate API key security and return list of warnings."""
        warnings = []
        
        if not api_key:
            return warnings
        
        # Check for common security issues
        if api_key.lower() in ['test', 'demo', 'example', 'placeholder', 'your-key-here']:
            warnings.append(f"API key appears to be a placeholder value")
        
        if len(api_key) < 20:
            warnings.append(f"API key appears to be too short")
        
        # Check format if we have a pattern for this provider
        if provider in self.API_KEY_PATTERNS:
            if not self.API_KEY_PATTERNS[provider].match(api_key):
                warnings.append(f"API key format doesn't match expected pattern for {provider}")
        
        return warnings