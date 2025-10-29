#!/usr/bin/env python3
"""
Entity harmonization using gemini-2.5-pro with semantic alphabetic batching.
Processes entities in letter-range batches (A-D, E-H, etc.) to ensure
variants are grouped together while fitting in output token limits.
"""

import json
import time
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

import litellm
from dotenv import load_dotenv

load_dotenv()

litellm.telemetry = False
litellm.drop_params = True


PERSONS_PROMPT = """You are an expert WWII Pacific Theater naval historian. Harmonize person name variants.

**RULES:**
1. Normalize capitalization: "NIMITZ" → "Nimitz, Chester W., Admiral"
2. Spell out ranks: "Gen" → "General", "Adm" → "Admiral", "RADM" → "Rear Admiral"
3. Same person, different ranks → create subentries
4. Only merge when HIGHLY CONFIDENT (use your historical knowledge)
5. Full official names when known

**EXAMPLE:**
Input: ["NIMITZ", "Nimitz, Admiral", "Nimitz, Chester W., ADM"]
Output:
```json
{{
  "Nimitz, Chester W., Admiral": {{
    "variants": ["NIMITZ", "Nimitz, Admiral", "Nimitz, Chester W., ADM"],
    "subentries": ["Commander in Chief, Pacific (1941-1945)", "Fleet Admiral (1944-1945)"]
  }}
}}
```

**ENTRIES FOR LETTERS {letter_range}:**
{entity_list}

Return complete JSON mapping for these entries only."""

PLACES_PROMPT = """You are an expert on Pacific Theater geography. Harmonize place names.

**RULES:**
1. **KEEP ALL COORDINATES** - they are legitimate references
2. Harmonize coordinate format: "DD-MM N, DDD-MM E" (consistent spacing)
3. Normalize place names: "OAHU" → "Oahu"
4. Format: "Specific (General)" e.g., "Guadalcanal (Solomon Islands)"

**EXAMPLE:**
```json
{{
  "Pearl Harbor": {{"variants": ["PEARL HARBOR", "Pearl Harbor"]}},
  "05-18 N, 125-50 E": {{"variants": ["05-18N, 125-50E", "05-18N,125-50E"], "type": "coordinate"}}
}}
```

**ENTRIES FOR LETTERS {letter_range}:**
{entity_list}

Return complete JSON mapping."""

SHIPS_PROMPT = """You are an expert on WWII naval vessels. Harmonize ship entries.

**RULES:**
1. Standard format: "Name (Hull Number)" without USS/IJN prefix
2. **KEEP generic types** like "DD", "AK" - mark as "[unspecified]"
3. Normalize capitalization
4. Merge variants of same ship

**EXAMPLE:**
```json
{{
  "Enterprise (CV-6)": {{"variants": ["USS Enterprise", "Enterprise (CV-6)", "ENTERPRISE (CV-6)"]}},
  "DD [unspecified]": {{"variants": ["DD", "1 DD"], "note": "Generic destroyer reference"}}
}}
```

**ENTRIES FOR LETTERS/CATEGORIES {letter_range}:**
{entity_list}

Return complete JSON mapping."""

ORGANIZATIONS_PROMPT = """You are an expert on WWII Pacific military organizations. Harmonize entries.

**RULES:**
1. CINCPAC ≠ COMINCH (different commands, keep separate!)
2. Normalize: "CINCPAC" (standard form)
3. "TF 16" → "Task Force 16"
4. Spell out abbreviations in subentries

**EXAMPLE:**
```json
{{
  "CINCPAC": {{
    "variants": ["CINCPAC", "CinCPac"],
    "full_name": "Commander in Chief, Pacific"
  }},
  "COMINCH": {{
    "variants": ["COMINCH", "Cominch"],
    "full_name": "Commander in Chief, U.S. Fleet"
  }}
}}
```

**ENTRIES FOR LETTERS {letter_range}:**
{entity_list}

Return complete JSON mapping."""


def get_alphabetic_batches(entities: List[str], ranges: List[str]) -> Dict[str, List[str]]:
    """Group entities by alphabetic ranges"""
    batches = defaultdict(list)

    for entity in entities:
        first_char = entity[0].upper() if entity else 'Z'

        # Find which range this belongs to
        for range_key in ranges:
            range_letters = range_key.replace('-', '')
            if first_char in range_letters:
                batches[range_key].append(entity)
                break
        else:
            # Numbers and special chars go to last batch
            batches[ranges[-1]].append(entity)

    return dict(batches)


def harmonize_batch(entities: List[str], entity_type: str, letter_range: str, model: str = "gemini/gemini-2.5-pro"):
    """Harmonize one alphabetic batch"""

    prompts = {
        "persons": PERSONS_PROMPT,
        "places": PLACES_PROMPT,
        "ships": SHIPS_PROMPT,
        "organizations": ORGANIZATIONS_PROMPT
    }

    prompt = prompts[entity_type].format(
        letter_range=letter_range,
        entity_list="\n".join(entities)
    )

    try:
        # Enable grounding
        extra_body = {
            "google_search_retrieval": {
                "dynamic_retrieval_config": {
                    "mode": "MODE_DYNAMIC",
                    "dynamic_threshold": 0.3
                }
            }
        }

        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=16384,  # Gemini 2.5 Pro limit
            extra_body=extra_body
        )

        content = response.choices[0].message.content

        # Extract JSON
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        elif "```" in content:
            json_start = content.find("```") + 3
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()

        harmonized = json.loads(content)

        # Calculate cost
        cost = 0
        if hasattr(response, 'usage') and response.usage:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            # Gemini 2.5 Pro pricing
            cost = (prompt_tokens * 1.25 / 1_000_000) + (completion_tokens * 5.0 / 1_000_000)

        return harmonized, cost, None

    except json.JSONDecodeError as e:
        return {}, 0.0, f"JSON error: {str(e)}"
    except Exception as e:
        return {}, 0.0, f"Error: {str(e)}"


