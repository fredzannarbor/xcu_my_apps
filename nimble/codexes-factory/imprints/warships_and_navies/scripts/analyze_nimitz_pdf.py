#!/usr/bin/env python3
"""
Analyze the Nimitz Graybook PDF structure, bookmarks, and page distribution.
"""

import fitz  # PyMuPDF
import json
from pathlib import Path

def analyze_pdf(pdf_path):
    """Analyze PDF structure, bookmarks, and pages."""
    print(f"Analyzing: {pdf_path}")
    print("=" * 80)

    doc = fitz.open(pdf_path)

    # Basic info
    num_pages = len(doc)
    print(f"\nTotal Pages: {num_pages:,}")

    # Get metadata
    metadata = doc.metadata
    if metadata:
        print("\nMetadata:")
        for key, value in metadata.items():
            if value:
                print(f"  {key}: {value}")

    # Get bookmarks/outline (Table of Contents)
    print("\nBookmarks/Outline:")
    toc = doc.get_toc()

    if toc:
        print(f"Found {len(toc)} bookmarks")
        print("\nFirst 50 bookmarks:")
        for level, title, page_num in toc[:50]:
            indent = "  " * (level - 1)
            print(f"{indent}- {title}: Page {page_num}")

        if len(toc) > 50:
            print(f"\n... and {len(toc) - 50} more bookmarks")
            print("\nLast 10 bookmarks:")
            for level, title, page_num in toc[-10:]:
                indent = "  " * (level - 1)
                print(f"{indent}- {title}: Page {page_num}")
    else:
        print("  No bookmarks found")

    # Analyze page sizes (sample pages)
    print("\n\nPage Size Analysis:")
    sample_indices = list(range(min(10, num_pages))) + \
                    [num_pages // 2] + \
                    list(range(max(0, num_pages - 10), num_pages))

    sizes = {}
    for i in set(sample_indices):
        page = doc[i]
        rect = page.rect
        width = rect.width / 72  # Convert points to inches
        height = rect.height / 72
        size_key = f"{width:.2f} x {height:.2f}"
        if size_key not in sizes:
            sizes[size_key] = []
        sizes[size_key].append(i + 1)

    for size, pages in sorted(sizes.items()):
        print(f"  {size} inches: pages {pages[:5]}{'...' if len(pages) > 5 else ''}")

        # Volume page ranges from README
        volumes = {
            "Volume 1": (1, 861),
            "Volume 2": (862, 1262),
            "Volume 3": (1263, 1612),
            "Volume 4": (1613, 1830),
            "Volume 5": (1831, 2485),
            "Volume 6": (2486, 3249),
            "Volume 7": (3250, 3548),
            "Volume 8": "Not sequentially numbered"
        }

        print("\n\nVolume Page Counts (from README):")
        print("-" * 60)
        total_pages_documented = 0
        for vol, pages in volumes.items():
            if isinstance(pages, tuple):
                start, end = pages
                count = end - start + 1
                total_pages_documented += count
                # Add 10 pages for front matter estimate
                with_front_matter = count + 10
                status = "⚠️  EXCEEDS LIMIT" if with_front_matter > 840 else "✓ OK"
                print(f"{vol}: pages {start:,}-{end:,} = {count:,} pages (+10 front matter = {with_front_matter}) {status}")
            else:
                print(f"{vol}: {pages}")

        print(f"\nTotal documented pages: {total_pages_documented:,}")
        print(f"Actual PDF pages: {num_pages:,}")
        print(f"Difference: {num_pages - total_pages_documented:,} pages")

        # Check for Volume 5 (the problem child)
        vol5_count = 2485 - 1831 + 1
        print(f"\n⚠️  Volume 5 has {vol5_count} pages")
        print(f"   With 10-page front matter: {vol5_count + 10} pages")
        print(f"   Exceeds 840 limit by: {vol5_count + 10 - 840} pages")
        print(f"   Need to reduce by at least: {vol5_count + 10 - 840} pages")

    doc.close()

    return {
        'total_pages': num_pages,
        'volumes': volumes,
        'bookmarks_found': len(toc) > 0 if toc else False
    }

if __name__ == "__main__":
    pdf_path = "/Users/fred/xcu_my_apps/nimble/codexes-factory/input_files_by_imprint/big_five_warships_and_navies/MSC334_01_17_01 (1).pdf"

    result = analyze_pdf(pdf_path)

    print("\n" + "=" * 80)
    print("Analysis complete!")
