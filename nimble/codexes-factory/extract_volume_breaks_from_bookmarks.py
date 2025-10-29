#!/usr/bin/env python3
"""
Extract volume breaks from top-level bookmarks in the 4023-page PDF.
Create initial page mapping: master PDF page → (volume, page_in_volume)

Then account for NHHC page removal (page 1 of each volume).
"""

import fitz
import json
from pathlib import Path


def main():
    print("=" * 80)
    print("Extracting Volume Breaks from PDF Bookmarks")
    print("=" * 80)
    print()

    # Open PDF
    pdf_path = Path("imprints/nimble_books_llc/graybooks/MSC334_01_17_01.pdf")
    pdf = fitz.open(pdf_path)

    print(f"Source PDF: {pdf_path}")
    print(f"Total pages: {len(pdf)}")
    print()

    # Get bookmarks (TOC)
    toc = pdf.get_toc()

    # Extract top-level bookmarks (level 1)
    top_level = [entry for entry in toc if entry[0] == 1]

    print("Top-level bookmarks (volume breaks):")
    print()

    volume_breaks = []

    for i, bookmark in enumerate(top_level):
        level, title, page_num = bookmark

        print(f"{i+1}. {title}")
        print(f"   Starts at PDF page: {page_num-1} (human page {page_num})")

        volume_breaks.append({
            "volume": i + 1,
            "title": title,
            "pdf_start_page": page_num - 1,  # PDF is 0-indexed
            "human_start_page": page_num
        })

    # Calculate end pages
    for i in range(len(volume_breaks)):
        if i < len(volume_breaks) - 1:
            volume_breaks[i]["pdf_end_page"] = volume_breaks[i+1]["pdf_start_page"] - 1
            volume_breaks[i]["human_end_page"] = volume_breaks[i+1]["human_start_page"] - 1
        else:
            # Last volume goes to end of PDF
            volume_breaks[i]["pdf_end_page"] = len(pdf) - 1
            volume_breaks[i]["human_end_page"] = len(pdf)

        volume_breaks[i]["total_pages"] = (volume_breaks[i]["pdf_end_page"] -
                                           volume_breaks[i]["pdf_start_page"] + 1)

    print("\n" + "=" * 80)
    print("Volume Structure:")
    print("=" * 80)
    print()

    for vol in volume_breaks:
        print(f"Volume {vol['volume']}: {vol['title']}")
        print(f"  PDF pages: {vol['pdf_start_page']}-{vol['pdf_end_page']}")
        print(f"  Human pages: {vol['human_start_page']}-{vol['human_end_page']}")
        print(f"  Total: {vol['total_pages']} pages")
        print()

    # Create initial page mapping (BEFORE NHHC removal)
    print("Creating initial page mapping...")

    initial_mapping = {}

    for vol in volume_breaks:
        vol_num = vol['volume']
        start_pdf = vol['pdf_start_page']
        end_pdf = vol['pdf_end_page']

        for pdf_page in range(start_pdf, end_pdf + 1):
            page_in_volume = pdf_page - start_pdf + 1  # 1-indexed

            initial_mapping[pdf_page] = {
                "volume": vol_num,
                "page_in_volume": page_in_volume,
                "pdf_page": pdf_page,
                "human_page": pdf_page + 1
            }

    # Save initial mapping
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "initial_volume_mapping_from_bookmarks.json"

    with open(output_file, 'w') as f:
        json.dump({
            "source": str(pdf_path),
            "extraction_method": "top-level bookmarks",
            "total_pdf_pages": len(pdf),
            "volume_breaks": volume_breaks,
            "page_mapping": {str(k): v for k, v in initial_mapping.items()},
            "note": "This is BEFORE removing NHHC pages. Page 1 of each volume will be removed."
        }, f, indent=2)

    print(f"✓ Saved: {output_file}")
    print()

    # Show what will be removed
    print("=" * 80)
    print("NHHC Pages to Remove (first page of each volume):")
    print("=" * 80)
    print()

    for vol in volume_breaks:
        first_page = vol['pdf_start_page']
        page = pdf[first_page]
        text_sample = page.get_text()[:200].replace('\n', ' ')

        print(f"Volume {vol['volume']}: PDF page {first_page} (human {first_page+1})")

        if "naval history" in text_sample.lower() or "nhhc" in text_sample.lower():
            print(f"  ✓ Contains NHHC text")
        else:
            print(f"  ⚠️  May not be NHHC page")

        print(f"  Sample: {text_sample[:100]}...")
        print()

    pdf.close()

    print("=" * 80)
    print("Next step: Create final mapping after NHHC removal")
    print("=" * 80)


if __name__ == "__main__":
    main()
