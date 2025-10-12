#!/usr/bin/env python3

"""
Test script for multi-level configuration system.

This script tests the multi-level configuration system to ensure it correctly
resolves configuration values from different levels with proper priority handling.
"""

import os
import sys
import json
import logging
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Import the necessary modules
from codexes.modules.distribution.multi_level_config import (
    MultiLevelConfiguration, ConfigurationLevel, ConfigurationContext,
    ConfigurationValidator, create_default_multi_level_config
)

def test_multi_level_configuration():
    """Test multi-level configuration system."""
    logger.info("Starting multi-level configuration test")
    
    # Create temporary directory for test configurations
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "test_configs"
        config_dir.mkdir(parents=True)
        
        # Create test configuration files
        create_test_config_files(config_dir)
        
        # Test results
        results = {
            "basic_resolution": {},
            "priority_testing": {},
            "context_resolution": {},
            "validation_testing": {},
            "configuration_info": {},
            "file_operations": {}
        }
        
        # Create multi-level configuration
        config = MultiLevelConfiguration(str(config_dir))
        
        # Test basic configuration resolution
        logger.info("Testing basic configuration resolution")
        
        basic_tests = [
            "lightning_source_account",
            "us_wholesale_discount", 
            "publisher",
            "imprint",
            "language_code",
            "binding_type",
            "nonexistent_key"
        ]
        
        for key in basic_tests:
            value = config.get_value(key, default="DEFAULT_VALUE")
            logger.info(f"Basic resolution - {key}: {value}")
            results["basic_resolution"][key] = value
        
        # Test priority-based resolution
        logger.info("\\nTesting priority-based resolution")
        
        # Create contexts with different levels of specificity
        contexts = [
            ConfigurationContext(),  # No context
            ConfigurationContext(publisher_name="test_publisher"),  # Publisher context
            ConfigurationContext(imprint_name="test_imprint"),  # Imprint context
            ConfigurationContext(
                publisher_name="test_publisher", 
                imprint_name="test_imprint"
            ),  # Both publisher and imprint
            ConfigurationContext(
                publisher_name="test_publisher",
                imprint_name="test_imprint",
                book_isbn="9781234567890"
            ),  # Full context
            ConfigurationContext(
                field_overrides={"us_wholesale_discount": "99"}
            )  # Field override context
        ]
        
        test_key = "us_wholesale_discount"
        for i, context in enumerate(contexts):
            value = config.get_value(test_key, context, default="NO_VALUE")
            context_desc = f"Context {i+1}"
            if context.publisher_name:
                context_desc += f" (pub: {context.publisher_name})"
            if context.imprint_name:
                context_desc += f" (imp: {context.imprint_name})"
            if context.book_isbn:
                context_desc += f" (book: {context.book_isbn})"
            if context.field_overrides:
                context_desc += f" (overrides: {list(context.field_overrides.keys())})"
            
            logger.info(f"Priority test - {context_desc}: {value}")
            results["priority_testing"][context_desc] = value
        
        # Test context-specific resolution
        logger.info("\\nTesting context-specific resolution")
        
        context_tests = [
            {
                "name": "Publisher-specific",
                "context": ConfigurationContext(publisher_name="test_publisher"),
                "keys": ["publisher_specific_field", "us_wholesale_discount"]
            },
            {
                "name": "Imprint-specific", 
                "context": ConfigurationContext(imprint_name="test_imprint"),
                "keys": ["imprint_specific_field", "language_code"]
            },
            {
                "name": "Combined context",
                "context": ConfigurationContext(
                    publisher_name="test_publisher",
                    imprint_name="test_imprint"
                ),
                "keys": ["us_wholesale_discount", "language_code", "publisher_specific_field"]
            }
        ]
        
        for test in context_tests:
            test_results = {}
            for key in test["keys"]:
                value = config.get_value(key, test["context"], default="NOT_FOUND")
                logger.info(f"{test['name']} - {key}: {value}")
                test_results[key] = value
            results["context_resolution"][test["name"]] = test_results
        
        # Test validation
        logger.info("\\nTesting validation")
        
        validation_tests = [
            {"key": "us_wholesale_discount", "value": "45", "should_pass": True},
            {"key": "us_wholesale_discount", "value": "150", "should_pass": False},
            {"key": "us_wholesale_discount", "value": "-10", "should_pass": False},
            {"key": "lightning_source_account", "value": "LSI123456", "should_pass": True},
            {"key": "lightning_source_account", "value": "", "should_pass": False},
            {"key": "isbn13", "value": "9781234567890", "should_pass": True},
            {"key": "isbn13", "value": "invalid-isbn", "should_pass": False},
            {"key": "publication_date", "value": "2024-03-15", "should_pass": True},
            {"key": "publication_date", "value": "invalid-date", "should_pass": False}
        ]
        
        for test in validation_tests:
            success = config.set_value(
                test["key"], 
                test["value"], 
                ConfigurationLevel.GLOBAL_DEFAULT,
                description=f"Test value for {test['key']}"
            )
            
            result = "PASS" if success == test["should_pass"] else "FAIL"
            logger.info(f"Validation - {test['key']}='{test['value']}': {result} (expected: {'pass' if test['should_pass'] else 'fail'})")
            
            results["validation_testing"][f"{test['key']}_{test['value']}"] = {
                "success": success,
                "expected": test["should_pass"],
                "result": result
            }
        
        # Test configuration information
        logger.info("\\nTesting configuration information")
        
        info_keys = ["us_wholesale_discount", "lightning_source_account", "nonexistent_key"]
        context = ConfigurationContext(
            publisher_name="test_publisher",
            imprint_name="test_imprint"
        )
        
        for key in info_keys:
            info = config.get_configuration_info(key, context)
            logger.info(f"Config info - {key}: level={info.get('level')}, value={info.get('value')}")
            results["configuration_info"][key] = info
        
        # Test file operations
        logger.info("\\nTesting file operations")
        
        # Test saving configuration
        test_config_path = config_dir / "test_save.json"
        save_success = config.save_configuration_file(
            str(test_config_path), 
            ConfigurationLevel.GLOBAL_DEFAULT
        )
        logger.info(f"Save configuration: {'SUCCESS' if save_success else 'FAILED'}")
        results["file_operations"]["save_success"] = save_success
        
        # Test loading configuration
        if test_config_path.exists():
            load_success = config.load_configuration_file(
                str(test_config_path),
                ConfigurationLevel.BOOK_SPECIFIC
            )
            logger.info(f"Load configuration: {'SUCCESS' if load_success else 'FAILED'}")
            results["file_operations"]["load_success"] = load_success
        
        # Test listing all configurations
        logger.info("\\nTesting configuration listing")
        all_configs = config.list_all_configurations(context)
        logger.info(f"Total configurations found: {len(all_configs)}")
        results["configuration_info"]["total_configs"] = len(all_configs)
        
        # Show sample configurations
        sample_keys = list(all_configs.keys())[:5]
        for key in sample_keys:
            info = all_configs[key]
            logger.info(f"Sample config - {key}: {info.get('value')} (from {info.get('level')})")
        
        # Test default configuration creation
        logger.info("\\nTesting default configuration creation")
        default_config = create_default_multi_level_config(str(config_dir))
        
        # Test some default validations
        default_validation_tests = [
            {"key": "us_wholesale_discount", "value": "40", "expected": True},
            {"key": "contact_email", "value": "test@example.com", "expected": True},
            {"key": "contact_email", "value": "invalid-email", "expected": False},
            {"key": "language_code", "value": "eng", "expected": True},
            {"key": "language_code", "value": "invalid", "expected": False}
        ]
        
        default_validation_results = {}
        for test in default_validation_tests:
            success = default_config.set_value(
                test["key"],
                test["value"],
                ConfigurationLevel.GLOBAL_DEFAULT
            )
            result = "PASS" if success == test["expected"] else "FAIL"
            logger.info(f"Default validation - {test['key']}='{test['value']}': {result}")
            default_validation_results[f"{test['key']}_{test['value']}"] = {
                "success": success,
                "expected": test["expected"],
                "result": result
            }
        
        results["default_validation"] = default_validation_results
        
        # Save results to a JSON file for inspection
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"multi_level_config_test_{timestamp}.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Test results saved to {output_path}")
        
        return results

