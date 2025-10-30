#!/usr/bin/env python3
"""
OCR Nimitz Graybook pages using Gemini Flash (ultra-low cost vision model).
Estimated cost: $1-3 for all 4,023 pages vs $50-100 for Claude.
"""

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
litellm.drop_params = True  # Drop unsupported params

def ocr_image_with_gemini(image_path, page_num):
    """OCR a single image using Gemini Flash vision."""

    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = f.read()
    image_b64 = base64.b64encode(image_data).decode('utf-8')

    # Construct vision request for Gemini format
    messages = [{
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_b64}"
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

    # Try multiple models in order of preference (cheapest first)
    models_to_try = [
        "gemini/gemini-2.0-flash-exp",  # Latest, fastest, cheapest
        "gemini/gemini-1.5-flash",      # Fallback
        "gpt-4o-mini",                   # Fallback if Gemini fails
    ]

    for model in models_to_try:
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

                # Gemini Flash pricing (as of late 2024)
                # Input: $0.075 / 1M tokens, Output: $0.30 / 1M tokens
                if "gemini" in model.lower():
                    cost = (prompt_tokens * 0.075 / 1_000_000) + (completion_tokens * 0.30 / 1_000_000)
                elif "gpt-4o-mini" in model.lower():
                    # GPT-4o-mini: Input $0.15/1M, Output $0.60/1M
                    cost = (prompt_tokens * 0.15 / 1_000_000) + (completion_tokens * 0.60 / 1_000_000)

            return {
                "success": True,
                "text": response.choices[0].message.content,
                "model": model,
                "tokens": {
                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                    "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                    "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0
                },
                "cost": cost
            }
        except Exception as e:
            error_msg = str(e)
            # If this model failed, try next one
            if model == models_to_try[-1]:
                # Last model, return error
                return {
                    "success": False,
                    "error": f"All models failed. Last error: {error_msg}",
                    "text": "",
                    "cost": 0
                }
            # Try next model
            print(f"  ⚠️  {model} failed, trying next model...")
            continue

def process_pages_with_checkpointing(pages_dir="nimitz_pages", output_dir="nimitz_ocr_gemini", start_page=0, end_page=None):
    """Process pages with checkpointing."""

    pages_path = Path(pages_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Load manifest
    manifest_file = pages_path / "manifest.json"
    with open(manifest_file) as f:
        manifest = json.load(f)

    total_pages = manifest["total_pages"]
    if end_page is None:
        end_page = total_pages

    # Load or create checkpoint
    checkpoint_file = output_path / "checkpoint.json"
    if checkpoint_file.exists():
        with open(checkpoint_file) as f:
            checkpoint = json.load(f)
        print(f"📍 Resuming from checkpoint: page {checkpoint['last_completed_page'] + 1}")
        start_page = checkpoint['last_completed_page'] + 1
    else:
        checkpoint = {
            "last_completed_page": start_page - 1,
            "total_tokens": 0,
            "total_cost": 0.0,
            "pages_processed": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat()
        }

    # Open results file in append mode
    results_file = output_path / "ocr_results.jsonl"
    results_handle = open(results_file, 'a')

    print(f"\n{'='*80}")
    print(f"OCR Processing with Gemini Flash (ultra-low cost)")
    print(f"Pages {start_page} to {end_page-1} (total: {end_page - start_page})")
    print(f"Total pages in dataset: {total_pages}")
    print(f"{'='*80}\n")

    start_time = time.time()

    try:
        for page_num in range(start_page, end_page):
            page_start = time.time()

            page_info = manifest["pages"][page_num]
            image_path = pages_path / page_info["image_filename"]

            # OCR with Gemini
            result = ocr_image_with_gemini(image_path, page_num)

            # Save result
            page_result = {
                "page_number": page_num,
                "page_number_human": page_num + 1,
                "success": result["success"],
                "original_ocr_length": page_info["original_ocr_length"],
                "new_ocr_length": len(result["text"]),
                "new_ocr_text": result["text"],
                "model": result.get("model", "unknown"),
                "timestamp": datetime.now().isoformat()
            }

            if result["success"]:
                page_result["tokens"] = result["tokens"]
                page_result["cost"] = result["cost"]
                checkpoint["total_tokens"] += result["tokens"].get("total_tokens", 0)
                checkpoint["total_cost"] += result.get("cost", 0)
            else:
                page_result["error"] = result["error"]
                checkpoint["errors"] += 1

            # Write result
            results_handle.write(json.dumps(page_result) + "\n")
            results_handle.flush()

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
            avg_time = elapsed / pages_done
            eta_minutes = (avg_time * pages_remaining) / 60

            status = "✅" if result["success"] else "❌"
            print(f"{status} Page {page_num+1}/{total_pages} | "
                  f"Model: {result.get('model', 'N/A')[:20]} | "
                  f"OCR: {page_info['original_ocr_length']} → {len(result['text'])} chars | "
                  f"{page_time:.1f}s | "
                  f"ETA: {eta_minutes:.0f}m | "
                  f"Cost: ${checkpoint['total_cost']:.4f}")

            # Save stats every 50 pages
            if pages_done % 50 == 0:
                stats = {
                    "pages_processed": checkpoint["pages_processed"],
                    "pages_remaining": pages_remaining,
                    "total_tokens": checkpoint["total_tokens"],
                    "total_cost": checkpoint["total_cost"],
                    "errors": checkpoint["errors"],
                    "elapsed_minutes": elapsed / 60,
                    "estimated_remaining_minutes": eta_minutes,
                    "avg_seconds_per_page": avg_time,
                    "avg_cost_per_page": checkpoint["total_cost"] / checkpoint["pages_processed"],
                    "last_update": datetime.now().isoformat()
                }
                with open(output_path / "stats.json", 'w') as f:
                    json.dump(stats, f, indent=2)

            # Rate limiting (Gemini Flash has high limits, but be respectful)
            time.sleep(0.1)

    finally:
        results_handle.close()

    total_time = time.time() - start_time

    # Final stats
    print(f"\n{'='*80}")
    print(f"✅ OCR Processing Complete!")
    print(f"{'='*80}")
    print(f"Pages processed: {checkpoint['pages_processed']}")
    print(f"Errors: {checkpoint['errors']}")
    print(f"Total tokens: {checkpoint['total_tokens']:,}")
    print(f"Total cost: ${checkpoint['total_cost']:.2f}")
    print(f"Avg cost per page: ${checkpoint['total_cost']/checkpoint['pages_processed']:.4f}")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Avg time per page: {total_time/checkpoint['pages_processed']:.1f}s")
    print(f"\nResults: {results_file}")

    return checkpoint

if __name__ == "__main__":
    checkpoint = process_pages_with_checkpointing()

    print("\n" + "="*80)
    print("OCR Enhancement Complete!")
    print(f"Total cost: ${checkpoint['total_cost']:.2f}")
    print("Next step: Create enhanced searchable PDF")
    print("="*80)
