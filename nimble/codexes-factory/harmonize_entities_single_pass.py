#!/usr/bin/env python3
"""
Single-pass entity harmonization using gemini-2.5-flash-lite.
Processes entire entity list at once to catch all variants.
Includes checkpointing and chunked output handling.
"""

import json
import time
from pathlib import Path
from typing import Dict, List

import litellm
from dotenv import load_dotenv

load_dotenv()

litellm.telemetry = False
litellm.drop_params = True


# Separate prompts for each entity type with specific rules

PERSONS_HARMONIZATION_PROMPT = """You are an expert WWII Pacific Theater naval historian. Harmonize these person name variants following these rules:

**RULES:**
1. Normalize capitalization: "NIMITZ" → "Nimitz, Chester W., ADM"
2. Spell out ranks: "Gen" → "General", "Adm" → "Admiral"
3. Same person, different ranks → use subentries (e.g., "Spruance, Raymond A." with subentries for "RADM (1942)", "VADM (1944)", "ADM (1945)")
4. Only merge when HIGHLY CONFIDENT same person
5. Use full official names when known
6. Preserve uncertain entries separately

**FORMAT:**
```json
{{
  "Nimitz, Chester W., Admiral": {{
    "variants": ["NIMITZ", "Nimitz, Admiral", "Nimitz, Chester W., ADM"],
    "subentries": ["Commander in Chief, Pacific (1941-1945)", "Fleet Admiral (1944)"]
  }},
  "Uncertain Entry": {{
    "variants": ["only_this_one"],
    "subentries": []
  }}
}}
```

**ENTRIES ({count} total):**
{entity_list}

Return complete JSON mapping."""

PLACES_HARMONIZATION_PROMPT = """You are an expert on Pacific Theater geography. Harmonize these place names:

**RULES:**
1. **KEEP coordinates** - they are legitimate references
2. Harmonize coordinates to consistent format: "DD-MM N, DDD-MM E" or decimal degrees
3. Normalize place names: "OAHU" → "Oahu"
4. Standard format: "Specific (General)" e.g., "Guadalcanal (Solomon Islands)"
5. Merge obvious variants only

**COORDINATE EXAMPLES:**
- "05-18N, 125-50E" → "05-18 N, 125-50 E" (consistent spacing)
- "30.5 N 179.5 E" → keep as is (decimal format)

**FORMAT:**
```json
{{
  "Pearl Harbor": {{
    "variants": ["PEARL HARBOR", "Pearl Harbor", "Pearl harbor"],
    "type": "naval_base"
  }},
  "05-18 N, 125-50 E": {{
    "variants": ["05-18N, 125-50E", "05-18N,125-50E"],
    "type": "coordinate"
  }}
}}
```

**ENTRIES ({count} total):**
{entity_list}

Return complete JSON mapping."""

SHIPS_HARMONIZATION_PROMPT = """You are an expert on WWII naval vessels. Harmonize these ship entries:

**RULES:**
1. Normalize capitalization
2. Standard format: "Name (Hull Number)" without USS/IJN prefix
3. **KEEP generic references** like "DD", "AK" - they are legitimate
4. Distinguish generic types: "DD [unspecified]" vs "DD [damaged]" if context suggests different roles
5. For now, keep all generic references as-is until we can analyze context

**FORMAT:**
```json
{{
  "Enterprise (CV-6)": {{
    "variants": ["USS Enterprise", "Enterprise (CV-6)", "ENTERPRISE (CV-6)", "Enterprise"],
    "type": "carrier"
  }},
  "DD [unspecified]": {{
    "variants": ["DD", "1 DD"],
    "type": "generic_destroyer"
  }}
}}
```

**ENTRIES ({count} total):**
{entity_list}

Return complete JSON mapping."""

ORGANIZATIONS_HARMONIZATION_PROMPT = """You are an expert on WWII Pacific military organizations. Harmonize these entries:

**RULES:**
1. CINCPAC ≠ COMINCH (different commands, keep separate!)
2. Normalize capitalization: "CINCPAC" is standard
3. Merge variants of same organization
4. Spell out abbreviations in subentries
5. Task Force variants: "TF 16" → "Task Force 16"

**FORMAT:**
```json
{{
  "CINCPAC": {{
    "variants": ["CINCPAC", "CinCPac", "CINPAC"],
    "full_name": "Commander in Chief, Pacific",
    "subentries": []
  }},
  "COMINCH": {{
    "variants": ["COMINCH", "Cominch", "COMICH"],
    "full_name": "Commander in Chief, U.S. Fleet",
    "subentries": []
  }}
}}
```

**ENTRIES ({count} total):**
{entity_list}

Return complete JSON mapping."""


