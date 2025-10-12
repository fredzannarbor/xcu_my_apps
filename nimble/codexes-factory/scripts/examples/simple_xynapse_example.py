#!/usr/bin/env python3
"""
Simple example showing how to load and use xynapse_traces imprint.
"""

from src.codexes.modules.imprints.services.imprint_manager import ImprintManager

def main():
    print("=== Loading xynapse_traces Imprint ===")
    
    # 1. Initialize manager
    manager = ImprintManager()
    
    # 2. Load the imprint
    xynapse = manager.get_imprint("Xynapse Traces")
    
    print(f"✅ Loaded: {xynapse.name}")
    print(f"   Status: {xynapse.status.value}")
    print(f"   Publisher: {xynapse.publisher}")
    print(f"   Path: {xynapse.path}")
    
    # 3. Get LSI configuration for pipeline
    print("\n=== LSI Configuration ===")
    lsi_mappings = manager.get_field_mappings("Xynapse Traces")
    
    for field, value in lsi_mappings.items():
        print(f"{field}: {value}")
    
    # 4. Get pipeline configuration
    print("\n=== Pipeline Configuration ===")
    config = manager.get_pipeline_configuration("Xynapse Traces")
    
    # Show important settings
    important_settings = [
        "publisher", "lightning_source_account", "rendition_booktype", 
        "language_code", "territorial_rights", "binding_type"
    ]
    
    for setting in important_settings:
        if setting in config:
            print(f"{setting}: {config[setting]}")
    
    # 5. Show imprint constraints
    print("\n=== Content Constraints ===")
    if xynapse.constraints:
        summary = xynapse.constraints.get_validation_summary()
        print(f"Preferred genres: {summary['preferred_genres']}")
        print(f"Target audiences: {summary['target_audiences']}")
        print(f"Supported languages: {summary['supported_languages']}")
    
    print(f"\n✅ xynapse_traces imprint successfully loaded and ready for use!")
    
    return xynapse

if __name__ == "__main__":
    imprint = main()