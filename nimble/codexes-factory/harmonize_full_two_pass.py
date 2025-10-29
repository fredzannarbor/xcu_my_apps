#!/usr/bin/env python3
"""
Full two-pass harmonization using openai/gpt-5-mini.
Pass 1: Small batches (100 entries) for within-batch harmonization
Pass 2: Cross-batch reconciliation of all harmonized entries
"""

import json
import time
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

import litellm
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

litellm.telemetry = False
litellm.drop_params = True


PASS1_PERSONS_PROMPT = """Harmonize these person name variants.

RULES:
1. Normalize capitalization: NIMITZ → Nimitz
2. Spell out ranks: Gen → General, Adm → Admiral, RADM → Rear Admiral
3. Same person, different ranks → subentries
4. Full official names when known
5. Only merge when HIGHLY CONFIDENT

Return JSON:
{{
  "Authoritative Name": {{"variants": ["var1", "var2"], "subentries": ["rank info"]}},
  ...
}}

ENTRIES:
{entity_list}"""

PASS1_PLACES_PROMPT = """Harmonize place names.

RULES:
1. KEEP all coordinates (legitimate references)
2. Harmonize coordinate format: "DD-MM N, DDD-MM E"
3. Normalize: OAHU → Oahu
4. Format: "Specific (General)"

Return JSON:
{{
  "Pearl Harbor": {{"variants": ["PEARL HARBOR", "Pearl Harbor"], "type": "naval_base"}},
  "05-18 N, 125-50 E": {{"variants": ["05-18N, 125-50E"], "type": "coordinate"}},
  ...
}}

ENTRIES:
{entity_list}"""

PASS1_SHIPS_PROMPT = """Harmonize ship names.

RULES:
1. Format: "Name (Hull Number)" without USS/IJN
2. KEEP generic "DD", "AK" - mark as "[unspecified]"
3. Normalize capitalization

Return JSON:
{{
  "Enterprise (CV-6)": {{"variants": ["USS Enterprise", "ENTERPRISE (CV-6)"]}},
  "DD [unspecified]": {{"variants": ["DD", "1 DD"], "note": "Generic destroyer"}},
  ...
}}

ENTRIES:
{entity_list}"""

PASS1_ORGS_PROMPT = """Harmonize organization names.

RULES:
1. CINCPAC ≠ COMINCH (different commands!)
2. Normalize: "TF 16" → "Task Force 16"
3. Spell out in subentries

Return JSON:
{{
  "CINCPAC": {{"variants": ["CINCPAC", "CinCPac"], "full_name": "Commander in Chief, Pacific"}},
  ...
}}

ENTRIES:
{entity_list}"""

PASS2_PROMPT = """Find duplicates ACROSS these harmonized batches.

BATCH RESULTS FROM PASS 1:
{all_entries}

Find persons/places/ships/orgs that appear multiple times with different name formats.

Example: "Admiral Nimitz" + "Nimitz, Chester W., Admiral" → SAME

Return JSON:
{{
  "cross_batch_merges": [
    {{
      "authoritative": "Nimitz, Chester W., Admiral",
      "merge_these": ["Admiral Nimitz", "Nimitz, ADM"],
      "reasoning": "All refer to Chester W. Nimitz, CINCPAC"
    }}
  ]
}}"""


def create_small_batches(entities: List[str], batch_size: int = 100) -> List[List[str]]:
    """Create small batches of entities"""
    batches = []
    for i in range(0, len(entities), batch_size):
        batches.append(entities[i:i + batch_size])
    return batches


def harmonize_batch_pass1(batch: List[str], entity_type: str, model: str = "gemini/gemini-2.5-flash") -> tuple:
    """Pass 1: Harmonize within a single batch"""

    prompts = {
        "persons": PASS1_PERSONS_PROMPT,
        "places": PASS1_PLACES_PROMPT,
        "ships": PASS1_SHIPS_PROMPT,
        "organizations": PASS1_ORGS_PROMPT
    }

    prompt = prompts[entity_type].format(entity_list="\n".join(batch))

    try:
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=16384  # Increased for full batch output
        )

        content = response.choices[0].message.content
        harmonized = json.loads(content)

        cost = (response.usage.prompt_tokens * 0.15 / 1_000_000) + (response.usage.completion_tokens * 0.60 / 1_000_000)

        return harmonized, cost, None

    except Exception as e:
        return {entity: {"variants": [entity], "subentries": []} for entity in batch}, 0.0, str(e)


def harmonize_cross_batch_pass2(all_harmonized: List[str], entity_type: str, model: str = "gemini/gemini-2.5-flash") -> tuple:
    """Pass 2: Find cross-batch duplicates"""

    prompt = PASS2_PROMPT.format(all_entries="\n".join(all_harmonized))

    try:
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=16384  # Increased for full output
        )

        content = response.choices[0].message.content
        merges = json.loads(content)

        cost = (response.usage.prompt_tokens * 0.15 / 1_000_000) + (response.usage.completion_tokens * 0.60 / 1_000_000)

        return merges, cost, None

    except Exception as e:
        return {"cross_batch_merges": []}, 0.0, str(e)


