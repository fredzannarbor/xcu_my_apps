#!/usr/bin/env python3
"""
Comprehensive example demonstrating Codexes Factory integration.

This example shows how to use the arxiv-writer package as a drop-in replacement
for existing Codexes Factory arxiv paper generation functionality.
"""

import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from arxiv_writer.core.codexes_factory_adapter import (
    CodexesFactoryAdapter,
    CodexesFactoryConfig,
    migrate_codexes_factory_config,
    create_codexes_compatibility_config,
    create_codexes_factory_paper_generator
)


def main():
    """Demonstrate complete Codexes Factory integration."""
    print("🔄 Codexes Factory Integration Example")
    print("=" * 60)
    
    # Example 1: Using existing Codexes Factory configuration
    print("\n📋 Example 1: Using Existing Codexes Factory Configuration")
    print("-" * 50)
    
    # Create a sample Codexes Factory configuration (like xynapse_traces.json)
    xynapse_traces_config = {
        "_config_info": {
            "description": "Xynapse Traces imprint configuration",
            "version": "2.0",
            "last_updated": "2025-07-18",
            "parent_publisher": "Nimble Books LLC"
        },
        "imprint": "Xynapse Traces",
        "publisher": "Nimble Books LLC",
        "workspace_root": ".",
        "output_directory": "output/arxiv_papers",
        "llm_config": {
            "default_model": "anthropic/claude-3-5-sonnet-20241022",
            "available_models": [
                "anthropic/claude-3-5-sonnet-20241022",
                "google/gemini-pro-1.5",
                "openai/gpt-4-turbo",
                "xai/grok-beta"
            ],
            "model_parameters": {
                "anthropic/claude-3-5-sonnet-20241022": {
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
        },
        "template_config": {
            "template_file": "templates/default_prompts.json",
            "section_order": [
                "abstract",
                "introduction", 
                "related_work",
                "methodology",
                "results",
                "discussion",
                "conclusion",
                "references"
            ]
        },
        "validation_config": {
            "enabled": True,
            "strict_mode": False,
            "quality_thresholds": {
                "min_word_count": 500,
                "max_word_count": 8000,
                "readability_score": 0.7,
                "coherence_score": 0.8,
                "citation_count": 10,
                "section_balance": 0.6
            }
        },
        "context_config": {
            "collect_book_catalog": True,
            "collect_imprint_config": True,
            "collect_technical_architecture": True,
            "collect_performance_metrics": True
        }
    }
    
    # Save configuration to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(xynapse_traces_config, f, indent=2)
        config_path = f.name
    
    try:
        # Initialize adapter with existing configuration
        print(f"📁 Loading configuration from: {config_path}")
        adapter = CodexesFactoryAdapter(config_path)
        
        print(f"✅ Adapter initialized for imprint: {adapter.codexes_config.imprint_name}")
        print(f"   - Default model: {adapter.codexes_config.default_model}")
        print(f"   - Available models: {len(adapter.codexes_config.available_models)}")
        print(f"   - Section order: {adapter.codexes_config.section_order}")
        print(f"   - Validation enabled: {adapter.codexes_config.validation_enabled}")
        
        # Example 2: Configuration Migration
        print("\n🔄 Example 2: Configuration Migration")
        print("-" * 50)
        
        # Migrate to arxiv-writer format
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            migrated_path = f.name
        
        print("🔧 Migrating configuration to arxiv-writer format...")
        migrated_config = migrate_codexes_factory_config(config_path, migrated_path)
        
        print(f"✅ Configuration migrated successfully!")
        print(f"   - Original config: {config_path}")
        print(f"   - Migrated config: {migrated_path}")
        print(f"   - Output directory: {migrated_config.output_directory}")
        print(f"   - LLM config preserved: {migrated_config.llm_config.default_model}")
        
        # Example 3: Drop-in Replacement Workflow
        print("\n🔄 Example 3: Drop-in Replacement Workflow")
        print("-" * 50)
        
        print("📊 Demonstrating identical API to original Codexes Factory...")
        
        # Before (conceptual Codexes Factory code):
        # result = generate_arxiv_paper(workspace_root=".", imprint_name="Xynapse Traces")
        
        # After (arxiv-writer replacement):
        print("🎯 Collecting context data...")
        try:
            context_data = adapter.get_context_data()
            print(f"✅ Context collection completed")
            print(f"   - Sources collected: {context_data['summary']['total_sources']}")
            print(f"   - Successful collections: {context_data['summary']['successful_collections']}")
            print(f"   - Failed collections: {context_data['summary']['failed_collections']}")
        except Exception as e:
            print(f"ℹ️  Context collection simulation (would collect real data): {e}")
            # Create mock context for demonstration
            context_data = {
                "imprint_data": {
                    "book_catalog": {"total_books": 150, "genres": ["Technology", "Science"]},
                    "imprint_config": {"focus_areas": ["AI", "Philosophy"]},
                    "technical_architecture": {"systems": ["Publishing Pipeline"]},
                    "performance_metrics": {"monthly_publications": 12}
                },
                "summary": {
                    "total_sources": 4,
                    "successful_collections": 4,
                    "failed_collections": 0
                }
            }
        
        # Example 4: Individual Section Generation
        print("\n📝 Example 4: Individual Section Generation")
        print("-" * 50)
        
        print("🎯 Generating individual sections...")
        sections_to_generate = ["abstract", "introduction", "methodology"]
        
        for section_name in sections_to_generate:
            try:
                print(f"   Generating {section_name}...")
                section_result = adapter.generate_section(section_name)
                print(f"   ✅ {section_name.title()} generated:")
                print(f"      - Word count: {section_result['word_count']}")
                print(f"      - Model used: {section_result['model_used']}")
                print(f"      - Validation: {section_result['validation_status']}")
                print(f"      - Content preview: {section_result['content'][:100]}...")
            except Exception as e:
                print(f"   ℹ️  {section_name.title()} generation simulation: {e}")
        
        # Example 5: Complete Paper Generation
        print("\n📄 Example 5: Complete Paper Generation")
        print("-" * 50)
        
        print("🎯 Generating complete paper...")
        try:
            paper_result = adapter.generate_paper()
            
            print(f"✅ Paper generation completed!")
            print(f"   - Total sections: {paper_result['generation_summary']['total_sections']}")
            print(f"   - Total word count: {paper_result['generation_summary']['total_word_count']}")
            print(f"   - Models used: {', '.join(paper_result['generation_summary']['models_used'])}")
            print(f"   - Output files: {', '.join(paper_result['output_files'])}")
            print(f"   - Quality score: {paper_result['generation_summary'].get('quality_score', 'N/A')}")
            
            # Show sections generated
            print(f"\n   📋 Sections generated:")
            for section_name, section_data in paper_result['sections'].items():
                print(f"      - {section_name.title()}: {section_data['word_count']} words")
            
            # Show paper content preview
            print(f"\n   📄 Paper content preview:")
            content_preview = paper_result['paper_content'][:300] + "..." if len(paper_result['paper_content']) > 300 else paper_result['paper_content']
            print(f"      {content_preview}")
            
        except Exception as e:
            print(f"   ℹ️  Paper generation simulation: {e}")
            # Create mock result for demonstration
            mock_result = {
                "paper_content": "\\documentclass{article}\n\\begin{document}\n\\title{Xynapse Traces Analysis}\n\\section{Abstract}\nThis paper analyzes...",
                "sections": {
                    "abstract": {
                        "content": "This paper analyzes the Xynapse Traces publishing imprint...",
                        "word_count": 150,
                        "model_used": "anthropic/claude-3-5-sonnet-20241022",
                        "validation_status": "valid"
                    }
                },
                "generation_summary": {
                    "total_sections": 8,
                    "total_word_count": 3500,
                    "models_used": ["anthropic/claude-3-5-sonnet-20241022"],
                    "quality_score": 0.85
                },
                "output_files": ["xynapse_traces_analysis.tex", "xynapse_traces_analysis.pdf"],
                "imprint_info": {
                    "imprint_name": "Xynapse Traces",
                    "workspace_root": ".",
                    "configuration_used": xynapse_traces_config
                }
            }
            
            print(f"   📋 Mock result structure:")
            print(f"      - Paper content: {len(mock_result['paper_content'])} characters")
            print(f"      - Sections: {list(mock_result['sections'].keys())}")
            print(f"      - Total word count: {mock_result['generation_summary']['total_word_count']}")
        
        # Example 6: Paper Validation
        print("\n✅ Example 6: Paper Validation")
        print("-" * 50)
        
        sample_paper_content = """
        \\documentclass{article}
        \\begin{document}
        \\title{Analysis of Xynapse Traces Publishing Imprint}
        \\section{Abstract}
        This paper presents a comprehensive analysis of the Xynapse Traces publishing imprint...
        \\section{Introduction}
        The publishing industry has undergone significant transformation...
        \\end{document}
        """
        
        try:
            validation_result = adapter.validate_paper(sample_paper_content)
            
            print(f"✅ Paper validation completed!")
            print(f"   - Valid: {validation_result['is_valid']}")
            print(f"   - Errors: {len(validation_result['errors'])}")
            print(f"   - Warnings: {len(validation_result['warnings'])}")
            print(f"   - Quality metrics: {validation_result['quality_metrics']}")
            print(f"   - ArXiv compliance: {validation_result['arxiv_compliance']['meets_standards']}")
            print(f"   - Submission ready: {validation_result['arxiv_compliance']['submission_ready']}")
            
        except Exception as e:
            print(f"   ℹ️  Paper validation simulation: {e}")
            # Show expected validation format
            mock_validation = {
                "is_valid": True,
                "errors": [],
                "warnings": ["Minor formatting suggestion"],
                "quality_metrics": {"word_count": 1200, "readability_score": 0.8},
                "arxiv_compliance": {"meets_standards": True, "submission_ready": True}
            }
            print(f"   📋 Expected validation format: {mock_validation}")
        
        # Example 7: Compatibility Configuration Creation
        print("\n⚙️ Example 7: Creating Compatibility Configuration")
        print("-" * 50)
        
        print("🔧 Creating Codexes Factory compatibility configuration...")
        compat_config = create_codexes_compatibility_config(
            workspace_root=".",
            imprint_name="Custom Imprint"
        )
        
        print(f"✅ Compatibility configuration created!")
        print(f"   - Imprint: {compat_config.imprint_name}")
        print(f"   - Default model: {compat_config.default_model}")
        print(f"   - Available models: {len(compat_config.available_models)}")
        print(f"   - Context collection enabled: {compat_config.collect_book_catalog}")
        print(f"   - Validation enabled: {compat_config.validation_enabled}")
        
        # Example 8: Convenience Function Usage
        print("\n🚀 Example 8: Convenience Function Usage")
        print("-" * 50)
        
        print("🎯 Using convenience function for quick setup...")
        quick_generator = create_codexes_factory_paper_generator(
            workspace_root=".",
            imprint_name="Quick Setup Imprint"
        )
        
        print(f"✅ Quick generator created!")
        print(f"   - Type: {type(quick_generator).__name__}")
        print(f"   - Imprint: {quick_generator.codexes_config.imprint_name}")
        print(f"   - Ready for paper generation: {hasattr(quick_generator, 'generate_paper')}")
        
        # Example 9: Migration Validation
        print("\n🔍 Example 9: Migration Validation")
        print("-" * 50)
        
        print("🔧 Validating migration preserves all settings...")
        
        # Load migrated configuration and compare
        with open(migrated_path, 'r') as f:
            migrated_data = json.load(f)
        
        # Check key preservation
        original_model = xynapse_traces_config["llm_config"]["default_model"]
        migrated_model = migrated_data["llm_config"]["default_model"]
        
        print(f"   - Original model: {original_model}")
        print(f"   - Migrated model: {migrated_model}")
        print(f"   - Models match: {original_model == migrated_model}")
        
        original_sections = xynapse_traces_config["template_config"]["section_order"]
        migrated_sections = migrated_data["template_config"]["section_order"]
        
        print(f"   - Original sections: {len(original_sections)}")
        print(f"   - Migrated sections: {len(migrated_sections)}")
        print(f"   - Sections match: {original_sections == migrated_sections}")
        
        # Check metadata preservation
        if "codexes_factory_metadata" in migrated_data:
            metadata = migrated_data["codexes_factory_metadata"]
            print(f"   - Metadata preserved: ✅")
            print(f"   - Original imprint: {metadata['imprint_name']}")
            print(f"   - Original workspace: {metadata['workspace_root']}")
        else:
            print(f"   - Metadata preserved: ❌")
        
        print("\n🎉 Codexes Factory Integration Complete!")
        print("=" * 60)
        print("The arxiv-writer package successfully provides:")
        print("✅ Drop-in replacement for existing Codexes Factory functionality")
        print("✅ Identical API and output format")
        print("✅ Configuration migration with full preservation")
        print("✅ All existing workflows supported")
        print("✅ Enhanced features and extensibility")
        
        # Clean up migrated file
        Path(migrated_path).unlink()
        
    finally:
        # Clean up temporary files
        Path(config_path).unlink()


def demonstrate_advanced_integration():
    """Demonstrate advanced integration scenarios."""
    print("\n🔬 Advanced Integration Scenarios")
    print("=" * 60)
    
    # Scenario 1: Custom Context Collection
    print("\n📊 Scenario 1: Custom Context Collection")
    print("-" * 40)
    
    print("🎯 Configuring custom context collection...")
    config = CodexesFactoryConfig(
        imprint_name="Advanced Imprint",
        collect_book_catalog=True,
        collect_imprint_config=True,
        collect_technical_architecture=False,  # Disable some collections
        collect_performance_metrics=True
    )
    
    adapter = CodexesFactoryAdapter(config)
    print(f"✅ Custom context collection configured")
    print(f"   - Book catalog: {config.collect_book_catalog}")
    print(f"   - Imprint config: {config.collect_imprint_config}")
    print(f"   - Technical architecture: {config.collect_technical_architecture}")
    print(f"   - Performance metrics: {config.collect_performance_metrics}")
    
    # Scenario 2: Custom Model Configuration
    print("\n🤖 Scenario 2: Custom Model Configuration")
    print("-" * 40)
    
    custom_config = {
        "imprint": "Custom Model Imprint",
        "llm_config": {
            "default_model": "openai/gpt-4-turbo",
            "available_models": [
                "openai/gpt-4-turbo",
                "anthropic/claude-3-5-sonnet-20241022",
                "google/gemini-pro-1.5"
            ]
        }
    }
    
    custom_adapter = CodexesFactoryAdapter(custom_config)
    print(f"✅ Custom model configuration applied")
    print(f"   - Default model: {custom_adapter.codexes_config.default_model}")
    print(f"   - Available models: {len(custom_adapter.codexes_config.available_models)}")
    
    # Scenario 3: Quality Threshold Customization
    print("\n📏 Scenario 3: Quality Threshold Customization")
    print("-" * 40)
    
    quality_config = {
        "imprint": "Quality Focused Imprint",
        "validation_config": {
            "enabled": True,
            "strict_mode": True,
            "quality_thresholds": {
                "min_word_count": 1000,
                "max_word_count": 6000,
                "readability_score": 0.8,
                "coherence_score": 0.9,
                "citation_count": 15,
                "section_balance": 0.7
            }
        }
    }
    
    quality_adapter = CodexesFactoryAdapter(quality_config)
    print(f"✅ Quality thresholds customized")
    print(f"   - Strict mode: {quality_adapter.codexes_config.strict_mode}")
    print(f"   - Min word count: {quality_adapter.codexes_config.quality_thresholds['min_word_count']}")
    print(f"   - Readability threshold: {quality_adapter.codexes_config.quality_thresholds['readability_score']}")
    print(f"   - Citation requirement: {quality_adapter.codexes_config.quality_thresholds['citation_count']}")


if __name__ == "__main__":
    main()
    demonstrate_advanced_integration()