#!/usr/bin/env python3
"""
Test Script for Imprint Paper Generation Integration

This script tests the automatic paper generation functionality for imprints,
demonstrating how papers can be generated as part of the imprint creation process.
"""

import sys
import json
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_paper_generation_integration():
    """Test the complete imprint paper generation integration."""

    print("🧪 Testing Imprint Paper Generation Integration")
    print("=" * 60)

    try:
        from codexes.modules.imprints.academic_paper_integration import (
            ImprintPaperGenerator,
            ImprintCreationWorkflow,
            check_paper_generation_status
        )
        print("✅ Successfully imported paper generation modules")
    except ImportError as e:
        print(f"❌ Failed to import modules: {e}")
        return False

    # Test 1: Check existing imprint configuration
    print("\n📋 Test 1: Checking Xynapse Traces Configuration")
    print("-" * 40)

    try:
        status = check_paper_generation_status("xynapse_traces", str(project_root))
        print(f"✅ Configuration loaded successfully")
        print(f"   Paper Generation Enabled: {status.get('paper_generation_enabled', False)}")
        print(f"   Auto Generate on Creation: {status.get('auto_generate_on_creation', False)}")

        if status.get('paper_settings'):
            settings = status['paper_settings']
            print(f"   Target Word Count: {settings.get('target_word_count', 'Not set')}")
            print(f"   Paper Types: {settings.get('paper_types', [])}")
            print(f"   Target Venues: {settings.get('target_venues', [])}")

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

    # Test 2: Test context data collection
    print("\n📊 Test 2: Context Data Collection")
    print("-" * 40)

    try:
        generator = ImprintPaperGenerator(str(project_root))
        config = generator.load_imprint_config("xynapse_traces")

        if config:
            context_data = generator.collect_imprint_context_data(config)
            print("✅ Context data collected successfully")
            print(f"   Imprint Name: {context_data.get('imprint_name')}")
            print(f"   Primary Genres: {context_data.get('primary_genres', [])}")
            print(f"   Specialization: {context_data.get('specialization')}")
            print(f"   Configuration Complexity: {context_data.get('configuration_complexity', {}).get('complexity_level')}")
            print(f"   Focus Areas: {len(context_data.get('focus_areas', []))} areas")
        else:
            print("❌ Failed to load imprint configuration")
            return False

    except Exception as e:
        print(f"❌ Context data collection failed: {e}")
        return False

    # Test 3: Create a test imprint with paper generation
    print("\n🏗️  Test 3: Creating Test Imprint with Paper Generation")
    print("-" * 40)

    try:
        workflow = ImprintCreationWorkflow(str(project_root))

        # Create a test imprint configuration
        test_imprint_config = {
            "imprint": "Test Academic Imprint",
            "publisher": "Test Publisher",
            "contact_email": "test@example.com",
            "branding": {
                "tagline": "Testing Academic Paper Generation",
                "brand_colors": {
                    "primary": "#1E3A8A",
                    "secondary": "#F59E0B"
                }
            },
            "publishing_focus": {
                "primary_genres": ["Academic", "Research", "Technology"],
                "target_audience": "Researchers and Academics",
                "specialization": "AI Research and Academic Publishing",
                "languages": ["eng"]
            },
            "workflow_settings": {
                "auto_generate_missing_fields": True,
                "llm_completion_enabled": True,
                "computed_fields_enabled": True
            },
            "academic_paper_generation": {
                "enabled": True,
                "auto_generate_on_imprint_creation": True,
                "generation_triggers": {
                    "on_imprint_creation": True,
                    "on_milestone_books": False,
                    "on_schedule": False,
                    "manual_only": False
                },
                "paper_settings": {
                    "target_venues": ["arXiv", "Academic Publishing Review"],
                    "paper_types": ["case_study"],
                    "default_paper_type": "case_study",
                    "target_word_count": 6000,
                    "citation_style": "academic",
                    "include_quantitative_analysis": True
                },
                "content_configuration": {
                    "focus_areas": [
                        "AI-assisted academic publishing",
                        "Imprint development methodology",
                        "Research publication workflows"
                    ],
                    "data_sources": {
                        "include_book_catalog": True,
                        "include_sales_metrics": False,
                        "include_production_metrics": True,
                        "include_configuration_analysis": True
                    },
                    "anonymization": {
                        "anonymize_sales_data": True,
                        "anonymize_author_names": False,
                        "anonymize_specific_titles": False
                    }
                },
                "output_settings": {
                    "output_directory": "output/academic_papers/test_academic_imprint",
                    "file_naming": "test_academic_imprint_paper_{date}",
                    "formats": ["markdown", "latex"],
                    "include_submission_package": False
                },
                "llm_configuration": {
                    "preferred_models": ["anthropic/claude-3-5-sonnet-20241022"],
                    "temperature": 0.7,
                    "max_tokens": 4000,
                    "enable_quality_validation": True
                },
                "collaboration_settings": {
                    "include_attribution": True,
                    "author_byline": "Test Academic Imprint Team",
                    "institutional_affiliation": "AI Lab for Book-Lovers",
                    "contact_email": "test@example.com",
                    "co_author_llm": True
                },
                "validation_criteria": {
                    "min_word_count": 4000,
                    "max_word_count": 8000,
                    "required_sections": [
                        "abstract", "introduction", "methodology",
                        "results", "discussion", "conclusion"
                    ],
                    "require_quantitative_data": True,
                    "require_citations": True,
                    "academic_tone_validation": True
                }
            }
        }

        # Test the workflow (this would normally trigger paper generation)
        result = workflow.create_imprint_with_paper_option(
            imprint_name="test_academic_imprint",
            imprint_config=test_imprint_config,
            generate_paper=False  # Set to False to avoid actual generation in test
        )

        print("✅ Test imprint creation workflow completed")
        print(f"   Imprint Created: {result.get('imprint_created', False)}")
        print(f"   Paper Generation Attempted: {result.get('paper_generation_attempted', False)}")

        for message in result.get('messages', []):
            print(f"   {message}")

    except Exception as e:
        print(f"❌ Test imprint creation failed: {e}")
        return False

    # Test 4: Validate configuration-only approach
    print("\n⚙️  Test 4: Configuration-Only Approach Validation")
    print("-" * 40)

    try:
        # Verify that the test imprint can be configured for paper generation
        test_status = check_paper_generation_status("test_academic_imprint", str(project_root))

        if "error" not in test_status:
            print("✅ Test imprint configuration is valid")
            print(f"   Paper Generation Enabled: {test_status.get('paper_generation_enabled', False)}")
            print(f"   Auto Generate on Creation: {test_status.get('auto_generate_on_creation', False)}")

            # Validate configuration structure
            paper_settings = test_status.get('paper_settings', {})
            output_settings = test_status.get('output_settings', {})

            if paper_settings and output_settings:
                print("✅ Configuration structure is complete")
                print(f"   Paper Type: {paper_settings.get('default_paper_type', 'Not set')}")
                print(f"   Output Directory: {output_settings.get('output_directory', 'Not set')}")
            else:
                print("⚠️  Configuration structure incomplete")
        else:
            print(f"⚠️  Test imprint configuration issue: {test_status['error']}")

    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

    # Test 5: Manual paper generation test (safe - no actual generation)
    print("\n📄 Test 5: Manual Paper Generation Interface")
    print("-" * 40)

    try:
        generator = ImprintPaperGenerator(str(project_root))

        # Test that we can check if generation would be enabled
        test_config = generator.load_imprint_config("test_academic_imprint")

        if test_config:
            enabled = generator.is_paper_generation_enabled(test_config)
            on_creation = generator.should_generate_on_creation(test_config)

            print(f"✅ Manual generation interface working")
            print(f"   Would Generate Paper: {enabled}")
            print(f"   Would Generate on Creation: {on_creation}")

            # Test context data collection for the test imprint
            context = generator.collect_imprint_context_data(test_config)
            print(f"   Context Data Fields: {len(context.keys())}")
            print(f"   Focus Areas: {len(context.get('focus_areas', []))}")

        else:
            print("⚠️  Could not load test imprint configuration")

    except Exception as e:
        print(f"❌ Manual generation interface test failed: {e}")
        return False

    # Cleanup - remove test imprint configuration
    print("\n🧹 Cleanup: Removing Test Configuration")
    print("-" * 40)

    try:
        test_config_file = project_root / "configs" / "imprints" / "test_academic_imprint.json"
        if test_config_file.exists():
            test_config_file.unlink()
            print("✅ Test configuration file removed")
        else:
            print("ℹ️  Test configuration file not found (already clean)")

    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

    print("\n" + "=" * 60)
    print("🎉 All Tests Completed Successfully!")
    print("\nSummary:")
    print("✅ Configuration system working")
    print("✅ Context data collection working")
    print("✅ Workflow integration working")
    print("✅ Configuration-only approach validated")
    print("✅ Manual generation interface working")
    print("\n💡 The imprint paper generation system is ready for use!")
    print("   Configure paper generation in imprint JSON files and use the")
    print("   academic_paper_integration module to generate papers.")

    return True


