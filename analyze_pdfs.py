#!/usr/bin/env python3
"""
Analyze submarine patrol report PDFs to determine page counts, file sizes, and quality metrics.
"""

import fitz  # PyMuPDF
import os
from pathlib import Path
import json
from typing import Dict, List, Tuple

def analyze_pdf(pdf_path: Path) -> Dict:
    """
    Analyze a single PDF file using PyMuPDF.

    Returns dict with:
    - page_count: number of pages
    - file_size_mb: file size in megabytes
    - page_dimensions: list of (width, height) tuples
    - has_text: whether PDF contains extractable text
    - avg_dpi: estimated average DPI (from image analysis)
    """
    try:
        doc = fitz.open(pdf_path)

        # Basic metrics
        page_count = len(doc)
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)

        # Sample first, middle, and last pages for analysis
        sample_indices = [0, page_count // 2, page_count - 1] if page_count > 2 else range(page_count)

        page_dimensions = []
        text_lengths = []
        image_counts = []

        for i in sample_indices:
            page = doc[i]
            rect = page.rect
            page_dimensions.append((rect.width, rect.height))

            # Check for text
            text = page.get_text()
            text_lengths.append(len(text.strip()))

            # Check for images
            image_list = page.get_images()
            image_counts.append(len(image_list))

        # Calculate averages
        avg_width = sum(d[0] for d in page_dimensions) / len(page_dimensions)
        avg_height = sum(d[1] for d in page_dimensions) / len(page_dimensions)
        avg_text_length = sum(text_lengths) / len(text_lengths)
        avg_image_count = sum(image_counts) / len(image_counts)

        # Estimate DPI (assuming 8.5x11 page is ~612x792 points at 72 DPI)
        # Higher dimensions suggest scanned images
        estimated_dpi = int((avg_height / 11.0) * 72)

        has_text = avg_text_length > 100  # At least some meaningful text

        doc.close()

        return {
            "page_count": page_count,
            "file_size_mb": round(file_size_mb, 2),
            "avg_dimensions": (round(avg_width, 1), round(avg_height, 1)),
            "estimated_dpi": estimated_dpi,
            "has_text": has_text,
            "avg_text_length": int(avg_text_length),
            "avg_images_per_page": round(avg_image_count, 1),
            "status": "success"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def analyze_all_submarines(base_path: Path) -> Dict:
    """
    Analyze all submarine patrol report PDFs and aggregate by submarine.
    """
    results = {}

    # Find all submarine directories
    for sub_dir in sorted(base_path.iterdir()):
        if not sub_dir.is_dir():
            continue

        submarine_name = sub_dir.name
        pdf_files = list(sub_dir.glob("*.pdf"))

        if not pdf_files:
            continue

        submarine_data = {
            "hull_number": submarine_name.split("_")[0],
            "name": "_".join(submarine_name.split("_")[1:]),
            "parts": [],
            "total_pages": 0,
            "total_size_mb": 0
        }

        for pdf_path in sorted(pdf_files):
            print(f"Analyzing: {pdf_path.name}")
            analysis = analyze_pdf(pdf_path)

            if analysis["status"] == "success":
                part_data = {
                    "filename": pdf_path.name,
                    **analysis
                }
                submarine_data["parts"].append(part_data)
                submarine_data["total_pages"] += analysis["page_count"]
                submarine_data["total_size_mb"] += analysis["file_size_mb"]

        submarine_data["total_size_mb"] = round(submarine_data["total_size_mb"], 2)
        results[submarine_name] = submarine_data

    return results

def print_summary(results: Dict):
    """Print a formatted summary of the analysis."""
    print("\n" + "=" * 100)
    print("SUBMARINE PATROL REPORTS - PDF ANALYSIS SUMMARY")
    print("=" * 100)
    print()

    # Summary table
    print(f"{'Submarine':<25} {'Parts':<8} {'Pages':<10} {'Size (MB)':<12} {'Avg DPI':<10} {'Text?':<8}")
    print("-" * 100)

    total_pages = 0
    total_size = 0
    total_parts = 0

    for sub_name, data in sorted(results.items()):
        parts_count = len(data["parts"])
        pages = data["total_pages"]
        size = data["total_size_mb"]

        # Get average DPI across parts
        if data["parts"]:
            avg_dpi = int(sum(p["estimated_dpi"] for p in data["parts"]) / len(data["parts"]))
            has_text = "Yes" if all(p["has_text"] for p in data["parts"]) else "Mixed"
        else:
            avg_dpi = 0
            has_text = "N/A"

        print(f"{sub_name:<25} {parts_count:<8} {pages:<10} {size:<12.1f} {avg_dpi:<10} {has_text:<8}")

        total_pages += pages
        total_size += size
        total_parts += parts_count

    print("-" * 100)
    print(f"{'TOTAL':<25} {total_parts:<8} {total_pages:<10} {total_size:<12.1f}")
    print()

    # Detailed breakdown by submarine
    print("\n" + "=" * 100)
    print("DETAILED BREAKDOWN BY SUBMARINE")
    print("=" * 100)

    for sub_name, data in sorted(results.items()):
        print(f"\n{data['hull_number']} {data['name']}")
        print(f"  Total Pages: {data['total_pages']}")
        print(f"  Total Size: {data['total_size_mb']} MB")
        print(f"  Parts: {len(data['parts'])}")

        for part in data["parts"]:
            print(f"    - {part['filename']}: {part['page_count']} pages, "
                  f"{part['file_size_mb']} MB, "
                  f"{part['estimated_dpi']} DPI, "
                  f"{'text' if part['has_text'] else 'image-only'}")

    # Publication recommendations
    print("\n" + "=" * 100)
    print("PUBLICATION VOLUME RECOMMENDATIONS")
    print("=" * 100)
    print()

    # Categorize by page count
    short_books = []  # < 200 pages
    medium_books = []  # 200-400 pages
    long_books = []  # > 400 pages

    for sub_name, data in results.items():
        if data['total_pages'] < 200:
            short_books.append((sub_name, data))
        elif data['total_pages'] < 400:
            medium_books.append((sub_name, data))
        else:
            long_books.append((sub_name, data))

    print(f"Short books (<200 pages): {len(short_books)}")
    for sub_name, data in short_books:
        print(f"  - {sub_name}: {data['total_pages']} pages")

    print(f"\nMedium books (200-400 pages): {len(medium_books)}")
    for sub_name, data in medium_books:
        print(f"  - {sub_name}: {data['total_pages']} pages")

    print(f"\nLong books (>400 pages): {len(long_books)}")
    for sub_name, data in long_books:
        print(f"  - {sub_name}: {data['total_pages']} pages")

    print("\nRECOMMENDATIONS:")
    print(f"  - Standalone volumes: {len(medium_books) + len(long_books)} submarines")
    print(f"  - Combined volume candidates: {len(short_books)} submarines (could create {(len(short_books) + 1) // 2} combo books)")
    print(f"  - Total potential volumes: {len(medium_books) + len(long_books) + (len(short_books) + 1) // 2}")

    # Average pages per submarine
    avg_pages = total_pages / len(results)
    print(f"\n  - Average pages per submarine: {avg_pages:.0f}")
    print(f"  - Total pages across all submarines: {total_pages}")

if __name__ == "__main__":
    base_path = Path("input_files_by_imprint/warships_and_navies/submarine_patrol_reports")

    if not base_path.exists():
        print(f"Error: Directory not found: {base_path}")
        exit(1)

    print(f"Analyzing PDFs in: {base_path}")
    print()

    results = analyze_all_submarines(base_path)

    # Save results to JSON
    output_file = "submarine_pdf_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nAnalysis saved to: {output_file}")

    # Print summary
    print_summary(results)
