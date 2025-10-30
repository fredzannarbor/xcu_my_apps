#!/usr/bin/env python3
"""
Create Nimitz volumes with EXACT page specifications.

Source: MSC334_01_17_01 (1).pdf (PDF page numbers are 0-indexed, so subtract 1)

Volume 1: PDF pages 0-860 (human pages 1-861), REMOVE page 0, REMOVE 712-865 → move to Vol 2
Volume 2: PDF pages 712-865 (moved from Vol 1) + 861-1261 (human 862-1262), REMOVE page 861
Volume 3: PDF pages 1262-1611 (human 1263-1612), REMOVE page 1262
Volume 4: PDF pages 1612-1829 (human 1613-1830), REMOVE page 1612
Volume 5: PDF pages 1830-2484 (human 1831-2485), REMOVE page 1830
Volume 6: PDF pages 2485-3248 (human 2486-3249), REMOVE page 2485
Volume 7: PDF pages 3249-3547 (human 3250-3548), REMOVE page 3249
Volume 8: PDF pages 3548-end (not sequential), REMOVE first page

Front/back matter added to all volumes.
8.5 x 11, vector quality preserved, centered.
"""

import fitz
from pathlib import Path
import json
from datetime import datetime


def create_placeholder(pdf_out, page_type, volume_data):
    """Create front/back matter placeholder"""
    page = pdf_out.new_page(width=612, height=792)

    if page_type == "title":
        page.insert_text((72, 200), "Command Summary of", fontsize=24)
        page.insert_text((72, 230), "Fleet Admiral Chester W. Nimitz, USN", fontsize=24)
        page.insert_text((72, 300), f"Volume {volume_data['number']}", fontsize=20)
        page.insert_text((72, 340), volume_data['subtitle'], fontsize=12)
        page.insert_text((72, 500), "The Nimitz \"Graybook\"", fontsize=16)
        page.insert_text((72, 600), "Warships & Navies", fontsize=14)
        page.insert_text((72, 630), "Nimble Books LLC, 2025", fontsize=12)

    elif page_type == "copyright":
        page.insert_text((72, 500), f"Volume {volume_data['number']}: {volume_data['subtitle']}", fontsize=10)
        page.insert_text((72, 530), "Public domain. Published by Warships & Navies.", fontsize=9)
        page.insert_text((72, 560), "ISBN: [TBD]", fontsize=9)

    elif page_type == "contents":
        page.insert_text((72, 100), "Table of Contents", fontsize=18)
        page.insert_text((72, 150), "[From bookmarks]", fontsize=10)

    elif page_type == "intro":
        page.insert_text((72, 100), f"Introduction to Volume {volume_data['number']}", fontsize=18)
        page.insert_text((72, 150), f"Period: {volume_data['period']}", fontsize=11)
        page.insert_text((72, 200), "[Max 2 pages]", fontsize=10)

    elif page_type == "vol0_ref":
        page.insert_text((72, 300), "Indices and Reference Materials", fontsize=14)
        page.insert_text((72, 350), "Complete indices in Volume 0", fontsize=10)

    return page


def copy_page_centered(pdf_out, source_pdf, page_num):
    """Copy page preserving vector quality, centered on 8.5x11"""

    source_page = source_pdf[page_num]
    new_page = pdf_out.new_page(width=612, height=792)

    src_rect = source_page.rect
    src_w = src_rect.width
    src_h = src_rect.height

    # Center on page
    target_rect = fitz.Rect(
        (612 - src_w) / 2,
        (792 - src_h) / 2,
        (612 + src_w) / 2,
        (792 + src_h) / 2
    )

    new_page.show_pdf_page(target_rect, source_pdf, page_num)


def create_volume_1(source_pdf, output_dir):
    """Volume 1: Pages 1-861, remove page 1, remove 713-866"""

    vol = {"number": 1, "subtitle": "7 December 1941 through 6 July 1942",
           "period": "Pearl Harbor through early July 1942", "author": "Capt. Steele"}

    pdf = fitz.open()

    # Front matter (8 pages)
    create_placeholder(pdf, "title", vol)
    pdf.new_page(width=612, height=792)  # blank
    create_placeholder(pdf, "copyright", vol)
    pdf.new_page(width=612, height=792)
    create_placeholder(pdf, "contents", vol)
    pdf.new_page(width=612, height=792)
    create_placeholder(pdf, "intro", vol)
    pdf.new_page(width=612, height=792)

    # Content: pages 1-712 (PDF 0-711), skip page 0 (NHHC), skip 712-865
    for i in range(1, 712):  # PDF pages 1-711 (human 2-712)
        copy_page_centered(pdf, source_pdf, i)

    # Back matter
    if (712-1) % 2 == 1:  # Odd content pages, add blank
        pdf.new_page(width=612, height=792)
    create_placeholder(pdf, "vol0_ref", vol)

    total_pages = len(pdf)
    pdf.save(output_dir / "volume_1_final.pdf", garbage=4, deflate=True)
    pdf.close()

    return {"volume": 1, "pages": total_pages, "content": 711}


