"""Integration tests for configuration management system."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from trillions_of_people.core.config import ConfigManager
from trillions_of_people.core.exceptions import ConfigurationError


class TestConfigIntegration:
    """Integration tests for the complete configuration system."""
    
    def test_full_config_workflow(self):
        """Test complete configuration workflow with file, env, and CLI overrides."""
        # Create a temporary config file
        toml_content = '''
[trillions_of_people]
openai_api_key = "sk-file1234567890123456789012345678901234567890123456"
default_country = "Canada"
default_year = 2080
max_people_per_request = 7
enable_image_generation = false
log_level = "WARNING"
cache_ttl = 7200
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            try:
                # Test with file only
                config_manager = ConfigManager()
                config = config_manager.load_config(config_file=f.name)
                
                assert config.openai_api_key == "sk-file1234567890123456789012345678901234567890123456"
                assert config.default_country == "Canada"
                assert config.default_year == 2080
                assert config.max_people_per_request == 7
                assert config.enable_image_generation is False
                assert config.log_level == "WARNING"
                assert config.cache_ttl == 7200
                
                # Test with environment variables overriding file
                with patch.dict(os.environ, {
                    'TRILLIONS_OPENAI_API_KEY': 'sk-env1234567890123456789012345678901234567890123456',
                    'TRILLIONS_DEFAULT_COUNTRY': 'USA',
                    'TRILLIONS_ENABLE_IMAGE_GENERATION': 'true'
                }):
                    config = config_manager.load_config(config_file=f.name)
                    
                    # Env vars should override file
                    assert config.openai_api_key == "sk-env1234567890123456789012345678901234567890123456"
                    assert config.default_country == "USA"
                    assert config.enable_image_generation is True
                    
                    # File values should remain for non-overridden settings
                    assert config.default_year == 2080
                    assert config.max_people_per_request == 7
                    assert config.log_level == "WARNING"
                    
                    # Test with CLI overrides (highest precedence)
                    cli_overrides = {
                        'default_country': 'UK',
                        'max_people_per_request': 15,
                        'log_level': 'DEBUG'
                    }
                    
                    config = config_manager.load_config(
                        config_file=f.name,
                        cli_overrides=cli_overrides
                    )
                    
                    # CLI should override everything
                    assert config.default_country == "UK"
                    assert config.max_people_per_request == 15
                    assert config.log_level == "DEBUG"
                    
                    # Env should override file for non-CLI settings
                    assert config.openai_api_key == "sk-env1234567890123456789012345678901234567890123456"
                    assert config.enable_image_generation is True
                    
                    # File should provide defaults for non-overridden settings
                    assert config.default_year == 2080
                    assert config.cache_ttl == 7200
                    
            finally:
                os.unlink(f.name)
    
    def test_config_validation_integration(self):
        """Test that validation works across all configuration sources."""
        config_manager = ConfigManager()
        
        # Test that invalid values from any source are caught
        with patch.dict(os.environ, {
            'TRILLIONS_MAX_PEOPLE_PER_REQUEST': '2000'  # Too high
        }):
            with pytest.raises(ConfigurationError, match="Invalid value for TRILLIONS_MAX_PEOPLE_PER_REQUEST"):
                config_manager.load_config()
        
        # Test that invalid TOML values are caught
        invalid_toml = '''
[trillions_of_people]
default_year = 500000
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(invalid_toml)
            f.flush()
            
            try:
                with pytest.raises(ConfigurationError, match="Invalid value for default_year"):
                    config_manager.load_config(config_file=f.name)
            finally:
                os.unlink(f.name)
    
    def test_sample_config_creation(self):
        """Test sample configuration file creation and usage."""
        config_manager = ConfigManager()
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            try:
                # Create sample config
                config_manager.create_sample_config(f.name)
                
                # Verify file exists and has correct permissions
                assert Path(f.name).exists()
                stat = Path(f.name).stat()
                assert oct(stat.st_mode)[-3:] == '600'
                
                # Verify content
                content = Path(f.name).read_text()
                assert '[trillions_of_people]' in content
                assert 'openai_api_key' in content
                assert 'default_country' in content
                
                # Test that the sample config can be loaded (with commented keys)
                config = config_manager.load_config(config_file=f.name)
                assert config.default_country == "Random"
                assert config.default_year == 2100
                
            finally:
                os.unlink(f.name)
    
    def test_logging_setup_integration(self):
        """Test that logging setup works with configuration."""
        config_manager = ConfigManager()
        
        # Test with different log levels
        for log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            with patch.dict(os.environ, {'TRILLIONS_LOG_LEVEL': log_level}):
                config = config_manager.load_config()
                assert config.log_level == log_level
                
                # Should not raise exception
                config_manager.setup_logging(config)
    
    def test_api_key_security_integration(self):
        """Test API key security validation integration."""
        config_manager = ConfigManager()
        
        # Test security warnings for various key issues
        warnings = config_manager.validate_api_key_security("test", "openai")
        assert any("placeholder" in w for w in warnings)
        
        warnings = config_manager.validate_api_key_security("sk-short", "openai")
        assert any("too short" in w for w in warnings)
        
        warnings = config_manager.validate_api_key_security("invalid-format", "openai")
        assert any("format" in w for w in warnings)
        
        # Test that valid keys don't generate warnings
        warnings = config_manager.validate_api_key_security(
            "sk-1234567890123456789012345678901234567890123456", 
            "openai"
        )
        assert len(warnings) == 0
    
    def test_error_handling_integration(self):
        """Test comprehensive error handling across the system."""
        config_manager = ConfigManager()
        
        # Test file permission errors
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[trillions_of_people]\ndefault_country = "US"')
            f.flush()
            
            try:
                # Make file unreadable
                os.chmod(f.name, 0o000)
                
                with pytest.raises(ConfigurationError, match="Error reading configuration file"):
                    config_manager.load_config(config_file=f.name)
                    
            finally:
                # Restore permissions and clean up
                os.chmod(f.name, 0o600)
                os.unlink(f.name)
        
        # Test directory creation for sample config
        with tempfile.TemporaryDirectory() as temp_dir:
            sample_path = Path(temp_dir) / "subdir" / "config.toml"
            
            # This should fail because parent directory doesn't exist
            with pytest.raises(ConfigurationError, match="Failed to create sample config file"):
                config_manager.create_sample_config(str(sample_path))