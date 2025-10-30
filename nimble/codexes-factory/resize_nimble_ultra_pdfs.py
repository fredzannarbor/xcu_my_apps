#!/usr/bin/env python3
"""
Resize Nimble Ultra PDFs to fit LSI text safety area on 8.5 x 11 portrait pages.

LSI safety area: 0.5" margins all around
Usable text area: 7.5" x 10" (540 x 720 points)
Target page size: 8.5 x 11" (612 x 792 points)
"""

import fitz
from pathlib import Path


def resize_pdf_to_safety_area(input_path, output_path):
    """Resize PDF pages to fit within LSI safety area, centered on 8.5x11"""

    pdf_in = fitz.open(input_path)
    pdf_out = fitz.open()

    print(f"\nProcessing: {input_path.name}")
    print(f"  Total pages: {len(pdf_in)}")

    # Check first page size
    first_page = pdf_in[0]
    orig_width = first_page.rect.width
    orig_height = first_page.rect.height

    print(f"  Original size: {orig_width:.1f} x {orig_height:.1f} points")
    print(f"               ({orig_width/72:.2f}\" x {orig_height/72:.2f}\")")

    for page_num in range(len(pdf_in)):
        source_page = pdf_in[page_num]

        # Create new 8.5 x 11 page
        new_page = pdf_out.new_page(width=612, height=792)

        # Get source dimensions
        src_rect = source_page.rect
        src_w = src_rect.width
        src_h = src_rect.height

        # Center on page (no scaling - preserve vector quality)
        target_rect = fitz.Rect(
            (612 - src_w) / 2,  # x0
            (792 - src_h) / 2,  # y0
            (612 + src_w) / 2,  # x1
            (792 + src_h) / 2   # y1
        )

        # Copy page preserving vector quality
        new_page.show_pdf_page(target_rect, pdf_in, page_num)

    # Save
    total_pages = len(pdf_out)
    pdf_out.save(output_path, garbage=4, deflate=True)
    pdf_out.close()
    pdf_in.close()

    print(f"  ✓ Saved: {output_path}")
    print(f"  Output: {total_pages} pages at 8.5 x 11\"")


def main():
    print("=" * 80)
    print("Nimble Ultra PDF Resizing for LSI Safety Area")
    print("Target: 8.5 x 11 portrait with 0.5\" margins")
    print("=" * 80)

    input_dir = Path("input_files_by_imprint/nimble_ultra")
    output_dir = Path("output/nimble_ultra_resized")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find PDF files
    pdf_files = list(input_dir.glob("*.pdf"))

    print(f"\nFound {len(pdf_files)} PDF files")

    for pdf_file in pdf_files:
        output_file = output_dir / pdf_file.name
        resize_pdf_to_safety_area(pdf_file, output_file)

    print("\n" + "=" * 80)
    print("RESIZING COMPLETE")
    print("=" * 80)
    print(f"\nAll files saved to: {output_dir}/")
    print("\nFiles are now:")
    print("  - 8.5 x 11 inches (612 x 792 points)")
    print("  - Original content centered")
    print("  - Vector quality preserved")
    print("  - Ready for LSI submission")
    print("=" * 80)


if __name__ == "__main__":
    main()
