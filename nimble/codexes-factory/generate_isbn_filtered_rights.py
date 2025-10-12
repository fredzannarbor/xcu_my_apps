#!/usr/bin/env python3
"""
Generate Rights Offering Sheet with ISBN filtering
"""

from pathlib import Path
import argparse

# Import rights management modules
try:
    from codexes.modules.rights_management import generate_imprint_rights_sheet
except ImportError:
    import sys
    sys.path.append('src')
    from codexes.modules.rights_management import generate_imprint_rights_sheet

def main():
    """Generate rights offering sheet with optional ISBN filtering."""

    parser = argparse.ArgumentParser(description='Generate rights offering sheet with optional ISBN filtering')
    parser.add_argument('--config', required=True, help='Path to imprint configuration file')
    parser.add_argument('--output-dir', required=True, help='Output directory for generated files')
    parser.add_argument('--isbn-filter', help='Comma-separated list of ISBNs to focus on (e.g., "123,456,789")')
    parser.add_argument('--demo', action='store_true', help='Run demo with sample ISBNs')

    args = parser.parse_args()

    if args.demo:
        # Demo mode with sample ISBNs
        print("🧪 Demo Mode: ISBN Filtering Rights Offering Sheet")
        print("=" * 60)
        print("Demo Features:")
        print("• Focus on specific titles by ISBN")
        print("• Reduced catalog showing only selected works")
        print("• Same professional formatting as full catalog")
        print("• Useful for targeted rights campaigns")
        print("=" * 60)

        # Use sample ISBNs for demo (you can replace these with actual ISBNs from your catalog)
        demo_isbns = "9798348294021,9798348294038,9798348294045"  # Sample ISBNs
        config_path = Path(args.config)
        output_dir = Path(args.output_dir)

        print(f"📖 Demo ISBN Filter: {demo_isbns}")
        print(f"📁 Configuration: {config_path}")
        print(f"📁 Output Directory: {output_dir}")

        isbn_filter = demo_isbns
    else:
        # Regular mode
        print("Generating Rights Offering Sheet with ISBN Filtering")
        print("=" * 55)

        config_path = Path(args.config)
        output_dir = Path(args.output_dir)
        isbn_filter = args.isbn_filter

        if isbn_filter:
            print(f"🔍 ISBN Filter: {isbn_filter}")
            print("• Only works matching these ISBNs will be included")
            print("• Featured title will be first matching work")
            print("• Catalog will show filtered titles only")
        else:
            print("📚 No ISBN filter - generating full catalog")

        print("=" * 55)

    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return

    print(f"✅ Found configuration: {config_path}")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")

    try:
        print("🔄 Generating rights offering sheet...")

        # Generate with ISBN filter if provided
        result = generate_imprint_rights_sheet(
            imprint_config_path=str(config_path),
            output_dir=str(output_dir),
            isbn_filter=isbn_filter
        )

        if result:
            result_path = Path(result)
            print(f"✅ Successfully generated: {result_path.name}")
            print(f"📄 Full path: {result}")

            # Show file size if it exists
            if result_path.exists():
                file_size = result_path.stat().st_size
                print(f"📏 File size: {file_size:,} bytes")

            if isbn_filter:
                print(f"\n🎯 ISBN Filter Results:")
                print(f"   📋 Target ISBNs: {isbn_filter}")
                print(f"   📖 Filtered catalog shows only matching titles")
                print(f"   🎨 Same professional formatting as full catalog")
                print(f"   📄 Suitable for focused rights marketing campaigns")
            else:
                print(f"\n📚 Full Catalog Generated:")
                print(f"   📖 All available titles included")
                print(f"   📄 Complete imprint catalog in appendix")

        else:
            print("❌ Failed to generate rights offering sheet")
            if isbn_filter:
                print("💡 Possible causes:")
                print("   • No works found matching the provided ISBNs")
                print("   • ISBNs may not exist in the catalog")
                print("   • Check ISBN format (digits only, no hyphens needed)")

    except Exception as e:
        print(f"❌ Error generating rights offering sheet: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()