def create_test_config_files(config_dir: Path):
    """Create test configuration files for testing."""
    
    # Create directories
    (config_dir / "publishers").mkdir(parents=True, exist_ok=True)
    (config_dir / "imprints").mkdir(parents=True, exist_ok=True)
    (config_dir / "books").mkdir(parents=True, exist_ok=True)
    
    # Global default configuration
    global_config = {
        "lightning_source_account": "LSI123456",
        "us_wholesale_discount": "40",
        "uk_wholesale_discount": "35",
        "language_code": "eng",
        "binding_type": "paperback",
        "interior_color": "BW",
        "carton_pack_quantity": "24",
        "territorial_rights": "World",
        "returnability": "Yes"
    }
    
    with open(config_dir / "default_lsi_config.json", 'w') as f:
        json.dump(global_config, f, indent=2)
    
    # Publisher-specific configuration
    publisher_config = {
        "publisher": "Test Publisher Inc.",
        "us_wholesale_discount": "45",  # Override global
        "publisher_specific_field": "publisher_value",
        "contact_email": "publisher@test.com",
        "territorial_rights": "US Only"  # Override global
    }
    
    with open(config_dir / "publishers" / "test_publisher.json", 'w') as f:
        json.dump(publisher_config, f, indent=2)
    
    # Imprint-specific configuration
    imprint_config = {
        "imprint": "Test Imprint",
        "language_code": "spa",  # Override global
        "imprint_specific_field": "imprint_value",
        "binding_type": "hardcover",  # Override global
        "us_wholesale_discount": "50"  # Override publisher and global
    }
    
    with open(config_dir / "imprints" / "test_imprint.json", 'w') as f:
        json.dump(imprint_config, f, indent=2)
    
    # Book-specific configuration
    book_config = {
        "title": "Test Book",
        "author": "Test Author",
        "isbn13": "9781234567890",
        "us_wholesale_discount": "55",  # Override all others
        "book_specific_field": "book_value",
        "special_instructions": "Handle with care"
    }
    
    with open(config_dir / "books" / "9781234567890.json", 'w') as f:
        json.dump(book_config, f, indent=2)

if __name__ == "__main__":
    test_multi_level_configuration()