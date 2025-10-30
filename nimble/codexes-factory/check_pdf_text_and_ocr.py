#!/usr/bin/env python3
"""
Check PDF text content and perform OCR if needed.
Uses vision LLM for scanned/image-only PDFs.
"""

import fitz
import base64
import litellm
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

litellm.telemetry = False


def check_text_content(pdf_path):
    """Check if PDF has sufficient embedded text"""
    pdf = fitz.open(pdf_path)

    page_count = len(pdf)
    total_text = 0
    for page in pdf:
        total_text += len(page.get_text())

    pdf.close()

    avg_per_page = total_text / page_count if page_count > 0 else 0

    return total_text, avg_per_page


def ocr_pdf_with_vision(pdf_path, output_file, model="gemini/gemini-2.5-pro"):
    """OCR PDF using vision LLM (like Nimitz approach)"""

    pdf = fitz.open(pdf_path)

    print(f"  Performing vision OCR on {len(pdf)} pages...")

    ocr_results = []

    for page_num in range(len(pdf)):
        page = pdf[page_num]

        # Convert to image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')

        # Vision prompt
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                },
                {
                    "type": "text",
                    "text": "Transcribe all text from this document page. Return only the text, preserving formatting."
                }
            ]
        }]

        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                max_tokens=4096
            )

            ocr_text = response.choices[0].message.content
            ocr_results.append(f"--- Page {page_num + 1} ---\n{ocr_text}\n")

            if (page_num + 1) % 10 == 0:
                print(f"    Processed {page_num + 1}/{len(pdf)} pages...")

        except Exception as e:
            print(f"    Error on page {page_num + 1}: {e}")
            ocr_results.append(f"--- Page {page_num + 1} ---\n[OCR failed]\n")

    pdf.close()

    # Save OCR text
    with open(output_file, 'w') as f:
        f.write("\n".join(ocr_results))

    print(f"  ✓ OCR complete, saved to {output_file}")


def main():
    print("=" * 80)
    print("PDF Text Check and OCR")
    print("=" * 80)
    print()

    input_dir = Path("output/nimble_ultra_resized")
    output_dir = Path("output/nimble_ultra_ocr")
    output_dir.mkdir(exist_ok=True)

    for pdf_file in input_dir.glob("*.pdf"):
        print(f"\n{pdf_file.name}:")

        total_text, avg_per_page = check_text_content(pdf_file)

        print(f"  Embedded text: {total_text:,} chars total, {avg_per_page:.0f} avg/page")

        if avg_per_page < 100:
            print(f"  ⚠️  Low text content - needs OCR")

            output_file = output_dir / f"{pdf_file.stem}_ocr.txt"

            if not output_file.exists():
                ocr_pdf_with_vision(pdf_file, output_file)
            else:
                print(f"  ✓ OCR already exists: {output_file}")
        else:
            print(f"  ✓ Sufficient embedded text")

    print("\n" + "=" * 80)
    print("Check complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
