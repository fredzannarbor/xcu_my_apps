#!/usr/bin/env python3
"""
Example script showing how to load and use the xynapse_traces imprint
with the new imprint management architecture.
"""

from src.codexes.modules.imprints.services.imprint_manager import ImprintManager

def main():
    # Initialize the imprint manager
    print("🔧 Initializing Imprint Manager...")
    manager = ImprintManager()
    
    # Load the xynapse_traces imprint
    print("📖 Loading xynapse_traces imprint...")
    xynapse = manager.get_imprint("Xynapse Traces")
    
    if not xynapse:
        print("❌ xynapse_traces imprint not found!")
        return
    
    print(f"✅ Successfully loaded: {xynapse.name}")
    print(f"   Publisher: {xynapse.publisher}")
    print(f"   Status: {xynapse.status.value}")
    print(f"   Total books: {xynapse.metrics.total_books}")
    
    # Example 1: Get pipeline configuration for book production
    print("\n📋 Getting pipeline configuration...")
    pipeline_config = manager.get_pipeline_configuration("Xynapse Traces", context="general")
    
    print("Key pipeline settings:")
    important_keys = ["lightning_source_account", "rendition_booktype", "language_code", 
                     "territorial_rights", "publisher"]
    for key in important_keys:
        if key in pipeline_config:
            print(f"   {key}: {pipeline_config[key]}")
    
    # Example 2: Get LSI field mappings for distribution
    print("\n🏭 Getting LSI field mappings...")
    lsi_mappings = manager.get_field_mappings("Xynapse Traces")
    
    print("LSI field mappings:")
    for field, value in lsi_mappings.items():
        print(f"   {field}: {value}")
    
    # Example 3: Validate sample content against imprint constraints
    print("\n✅ Validating sample content...")
    sample_content = {
        "title": "AI and the Future of Scientific Discovery", 
        "genre": "Technology",
        "target_audience": "Academic and Professional",
        "language": "eng",
        "word_count": 75000,
        "imprint": "Xynapse Traces"
    }
    
    validation = manager.validate_content_for_imprint("Xynapse Traces", sample_content)
    
    print(f"Content validation result: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
    if validation.get("warnings"):
        print("Warnings:")
        for warning in validation["warnings"]:
            print(f"   ⚠️ {warning}")
    if validation.get("errors"):
        print("Errors:")
        for error in validation["errors"]:
            print(f"   ❌ {error}")
    
    # Example 4: Apply imprint settings to content
    print("\n🎨 Applying imprint settings to content...")
    enhanced_content = manager.apply_imprint_to_content("Xynapse Traces", sample_content.copy())
    
    print("Enhanced content with imprint settings:")
    new_keys = set(enhanced_content.keys()) - set(sample_content.keys())
    for key in sorted(new_keys):
        print(f"   {key}: {enhanced_content[key]}")
    
    # Example 5: Get imprint validation status
    print("\n🔍 Validating imprint setup...")
    imprint_validation = manager.validate_imprint("Xynapse Traces")
    
    print(f"Imprint validation: {'✅ Valid' if imprint_validation['overall_valid'] else '❌ Invalid'}")
    if imprint_validation.get("warnings"):
        print("Setup warnings:")
        for warning in imprint_validation["warnings"]:
            print(f"   ⚠️ {warning}")
    
    # Example 6: Access specific components
    print("\n🔧 Accessing specific components...")
    
    if xynapse.configuration:
        print("Configuration:")
        config = xynapse.configuration.get_resolved_config()
        print(f"   Total settings: {len(config)}")
        print(f"   Lightning Source Account: {config.get('lightning_source_account', 'Not set')}")
    
    if xynapse.assets:
        print("Assets:")
        print(f"   Total assets: {len(xynapse.assets.assets)}")
        print(f"   Interior template: {'✅' if xynapse.assets.get_interior_template_path() else '❌'}")
        print(f"   Cover template: {'✅' if xynapse.assets.get_cover_template_path() else '❌'}")
    
    if xynapse.constraints:
        print("Content constraints:")
        summary = xynapse.constraints.get_validation_summary()
        print(f"   Active constraints: {summary['active_constraints']}")
        print(f"   Preferred genres: {', '.join(summary['preferred_genres'])}")
    
    print("\n🎉 Example complete! The xynapse_traces imprint is ready for use.")


if __name__ == "__main__":
    main()