def harmonize_entity_type_single_pass(
    entity_list: List[str],
    entity_type: str,
    model: str = "gemini/gemini-2.5-flash-lite"
) -> Dict:
    """Harmonize all entities of one type in a single pass"""

    # Select prompt based on type
    prompts = {
        "persons": PERSONS_HARMONIZATION_PROMPT,
        "places": PLACES_HARMONIZATION_PROMPT,
        "ships": SHIPS_HARMONIZATION_PROMPT,
        "organizations": ORGANIZATIONS_HARMONIZATION_PROMPT
    }

    prompt = prompts[entity_type].format(
        count=len(entity_list),
        entity_list="\n".join(entity_list)
    )

    print(f"  Sending {len(entity_list):,} entries to {model}...")
    print(f"  Prompt size: ~{len(prompt):,} characters")

    try:
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=32768  # Large output for comprehensive mapping
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
            # Gemini Flash Lite pricing
            cost = (prompt_tokens * 0.075 / 1_000_000) + (completion_tokens * 0.30 / 1_000_000)

        print(f"  ✓ Success! Cost: ${cost:.4f}")
        print(f"  Harmonized to: {len(harmonized):,} authoritative entries")
        print(f"  Reduction: {len(entity_list) - len(harmonized):,} ({(len(entity_list)-len(harmonized))/len(entity_list)*100:.1f}%)")

        return harmonized, cost

    except json.JSONDecodeError as e:
        print(f"  ✗ JSON parsing error: {e}")
        print(f"  Response length: {len(content)} chars")
        print(f"  Saving raw response for debugging...")

        # Save problematic response
        debug_file = Path(f"nimitz_ocr_gemini/harmonization_debug_{entity_type}.txt")
        with open(debug_file, 'w') as f:
            f.write(content)
        print(f"  Saved to: {debug_file}")

        # Return as-is (no harmonization)
        return {entity: {"variants": [entity], "subentries": []} for entity in entity_list}, 0.0

    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return {entity: {"variants": [entity], "subentries": []} for entity in entity_list}, 0.0


def main():
    print("=" * 80)
    print("Single-Pass Entity Harmonization")
    print("Model: gemini-2.5-flash-lite")
    print("Standards: CMOS 18th Ed + Naval History")
    print("=" * 80)
    print()

    # Load refined entities
    refined_file = Path("nimitz_ocr_gemini/entities_refined.json")
    with open(refined_file, 'r') as f:
        data = json.load(f)

    entities = data["entities"]

    # Load page mappings
    print("Loading entity-page index...")
    page_index_file = Path("nimitz_ocr_gemini/entity_page_index.json")
    with open(page_index_file, 'r') as f:
        page_index_data = json.load(f)

    entity_page_mappings = page_index_data["entity_page_mappings"]
    print("✓ Loaded page references")
    print()

    total_cost = 0.0
    harmonized_all = {}

    # Process each entity type
    for entity_type in ["persons", "places", "ships", "organizations"]:
        print(f"\n{entity_type.upper()}")
        print("-" * 80)
        print(f"Original entries: {len(entities[entity_type]):,}")

        harmonized, cost = harmonize_entity_type_single_pass(
            entities[entity_type],
            entity_type
        )

        total_cost += cost
        harmonized_all[entity_type] = harmonized

        # Save checkpoint
        checkpoint_file = Path(f"nimitz_ocr_gemini/harmonization_checkpoint_{entity_type}.json")
        with open(checkpoint_file, 'w') as f:
            json.dump({
                "entity_type": entity_type,
                "harmonized": harmonized,
                "cost": cost,
                "timestamp": "2025-10-27"
            }, f, indent=2)
        print(f"  ✓ Checkpoint saved: {checkpoint_file}")

        time.sleep(2)  # Rate limiting between types

    # Merge harmonization with page references
    print("\n" + "=" * 80)
    print("Merging harmonization with page references...")
    print("=" * 80)

    final_indices = {}

    for entity_type in harmonized_all:
        final_indices[entity_type] = {}

        for authoritative, data in harmonized_all[entity_type].items():
            # Collect page references from all variants
            all_pages = set()

            for variant in data.get("variants", []):
                if variant in entity_page_mappings[entity_type]:
                    all_pages.update(entity_page_mappings[entity_type][variant])

            # Sort pages
            sorted_pages = sorted(list(all_pages), key=lambda x: (int(x.split('-')[0]), int(x.split(':')[1])))

            final_indices[entity_type][authoritative] = {
                "pages": sorted_pages,
                "page_count": len(sorted_pages),
                "subentries": data.get("subentries", []),
                "variants_merged": data.get("variants", [])
            }

    # Save final harmonized indices with page references
    output_file = Path("nimitz_ocr_gemini/indices_harmonized_with_pages.json")
    with open(output_file, 'w') as f:
        json.dump({
            "harmonization_date": "2025-10-27",
            "model": "gemini/gemini-2.5-flash-lite",
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

    print(f"\n✓ Saved final harmonized indices: {output_file}")
    print()

    # Summary
    print("=" * 80)
    print("HARMONIZATION COMPLETE")
    print("=" * 80)
    print(f"\nTotal cost: ${total_cost:.4f}")
    print(f"\nFinal index sizes:")
    for entity_type in final_indices:
        original = len(entities[entity_type])
        harmonized = len(final_indices[entity_type])
        reduction = original - harmonized
        print(f"  {entity_type.capitalize()}: {harmonized:,} (reduced from {original:,}, -{reduction:,})")

    print(f"\n  TOTAL: {sum(len(v) for v in final_indices.values()):,} authoritative entries")
    print("=" * 80)


if __name__ == "__main__":
    main()
