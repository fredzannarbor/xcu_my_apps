"""
Logging configuration manager for centralized logging setup and configuration.

This module provides the LoggingConfigManager class that handles:
- Centralized logging setup and configuration
- Application of LiteLLM filters to appropriate loggers
- Environment-specific logging settings
- Consistent logging format across the application
- Configuration file-based settings management
"""

import logging
import logging.config
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

from .logging_filters import LiteLLMFilter, SuccessMessageFilter


class LoggingConfigManager:
    """Manages logging configuration and setup for the application."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the logging configuration manager.
        
        Args:
            config_file: Path to the logging configuration file.
                        If None, uses default path 'configs/logging_config.json'.
        """
        self.config_file = config_file or 'configs/logging_config.json'
        self.litellm_filter = LiteLLMFilter()
        self.success_filter = SuccessMessageFilter()
        self._configured = False
        self._config_data = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from the configuration file."""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config_data = json.load(f)
            else:
                # Use default configuration if file doesn't exist
                self._config_data = self._get_default_config_data()
        except Exception as e:
            # Fall back to default configuration if loading fails
            self._config_data = self._get_default_config_data()
            print(f"Warning: Failed to load logging config from {self.config_file}: {e}")
            print("Using default logging configuration")
    
    def _get_default_config_data(self) -> Dict[str, Any]:
        """Get default configuration data structure."""
        return {
            "settings": {
                "litellm_filtering": {
                    "enabled": True,
                    "debug_mode_override": False
                },
                "statistics_reporting": {
                    "enabled": True,
                    "detail_level": "standard",
                    "include_model_breakdown": True,
                    "include_prompt_breakdown": True,
                    "include_cost_analysis": True
                },
                "log_levels": {
                    "application": "INFO",
                    "litellm": "WARNING",
                    "openai": "WARNING",
                    "httpx": "WARNING"
                },
                "output_formats": {
                    "console_format": "standard",
                    "file_format": "detailed",
                    "timestamp_format": "%Y-%m-%d %H:%M:%S"
                },
                "handlers": {
                    "console_enabled": True,
                    "file_enabled": True,
                    "error_file_enabled": True,
                    "console_level": "INFO",
                    "file_level": "DEBUG",
                    "error_file_level": "ERROR"
                },
                "files": {
                    "application_log": "logs/application.log",
                    "error_log": "logs/errors.log",
                    "statistics_log": "logs/statistics.log",
                    "encoding": "utf-8"
                }
            },
            "format_templates": {
                "simple": "%(levelname)s - %(message)s",
                "standard": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
            }
        }
    
    def setup_logging(self, config: Optional[Dict[str, Any]] = None, environment: Optional[str] = None) -> None:
        """
        Set up logging configuration with optional custom config.
        
        Args:
            config: Optional custom logging configuration dictionary.
                   If None, uses configuration from config file.
            environment: Optional environment name for environment-specific overrides.
        """
        if config is None:
            config = self._build_logging_config(environment)
        
        # Apply the configuration
        logging.config.dictConfig(config)
        
        # Apply LiteLLM filter to appropriate loggers if enabled
        if self._is_litellm_filtering_enabled():
            self.apply_litellm_filter()
        
        # Configure formatters if needed
        self.configure_formatters()
        
        self._configured = True
        
        # Log that configuration is complete (only if we have a logger configured)
        try:
            logger = logging.getLogger(__name__)
            logger.info("Logging configuration applied successfully")
        except Exception:
            # If logging fails, just continue - configuration was still applied
            pass
    
    def _is_litellm_filtering_enabled(self) -> bool:
        """Check if LiteLLM filtering is enabled in configuration."""
        return self._config_data.get("settings", {}).get("litellm_filtering", {}).get("enabled", True)
    
    def _get_environment_overrides(self, environment: Optional[str]) -> Dict[str, Any]:
        """Get environment-specific configuration overrides."""
        if not environment:
            environment = os.getenv('ENVIRONMENT', 'development').lower()
        
        overrides = self._config_data.get("settings", {}).get("environment_overrides", {})
        return overrides.get(environment, {})
    
    def _build_logging_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Build the logging configuration dictionary from config data."""
        settings = self._config_data.get("settings", {})
        format_templates = self._config_data.get("format_templates", {})
        
        # Apply environment overrides
        env_overrides = self._get_environment_overrides(environment)
        if env_overrides:
            settings = self._merge_config(settings, env_overrides)
        
        # Determine environment and debug mode
        environment = environment or os.getenv('ENVIRONMENT', 'development').lower()
        debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # Override debug mode if specified in config
        if settings.get("litellm_filtering", {}).get("debug_mode_override"):
            debug_mode = True
        
        # Get log levels
        log_levels = settings.get("log_levels", {})
        handlers_config = settings.get("handlers", {})
        files_config = settings.get("files", {})
        output_formats = settings.get("output_formats", {})
        
        # Ensure logs directory exists
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        # Build formatters
        formatters = {}
        for name, template in format_templates.items():
            if isinstance(template, dict):
                formatters[name] = template
            else:
                formatters[name] = {
                    'format': template,
                    'datefmt': output_formats.get('timestamp_format', '%Y-%m-%d %H:%M:%S')
                }
        
        # Build handlers
        handlers = {}
        
        if handlers_config.get("console_enabled", True):
            handlers['console'] = {
                'class': 'codexes.core.logging_filters.SuccessAwareHandler',
                'level': handlers_config.get("console_level", "INFO"),
                'formatter': output_formats.get("console_format", "standard"),
                'stream': 'ext://sys.stdout'
            }
        
        if handlers_config.get("file_enabled", True):
            handlers['file'] = {
                'class': 'logging.FileHandler',
                'level': handlers_config.get("file_level", "DEBUG"),
                'formatter': output_formats.get("file_format", "detailed"),
                'filename': files_config.get("application_log", "logs/application.log"),
                'mode': 'a',
                'encoding': files_config.get("encoding", "utf-8")
            }
        
        if handlers_config.get("error_file_enabled", True):
            handlers['error_file'] = {
                'class': 'logging.FileHandler',
                'level': handlers_config.get("error_file_level", "ERROR"),
                'formatter': output_formats.get("file_format", "detailed"),
                'filename': files_config.get("error_log", "logs/errors.log"),
                'mode': 'a',
                'encoding': files_config.get("encoding", "utf-8")
            }
        
        # Build loggers configuration
        loggers = {
            # Application loggers
            'codexes': {
                'level': log_levels.get("application", "INFO"),
                'handlers': list(handlers.keys()),
                'propagate': False
            },
            # LiteLLM logger - set to INFO so our filter can work
            'litellm': {
                'level': 'INFO',  # Always INFO so filter can process messages
                'handlers': list(handlers.keys()),  # Use all handlers so important messages appear
                'propagate': False
            },
            # OpenAI logger
            'openai': {
                'level': log_levels.get("openai", "WARNING") if not debug_mode else 'DEBUG',
                'handlers': ['file'] if 'file' in handlers else [],
                'propagate': False
            },
            # HTTP client logger
            'httpx': {
                'level': log_levels.get("httpx", "WARNING") if not debug_mode else 'DEBUG',
                'handlers': ['file'] if 'file' in handlers else [],
                'propagate': False
            },
            # Root logger
            '': {
                'level': log_levels.get("application", "INFO"),
                'handlers': list(handlers.keys())
            }
        }
        
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': formatters,
            'handlers': handlers,
            'loggers': loggers
        }
    
    def _merge_config(self, base_config: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration overrides into base configuration."""
        result = base_config.copy()
        
        for key, value in overrides.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def apply_litellm_filter(self) -> None:
        """Apply LiteLLM filter to appropriate loggers and success filter to all loggers."""
        # Update filter settings from config
        litellm_config = self._config_data.get("settings", {}).get("litellm_filtering", {})
        self.litellm_filter.debug_mode = litellm_config.get("debug_mode_override", False)
        
        # Apply success filter to root logger to ensure ✅ messages always appear
        root_logger = logging.getLogger()
        root_logger.addFilter(self.success_filter)
        
        # Apply success filter to application logger
        app_logger = logging.getLogger('codexes')
        app_logger.addFilter(self.success_filter)
        
        # Apply filter to all LiteLLM logger variations
        litellm_logger_names = [
            'litellm',
            'LiteLLM',
            'LiteLLM Proxy', 
            'LiteLLM Router'
        ]
        
        for logger_name in litellm_logger_names:
            logger_obj = logging.getLogger(logger_name)
            
            # Remove any existing handlers that LiteLLM might have added
            logger_obj.handlers.clear()
            
            # Add our filters
            logger_obj.addFilter(self.litellm_filter)
            logger_obj.addFilter(self.success_filter)
            
            # Set appropriate level
            logger_obj.setLevel(logging.INFO)
            
            # Add our controlled handlers
            for handler in root_logger.handlers:
                logger_obj.addHandler(handler)
            
            # Ensure propagation is disabled to prevent duplicate messages
            logger_obj.propagate = False
        
        # Also apply to any other verbose loggers that might be related
        openai_logger = logging.getLogger('openai')
        openai_logger.addFilter(self.litellm_filter)
        openai_logger.addFilter(self.success_filter)
        
        # Apply to httpx logger which LiteLLM uses for HTTP requests
        httpx_logger = logging.getLogger('httpx')
        httpx_logger.addFilter(self.litellm_filter)
        httpx_logger.addFilter(self.success_filter)
        
        logger = logging.getLogger(__name__)
        logger.debug("LiteLLM filters and success filters applied to all relevant loggers")
    
    def configure_formatters(self) -> None:
        """Configure custom formatters for enhanced readability."""
        # This method can be extended to add custom formatters
        # For now, the formatters are configured in the dict config
        pass
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get the default logging configuration.
        
        Returns:
            Default logging configuration dictionary.
        """
        # Determine environment
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # Set log level based on environment
        if debug_mode:
            log_level = 'DEBUG'
        elif environment == 'production':
            log_level = 'INFO'
        else:
            log_level = 'INFO'
        
        # Ensure logs directory exists
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'detailed': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'simple': {
                    'format': '%(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'codexes.core.logging_filters.SuccessAwareHandler',
                    'level': log_level,
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'level': 'DEBUG',
                    'formatter': 'detailed',
                    'filename': 'logs/application.log',
                    'mode': 'a',
                    'encoding': 'utf-8'
                },
                'error_file': {
                    'class': 'logging.FileHandler',
                    'level': 'ERROR',
                    'formatter': 'detailed',
                    'filename': 'logs/errors.log',
                    'mode': 'a',
                    'encoding': 'utf-8'
                }
            },
            'loggers': {
                # Application loggers
                'codexes': {
                    'level': log_level,
                    'handlers': ['console', 'file'],
                    'propagate': False
                },
                # LiteLLM logger - set to INFO so our filter can work
                'litellm': {
                    'level': 'INFO',  # Always INFO so filter can process messages
                    'handlers': ['console', 'file', 'error_file'],  # Use all handlers so important messages appear
                    'propagate': False
                },
                # OpenAI logger
                'openai': {
                    'level': 'WARNING' if not debug_mode else 'DEBUG',
                    'handlers': ['file'],
                    'propagate': False
                },
                # HTTP client logger
                'httpx': {
                    'level': 'WARNING' if not debug_mode else 'DEBUG',
                    'handlers': ['file'],
                    'propagate': False
                },
                # Root logger
                '': {
                    'level': log_level,
                    'handlers': ['console', 'file', 'error_file']
                }
            }
        }
        
        return config
    
    def get_environment_config(self, environment: str) -> Dict[str, Any]:
        """
        Get environment-specific logging configuration.
        
        Args:
            environment: Environment name ('development', 'production', 'testing')
            
        Returns:
            Environment-specific logging configuration.
        """
        base_config = self._get_default_config()
        
        if environment.lower() == 'production':
            # Production: Less verbose, focus on errors and important info
            base_config['handlers']['console']['level'] = 'WARNING'
            base_config['loggers']['']['level'] = 'INFO'
            base_config['loggers']['codexes']['level'] = 'INFO'
            
        elif environment.lower() == 'testing':
            # Testing: Minimal console output, detailed file logging
            base_config['handlers']['console']['level'] = 'ERROR'
            base_config['handlers']['file']['filename'] = 'logs/test.log'
            base_config['handlers']['error_file']['filename'] = 'logs/test_errors.log'
            
        elif environment.lower() == 'development':
            # Development: More verbose for debugging
            base_config['handlers']['console']['level'] = 'DEBUG'
            base_config['loggers']['']['level'] = 'DEBUG'
            base_config['loggers']['codexes']['level'] = 'DEBUG'
        
        return base_config
    
    def is_configured(self) -> bool:
        """
        Check if logging has been configured.
        
        Returns:
            True if logging has been configured, False otherwise.
        """
        return self._configured
    
    def reset_configuration(self) -> None:
        """Reset logging configuration to allow reconfiguration."""
        # Remove all handlers from all loggers
        for logger_name in logging.Logger.manager.loggerDict:
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
            logger.filters.clear()
        
        # Clear root logger handlers and filters
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.filters.clear()
        
        self._configured = False
    
    def enable_debug_mode(self) -> None:
        """Enable debug mode for more verbose logging."""
        # Update LiteLLM filter to allow debug messages
        self.litellm_filter.debug_mode = True
        
        # Update logger levels
        logging.getLogger('litellm').setLevel(logging.DEBUG)
        logging.getLogger('openai').setLevel(logging.DEBUG)
        logging.getLogger('httpx').setLevel(logging.DEBUG)
        logging.getLogger('codexes').setLevel(logging.DEBUG)
        
        logger = logging.getLogger(__name__)
        logger.info("Debug mode enabled - verbose logging activated")
    
    def disable_debug_mode(self) -> None:
        """Disable debug mode to reduce logging verbosity."""
        # Update LiteLLM filter to suppress debug messages
        self.litellm_filter.debug_mode = False
        
        # Update logger levels
        logging.getLogger('litellm').setLevel(logging.WARNING)
        logging.getLogger('openai').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('codexes').setLevel(logging.INFO)
        
        logger = logging.getLogger(__name__)
        logger.info("Debug mode disabled - reduced logging verbosity")
    
    def get_statistics_config(self) -> Dict[str, Any]:
        """
        Get statistics reporting configuration.
        
        Returns:
            Dictionary containing statistics reporting configuration.
        """
        stats_config = self._config_data.get("settings", {}).get("statistics_reporting", {})
        detail_levels = self._config_data.get("detail_levels", {})
        
        # Get the detail level configuration
        detail_level = stats_config.get("detail_level", "standard")
        detail_config = detail_levels.get(detail_level, {})
        
        # Merge base config with detail level config
        result = {
            "enabled": stats_config.get("enabled", True),
            "detail_level": detail_level,
            "include_model_breakdown": detail_config.get("include_model_breakdown", 
                                                       stats_config.get("include_model_breakdown", True)),
            "include_prompt_breakdown": detail_config.get("include_prompt_breakdown", 
                                                        stats_config.get("include_prompt_breakdown", True)),
            "include_cost_analysis": detail_config.get("include_cost_analysis", 
                                                     stats_config.get("include_cost_analysis", True)),
            "include_timing_analysis": detail_config.get("include_timing_analysis", False),
            "include_performance_metrics": detail_config.get("include_performance_metrics", False)
        }
        
        return result
    
    def get_litellm_filter_config(self) -> Dict[str, Any]:
        """
        Get LiteLLM filter configuration.
        
        Returns:
            Dictionary containing LiteLLM filter configuration.
        """
        return self._config_data.get("settings", {}).get("litellm_filtering", {
            "enabled": True,
            "debug_mode_override": False
        })
    
    def get_log_file_paths(self) -> Dict[str, str]:
        """
        Get configured log file paths.
        
        Returns:
            Dictionary containing log file paths.
        """
        files_config = self._config_data.get("settings", {}).get("files", {})
        return {
            "application_log": files_config.get("application_log", "logs/application.log"),
            "error_log": files_config.get("error_log", "logs/errors.log"),
            "statistics_log": files_config.get("statistics_log", "logs/statistics.log")
        }
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration settings dynamically.
        
        Args:
            updates: Dictionary of configuration updates to apply.
        """
        if not self._config_data:
            self._config_data = self._get_default_config_data()
        
        self._config_data = self._merge_config(self._config_data, updates)
        
        # If logging is already configured, reconfigure with new settings
        if self._configured:
            self.reset_configuration()
            self.setup_logging()
    
    def save_config(self, file_path: Optional[str] = None) -> None:
        """
        Save current configuration to file.
        
        Args:
            file_path: Optional path to save configuration to.
                      If None, uses the original config file path.
        """
        save_path = file_path or self.config_file
        
        try:
            config_path = Path(save_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)
                
            logger = logging.getLogger(__name__)
            logger.info(f"Logging configuration saved to {save_path}")
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to save logging configuration to {save_path}: {e}")
            raise


# Global instance for easy access
_logging_manager = None


def get_logging_manager(config_file: Optional[str] = None) -> LoggingConfigManager:
    """
    Get the global logging configuration manager instance.
    
    Args:
        config_file: Optional path to configuration file.
    
    Returns:
        Global LoggingConfigManager instance.
    """
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingConfigManager(config_file)
    return _logging_manager


def setup_application_logging(config: Optional[Dict[str, Any]] = None, 
                            environment: Optional[str] = None,
                            config_file: Optional[str] = None) -> None:
    """
    Convenience function to set up application logging.
    
    Args:
        config: Optional custom logging configuration.
        environment: Optional environment name for environment-specific settings.
        config_file: Optional path to configuration file.
    """
    manager = get_logging_manager(config_file)
    manager.setup_logging(config, environment)


def get_statistics_config() -> Dict[str, Any]:
    """
    Get statistics reporting configuration from the global manager.
    
    Returns:
        Statistics reporting configuration dictionary.
    """
    manager = get_logging_manager()
    return manager.get_statistics_config()


def get_litellm_filter_config() -> Dict[str, Any]:
    """
    Get LiteLLM filter configuration from the global manager.
    
    Returns:
        LiteLLM filter configuration dictionary.
    """
    manager = get_logging_manager()
    return manager.get_litellm_filter_config()