def apply_merges(harmonized: Dict, merges: List[Dict]) -> Dict:
    """Apply cross-batch merge instructions"""

    result = dict(harmonized)

    for merge in merges:
        auth = merge["authoritative"]
        to_merge = merge["merge_these"]

        all_variants = set()
        all_subentries = []

        # Collect from all entries being merged
        for entity in [auth] + to_merge:
            if entity in result:
                all_variants.update(result[entity].get("variants", [entity]))
                all_subentries.extend(result[entity].get("subentries", []))

                if entity != auth:
                    del result[entity]

        result[auth] = {
            "variants": sorted(list(all_variants)),
            "subentries": list(set(all_subentries))
        }

    return result


def main():
    print("=" * 80)
    print("Full Two-Pass Harmonization - gemini/gemini-2.5-flash")
    print("Batch size: 100 entries per batch")
    print("=" * 80)
    print()

    # Load data
    refined_file = Path("nimitz_ocr_gemini/entities_refined.json")
    with open(refined_file, 'r') as f:
        entities = json.load(f)["entities"]

    page_index_file = Path("nimitz_ocr_gemini/entity_page_index.json")
    with open(page_index_file, 'r') as f:
        entity_page_mappings = json.load(f)["entity_page_mappings"]

    model = "openai/gpt-5-mini"
    total_cost = 0.0
    final_indices = {}

    for entity_type in ["persons", "places", "ships", "organizations"]:
        print(f"\n{'=' * 80}")
        print(f"{entity_type.upper()}")
        print('=' * 80)

        entity_list = entities[entity_type]
        print(f"Total entries: {len(entity_list):,}")

        # PASS 1: Batch harmonization
        batches = create_small_batches(entity_list, batch_size=100)
        print(f"Pass 1: Processing {len(batches)} batches of ~100 entries...")

        all_harmonized = {}

        for i, batch in enumerate(tqdm(batches, desc=f"  {entity_type} Pass 1")):
            harmonized, cost, error = harmonize_batch_pass1(batch, entity_type, model)

            if error:
                print(f"\n  Batch {i+1} error: {error[:100]}")

            all_harmonized.update(harmonized)
            total_cost += cost

            # Checkpoint every 10 batches
            if (i + 1) % 10 == 0:
                checkpoint = Path(f"nimitz_ocr_gemini/pass1_checkpoint_{entity_type}_{i+1}.json")
                with open(checkpoint, 'w') as f:
                    json.dump(all_harmonized, f, indent=2)

            time.sleep(0.5)  # Rate limiting

        print(f"  Pass 1 complete: {len(entity_list):,} → {len(all_harmonized):,} (-{len(entity_list)-len(all_harmonized):,})")

        # PASS 2: Cross-batch reconciliation
        print(f"  Pass 2: Cross-batch reconciliation...")

        merges, cost, error = harmonize_cross_batch_pass2(list(all_harmonized.keys()), entity_type, model)

        total_cost += cost

        if error:
            print(f"  Pass 2 error: {error[:100]}")
            final_harmonized = all_harmonized
        else:
            merge_list = merges.get("cross_batch_merges", [])
            print(f"  Found {len(merge_list)} cross-batch duplicates")

            final_harmonized = apply_merges(all_harmonized, merge_list)

        print(f"  Final: {len(final_harmonized):,} entries")

        # Merge with page references
        final_with_pages = {}
        for auth, data in final_harmonized.items():
            all_pages = set()

            for variant in data.get("variants", [auth]):
                if variant in entity_page_mappings[entity_type]:
                    all_pages.update(entity_page_mappings[entity_type][variant])

            sorted_pages = sorted(list(all_pages), key=lambda x: (int(x.split('-')[0]), int(x.split(':')[1])))

            final_with_pages[auth] = {
                "pages": sorted_pages,
                "page_count": len(sorted_pages),
                "subentries": data.get("subentries", []),
                "variants_merged": data.get("variants", [auth])
            }

        final_indices[entity_type] = final_with_pages

    # Save final
    output = Path("nimitz_ocr_gemini/indices_complete_harmonized.json")
    with open(output, 'w') as f:
        json.dump({
            "harmonization_date": "2025-10-27",
            "model": model,
            "total_cost": total_cost,
            "batch_size": 100,
            "two_pass": True,
            "indices": final_indices,
            "stats": {
                et: {
                    "entries": len(final_indices[et]),
                    "page_refs": sum(len(v["pages"]) for v in final_indices[et].values())
                }
                for et in final_indices
            }
        }, f, indent=2)

    print("\n" + "=" * 80)
    print("COMPLETE TWO-PASS HARMONIZATION FINISHED")
    print("=" * 80)
    print(f"\nModel: {model}")
    print(f"Total cost: ${total_cost:.2f}")
    print(f"\nFinal indices:")
    for et in final_indices:
        print(f"  {et.capitalize()}: {len(final_indices[et]):,} entries")
    print(f"  TOTAL: {sum(len(v) for v in final_indices.values()):,}")
    print(f"\nSaved: {output}")
    print("=" * 80)


if __name__ == "__main__":
    main()
