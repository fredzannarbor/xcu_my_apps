#!/usr/bin/env python3
"""
Extract initial page mapping from schedule file.
Maps master PDF pages (1-4023) to initial volume structure.

Based on nimitz_graybook_schedule.json page ranges.
"""

import json
from pathlib import Path


def main():
    print("=" * 80)
    print("Extracting Initial Volume Page Mapping")
    print("=" * 80)
    print()

    # Load schedule
    schedule_file = Path("imprints/warships_and_navies/nimitz_graybook_schedule.json")

    with open(schedule_file, 'r') as f:
        schedule = json.load(f)

    volumes_spec = schedule["publishing_schedule"][0]["books"][1:]  # Skip Volume 0

    print("Volume structure from schedule:")
    print()

    mapping = {}
    volume_info = []

    for vol in volumes_spec:
        vol_num = vol["volume_number"]
        page_range = vol["original_page_range"]

        # Parse page range (format: "1-861" or "862-1262")
        start, end = page_range.split("-")
        master_start = int(start)
        master_end = int(end)
        total_pages = master_end - master_start + 1

        print(f"Volume {vol_num}: Master pages {master_start}-{master_end} ({total_pages} pages)")

        volume_info.append({
            "volume": vol_num,
            "master_start": master_start,
            "master_end": master_end,
            "total_pages": total_pages,
            "subtitle": vol["subtitle"]
        })

        # Create mapping for each page
        for master_page in range(master_start, master_end + 1):
            page_in_volume = master_page - master_start + 1

            mapping[str(master_page)] = {
                "volume": vol_num,
                "page_in_volume": page_in_volume,
                "master_page": master_page,
                "pdf_page": master_page - 1,  # PDF is 0-indexed
                "reference": f"{vol_num}:BODY:{page_in_volume}"
            }

    # Save mapping
    output_file = Path("nimitz_ocr_gemini/initial_volume_page_mapping.json")

    with open(output_file, 'w') as f:
        json.dump({
            "created": "2025-10-29",
            "source": "nimitz_graybook_schedule.json",
            "note": "Initial mapping BEFORE any reorganization (713-866 move, NHHC page removal)",
            "total_pages": 4023,
            "volumes": volume_info,
            "page_mapping": mapping
        }, f, indent=2)

    print(f"\n✓ Saved: {output_file}")
    print()

    # Sample mappings
    print("Sample mappings:")
    print(f"  Master page 1 → {mapping['1']}")
    print(f"  Master page 867 → {mapping['867']}")
    print(f"  Master page 4023 → {mapping['4023']}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
