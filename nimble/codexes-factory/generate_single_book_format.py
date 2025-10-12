#!/usr/bin/env python3
"""
Generate Rights Offering Sheet with single featured book and appendix
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
    """Generate rights offering sheet with single book format and appendix."""

    print("Generating Rights Offering Sheet with Single Book & Appendix Format")
    print("=" * 70)
    print("New Layout:")
    print("• Single featured book with detailed description")
    print("• Large cover image (2.0in × 3.0in) with text wrapping")
    print("• 5-7 detailed bullet points")
    print("• Complete catalog appendix listing all titles")
    print("=" * 70)

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
        # Generate the single book format rights offering sheet
        print("🔄 Generating single book format rights offering sheet...")
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

            print("\n📐 Single Book Layout Features:")
            print("   ✅ Featured book with detailed description")
            print("   ✅ Large cover image with text wrapping")
            print("   ✅ Comprehensive bullet points (7 features)")
            print("   ✅ Complete catalog appendix")
            print("\n📚 Featured Book:")
            print("   📖 Advanced Propulsion: Fast vs. Safe")
            print("\n📋 Appendix:")
            print("   📝 Complete listing of all forthcoming titles")

        else:
            print("❌ Failed to generate single book format rights offering sheet")

    except Exception as e:
        print(f"❌ Error generating single book format rights offering sheet: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()