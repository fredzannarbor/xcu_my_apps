#!/usr/bin/env python3
"""
Create enhanced volume mapping with:
1. 'deleted' flag for NHHC pages (first page of each volume)
2. 'enhanced_pdf_page' accounting for 8 pages front matter + 2 pages back matter

Example for Volume 1:
- Original PDF page 0 → deleted=True
- Front matter pages 1-8 (roman numerals i-viii) → new placeholder items
- Original PDF page 1 → enhanced_pdf_page 9
- Original PDF page 2 → enhanced_pdf_page 10
- ... etc
- Back matter pages → 2 unnumbered pages after content
"""

import json
from pathlib import Path


def main():
    print("=" * 80)
    print("Creating Enhanced Volume Mapping")
    print("With front matter (8 pages) and back matter (2 pages)")
    print("=" * 80)
    print()

    # Load initial mapping
    initial_file = Path("output/initial_volume_mapping_from_bookmarks.json")

    with open(initial_file, 'r') as f:
        initial_data = json.load(f)

    volume_breaks = initial_data["volume_breaks"]
    initial_mapping = initial_data["page_mapping"]

    # Create enhanced mapping
    enhanced_mapping = {}

    for vol in volume_breaks:
        vol_num = vol['volume']
        start_pdf = vol['pdf_start_page']
        end_pdf = vol['pdf_end_page']

        print(f"Volume {vol_num}:")

        # FRONT MATTER (8 pages, roman numerals)
        front_matter_pages = []
        for i in range(1, 9):
            roman = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii'][i-1]
            page_type = ['title', 'blank', 'copyright', 'blank', 'contents', 'blank', 'intro', 'intro_cont'][i-1]

            key = f"vol{vol_num}_front_{i}"
            enhanced_mapping[key] = {
                "volume": vol_num,
                "page_type": "front_matter",
                "page_number_roman": roman,
                "enhanced_pdf_page": i,
                "placeholder_type": page_type,
                "deleted": False
            }
            front_matter_pages.append(key)

        print(f"  Front matter: pages i-viii (enhanced pages 1-8)")

        # CONTENT PAGES
        enhanced_page_counter = 9  # Content starts at page 9
        content_pages_added = 0

        for pdf_page in range(start_pdf, end_pdf + 1):
            key = str(pdf_page)

            # First page of volume (NHHC readme) → deleted
            if pdf_page == start_pdf:
                enhanced_mapping[key] = {
                    "volume": vol_num,
                    "page_type": "nhhc_readme",
                    "pdf_page": pdf_page,
                    "human_page": pdf_page + 1,
                    "deleted": True,
                    "reason": "NHHC Naval History and Heritage Command readme page"
                }
                print(f"  Deleted NHHC page: PDF {pdf_page} (human {pdf_page+1})")
                continue

            # Regular content page
            page_in_volume = pdf_page - start_pdf  # 0-indexed from volume start (after removing first)

            enhanced_mapping[key] = {
                "volume": vol_num,
                "page_type": "content",
                "pdf_page": pdf_page,
                "human_page": pdf_page + 1,
                "page_in_volume": page_in_volume,
                "enhanced_pdf_page": enhanced_page_counter,
                "deleted": False
            }

            enhanced_page_counter += 1
            content_pages_added += 1

        print(f"  Content pages: {content_pages_added} (enhanced pages 9-{enhanced_page_counter-1})")

        # BACK MATTER (2 unnumbered pages)
        for i in range(1, 3):
            key = f"vol{vol_num}_back_{i}"
            page_type = ['vol0_reference', 'blank'][i-1]

            enhanced_mapping[key] = {
                "volume": vol_num,
                "page_type": "back_matter",
                "enhanced_pdf_page": enhanced_page_counter,
                "placeholder_type": page_type,
                "deleted": False,
                "page_number": "unnumbered"
            }
            enhanced_page_counter += 1

        print(f"  Back matter: 2 unnumbered pages (enhanced pages {enhanced_page_counter-2}-{enhanced_page_counter-1})")
        print(f"  Total volume pages: {enhanced_page_counter - 1}")
        print()

    # Save enhanced mapping
    output_file = Path("output/enhanced_volume_mapping.json")

    with open(output_file, 'w') as f:
        json.dump({
            "created": "2025-10-29",
            "source_pdf": "MSC334_01_17_01.pdf",
            "mapping_includes": [
                "Front matter: 8 pages (i-viii)",
                "Content: Original pages minus NHHC first page",
                "Back matter: 2 unnumbered pages",
                "Deleted flag for NHHC pages"
            ],
            "volume_structure": {
                vol['volume']: {
                    "title": vol['title'],
                    "original_pdf_pages": f"{vol['pdf_start_page']}-{vol['pdf_end_page']}",
                    "total_original": vol['total_pages'],
                    "nhhc_removed": 1,
                    "front_matter": 8,
                    "back_matter": 2
                }
                for vol in volume_breaks
            },
            "enhanced_mapping": enhanced_mapping
        }, f, indent=2)

    print("=" * 80)
    print(f"✓ Enhanced mapping saved: {output_file}")
    print("=" * 80)
    print()

    # Statistics
    total_items = len(enhanced_mapping)
    deleted = sum(1 for v in enhanced_mapping.values() if v.get('deleted'))
    front_matter = sum(1 for v in enhanced_mapping.values() if v.get('page_type') == 'front_matter')
    back_matter = sum(1 for v in enhanced_mapping.values() if v.get('page_type') == 'back_matter')
    content = sum(1 for v in enhanced_mapping.values() if v.get('page_type') == 'content')

    print("Mapping statistics:")
    print(f"  Total entries: {total_items:,}")
    print(f"  Content pages: {content:,}")
    print(f"  Front matter placeholders: {front_matter}")
    print(f"  Back matter placeholders: {back_matter}")
    print(f"  Deleted (NHHC): {deleted}")
    print()
    print("This mapping preserves entity-to-page reference accuracy!")
    print("=" * 80)


if __name__ == "__main__":
    main()
