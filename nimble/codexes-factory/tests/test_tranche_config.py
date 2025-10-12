#!/usr/bin/env python3
"""
Test script for tranche configuration system.
"""

import os
import sys
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from codexes.modules.distribution.tranche_config_loader import TrancheConfigLoader
from codexes.modules.distribution.multi_level_config import (
    MultiLevelConfiguration,
    ConfigurationContext,
    ConfigurationLevel
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_list_tranches():
    """Test listing available tranches."""
    loader = TrancheConfigLoader()
    tranches = loader.list_available_tranches()
    logger.info(f"Available tranches: {tranches}")
    return tranches

def test_load_tranche_config(tranche_name):
    """Test loading tranche configuration."""
    loader = TrancheConfigLoader()
    config = loader.load_tranche_config(tranche_name)
    logger.info(f"Tranche config info: {config.get('_config_info', {})}")
    logger.info(f"Tranche info: {config.get('tranche_info', {})}")
    return config

def test_tranche_context(tranche_name):
    """Test creating tranche context."""
    loader = TrancheConfigLoader()
    context = loader.get_tranche_context(tranche_name)
    logger.info(f"Tranche context: {context}")
    return context

def test_tranche_values(tranche_name):
    """Test getting tranche values."""
    loader = TrancheConfigLoader()
    
    # Test various configuration values
    test_keys = [
        "rendition_booktype",
        "publisher",
        "imprint",
        "lightning_source_account",
        "required_bisac_subject"
    ]
    
    logger.info(f"Testing tranche values for {tranche_name}:")
    for key in test_keys:
        value = loader.get_tranche_value(tranche_name, key, f"Default {key}")
        logger.info(f"  {key}: {value}")
    
    # Test field exclusions
    exclusions = loader.get_tranche_field_exclusions(tranche_name)
    logger.info(f"Field exclusions: {exclusions}")
    
    # Test annotation boilerplate
    boilerplate = loader.get_tranche_annotation_boilerplate(tranche_name)
    logger.info(f"Annotation boilerplate: {boilerplate}")

def test_multi_level_resolution(tranche_name):
    """Test multi-level configuration resolution with tranche."""
    config = MultiLevelConfiguration()
    
    # Create context with tranche
    context = ConfigurationContext(
        tranche_name=tranche_name,
        publisher_name="nimble_books",
        imprint_name="xynapse_traces"
    )
    
    # Test resolution of various keys
    test_keys = [
        "rendition_booktype",
        "publisher",
        "imprint",
        "lightning_source_account"
    ]
    
    logger.info(f"Testing multi-level resolution with tranche {tranche_name}:")
    for key in test_keys:
        value = config.get_value(key, context, f"Default {key}")
        info = config.get_configuration_info(key, context)
        logger.info(f"  {key}: {value} (from {info.get('level', 'unknown')})")

def main():
    """Main function."""
    logger.info("Testing tranche configuration system")
    
    # List available tranches
    tranches = test_list_tranches()
    
    if not tranches:
        logger.error("No tranches found. Please create a tranche configuration file.")
        return
    
    # Use the first tranche for testing
    tranche_name = tranches[0]
    
    # Test loading tranche config
    test_load_tranche_config(tranche_name)
    
    # Test tranche context
    test_tranche_context(tranche_name)
    
    # Test tranche values
    test_tranche_values(tranche_name)
    
    # Test multi-level resolution
    test_multi_level_resolution(tranche_name)
    
    logger.info("All tests completed")

if __name__ == "__main__":
    main()