#!/usr/bin/env python3
"""
Generate Rights Offering Sheet with longtable catalog
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
    """Generate rights offering sheet with longtable catalog."""

    print("Generating Rights Offering Sheet with Longtable Catalog")
    print("=" * 65)
    print("Longtable Features:")
    print("• Proper table formatting with aligned columns")
    print("• Page breaks handled automatically")
    print("• Subtle row shading (95% gray for readability)")
    print("• Professional table headers and footers")
    print("• Column alignment: Title (left), Date (center), Pages (right)")
    print("=" * 65)

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
        # Generate the longtable catalog rights offering sheet
        print("🔄 Generating longtable catalog rights offering sheet...")
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

            print("\n📐 Longtable Catalog Features:")
            print("   ✅ Professional table layout with booktabs styling")
            print("   ✅ Automatic page breaks for large datasets")
            print("   ✅ Subtle alternating row shading (95% gray)")
            print("   ✅ Proper column alignment and spacing")
            print("   ✅ Table headers on each page")
            print("   ✅ Continuation markers for page breaks")

            print("\n📊 Table Structure:")
            print("   📚 Title: Left-aligned, 4.2 inches wide")
            print("   📅 Publication: Center-aligned")
            print("   📄 Pages: Right-aligned")

        else:
            print("❌ Failed to generate longtable catalog rights offering sheet")

    except Exception as e:
        print(f"❌ Error generating longtable catalog rights offering sheet: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()