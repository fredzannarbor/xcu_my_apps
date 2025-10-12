#!/usr/bin/env python3
"""
Generate Academic Paper for Xynapse Traces Imprint

Simple script to generate an academic paper documenting the AI-assisted
development of the Xynapse Traces imprint.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def main():
    """Generate academic paper for xynapse_traces imprint."""

    print("🚀 Generating Academic Paper for Xynapse Traces Imprint")
    print("=" * 60)

    try:
        from codexes.modules.imprints.academic_paper_integration import generate_paper_for_new_imprintP

        print("📋 Loading xynapse_traces imprint configuration...")
        print("🔍 Collecting context data...")
        print("📄 Generating academic paper...")

        result = generate_paper_for_new_imprint('xynapse_traces')

        if result and result.get('success'):
            print("\n✅ Paper Generated Successfully!")
            print("-" * 40)
            print(f"📁 Output Directory: {result.get('output_directory')}")
            print(f"📄 Imprint: {result.get('imprint_name')}")

            # Show context data used
            context_data = result.get('context_data', {})
            if context_data:
                print(f"🔬 Research Focus: {', '.join(context_data.get('focus_areas', [])[:3])}")
                print(f"📊 Target Word Count: {context_data.get('target_word_count', 'N/A')}")
                print(f"🎯 Paper Type: {context_data.get('paper_type', 'case_study').replace('_', ' ').title()}")

                complexity = context_data.get('configuration_complexity', {})
                if complexity:
                    print(f"⚙️  Configuration Complexity: {complexity.get('complexity_level', 'unknown').title()}")

            print(f"\n📚 Paper Title: 'AI-Assisted Development of Xynapse Traces: A Case Study'")
            print(f"🏛️  Institution: AI Lab for Book-Lovers")
            print(f"📧 Contact: xynapse@nimblebooks.com")

        else:
            error = result.get('error', 'Unknown error') if result else 'Generation failed'
            print(f"\n❌ Paper Generation Failed")
            print("-" * 40)
            print(f"Error: {error}")

            if result and result.get('context_data'):
                print(f"\nℹ️  Context data was collected successfully:")
                context = result.get('context_data', {})
                print(f"   Imprint: {context.get('imprint_name', 'N/A')}")
                print(f"   Specialization: {context.get('specialization', 'N/A')}")
                print("   The error occurred during paper generation, not data collection.")

    except ImportError as e:
        print(f"\n❌ Import Error")
        print("-" * 40)
        print(f"Could not import paper generation module: {e}")
        print("Make sure the arxiv-writer integration is properly set up.")

    except FileNotFoundError as e:
        print(f"\n❌ Configuration Error")
        print("-" * 40)
        print(f"Xynapse Traces configuration not found: {e}")
        print("Make sure configs/imprints/xynapse_traces.json exists.")

    except Exception as e:
        print(f"\n❌ Unexpected Error")
        print("-" * 40)
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")

        # Show some debug info
        print(f"\nDebug Information:")
        print(f"   Python path: {sys.path[0]}")
        print(f"   Working directory: {Path.cwd()}")
        print(f"   Project root: {project_root}")

if __name__ == "__main__":
    main()