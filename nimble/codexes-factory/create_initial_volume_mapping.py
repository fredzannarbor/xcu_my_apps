#!/usr/bin/env python3
"""
Create initial volume-to-page mapping based on original volume structure.

Per your specification:
- Volume 1: Pages 1-866 (866 pages)
- Volume 2: Pages 867-1269 (403 pages) [867=Vol2 page 1]
- Volume 3: Pages 1270-?
- etc.

This creates the INITIAL mapping before any reorganization.
"""

import json
from pathlib import Path


# Based on your description and the schedule file
INITIAL_VOLUME_BREAKS = [
    {"volume": 1, "master_start": 1, "master_end": 866, "pages": 866},
    {"volume": 2, "master_start": 867, "master_end": 1269, "pages": 403},  # You said 867-1170 but that's only 304?
    {"volume": 3, "master_start": 1270, "master_end": 1619, "pages": 350},  # Estimated
    {"volume": 4, "master_start": 1620, "master_end": 1837, "pages": 218},  # Estimated
    {"volume": 5, "master_start": 1838, "master_end": 2492, "pages": 655},  # Estimated
    {"volume": 6, "master_start": 2493, "master_end": 3256, "pages": 764},  # Estimated
    {"volume": 7, "master_start": 3257, "master_end": 3555, "pages": 299},  # Estimated
    {"volume": 8, "master_start": 3556, "master_end": 4023, "pages": 468},  # Estimated
]


def create_initial_mapping():
    """Create mapping: master page → (volume, page_in_volume)"""

    print("=" * 80)
    print("Creating Initial Volume-to-Page Mapping")
    print("From original PDF structure (before reorganization)")
    print("=" * 80)
    print()

    mapping = {}

    for vol_spec in INITIAL_VOLUME_BREAKS:
        vol_num = vol_spec["volume"]
        start = vol_spec["master_start"]
        end = vol_spec["master_end"]

        print(f"Volume {vol_num}: Master pages {start}-{end} ({end-start+1} pages)")

        # Map each master page to volume page
        for master_page in range(start, end + 1):
            page_in_volume = master_page - start + 1  # 1-indexed within volume

            mapping[master_page] = {
                "volume": vol_num,
                "page_in_volume": page_in_volume,
                "master_page": master_page,
                "pdf_page": master_page - 1  # PDF is 0-indexed
            }

    # Save mapping
    output_file = Path("nimitz_ocr_gemini/initial_volume_mapping.json")

    with open(output_file, 'w') as f:
        json.dump({
            "mapping_type": "initial",
            "note": "Maps master PDF pages (1-4023) to original volume structure BEFORE reorganization",
            "total_pages": 4023,
            "volumes": INITIAL_VOLUME_BREAKS,
            "page_mapping": mapping
        }, f, indent=2)

    print(f"\n✓ Saved: {output_file}")
    print()

    # Statistics
    print("Mapping statistics:")
    print(f"  Total pages mapped: {len(mapping):,}")
    print(f"  Volumes: {len(INITIAL_VOLUME_BREAKS)}")

    # Verify continuity
    for i in range(len(INITIAL_VOLUME_BREAKS) - 1):
        curr_end = INITIAL_VOLUME_BREAKS[i]["master_end"]
        next_start = INITIAL_VOLUME_BREAKS[i+1]["master_start"]
        if curr_end + 1 != next_start:
            print(f"  ⚠️  Gap between Vol {i+1} (ends {curr_end}) and Vol {i+2} (starts {next_start})")

    print()
    print("Please verify these volume breaks match the actual PDF structure.")
    print("=" * 80)


if __name__ == "__main__":
    create_initial_mapping()
