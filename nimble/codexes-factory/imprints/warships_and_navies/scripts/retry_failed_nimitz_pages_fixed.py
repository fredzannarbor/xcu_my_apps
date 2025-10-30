#!/usr/bin/env python3
"""
Retry failed OCR pages from Nimitz Graybook using direct litellm calls
"""

import json
import base64
import time
from pathlib import Path
from datetime import datetime

import fitz  # PyMuPDF
import litellm
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Configure litellm
litellm.telemetry = False
litellm.drop_params = True


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


def retry_ocr_page(pdf_doc, page_num, model="gpt-4o-mini", retries=3):
    """Retry OCR for a single page using litellm"""

    page = pdf_doc[page_num]

    # Convert page to PNG image
    mat = fitz.Matrix(2, 2)  # 2x scaling for better quality
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')

    # Create messages for vision API
    messages = [{
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_b64}"
                }
            },
            {
                "type": "text",
                "text": """Transcribe all text from this historical military document page with high accuracy.

Instructions:
- Transcribe ALL text exactly as it appears including headers, footers, page numbers, marginalia
- Preserve formatting, line breaks, and spacing as much as possible
- Maintain exact capitalization
- For unclear characters, make your best determination based on context
- Return ONLY the transcribed text with no commentary

Begin transcription:"""
            }
        ]
    }]

    for attempt in range(retries):
        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                max_tokens=4096,
                temperature=0.0
            )

            # Calculate cost
            cost = 0
            if hasattr(response, 'usage') and response.usage:
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens

                if "gpt-4o-mini" in model.lower():
                    cost = (prompt_tokens * 0.15 / 1_000_000) + (completion_tokens * 0.60 / 1_000_000)
                elif "gemini" in model.lower():
                    cost = (prompt_tokens * 0.075 / 1_000_000) + (completion_tokens * 0.30 / 1_000_000)

            return {
                "page_number": page_num,
                "page_number_human": page_num + 1,
                "success": True,
                "original_ocr_length": len(page.get_text()),
                "new_ocr_length": len(response.choices[0].message.content),
                "new_ocr_text": response.choices[0].message.content,
                "model": model,
                "timestamp": datetime.now().isoformat(),
                "tokens": {
                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                    "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                    "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0
                },
                "cost": cost,
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
    retry_results_file = ocr_dir / "ocr_results_retry_fixed.jsonl"

    # Remove old retry file if exists
    if retry_results_file.exists():
        retry_results_file.unlink()

    # Model to use
    model = "gpt-4o-mini"

    print("=" * 80)
    print("Nimitz Graybook OCR Retry - Failed Pages (Fixed)")
    print("=" * 80)
    print(f"Using model: {model}")
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

    # Process failed pages
    retry_results = []
    total_cost = 0.0
    total_tokens = 0
    success_count = 0

    print(f"Retrying {len(failed_pages)} failed pages...")
    print()

    for page_num in tqdm(failed_pages, desc="Processing"):
        result = retry_ocr_page(pdf_doc, page_num, model=model)

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
    print(f"Total cost: ${total_cost:.4f}")
    print(f"Avg cost per page: ${total_cost/success_count if success_count > 0 else 0:.4f}")
    print()
    print(f"Retry results saved to: {retry_results_file}")
    print()
    print("Next step: Run merge script to combine retry results with main file")
    print("=" * 80)


if __name__ == "__main__":
    main()
