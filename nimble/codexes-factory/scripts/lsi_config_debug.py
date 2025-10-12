#!/usr/bin/env python
"""
LSI Configuration Debugging Script

This script adds debug logging to the LSI configuration class to help diagnose
why the configuration isn't being loaded properly.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("lsi_config_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("lsi_config_debug")

try:
    # Try importing with the standard module path
    from codexes.modules.distribution.lsi_configuration import LSIConfiguration
except ModuleNotFoundError:
    # Fall back to src-prefixed imports when running from project root
    from src.codexes.modules.distribution.lsi_configuration import LSIConfiguration

# Monkey patch the LSIConfiguration class to add debug logging
original_init = LSIConfiguration.__init__
original_load_config_file = LSIConfiguration._load_config_file
original_load_default_configs = LSIConfiguration._load_default_configs
original_load_publisher_config = LSIConfiguration._load_publisher_config
original_load_imprint_config = LSIConfiguration._load_imprint_config
original_parse_config_data = LSIConfiguration._parse_config_data
original_get_field_value = LSIConfiguration.get_field_value

def debug_init(self, config_path=None, config_dir=None):
    logger.debug(f"Initializing LSIConfiguration with config_path={config_path}, config_dir={config_dir}")
    original_init(self, config_path, config_dir)
    logger.debug(f"LSIConfiguration initialized with:")
    logger.debug(f"  config_dir: {self.config_dir}")
    logger.debug(f"  publishers_dir: {self.publishers_dir}")
    logger.debug(f"  imprints_dir: {self.imprints_dir}")
    logger.debug(f"  _defaults: {self._defaults}")
    logger.debug(f"  _field_overrides: {self._field_overrides}")
    logger.debug(f"  _imprint_configs: {list(self._imprint_configs.keys())}")
    logger.debug(f"  _territorial_configs: {list(self._territorial_configs.keys())}")

def debug_load_config_file(self, config_path):
    logger.debug(f"Loading config file: {config_path}")
    try:
        original_load_config_file(self, config_path)
        logger.debug(f"Successfully loaded config file: {config_path}")
        logger.debug(f"  _defaults: {self._defaults}")
        logger.debug(f"  _field_overrides: {self._field_overrides}")
        logger.debug(f"  _imprint_configs: {list(self._imprint_configs.keys())}")
        logger.debug(f"  _territorial_configs: {list(self._territorial_configs.keys())}")
    except Exception as e:
        logger.error(f"Error loading config file {config_path}: {e}")
        raise

def debug_load_default_configs(self):
    logger.debug("Loading default configs")
    try:
        original_load_default_configs(self)
        logger.debug("Successfully loaded default configs")
        logger.debug(f"  _defaults: {self._defaults}")
        logger.debug(f"  _field_overrides: {self._field_overrides}")
        logger.debug(f"  _imprint_configs: {list(self._imprint_configs.keys())}")
        logger.debug(f"  _territorial_configs: {list(self._territorial_configs.keys())}")
    except Exception as e:
        logger.error(f"Error loading default configs: {e}")
        raise

def debug_load_publisher_config(self, config_path):
    logger.debug(f"Loading publisher config: {config_path}")
    try:
        original_load_publisher_config(self, config_path)
        logger.debug(f"Successfully loaded publisher config: {config_path}")
    except Exception as e:
        logger.error(f"Error loading publisher config {config_path}: {e}")
        logger.exception(e)

def debug_load_imprint_config(self, config_path):
    logger.debug(f"Loading imprint config: {config_path}")
    try:
        original_load_imprint_config(self, config_path)
        logger.debug(f"Successfully loaded imprint config: {config_path}")
        imprint_name = config_path.stem
        if imprint_name in self._imprint_configs:
            logger.debug(f"  Imprint config loaded for: {imprint_name}")
            logger.debug(f"  Publisher: {self._imprint_configs[imprint_name].publisher}")
            logger.debug(f"  Default values: {self._imprint_configs[imprint_name].default_values}")
            logger.debug(f"  Field overrides: {self._imprint_configs[imprint_name].field_overrides}")
            logger.debug(f"  Territorial configs: {list(self._imprint_configs[imprint_name].territorial_configs.keys())}")
        else:
            logger.warning(f"  Imprint config not found for: {imprint_name} after loading")
    except Exception as e:
        logger.error(f"Error loading imprint config {config_path}: {e}")
        logger.exception(e)

def debug_parse_config_data(self, config_data):
    logger.debug(f"Parsing config data: {list(config_data.keys())}")
    try:
        original_parse_config_data(self, config_data)
        logger.debug("Successfully parsed config data")
    except Exception as e:
        logger.error(f"Error parsing config data: {e}")
        logger.exception(e)

def debug_get_field_value(self, field_name, imprint=None, territory=None):
    logger.debug(f"Getting field value: field_name={field_name}, imprint={imprint}, territory={territory}")
    value = original_get_field_value(self, field_name, imprint, territory)
    logger.debug(f"Field value for {field_name}: {value}")
    return value

# Apply the monkey patches
LSIConfiguration.__init__ = debug_init
LSIConfiguration._load_config_file = debug_load_config_file
LSIConfiguration._load_default_configs = debug_load_default_configs
LSIConfiguration._load_publisher_config = debug_load_publisher_config
LSIConfiguration._load_imprint_config = debug_load_imprint_config
LSIConfiguration._parse_config_data = debug_parse_config_data
LSIConfiguration.get_field_value = debug_get_field_value

def test_config_loading(config_path=None):
    """Test loading the LSI configuration and print debug information."""
    logger.info(f"Testing LSI configuration loading with config_path={config_path}")
    
    try:
        # Create the configuration
        config = LSIConfiguration(config_path)
        
        # Print configuration information
        logger.info("LSI Configuration loaded successfully")
        logger.info(f"Default values: {config._defaults}")
        logger.info(f"Field overrides: {config._field_overrides}")
        logger.info(f"Imprint configs: {list(config._imprint_configs.keys())}")
        logger.info(f"Territorial configs: {list(config._territorial_configs.keys())}")
        
        # Test getting field values
        test_fields = [
            "Lightning Source Account #",
            "Cover/Jacket Submission Method",
            "Text Block SubmissionMethod",
            "Rendition /Booktype",
            "US Wholesale Discount",
            "UK Wholesale Discount (%)",
            "Territorial Rights"
        ]
        
        logger.info("Testing field value retrieval:")
        for field in test_fields:
            value = config.get_field_value(field)
            logger.info(f"  {field}: {value}")
        
        # Test with imprint
        if config._imprint_configs:
            imprint = list(config._imprint_configs.keys())[0]
            logger.info(f"Testing field value retrieval with imprint={imprint}:")
            for field in test_fields:
                value = config.get_field_value(field, imprint)
                logger.info(f"  {field} (imprint={imprint}): {value}")
        
        # Test with territory
        if config._territorial_configs:
            territory = list(config._territorial_configs.keys())[0]
            logger.info(f"Testing field value retrieval with territory={territory}:")
            for field in test_fields:
                value = config.get_field_value(field, territory=territory)
                logger.info(f"  {field} (territory={territory}): {value}")
        
        # Test with both imprint and territory
        if config._imprint_configs and config._territorial_configs:
            imprint = list(config._imprint_configs.keys())[0]
            territory = list(config._territorial_configs.keys())[0]
            logger.info(f"Testing field value retrieval with imprint={imprint}, territory={territory}:")
            for field in test_fields:
                value = config.get_field_value(field, imprint, territory)
                logger.info(f"  {field} (imprint={imprint}, territory={territory}): {value}")
        
        return config
    except Exception as e:
        logger.error(f"Error testing LSI configuration: {e}")
        logger.exception(e)
        return None

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Test LSI configuration loading")
    parser.add_argument("--config", help="Path to LSI configuration file")
    args = parser.parse_args()
    
    # Test configuration loading
    config = test_config_loading(args.config)
    
    # Print summary
    if config:
        print("\nLSI Configuration loaded successfully")
        print(f"Default values: {len(config._defaults)} items")
        print(f"Field overrides: {len(config._field_overrides)} items")
        print(f"Imprint configs: {list(config._imprint_configs.keys())}")
        print(f"Territorial configs: {list(config._territorial_configs.keys())}")
    else:
        print("\nFailed to load LSI configuration")
    
    print("\nSee lsi_config_debug.log for detailed logging information")