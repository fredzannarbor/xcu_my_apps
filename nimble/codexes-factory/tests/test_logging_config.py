"""
Tests for the LoggingConfigManager class.

This module tests the centralized logging configuration management,
including LiteLLM filter application and environment-specific settings.
"""

import logging
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.logging_config import (
    LoggingConfigManager,
    get_logging_manager,
    setup_application_logging
)
from codexes.core.logging_filters import LiteLLMFilter


class TestLoggingConfigManager:
    """Test cases for LoggingConfigManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = LoggingConfigManager()
        # Reset any existing configuration
        self.manager.reset_configuration()
    
    def teardown_method(self):
        """Clean up after tests."""
        # Reset logging configuration
        self.manager.reset_configuration()
    
    def test_initialization(self):
        """Test LoggingConfigManager initialization."""
        manager = LoggingConfigManager()
        assert isinstance(manager.litellm_filter, LiteLLMFilter)
        assert not manager.is_configured()
    
    def test_setup_logging_default(self):
        """Test setting up logging with default configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory to avoid creating logs in project
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                self.manager.setup_logging()
                
                assert self.manager.is_configured()
                
                # Check that loggers exist and have correct levels
                codexes_logger = logging.getLogger('codexes')
                assert codexes_logger.level <= logging.INFO
                
                litellm_logger = logging.getLogger('litellm')
                assert litellm_logger.level >= logging.WARNING
                
                # Check that logs directory was created
                assert Path('logs').exists()
                
            finally:
                os.chdir(original_cwd)
    
    def test_setup_logging_custom_config(self):
        """Test setting up logging with custom configuration."""
        custom_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'simple': {
                    'format': '%(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'DEBUG',
                    'formatter': 'simple'
                }
            },
            'loggers': {
                'test': {
                    'level': 'DEBUG',
                    'handlers': ['console'],
                    'propagate': False
                }
            }
        }
        
        self.manager.setup_logging(custom_config)
        
        assert self.manager.is_configured()
        
        # Check that custom logger was configured
        test_logger = logging.getLogger('test')
        assert test_logger.level == logging.DEBUG
    
    def test_apply_litellm_filter(self):
        """Test that LiteLLM filter is applied to appropriate loggers."""
        self.manager.apply_litellm_filter()
        
        # Check that filters were added to relevant loggers
        litellm_logger = logging.getLogger('litellm')
        openai_logger = logging.getLogger('openai')
        httpx_logger = logging.getLogger('httpx')
        
        assert any(isinstance(f, LiteLLMFilter) for f in litellm_logger.filters)
        assert any(isinstance(f, LiteLLMFilter) for f in openai_logger.filters)
        assert any(isinstance(f, LiteLLMFilter) for f in httpx_logger.filters)
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'production'})
    def test_get_environment_config_production(self):
        """Test production environment configuration."""
        config = self.manager.get_environment_config('production')
        
        assert config['handlers']['console']['level'] == 'WARNING'
        assert config['loggers']['']['level'] == 'INFO'
        assert config['loggers']['codexes']['level'] == 'INFO'
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'testing'})
    def test_get_environment_config_testing(self):
        """Test testing environment configuration."""
        config = self.manager.get_environment_config('testing')
        
        assert config['handlers']['console']['level'] == 'ERROR'
        assert 'test.log' in config['handlers']['file']['filename']
        assert 'test_errors.log' in config['handlers']['error_file']['filename']
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'development'})
    def test_get_environment_config_development(self):
        """Test development environment configuration."""
        config = self.manager.get_environment_config('development')
        
        assert config['handlers']['console']['level'] == 'DEBUG'
        assert config['loggers']['']['level'] == 'DEBUG'
        assert config['loggers']['codexes']['level'] == 'DEBUG'
    
    @patch.dict(os.environ, {'DEBUG': 'true'})
    def test_debug_mode_environment_variable(self):
        """Test that DEBUG environment variable affects configuration."""
        config = self.manager._get_default_config()
        
        # In debug mode, log level should be DEBUG
        assert config['handlers']['console']['level'] == 'DEBUG'
        assert config['loggers']['litellm']['level'] == 'DEBUG'
    
    def test_enable_debug_mode(self):
        """Test enabling debug mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Set up logging first
                self.manager.setup_logging()
                
                # Enable debug mode
                self.manager.enable_debug_mode()
                
                # Check that debug mode is enabled on filter
                assert self.manager.litellm_filter.debug_mode
                
                # Check that logger levels were updated
                assert logging.getLogger('litellm').level == logging.DEBUG
                assert logging.getLogger('codexes').level == logging.DEBUG
                
            finally:
                os.chdir(original_cwd)
    
    def test_disable_debug_mode(self):
        """Test disabling debug mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Set up logging and enable debug mode first
                self.manager.setup_logging()
                self.manager.enable_debug_mode()
                
                # Disable debug mode
                self.manager.disable_debug_mode()
                
                # Check that debug mode is disabled on filter
                assert not self.manager.litellm_filter.debug_mode
                
                # Check that logger levels were updated
                assert logging.getLogger('litellm').level == logging.WARNING
                assert logging.getLogger('codexes').level == logging.INFO
                
            finally:
                os.chdir(original_cwd)
    
    def test_reset_configuration(self):
        """Test resetting logging configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Set up logging first
                self.manager.setup_logging()
                assert self.manager.is_configured()
                
                # Reset configuration
                self.manager.reset_configuration()
                assert not self.manager.is_configured()
                
                # Check that handlers were cleared
                root_logger = logging.getLogger()
                assert len(root_logger.handlers) == 0
                
            finally:
                os.chdir(original_cwd)
    
    def test_is_configured(self):
        """Test configuration status tracking."""
        assert not self.manager.is_configured()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                self.manager.setup_logging()
                assert self.manager.is_configured()
                
            finally:
                os.chdir(original_cwd)


class TestGlobalFunctions:
    """Test cases for global logging functions."""
    
    def test_get_logging_manager_singleton(self):
        """Test that get_logging_manager returns the same instance."""
        manager1 = get_logging_manager()
        manager2 = get_logging_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, LoggingConfigManager)
    
    def test_setup_application_logging(self):
        """Test the convenience function for setting up application logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                setup_application_logging()
                
                # Check that logging was configured
                manager = get_logging_manager()
                assert manager.is_configured()
                
                # Check that logs directory exists
                assert Path('logs').exists()
                
            finally:
                os.chdir(original_cwd)
    
    def test_setup_application_logging_with_config(self):
        """Test setup_application_logging with custom config."""
        # Reset global manager to avoid interference from other tests
        import codexes.core.logging_config as logging_config_module
        logging_config_module._logging_manager = None
        
        custom_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO'
                }
            },
            'loggers': {
                'test': {
                    'level': 'INFO',
                    'handlers': ['console']
                }
            }
        }
        
        setup_application_logging(custom_config)
        
        manager = get_logging_manager()
        assert manager.is_configured()
        
        # Check that custom logger was configured
        test_logger = logging.getLogger('test')
        assert test_logger.level == logging.INFO


class TestEnvironmentIntegration:
    """Test cases for environment variable integration."""
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'production', 'DEBUG': 'false'})
    def test_production_environment_setup(self):
        """Test logging setup in production environment."""
        manager = LoggingConfigManager()
        config = manager._get_default_config()
        
        # Production should have less verbose console logging
        assert config['handlers']['console']['level'] == 'INFO'
        assert config['loggers']['litellm']['level'] == 'WARNING'
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'development', 'DEBUG': 'true'})
    def test_development_environment_setup(self):
        """Test logging setup in development environment."""
        manager = LoggingConfigManager()
        config = manager._get_default_config()
        
        # Development with debug should be very verbose
        assert config['handlers']['console']['level'] == 'DEBUG'
        assert config['loggers']['litellm']['level'] == 'DEBUG'
    
    @patch.dict(os.environ, {}, clear=True)
    def test_default_environment_setup(self):
        """Test logging setup with no environment variables."""
        manager = LoggingConfigManager()
        config = manager._get_default_config()
        
        # Should default to INFO level
        assert config['handlers']['console']['level'] == 'INFO'
        assert config['loggers']['litellm']['level'] == 'WARNING'