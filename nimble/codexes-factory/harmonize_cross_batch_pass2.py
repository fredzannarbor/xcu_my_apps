#!/usr/bin/env python3
"""
Pass 2: Cross-batch harmonization reconciliation.
Identifies and merges entities that were separated by alphabetic batching.

Example: "Marshall, General George C." (M batch) + "General, George Marshall" (G batch)
Should merge into single entry.
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


CROSS_BATCH_PROMPT = """You are an expert WWII Pacific Theater naval historian. You have already harmonized entities within alphabetic batches. Now identify any remaining duplicates that were split across batches due to different name formats.

**YOUR TASK:** Find entities that refer to the SAME person/place/ship/organization but have different name structures.

**COMMON PATTERNS TO CATCH:**

**Persons:**
- "Marshall, General George C." vs "General, George Marshall" → SAME PERSON (inverted format)
- "Nimitz, Admiral" vs "Admiral Nimitz" → SAME PERSON
- "Spruance, Raymond A., RADM" vs "Spruance, VADM" → SAME PERSON (rank progression)

**Places:**
- "Pearl Harbor" vs "Harbor, Pearl" → SAME PLACE (inverted)
- Coordinate variants already handled in Pass 1

**Ships:**
- "Enterprise (CV-6)" vs "Enterprise, USS (CV-6)" → SAME SHIP

**Organizations:**
- "Task Force 16" vs "TF 16" → SAME (but these should be caught in Pass 1)
- Verify CINCPAC vs COMINCH are DIFFERENT (do NOT merge!)

**RULES:**
1. Only merge when 100% CONFIDENT
2. Use your historical knowledge
3. If uncertain, keep separate
4. Return ONLY the duplicates to merge (not all entries)

**INPUT: Harmonized entries from Pass 1 ({count} entries in {entity_type})**

{entity_list}

**OUTPUT FORMAT:**
```json
{{
  "merges": [
    {{
      "authoritative": "Marshall, General George C.",
      "merge_these": ["General, George Marshall", "Marshall, George C., Gen"],
      "reasoning": "All refer to U.S. Army Chief of Staff George C. Marshall"
    }},
    {{
      "authoritative": "Nimitz, Chester W., Admiral",
      "merge_these": ["Admiral Nimitz", "Nimitz, Fleet Admiral"],
      "reasoning": "All refer to Chester W. Nimitz, CINCPAC"
    }}
  ]
}}
```

