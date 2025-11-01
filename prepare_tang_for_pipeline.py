#!/usr/bin/env python3
"""
Convert USS TANG OCR JSONL output to format expected by Nimble Ultra pipeline.

The pipeline expects a PDF or a concatenated text file. We'll create a text file
with page markers from the JSONL OCR output.
"""

import json
from pathlib import Path

def jsonl_to_text(jsonl_file, output_file):
    """Convert JSONL OCR output to single text file with page markers."""

    pages = []

    with open(jsonl_file) as f:
        for line in f:
            page_data = json.loads(line)
            if page_data["success"] and page_data.get("ocr_text"):
                page_num = page_data["page_number_human"]
                ocr_text = page_data["ocr_text"]
                pages.append((page_num, ocr_text))

    # Write to output file with page markers
    with open(output_file, 'w') as f:
        f.write("# USS TANG (SS-306) Complete War Patrol Reports\n")
        f.write("# OCR'd from maritime.org scanned microfilm\n")
        f.write("# Source: U.S. Naval History and Heritage Command\n\n")

        for page_num, text in pages:
            f.write(f"\n{'='*80}\n")
            f.write(f"PAGE {page_num}\n")
            f.write(f"{'='*80}\n\n")
            f.write(text)
            f.write("\n\n")

    print(f"✅ Converted {len(pages)} pages to {output_file}")
    print(f"   Total characters: {sum(len(t) for _, t in pages):,}")

if __name__ == "__main__":
    jsonl_file = Path("ocr_output/SS-306_TANG/SS-306_TANG_ocr.jsonl")
    output_file = Path("input_files_by_imprint/warships_and_navies/submarine_patrol_reports/SS-306_TANG/SS-306_TANG_complete.txt")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    jsonl_to_text(jsonl_file, output_file)

    print(f"\nReady for Nimble Ultra pipeline!")
    print(f"Schedule CSV: imprints/warships_and_navies/tang_schedule.csv")
    print(f"Source file: {output_file}")
