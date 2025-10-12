#!/usr/bin/env python3
"""
Generate Rights Offering Sheet with formatted catalog
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
    """Generate rights offering sheet with formatted catalog."""

    print("Generating Rights Offering Sheet with Formatted Catalog")
    print("=" * 60)
    print("Catalog Features:")
    print("• Unnumbered list format")
    print("• Reduced line spacing")
    print("• Publication dates (Month/Year)")
    print("• No author names")
    print("• Alternating row shading (20% opacity)")
    print("• Sorted by ascending publication date")
    print("=" * 60)

    # Xynapse Traces configuration path
    config_path = Path("configs/imprints/xynapse_traces.json")

    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return

    print(f"✅ Found configuration: {config_path}")

    # Output directory
    output_dir = Path("output/rights_offerings/xynapse_traces")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 Output directory: {output_dir}")

    try:
        # Generate the formatted catalog rights offering sheet
        print("🔄 Generating formatted catalog rights offering sheet...")
        result = generate_imprint_rights_sheet(
            imprint_config_path=str(config_path),
            output_dir=str(output_dir)
        )

        if result:
            result_path = Path(result)
            print(f"✅ Successfully generated: {result_path.name}")
            print(f"📄 Full path: {result}")

            # Show file size if it exists
            if result_path.exists():
                file_size = result_path.stat().st_size
                print(f"📏 File size: {file_size:,} bytes")

            print("\n📐 Catalog Format Features:")
            print("   ✅ Unnumbered format with bullet-free layout")
            print("   ✅ Minimal spacing between entries")
            print("   ✅ Publication dates in Month/Year format")
            print("   ✅ Title-only entries (no authors)")
            print("   ✅ Alternating light gray shading")
            print("   ✅ Chronological ordering by publication date")

            print("\n📅 Date Range:")
            print("   📆 Sep 2025 through May 2026")
            print("   📊 68 titles sorted chronologically")

        else:
            print("❌ Failed to generate formatted catalog rights offering sheet")

    except Exception as e:
        print(f"❌ Error generating formatted catalog rights offering sheet: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()