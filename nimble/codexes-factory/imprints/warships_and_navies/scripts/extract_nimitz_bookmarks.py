#!/usr/bin/env python3
"""
Extract bookmarks from Nimitz Graybook PDF and map to volumes.
Remove NHHC readme pages and create new page numbering: {volume}-BODY:{page}
"""

import json
import fitz  # PyMuPDF
from pathlib import Path
from collections import defaultdict


def extract_bookmarks_hierarchy(doc):
    """Extract all bookmarks with hierarchy"""
    bookmarks = []
    toc = doc.get_toc()

    for level, title, page_num in toc:
        bookmarks.append({
            "level": level,
            "title": title.strip(),
            "page_number": page_num - 1,  # Convert to 0-based
            "page_number_human": page_num
        })

    return bookmarks


def map_bookmarks_to_volumes(bookmarks):
    """Map bookmarks to volumes based on page ranges from schedule"""

    # Volume definitions from nimitz_graybook_schedule.json
    volumes = [
        {"number": 1, "start": 0, "end": 860, "title": "7 December 1941 to 31 August 1942"},
        {"number": 2, "start": 861, "end": 1261, "title": "1 September 1942 to 31 December 1942"},
        {"number": 3, "start": 1262, "end": 1611, "title": "1 January 1943 to 30 June 1943"},
        {"number": 4, "start": 1612, "end": 1829, "title": "1 July 1943 to 31 December 1943"},
        {"number": 5, "start": 1830, "end": 2484, "title": "1 January 1944 to 31 December 1944"},
        {"number": 6, "start": 2485, "end": 3248, "title": "1 January 1945 to 1 July 1945"},
        {"number": 7, "start": 3249, "end": 3547, "title": "1 July 1945 to 31 August 1945"},
        {"number": 8, "start": 3548, "end": 4022, "title": "Selected Dispatches"}
    ]

    # Map each bookmark to a volume
    for bookmark in bookmarks:
        page = bookmark["page_number"]

        for vol in volumes:
            if vol["start"] <= page <= vol["end"]:
                bookmark["volume"] = vol["number"]
                bookmark["volume_title"] = vol["title"]
                bookmark["page_in_volume"] = page - vol["start"] + 1
                break

    return bookmarks, volumes


def identify_nhhc_readme_pages(doc, volumes):
    """
    Identify NHHC readme pages at the start of each volume.
    These are typically 1 page at the beginning of each volume section.
    """
    readme_pages = []

    for vol in volumes:
        # Check first page of each volume for NHHC readme indicators
        page = doc[vol["start"]]
        text = page.get_text().lower()

        # Common readme indicators
        if any(indicator in text for indicator in [
            "naval history and heritage command",
            "nhhc",
            "papers of fleet admiral",
            "manuscript collection",
            "this document"
        ]):
            readme_pages.append({
                "volume": vol["number"],
                "original_page": vol["start"],
                "is_readme": True
            })
            print(f"  ✓ Found NHHC readme at page {vol['start']} (Volume {vol['number']})")

    return readme_pages


def create_page_mapping(volumes, readme_pages, bookmarks):
    """
    Create mapping from original page numbers to new numbering scheme.
    Format: {volume}-BODY:{page_in_volume}
    Excludes NHHC readme pages.
    """
    page_mapping = {}
    readme_page_nums = {p["original_page"] for p in readme_pages}

    for vol in volumes:
        vol_num = vol["number"]
        body_page = 1

        for orig_page in range(vol["start"], vol["end"] + 1):
            if orig_page in readme_page_nums:
                # Mark as excluded
                page_mapping[orig_page] = {
                    "new_page_id": None,
                    "excluded": True,
                    "reason": "NHHC readme",
                    "volume": vol_num
                }
            else:
                # Create new page number
                page_mapping[orig_page] = {
                    "new_page_id": f"{vol_num}-BODY:{body_page}",
                    "volume": vol_num,
                    "body_page": body_page,
                    "excluded": False
                }
                body_page += 1

    return page_mapping


def update_bookmarks_with_new_pages(bookmarks, page_mapping):
    """Update bookmark page references with new numbering"""

    updated_bookmarks = []

    for bookmark in bookmarks:
        orig_page = bookmark["page_number"]

        if orig_page in page_mapping:
            mapping = page_mapping[orig_page]

            if mapping["excluded"]:
                # Skip bookmarks pointing to excluded pages
                continue

            bookmark["new_page_id"] = mapping["new_page_id"]
            bookmark["body_page"] = mapping["body_page"]
            updated_bookmarks.append(bookmark)

    return updated_bookmarks


