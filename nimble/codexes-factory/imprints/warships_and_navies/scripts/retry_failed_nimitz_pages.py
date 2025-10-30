#!/usr/bin/env python3
"""
Retry failed OCR pages from Nimitz Graybook using gpt-4o-mini
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

import fitz  # PyMuPDF
from nimble_llm_caller import LLMCaller
from tqdm import tqdm


def load_existing_results(jsonl_path):
    """Load existing OCR results and identify failed pages"""
    results = {}
    failed_pages = []

    with open(jsonl_path, 'r') as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                page_num = entry.get('page_number')
                results[page_num] = entry

                if not entry.get('success', False):
                    failed_pages.append(page_num)

    return results, failed_pages


def retry_ocr_page(pdf_doc, page_num, llm_caller, retries=3):
    """Retry OCR for a single page using gemini/gemini-2.5-flash"""

    page = pdf_doc[page_num]

    # Convert page to image
    mat = fitz.Matrix(2, 2)  # 2x scaling for better quality
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")

    # Create prompt
    prompt = """Extract all text from this scanned document page.

Instructions:
- Transcribe exactly what you see, including all text, numbers, tables, and headers
- Preserve formatting, spacing, and line breaks as much as possible
- If text is unclear or illegible, use [illegible]
- For tables, preserve column alignment with spaces or tabs
- Include page numbers if visible

Return only the extracted text, no additional commentary."""

    for attempt in range(retries):
        try:
            # Use gemini/gemini-2.5-flash specifically
            response = llm_caller.call(
                model="gemini/gemini-2.5-flash",
                prompt=prompt,
                images=[img_data],
                temperature=0.0,
                max_tokens=4096
            )

            return {
                "page_number": page_num,
                "page_number_human": page_num + 1,
                "success": True,
                "original_ocr_length": len(page.get_text()),
                "new_ocr_length": len(response.content),
                "new_ocr_text": response.content,
                "model": response.model,
                "timestamp": datetime.now().isoformat(),
                "tokens": {
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens
                },
                "cost": response.cost,
                "retry_attempt": attempt + 1
            }

        except Exception as e:
            if attempt == retries - 1:
                return {
                    "page_number": page_num,
                    "page_number_human": page_num + 1,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "retry_attempt": attempt + 1
                }
            time.sleep(2 ** attempt)  # Exponential backoff

    return None


def main():
    # Paths
    pdf_path = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/imprints/nimble_books_llc/graybooks/MSC334_01_17_01.pdf")
    ocr_dir = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/nimitz_ocr_gemini")
    results_file = ocr_dir / "ocr_results.jsonl"
    retry_results_file = ocr_dir / "ocr_results_retry.jsonl"

    print("=" * 80)
    print("Nimitz Graybook OCR Retry - Failed Pages")
    print("=" * 80)
    print(f"Using model: gemini/gemini-2.5-flash")
    print()

    # Load existing results
    print("Loading existing results...")
    existing_results, failed_pages = load_existing_results(results_file)
    print(f"Found {len(failed_pages)} failed pages out of {len(existing_results)} total")
    print()

    if not failed_pages:
        print("No failed pages to retry!")
        return

    # Open PDF
    print(f"Opening PDF: {pdf_path}")
    pdf_doc = fitz.open(pdf_path)
    print(f"Total pages in PDF: {len(pdf_doc)}")
    print()

    # Initialize LLM caller
    llm_caller = LLMCaller()

    # Process failed pages
    retry_results = []
    total_cost = 0.0
    total_tokens = 0
    success_count = 0

    print(f"Retrying {len(failed_pages)} failed pages...")
    print()

    for page_num in tqdm(failed_pages, desc="Processing"):
        result = retry_ocr_page(pdf_doc, page_num, llm_caller)

        if result:
            retry_results.append(result)

            if result.get('success'):
                success_count += 1
                total_cost += result.get('cost', 0)
                total_tokens += result.get('tokens', {}).get('total_tokens', 0)

            # Write to retry file
            with open(retry_results_file, 'a') as f:
                f.write(json.dumps(result) + '\n')

        # Small delay between requests
        time.sleep(0.5)

    pdf_doc.close()

    # Print summary
    print()
    print("=" * 80)
    print("Retry Complete!")
    print("=" * 80)
    print(f"Pages retried: {len(failed_pages)}")
    print(f"Successful: {success_count}")
    print(f"Still failed: {len(failed_pages) - success_count}")
    print(f"Success rate: {success_count/len(failed_pages)*100:.1f}%")
    print()
    print(f"Total tokens: {total_tokens:,}")
    print(f"Total cost: ${total_cost:.2f}")
    print(f"Avg cost per page: ${total_cost/len(failed_pages):.4f}")
    print()
    print(f"Retry results saved to: {retry_results_file}")
    print()
    print("Next step: Run merge script to combine retry results with main file")
    print("=" * 80)


if __name__ == "__main__":
    main()