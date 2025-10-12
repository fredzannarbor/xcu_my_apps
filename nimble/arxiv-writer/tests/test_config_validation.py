"""
Unit tests for configuration validation and error handling.
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from typing import Dict, Any

from src.arxiv_writer.config.loader import ConfigLoader
from src.arxiv_writer.core.exceptions import ConfigurationError
from src.arxiv_writer.core.models import PaperConfig


class TestConfigLoader:
    """Test cases for configuration loading functionality."""
    
    def test_load_default_config(self):
        """Test loading default configuration."""
        config = ConfigLoader.load_default()
        
        assert isinstance(config, PaperConfig)
        # Default config should have basic required fields
        assert hasattr(config, 'output_directory')
        assert hasattr(config, 'llm_config')
    
    def test_load_from_dict_valid(self):
        """Test loading configuration from valid dictionary."""
        config_data = {
            "output_directory": "/tmp/test",
            "llm_config": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.7
            },
            "template_config": {
                "template_file": "default.json"
            }
        }
        
        config = ConfigLoader.load_from_dict(config_data)
        
        assert isinstance(config, PaperConfig)
        assert config.output_directory == "/tmp/test"
    
    def test_load_from_dict_invalid(self):
        """Test loading configuration from invalid dictionary."""
        invalid_data = {
            "invalid_field": "value",
            "llm_config": "not_a_dict"  # Should be dict
        }
        
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load_from_dict(invalid_data)
        
        assert "Failed to load configuration from dict" in str(exc_info.value)
    
    def test_load_from_dict_empty(self):
        """Test loading configuration from empty dictionary."""
        config = ConfigLoader.load_from_dict({})
        
        assert isinstance(config, PaperConfig)
        # Should use defaults for missing fields
    
    def test_load_from_file_valid_json(self):
        """Test loading configuration from valid JSON file."""
        config_data = {
            "output_directory": "/tmp/test",
            "llm_config": {
                "provider": "openai",
                "model": "gpt-4"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            with patch.object(PaperConfig, 'from_file') as mock_from_file:
                mock_from_file.return_value = PaperConfig()
                config = ConfigLoader.load_from_file(temp_path)
                
                assert isinstance(config, PaperConfig)
                mock_from_file.assert_called_once_with(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_from_file_nonexistent(self):
        """Test loading configuration from non-existent file."""
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load_from_file("/nonexistent/path/config.json")
        
        assert "Failed to load configuration from" in str(exc_info.value)
    
    def test_load_from_file_invalid_json(self):
        """Test loading configuration from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json content")
            temp_path = f.name
        
        try:
            with patch.object(PaperConfig, 'from_file') as mock_from_file:
                mock_from_file.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
                
                with pytest.raises(ConfigurationError) as exc_info:
                    ConfigLoader.load_from_file(temp_path)
                
                assert "Failed to load configuration from" in str(exc_info.value)
        finally:
            os.unlink(temp_path)
    
    def test_resolve_environment_variables_simple(self):
        """Test resolving simple environment variables."""
        os.environ['TEST_VAR'] = 'test_value'
        
        config_dict = {
            "api_key": "${TEST_VAR}",
            "model": "gpt-4"
        }
        
        try:
            resolved = ConfigLoader.resolve_environment_variables(config_dict)
            
            assert resolved["api_key"] == "test_value"
            assert resolved["model"] == "gpt-4"
        finally:
            del os.environ['TEST_VAR']
    
    def test_resolve_environment_variables_nested(self):
        """Test resolving environment variables in nested structures."""
        os.environ['API_KEY'] = 'secret_key'
        os.environ['MODEL_NAME'] = 'gpt-4'
        
        config_dict = {
            "llm_config": {
                "api_key": "${API_KEY}",
                "model": "${MODEL_NAME}",
                "temperature": 0.7
            },
            "output_dir": "/tmp/output"
        }
        
        try:
            resolved = ConfigLoader.resolve_environment_variables(config_dict)
            
            assert resolved["llm_config"]["api_key"] == "secret_key"
            assert resolved["llm_config"]["model"] == "gpt-4"
            assert resolved["llm_config"]["temperature"] == 0.7
            assert resolved["output_dir"] == "/tmp/output"
        finally:
            del os.environ['API_KEY']
            del os.environ['MODEL_NAME']
    
    def test_resolve_environment_variables_list(self):
        """Test resolving environment variables in lists."""
        os.environ['MODEL1'] = 'gpt-4'
        os.environ['MODEL2'] = 'gpt-3.5-turbo'
        
        config_dict = {
            "models": ["${MODEL1}", "${MODEL2}", "claude-3-opus"]
        }
        
        try:
            resolved = ConfigLoader.resolve_environment_variables(config_dict)
            
            assert resolved["models"] == ["gpt-4", "gpt-3.5-turbo", "claude-3-opus"]
        finally:
            del os.environ['MODEL1']
            del os.environ['MODEL2']
    
    def test_resolve_environment_variables_missing(self):
        """Test resolving missing environment variables."""
        config_dict = {
            "api_key": "${MISSING_VAR}",
            "model": "gpt-4"
        }
        
        resolved = ConfigLoader.resolve_environment_variables(config_dict)
        
        # Missing variables should remain as-is
        assert resolved["api_key"] == "${MISSING_VAR}"
        assert resolved["model"] == "gpt-4"
    
    def test_resolve_environment_variables_non_env_strings(self):
        """Test that non-environment variable strings are unchanged."""
        config_dict = {
            "normal_string": "just a string",
            "partial_env": "prefix_${VAR}_suffix",
            "not_env": "$VAR",
            "also_not_env": "${VAR"
        }
        
        resolved = ConfigLoader.resolve_environment_variables(config_dict)
        
        assert resolved["normal_string"] == "just a string"
        assert resolved["partial_env"] == "prefix_${VAR}_suffix"
        assert resolved["not_env"] == "$VAR"
        assert resolved["also_not_env"] == "${VAR"
    
    def test_resolve_environment_variables_complex_structure(self):
        """Test resolving environment variables in complex nested structures."""
        os.environ['DB_HOST'] = 'localhost'
        os.environ['DB_PORT'] = '5432'
        os.environ['API_KEY'] = 'secret'
        
        config_dict = {
            "database": {
                "host": "${DB_HOST}",
                "port": "${DB_PORT}",
                "credentials": {
                    "username": "admin",
                    "password": "${API_KEY}"
                }
            },
            "services": [
                {
                    "name": "llm_service",
                    "config": {
                        "api_key": "${API_KEY}",
                        "endpoints": ["${DB_HOST}:8080", "backup.example.com"]
                    }
                }
            ]
        }
        
        try:
            resolved = ConfigLoader.resolve_environment_variables(config_dict)
            
            assert resolved["database"]["host"] == "localhost"
            assert resolved["database"]["port"] == "5432"
            assert resolved["database"]["credentials"]["password"] == "secret"
            assert resolved["services"][0]["config"]["api_key"] == "secret"
            assert resolved["services"][0]["config"]["endpoints"][0] == "localhost:8080"
            assert resolved["services"][0]["config"]["endpoints"][1] == "backup.example.com"
        finally:
            del os.environ['DB_HOST']
            del os.environ['DB_PORT']
            del os.environ['API_KEY']