def create_volume_2(source_pdf, output_dir):
    """Volume 2: Pages from Vol 1 (713-866) + original 862-1262, remove 862"""

    vol = {"number": 2, "subtitle": "Including materials from 6 July 1942 through 31 December 1942",
           "period": "Guadalcanal campaign", "author": "CINCPAC Staff"}

    pdf = fitz.open()

    # Front matter
    for _ in range(4):  # title, blank, copyright, blank
        if _ % 2 == 0:
            create_placeholder(pdf, ["title", "copyright", "contents", "intro"][_//2], vol)
        else:
            pdf.new_page(width=612, height=792)
    create_placeholder(pdf, "contents", vol)
    pdf.new_page(width=612, height=792)
    create_placeholder(pdf, "intro", vol)
    pdf.new_page(width=612, height=792)

    # Content: Moved pages from Vol 1 (PDF 712-865, human 713-866)
    for i in range(712, 866):
        copy_page_centered(pdf, source_pdf, i)

    # Then original Vol 2 content (PDF 862-1261, human 863-1262), skip 861
    for i in range(862, 1262):  # Skip PDF 861 (human 862)
        copy_page_centered(pdf, source_pdf, i)

    # Back matter
    content = (866-712) + (1262-862)
    if content % 2 == 1:
        pdf.new_page(width=612, height=792)
    create_placeholder(pdf, "vol0_ref", vol)

    total_pages = len(pdf)
    pdf.save(output_dir / "volume_2_final.pdf", garbage=4, deflate=True)
    pdf.close()

    return {"volume": 2, "pages": total_pages, "content": content}


def create_volume_generic(source_pdf, vol_num, start_pdf, end_pdf, subtitle, period, output_dir):
    """Generic volume creator for volumes 3-8"""

    vol = {"number": vol_num, "subtitle": subtitle, "period": period, "author": "CINCPAC Staff"}

    pdf = fitz.open()

    # Front matter (8 pages)
    create_placeholder(pdf, "title", vol)
    pdf.new_page(width=612, height=792)
    create_placeholder(pdf, "copyright", vol)
    pdf.new_page(width=612, height=792)
    create_placeholder(pdf, "contents", vol)
    pdf.new_page(width=612, height=792)
    create_placeholder(pdf, "intro", vol)
    pdf.new_page(width=612, height=792)

    # Content: skip first page, copy rest
    for i in range(start_pdf + 1, end_pdf + 1):
        copy_page_centered(pdf, source_pdf, i)

    # Back matter
    content = end_pdf - start_pdf  # Already excluded first page
    if content % 2 == 1:
        pdf.new_page(width=612, height=792)
    create_placeholder(pdf, "vol0_ref", vol)

    total_pages = len(pdf)
    pdf.save(output_dir / f"volume_{vol_num}_final.pdf", garbage=4, deflate=True)
    pdf.close()

    return {"volume": vol_num, "pages": total_pages, "content": content}


def main():
    print("=" * 80)
    print("Nimitz Volumes - Deterministic Page Extraction")
    print("=" * 80)
    print()

    source = fitz.open("imprints/nimble_books_llc/graybooks/MSC334_01_17_01.pdf")
    output_dir = Path("nimitz_ocr_gemini/volumes_final")
    output_dir.mkdir(exist_ok=True)

    print(f"Source: {len(source)} pages")
    print()

    results = []

    # Volume 1 (special handling)
    print("Creating Volume 1...")
    results.append(create_volume_1(source, output_dir))

    # Volume 2 (special handling)
    print("Creating Volume 2...")
    results.append(create_volume_2(source, output_dir))

    # Volumes 3-8
    specs = [
        (3, 1262, 1611, "1 January 1943 to 30 June 1943", "Central Solomons"),
        (4, 1612, 1829, "1 July 1943 to 31 December 1943", "Gilberts campaign"),
        (5, 1830, 2484, "1 January 1944 to 31 December 1944", "Marshalls, Marianas, Philippines"),
        (6, 2485, 3248, "1 January 1945 to 1 July 1945", "Iwo Jima, Okinawa"),
        (7, 3249, 3547, "1 July 1945 to 31 August 1945", "Final operations, surrender"),
        (8, 3548, 4022, "Selected Dispatches", "Midway and early war")
    ]

    for vol_num, start, end, subtitle, period in specs:
        print(f"Creating Volume {vol_num}...")
        results.append(create_volume_generic(source, vol_num, start, end, subtitle, period, output_dir))

    source.close()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n{'Vol':<5} {'Total':<8} {'Content':<10} {'Limit':<10}")
    print("-" * 40)

    for r in results:
        status = "✓" if r['pages'] <= 840 else "✗"
        print(f"{r['volume']:<5} {r['pages']:<8} {r['content']:<10} {status:<10}")

    with open(output_dir / "volumes_final_summary.json", 'w') as f:
        json.dump({"created": datetime.now().isoformat(), "volumes": results}, f, indent=2)

    print(f"\n✓ Files: {output_dir}/volume_*_final.pdf")
    print("=" * 80)


if __name__ == "__main__":
    main()
