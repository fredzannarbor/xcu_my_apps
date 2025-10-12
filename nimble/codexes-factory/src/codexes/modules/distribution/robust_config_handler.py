
"""
Robust Configuration Error Handler

This module provides comprehensive error handling for configuration loading and validation.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConfigurationError:
    """Represents a configuration error with context."""
    error_type: str
    message: str
    file_path: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


class RobustConfigurationHandler:
    """Provides robust error handling for configuration operations."""
    
    def __init__(self):
        self.errors: List[ConfigurationError] = []
        self.warnings: List[str] = []
    
    def load_config_with_fallback(self, config_path: str, fallback_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Load configuration with comprehensive error handling and fallback."""
        if fallback_config is None:
            fallback_config = {}
        
        try:
            path = Path(config_path)
            
            # Check if file exists
            if not path.exists():
                error = ConfigurationError(
                    error_type="FILE_NOT_FOUND",
                    message=f"Configuration file not found: {config_path}",
                    file_path=config_path,
                    suggestion="Create the configuration file or check the path"
                )
                self.errors.append(error)
                logger.warning(f"Config file not found, using fallback: {config_path}")
                return fallback_config
            
            # Check if file is readable
            if not os.access(path, os.R_OK):
                error = ConfigurationError(
                    error_type="PERMISSION_DENIED",
                    message=f"Cannot read configuration file: {config_path}",
                    file_path=config_path,
                    suggestion="Check file permissions"
                )
                self.errors.append(error)
                logger.error(f"Cannot read config file, using fallback: {config_path}")
                return fallback_config
            
            # Try to load JSON
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for empty file
                if not content.strip():
                    error = ConfigurationError(
                        error_type="EMPTY_FILE",
                        message=f"Configuration file is empty: {config_path}",
                        file_path=config_path,
                        suggestion="Add valid JSON configuration to the file"
                    )
                    self.errors.append(error)
                    logger.warning(f"Empty config file, using fallback: {config_path}")
                    return fallback_config
                
                # Parse JSON with detailed error reporting
                try:
                    config = json.loads(content)
                except json.JSONDecodeError as e:
                    error = ConfigurationError(
                        error_type="INVALID_JSON",
                        message=f"Invalid JSON in configuration file: {e.msg}",
                        file_path=config_path,
                        line_number=e.lineno,
                        suggestion=f"Fix JSON syntax error at line {e.lineno}, column {e.colno}"
                    )
                    self.errors.append(error)
                    logger.error(f"Invalid JSON in config file, using fallback: {config_path}")
                    return fallback_config
                
                # Validate configuration structure
                if not isinstance(config, dict):
                    error = ConfigurationError(
                        error_type="INVALID_STRUCTURE",
                        message=f"Configuration must be a JSON object, got {type(config).__name__}",
                        file_path=config_path,
                        suggestion="Ensure the configuration file contains a JSON object ({})"
                    )
                    self.errors.append(error)
                    logger.error(f"Invalid config structure, using fallback: {config_path}")
                    return fallback_config
                
                # Merge with fallback config (fallback provides defaults)
                merged_config = {**fallback_config, **config}
                
                logger.info(f"Successfully loaded configuration: {config_path}")
                return merged_config
                
        except Exception as e:
            error = ConfigurationError(
                error_type="UNEXPECTED_ERROR",
                message=f"Unexpected error loading configuration: {str(e)}",
                file_path=config_path,
                suggestion="Check the configuration file and system permissions"
            )
            self.errors.append(error)
            logger.error(f"Unexpected error loading config, using fallback: {config_path}")
            return fallback_config
    
    def validate_required_fields(self, config: Dict[str, Any], required_fields: List[str], 
                                config_path: str) -> bool:
        """Validate that required fields are present in configuration."""
        all_valid = True
        
        for field in required_fields:
            if field not in config:
                error = ConfigurationError(
                    error_type="MISSING_REQUIRED_FIELD",
                    message=f"Required field '{field}' missing from configuration",
                    file_path=config_path,
                    suggestion=f"Add '{field}' to the configuration file"
                )
                self.errors.append(error)
                all_valid = False
            elif config[field] is None or (isinstance(config[field], str) and not config[field].strip()):
                error = ConfigurationError(
                    error_type="EMPTY_REQUIRED_FIELD",
                    message=f"Required field '{field}' is empty",
                    file_path=config_path,
                    suggestion=f"Provide a valid value for '{field}'"
                )
                self.errors.append(error)
                all_valid = False
        
        return all_valid
    
    def get_error_report(self) -> Dict[str, Any]:
        """Get comprehensive error report."""
        return {
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [
                {
                    "type": error.error_type,
                    "message": error.message,
                    "file": error.file_path,
                    "line": error.line_number,
                    "suggestion": error.suggestion
                }
                for error in self.errors
            ],
            "warnings": self.warnings
        }
    
    def clear_errors(self):
        """Clear all errors and warnings."""
        self.errors.clear()
        self.warnings.clear()
