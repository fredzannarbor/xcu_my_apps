#!/usr/bin/env python3
"""
Create master page mapping for Nimitz volumes.
Critical for preserving entity-to-page reference accuracy after PDF reorganization.

Maps: Original PDF page → Final volume and page number
"""

import json
from pathlib import Path


def create_master_mapping():
    """
    Create complete mapping from original 4023-page PDF to final 8 volumes.
    """

    print("=" * 80)
    print("Creating Master Page Mapping")
    print("=" * 80)
    print()

    mapping = {}

    # VOLUME 1: Original PDF pages 1-861 (skip 0), remove 712-865
    # Human readable: pages 1-861, skip 1, remove 713-866
    vol_1_front_matter = 8
    vol_1_page_counter = vol_1_front_matter + 1  # Start at page 9 (first recto after front matter)

    print("Volume 1:")
    print(f"  Front matter: pages 1-{vol_1_front_matter}")
    print(f"  Content starts: page {vol_1_page_counter}")

    # Pages 1-711 (skip 0, skip 712-865)
    for orig_page in range(1, 712):  # PDF pages 1-711
        mapping[orig_page] = {
            "volume": 1,
            "page_in_volume": vol_1_page_counter,
            "page_reference": f"1:{vol_1_page_counter}",
            "original_pdf_page": orig_page,
            "original_human_page": orig_page + 1
        }
        vol_1_page_counter += 1

    mapping[0] = {"excluded": True, "reason": "NHHC readme page"}

    for orig_page in range(712, 866):  # These moved to Volume 2
        mapping[orig_page] = {"moved_to_volume": 2, "original_pdf_page": orig_page}

    print(f"  Content ends: page {vol_1_page_counter - 1}")
    print(f"  Total content pages: {vol_1_page_counter - vol_1_front_matter - 1}")

    # VOLUME 2: Pages moved from Vol 1 (712-865) + original 862-1261 (skip 861)
    vol_2_front_matter = 8
    vol_2_page_counter = vol_2_front_matter + 1

    print(f"\nVolume 2:")
    print(f"  Front matter: pages 1-{vol_2_front_matter}")

    # First: moved pages from Vol 1 (PDF 712-865)
    for orig_page in range(712, 866):
        mapping[orig_page] = {
            "volume": 2,
            "page_in_volume": vol_2_page_counter,
            "page_reference": f"2:{vol_2_page_counter}",
            "original_pdf_page": orig_page,
            "original_human_page": orig_page + 1,
            "note": "Moved from Volume 1"
        }
        vol_2_page_counter += 1

    mapping[861] = {"excluded": True, "reason": "NHHC readme page"}

    # Then: original Vol 2 pages (PDF 862-1261)
    for orig_page in range(862, 1262):
        mapping[orig_page] = {
            "volume": 2,
            "page_in_volume": vol_2_page_counter,
            "page_reference": f"2:{vol_2_page_counter}",
            "original_pdf_page": orig_page,
            "original_human_page": orig_page + 1
        }
        vol_2_page_counter += 1

    # VOLUMES 3-8: Standard pattern (remove first page, add front/back matter)
    volume_specs = [
        (3, 1262, 1611),
        (4, 1612, 1829),
        (5, 1830, 2484),
        (6, 2485, 3248),
        (7, 3249, 3547),
        (8, 3548, 4022)
    ]

    for vol_num, start_pdf, end_pdf in volume_specs:
        front_matter = 8
        page_counter = front_matter + 1

        print(f"\nVolume {vol_num}:")

        # Skip first page (NHHC readme)
        mapping[start_pdf] = {"excluded": True, "reason": "NHHC readme page"}

        # Map remaining pages
        for orig_page in range(start_pdf + 1, end_pdf + 1):
            mapping[orig_page] = {
                "volume": vol_num,
                "page_in_volume": page_counter,
                "page_reference": f"{vol_num}:{page_counter}",
                "original_pdf_page": orig_page,
                "original_human_page": orig_page + 1
            }
            page_counter += 1

        print(f"  Pages mapped: {start_pdf + 1}-{end_pdf} → Vol {vol_num} pages {front_matter+1}-{page_counter-1}")

    # Save mapping
    output_file = Path("nimitz_ocr_gemini/master_page_mapping.json")

    with open(output_file, 'w') as f:
        json.dump({
            "created": "2025-10-29",
            "source_pdf": "MSC334_01_17_01.pdf",
            "total_original_pages": 4023,
            "mapping": mapping,
            "format_note": "Page references use format 'volume:page_in_volume'",
            "usage_note": "Use this to convert entity page references from original PDF to final volume page numbers"
        }, f, indent=2)

    print(f"\n✓ Master mapping saved: {output_file}")
    print()

    # Statistics
    mapped = sum(1 for v in mapping.values() if "volume" in v)
    excluded = sum(1 for v in mapping.values() if v.get("excluded"))

    print("=" * 80)
    print("MAPPING STATISTICS")
    print("=" * 80)
    print(f"Total pages mapped: {mapped:,}")
    print(f"Pages excluded (NHHC): {excluded}")
    print(f"Pages moved (Vol 1→2): 154")
    print()
    print("This mapping file is CRITICAL for accurate index page references!")
    print("=" * 80)


if __name__ == "__main__":
    create_master_mapping()
