#!/usr/bin/env python3
"""
Extract all pages from Nimitz PDF as individual PNG images for OCR processing.
"""

import fitz  # PyMuPDF
from pathlib import Path
import json

def extract_all_pages(pdf_path, output_dir="nimitz_pages"):
    """Extract all pages as PNG images."""

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    print(f"Total pages: {total_pages:,}")
    print(f"Extracting to: {output_path}")
    print("")

    # Create manifest file
    manifest = {
        "total_pages": total_pages,
        "source_pdf": pdf_path,
        "output_dir": str(output_path),
        "pages": []
    }

    for page_num in range(total_pages):
        page = doc[page_num]

        # Extract at 2x resolution (~144 DPI)
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)

        # Save with zero-padded filename
        image_filename = f"page_{page_num:05d}.png"
        image_path = output_path / image_filename
        pix.save(str(image_path))

        # Get original OCR for comparison
        original_ocr = page.get_text("text")

        manifest["pages"].append({
            "page_number": page_num,
            "page_number_human": page_num + 1,
            "image_filename": image_filename,
            "image_path": str(image_path),
            "original_ocr_length": len(original_ocr)
        })

        if (page_num + 1) % 100 == 0:
            print(f"Extracted {page_num + 1:,} / {total_pages:,} pages...")

    # Save manifest
    manifest_file = output_path / "manifest.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\n✅ Extraction complete!")
    print(f"Total pages extracted: {total_pages:,}")
    print(f"Manifest saved to: {manifest_file}")

    doc.close()
    return manifest

if __name__ == "__main__":
    pdf_path = "/Users/fred/xcu_my_apps/nimble/codexes-factory/input_files_by_imprint/big_five_warships_and_navies/MSC334_01_17_01 (1).pdf"

    manifest = extract_all_pages(pdf_path)

    print(f"\nPages are ready for OCR processing via Claude Vision agents.")
    print(f"Images location: nimitz_pages/")
