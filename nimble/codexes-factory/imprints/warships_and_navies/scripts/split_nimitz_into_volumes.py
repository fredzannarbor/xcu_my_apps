#!/usr/bin/env python3
"""
Split Nimitz Graybook PDF into 8 publication-ready volumes.

Volume specifications:
- Remove NHHC "about" pages (first page of each volume section)
- Add front matter: title, copyright, contents, introduction (2 pages max)
- Add back matter: reference to Volume 0
- Volume content begins on recto (odd page)
- Shrink pages to fit within 0.5" margins on 8.5x11
- Portrait orientation
- LSI 840-page color hardcover limit

Volume 1 special handling:
- Move pages 713-866 to Volume 2
- Volume 1: "7 December 1941 through 6 July 1942"
- Volume 2: "Including materials from 6 July 1942, through 31 December 1942"
"""

import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime


# Volume definitions with adjusted page ranges
VOLUMES = [
    {
        "number": 1,
        "original_start": 0,
        "original_end": 712,  # Moved 713-860 to Volume 2
        "subtitle": "7 December 1941 through 6 July 1942",
        "period": "Pearl Harbor, Wake Island, Doolittle Raid, Coral Sea, Midway",
        "author": "Captain James M. Steele, USN (CINCPAC Staff)"
    },
    {
        "number": 2,
        "original_start": 713,  # Now starts with materials from 6 July
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


def create_placeholder_page(pdf_out, page_type, volume_data):
    """Create a placeholder page for front/back matter"""

    page = pdf_out.new_page(width=612, height=792)  # 8.5 x 11 inches
    text_page = page

    if page_type == "title":
        # Title page
        text_page.insert_text((100, 200), "Command Summary of", fontsize=24)
        text_page.insert_text((100, 230), "Fleet Admiral Chester W. Nimitz, USN", fontsize=24)
        text_page.insert_text((100, 300), f"Volume {volume_data['number']}", fontsize=20)
        text_page.insert_text((100, 340), volume_data['subtitle'], fontsize=14)
        text_page.insert_text((100, 500), "The Nimitz \"Graybook\"", fontsize=16)
        text_page.insert_text((100, 600), "Warships & Navies", fontsize=14)
        text_page.insert_text((100, 630), "Nimble Books LLC", fontsize=12)
        text_page.insert_text((100, 660), "2025", fontsize=12)

    elif page_type == "copyright":
        # Copyright page
        text_page.insert_text((50, 500), f"Volume {volume_data['number']}: {volume_data['subtitle']}", fontsize=10)
        text_page.insert_text((50, 530), "This document is in the public domain.", fontsize=10)
        text_page.insert_text((50, 560), "Published by Warships & Navies, an imprint of Nimble Books LLC", fontsize=9)
        text_page.insert_text((50, 590), "Original source: Naval History and Heritage Command", fontsize=9)
        text_page.insert_text((50, 620), "ISBN: [TBD]", fontsize=9)

    elif page_type == "contents":
        # Table of contents placeholder
        text_page.insert_text((100, 100), "Table of Contents", fontsize=18)
        text_page.insert_text((100, 150), "[Contents will be generated from bookmarks]", fontsize=10)

    elif page_type == "introduction":
        # Introduction placeholder
        text_page.insert_text((100, 100), f"Introduction to Volume {volume_data['number']}", fontsize=18)
        text_page.insert_text((100, 150), f"Period covered: {volume_data['period']}", fontsize=11)
        text_page.insert_text((100, 200), "[2-page introduction placeholder]", fontsize=10)
        text_page.insert_text((100, 250), f"Author: {volume_data['author']}", fontsize=10)

    elif page_type == "back_reference":
        # Back matter - reference to Volume 0
        text_page.insert_text((100, 300), "Comprehensive Indices and Reference Materials", fontsize=14)
        text_page.insert_text((100, 350), "For complete indices of Persons, Places, Ships, and Organizations", fontsize=10)
        text_page.insert_text((100, 380), "across all 8 volumes, please refer to:", fontsize=10)
        text_page.insert_text((100, 420), "Volume 0: Master Guide and Analytical Companion", fontsize=12)

    return page


def shrink_page_to_margins(page, margin_inches=0.5):
    """
    Shrink page content to fit within margins on 8.5x11 page.
    Target area: 7.5 x 10 inches (with 0.5" margins all around)
    """

    # Get page dimensions
    page_rect = page.rect
    page_width = page_rect.width
    page_height = page_rect.height

    # Target dimensions (8.5 x 11 inches = 612 x 792 points)
    target_width = 612
    target_height = 792
    margin_points = margin_inches * 72  # Convert to points

    # Available space after margins
    available_width = target_width - (2 * margin_points)  # 7.5 inches
    available_height = target_height - (2 * margin_points)  # 10 inches

    # Calculate scaling factor (maintain aspect ratio)
    scale_x = available_width / page_width
    scale_y = available_height / page_height
    scale = min(scale_x, scale_y)  # Use smaller to fit both dimensions

    # Create transformation matrix: scale and center
    mat = fitz.Matrix(scale, scale)

    # Calculate centering offsets
    scaled_width = page_width * scale
    scaled_height = page_height * scale
    x_offset = margin_points + (available_width - scaled_width) / 2
    y_offset = margin_points + (available_height - scaled_height) / 2

    mat = mat.pretranslate(x_offset, y_offset)

    return mat


def create_volume_pdf(source_pdf, volume_data, output_dir):
    """Create a single volume PDF with front and back matter"""

    vol_num = volume_data['number']
    start_page = volume_data['original_start']
    end_page = volume_data['original_end']

    print(f"\nVolume {vol_num}: {volume_data['subtitle']}")
    print(f"  Original pages: {start_page} to {end_page} ({end_page - start_page + 1} pages)")

    # Create output PDF
    pdf_out = fitz.open()

    # FRONT MATTER (even number of pages to ensure content starts on recto)

    # 1. Title page (recto, page i)
    create_placeholder_page(pdf_out, "title", volume_data)

    # 2. Blank (verso, page ii)
    pdf_out.new_page(width=612, height=792)

    # 3. Copyright (recto, page iii)
    create_placeholder_page(pdf_out, "copyright", volume_data)

    # 4. Blank (verso, page iv)
    pdf_out.new_page(width=612, height=792)

    # 5. Contents (recto, page v)
    create_placeholder_page(pdf_out, "contents", volume_data)

    # 6. Blank (verso, page vi)
    pdf_out.new_page(width=612, height=792)

    # 7-8. Introduction (rectos/verso, pages vii-viii, max 2 pages)
    create_placeholder_page(pdf_out, "introduction", volume_data)
    pdf_out.new_page(width=612, height=792)  # Page viii (verso or continuation)

    print(f"  Front matter: 8 pages")

    # MAIN CONTENT (starts on recto, page 1)
    # Note: We now have 8 front matter pages (even number), so next page is recto

    content_pages = 0

    for page_num in range(start_page, end_page + 1):
        # Skip NHHC "about" page if it's the first page of volume
        if page_num == start_page:
            # Check if it's an NHHC readme page
            page = source_pdf[page_num]
            text = page.get_text().lower()
            if any(indicator in text for indicator in ["naval history and heritage command", "nhhc", "papers of fleet admiral"]):
                print(f"  Skipping NHHC readme page at {page_num}")
                continue

        # Copy page with scaling
        source_page = source_pdf[page_num]

        # Create new page in standard size
        new_page = pdf_out.new_page(width=612, height=792)

        # Calculate transformation to fit in margins
        mat = shrink_page_to_margins(source_page)

        # Show the source page with transformation (correct PyMuPDF syntax)
        new_page.show_pdf_page(new_page.rect, source_pdf, page_num, clip=source_page.rect)

        # Apply scaling by inserting as pixmap instead
        pix = source_page.get_pixmap(matrix=mat)
        new_page.insert_image(new_page.rect, pixmap=pix)

        content_pages += 1

    print(f"  Content pages: {content_pages}")

    # BACK MATTER
    # Add blank if needed to make content end on verso
    if content_pages % 2 == 1:
        pdf_out.new_page(width=612, height=792)
        print(f"  Added blank page after content")

    # Reference to Volume 0 (recto)
    create_placeholder_page(pdf_out, "back_reference", volume_data)

    total_pages = len(pdf_out)
    print(f"  TOTAL PAGES: {total_pages}")

    if total_pages > 840:
        print(f"  ⚠️  WARNING: {total_pages} pages exceeds LSI 840-page limit!")

    # Save volume
    output_file = output_dir / f"nimitz_volume_{vol_num}.pdf"
    pdf_out.save(output_file)
    pdf_out.close()

    print(f"  ✓ Saved: {output_file}")

    return {
        "volume": vol_num,
        "total_pages": total_pages,
        "content_pages": content_pages,
        "front_matter": 8,
        "back_matter": 2 if content_pages % 2 == 1 else 1,
        "within_limit": total_pages <= 840
    }


def main():
    print("=" * 80)
    print("Nimitz Graybook - Split into 8 Publication Volumes")
    print("=" * 80)
    print()

    # Paths
    source_pdf_path = Path("imprints/nimble_books_llc/graybooks/MSC334_01_17_01.pdf")
    output_dir = Path("nimitz_ocr_gemini/publication_volumes")
    output_dir.mkdir(exist_ok=True)

    print(f"Source PDF: {source_pdf_path}")
    print(f"Output directory: {output_dir}")
    print()

    # Open source PDF
    print("Opening source PDF...")
    source_pdf = fitz.open(source_pdf_path)
    print(f"✓ Loaded {len(source_pdf)} pages")
    print()

    # Process each volume
    results = []

    for volume_data in VOLUMES:
        result = create_volume_pdf(source_pdf, volume_data, output_dir)
        results.append(result)

    source_pdf.close()

    # Summary
    print("\n" + "=" * 80)
    print("VOLUME CREATION SUMMARY")
    print("=" * 80)
    print()

    print(f"{'Volume':<10} {'Pages':<10} {'Content':<10} {'Within Limit':<15}")
    print("-" * 80)

    for result in results:
        status = "✓ YES" if result['within_limit'] else "✗ NO"
        print(f"{result['volume']:<10} {result['total_pages']:<10} {result['content_pages']:<10} {status:<15}")

    print()
    print(f"Total volumes created: {len(results)}")
    print(f"Volumes exceeding 840-page limit: {sum(1 for r in results if not r['within_limit'])}")
    print()

    # Save summary
    summary_file = output_dir / "volume_split_summary.json"
    import json
    with open(summary_file, 'w') as f:
        json.dump({
            "split_date": datetime.now().isoformat(),
            "source_pdf": str(source_pdf_path),
            "total_source_pages": 4023,
            "volumes": results,
            "notes": [
                "Front matter: 8 pages (title, copyright, contents, intro)",
                "Content begins on recto (odd page)",
                "Back matter: 1-2 pages (reference to Volume 0)",
                "Pages shrunk to fit 0.5 inch margins on 8.5x11",
                "NHHC readme pages removed from volume starts",
                "Volume 1: Moved pages 713-860 to Volume 2"
            ]
        }, f, indent=2)

    print(f"✓ Summary saved: {summary_file}")
    print()
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Review Volume 1 page count (should be under 840)")
    print("2. Generate actual front matter content (title, intro, etc.)")
    print("3. Add bookmarks/TOC for each volume")
    print("4. Create covers for each volume")
    print("=" * 80)


if __name__ == "__main__":
    main()
