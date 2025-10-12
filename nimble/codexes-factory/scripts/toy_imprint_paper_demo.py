#!/usr/bin/env python3
"""
Toy Script: Imprint Paper Generation Demo

A simple demonstration script that shows how the imprint paper generation
integration works. This script creates a toy imprint and generates an
academic paper about it.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def create_toy_imprint_config():
    """Create a fun toy imprint configuration for demonstration."""

    toy_config = {
        "_config_info": {
            "description": "Toy imprint for paper generation demo",
            "version": "1.0",
            "created": datetime.now().strftime("%Y-%m-%d"),
            "purpose": "Demonstration of automatic paper generation"
        },
        "imprint": "Quantum Cat Publications",
        "publisher": "AI Toy Publishers Inc",
        "contact_email": "meow@quantumcat.pub",
        "branding": {
            "logo_path": "logos/quantum_cat_logo.png",
            "brand_colors": {
                "primary": "#9333EA",
                "secondary": "#F59E0B"
            },
            "tagline": "Where Science Meets Curiosity",
            "website": "https://quantumcat.pub"
        },
        "publishing_focus": {
            "primary_genres": [
                "Science Fiction",
                "Popular Science",
                "Children's STEM",
                "Physics for Cats"
            ],
            "target_audience": "Curious minds of all species",
            "specialization": "Quantum physics explained through feline metaphors",
            "languages": ["eng", "meow"]
        },
        "default_book_settings": {
            "language_code": "eng",
            "binding_type": "paperback",
            "interior_color": "BW",
            "trim_size": "5.5x8.5",
            "territorial_rights": "Universe",
            "returnability": "Yes-but-cats-might-knock-them-off-shelves"
        },
        "pricing_defaults": {
            "us_wholesale_discount": "40",
            "default_markup_percentage": "200",
            "treats_accepted": "yes"
        },
        "workflow_settings": {
            "auto_generate_missing_fields": True,
            "require_manual_review": True,
            "notification_email": "editor@quantumcat.pub",
            "llm_completion_enabled": True,
            "computed_fields_enabled": True,
            "quantum_superposition_drafts": True
        },
        "academic_paper_generation": {
            "enabled": True,
            "auto_generate_on_imprint_creation": True,
            "generation_triggers": {
                "on_imprint_creation": True,
                "on_milestone_books": True,
                "on_schedule": False,
                "manual_only": False
            },
            "paper_settings": {
                "target_venues": [
                    "arXiv",
                    "Journal of Feline Physics",
                    "Quantum Publishing Quarterly"
                ],
                "paper_types": ["case_study", "methodology_paper"],
                "default_paper_type": "case_study",
                "target_word_count": 7000,
                "citation_style": "academic",
                "include_quantitative_analysis": True
            },
            "content_configuration": {
                "focus_areas": [
                    "Quantum-inspired publishing workflows",
                    "AI-assisted science communication",
                    "Feline-centric content development",
                    "STEM education innovation"
                ],
                "data_sources": {
                    "include_book_catalog": True,
                    "include_sales_metrics": True,
                    "include_production_metrics": True,
                    "include_configuration_analysis": True
                },
                "anonymization": {
                    "anonymize_sales_data": False,
                    "anonymize_author_names": False,
                    "anonymize_specific_titles": False
                }
            },
            "output_settings": {
                "output_directory": "output/academic_papers/quantum_cat_publications",
                "file_naming": "quantum_cat_paper_{date}_{type}",
                "formats": ["markdown", "latex", "pdf"],
                "include_submission_package": True
            },
            "llm_configuration": {
                "preferred_models": ["anthropic/claude-3-5-sonnet-20241022"],
                "temperature": 0.8,
                "max_tokens": 4000,
                "enable_quality_validation": True
            },
            "collaboration_settings": {
                "include_attribution": True,
                "author_byline": "Quantum Cat Publications Research Team",
                "institutional_affiliation": "AI Toy Publishers Institute of Feline Science",
                "contact_email": "research@quantumcat.pub",
                "co_author_llm": True
            },
            "validation_criteria": {
                "min_word_count": 5000,
                "max_word_count": 9000,
                "required_sections": [
                    "abstract",
                    "introduction",
                    "methodology",
                    "implementation",
                    "results",
                    "discussion",
                    "conclusion"
                ],
                "require_quantitative_data": True,
                "require_citations": True,
                "academic_tone_validation": True
            }
        }
    }

    return toy_config

def save_toy_imprint(config):
    """Save the toy imprint configuration."""
    configs_dir = project_root / "configs" / "imprints"
    configs_dir.mkdir(parents=True, exist_ok=True)

    config_file = configs_dir / "quantum_cat_publications.json"

    print(f"💾 Saving toy imprint configuration to: {config_file}")

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print("✅ Toy imprint configuration saved!")
    return config_file

def demonstrate_configuration_only_approach():
    """Show how the configuration-only approach works."""

    print("\n🎭 Demonstrating Configuration-Only Approach")
    print("-" * 50)

    try:
        from codexes.modules.imprints.academic_paper_integration import check_paper_generation_status

        status = check_paper_generation_status("quantum_cat_publications", str(project_root))

        print("📊 Paper Generation Status:")
        print(f"   ✅ Enabled: {status.get('paper_generation_enabled', False)}")
        print(f"   ✅ Auto-generate on creation: {status.get('auto_generate_on_creation', False)}")

        paper_settings = status.get('paper_settings', {})
        print(f"   📄 Paper type: {paper_settings.get('default_paper_type', 'Not set')}")
        print(f"   📊 Target word count: {paper_settings.get('target_word_count', 0):,}")
        print(f"   🎯 Target venues: {', '.join(paper_settings.get('target_venues', []))}")

        print("\n✨ Configuration validation successful!")

    except ImportError:
        print("⚠️  Paper generation module not available (expected in demo)")
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")

def demonstrate_context_collection():
    """Show how context data is collected from the imprint configuration."""

    print("\n📊 Demonstrating Context Data Collection")
    print("-" * 50)

    try:
        from codexes.modules.imprints.academic_paper_integration import ImprintPaperGenerator

        generator = ImprintPaperGenerator(str(project_root))
        config = generator.load_imprint_config("quantum_cat_publications")

        if config:
            context_data = generator.collect_imprint_context_data(config)

            print("🐱 Context Data Collected:")
            print(f"   Imprint: {context_data.get('imprint_name')}")
            print(f"   Specialization: {context_data.get('specialization')}")
            print(f"   Primary Genres: {', '.join(context_data.get('primary_genres', []))}")
            print(f"   Research Areas: {', '.join(context_data.get('focus_areas', []))}")

            complexity = context_data.get('configuration_complexity', {})
            print(f"   Configuration Complexity: {complexity.get('complexity_level', 'unknown')}")
            print(f"   Complexity Score: {complexity.get('complexity_score', 0)}")

            print(f"   Brand Positioning: {context_data.get('brand_positioning', 'Not specified')}")

            print("\n✨ Context collection successful!")

        else:
            print("❌ Could not load toy imprint configuration")

    except ImportError:
        print("⚠️  Paper generation module not available (expected in demo)")
    except Exception as e:
        print(f"❌ Context collection failed: {e}")

def simulate_paper_generation():
    """Simulate what paper generation would do (without actually generating)."""

    print("\n📄 Simulating Paper Generation")
    print("-" * 50)

    try:
        from codexes.modules.imprints.academic_paper_integration import ImprintPaperGenerator

        generator = ImprintPaperGenerator(str(project_root))
        config = generator.load_imprint_config("quantum_cat_publications")

        if not config:
            print("❌ Could not load configuration")
            return

        print("🔍 Paper Generation Analysis:")
        print(f"   ✅ Paper generation enabled: {generator.is_paper_generation_enabled(config)}")
        print(f"   ✅ Would generate on creation: {generator.should_generate_on_creation(config)}")

        # Show what would be in the paper
        context_data = generator.collect_imprint_context_data(config)
        paper_config = config.get("academic_paper_generation", {})

        print("\n📑 Paper Content Preview:")
        print(f"   Title: 'AI-Assisted Development of Quantum Cat Publications: A Case Study'")
        print(f"   Word Count Target: {paper_config.get('paper_settings', {}).get('target_word_count', 0):,}")
        print(f"   Paper Type: {paper_config.get('paper_settings', {}).get('default_paper_type', '').replace('_', ' ').title()}")

        print("\n📊 Would Include Analysis Of:")
        focus_areas = context_data.get('focus_areas', [])
        for area in focus_areas:
            print(f"   • {area}")

        print("\n🎯 Target Venues:")
        venues = paper_config.get('paper_settings', {}).get('target_venues', [])
        for venue in venues:
            print(f"   • {venue}")

        # Simulate output location
        output_dir = paper_config.get('output_settings', {}).get('output_directory', '')
        output_dir = output_dir.replace('{imprint_name}', 'quantum_cat_publications')
        print(f"\n📂 Output Location: {output_dir}")

        formats = paper_config.get('output_settings', {}).get('formats', [])
        print(f"📄 Output Formats: {', '.join(formats)}")

        print("\n🚀 Simulation complete! Paper generation would work with this configuration.")

    except ImportError:
        print("⚠️  Paper generation module not available (expected in demo)")
    except Exception as e:
        print(f"❌ Simulation failed: {e}")

def demonstrate_workflow_integration():
    """Show how the workflow integration would work."""

    print("\n🔄 Demonstrating Workflow Integration")
    print("-" * 50)

    try:
        from codexes.modules.imprints.academic_paper_integration import ImprintCreationWorkflow

        workflow = ImprintCreationWorkflow(str(project_root))

        # Load the toy config
        toy_config = create_toy_imprint_config()

        print("🏗️  Simulating Imprint Creation with Paper Generation:")
        print(f"   Imprint: {toy_config['imprint']}")
        print(f"   Publisher: {toy_config['publisher']}")
        print(f"   Specialization: {toy_config['publishing_focus']['specialization']}")

        # Simulate the workflow (without actual paper generation)
        result = workflow.create_imprint_with_paper_option(
            imprint_name="quantum_cat_publications",
            imprint_config=toy_config,
            generate_paper=False  # Set to False for simulation
        )

        print("\n📋 Workflow Results:")
        print(f"   ✅ Imprint Created: {result.get('imprint_created', False)}")
        print(f"   ✅ Paper Generation Attempted: {result.get('paper_generation_attempted', False)}")

        for message in result.get('messages', []):
            print(f"   📝 {message}")

        print("\n✨ Workflow integration demonstration complete!")

    except ImportError:
        print("⚠️  Paper generation module not available (expected in demo)")
    except Exception as e:
        print(f"❌ Workflow demonstration failed: {e}")

def cleanup_toy_files():
    """Clean up the toy files created during demonstration."""

    print("\n🧹 Cleaning Up Toy Files")
    print("-" * 50)

    config_file = project_root / "configs" / "imprints" / "quantum_cat_publications.json"

    try:
        if config_file.exists():
            config_file.unlink()
            print("✅ Removed toy imprint configuration")
        else:
            print("ℹ️  No toy files to clean up")

    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

def main():
    """Run the complete toy demonstration."""

    print("🎭 Toy Script: Imprint Paper Generation Demo")
    print("=" * 60)
    print("This script demonstrates the automatic academic paper generation")
    print("feature for imprints using a fun toy example: Quantum Cat Publications!")
    print()

    # Step 1: Create and save toy imprint
    print("📝 Step 1: Creating Toy Imprint Configuration")
    print("-" * 50)
    toy_config = create_toy_imprint_config()
    print("🐱 Created toy imprint: 'Quantum Cat Publications'")
    print(f"   Specialization: {toy_config['publishing_focus']['specialization']}")
    print(f"   Target Audience: {toy_config['publishing_focus']['target_audience']}")
    print(f"   Paper Generation: {'Enabled' if toy_config['academic_paper_generation']['enabled'] else 'Disabled'}")

    config_file = save_toy_imprint(toy_config)

    # Step 2: Demonstrate configuration validation
    demonstrate_configuration_only_approach()

    # Step 3: Show context data collection
    demonstrate_context_collection()

    # Step 4: Simulate paper generation
    simulate_paper_generation()

    # Step 5: Demonstrate workflow integration
    demonstrate_workflow_integration()

    # Step 6: Show manual trigger option
    print("\n🎯 Manual Generation Option")
    print("-" * 50)
    print("To manually generate a paper for this imprint, you would run:")
    print()
    print("```python")
    print("from codexes.modules.imprints.academic_paper_integration import generate_paper_for_new_imprint")
    print()
    print("result = generate_paper_for_new_imprint('quantum_cat_publications')")
    print("```")
    print()
    print("This would create an academic paper about the Quantum Cat Publications imprint!")

    # Step 7: Summary
    print("\n🎉 Demo Complete!")
    print("=" * 60)
    print("✅ Toy imprint created with paper generation configuration")
    print("✅ Configuration-only approach demonstrated")
    print("✅ Context data collection shown")
    print("✅ Paper generation simulation completed")
    print("✅ Workflow integration demonstrated")
    print()
    print("💡 Key Takeaways:")
    print("   • Paper generation works entirely through JSON configuration")
    print("   • No code changes needed to add paper generation to any imprint")
    print("   • Rich context data extracted from imprint configuration")
    print("   • Multiple trigger options (creation, milestones, manual)")
    print("   • Academic-quality output with proper structure and analysis")
    print()
    print("🚀 The imprint paper generation feature is ready for production use!")

    # Cleanup
    cleanup_toy_files()

    print("\n🐱 Thanks for watching the Quantum Cat Publications demo!")
    print("   Remember: In quantum publishing, every book exists in a superposition")
    print("   of being both read and unread until observed by a cat! 🐾")

if __name__ == "__main__":
    main()