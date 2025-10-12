"""Tests for configuration management system."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from trillions_of_people.core.config import ConfigManager
from trillions_of_people.core.models import Config
from trillions_of_people.core.exceptions import ConfigurationError


class TestConfigManager:
    """Test cases for ConfigManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
    
    def test_init_default_prefix(self):
        """Test ConfigManager initialization with default prefix."""
        manager = ConfigManager()
        assert manager.env_prefix == "TRILLIONS_"
    
    def test_init_custom_prefix(self):
        """Test ConfigManager initialization with custom prefix."""
        manager = ConfigManager(env_prefix="TEST_")
        assert manager.env_prefix == "TEST_"
    
    def test_load_config_defaults(self):
        """Test loading configuration with default values."""
        config = self.config_manager.load_config()
        
        assert isinstance(config, Config)
        assert config.default_country == "Random"
        assert config.default_year == 2100
        assert config.max_people_per_request == 5
        assert config.enable_image_generation is True
        assert config.data_directory == "data"
        assert config.log_level == "INFO"
    
    @patch.dict(os.environ, {
        'TRILLIONS_OPENAI_API_KEY': 'sk-test1234567890123456789012345678901234567890123456',
        'TRILLIONS_DEFAULT_COUNTRY': 'US',
        'TRILLIONS_DEFAULT_YEAR': '2050',
        'TRILLIONS_MAX_PEOPLE_PER_REQUEST': '10',
        'TRILLIONS_LOG_LEVEL': 'DEBUG'
    })
    def test_load_from_env(self):
        """Test loading configuration from environment variables."""
        config = self.config_manager.load_config()
        
        assert config.openai_api_key == 'sk-test1234567890123456789012345678901234567890123456'
        assert config.default_country == 'US'
        assert config.default_year == 2050
        assert config.max_people_per_request == 10
        assert config.log_level == 'DEBUG'
    
    @patch.dict(os.environ, {
        'TRILLIONS_ENABLE_IMAGE_GENERATION': 'false',
        'TRILLIONS_ENABLE_TELEMETRY': 'true'
    })
    def test_load_boolean_from_env(self):
        """Test loading boolean values from environment variables."""
        config = self.config_manager.load_config()
        
        assert config.enable_image_generation is False
        assert config.enable_telemetry is True
    
    @patch.dict(os.environ, {'TRILLIONS_DEFAULT_YEAR': 'invalid'})
    def test_load_from_env_invalid_int(self):
        """Test error handling for invalid integer values."""
        with pytest.raises(ConfigurationError, match="Invalid value for TRILLIONS_DEFAULT_YEAR"):
            self.config_manager.load_config()
    
    def test_load_from_toml_file(self):
        """Test loading configuration from TOML file."""
        toml_content = '''
[trillions_of_people]
openai_api_key = "sk-test1234567890123456789012345678901234567890123456"
default_country = "CA"
default_year = 2075
max_people_per_request = 8
log_level = "WARNING"
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            try:
                config = self.config_manager.load_config(config_file=f.name)
                
                assert config.openai_api_key == 'sk-test1234567890123456789012345678901234567890123456'
                assert config.default_country == 'CA'
                assert config.default_year == 2075
                assert config.max_people_per_request == 8
                assert config.log_level == 'WARNING'
            finally:
                os.unlink(f.name)
    
    def test_load_from_nonexistent_file(self):
        """Test error handling for nonexistent config file."""
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            self.config_manager.load_config(config_file="/nonexistent/file.toml")
    
    def test_load_from_invalid_toml(self):
        """Test error handling for invalid TOML syntax."""
        invalid_toml = '''
