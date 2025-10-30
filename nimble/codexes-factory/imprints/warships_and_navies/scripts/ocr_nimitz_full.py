#!/usr/bin/env python3
"""
Full OCR processing of Nimitz Graybook using Claude Vision API.
Processes all 4,023 pages with progress tracking and checkpointing.
"""

import fitz  # PyMuPDF
import json
import base64
from pathlib import Path
from datetime import datetime
import time
import litellm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure litellm
litellm.telemetry = False

def extract_page_image(page, scale=2.0):
    """Extract page as high-res PNG image data."""
    mat = fitz.Matrix(scale, scale)  # 2x = ~144 DPI
    pix = page.get_pixmap(matrix=mat)
    return pix.tobytes("png")

def ocr_page_with_claude(image_data, page_num):
    """OCR a single page using Claude Vision API."""

    # Encode image to base64
    image_b64 = base64.b64encode(image_data).decode('utf-8')

    # Construct vision API request
    messages = [{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_b64
                }
            },
            {
                "type": "text",
                "text": """Please transcribe all text from this historical document page with high accuracy.

Instructions:
- Transcribe ALL text exactly as it appears
- Preserve formatting, line breaks, and spacing
- Maintain capitalization exactly
- Include headers, footers, page numbers, and marginalia
- For unclear characters, make your best determination based on context
- Do not add commentary or notes, only the transcription

Return only the transcribed text."""
            }
        ]
    }]

    # Call Claude Vision API via litellm
    try:
        response = litellm.completion(
            model="claude-3-5-sonnet-20241022",
            messages=messages,
            max_tokens=4000,
            temperature=0.0  # Deterministic for OCR
        )

        return {
            "success": True,
            "text": response.choices[0].message.content,
            "tokens": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "text": ""
        }

def process_pdf_with_checkpointing(pdf_path, output_dir, start_page=0, end_page=None):
    """Process PDF with progress tracking and checkpointing."""

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Initialize checkpoint file
    checkpoint_file = output_path / "checkpoint.json"
    results_file = output_path / "ocr_results.jsonl"
    stats_file = output_path / "ocr_stats.json"

    # Load checkpoint if exists
    if checkpoint_file.exists():
        with open(checkpoint_file) as f:
            checkpoint = json.load(f)
        print(f"📍 Resuming from checkpoint: page {checkpoint['last_completed_page'] + 1}")
        start_page = checkpoint['last_completed_page'] + 1
    else:
        checkpoint = {
            "last_completed_page": start_page - 1,
            "total_tokens": 0,
            "pages_processed": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat()
        }

    # Open PDF
    print(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    if end_page is None:
        end_page = total_pages

    print(f"\n{'='*80}")
    print(f"OCR Processing: Pages {start_page} to {end_page-1} (total: {end_page - start_page})")
    print(f"Total pages in PDF: {total_pages}")
    print(f"{'='*80}\n")

    # Open results file in append mode
    results_file_handle = open(results_file, 'a')

    start_time = time.time()

    try:
        for page_num in range(start_page, end_page):
            page_start = time.time()

            # Extract page
            page = doc[page_num]

            # Get original OCR for comparison
            original_ocr = page.get_text("text")

            # Extract as image
            try:
                image_data = extract_page_image(page)
            except Exception as e:
                print(f"❌ Error extracting page {page_num}: {e}")
                checkpoint["errors"] += 1
                continue

            # OCR with Claude
            result = ocr_page_with_claude(image_data, page_num)

            # Save result
            page_result = {
                "page_number": page_num,
                "page_number_human": page_num + 1,
                "success": result["success"],
                "original_ocr_length": len(original_ocr),
                "new_ocr_length": len(result["text"]),
                "new_ocr_text": result["text"],
                "timestamp": datetime.now().isoformat()
            }

            if result["success"]:
                page_result["tokens"] = result["tokens"]
                checkpoint["total_tokens"] += result["tokens"].get("total_tokens", 0)
            else:
                page_result["error"] = result["error"]
                checkpoint["errors"] += 1

            # Write result to JSONL
            results_file_handle.write(json.dumps(page_result) + "\n")
            results_file_handle.flush()

            # Update checkpoint
            checkpoint["last_completed_page"] = page_num
            checkpoint["pages_processed"] += 1

            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)

            # Progress reporting
            page_time = time.time() - page_start
            elapsed = time.time() - start_time
            pages_done = page_num - start_page + 1
            pages_remaining = end_page - page_num - 1
            avg_time_per_page = elapsed / pages_done
            eta_seconds = avg_time_per_page * pages_remaining
            eta_minutes = eta_seconds / 60

            status = "✅" if result["success"] else "❌"
            print(f"{status} Page {page_num+1}/{total_pages} | "
                  f"OCR: {len(original_ocr)} → {len(result['text'])} chars | "
                  f"Time: {page_time:.1f}s | "
                  f"ETA: {eta_minutes:.1f} min | "
                  f"Tokens: {checkpoint['total_tokens']:,}")

            # Save stats every 10 pages
            if pages_done % 10 == 0:
                stats = {
                    "pages_processed": checkpoint["pages_processed"],
                    "pages_remaining": pages_remaining,
                    "total_tokens": checkpoint["total_tokens"],
                    "errors": checkpoint["errors"],
                    "elapsed_minutes": elapsed / 60,
                    "estimated_remaining_minutes": eta_minutes,
                    "avg_seconds_per_page": avg_time_per_page,
                    "last_update": datetime.now().isoformat()
                }
                with open(stats_file, 'w') as f:
                    json.dump(stats, f, indent=2)

            # Rate limiting - small delay between requests
            time.sleep(0.5)

    finally:
        results_file_handle.close()
        doc.close()

    total_time = time.time() - start_time

    # Final stats
    print(f"\n{'='*80}")
    print(f"✅ OCR Processing Complete!")
    print(f"{'='*80}")
    print(f"Pages processed: {checkpoint['pages_processed']}")
    print(f"Errors: {checkpoint['errors']}")
    print(f"Total tokens: {checkpoint['total_tokens']:,}")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Avg time per page: {total_time/checkpoint['pages_processed']:.1f}s")
    print(f"\nResults saved to: {results_file}")
    print(f"Checkpoint saved to: {checkpoint_file}")

    return checkpoint

if __name__ == "__main__":
    pdf_path = "/Users/fred/xcu_my_apps/nimble/codexes-factory/input_files_by_imprint/big_five_warships_and_navies/MSC334_01_17_01 (1).pdf"
    output_dir = "nimitz_ocr_enhanced"

    # Process all pages
    checkpoint = process_pdf_with_checkpointing(
        pdf_path=pdf_path,
        output_dir=output_dir,
        start_page=0,
        end_page=None  # Process all pages
    )

    print("\n" + "="*80)
    print("Next steps:")
    print("1. Review results in nimitz_ocr_enhanced/ocr_results.jsonl")
    print("2. Create enhanced searchable PDF with new OCR layer")
    print("="*80)