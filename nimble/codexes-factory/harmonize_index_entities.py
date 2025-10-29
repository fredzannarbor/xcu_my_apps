#!/usr/bin/env python3
"""
Harmonize index entries using gemini-2.5-pro with grounding.
Resolves variant spellings and formats using detailed historical knowledge.

Example:
  Marshall, Gen
  Marshall, Gen'l
  Marshall, General George C.
  => Marshall, General George C.

Per CMOS 18th ed and naval history expertise.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Tuple

import litellm
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

litellm.telemetry = False
litellm.drop_params = True


HARMONIZATION_PROMPT = """You are an expert naval historian with encyclopedic knowledge of World War II Pacific Theater personnel, ships, places, and organizations. You follow Chicago Manual of Style 18th Edition (2024) indexing guidelines.

Your task: Harmonize variant spellings and formats of index entries into single authoritative forms.

**RULES:**

1. **Use authoritative names**: Full official names with proper ranks/designations
2. **Resolve ambiguities with confidence**: Only merge entries you can verify refer to the same entity
3. **When uncertain, preserve separately**: Do not guess - keep variants if not confident
4. **Follow CMOS 18th ed**:
   - Persons: "Last, First Middle, RANK"
   - Ships: "Name (Hull Number)" without USS/IJN prefix
   - Places: Specific to general "Guadalcanal (Solomon Islands)"
   - Organizations: Official designation

**EXAMPLES:**

Persons:
```
Input: ["Marshall, Gen", "Marshall, Gen'l", "Marshall, George C.", "Marshall, George C., GEN", "General, Marshal George"]
Output: {"Marshall, General George C.": ["Marshall, Gen", "Marshall, Gen'l", "Marshall, George C.", "Marshall, George C., GEN", "General, Marshal George"]}
Reasoning: All refer to General George C. Marshall, U.S. Army Chief of Staff
```

Ships:
```
Input: ["USS Enterprise", "Enterprise (CV-6)", "Enterprise", "ENTERPRISE (CV-6)"]
Output: {"Enterprise (CV-6)": ["USS Enterprise", "Enterprise (CV-6)", "Enterprise", "ENTERPRISE (CV-6)"]}
Reasoning: Single carrier, CV-6 hull number, drop USS prefix per CMOS
```

Places:
```
Input: ["Guadalcanal", "Guadalcanal (Solomon Islands)", "Guadalcanal, Solomon Islands"]
Output: {"Guadalcanal (Solomon Islands)": ["Guadalcanal", "Guadalcanal (Solomon Islands)", "Guadalcanal, Solomon Islands"]}
Reasoning: Standard geographic format per CMOS
```

**YOUR TASK:**

Given this list of {entity_type} entries, identify variant spellings that refer to the same entity and merge them.

Return JSON:
```json
{{
  "Authoritative Entry 1": ["variant1", "variant2", ...],
  "Authoritative Entry 2": ["variant3", "variant4", ...],
  "Preserved Entry": ["only_this_variant"]
}}
```

**ENTITIES TO HARMONIZE ({count} total):**

{entity_list}