def main():
    print("=" * 80)
    print("Entity Harmonization - Alphabetic Batching")
    print("Model: gemini-2.5-pro with grounding")
    print("=" * 80)
    print()

    # Load data
    refined_file = Path("nimitz_ocr_gemini/entities_refined.json")
    with open(refined_file, 'r') as f:
        data = json.load(f)

    entities = data["entities"]

    # Load page mappings
    page_index_file = Path("nimitz_ocr_gemini/entity_page_index.json")
    with open(page_index_file, 'r') as f:
        page_index_data = json.load(f)

    entity_page_mappings = page_index_data["entity_page_mappings"]

    # Define alphabetic ranges (tuned to keep batches manageable)
    letter_ranges = [
        "ABCD", "EFGH", "IJKL", "MNOP", "QRST", "UVWXYZ0-9"
    ]

    total_cost = 0.0
    all_harmonized = {}

    for entity_type in ["persons", "places", "ships", "organizations"]:
        print(f"\n{'=' * 80}")
        print(f"{entity_type.upper()}")
        print('=' * 80)
        print(f"Total entries: {len(entities[entity_type]):,}")

        # Group into alphabetic batches
        batches = get_alphabetic_batches(entities[entity_type], letter_ranges)

        print(f"Batches: {len(batches)}")
        for range_key, batch_entities in batches.items():
            print(f"  {range_key}: {len(batch_entities):,} entries")
        print()

        harmonized_type = {}

        for range_key in letter_ranges:
            if range_key not in batches:
                continue

            batch = batches[range_key]
            print(f"  Processing {range_key} ({len(batch):,} entries)...", end=" ")

            harmonized_batch, cost, error = harmonize_batch(batch, entity_type, range_key)

            if error:
                print(f"✗ {error}")
                # Keep originals
                for entity in batch:
                    harmonized_type[entity] = {"variants": [entity], "subentries": []}
            else:
                print(f"✓ ${cost:.4f} - {len(harmonized_batch):,} harmonized")
                harmonized_type.update(harmonized_batch)
                total_cost += cost

            # Save checkpoint after each batch
            checkpoint_file = Path(f"nimitz_ocr_gemini/checkpoint_{entity_type}_{range_key}.json")
            with open(checkpoint_file, 'w') as f:
                json.dump(harmonized_batch if not error else {}, f, indent=2)

            time.sleep(1)  # Rate limiting

        all_harmonized[entity_type] = harmonized_type

        print(f"\n  {entity_type.capitalize()} complete: {len(harmonized_type):,} final entries")
        print(f"  Reduction: {len(entities[entity_type]) - len(harmonized_type):,}")

    # Merge with page references
    print("\n" + "=" * 80)
    print("Merging with page references...")
    print("=" * 80)

    final_indices = {}

    for entity_type in all_harmonized:
        final_indices[entity_type] = {}

        for authoritative, data in all_harmonized[entity_type].items():
            all_pages = set()

            for variant in data.get("variants", [authoritative]):
                if variant in entity_page_mappings[entity_type]:
                    all_pages.update(entity_page_mappings[entity_type][variant])

            sorted_pages = sorted(list(all_pages), key=lambda x: (int(x.split('-')[0]), int(x.split(':')[1])))

            final_indices[entity_type][authoritative] = {
                "pages": sorted_pages,
                "page_count": len(sorted_pages),
                "subentries": data.get("subentries", []),
                "variants_merged": data.get("variants", [authoritative])
            }

    # Save final
    output_file = Path("nimitz_ocr_gemini/indices_harmonized_pro.json")
    with open(output_file, 'w') as f:
        json.dump({
            "harmonization_date": "2025-10-27",
            "model": "gemini/gemini-2.5-pro",
            "grounding": "enabled",
            "total_cost": total_cost,
            "indices": final_indices,
            "stats": {
                entity_type: {
                    "total_entries": len(final_indices[entity_type]),
                    "total_page_refs": sum(len(v["pages"]) for v in final_indices[entity_type].values())
                }
                for entity_type in final_indices
            }
        }, f, indent=2)

    print(f"\n✓ Saved: {output_file}")
    print()
    print("=" * 80)
    print("HARMONIZATION COMPLETE")
    print("=" * 80)
    print(f"Total cost: ${total_cost:.2f}")
    print(f"\nFinal counts:")
    for et in final_indices:
        print(f"  {et.capitalize()}: {len(final_indices[et]):,}")
    print(f"  TOTAL: {sum(len(v) for v in final_indices.values()):,}")
    print("=" * 80)


if __name__ == "__main__":
    main()
