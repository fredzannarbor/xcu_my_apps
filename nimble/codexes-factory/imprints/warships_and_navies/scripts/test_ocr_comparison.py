#!/usr/bin/env python3
"""
Test OCR quality by comparing existing PDF OCR with Claude vision API on 10 random pages.
"""

import fitz  # PyMuPDF
import random
import json
import base64
from pathlib import Path
from datetime import datetime

# Import LLM caller
try:
    from nimble_llm_caller import call_model
except ImportError:
    print("Warning: nimble_llm_caller not available, will use placeholder")
    call_model = None

def extract_random_pages(pdf_path, num_pages=10, seed=42):
    """Extract random pages from PDF with their existing OCR text and images."""
    random.seed(seed)  # For reproducibility

    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    # Select random page numbers (avoiding first and last 10 pages which might be covers)
    page_numbers = random.sample(range(50, total_pages - 50), num_pages)
    page_numbers.sort()

    results = []
    output_dir = Path("output/ocr_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Extracting {num_pages} random pages...")
    print(f"Selected pages: {page_numbers}")

    for i, page_num in enumerate(page_numbers, 1):
        print(f"\nProcessing page {i}/{num_pages}: PDF page {page_num + 1}")

        page = doc[page_num]

        # Extract existing OCR text
        existing_text = page.get_text()

        # Extract page as image
        pix = page.get_pixmap(dpi=300)
        img_path = output_dir / f"page_{page_num+1:04d}.png"
        pix.save(str(img_path))

        # Convert image to base64 for Claude API
        with open(img_path, 'rb') as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')

        results.append({
            'page_number': page_num + 1,
            'existing_ocr': existing_text,
            'image_path': str(img_path),
            'image_base64': img_base64,
            'text_length': len(existing_text)
        })

        print(f"  Existing OCR length: {len(existing_text)} characters")

    doc.close()

    return results

def ocr_with_claude(image_base64, page_number):
    """Use Claude vision API to OCR a page image."""

    prompt = """Please transcribe all text visible in this historical document page.

This is a page from the Nimitz "Graybook" - WWII Pacific naval command summaries from 1941-1945.

Instructions:
1. Transcribe ALL visible text, including:
   - Headers, dates, and page numbers
   - Body text and paragraphs
   - Any handwritten notes or annotations
   - Classification markings
   - Tables and structured data

2. Preserve formatting where possible:
   - Use line breaks to match the original layout
   - Indicate tables with | separators if present
   - Note any illegible sections with [illegible]

3. Be precise with:
   - Dates and times
   - Ship names and designations
   - Geographic locations
   - Military terminology and abbreviations

Return only the transcribed text, no commentary."""

    if not call_model:
        return "[Claude API not available - placeholder text]"

    try:
        response = call_model(
            model="claude-3-5-sonnet-20241022",
            prompt=prompt,
            images=[{
                'type': 'base64',
                'source': {
                    'type': 'base64',
                    'media_type': 'image/png',
                    'data': image_base64
                }
            }],
            max_tokens=4000,
            temperature=0
        )

        return response.get('content', '[No response]')

    except Exception as e:
        return f"[Error during OCR: {str(e)}]"

def generate_comparison_report(results, output_path):
    """Generate a markdown report comparing OCR results."""

    report = f"""# Nimitz Graybook OCR Quality Comparison

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Test:** Comparison of existing PDF OCR vs Claude 3.5 Sonnet Vision API
**Sample Size:** {len(results)} randomly selected pages

## Summary

| Metric | Value |
|--------|-------|
| Total pages tested | {len(results)} |
| Average existing OCR length | {sum(r['text_length'] for r in results) / len(results):.0f} chars |
| Average Claude OCR length | {sum(len(r.get('claude_ocr', '')) for r in results) / len(results):.0f} chars |

## Page-by-Page Comparison

"""

    for i, result in enumerate(results, 1):
        page_num = result['page_number']
        existing_ocr = result['existing_ocr']
        claude_ocr = result.get('claude_ocr', '[Not yet processed]')

        report += f"""### Page {i}: PDF Page {page_num}

**Image:** `{result['image_path']}`

#### Existing PDF OCR ({len(existing_ocr)} characters)
```
{existing_ocr[:1000]}{'...' if len(existing_ocr) > 1000 else ''}
```

#### Claude 3.5 Sonnet OCR ({len(claude_ocr)} characters)
```
{claude_ocr[:1000]}{'...' if len(claude_ocr) > 1000 else ''}
```

---

"""

    report += f"""## Analysis

### Quality Observations
- Existing OCR is from 2012 digitization using OCR technology of that era
- Claude 3.5 Sonnet uses 2024-2025 vision AI technology
- Key differences to evaluate:
  - Accuracy of text recognition
  - Preservation of formatting
  - Handling of tables and structured data
  - Recognition of handwritten annotations
  - Accuracy with military terminology and ship names

### Cost Estimate
- Per-image cost: ~$0.005 (Claude 3.5 Sonnet)
- Total pages: 4,023
- Estimated total cost: ~$20-50 depending on output length

### Recommendation
[To be filled in after reviewing comparison results]

"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ Report saved to: {output_path}")

def main():
    pdf_path = "/Users/fred/xcu_my_apps/nimble/codexes-factory/input_files_by_imprint/big_five_warships_and_navies/MSC334_01_17_01 (1).pdf"

    # Extract random pages
    results = extract_random_pages(pdf_path, num_pages=10)

    # Save intermediate results
    output_dir = Path("output/ocr_test")
    json_path = output_dir / "ocr_test_data.json"

    # Save without base64 for readability
    results_for_json = [{k: v for k, v in r.items() if k != 'image_base64'} for r in results]
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results_for_json, f, indent=2)

    print(f"\n✅ Extracted data saved to: {json_path}")

    # OCR with Claude (if available)
    if call_model:
        print("\n🔄 Running Claude Vision API on extracted pages...")
        for i, result in enumerate(results, 1):
            print(f"  OCR page {i}/{len(results)}...")
            result['claude_ocr'] = ocr_with_claude(result['image_base64'], result['page_number'])
    else:
        print("\n⚠️  Claude API not available - generating partial report")

    # Generate comparison report
    report_path = output_dir / "ocr_comparison_report.md"
    generate_comparison_report(results, report_path)

    print("\n" + "="*80)
    print("OCR Comparison Test Complete!")
    print(f"Review the report at: {report_path}")
    print(f"Page images saved in: {output_dir}")

if __name__ == "__main__":
    main()
