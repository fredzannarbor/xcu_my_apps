#!/usr/bin/env python3
"""
Build final publication PDFs using the final_volume_mapping.json

Implements:
- 8 pages front matter (roman i-viii)
- Content pages (NHHC pages removed, Vol 1 pages moved to Vol 2)
- 2 pages back matter (unnumbered)
- 8.5 x 11, vector quality preserved, centered
"""

import fitz
import json
from pathlib import Path


def create_placeholder_page(pdf, page_type, vol_num):
    """Create front/back matter placeholder"""
    page = pdf.new_page(width=612, height=792)

    if page_type == "title":
        page.insert_text((72, 200), "Command Summary of", fontsize=24)
        page.insert_text((72, 230), "Fleet Admiral Chester W. Nimitz, USN", fontsize=24)
        page.insert_text((72, 300), f"Volume {vol_num}", fontsize=20)
        page.insert_text((72, 500), "The Nimitz \"Graybook\"", fontsize=16)
        page.insert_text((72, 600), "Warships & Navies", fontsize=14)
        page.insert_text((72, 630), "Nimble Books LLC, 2025", fontsize=12)

    elif page_type == "copyright":
        page.insert_text((72, 500), f"Volume {vol_num}", fontsize=10)
        page.insert_text((72, 530), "Public domain", fontsize=9)
        page.insert_text((72, 560), "ISBN: [TBD]", fontsize=9)

    elif page_type == "contents":
        page.insert_text((72, 100), "Table of Contents", fontsize=18)

    elif page_type in ["intro", "intro_cont"]:
        page.insert_text((72, 100), f"Introduction - Volume {vol_num}", fontsize=18)

    elif page_type == "vol0_reference":
        page.insert_text((72, 300), "Comprehensive Indices", fontsize=14)
        page.insert_text((72, 350), "See Volume 0 for complete indices", fontsize=10)

    elif page_type == "blank":
        pass  # Blank page

    return page


def build_volume_pdf(source_pdf, vol_num, mapping, output_dir):
    """Build one volume PDF from mapping"""

    print(f"\nBuilding Volume {vol_num}...")

    pdf_out = fitz.open()

    # Get all pages for this volume from mapping, sorted by enhanced_pdf_page
    vol_pages = []

    for key, data in mapping.items():
        if data.get('volume') == vol_num and not data.get('deleted'):
            vol_pages.append((key, data))

    # Sort by enhanced_pdf_page
    vol_pages.sort(key=lambda x: x[1]['enhanced_pdf_page'])

    for key, page_data in vol_pages:
        page_type = page_data.get('page_type')

        if page_type in ['front_matter', 'back_matter']:
            # Create placeholder
            placeholder_type = page_data.get('placeholder_type', 'blank')
            create_placeholder_page(pdf_out, placeholder_type, vol_num)

        elif page_type == 'content':
            # Copy original PDF page
            pdf_page = page_data['pdf_page']
            source_page = source_pdf[pdf_page]

            new_page = pdf_out.new_page(width=612, height=792)

            # Center original page on 8.5 x 11
            src_rect = source_page.rect
            target_rect = fitz.Rect(
                (612 - src_rect.width) / 2,
                (792 - src_rect.height) / 2,
                (612 + src_rect.width) / 2,
                (792 + src_rect.height) / 2
            )

            new_page.show_pdf_page(target_rect, source_pdf, pdf_page)

    total_pages = len(pdf_out)

    # Save
    output_file = output_dir / f"volume_{vol_num}_final.pdf"
    pdf_out.save(output_file, garbage=4, deflate=True)
    pdf_out.close()

    print(f"  ✓ Created {total_pages} pages")
    print(f"  ✓ Saved: {output_file}")

    return total_pages


def main():
    print("=" * 80)
    print("Building Final Publication Volumes")
    print("Using final_volume_mapping.json")
    print("=" * 80)

    # Load mapping
    mapping_file = Path("output/final_volume_mapping.json")

    with open(mapping_file, 'r') as f:
        data = json.load(f)

    mapping = data["mapping"]

    # Open source PDF
    source_pdf = fitz.open("imprints/nimble_books_llc/graybooks/MSC334_01_17_01.pdf")

    output_dir = Path("output/volumes")
    output_dir.mkdir(exist_ok=True)

    # Build all 8 volumes
    results = {}

    for vol_num in range(1, 9):
        pages = build_volume_pdf(source_pdf, vol_num, mapping, output_dir)
        results[vol_num] = pages

    source_pdf.close()

    # Summary
    print("\n" + "=" * 80)
    print("VOLUME BUILD COMPLETE")
    print("=" * 80)
    print()

    for vol_num in range(1, 9):
        pages = results[vol_num]
        status = "✓" if pages <= 840 else "✗"
        print(f"Volume {vol_num}: {pages} pages {status}")

    print()
    print(f"All volumes saved to: {output_dir}/")
    print("=" * 80)


if __name__ == "__main__":
    main()
