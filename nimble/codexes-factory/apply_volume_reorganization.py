#!/usr/bin/env python3
"""
Apply volume reorganization: Move PDF pages 712-865 (human 713-866) from Volume 1 to Volume 2.

This brings Volume 1 under the 840-page limit.

Updates:
- Pages 712-865 change from volume:1 to volume:2
- Volume 1 page count: 875 → 721 (under limit!)
- Volume 2 page count: 412 → 566
- All enhanced_pdf_page numbers recalculated
"""

import json
from pathlib import Path


def main():
    print("=" * 80)
    print("Applying Volume Reorganization")
    print("Moving PDF pages 712-865 from Volume 1 to Volume 2")
    print("=" * 80)
    print()

    # Load enhanced mapping
    enhanced_file = Path("output/enhanced_volume_mapping.json")

    with open(enhanced_file, 'r') as f:
        data = json.load(f)

    mapping = data["enhanced_mapping"]

    # Identify pages to move (PDF 712-865, human 713-866)
    pages_to_move = []
    for pdf_page in range(712, 866):
        key = str(pdf_page)
        if key in mapping and mapping[key].get('volume') == 1:
            pages_to_move.append(key)

    print(f"Pages to move: {len(pages_to_move)} pages (PDF 712-865)")
    print()

    # Move pages to Volume 2
    for key in pages_to_move:
        mapping[key]['volume'] = 2
        mapping[key]['moved_from_volume'] = 1
        mapping[key]['note'] = "Moved from Volume 1 to Volume 2 to meet LSI page limit"

    # Rebuild enhanced_pdf_page numbers for all volumes
    print("Recalculating enhanced_pdf_page numbers...")
    print()

    for vol_num in range(1, 9):
        print(f"Volume {vol_num}:")

        # Get all pages for this volume (excluding deleted)
        vol_pages = []

        # Front matter
        for i in range(1, 9):
            key = f"vol{vol_num}_front_{i}"
            if key in mapping:
                vol_pages.append((key, 'front', i))

        # Content pages (sorted by original PDF page)
        content_keys = [k for k, v in mapping.items()
                       if v.get('volume') == vol_num
                       and v.get('page_type') == 'content'
                       and not v.get('deleted')]

        # Sort by PDF page number
        content_keys_sorted = sorted(content_keys, key=lambda k: int(k) if k.isdigit() else 0)

        for key in content_keys_sorted:
            vol_pages.append((key, 'content', mapping[key].get('pdf_page')))

        # Back matter
        for i in range(1, 3):
            key = f"vol{vol_num}_back_{i}"
            if key in mapping:
                vol_pages.append((key, 'back', i))

        # Assign new enhanced_pdf_page numbers
        for idx, (key, page_type, _) in enumerate(vol_pages, 1):
            mapping[key]['enhanced_pdf_page'] = idx

        total_pages = len(vol_pages)
        content_pages = sum(1 for _, pt, _ in vol_pages if pt == 'content')

        print(f"  Total pages: {total_pages}")
        print(f"  Content pages: {content_pages}")

        if total_pages > 840:
            print(f"  ⚠️  OVER LIMIT by {total_pages - 840} pages")
        else:
            print(f"  ✓ Under limit ({840 - total_pages} margin)")

        print()

    # Save final mapping
    output_file = Path("output/final_volume_mapping.json")

    with open(output_file, 'w') as f:
        json.dump({
            "created": "2025-10-29",
            "reorganization": "Pages 712-865 moved from Volume 1 to Volume 2",
            "page_structure": {
                "front_matter": "8 pages (i-viii)",
                "content": "Original pages minus NHHC first page",
                "back_matter": "2 unnumbered pages"
            },
            "mapping": mapping
        }, f, indent=2)

    print("=" * 80)
    print(f"✓ Final mapping saved: {output_file}")
    print("=" * 80)
    print()
    print("This mapping is ready for:")
    print("1. Creating final PDFs")
    print("2. Converting entity page references from original PDF to final volume pages")
    print("=" * 80)


if __name__ == "__main__":
    main()