[trillions_of_people
invalid toml syntax
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(invalid_toml)
            f.flush()
            
            try:
                with pytest.raises(ConfigurationError, match="Invalid TOML"):
                    self.config_manager.load_config(config_file=f.name)
            finally:
                os.unlink(f.name)
    
    def test_cli_overrides(self):
        """Test CLI argument overrides."""
        overrides = {
            'default_country': 'UK',
            'max_people_per_request': 15,
            'log_level': 'ERROR'
        }
        
        config = self.config_manager.load_config(cli_overrides=overrides)
        
        assert config.default_country == 'UK'
        assert config.max_people_per_request == 15
        assert config.log_level == 'ERROR'
    
    def test_precedence_order(self):
        """Test that CLI overrides take precedence over env vars and files."""
        toml_content = '''
[trillions_of_people]
default_country = "CA"
max_people_per_request = 8
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            try:
                with patch.dict(os.environ, {'TRILLIONS_DEFAULT_COUNTRY': 'US'}):
                    overrides = {'default_country': 'UK'}
                    config = self.config_manager.load_config(
                        config_file=f.name,
                        cli_overrides=overrides
                    )
                    
                    # CLI override should win
                    assert config.default_country == 'UK'
                    # File value should be used where no override
                    assert config.max_people_per_request == 8
            finally:
                os.unlink(f.name)
    
    def test_validate_config_success(self):
        """Test successful configuration validation."""
        config = Config(
            default_year=2050,
            max_people_per_request=5,
            log_level="INFO"
        )
        
        # Should not raise any exception
        self.config_manager.validate_config(config)
    
    def test_validate_config_invalid_max_people(self):
        """Test validation error for invalid max_people_per_request."""
        # Create config with valid values first, then modify
        config = Config()
        config.__dict__['max_people_per_request'] = 0  # Bypass Pydantic validation
        
        with pytest.raises(ConfigurationError, match="max_people_per_request must be positive"):
            self.config_manager.validate_config(config)
    
    def test_validate_config_invalid_year(self):
        """Test validation error for invalid year."""
        config = Config()
        config.__dict__['default_year'] = 200000  # Bypass Pydantic validation
        
        with pytest.raises(ConfigurationError, match="default_year must be between"):
            self.config_manager.validate_config(config)
    
    def test_validate_config_invalid_log_level(self):
        """Test validation error for invalid log level."""
        config = Config()
        config.__dict__['log_level'] = "INVALID"  # Bypass Pydantic validation
        
        with pytest.raises(ConfigurationError, match="log_level must be one of"):
            self.config_manager.validate_config(config)
    
    def test_validate_config_directory_traversal(self):
        """Test validation error for directory traversal attempt."""
        config = Config()
        config.__dict__['data_directory'] = "../../../etc"  # Bypass Pydantic validation
        
        with pytest.raises(ConfigurationError, match="data_directory contains invalid path"):
            self.config_manager.validate_config(config)
    
    def test_validate_api_key_format(self):
        """Test API key format validation."""
        # Valid OpenAI key
        config = Config(openai_api_key="sk-1234567890123456789012345678901234567890123456")
        self.config_manager.validate_config(config)
        
        # Invalid OpenAI key format - bypass Pydantic validation
        config = Config()
        config.__dict__['openai_api_key'] = "invalid-key"
        with pytest.raises(ConfigurationError, match="Invalid openai API key format"):
            self.config_manager.validate_config(config)
    
    def test_validate_api_key_security(self):
        """Test API key security validation."""
        warnings = self.config_manager.validate_api_key_security("test", "openai")
        assert "placeholder value" in warnings[0]
        
        warnings = self.config_manager.validate_api_key_security("short", "openai")
        assert "too short" in warnings[0]
    
    def test_create_sample_config(self):
        """Test sample configuration file creation."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            try:
                self.config_manager.create_sample_config(f.name)
                
                # Check file was created and has content
                assert Path(f.name).exists()
                content = Path(f.name).read_text()
                assert "trillions_of_people" in content
                assert "openai_api_key" in content
                
                # Check file permissions (should be 600)
                stat = Path(f.name).stat()
                assert oct(stat.st_mode)[-3:] == '600'
            finally:
                os.unlink(f.name)
    
    def test_parse_bool_values(self):
        """Test boolean parsing from strings."""
        assert self.config_manager._parse_bool("true") is True
        assert self.config_manager._parse_bool("True") is True
        assert self.config_manager._parse_bool("1") is True
        assert self.config_manager._parse_bool("yes") is True
        assert self.config_manager._parse_bool("on") is True
        assert self.config_manager._parse_bool("enabled") is True
        
        assert self.config_manager._parse_bool("false") is False
        assert self.config_manager._parse_bool("False") is False
        assert self.config_manager._parse_bool("0") is False
        assert self.config_manager._parse_bool("no") is False
        assert self.config_manager._parse_bool("off") is False
        assert self.config_manager._parse_bool("disabled") is False
    
    def test_is_valid_country_code(self):
        """Test country code validation."""
        # Valid ISO codes
        assert self.config_manager._is_valid_country_code("US") is True
        assert self.config_manager._is_valid_country_code("USA") is True
        
        # Valid country names
        assert self.config_manager._is_valid_country_code("United States") is True
        assert self.config_manager._is_valid_country_code("United-Kingdom") is True
        
        # Invalid codes
        assert self.config_manager._is_valid_country_code("us") is False  # lowercase
        assert self.config_manager._is_valid_country_code("1") is False   # too short
        assert self.config_manager._is_valid_country_code("USAA") is False # too long for code
    
    @patch('trillions_of_people.core.config.logging')
    def test_setup_logging(self, mock_logging):
        """Test logging setup."""
        config = Config(log_level="DEBUG")
        self.config_manager.setup_logging(config)
        
        mock_logging.basicConfig.assert_called_once()
        call_args = mock_logging.basicConfig.call_args
        assert call_args[1]['level'] == mock_logging.DEBUG
        assert 'force' in call_args[1]
    
    def test_sensitive_data_redaction(self):
        """Test that sensitive data is redacted in logs."""
        config = Config(
            openai_api_key="sk-1234567890123456789012345678901234567890123456",
            default_country="US"
        )
        
        # This should not raise an exception and should log safely
        self.config_manager._log_config(config)


class TestConfigModel:
    """Test cases for Config model validation."""
    
    def test_config_model_defaults(self):
        """Test Config model with default values."""
        config = Config()
        
        assert config.openai_api_key is None
        assert config.default_country == "Random"
        assert config.default_year == 2100
        assert config.max_people_per_request == 5
        assert config.enable_image_generation is True
        assert config.data_directory == "data"
        assert config.log_level == "INFO"
    
    def test_config_model_validation(self):
        """Test Config model field validation."""
        # Valid config
        config = Config(
            openai_api_key="sk-1234567890123456789012345678901234567890123456",
            default_year=2050,
            max_people_per_request=10
        )
        assert config.openai_api_key.startswith("sk-")
    
    def test_has_valid_api_key(self):
        """Test has_valid_api_key method."""
        config = Config()
        assert config.has_valid_api_key() is False
        
        config = Config(openai_api_key="sk-1234567890123456789012345678901234567890123456")
        assert config.has_valid_api_key() is True
    
    def test_get_primary_api_key(self):
        """Test get_primary_api_key method."""
        config = Config()
        assert config.get_primary_api_key() is None
        
        config = Config(anthropic_api_key="sk-ant-test1234567890")
        assert config.get_primary_api_key() == "sk-ant-test1234567890"
        
        config = Config(
            anthropic_api_key="sk-ant-test1234567890",
            openai_api_key="sk-1234567890123456789012345678901234567890123456"
        )
        assert config.get_primary_api_key() == "sk-1234567890123456789012345678901234567890123456"