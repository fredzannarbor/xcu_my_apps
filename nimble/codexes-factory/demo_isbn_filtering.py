#!/usr/bin/env python3
"""
Demo: ISBN Filtering for Rights Offering Sheets
"""

from pathlib import Path

# Import rights management modules
try:
    from codexes.modules.rights_management import generate_imprint_rights_sheet
except ImportError:
    import sys
    sys.path.append('src')
    from codexes.modules.rights_management import generate_imprint_rights_sheet

def main():
    """Demonstrate ISBN filtering functionality."""

    print("🧪 Demo: ISBN Filtering for Rights Offering Sheets")
    print("=" * 60)
    print("This demo shows how to generate focused rights offering sheets")
    print("by filtering on specific ISBNs for targeted marketing campaigns.")
    print("=" * 60)

    # Xynapse Traces configuration path
    config_path = Path("configs/imprints/xynapse_traces.json")
    output_dir = Path("output/rights_offerings/xynapse_traces")

    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return

    # Demo scenarios
    scenarios = [
        {
            "name": "Full Catalog",
            "description": "Generate complete rights offering with all titles",
            "isbn_filter": None
        },
        {
            "name": "Targeted Campaign",
            "description": "Focus on 2-3 specific titles for targeted marketing",
            "isbn_filter": "9781608883653,9781608883660"  # Available ISBNs
        },
        {
            "name": "Single Title Focus",
            "description": "Highlight one specific title",
            "isbn_filter": "9781608883660"  # Single ISBN
        }
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 Scenario {i}: {scenario['name']}")
        print(f"📝 {scenario['description']}")

        if scenario['isbn_filter']:
            print(f"🔍 ISBN Filter: {scenario['isbn_filter']}")
        else:
            print("📚 No filter - full catalog")

        try:
            # Generate rights offering sheet
            result = generate_imprint_rights_sheet(
                imprint_config_path=str(config_path),
                output_dir=str(output_dir),
                isbn_filter=scenario['isbn_filter']
            )

            if result:
                result_path = Path(result)
                file_size = result_path.stat().st_size if result_path.exists() else 0

                print(f"✅ Generated: {result_path.name}")
                print(f"📏 Size: {file_size:,} bytes")

                if scenario['isbn_filter']:
                    print(f"🎯 Filtered catalog contains only matching titles")
                else:
                    print(f"📖 Full catalog with all available titles")
            else:
                print(f"❌ Failed to generate (no matching ISBNs found)")

        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n🎉 Demo Complete!")
    print(f"\n💡 Usage Tips:")
    print(f"   • Use ISBN filtering for focused rights campaigns")
    print(f"   • Multiple ISBNs: '123,456,789' (comma-separated)")
    print(f"   • Single ISBN: '123456789'")
    print(f"   • Hyphens and spaces are automatically cleaned")
    print(f"   • Both 'isbn' and 'isbn13' fields are checked")

    print(f"\n📂 Output files saved to: {output_dir}")

if __name__ == "__main__":
    main()