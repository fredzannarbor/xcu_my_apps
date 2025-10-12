#!/usr/bin/env python3

"""
Test script for imprint configuration system.

This script tests the imprint configuration management system to ensure it correctly
loads, validates, and integrates imprint-specific configurations.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Import the necessary modules
from codexes.modules.distribution.imprint_config_loader import (
    ImprintConfigurationManager, create_enhanced_lsi_registry_with_imprints
)
from codexes.modules.distribution.multi_level_config import (
    MultiLevelConfiguration, ConfigurationContext
)

def test_imprint_configuration():
    """Test imprint configuration system."""
    logger.info("Starting imprint configuration test")
    
    # Test results
    results = {
        "imprint_loading": {},
        "configuration_extraction": {},
        "validation_results": {},
        "multi_level_integration": {},
        "field_mapping_integration": {},
        "template_creation": {}
    }
    
    # Create imprint configuration manager
    imprint_manager = ImprintConfigurationManager("configs")
    
    # Test imprint loading
    logger.info("Testing imprint loading")
    
    imprint_names = imprint_manager.get_imprint_names()
    logger.info(f"Found {len(imprint_names)} imprints: {imprint_names}")
    results["imprint_loading"]["total_imprints"] = len(imprint_names)
    results["imprint_loading"]["imprint_names"] = imprint_names
    
    # Test configuration extraction for each imprint
    logger.info("\\nTesting configuration extraction")
    
    for imprint_name in imprint_names:
        logger.info(f"Testing imprint: {imprint_name}")
        
        # Get imprint configuration
        config = imprint_manager.get_imprint_config(imprint_name)
        if config:
            logger.info(f"  Configuration loaded: {len(config)} sections")
            
            # Get defaults
            defaults = imprint_manager.get_imprint_defaults(imprint_name)
            logger.info(f"  Default values: {len(defaults)} fields")
            
            # Get field mappings
            mappings = imprint_manager.get_imprint_field_mappings(imprint_name)
            logger.info(f"  Field mappings: {len(mappings)} mappings")
            
            # Get territorial pricing
            territorial = imprint_manager.get_territorial_pricing_config(imprint_name)
            logger.info(f"  Territorial configs: {len(territorial)} territories")
            
            # Store results
            results["configuration_extraction"][imprint_name] = {
                "config_sections": len(config),
                "default_values": len(defaults),
                "field_mappings": len(mappings),
                "territorial_configs": len(territorial),
                "sample_defaults": dict(list(defaults.items())[:5]),  # First 5 defaults
                "sample_mappings": dict(list(mappings.items())[:3])   # First 3 mappings
            }
        else:
            logger.warning(f"  No configuration found for {imprint_name}")
            results["configuration_extraction"][imprint_name] = {"error": "Configuration not found"}
    
    # Test validation
    logger.info("\\nTesting configuration validation")
    
    for imprint_name in imprint_names:
        validation_result = imprint_manager.validate_imprint_config(imprint_name)
        
        status = "VALID" if validation_result["valid"] else "INVALID"
        logger.info(f"Validation - {imprint_name}: {status}")
        
        if validation_result["errors"]:
            logger.info(f"  Errors: {validation_result['errors']}")
        
        if validation_result["warnings"]:
            logger.info(f"  Warnings: {validation_result['warnings']}")
        
        results["validation_results"][imprint_name] = validation_result
    
    # Test multi-level configuration integration
    logger.info("\\nTesting multi-level configuration integration")
    
    multi_config = MultiLevelConfiguration("configs")
    imprint_manager.integrate_with_multi_level_config(multi_config)
    
    # Test configuration resolution with imprint context
    test_imprint = imprint_names[0] if imprint_names else "xynapse_traces"
    context = imprint_manager.create_imprint_context(test_imprint)
    
    test_keys = [
        "us_wholesale_discount",
        "binding_type",
        "language_code",
        "carton_pack_quantity",
        "territorial_rights"
    ]
    
    integration_results = {}
    for key in test_keys:
        value = multi_config.get_value(key, context, default="NOT_FOUND")
        logger.info(f"Multi-level resolution - {key}: {value}")
        integration_results[key] = value
    
    results["multi_level_integration"] = {
        "test_imprint": test_imprint,
        "resolved_values": integration_results
    }
    
    # Test field mapping integration
    logger.info("\\nTesting field mapping integration")
    
    if imprint_names:
        test_imprint = imprint_names[0]
        registry = create_enhanced_lsi_registry_with_imprints(test_imprint, "configs")
        
        # Test some field mappings
        test_fields = [
            "Lightning Source Account",
            "Stamped Text CENTER",
            "Publisher Reference ID",
            "Carton Pack Quantity"
        ]
        
        mapping_results = {}
        for field in test_fields:
            if registry.has_strategy(field):
                # Create dummy metadata for testing
                from codexes.modules.metadata.metadata_models import CodexMetadata
                from codexes.modules.distribution.field_mapping import MappingContext
                
                dummy_metadata = CodexMetadata(title="Test Book", isbn13="9781234567890")
                dummy_context = MappingContext()
                
                try:
                    strategy = registry.get_strategy(field)
                    value = strategy.map_field(dummy_metadata, dummy_context)
                    logger.info(f"Field mapping - {field}: {value}")
                    mapping_results[field] = value
                except Exception as e:
                    logger.warning(f"Field mapping error - {field}: {e}")
                    mapping_results[field] = f"ERROR: {str(e)}"
            else:
                logger.info(f"Field mapping - {field}: NO_STRATEGY")
                mapping_results[field] = "NO_STRATEGY"
        
        results["field_mapping_integration"] = {
            "test_imprint": test_imprint,
            "field_results": mapping_results
        }
    
    # Test template creation
    logger.info("\\nTesting template creation")
    
    test_imprint_name = "Test Imprint"
    test_publisher_name = "Test Publisher"
    test_contact_email = "test@example.com"
    
    creation_success = imprint_manager.create_imprint_from_template(
        test_imprint_name,
        test_publisher_name,
        test_contact_email
    )
    
    logger.info(f"Template creation: {'SUCCESS' if creation_success else 'FAILED'}")
    
    if creation_success:
        # Validate the created imprint
        validation = imprint_manager.validate_imprint_config(test_imprint_name)
        logger.info(f"Created imprint validation: {'VALID' if validation['valid'] else 'INVALID'}")
        
        # Clean up - remove the test imprint file
        test_file = Path("configs/imprints/test_imprint.json")
        if test_file.exists():
            test_file.unlink()
            logger.info("Cleaned up test imprint file")
    
    results["template_creation"] = {
        "creation_success": creation_success,
        "test_imprint": test_imprint_name
    }
    
    # Test context creation
    logger.info("\\nTesting context creation")
    
    if imprint_names:
        test_imprint = imprint_names[0]
        context = imprint_manager.create_imprint_context(
            test_imprint,
            book_isbn="9781234567890"
        )
        
        logger.info(f"Context creation - Imprint: {context.imprint_name}")
        logger.info(f"Context creation - Publisher: {context.publisher_name}")
        logger.info(f"Context creation - Book ISBN: {context.book_isbn}")
        
        results["context_creation"] = {
            "imprint_name": context.imprint_name,
            "publisher_name": context.publisher_name,
            "book_isbn": context.book_isbn
        }
    
    # Test configuration comparison
    logger.info("\\nTesting configuration comparison")
    
    if len(imprint_names) >= 2:
        imprint1 = imprint_names[0]
        imprint2 = imprint_names[1]
        
        defaults1 = imprint_manager.get_imprint_defaults(imprint1)
        defaults2 = imprint_manager.get_imprint_defaults(imprint2)
        
        # Find common keys
        common_keys = set(defaults1.keys()) & set(defaults2.keys())
        different_values = {}
        
        for key in common_keys:
            if defaults1[key] != defaults2[key]:
                different_values[key] = {
                    imprint1: defaults1[key],
                    imprint2: defaults2[key]
                }
        
        logger.info(f"Configuration comparison - {imprint1} vs {imprint2}:")
        logger.info(f"  Common keys: {len(common_keys)}")
        logger.info(f"  Different values: {len(different_values)}")
        
        # Show some differences
        for key, values in list(different_values.items())[:3]:
            logger.info(f"  {key}: {imprint1}='{values[imprint1]}', {imprint2}='{values[imprint2]}'")
        
        results["configuration_comparison"] = {
            "imprint1": imprint1,
            "imprint2": imprint2,
            "common_keys": len(common_keys),
            "different_values": len(different_values),
            "sample_differences": dict(list(different_values.items())[:3])
        }
    
    # Save results to a JSON file for inspection
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"imprint_config_test_{timestamp}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Test results saved to {output_path}")
    
    return results

if __name__ == "__main__":
    test_imprint_configuration()