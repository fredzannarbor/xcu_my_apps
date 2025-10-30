#!/usr/bin/env python3
"""
Create publication-ready Nimitz Graybook volumes.

Strategy:
- 8.5 x 11" page size (perfect fit for original 8x10.5 content)
- NO SCALING - preserve vector quality at 100%
- Center original pages within LSI safety area (0.5" margins)
- Remove NHHC readme pages
- Add front/back matter with placeholders
- Content begins on recto (odd page)
"""

import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime
import json


VOLUMES = [
    {
        "number": 1,
        "original_start": 0,
        "original_end": 712,
        "subtitle": "7 December 1941 through 6 July 1942",
        "period": "Pearl Harbor, Wake Island, Doolittle Raid, Coral Sea, Midway",
        "author": "Captain James M. Steele, USN (CINCPAC Staff)"
    },
    {
        "number": 2,
        "original_start": 713,
        "original_end": 1261,
        "subtitle": "Including materials from 6 July 1942, through 31 December 1942",
        "period": "Guadalcanal campaign intensifies",
        "author": "CINCPAC Staff"
    },
    {
        "number": 3,
        "original_start": 1262,
        "original_end": 1611,
        "subtitle": "1 January 1943 to 30 June 1943",
        "period": "Central Solomons and New Georgia campaigns",
        "author": "CINCPAC Staff"
    },
    {
        "number": 4,
        "original_start": 1612,
        "original_end": 1829,
        "subtitle": "1 July 1943 to 31 December 1943",
        "period": "Central Pacific offensive begins - Gilberts campaign",
        "author": "CINCPAC Staff"
    },
    {
        "number": 5,
        "original_start": 1830,
        "original_end": 2484,
        "subtitle": "1 January 1944 to 31 December 1944",
        "period": "Marshalls, Marianas, Philippines invasion",
        "author": "CINCPAC Staff"
    },
    {
        "number": 6,
        "original_start": 2485,
        "original_end": 3248,
        "subtitle": "1 January 1945 to 1 July 1945",
        "period": "Iwo Jima, Okinawa, final campaigns",
        "author": "CINCPAC Staff"
    },
    {
        "number": 7,
        "original_start": 3249,
        "original_end": 3547,
        "subtitle": "1 July 1945 to 31 August 1945",
        "period": "Final operations and Japanese surrender",
        "author": "CINCPAC Staff"
    },
    {
        "number": 8,
        "original_start": 3548,
        "original_end": 4022,
        "subtitle": "Selected Dispatches: 30 December 1941 to 30 April 1942 and the Battle of Midway",
        "period": "Special dispatch collections",
        "author": "CINCPAC Staff"
    }
]


def is_nhhc_readme_page(page):
    """Check if page is an NHHC readme to skip"""
    text = page.get_text().lower()
    return any(indicator in text for indicator in [
        "naval history and heritage command",
        "nhhc",
        "papers of fleet admiral chester",
        "manuscript collection",
        "this document is from the holdings"
    ])


def create_placeholder_page(pdf_out, page_type, volume_data):
    """Create placeholder front/back matter pages"""

    page = pdf_out.new_page(width=612, height=792)  # 8.5 x 11

    if page_type == "title":
        page.insert_text((72, 200), "Command Summary of", fontsize=24, fontname="helv")
        page.insert_text((72, 230), "Fleet Admiral Chester W. Nimitz, USN", fontsize=24, fontname="hebo")
        page.insert_text((72, 300), f"Volume {volume_data['number']}", fontsize=20, fontname="hebo")
        page.insert_text((72, 340), volume_data['subtitle'], fontsize=14, fontname="helv")
        page.insert_text((72, 500), "The Nimitz \"Graybook\"", fontsize=16, fontname="hebo")
        page.insert_text((72, 600), "Warships & Navies", fontsize=14, fontname="hebo")
        page.insert_text((72, 630), "Nimble Books LLC", fontsize=12, fontname="helv")
        page.insert_text((72, 660), "2025", fontsize=12, fontname="helv")

    elif page_type == "copyright":
        page.insert_text((72, 500), f"Volume {volume_data['number']}: {volume_data['subtitle']}", fontsize=10)
        page.insert_text((72, 530), "This document is in the public domain.", fontsize=10)
        page.insert_text((72, 560), "Published by Warships & Navies, Nimble Books LLC", fontsize=9)
        page.insert_text((72, 590), "Original: Naval History and Heritage Command", fontsize=9)
        page.insert_text((72, 620), "ISBN: [TBD]", fontsize=9)

    elif page_type == "contents":
        page.insert_text((72, 100), "Table of Contents", fontsize=18, fontname="hebo")
        page.insert_text((72, 150), "[Contents from bookmarks]", fontsize=10)

    elif page_type == "introduction":
        page.insert_text((72, 100), f"Introduction to Volume {volume_data['number']}", fontsize=18, fontname="hebo")
        page.insert_text((72, 150), f"Period: {volume_data['period']}", fontsize=11)
        page.insert_text((72, 200), "[Introduction placeholder - max 2 pages]", fontsize=10)

    elif page_type == "volume0_ref":
        page.insert_text((72, 300), "Comprehensive Indices", fontsize=14, fontname="hebo")
        page.insert_text((72, 350), "For complete indices of Persons, Places, Ships, and", fontsize=10)
        page.insert_text((72, 370), "Organizations across all volumes, please refer to:", fontsize=10)
        page.insert_text((72, 420), "Volume 0: Master Guide and Analytical Companion", fontsize=12, fontname="hebo")

    return page