**IMPORTANT:**
- Only merge when HIGHLY CONFIDENT they refer to same entity
- Use your historical knowledge (e.g., you know George C. Marshall was Army Chief of Staff)
- Preserve entries when uncertain
- Return ALL entries (merged or preserved as-is)
"""


def harmonize_entity_batch(entities: List[str], entity_type: str, model: str = "gemini/gemini-2.5-pro") -> Dict[str, List[str]]:
    """Harmonize a batch of entities using LLM with grounding"""

    prompt = HARMONIZATION_PROMPT.format(
        entity_type=entity_type,
        count=len(entities),
        entity_list="\n".join(f"- {e}" for e in entities)
    )

    try:
        # Enable grounding for Gemini
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
            temperature=0.0,  # Deterministic for name resolution
            max_tokens=32768,  # Large output for many entities
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
            # Gemini 2.5 Pro pricing estimate
            cost = (prompt_tokens * 2.0 / 1_000_000) + (completion_tokens * 6.0 / 1_000_000)

        return harmonized, cost

    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        # Return entities as-is (no harmonization)
        return {entity: [entity] for entity in entities}, 0.0


def harmonize_all_entities(batch_size: int = 500):
    """Harmonize all entity types in batches"""

    print("=" * 80)
    print("Harmonizing Index Entries")
    print("Using: gemini-2.5-pro with grounding")
    print("Standards: CMOS 18th ed + Naval History Expertise")
    print("=" * 80)
    print()

    # Load refined entities
    refined_file = Path("nimitz_ocr_gemini/entities_refined.json")
    with open(refined_file, 'r') as f:
        data = json.load(f)

    entities = data["entities"]

    total_cost = 0.0
    harmonized_all = {}

    for entity_type in ["persons", "places", "ships", "organizations"]:
        print(f"\n{entity_type.upper()}")
        print("-" * 80)

        entity_list = entities[entity_type]
        print(f"Total entries: {len(entity_list):,}")

        # Process in batches
        harmonized_type = {}
        num_batches = (len(entity_list) + batch_size - 1) // batch_size

        print(f"Processing in {num_batches} batch{'es' if num_batches > 1 else ''} of {batch_size} entries...")

        for i in range(0, len(entity_list), batch_size):
            batch = entity_list[i:i+batch_size]
            batch_num = i // batch_size + 1

            print(f"\n  Batch {batch_num}/{num_batches} ({len(batch)} entries)...", end=" ")

            harmonized_batch, cost = harmonize_entity_batch(batch, entity_type)
            total_cost += cost

            # Merge into harmonized_type
            harmonized_type.update(harmonized_batch)

            print(f"✓ (${cost:.4f})")

            # Rate limiting
            time.sleep(2)

        # Calculate reduction
        original_count = len(entity_list)
        harmonized_count = len(harmonized_type)
        reduction = original_count - harmonized_count

        print(f"\n  Original entries: {original_count:,}")
        print(f"  Harmonized to: {harmonized_count:,}")
        print(f"  Reduction: {reduction:,} ({reduction/original_count*100:.1f}% deduplicated)")

        harmonized_all[entity_type] = harmonized_type

    # Save harmonized results
    output_file = Path("nimitz_ocr_gemini/entities_harmonized.json")
    with open(output_file, 'w') as f:
        json.dump({
            "harmonization_date": "2025-10-27",
            "model": "gemini/gemini-2.5-pro",
            "grounding": "enabled",
            "total_cost": total_cost,
            "standards": "CMOS 18th Ed (2024) + Naval History Expertise",
            "entities": harmonized_all,
            "stats": {
                entity_type: len(harmonized_all[entity_type])
                for entity_type in harmonized_all
            }
        }, f, indent=2)

    # Also save just the authoritative entries for index generation
    authoritative_file = Path("nimitz_ocr_gemini/entities_authoritative.json")
    with open(authoritative_file, 'w') as f:
        json.dump({
            "persons": sorted(list(harmonized_all["persons"].keys())),
            "places": sorted(list(harmonized_all["places"].keys())),
            "ships": sorted(list(harmonized_all["ships"].keys())),
            "organizations": sorted(list(harmonized_all["organizations"].keys()))
        }, f, indent=2)

    print("\n" + "=" * 80)
    print("HARMONIZATION COMPLETE")
    print("=" * 80)
    print(f"\nTotal cost: ${total_cost:.2f}")
    print(f"\nFinal counts:")
    for entity_type, harmonized in harmonized_all.items():
        print(f"  {entity_type.capitalize()}: {len(harmonized):,}")
    print(f"  TOTAL: {sum(len(v) for v in harmonized_all.values()):,}")
    print()
    print(f"Saved:")
    print(f"  Full harmonization: {output_file}")
    print(f"  Authoritative list: {authoritative_file}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    harmonize_all_entities(batch_size=500)
