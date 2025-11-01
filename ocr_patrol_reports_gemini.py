#!/usr/bin/env python3
"""
OCR submarine patrol reports using Gemini 2.5 Flash (latest ultra-low cost vision model).

Features:
- Handles typed text, handwritten annotations, tables, and forms
- Distinguishes between original typed content and handwritten notes
- Preserves structure and formatting
- Checkpointing for resume capability
- Cost tracking

Estimated cost: ~$0.0001-0.0005 per page = $0.50-2.50 for all 4,662 pages
"""

import json
import base64
from pathlib import Path
from datetime import datetime
import time
import litellm
from dotenv import load_dotenv
import fitz  # PyMuPDF
import argparse

# Load environment variables
load_dotenv()

# Configure litellm
litellm.telemetry = False
litellm.drop_params = True

def extract_pdf_page_as_image(pdf_path, page_num, dpi=300):
    """
    Extract a single page from PDF as high-quality image for OCR.

    Args:
        pdf_path: Path to PDF file
        page_num: Page number (0-indexed)
        dpi: Resolution for rendering (300 recommended for OCR)

    Returns:
        PNG image bytes
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num]

    # Render page to image at specified DPI
    # zoom factor: dpi/72 (72 is default DPI)
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    # Convert to PNG bytes
    img_bytes = pix.tobytes("png")
    doc.close()

    return img_bytes

def ocr_page_with_gemini(image_bytes, page_num, submarine_name):
    """
    OCR a single page using Gemini 2.5 Flash vision.

    Specialized prompt for submarine patrol reports that handles:
    - Typed typewriter text (often faded)
    - Handwritten annotations and corrections
    - Tables and forms
    - Stamps and signatures
    """

    # Encode image
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

    # Construct vision request
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
                "text": """Transcribe all text from this WWII submarine patrol report page with high accuracy.

CRITICAL INSTRUCTIONS:
1. Transcribe ALL text exactly as it appears including:
   - Typed typewriter text (often faded)
   - Handwritten annotations, corrections, and marginalia
   - Headers, footers, page numbers, stamps
   - Tables, forms, and structured data
   - Coordinates, times, and numerical data

2. DISTINGUISH between typed and handwritten text:
   - For handwritten text, use [HANDWRITTEN: text here]
   - For stamps or official marks, use [STAMP: text here]
   - For signatures, use [SIGNATURE: name if legible]

3. Preserve formatting:
   - Maintain line breaks and spacing
   - Preserve table structure using | separators if present
   - Keep exact capitalization
   - Maintain indentation where meaningful

4. For unclear or degraded text:
   - Make best determination based on context
   - Use [UNCLEAR: best guess] if uncertain
   - Naval terminology: USS, torpedoes, periscope, depth charges, etc.
   - Common abbreviations: CDR, LCDR, LT, ENS, CO, XO, etc.

5. Special elements to preserve:
   - Coordinates (e.g., 35-12N, 125-45E)
   - Times (e.g., 0342, 1445)
   - Dates
   - Ship names and hull numbers
   - Tonnage figures
   - Ranges and bearings

6. Return ONLY the transcribed text - NO commentary, explanations, or meta-text