def main():
    # Paths
    pdf_path = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/imprints/nimble_books_llc/graybooks/MSC334_01_17_01.pdf")
    output_dir = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/nimitz_ocr_gemini")

    print("=" * 80)
    print("Nimitz Graybook Bookmark Extraction & Page Mapping")
    print("=" * 80)
    print()

    # Open PDF
    print(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    print(f"Total pages: {len(doc)}")
    print()

    # Extract bookmarks
    print("Extracting bookmarks...")
    bookmarks = extract_bookmarks_hierarchy(doc)
    print(f"Found {len(bookmarks)} bookmarks")
    print()

    # Map to volumes
    print("Mapping bookmarks to volumes...")
    bookmarks, volumes = map_bookmarks_to_volumes(bookmarks)

    # Count bookmarks per volume
    vol_counts = defaultdict(int)
    for b in bookmarks:
        if "volume" in b:
            vol_counts[b["volume"]] += 1

    for vol_num in sorted(vol_counts.keys()):
        print(f"  Volume {vol_num}: {vol_counts[vol_num]} bookmarks")
    print()

    # Identify NHHC readme pages
    print("Identifying NHHC readme pages...")
    readme_pages = identify_nhhc_readme_pages(doc, volumes)
    print(f"Found {len(readme_pages)} readme pages to exclude")
    print()

    # Create page mapping
    print("Creating new page numbering scheme...")
    page_mapping = create_page_mapping(volumes, readme_pages, bookmarks)

    # Show sample mappings
    print("Sample page mappings:")
    sample_pages = [0, 1, 2, 861, 862, 863, 1262, 1263]
    for orig_page in sample_pages:
        if orig_page in page_mapping:
            mapping = page_mapping[orig_page]
            if mapping["excluded"]:
                print(f"  Page {orig_page:4d} → EXCLUDED (readme)")
            else:
                print(f"  Page {orig_page:4d} → {mapping['new_page_id']}")
    print()

    # Update bookmarks
    print("Updating bookmark page references...")
    updated_bookmarks = update_bookmarks_with_new_pages(bookmarks, page_mapping)
    print(f"Updated {len(updated_bookmarks)} bookmarks (excluded {len(bookmarks) - len(updated_bookmarks)})")
    print()

    # Save outputs
    print("Saving outputs...")

    # Save full bookmark data
    bookmarks_file = output_dir / "bookmarks_with_volumes.json"
    with open(bookmarks_file, 'w') as f:
        json.dump({
            "total_bookmarks": len(updated_bookmarks),
            "volumes": volumes,
            "bookmarks": updated_bookmarks
        }, f, indent=2)
    print(f"  ✓ Saved: {bookmarks_file}")

    # Save page mapping
    mapping_file = output_dir / "page_mapping.json"
    with open(mapping_file, 'w') as f:
        json.dump({
            "total_pages": len(page_mapping),
            "excluded_pages": len(readme_pages),
            "mapping": page_mapping
        }, f, indent=2)
    print(f"  ✓ Saved: {mapping_file}")

    # Save readme pages info
    readme_file = output_dir / "excluded_readme_pages.json"
    with open(readme_file, 'w') as f:
        json.dump({
            "readme_pages": readme_pages,
            "total_excluded": len(readme_pages)
        }, f, indent=2)
    print(f"  ✓ Saved: {readme_file}")

    # Create human-readable TOC
    toc_file = output_dir / "table_of_contents.txt"
    with open(toc_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("NIMITZ GRAYBOOK - COMPLETE TABLE OF CONTENTS\n")
        f.write("=" * 80 + "\n\n")

        current_vol = None
        for bookmark in updated_bookmarks:
            vol = bookmark.get("volume")
            if vol != current_vol:
                current_vol = vol
                f.write(f"\n{'=' * 80}\n")
                f.write(f"VOLUME {vol}: {bookmark.get('volume_title', '')}\n")
                f.write(f"{'=' * 80}\n\n")

            indent = "  " * (bookmark["level"] - 1)
            f.write(f"{indent}{bookmark['title']:<60} {bookmark['new_page_id']:>15}\n")

    print(f"  ✓ Saved: {toc_file}")
    print()

    doc.close()

    # Print summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Total bookmarks extracted: {len(bookmarks)}")
    print(f"Bookmarks after excluding readme pages: {len(updated_bookmarks)}")
    print(f"Pages excluded (NHHC readme): {len(readme_pages)}")
    print(f"Total pages with new numbering: {len([p for p in page_mapping.values() if not p['excluded']])}")
    print()
    print("New page format: {volume}-BODY:{page_in_volume}")
    print("Example: 1-BODY:1, 1-BODY:2, ..., 2-BODY:1, 2-BODY:2, ...")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
