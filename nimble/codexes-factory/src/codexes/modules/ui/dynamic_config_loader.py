"""
Dynamic Configuration Discovery and Loading for Streamlit UI
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import jsonschema
from datetime import datetime


class DynamicConfigurationLoader:
    """Scan and load configuration files from the file system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_schemas = self._load_config_schemas()
        
    def _load_config_schemas(self) -> Dict[str, Dict]:
        """Load JSON schemas for configuration validation"""
        schemas = {}
        
        # Publisher schema
        schemas['publisher'] = {
            "type": "object",
            "required": ["publisher", "lightning_source_account"],
            "properties": {
                "publisher": {"type": "string"},
                "lightning_source_account": {"type": "string"},
                "contact_email": {"type": "string"},
                "company_info": {"type": "object"},
                "default_settings": {"type": "object"},
                "pricing_strategy": {"type": "object"},
                "distribution_settings": {"type": "object"}
            }
        }
        
        # Imprint schema
        schemas['imprint'] = {
            "type": "object",
            "required": ["imprint", "publisher"],
            "properties": {
                "imprint": {"type": "string"},
                "publisher": {"type": "string"},
                "contact_email": {"type": "string"},
                "branding": {"type": "object"},
                "publishing_focus": {"type": "object"},
                "default_book_settings": {"type": "object"}
            }
        }
        
        # Tranche schema
        schemas['tranche'] = {
            "type": "object",
            "required": ["tranche_info", "publisher", "imprint"],
            "properties": {
                "tranche_info": {"type": "object"},
                "publisher": {"type": "string"},
                "imprint": {"type": "string"},
                "field_overrides": {"type": "object"},
                "field_exclusions": {"type": "array"}
            }
        }
        
        return schemas
    
    def scan_publishers(self) -> List[str]:
        """Scan for available publisher configurations"""
        publishers = []
        publisher_dir = Path("configs/publishers")
        
        if not publisher_dir.exists():
            self.logger.warning(f"Publisher directory not found: {publisher_dir}")
            return publishers
            
        try:
            for file_path in publisher_dir.glob("*.json"):
                if file_path.name.startswith('.'):
                    continue
                    
                # Validate the configuration file
                if self._validate_config_file(file_path, 'publisher'):
                    publishers.append(file_path.stem)
                else:
                    self.logger.warning(f"Invalid publisher config: {file_path}")
                    
        except Exception as e:
            self.logger.error(f"Error scanning publishers: {e}")
            
        return sorted(publishers)
    
    def scan_imprints(self, publisher: str = None) -> List[str]:
        """Scan for available imprint configurations"""
        imprints = []
        # Prefer 'imprints/' with a fallback to legacy 'configs/imprints'
        preferred_dir = Path("imprints")
        legacy_dir = Path("configs/imprints")
        imprint_dir = preferred_dir if preferred_dir.exists() else legacy_dir
        
        if not imprint_dir.exists():
            self.logger.warning(f"Imprint directory not found: {preferred_dir} (also checked {legacy_dir})")
            return imprints
            
        try:
            # If publisher is specified, try to get the actual publisher name from config
            actual_publisher_name = None
            if publisher:
                # First try to load publisher config to get actual name
                publisher_config = self.load_configuration_file('publisher', publisher)
                if publisher_config:
                    actual_publisher_name = publisher_config.get('publisher', publisher)
                else:
                    # Fallback to the provided publisher name
                    actual_publisher_name = publisher
            
            for file_path in imprint_dir.glob("*.json"):
                if file_path.name.startswith('.'):
                    continue
                    
                # Validate the configuration file
                if self._validate_config_file(file_path, 'imprint'):
                    # If publisher is specified, filter by publisher
                    if publisher:
                        config = self.load_configuration_file('imprint', file_path.stem)
                        if config:
                            imprint_publisher = config.get('publisher', '')
                            # Match against both the filename and actual publisher name
                            if (imprint_publisher == publisher or 
                                imprint_publisher == actual_publisher_name):
                                imprints.append(file_path.stem)
                    else:
                        imprints.append(file_path.stem)
                else:
                    self.logger.warning(f"Invalid imprint config: {file_path}")
                    
        except Exception as e:
            self.logger.error(f"Error scanning imprints: {e}")
            
        return sorted(imprints)
    
    def scan_tranches(self, imprint: str = None) -> List[str]:
        """Scan for available tranche configurations"""
        tranches = []
        tranche_dir = Path("configs/tranches")
        
        if not tranche_dir.exists():
            self.logger.warning(f"Tranche directory not found: {tranche_dir}")
            return tranches
            
        try:
            for file_path in tranche_dir.glob("*.json"):
                if file_path.name.startswith('.'):
                    continue
                    
                # Validate the configuration file
                if self._validate_config_file(file_path, 'tranche'):
                    # If imprint is specified, filter by imprint
                    if imprint:
                        config = self.load_configuration_file('tranche', file_path.stem)
                        if config and config.get('imprint') == imprint:
                            tranches.append(file_path.stem)
                    else:
                        tranches.append(file_path.stem)
                else:
                    self.logger.warning(f"Invalid tranche config: {file_path}")
                    
        except Exception as e:
            self.logger.error(f"Error scanning tranches: {e}")
            
        return sorted(tranches)
    
    def load_configuration_file(self, config_type: str, name: str) -> Optional[Dict[str, Any]]:
        """Load and parse a configuration file"""
        config_dirs = {
            'publisher': 'configs/publishers',
            'imprint': 'configs/imprints',
            'tranche': 'configs/tranches'
        }
        
        if config_type not in config_dirs:
            self.logger.error(f"Unknown configuration type: {config_type}")
            return None
            
        config_path = Path(config_dirs[config_type]) / f"{name}.json"
        
        if not config_path.exists():
            self.logger.error(f"Configuration file not found: {config_path}")
            return None
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Validate against schema
            if self.validate_configuration_structure(config, config_type):
                return config
            else:
                self.logger.error(f"Configuration validation failed: {config_path}")
                return None
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in {config_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading configuration {config_path}: {e}")
            return None
    
    def validate_configuration_structure(self, config: Dict[str, Any], config_type: str) -> bool:
        """Validate configuration structure against schema"""
        if config_type not in self.config_schemas:
            self.logger.warning(f"No schema available for config type: {config_type}")
            return True  # Allow if no schema
            
        try:
            jsonschema.validate(config, self.config_schemas[config_type])
            return True
        except jsonschema.ValidationError as e:
            self.logger.error(f"Schema validation error for {config_type}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected validation error: {e}")
            return False
    
    def _validate_config_file(self, file_path: Path, config_type: str) -> bool:
        """Validate a configuration file without fully loading it"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return self.validate_configuration_structure(config, config_type)
        except Exception as e:
            self.logger.error(f"Error validating config file {file_path}: {e}")
            return False
    
    def get_configuration_metadata(self, config_type: str, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata about a configuration file"""
        config = self.load_configuration_file(config_type, name)
        if not config:
            return None
            
        metadata = {
            'name': name,
            'type': config_type,
            'last_modified': None,
            'description': None,
            'version': None
        }
        
        # Extract metadata from _config_info section
        config_info = config.get('_config_info', {})
        metadata['description'] = config_info.get('description', '')
        metadata['version'] = config_info.get('version', '')
        metadata['last_updated'] = config_info.get('last_updated', '')
        
        # Get file modification time
        config_dirs = {
            'publisher': 'configs/publishers',
            'imprint': 'configs/imprints',
            'tranche': 'configs/tranches'
        }
        
        config_path = Path(config_dirs[config_type]) / f"{name}.json"
        if config_path.exists():
            metadata['last_modified'] = datetime.fromtimestamp(
                config_path.stat().st_mtime
            ).isoformat()
        
        return metadata
    
    def get_all_configurations_metadata(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get metadata for all available configurations"""
        metadata = {
            'publishers': [],
            'imprints': [],
            'tranches': []
        }
        
        # Get publisher metadata
        for publisher in self.scan_publishers():
            pub_metadata = self.get_configuration_metadata('publisher', publisher)
            if pub_metadata:
                metadata['publishers'].append(pub_metadata)
        
        # Get imprint metadata
        for imprint in self.scan_imprints():
            imp_metadata = self.get_configuration_metadata('imprint', imprint)
            if imp_metadata:
                metadata['imprints'].append(imp_metadata)
        
        # Get tranche metadata
        for tranche in self.scan_tranches():
            tr_metadata = self.get_configuration_metadata('tranche', tranche)
            if tr_metadata:
                metadata['tranches'].append(tr_metadata)
        
        return metadata
    
    def create_configuration_template(self, config_type: str) -> Dict[str, Any]:
        """Create a template for a new configuration"""
        templates = {
            'publisher': {
                "_config_info": {
                    "description": "New publisher configuration",
                    "version": "1.0",
                    "last_updated": datetime.now().strftime("%Y-%m-%d"),
                    "config_type": "publisher"
                },
                "publisher": "New Publisher Name",
                "contact_email": "contact@publisher.com",
                "lightning_source_account": "",
                "company_info": {
                    "legal_name": "",
                    "founded_year": "",
                    "headquarters": "",
                    "website": ""
                },
                "default_settings": {
                    "language_code": "eng",
                    "country_of_origin": "US",
                    "territorial_rights": "World"
                },
                "pricing_strategy": {
                    "us_wholesale_discount": "40",
                    "uk_wholesale_discount": "40",
                    "eu_wholesale_discount": "40"
                }
            },
            'imprint': {
                "_config_info": {
                    "description": "New imprint configuration",
                    "version": "1.0",
                    "last_updated": datetime.now().strftime("%Y-%m-%d"),
                    "config_type": "imprint"
                },
                "imprint": "New Imprint Name",
                "publisher": "Publisher Name",
                "contact_email": "imprint@publisher.com",
                "branding": {
                    "tagline": "",
                    "website": "",
                    "brand_colors": {
                        "primary": "#000000",
                        "secondary": "#FFFFFF"
                    }
                },
                "default_book_settings": {
                    "language_code": "eng",
                    "binding_type": "paperback",
                    "trim_size": "6x9"
                }
            },
            'tranche': {
                "_config_info": {
                    "description": "New tranche configuration",
                    "version": "1.0",
                    "last_updated": datetime.now().strftime("%Y-%m-%d"),
                    "config_type": "tranche"
                },
                "tranche_info": {
                    "tranche_id": "new-tranche",
                    "tranche_name": "New Tranche",
                    "book_count": 0,
                    "target_month": "",
                    "target_year": ""
                },
                "publisher": "Publisher Name",
                "imprint": "Imprint Name",
                "field_overrides": {},
                "field_exclusions": []
            }
        }
        
        return templates.get(config_type, {})