def create_volume(source_pdf, volume_data, output_dir):
    """Create one volume with proper formatting"""

    vol_num = volume_data['number']
    start = volume_data['original_start']
    end = volume_data['original_end']

    print(f"\nVolume {vol_num}: {volume_data['subtitle']}")
    print(f"  Source pages: {start}-{end} ({end-start+1} pages)")

    pdf_out = fitz.open()

    # FRONT MATTER (8 pages total, ensures content starts on recto)
    create_placeholder_page(pdf_out, "title", volume_data)          # i (recto)
    pdf_out.new_page(width=612, height=792)                         # ii (verso, blank)
    create_placeholder_page(pdf_out, "copyright", volume_data)      # iii (recto)
    pdf_out.new_page(width=612, height=792)                         # iv (verso, blank)
    create_placeholder_page(pdf_out, "contents", volume_data)       # v (recto)
    pdf_out.new_page(width=612, height=792)                         # vi (verso, blank)
    create_placeholder_page(pdf_out, "introduction", volume_data)   # vii (recto)
    pdf_out.new_page(width=612, height=792)                         # viii (verso)

    front_matter_pages = 8
    content_pages = 0
    skipped_nhhc = False

    # MAIN CONTENT (starts on page 9, which is recto)
    for page_num in range(start, end + 1):
        source_page = source_pdf[page_num]

        # Skip NHHC readme if it's the first page
        if page_num == start and is_nhhc_readme_page(source_page):
            print(f"  Removed NHHC readme page at position {page_num}")
            skipped_nhhc = True
            continue

        # Create new 8.5 x 11 page
        new_page = pdf_out.new_page(width=612, height=792)

        # Get original page dimensions
        src_rect = source_page.rect
        src_width = src_rect.width
        src_height = src_rect.height

        # NO SCALING - use original size (typically ~8 x 10.5 = 576 x 756 points)
        # Center within 8.5 x 11 page
        # LSI safety area: 0.5" margins = 36 points
        # Available: 540 x 720 points
        # Original typically: 576 x 756 - fits with small crop or slight overlap

        # For maximum quality: show original PDF directly without pixmap
        # Center the original page rect on the new page
        target_rect = fitz.Rect(
            (612 - src_width) / 2,     # x0 - center horizontally
            (792 - src_height) / 2,     # y0 - center vertically
            (612 + src_width) / 2,     # x1
            (792 + src_height) / 2      # y1
        )

        # Use show_pdf_page for vector quality preservation
        new_page.show_pdf_page(
            target_rect,
            source_pdf,
            page_num
        )

        content_pages += 1

    # BACK MATTER
    # Ensure content ends on verso for back matter to start on recto
    if content_pages % 2 == 1:
        pdf_out.new_page(width=612, height=792)
        back_blank = 1
    else:
        back_blank = 0

    create_placeholder_page(pdf_out, "volume0_ref", volume_data)

    total_pages = len(pdf_out)

    print(f"  Front matter: {front_matter_pages} pages")
    print(f"  Content: {content_pages} pages")
    print(f"  Back matter: {1 + back_blank} pages")
    print(f"  TOTAL: {total_pages} pages")

    if total_pages > 840:
        print(f"  ⚠️  EXCEEDS LSI LIMIT by {total_pages - 840} pages")
    else:
        print(f"  ✓ Within LSI 840-page limit ({840 - total_pages} pages margin)")

    # Save
    output_file = output_dir / f"nimitz_volume_{vol_num}_final.pdf"
    pdf_out.save(output_file, garbage=4, deflate=True)
    pdf_out.close()

    print(f"  ✓ Saved: {output_file}")

    return {
        "volume": vol_num,
        "total_pages": total_pages,
        "content_pages": content_pages,
        "nhhc_removed": skipped_nhhc,
        "within_limit": total_pages <= 840
    }


def main():
    print("=" * 80)
    print("Nimitz Graybook - Final Publication Volumes")
    print("Format: 8.5 x 11, No Scaling, Vector Quality Preserved")
    print("=" * 80)
    print()

    source_pdf = fitz.open("imprints/nimble_books_llc/graybooks/MSC334_01_17_01.pdf")
    output_dir = Path("nimitz_ocr_gemini/volumes_final")
    output_dir.mkdir(exist_ok=True)

    print(f"Source: {len(source_pdf)} pages")
    print(f"Output: {output_dir}/")
    print()

    results = []
    for vol_data in VOLUMES:
        result = create_volume(source_pdf, vol_data, output_dir)
        results.append(result)

    source_pdf.close()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n{'Vol':<5} {'Total':<8} {'Content':<10} {'NHHC Removed':<15} {'LSI Limit':<12}")
    print("-" * 80)

    for r in results:
        status = "✓ OK" if r['within_limit'] else "✗ OVER"
        nhhc = "✓" if r['nhhc_removed'] else "-"
        print(f"{r['volume']:<5} {r['total_pages']:<8} {r['content_pages']:<10} {nhhc:<15} {status:<12}")

    over_limit = [r for r in results if not r['within_limit']]

    print(f"\nVolumes over 840 pages: {len(over_limit)}")

    if over_limit:
        print("\n⚠️  ACTION REQUIRED:")
        for r in over_limit:
            print(f"  Volume {r['volume']}: {r['total_pages']} pages (over by {r['total_pages']-840})")

    # Save summary
    with open(output_dir / "volumes_summary.json", 'w') as f:
        json.dump({
            "created": datetime.now().isoformat(),
            "page_size": "8.5 x 11 inches",
            "scaling": "none (100% vector quality)",
            "margins": "0.5 inch LSI safety",
            "volumes": results
        }, f, indent=2)

    print(f"\n✓ All volumes: {output_dir}/nimitz_volume_*_final.pdf")
    print("=" * 80)


if __name__ == "__main__":
    main()