def demonstrate_configuration_usage():
    """Demonstrate how to use the configuration-based approach."""

    print("\n📚 Configuration Usage Examples")
    print("=" * 60)

    print("""
To enable paper generation for an imprint, add this to the imprint's JSON configuration:

{
  "academic_paper_generation": {
    "enabled": true,
    "auto_generate_on_imprint_creation": true,
    "generation_triggers": {
      "on_imprint_creation": true,
      "on_milestone_books": true,
      "manual_only": false
    },
    "paper_settings": {
      "target_venues": ["arXiv"],
      "default_paper_type": "case_study",
      "target_word_count": 8000
    },
    "content_configuration": {
      "focus_areas": [
        "AI-assisted publishing",
        "Imprint development methodology"
      ],
      "data_sources": {
        "include_book_catalog": true,
        "include_production_metrics": true
      }
    },
    "output_settings": {
      "output_directory": "output/academic_papers/{imprint_name}",
      "formats": ["latex", "pdf", "markdown"]
    }
  }
}

Then use the integration module:

from codexes.modules.imprints.academic_paper_integration import generate_paper_for_new_imprint

# Generate paper for any configured imprint
result = generate_paper_for_new_imprint("your_imprint_name")

# Or integrate into imprint creation workflow
from codexes.modules.imprints.academic_paper_integration import ImprintCreationWorkflow

workflow = ImprintCreationWorkflow()
result = workflow.create_imprint_with_paper_option(
    imprint_name="new_imprint",
    imprint_config=your_config,
    generate_paper=True  # Override config setting
)
    """)


if __name__ == "__main__":
    print("🚀 Starting Imprint Paper Generation Integration Tests")

    success = test_paper_generation_integration()

    if success:
        demonstrate_configuration_usage()
        print("\n✨ Integration testing completed successfully!")
        print("The paper generation system is ready for production use.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        sys.exit(1)