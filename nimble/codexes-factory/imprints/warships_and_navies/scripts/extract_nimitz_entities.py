#!/usr/bin/env python3
"""
Extract entities from Nimitz Graybook OCR results using Groq Llama 4 Scout.
Uses 10M context window to process ~1600 pages per batch (3 total batches).
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict

import litellm
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Configure litellm
litellm.telemetry = False
litellm.drop_params = True


ENTITY_EXTRACTION_PROMPT = """You are an extremely knowledgeable naval history enthusiast with deep expertise in World War II Pacific Theater operations. You are aware of the proper names and designations of all US, Japanese, British, and Australian ships, submarines, small craft, aircraft, units, officers, and bases. When you index an entity, you use the most authoritative, widely accepted name or designation.

Your task is to extract four types of entities from this historical naval document:

1. **PERSONS**: All named individuals (officers, enlisted, civilians, enemy personnel)
   - Use full name with rank when available: "Nimitz, Chester W., ADM"
   - Include rank abbreviations (ADM, RADM, CAPT, CDR, etc.)
   - Note promotions if evident from context

2. **PLACES**: Geographic locations (islands, atolls, bases, ports, ocean areas)
   - Use authoritative names: "Pearl Harbor" not "Pearl"
   - Include island groups in parentheses: "Guadalcanal (Solomon Islands)"
   - Include both official names and code names if mentioned

3. **SHIPS**: Naval vessels of all types
   - US ships: "USS Enterprise (CV-6)" with hull number
   - Japanese ships: "IJN Yamato"
   - Include ship type: carriers (CV), battleships (BB), cruisers (CA/CL), destroyers (DD), submarines (SS)
   - Distinguish between ships with same name using hull numbers

4. **ORGANIZATIONS**: Military units, task forces, commands, bases
   - Task forces: "Task Force 16", "Task Force 38"
   - Commands: "CINCPAC", "SOWESPAC", "3rd Fleet"
   - Divisions and groups: "Carrier Division 2"
   - Shore commands and bases when functioning as organizational entities

INSTRUCTIONS:
- Extract ALL entities of these four types from the provided document pages
- Use standard authoritative names (check your knowledge of WWII Pacific operations)
- Remove duplicates within each category
- Return ONLY valid JSON in this exact format:

{
  "persons": ["Nimitz, Chester W., ADM", "Spruance, Raymond A., RADM", ...],
  "places": ["Pearl Harbor", "Midway Atoll", "Guadalcanal (Solomon Islands)", ...],
  "ships": ["USS Enterprise (CV-6)", "USS Hornet (CV-8)", "IJN Akagi", ...],
  "organizations": ["CINCPAC", "Task Force 16", "3rd Fleet", ...]
}

Do NOT include any commentary, explanations, or text outside the JSON structure.

