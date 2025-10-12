#!/usr/bin/env python3

"""
Debug LSI Field Mapping

This script helps debug why specific LSI fields are not being populated correctly.
"""

import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_field_mappings():
    """Debug the field mapping registry to see what's registered."""
    
    try:
        # Import the necessary modules
        from src.codexes.modules.distribution.enhanced_field_mappings import create_comprehensive_lsi_registry
        from src.codexes.modules.distribution.lsi_configuration import LSIConfiguration
        
        # Create configuration and registry
        config = LSIConfiguration()
        registry = create_comprehensive_lsi_registry(config)
        
        # Fields we're interested in debugging
        debug_fields = [
            "Marketing Image",
            "Interior Path / Filename", 
            "Cover Path / Filename",
            "Annotation / Summary",
            "Contributor One BIO",
            "Series Name",
            "Table of Contents"
        ]
        
        print("Field Mapping Debug Report")
        print("=" * 60)
        
        for field in debug_fields:
            if registry.has_strategy(field):
                strategy = registry.get_strategy(field)
                strategy_type = type(strategy).__name__
                print(f"✅ {field:<35} -> {strategy_type}")
            else:
                print(f"❌ {field:<35} -> NOT REGISTERED")
        
        print("=" * 60)
        print(f"Total registered strategies: {len(registry.get_registered_fields())}")
        
        # Test a specific field mapping
        print("\nTesting Series Name mapping:")
        try:
            from src.codexes.modules.metadata.metadata_models import CodexMetadata
            from src.codexes.modules.distribution.field_mapping import MappingContext
            
            # Create test metadata
            metadata = CodexMetadata()
            metadata.title = "Test Book"
            
            # Create test context
            context = MappingContext("Series Name")
            
            # Test the mapping
            if registry.has_strategy("Series Name"):
                strategy = registry.get_strategy("Series Name")
                result = strategy.map_field(metadata, context)
                print(f"Series Name result: '{result}'")
            else:
                print("Series Name strategy not found")
                
        except Exception as e:
            print(f"Error testing Series Name: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error debugging field mappings: {e}")
        return False


def debug_tranche_config():
    """Debug tranche configuration loading."""
    
    try:
        tranche_path = "configs/tranches/xynapse_tranche_1.json"
        
        print("\nTranche Configuration Debug")
        print("=" * 60)
        
        if not Path(tranche_path).exists():
            print(f"❌ Tranche config not found: {tranche_path}")
            return False
        
        with open(tranche_path, 'r') as f:
            config = json.load(f)
        
        # Check for series info
        if "series_info" in config:
            series_info = config["series_info"]
            print(f"✅ Series info found:")
            for key, value in series_info.items():
                print(f"   {key}: {value}")
        else:
            print("❌ No series_info in tranche config")
        
        # Check for contributor info
        if "contributor_info" in config:
            contrib_info = config["contributor_info"]
            print(f"✅ Contributor info found:")
            for key, value in contrib_info.items():
                print(f"   {key}: {value[:50]}..." if len(str(value)) > 50 else f"   {key}: {value}")
        else:
            print("❌ No contributor_info in tranche config")
        
        # Check for file paths
        if "file_paths" in config:
            file_paths = config["file_paths"]
            print(f"✅ File paths found:")
            for key, value in file_paths.items():
                print(f"   {key}: {value}")
        else:
            print("❌ No file_paths in tranche config")
        
        return True
        
    except Exception as e:
        logger.error(f"Error debugging tranche config: {e}")
        return False


def main():
    """Main debug function."""
    print("Starting LSI field mapping debug...")
    
    success = True
    
    # Debug field mappings
    if not debug_field_mappings():
        success = False
    
    # Debug tranche configuration
    if not debug_tranche_config():
        success = False
    
    if success:
        print("\n✅ Debug completed successfully")
    else:
        print("\n❌ Debug completed with errors")
    
    return success


if __name__ == "__main__":
    main()