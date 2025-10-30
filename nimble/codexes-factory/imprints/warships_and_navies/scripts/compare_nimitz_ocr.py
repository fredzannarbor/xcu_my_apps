#!/usr/bin/env python3
"""
Compare existing OCR in Nimitz PDF with Claude Vision API OCR.
"""

import fitz  # PyMuPDF
import random
from pathlib import Path
import json

def extract_sample_pages(pdf_path, num_samples=5, output_dir="temp_ocr_comparison"):
    """Extract random pages as images and their existing OCR text."""

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    # Select random pages, avoiding first 50 (likely front matter)
    # and last 50 (likely indices)
    available_range = range(50, total_pages - 50)
    sample_pages = sorted(random.sample(list(available_range), num_samples))

    print(f"\nSelected pages: {sample_pages}")
    print(f"(Page numbers are 0-indexed, add 1 for human-readable)")

    results = []

    for page_num in sample_pages:
        page = doc[page_num]

        # Extract existing OCR text
        existing_text = page.get_text("text")

        # Save page as high-res image
        # Increase resolution for better OCR
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom = ~144 DPI from 72 DPI base
        pix = page.get_pixmap(matrix=mat)

        image_filename = f"page_{page_num:04d}.png"
        image_path = output_path / image_filename
        pix.save(str(image_path))

        result = {
            "page_number": page_num,
            "page_number_human": page_num + 1,
            "image_path": str(image_path),
            "existing_ocr_text": existing_text,
            "existing_ocr_length": len(existing_text),
            "page_size": {
                "width": page.rect.width,
                "height": page.rect.height
            }
        }

        results.append(result)

        print(f"\nPage {page_num + 1} ({page_num}):")
        print(f"  Image saved: {image_path}")
        print(f"  Existing OCR length: {len(existing_text)} chars")
        print(f"  First 200 chars: {existing_text[:200].strip()}")

    # Save results to JSON
    results_file = output_path / "extraction_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Extraction complete. Results saved to {results_file}")

    doc.close()
    return results

if __name__ == "__main__":
    pdf_path = "/Users/fred/xcu_my_apps/nimble/codexes-factory/input_files_by_imprint/big_five_warships_and_navies/MSC334_01_17_01 (1).pdf"

    # Set seed for reproducible random selection
    random.seed(42)

    results = extract_sample_pages(pdf_path, num_samples=3)

    print("\n" + "=" * 80)
    print("Next step: Run Claude Vision API on these images")
    print("=" * 80)