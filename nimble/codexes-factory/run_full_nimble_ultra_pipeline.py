#!/usr/bin/env python3
"""
Run COMPLETE Nimble Ultra pipeline with LLM content generation.

Full workflow:
1. Load PDF source
2. Generate LLM content (bibliographic info, abstracts, context, passages, indices, mnemonics)
3. Assemble all sections
4. Generate LaTeX with enriched content
5. Compile final PDF

This script actually calls the LLMs to enrich the documents.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import LLM caller (current API as of Oct 2025)
try:
    from codexes.core.llm_caller import call_model_with_prompt
except ImportError:
    from src.codexes.core.llm_caller import call_model_with_prompt

# Import Nimble Ultra prepress
from imprints.nimble_ultra.prepress import NimbleUltraGlobalProcessor


def load_prompts():
    """Load Nimble Ultra prompts"""
    prompts_file = Path("imprints/nimble_ultra/prompts.json")

    with open(prompts_file, 'r') as f:
        return json.load(f)


def generate_content_with_llm(pdf_path: Path, prompts: dict):
    """Generate all LLM content sections for a document"""

    print(f"  Stage 2: Generating LLM content...")

    # Check for OCR text first
    ocr_file = Path("output/nimble_ultra_ocr") / f"{pdf_path.stem}_ocr.txt"

    if ocr_file.exists():
        print(f"    Using OCR text from {ocr_file.name}")
        with open(ocr_file, 'r') as f:
            full_text = f.read()
    else:
        # Read PDF text for prompts
        import fitz
        pdf = fitz.open(pdf_path)
        full_text = "\n\n".join([page.get_text() for page in pdf])
        pdf.close()

    # Truncate if too long (use first 100K chars)
    if len(full_text) > 100000:
        print(f"    Text truncated from {len(full_text):,} to 100,000 chars")
        full_text = full_text[:100000]
    else:
        print(f"    Using {len(full_text):,} chars of text")

    pipeline_content = {
        "front_matter": {},
        "back_matter": {}
    }

    # Front matter sections
    front_sections = [
        ("bibliographic_key_phrases", "Stage 2a: Bibliographic keywords"),
        ("basic_info", "Stage 2b: Basic metadata"),
        ("publishers_note", "Stage 2c: Publisher note"),
        ("historical_context", "Stage 2d: Historical context"),
        ("abstracts_x4", "Stage 2e: Four abstracts"),
        ("important_passages", "Stage 2f: Important passages")
    ]

    # Back matter sections
    back_sections = [
        ("index_persons", "Stage 2g: Person index"),
        ("index_places", "Stage 2h: Place index"),
        ("mnemonics", "Stage 2i: Mnemonics")
    ]

    sections = front_sections + back_sections

    for section_key, stage_label in sections:
        print(f"    {stage_label}...")

        # Find prompt (may have different key names)
        prompt_key = None
        for key in prompts:
            if section_key in key.lower() or key.lower() in section_key:
                prompt_key = key
                break

        if not prompt_key:
            print(f"      ⚠️ Prompt not found for {section_key}, skipping")
            continue

        prompt_template = prompts[prompt_key].get("messages", [{}])[-1].get("content", "")  # Get last message (user message)

        # Fill in document text (prompts use {book_content} placeholder)
        prompt = prompt_template.replace("{book_content}", full_text[:100000])  # Limit context

        try:
            # Call LLM with proper config structure
            prompt_config = {
                "messages": [{"role": "user", "content": prompt}],
                "params": {"temperature": 0.7, "max_tokens": 16384}
            }

            response = call_model_with_prompt(
                model_name="gemini/gemini-2.5-pro",
                prompt_config=prompt_config,
                response_format_type="text"
            )

            content = response.get("content", response.get("raw_content", ""))

            # Organize into front_matter or back_matter
            if section_key in ["index_persons", "index_places", "mnemonics"]:
                pipeline_content["back_matter"][section_key] = content
            else:
                pipeline_content["front_matter"][section_key] = content

            print(f"      ✓ Generated ({len(content)} chars)")

        except Exception as e:
            print(f"      ✗ Error: {e}")
            error_msg = f"[Content generation failed: {e}]"

            # Organize errors too
            if section_key in ["index_persons", "index_places", "mnemonics"]:
                pipeline_content["back_matter"][section_key] = error_msg
            else:
                pipeline_content["front_matter"][section_key] = error_msg

    return pipeline_content


def main():
    print("=" * 80)
    print("Nimble Ultra FULL Production Pipeline with LLM Content Generation")
    print("=" * 80)
    print()

    # Load prompts
    prompts = load_prompts()
    print(f"Loaded {len(prompts)} prompts")
    print()

    # Initialize processor
    processor = NimbleUltraGlobalProcessor()

    # Input files
    input_dir = Path("output/nimble_ultra_resized")
    output_dir = Path("output/nimble_ultra_full_pipeline")
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_dir.glob("*.pdf"))

    for pdf_file in pdf_files:
        print(f"\n{'=' * 80}")
        print(f"Processing: {pdf_file.name}")
        print('=' * 80)

        # Stage 1: Load PDF
        print(f"  Stage 1: Loading PDF...")
        print(f"    ✓ {pdf_file.name} ({pdf_file.stat().st_size / 1024 / 1024:.1f} MB)")

        # Stage 2: Generate LLM content
        pipeline_content = generate_content_with_llm(pdf_file, prompts)

        # Stages 3-5: Assembly, LaTeX, PDF
        print(f"  Stage 3-5: Assembly, LaTeX generation, PDF compilation...")

        metadata = {
            "source_pdf": str(pdf_file),
            "title": pdf_file.stem.replace("-", " ").replace("_", " "),
            "imprint": "Nimble Ultra",
            "publisher": "Nimble Books LLC",
            "_pipeline_content": pipeline_content  # Key field!
        }

        try:
            results = processor.process_manuscript(
                input_path=str(pdf_file),
                output_dir=str(output_dir / pdf_file.stem),
                metadata=metadata
            )

            print(f"\n  ✓ COMPLETE: {pdf_file.name}")
            if results.get('pdf_path'):
                print(f"    Final PDF: {results['pdf_path']}")
            print()

        except Exception as e:
            print(f"\n  ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("FULL PIPELINE COMPLETE")
    print("=" * 80)
    print(f"\nOutput: {output_dir}/")
    print("=" * 80)


if __name__ == "__main__":
    main()
