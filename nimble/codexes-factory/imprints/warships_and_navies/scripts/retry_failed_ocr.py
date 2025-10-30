#!/usr/bin/env python3
"""
Retry failed OCR pages using GPT-4o-mini (cost-efficient alternative) and update results.
"""

import json
import base64
from pathlib import Path
import time
import litellm
from dotenv import load_dotenv

load_dotenv()
litellm.telemetry = False
litellm.drop_params = True

def ocr_page_with_vision(image_path, page_num):
    """OCR a single page using GPT-4o-mini."""

    with open(image_path, 'rb') as f:
        image_data = f.read()
    image_b64 = base64.b64encode(image_data).decode('utf-8')

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

    try:
        response = litellm.completion(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=4096,
            temperature=0.0
        )

        # GPT-4o-mini pricing: Input $0.15/1M, Output $0.60/1M
        cost = (response.usage.prompt_tokens * 0.15 / 1_000_000) + \
               (response.usage.completion_tokens * 0.60 / 1_000_000)

        return {
            "success": True,
            "text": response.choices[0].message.content,
            "model": "gpt-4o-mini",
            "tokens": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "cost": cost
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "text": "",
            "cost": 0
        }

def main():
    results_file = Path("nimitz_ocr_gemini/ocr_results.jsonl")
    pages_dir = Path("nimitz_pages")

    print("=" * 80)
    print("Retrying Failed OCR Pages with GPT-4o-mini")
    print("=" * 80)

    # Read all results and identify failures
    print("\n1. Loading existing results...")
    all_results = []
    failed_pages = []

    with open(results_file, 'r') as f:
        for line in f:
            result = json.loads(line)
            all_results.append(result)
            if not result["success"]:
                failed_pages.append(result["page_number"])

    print(f"   Found {len(failed_pages)} failed pages")
    print(f"   Page numbers: {min(failed_pages)} to {max(failed_pages)}")

    # Retry failed pages
    print(f"\n2. Retrying {len(failed_pages)} pages with GPT-4o-mini...")
    retried_results = {}
    total_cost = 0
    successes = 0
    failures = 0

    for i, page_num in enumerate(failed_pages, 1):
        image_path = pages_dir / f"page_{page_num:05d}.png"

        print(f"   [{i}/{len(failed_pages)}] Page {page_num + 1}...", end=" ")

        result = ocr_page_with_vision(image_path, page_num)
        retried_results[page_num] = result
        total_cost += result.get("cost", 0)

        if result["success"]:
            print(f"✅ {len(result['text'])} chars | ${result['cost']:.4f}")
            successes += 1
        else:
            print(f"❌ {result['error'][:50]}")
            failures += 1

        time.sleep(0.5)  # Rate limiting - more conservative

    print(f"\n3. Retry Results:")
    print(f"   Successes: {successes}")
    print(f"   Failures: {failures}")
    print(f"   Cost: ${total_cost:.2f}")

    # Update results
    print(f"\n4. Updating results file...")
    updated_results = []
    updates_made = 0

    for result in all_results:
        page_num = result["page_number"]

        if page_num in retried_results and retried_results[page_num]["success"]:
            # Replace with successful retry
            result["success"] = True
            result["new_ocr_text"] = retried_results[page_num]["text"]
            result["new_ocr_length"] = len(retried_results[page_num]["text"])
            result["model"] = retried_results[page_num]["model"]
            result["tokens"] = retried_results[page_num]["tokens"]
            result["retry_cost"] = retried_results[page_num]["cost"]
            updates_made += 1

        updated_results.append(result)

    # Write updated results
    backup_file = results_file.with_suffix('.jsonl.backup')
    results_file.rename(backup_file)
    print(f"   Backed up original to: {backup_file}")

    with open(results_file, 'w') as f:
        for result in updated_results:
            f.write(json.dumps(result) + '\n')

    print(f"   Updated {updates_made} entries in results file")

    # Final statistics
    final_successes = sum(1 for r in updated_results if r["success"])
    final_failures = sum(1 for r in updated_results if not r["success"])

    print("\n" + "=" * 80)
    print("FINAL STATISTICS")
    print("=" * 80)
    print(f"Total pages: {len(updated_results)}")
    print(f"Successful: {final_successes} ({final_successes/len(updated_results)*100:.1f}%)")
    print(f"Failed: {final_failures} ({final_failures/len(updated_results)*100:.1f}%)")
    print(f"Retry cost: ${total_cost:.2f}")
    print("\n✅ Complete! Updated results saved to:", results_file)

if __name__ == "__main__":
    main()