Begin transcription:"""
            }
        ]
    }]

    # Try multiple models in order of preference (cheapest/best first)
    models_to_try = [
        "gemini/gemini-2.5-flash",      # Latest (user specified)
        "gemini/gemini-2.0-flash-exp",  # Backup
        "gemini/gemini-1.5-flash",      # Fallback
        "gpt-4o-mini",                   # Last resort
    ]

    for model in models_to_try:
        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                max_tokens=8192,  # Patrol report pages can be dense
                temperature=0.0   # Deterministic for OCR
            )

            # Calculate cost
            cost = 0
            if hasattr(response, 'usage') and response.usage:
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens

                # Gemini pricing (approximate, verify with latest)
                if "gemini-2.5" in model.lower():
                    # Gemini 2.5 Flash pricing (estimated - verify actual)
                    cost = (prompt_tokens * 0.075 / 1_000_000) + (completion_tokens * 0.30 / 1_000_000)
                elif "gemini-2.0" in model.lower() or "gemini-1.5" in model.lower():
                    # Gemini 2.0/1.5 Flash pricing
                    cost = (prompt_tokens * 0.075 / 1_000_000) + (completion_tokens * 0.30 / 1_000_000)
                elif "gpt-4o-mini" in model.lower():
                    # GPT-4o-mini pricing
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
            if model == models_to_try[-1]:
                return {
                    "success": False,
                    "error": f"All models failed. Last error: {error_msg}",
                    "text": "",
                    "cost": 0
                }
            print(f"  ⚠️  {model} failed: {error_msg[:100]}... trying next model...")
            continue

def process_submarine_pdfs(
    input_dir="input_files_by_imprint/warships_and_navies/submarine_patrol_reports",
    output_dir="ocr_output",
    submarine_filter=None,
    dpi=300,
    sample_pages=None
):
    """
    Process submarine patrol report PDFs with Gemini OCR.

    Args:
        input_dir: Directory containing submarine PDF folders
        output_dir: Where to save OCR results
        submarine_filter: Process only this submarine (e.g., "SS-306_TANG")
        dpi: Resolution for page rendering
        sample_pages: If set, only process first N pages per PDF (for testing)
    """

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    # Find all submarine directories
    submarine_dirs = sorted([d for d in input_path.iterdir() if d.is_dir()])

    if submarine_filter:
        submarine_dirs = [d for d in submarine_dirs if d.name == submarine_filter]
        if not submarine_dirs:
            print(f"❌ Submarine not found: {submarine_filter}")
            return

    print(f"\n{'='*80}")
    print(f"Submarine Patrol Reports OCR with Gemini 2.5 Flash")
    print(f"Processing {len(submarine_dirs)} submarines")
    if sample_pages:
        print(f"SAMPLE MODE: First {sample_pages} pages per PDF only")
    print(f"{'='*80}\n")

    # Overall stats
    global_stats = {
        "total_submarines": 0,
        "total_pdfs": 0,
        "total_pages": 0,
        "total_cost": 0.0,
        "total_tokens": 0,
        "errors": 0,
        "start_time": datetime.now().isoformat()
    }

    for sub_dir in submarine_dirs:
        submarine_name = sub_dir.name
        print(f"\n{'='*80}")
        print(f"Processing: {submarine_name}")
        print(f"{'='*80}")

        # Create submarine output directory
        sub_output_dir = output_path / submarine_name
        sub_output_dir.mkdir(exist_ok=True, parents=True)

        # Find all PDFs for this submarine
        pdf_files = sorted(sub_dir.glob("*.pdf"))

        if not pdf_files:
            print(f"⚠️  No PDFs found in {sub_dir}")
            continue

        global_stats["total_submarines"] += 1

        for pdf_file in pdf_files:
            print(f"\n📄 Processing: {pdf_file.name}")

            # Open PDF to get page count
            doc = fitz.open(pdf_file)
            total_pages = len(doc)
            doc.close()

            # Determine pages to process
            pages_to_process = range(total_pages) if sample_pages is None else range(min(sample_pages, total_pages))

            print(f"   Pages: {len(pages_to_process)} of {total_pages}")

            global_stats["total_pdfs"] += 1

            # Load or create checkpoint for this PDF
            checkpoint_file = sub_output_dir / f"{pdf_file.stem}_checkpoint.json"
            if checkpoint_file.exists():
                with open(checkpoint_file) as f:
                    checkpoint = json.load(f)
                print(f"   📍 Resuming from page {checkpoint['last_completed_page'] + 1}")
                start_page = checkpoint['last_completed_page'] + 1
            else:
                checkpoint = {
                    "submarine_name": submarine_name,
                    "pdf_file": pdf_file.name,
                    "last_completed_page": -1,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "pages_processed": 0,
                    "errors": 0,
                    "start_time": datetime.now().isoformat()
                }
                start_page = 0

            # Open results file in append mode
            results_file = sub_output_dir / f"{pdf_file.stem}_ocr.jsonl"
            results_handle = open(results_file, 'a')

            pdf_start_time = time.time()

            try:
                for page_num in pages_to_process:
                    if page_num < start_page:
                        continue

                    page_start = time.time()

                    # Extract page as image
                    try:
                        image_bytes = extract_pdf_page_as_image(pdf_file, page_num, dpi=dpi)
                    except Exception as e:
                        print(f"   ❌ Page {page_num+1}: Failed to extract image: {e}")
                        checkpoint["errors"] += 1
                        continue

                    # OCR with Gemini
                    result = ocr_page_with_gemini(image_bytes, page_num, submarine_name)

                    # Save result
                    ocr_text = result.get("text", "") or ""  # Handle None case
                    page_result = {
                        "submarine_name": submarine_name,
                        "pdf_file": pdf_file.name,
                        "page_number": page_num,
                        "page_number_human": page_num + 1,
                        "success": result["success"],
                        "ocr_text": ocr_text,
                        "ocr_length": len(ocr_text),
                        "model": result.get("model", "unknown"),
                        "timestamp": datetime.now().isoformat()
                    }

                    if result["success"]:
                        page_result["tokens"] = result["tokens"]
                        page_result["cost"] = result["cost"]
                        checkpoint["total_tokens"] += result["tokens"].get("total_tokens", 0)
                        checkpoint["total_cost"] += result.get("cost", 0)
                        global_stats["total_tokens"] += result["tokens"].get("total_tokens", 0)
                        global_stats["total_cost"] += result.get("cost", 0)
                    else:
                        page_result["error"] = result["error"]
                        checkpoint["errors"] += 1
                        global_stats["errors"] += 1

                    # Write result
                    results_handle.write(json.dumps(page_result) + "\n")
                    results_handle.flush()

                    # Update checkpoint
                    checkpoint["last_completed_page"] = page_num
                    checkpoint["pages_processed"] += 1
                    global_stats["total_pages"] += 1

                    with open(checkpoint_file, 'w') as f:
                        json.dump(checkpoint, f, indent=2)

                    # Progress reporting
                    page_time = time.time() - page_start
                    elapsed = time.time() - pdf_start_time
                    pages_done = checkpoint["pages_processed"]
                    pages_remaining = len(pages_to_process) - pages_done

                    if pages_done > 0:
                        avg_time = elapsed / pages_done
                        eta_minutes = (avg_time * pages_remaining) / 60
                    else:
                        eta_minutes = 0

                    status = "✅" if result["success"] else "❌"
                    print(f"   {status} Page {page_num+1}/{total_pages} | "
                          f"Model: {result.get('model', 'N/A')[:25]} | "
                          f"OCR: {len(ocr_text)} chars | "
                          f"{page_time:.1f}s | "
                          f"Cost: ${checkpoint['total_cost']:.4f} | "
                          f"ETA: {eta_minutes:.0f}m")

                    # Rate limiting
                    time.sleep(0.1)

            finally:
                results_handle.close()

            pdf_time = time.time() - pdf_start_time
            print(f"\n   ✅ PDF Complete: {checkpoint['pages_processed']} pages in {pdf_time/60:.1f}m | Cost: ${checkpoint['total_cost']:.4f}")

    # Final global stats
    print(f"\n{'='*80}")
    print(f"✅ ALL SUBMARINES PROCESSED!")
    print(f"{'='*80}")
    print(f"Submarines: {global_stats['total_submarines']}")
    print(f"PDFs: {global_stats['total_pdfs']}")
    print(f"Pages: {global_stats['total_pages']}")
    print(f"Errors: {global_stats['errors']}")
    print(f"Total tokens: {global_stats['total_tokens']:,}")
    print(f"Total cost: ${global_stats['total_cost']:.2f}")
    print(f"Avg cost per page: ${global_stats['total_cost']/max(global_stats['total_pages'],1):.4f}")
    print(f"\nResults saved to: {output_path}")

    # Save global stats
    global_stats["end_time"] = datetime.now().isoformat()
    with open(output_path / "global_stats.json", 'w') as f:
        json.dump(global_stats, f, indent=2)

    return global_stats

def main():
    parser = argparse.ArgumentParser(
        description="OCR submarine patrol reports with Gemini 2.5 Flash"
    )
    parser.add_argument(
        "--input-dir",
        default="input_files_by_imprint/warships_and_navies/submarine_patrol_reports",
        help="Directory containing submarine PDF folders"
    )
    parser.add_argument(
        "--output-dir",
        default="ocr_output",
        help="Output directory for OCR results"
    )
    parser.add_argument(
        "--submarine",
        help="Process only this submarine (e.g., SS-306_TANG)"
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI for page rendering (default: 300)"
    )
    parser.add_argument(
        "--sample",
        type=int,
        help="Sample mode: process only first N pages per PDF (for testing)"
    )

    args = parser.parse_args()

    stats = process_submarine_pdfs(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        submarine_filter=args.submarine,
        dpi=args.dpi,
        sample_pages=args.sample
    )

    print("\n" + "="*80)
    print("OCR Complete!")
    print(f"Total cost: ${stats['total_cost']:.2f}")
    print("Next step: Use OCR'd text for annotation generation")
    print("="*80)

if __name__ == "__main__":
    main()