Return ONLY entities that should be merged. If no cross-batch duplicates found, return empty merges list."""


def find_cross_batch_duplicates(
    harmonized_entities: Dict,
    entity_type: str,
    model: str = "gemini/gemini-2.5-pro"
) -> tuple:
    """Find duplicates across alphabetic batches"""

    entity_list = list(harmonized_entities.keys())

    prompt = CROSS_BATCH_PROMPT.format(
        count=len(entity_list),
        entity_type=entity_type,
        entity_list="\n".join(entity_list)
    )

    print(f"  Analyzing {len(entity_list):,} harmonized entries for cross-batch duplicates...")

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
            max_tokens=8192,  # Smaller - just returning merge instructions
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

        merge_instructions = json.loads(content)

        # Calculate cost
        cost = 0
        if hasattr(response, 'usage') and response.usage:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            cost = (prompt_tokens * 1.25 / 1_000_000) + (completion_tokens * 5.0 / 1_000_000)

        return merge_instructions, cost, None

    except Exception as e:
        return {"merges": []}, 0.0, str(e)


def apply_cross_batch_merges(harmonized_entities: Dict, merge_instructions: Dict) -> Dict:
    """Apply cross-batch merge instructions"""

    merges = merge_instructions.get("merges", [])

    if not merges:
        return harmonized_entities

    print(f"  Applying {len(merges)} cross-batch merges...")

    result = dict(harmonized_entities)

    for merge in merges:
        authoritative = merge["authoritative"]
        to_merge = merge["merge_these"]

        # Collect variants and subentries from all merged entities
        all_variants = set()
        all_subentries = []

        # Start with authoritative entry
        if authoritative in result:
            all_variants.update(result[authoritative].get("variants", []))
            all_subentries.extend(result[authoritative].get("subentries", []))

        # Add from entities being merged
        for entity in to_merge:
            if entity in result:
                all_variants.update(result[entity].get("variants", []))
                all_subentries.extend(result[entity].get("subentries", []))

                # Remove the merged entity
                del result[entity]

        # Update authoritative entry
        result[authoritative] = {
            "variants": sorted(list(all_variants)),
            "subentries": list(set(all_subentries))  # Deduplicate subentries
        }

        print(f"    ✓ Merged {len(to_merge)} entries into: {authoritative}")

    return result


def main():
    print("=" * 80)
    print("Pass 2: Cross-Batch Reconciliation")
    print("Model: gemini-2.5-pro with grounding")
    print("=" * 80)
    print()

    # Wait for Pass 1 to complete
    pass1_file = Path("nimitz_ocr_gemini/indices_harmonized_pro.json")

    if not pass1_file.exists():
        print("⚠️  Pass 1 harmonization not complete yet.")
        print("   Waiting for: nimitz_ocr_gemini/indices_harmonized_pro.json")
        print()
        print("   Run this script after Pass 1 completes.")
        return

    # Load Pass 1 results
    print("Loading Pass 1 harmonization results...")
    with open(pass1_file, 'r') as f:
        pass1_data = json.load(f)

    indices = pass1_data["indices"]

    print(f"✓ Loaded Pass 1 results")
    print(f"  Cost from Pass 1: ${pass1_data.get('total_cost', 0):.2f}")
    print()

    total_cost_pass2 = 0.0
    final_indices = {}

    # Process each entity type
    for entity_type in ["persons", "places", "ships", "organizations"]:
        print(f"\n{entity_type.upper()}")
        print("-" * 80)
        print(f"Pass 1 entries: {len(indices[entity_type]):,}")

        # Extract just the harmonization mapping (not page refs yet)
        harmonized_only = {}
        for auth_entry, data in indices[entity_type].items():
            harmonized_only[auth_entry] = {
                "variants": data.get("variants_merged", []),
                "subentries": data.get("subentries", [])
            }

        # Find cross-batch duplicates
        merge_instructions, cost, error = find_cross_batch_duplicates(
            harmonized_only,
            entity_type
        )

        total_cost_pass2 += cost

        if error:
            print(f"  ✗ Error: {error}")
            final_indices[entity_type] = indices[entity_type]
        else:
            merges_count = len(merge_instructions.get("merges", []))
            print(f"  ✓ Found {merges_count} cross-batch duplicates (${cost:.4f})")

            # Apply merges to harmonized entities
            merged_harmonized = apply_cross_batch_merges(harmonized_only, merge_instructions)

            # Rebuild full index with page references
            final_with_pages = {}
            for auth_entry, data in merged_harmonized.items():
                # Find corresponding entry in original Pass 1 (might be merged from multiple)
                all_pages = set()

                # Check if this was an authoritative entry
                if auth_entry in indices[entity_type]:
                    all_pages.update(indices[entity_type][auth_entry]["pages"])

                # Check all variants
                for variant in data["variants"]:
                    if variant in indices[entity_type]:
                        all_pages.update(indices[entity_type][variant]["pages"])

                sorted_pages = sorted(list(all_pages), key=lambda x: (int(x.split('-')[0]), int(x.split(':')[1])))

                final_with_pages[auth_entry] = {
                    "pages": sorted_pages,
                    "page_count": len(sorted_pages),
                    "subentries": data.get("subentries", []),
                    "variants_merged": data.get("variants", [])
                }

            final_indices[entity_type] = final_with_pages

            reduction = len(indices[entity_type]) - len(final_with_pages)
            print(f"  Pass 2 reduction: {reduction} entries merged")

        time.sleep(2)  # Rate limiting

    # Save final indices
    output_file = Path("nimitz_ocr_gemini/indices_final.json")
    with open(output_file, 'w') as f:
        json.dump({
            "harmonization_date": "2025-10-27",
            "model": "gemini/gemini-2.5-pro",
            "pass1_cost": pass1_data.get("total_cost", 0),
            "pass2_cost": total_cost_pass2,
            "total_cost": pass1_data.get("total_cost", 0) + total_cost_pass2,
            "grounding": "enabled",
            "indices": final_indices,
            "stats": {
                entity_type: {
                    "total_entries": len(final_indices[entity_type]),
                    "total_page_refs": sum(len(v["pages"]) for v in final_indices[entity_type].values())
                }
                for entity_type in final_indices
            }
        }, f, indent=2)

    print("\n" + "=" * 80)
    print("PASS 2 COMPLETE - FINAL HARMONIZED INDICES")
    print("=" * 80)
    print(f"\nPass 1 cost: ${pass1_data.get('total_cost', 0):.2f}")
    print(f"Pass 2 cost: ${total_cost_pass2:.2f}")
    print(f"TOTAL COST: ${pass1_data.get('total_cost', 0) + total_cost_pass2:.2f}")
    print(f"\nFinal indices:")
    for et in final_indices:
        pass1_count = len(indices[et])
        pass2_count = len(final_indices[et])
        total_reduction = pass1_count - pass2_count
        print(f"  {et.capitalize()}: {pass2_count:,} (reduced {total_reduction} in Pass 2)")

    print(f"\n  TOTAL: {sum(len(v) for v in final_indices.values()):,} authoritative entries")
    print(f"\nSaved: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