class TestConfigurationErrorHandling:
    """Test cases for configuration error handling."""
    
    def test_configuration_error_creation(self):
        """Test creating ConfigurationError."""
        error = ConfigurationError("Test error message")
        
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_configuration_error_with_cause(self):
        """Test ConfigurationError with underlying cause."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            config_error = ConfigurationError("Configuration failed") from e
            
            assert str(config_error) == "Configuration failed"
            assert isinstance(config_error.__cause__, ValueError)
    
    def test_configuration_error_inheritance(self):
        """Test that ConfigurationError inherits properly."""
        error = ConfigurationError("Test")
        
        assert isinstance(error, Exception)
        assert isinstance(error, ConfigurationError)
    
    def test_load_from_file_error_propagation(self):
        """Test that file loading errors are properly wrapped."""
        with patch.object(PaperConfig, 'from_file') as mock_from_file:
            mock_from_file.side_effect = ValueError("Invalid config format")
            
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigLoader.load_from_file("test.json")
            
            assert "Failed to load configuration from test.json" in str(exc_info.value)
            assert isinstance(exc_info.value.__cause__, ValueError)
    
    def test_load_from_dict_error_propagation(self):
        """Test that dict loading errors are properly wrapped."""
        with patch.object(PaperConfig, 'from_dict') as mock_from_dict:
            mock_from_dict.side_effect = TypeError("Invalid type")
            
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigLoader.load_from_dict({"test": "data"})
            
            assert "Failed to load configuration from dict" in str(exc_info.value)
            assert isinstance(exc_info.value.__cause__, TypeError)


class TestConfigLoaderIntegration:
    """Integration tests for configuration loading."""
    
    def test_full_config_loading_workflow(self):
        """Test complete configuration loading workflow."""
        # Set up environment variables
        os.environ['OUTPUT_DIR'] = '/tmp/arxiv_output'
        os.environ['API_KEY'] = 'test_api_key'
        
        config_data = {
            "output_directory": "${OUTPUT_DIR}",
            "llm_config": {
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "${API_KEY}",
                "temperature": 0.7
            },
            "template_config": {
                "template_file": "default.json",
                "custom_templates": {}
            }
        }
        
        try:
            # Resolve environment variables
            resolved_data = ConfigLoader.resolve_environment_variables(config_data)
            
            # Verify environment variables were resolved
            assert resolved_data["output_directory"] == "/tmp/arxiv_output"
            assert resolved_data["llm_config"]["api_key"] == "test_api_key"
            
            # Load configuration from resolved data
            with patch.object(PaperConfig, 'from_dict') as mock_from_dict:
                mock_config = PaperConfig()
                mock_from_dict.return_value = mock_config
                
                config = ConfigLoader.load_from_dict(resolved_data)
                
                assert config == mock_config
                mock_from_dict.assert_called_once_with(resolved_data)
        finally:
            del os.environ['OUTPUT_DIR']
            del os.environ['API_KEY']
    
    def test_config_file_with_environment_variables(self):
        """Test loading config file that contains environment variables."""
        os.environ['TEST_MODEL'] = 'gpt-4'
        
        config_content = {
            "llm_config": {
                "model": "${TEST_MODEL}",
                "temperature": 0.5
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_content, f)
            temp_path = f.name
        
        try:
            with patch.object(PaperConfig, 'from_file') as mock_from_file:
                # Simulate PaperConfig.from_file resolving env vars
                def mock_from_file_impl(path):
                    with open(path, 'r') as file:
                        data = json.load(file)
                    resolved_data = ConfigLoader.resolve_environment_variables(data)
                    mock_config = PaperConfig()
                    mock_config._resolved_data = resolved_data
                    return mock_config
                
                mock_from_file.side_effect = mock_from_file_impl
                
                config = ConfigLoader.load_from_file(temp_path)
                
                assert hasattr(config, '_resolved_data')
                assert config._resolved_data["llm_config"]["model"] == "gpt-4"
        finally:
            os.unlink(temp_path)
            del os.environ['TEST_MODEL']
    
    def test_error_handling_chain(self):
        """Test error handling through the entire loading chain."""
        # Test file not found
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load_from_file("/nonexistent/config.json")
        assert "Failed to load configuration" in str(exc_info.value)
        
        # Test invalid data structure
        with pytest.raises(ConfigurationError) as exc_info:
            with patch.object(PaperConfig, 'from_dict') as mock_from_dict:
                mock_from_dict.side_effect = ValueError("Invalid structure")
                ConfigLoader.load_from_dict({"invalid": "data"})
        assert "Failed to load configuration from dict" in str(exc_info.value)
    
    def test_config_validation_edge_cases(self):
        """Test configuration validation with edge cases."""
        edge_cases = [
            {},  # Empty config
            {"output_directory": ""},  # Empty string
            {"llm_config": None},  # None value
            {"template_config": []},  # Wrong type
        ]
        
        for case in edge_cases:
            # Should either succeed with defaults or raise ConfigurationError
            try:
                config = ConfigLoader.load_from_dict(case)
                assert isinstance(config, PaperConfig)
            except ConfigurationError:
                # Expected for invalid configurations
                pass