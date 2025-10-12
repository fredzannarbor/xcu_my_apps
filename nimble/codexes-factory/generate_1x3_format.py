#!/usr/bin/env python3
"""
Generate Rights Offering Sheet with 1x3 table format
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
    """Generate rights offering sheet with 1x3 table format."""

    print("Generating Rights Offering Sheet with 1×3 Format")
    print("=" * 55)
    print("New Layout:")
    print("• Single horizontal row with 3 books")
    print("• Smaller thumbnails (0.6in × 0.9in)")
    print("• Narrower columns (1.8in each)")
    print("• Concise bullet points (3 per book)")
    print("=" * 55)

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
        # Generate the 1x3 format rights offering sheet
        print("🔄 Generating 1×3 format rights offering sheet...")
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

            print("\n📐 1×3 Layout Features:")
            print("   ✅ Three books in horizontal layout")
            print("   ✅ Compact thumbnails (0.6in × 0.9in)")
            print("   ✅ Efficient use of page width")
            print("   ✅ Clean professional presentation")
            print("\n📚 Featured Books:")
            print("   1. Advanced Propulsion: Fast vs. Safe")
            print("   2. AI Governance: Freedom vs. Constraint")
            print("   3. AI Openness: Sharing versus Secrecy")

        else:
            print("❌ Failed to generate 1×3 format rights offering sheet")

    except Exception as e:
        print(f"❌ Error generating 1×3 format rights offering sheet: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()