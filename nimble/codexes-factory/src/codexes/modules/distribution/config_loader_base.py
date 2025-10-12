"""
Base class for configuration loaders
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List


class ConfigLoaderBase:
    """Base class for configuration loaders"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def load_config_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load a JSON configuration file"""
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.warning(f"Configuration file not found: {file_path}")
                return None
                
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.logger.debug(f"Loaded configuration from: {file_path}")
            return config
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading configuration file {file_path}: {e}")
            return None
    
    def validate_config(self, config: Dict[str, Any], required_fields: List[str] = None) -> bool:
        """Basic configuration validation"""
        if not isinstance(config, dict):
            return False
            
        if required_fields:
            for field in required_fields:
                if field not in config:
                    self.logger.error(f"Required field missing: {field}")
                    return False
        
        return True
    
    def get_config_value(self, config: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Get a configuration value with fallback to default"""
        return config.get(key, default)