BEGIN EXTRACTION:"""


def load_ocr_results(ocr_file: Path) -> List[Dict]:
    """Load OCR results from JSONL file"""
    results = []
    with open(ocr_file, 'r') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results


def create_batches(ocr_results: List[Dict], batch_size: int = 1600) -> List[List[Dict]]:
    """Split OCR results into batches for processing"""
    batches = []
    for i in range(0, len(ocr_results), batch_size):
        batches.append(ocr_results[i:i + batch_size])
    return batches


def format_batch_for_extraction(batch: List[Dict]) -> str:
    """Format a batch of OCR results into text for entity extraction"""
    formatted = []

    for entry in batch:
        page_num = entry.get("page_number", "?")
        text = entry.get("new_ocr_text", "")

        formatted.append(f"--- PAGE {page_num} ---\n{text}\n")

    return "\n".join(formatted)


def extract_entities_from_batch(batch_text: str, batch_num: int, total_batches: int, model: str = "groq/llama-3.3-70b-versatile") -> Dict:
    """Extract entities from a batch using Groq Llama 4 Scout"""

    print(f"\nProcessing batch {batch_num}/{total_batches}")
    print(f"Text length: {len(batch_text):,} characters")

    messages = [{
        "role": "user",
        "content": ENTITY_EXTRACTION_PROMPT + "\n\n" + batch_text
    }]

    try:
        response = litellm.completion(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=16384  # Enough for large entity lists
        )

        # Parse response
        content = response.choices[0].message.content
        entities = json.loads(content)

        # Calculate cost
        cost = 0
        if hasattr(response, 'usage') and response.usage:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens

            # Groq Llama 3.3 70B pricing: $0.59/1M input, $0.79/1M output
            cost = (prompt_tokens * 0.59 / 1_000_000) + (completion_tokens * 0.79 / 1_000_000)

        print(f"  ✓ Extracted: {len(entities.get('persons', []))} persons, "
              f"{len(entities.get('places', []))} places, "
              f"{len(entities.get('ships', []))} ships, "
              f"{len(entities.get('organizations', []))} organizations")
        print(f"  Cost: ${cost:.4f}")

        return {
            "success": True,
            "entities": entities,
            "tokens": {
                "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0
            },
            "cost": cost,
            "model": model
        }

    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "entities": {"persons": [], "places": [], "ships": [], "organizations": []}
        }


def merge_entity_lists(all_batch_results: List[Dict]) -> Dict:
    """Merge and deduplicate entities from all batches"""

    merged = {
        "persons": set(),
        "places": set(),
        "ships": set(),
        "organizations": set()
    }

    for batch_result in all_batch_results:
        if batch_result.get("success"):
            entities = batch_result.get("entities", {})
            for entity_type in merged.keys():
                merged[entity_type].update(entities.get(entity_type, []))

    # Convert sets back to sorted lists
    return {
        entity_type: sorted(list(entity_set))
        for entity_type, entity_set in merged.items()
    }


def main():
    # Paths
    ocr_file = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/nimitz_ocr_gemini/ocr_results.jsonl")
    output_dir = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/nimitz_ocr_gemini")

    # Model configuration
    model = "groq/llama-3.3-70b-versatile"  # 128K context window
    batch_size = 200  # Pages per batch (fits in 128K context)

    print("=" * 80)
    print("Nimitz Graybook Entity Extraction")
    print("=" * 80)
    print(f"Model: {model}")
    print(f"Context window: 128K tokens (~200 pages per batch)")
    print()

    # Load OCR results
    print("Loading OCR results...")
    ocr_results = load_ocr_results(ocr_file)
    print(f"Loaded {len(ocr_results)} pages")
    print()

    # Create batches
    print(f"Creating batches of {batch_size} pages...")
    batches = create_batches(ocr_results, batch_size)
    print(f"Created {len(batches)} batches")
    print()

    # Process each batch
    batch_results = []
    total_cost = 0.0
    total_tokens = 0

    for i, batch in enumerate(batches, 1):
        # Format batch
        batch_text = format_batch_for_extraction(batch)

        # Extract entities
        result = extract_entities_from_batch(batch_text, i, len(batches), model)
        batch_results.append(result)

        if result.get("success"):
            total_cost += result.get("cost", 0)
            total_tokens += result.get("tokens", {}).get("total_tokens", 0)

        # Save intermediate result
        batch_file = output_dir / f"entities_batch_{i}.json"
        with open(batch_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"  Saved: {batch_file}")

        # Rate limiting - small delay between batches
        if i < len(batches):
            time.sleep(2)

    print()
    print("=" * 80)
    print("Merging and deduplicating entities...")
    print("=" * 80)

    # Merge all entities
    merged_entities = merge_entity_lists(batch_results)

    print(f"Total unique entities:")
    print(f"  Persons: {len(merged_entities['persons'])}")
    print(f"  Places: {len(merged_entities['places'])}")
    print(f"  Ships: {len(merged_entities['ships'])}")
    print(f"  Organizations: {len(merged_entities['organizations'])}")
    print()

    # Save final merged results
    final_file = output_dir / "entities_all.json"
    with open(final_file, 'w') as f:
        json.dump({
            "extraction_date": datetime.now().isoformat(),
            "model": model,
            "total_pages": len(ocr_results),
            "batches_processed": len(batches),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "entities": merged_entities,
            "stats": {
                "persons": len(merged_entities['persons']),
                "places": len(merged_entities['places']),
                "ships": len(merged_entities['ships']),
                "organizations": len(merged_entities['organizations']),
                "total_entities": sum(len(v) for v in merged_entities.values())
            }
        }, f, indent=2)

    print(f"✓ Saved final results: {final_file}")
    print()

    # Save human-readable indices
    for entity_type, entities in merged_entities.items():
        index_file = output_dir / f"index_{entity_type}.txt"
        with open(index_file, 'w') as f:
            f.write(f"{'=' * 80}\n")
            f.write(f"NIMITZ GRAYBOOK - INDEX OF {entity_type.upper()}\n")
            f.write(f"{'=' * 80}\n\n")
            f.write(f"Total entries: {len(entities)}\n\n")
            for entity in entities:
                f.write(f"{entity}\n")
        print(f"✓ Saved index: {index_file}")

    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Total pages processed: {len(ocr_results)}")
    print(f"Batches: {len(batches)}")
    print(f"Total tokens: {total_tokens:,}")
    print(f"Total cost: ${total_cost:.2f}")
    print(f"Avg cost per page: ${total_cost/len(ocr_results):.4f}")
    print()
    print(f"Total unique entities: {sum(len(v) for v in merged_entities.values()):,}")
    print("=" * 80)


if __name__ == "__main__":
    main()
